"""
데이터 레이어 엔티티 정의
도로 네트워크 그래프 구조
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


class RoadType(Enum):
    """도로 타입"""
    PRIMARY = "primary"           # 주요 도로
    SECONDARY = "secondary"       # 보조 도로
    TERTIARY = "tertiary"         # 3차 도로
    RESIDENTIAL = "residential"   # 주거지역 도로
    FOOTWAY = "footway"           # 보행자 도로
    PATH = "path"                 # 경로/산책로
    CYCLEWAY = "cycleway"         # 자전거 도로
    UNKNOWN = "unknown"           # 알 수 없음


@dataclass(frozen=True)
class Node:
    """
    교차로/노드 데이터 모델
    
    Attributes:
        id: 고유 식별자 (OSM node id)
        lat: 위도
        lng: 경도
        has_traffic_light: 신호등 존재 여부
    """
    id: int
    lat: float
    lng: float
    has_traffic_light: bool = False
    
    def to_tuple(self) -> Tuple[float, float]:
        """위도, 경도 튜플 반환"""
        return (self.lat, self.lng)
    
    def distance_to(self, other: 'Node') -> float:
        """
        다른 노드까지의 대략적인 거리 계산 (Haversine 공식)
        
        Args:
            other: 대상 노드
            
        Returns:
            거리 (km)
        """
        import math
        
        R = 6371  # 지구 반지름 (km)
        
        lat1, lng1 = math.radians(self.lat), math.radians(self.lng)
        lat2, lng2 = math.radians(other.lat), math.radians(other.lng)
        
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c


@dataclass(frozen=True)
class Edge:
    """
    도로/엣지 데이터 모델
    
    Attributes:
        id: 고유 식별자
        source_id: 시작 노드 ID
        target_id: 끝 노드 ID
        length_m: 도로 길이 (미터)
        road_type: 도로 타입
        name: 도로 이름 (선택)
        is_oneway: 일방통행 여부
    """
    id: int
    source_id: int
    target_id: int
    length_m: float
    road_type: RoadType = RoadType.UNKNOWN
    name: Optional[str] = None
    is_oneway: bool = False
    
    @property
    def length_km(self) -> float:
        """도로 길이 (km)"""
        return self.length_m / 1000.0


@dataclass
class RoadGraph:
    """
    도로 네트워크 그래프
    
    노드(교차로)와 엣지(도로)로 구성된 그래프 구조
    """
    nodes: Dict[int, Node] = field(default_factory=dict)
    edges: Dict[int, Edge] = field(default_factory=dict)
    _adjacency: Dict[int, Set[int]] = field(default_factory=dict)
    
    def add_node(self, node: Node) -> None:
        """노드 추가"""
        self.nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = set()
    
    def add_edge(self, edge: Edge) -> None:
        """엣지 추가 (양방향 인접 리스트 업데이트)"""
        self.edges[edge.id] = edge
        
        # 인접 리스트 업데이트
        if edge.source_id not in self._adjacency:
            self._adjacency[edge.source_id] = set()
        if edge.target_id not in self._adjacency:
            self._adjacency[edge.target_id] = set()
            
        self._adjacency[edge.source_id].add(edge.target_id)
        
        # 양방향 도로인 경우 역방향도 추가
        if not edge.is_oneway:
            self._adjacency[edge.target_id].add(edge.source_id)
    
    def get_node(self, node_id: int) -> Optional[Node]:
        """노드 ID로 노드 조회"""
        return self.nodes.get(node_id)
    
    def get_neighbors(self, node_id: int) -> Set[int]:
        """인접 노드 ID 목록 반환"""
        return self._adjacency.get(node_id, set())
    
    def get_edges_from(self, node_id: int) -> List[Edge]:
        """특정 노드에서 출발하는 엣지 목록 반환"""
        result = []
        for edge in self.edges.values():
            if edge.source_id == node_id:
                result.append(edge)
            elif not edge.is_oneway and edge.target_id == node_id:
                result.append(edge)
        return result
    
    def get_edge_between(self, source_id: int, target_id: int) -> Optional[Edge]:
        """두 노드 사이의 엣지 반환"""
        for edge in self.edges.values():
            if edge.source_id == source_id and edge.target_id == target_id:
                return edge
            if not edge.is_oneway and edge.source_id == target_id and edge.target_id == source_id:
                return edge
        return None
    
    @property
    def node_count(self) -> int:
        """노드 수"""
        return len(self.nodes)
    
    @property
    def edge_count(self) -> int:
        """엣지 수"""
        return len(self.edges)
    
    def get_traffic_light_nodes(self) -> List[Node]:
        """신호등이 있는 노드 목록 반환"""
        return [node for node in self.nodes.values() if node.has_traffic_light]
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """
        그래프의 바운딩 박스 반환
        
        Returns:
            (north, south, east, west) 튜플
        """
        if not self.nodes:
            return (0.0, 0.0, 0.0, 0.0)
        
        lats = [node.lat for node in self.nodes.values()]
        lngs = [node.lng for node in self.nodes.values()]
        
        return (max(lats), min(lats), max(lngs), min(lngs))
    
    def find_nearest_node(self, lat: float, lng: float) -> Optional[Node]:
        """
        주어진 좌표에서 가장 가까운 노드 찾기
        
        Args:
            lat: 위도
            lng: 경도
            
        Returns:
            가장 가까운 노드 (없으면 None)
        """
        if not self.nodes:
            return None
        
        temp_node = Node(id=-1, lat=lat, lng=lng)
        nearest = None
        min_dist = float('inf')
        
        for node in self.nodes.values():
            dist = temp_node.distance_to(node)
            if dist < min_dist:
                min_dist = dist
                nearest = node
        
        return nearest
