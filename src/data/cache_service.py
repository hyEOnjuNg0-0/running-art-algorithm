"""
그래프 캐싱 서비스
자주 사용되는 영역 데이터 캐싱 및 직렬화/역직렬화
"""
import hashlib
import json
import logging
import pickle
from pathlib import Path
from typing import Optional, Dict, Any

from src.data.entities import Node, Edge, RoadGraph, RoadType
from src.domain.entities import BoundingBox


logger = logging.getLogger(__name__)


class GraphCacheService:
    """
    그래프 캐싱 서비스
    
    파일 시스템 기반 캐싱으로 동일 영역 재요청 시 빠른 응답 제공
    """
    
    def __init__(self, cache_dir: str = ".cache/graphs"):
        """
        캐시 서비스 초기화
        
        Args:
            cache_dir: 캐시 파일 저장 디렉토리
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"캐시 디렉토리 초기화: {self.cache_dir}")
    
    def get_cache_key(
        self,
        bbox: Optional[BoundingBox] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        distance_m: Optional[float] = None,
        network_type: str = "walk"
    ) -> str:
        """
        캐시 키 생성
        
        Args:
            bbox: 바운딩 박스 (bbox 기반 조회 시)
            lat, lng, distance_m: 중심점 기반 조회 시
            network_type: 네트워크 타입
            
        Returns:
            캐시 키 문자열
        """
        if bbox:
            key_data = f"bbox_{bbox.north}_{bbox.south}_{bbox.east}_{bbox.west}_{network_type}"
        else:
            key_data = f"point_{lat}_{lng}_{distance_m}_{network_type}"
        
        # MD5 해시로 파일명 생성
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, cache_key: str) -> Optional[RoadGraph]:
        """
        캐시에서 그래프 조회
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            캐시된 그래프 (없으면 None)
        """
        # JSON 캐시 우선 확인
        json_file = self.cache_dir / f"{cache_key}.json"
        if json_file.exists():
            try:
                graph = self._load_from_json(json_file)
                if graph:
                    logger.info(f"캐시 히트 (JSON): {cache_key}")
                    return graph
            except Exception as e:
                logger.warning(f"JSON 캐시 로드 실패: {e}")

        # 기존 pickle 캐시 확인 (하위 호환)
        pkl_file = self.cache_dir / f"{cache_key}.pkl"
        if pkl_file.exists():
            try:
                with open(pkl_file, 'rb') as f:
                    graph = pickle.load(f)
                logger.info(f"캐시 히트 (pickle): {cache_key}")
                return graph
            except Exception as e:
                logger.warning(f"pickle 캐시 로드 실패: {e}")
        
        logger.debug(f"캐시 미스: {cache_key}")
        return None
    
    def set(self, cache_key: str, graph: RoadGraph) -> bool:
        """
        그래프를 캐시에 저장(JSON 형식)
        
        Args:
            cache_key: 캐시 키
            graph: 저장할 그래프
            
        Returns:
            저장 성공 여부
        """
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            self._save_to_json(graph, cache_file)
            logger.info(f"캐시 저장: {cache_key} ({graph.node_count} 노드, {graph.edge_count} 엣지)")
            return True
        except Exception as e:
            logger.error(f"캐시 저장 실패: {e}")
            return False
    
    def _save_to_json(self, graph: RoadGraph, filepath: Path) -> None:
        """그래프를 JSON 파일로 저장"""
        data = {
            "nodes": [
                {
                    "id": node.id,
                    "lat": node.lat,
                    "lng": node.lng,
                    "has_traffic_light": node.has_traffic_light
                }
                for node in graph.nodes.values()
            ],
            "edges": [
                {
                    "id": edge.id,
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "length_m": edge.length_m,
                    "road_type": edge.road_type.value,
                    "name": edge.name,
                    "is_oneway": edge.is_oneway
                }
                for edge in graph.edges.values()
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    
    def _load_from_json(self, filepath: Path) -> Optional[RoadGraph]:
        """JSON 파일에서 그래프 로드"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        graph = RoadGraph()
        
        for node_data in data.get("nodes", []):
            node = Node(
                id=node_data["id"],
                lat=node_data["lat"],
                lng=node_data["lng"],
                has_traffic_light=node_data.get("has_traffic_light", False)
            )
            graph.add_node(node)
        
        for edge_data in data.get("edges", []):
            road_type = RoadType(edge_data.get("road_type", "unknown"))
            edge = Edge(
                id=edge_data["id"],
                source_id=edge_data["source_id"],
                target_id=edge_data["target_id"],
                length_m=edge_data["length_m"],
                road_type=road_type,
                name=edge_data.get("name"),
                is_oneway=edge_data.get("is_oneway", False)
            )
            graph.add_edge(edge)
        
        return graph
    
    def delete(self, cache_key: str) -> bool:
        """
        캐시 항목 삭제
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            삭제 성공 여부
        """
        try:
            # JSON과 pickle 둘 다 삭제
            for ext in [".json", ".pkl"]:
                cache_file = self.cache_dir / f"{cache_key}{ext}"
                if cache_file.exists():
                    cache_file.unlink()
                    logger.info(f"캐시 삭제: {cache_key}{ext}")
            return True
        except Exception as e:
            logger.error(f"캐시 삭제 실패: {e}")
            return False
    
    def clear_all(self) -> int:
        """
        모든 캐시 삭제
        
        Returns:
            삭제된 파일 수
        """
        count = 0
        for ext in ["*.json", "*.pkl"]:
            for cache_file in self.cache_dir.glob(ext):
                try:
                    cache_file.unlink()
                    count += 1
                except Exception as e:
                    logger.warning(f"캐시 파일 삭제 실패: {cache_file}, {e}")
        
        logger.info(f"캐시 전체 삭제: {count}개 파일")
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 반환
        
        Returns:
            캐시 통계 딕셔너리
        """
        cache_files = list(self.cache_dir.glob("*.json")) + list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "cache_dir": str(self.cache_dir),
            "file_count": len(cache_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }
    
    def export_to_json(self, graph: RoadGraph, filepath: str) -> bool:
        """
        그래프를 JSON 형식으로 내보내기
        
        Args:
            graph: 내보낼 그래프
            filepath: 저장 경로
            
        Returns:
            저장 성공 여부
        """
        try:
            data = {
                "nodes": [
                    {
                        "id": node.id,
                        "lat": node.lat,
                        "lng": node.lng,
                        "has_traffic_light": node.has_traffic_light
                    }
                    for node in graph.nodes.values()
                ],
                "edges": [
                    {
                        "id": edge.id,
                        "source_id": edge.source_id,
                        "target_id": edge.target_id,
                        "length_m": edge.length_m,
                        "road_type": edge.road_type.value,
                        "name": edge.name,
                        "is_oneway": edge.is_oneway
                    }
                    for edge in graph.edges.values()
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"JSON 내보내기 완료: {filepath}")
            return True
        except Exception as e:
            logger.error(f"JSON 내보내기 실패: {e}")
            return False
    
    def import_from_json(self, filepath: str) -> Optional[RoadGraph]:
        """
        JSON 파일에서 그래프 가져오기
        
        Args:
            filepath: JSON 파일 경로
            
        Returns:
            로드된 그래프 (실패 시 None)
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            graph = RoadGraph()
            
            # 노드 로드
            for node_data in data.get("nodes", []):
                node = Node(
                    id=node_data["id"],
                    lat=node_data["lat"],
                    lng=node_data["lng"],
                    has_traffic_light=node_data.get("has_traffic_light", False)
                )
                graph.add_node(node)
            
            # 엣지 로드
            for edge_data in data.get("edges", []):
                road_type = RoadType(edge_data.get("road_type", "unknown"))
                edge = Edge(
                    id=edge_data["id"],
                    source_id=edge_data["source_id"],
                    target_id=edge_data["target_id"],
                    length_m=edge_data["length_m"],
                    road_type=road_type,
                    name=edge_data.get("name"),
                    is_oneway=edge_data.get("is_oneway", False)
                )
                graph.add_edge(edge)
            
            logger.info(f"JSON 가져오기 완료: {filepath}")
            return graph
        except Exception as e:
            logger.error(f"JSON 가져오기 실패: {e}")
            return None
