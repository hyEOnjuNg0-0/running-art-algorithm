"""
OSM 데이터 Repository 구현
osmnx 라이브러리를 활용한 OpenStreetMap 데이터 처리
"""
import logging
from typing import Optional, Dict, Any

import osmnx as ox
import networkx as nx

from src.data.entities import Node, Edge, RoadGraph, RoadType
from src.data.repository import GraphRepository, GraphFetchError
from src.domain.entities import BoundingBox


logger = logging.getLogger(__name__)


class OSMGraphRepository(GraphRepository):
    """
    OpenStreetMap 데이터를 활용한 그래프 Repository 구현
    
    osmnx 라이브러리를 사용하여 OSM에서 도로 네트워크를 가져옴
    """
    
    # OSM highway 태그를 RoadType으로 매핑
    HIGHWAY_TO_ROAD_TYPE: Dict[str, RoadType] = {
        "primary": RoadType.PRIMARY,
        "primary_link": RoadType.PRIMARY,
        "secondary": RoadType.SECONDARY,
        "secondary_link": RoadType.SECONDARY,
        "tertiary": RoadType.TERTIARY,
        "tertiary_link": RoadType.TERTIARY,
        "residential": RoadType.RESIDENTIAL,
        "living_street": RoadType.RESIDENTIAL,
        "footway": RoadType.FOOTWAY,
        "pedestrian": RoadType.FOOTWAY,
        "path": RoadType.PATH,
        "track": RoadType.PATH,
        "cycleway": RoadType.CYCLEWAY,
    }
    
    def __init__(self):
        """Repository 초기화"""
        # osmnx 설정
        ox.settings.use_cache = True
        ox.settings.log_console = False
    
    def get_graph_by_bbox(
        self,
        bbox: BoundingBox,
        network_type: str = "walk"
    ) -> RoadGraph:
        """
        바운딩 박스 영역의 도로 네트워크 그래프 반환
        
        Args:
            bbox: 영역 범위
            network_type: 네트워크 타입 ("walk", "bike", "drive", "all")
            
        Returns:
            도로 네트워크 그래프
        """
        try:
            logger.info(f"OSM 그래프 로딩 시작: bbox={bbox}, network_type={network_type}")
            
            # osmnx v2.0+ API: bbox를 튜플로 전달 (north, south, east, west)
            bbox_tuple = (bbox.north, bbox.south, bbox.east, bbox.west)
            
            import time
            start_time = time.time()
            
            G = ox.graph_from_bbox(
                bbox=bbox_tuple,
                network_type=network_type,
                simplify=True
            )
            
            elapsed = time.time() - start_time
            logger.info(f"OSM 그래프 로딩 완료: {elapsed:.1f}초 소요")
            
            return self._convert_to_road_graph(G)
            
        except Exception as e:
            logger.error(f"OSM 그래프 로딩 실패: {e}")
            raise GraphFetchError(f"바운딩 박스 영역 그래프 로딩 실패: {e}")
    
    def get_graph_by_point(
        self,
        lat: float,
        lng: float,
        distance_m: float = 1000,
        network_type: str = "walk"
    ) -> RoadGraph:
        """
        특정 지점 중심으로 일정 거리 내 도로 네트워크 그래프 반환
        
        Args:
            lat: 중심점 위도
            lng: 중심점 경도
            distance_m: 반경 (미터)
            network_type: 네트워크 타입
            
        Returns:
            도로 네트워크 그래프
        """
        try:
            logger.info(f"OSM 그래프 로딩: point=({lat}, {lng}), dist={distance_m}m")
            
            # osmnx로 그래프 가져오기
            G = ox.graph_from_point(
                center_point=(lat, lng),
                dist=distance_m,
                network_type=network_type,
                simplify=True
            )
            
            return self._convert_to_road_graph(G)
            
        except Exception as e:
            logger.error(f"OSM 그래프 로딩 실패: {e}")
            raise GraphFetchError(f"지점 중심 그래프 로딩 실패: {e}")
    
    def _convert_to_road_graph(self, G: nx.MultiDiGraph) -> RoadGraph:
        """
        NetworkX 그래프를 RoadGraph로 변환
        
        Args:
            G: osmnx에서 반환한 NetworkX 그래프
            
        Returns:
            RoadGraph 객체
        """
        road_graph = RoadGraph()
        
        # 노드 변환
        for node_id, data in G.nodes(data=True):
            has_traffic_light = self._check_traffic_light(data)
            
            node = Node(
                id=int(node_id),
                lat=data.get('y', 0.0),
                lng=data.get('x', 0.0),
                has_traffic_light=has_traffic_light
            )
            road_graph.add_node(node)
        
        # 엣지 변환
        edge_id = 0
        for u, v, key, data in G.edges(keys=True, data=True):
            edge = self._create_edge(edge_id, u, v, data)
            road_graph.add_edge(edge)
            edge_id += 1
        
        logger.info(f"그래프 변환 완료: {road_graph.node_count} 노드, {road_graph.edge_count} 엣지")
        
        return road_graph
    
    def _check_traffic_light(self, node_data: Dict[str, Any]) -> bool:
        """
        노드에 신호등이 있는지 확인
        
        Args:
            node_data: 노드 속성 딕셔너리
            
        Returns:
            신호등 존재 여부
        """
        # OSM에서 신호등 관련 태그 확인
        highway = node_data.get('highway', '')
        crossing = node_data.get('crossing', '')
        
        if highway == 'traffic_signals':
            return True
        if crossing in ['traffic_signals', 'signal']:
            return True
        
        return False
    
    def _create_edge(
        self,
        edge_id: int,
        source_id: int,
        target_id: int,
        edge_data: Dict[str, Any]
    ) -> Edge:
        """
        엣지 데이터 생성
        
        Args:
            edge_id: 엣지 ID
            source_id: 시작 노드 ID
            target_id: 끝 노드 ID
            edge_data: 엣지 속성 딕셔너리
            
        Returns:
            Edge 객체
        """
        # 길이 추출
        length_m = edge_data.get('length', 0.0)
        
        # 도로 타입 추출
        highway = edge_data.get('highway', 'unknown')
        if isinstance(highway, list):
            highway = highway[0] if highway else 'unknown'
        road_type = self.HIGHWAY_TO_ROAD_TYPE.get(highway, RoadType.UNKNOWN)
        
        # 도로 이름 추출
        name = edge_data.get('name', None)
        if isinstance(name, list):
            name = name[0] if name else None
        
        # 일방통행 여부
        oneway = edge_data.get('oneway', False)
        is_oneway = oneway is True or oneway == 'yes'
        
        return Edge(
            id=edge_id,
            source_id=int(source_id),
            target_id=int(target_id),
            length_m=float(length_m),
            road_type=road_type,
            name=name,
            is_oneway=is_oneway
        )
