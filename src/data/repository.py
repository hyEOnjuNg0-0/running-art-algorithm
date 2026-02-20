"""
그래프 Repository 인터페이스 정의
Clean Architecture의 Repository 패턴 적용
"""
from abc import ABC, abstractmethod
from typing import Optional

from src.data.entities import RoadGraph
from src.domain.entities import BoundingBox


class GraphRepository(ABC):
    """
    도로 네트워크 그래프 Repository 인터페이스
    
    외부 데이터 소스(OSM 등)에서 도로 네트워크를 가져오는 추상 인터페이스
    """
    
    @abstractmethod
    def get_graph_by_bbox(
        self,
        bbox: BoundingBox,
        network_type: str = "walk"
    ) -> RoadGraph:
        """
        바운딩 박스 영역의 도로 네트워크 그래프 반환
        
        Args:
            bbox: 영역 범위 (BoundingBox)
            network_type: 네트워크 타입 ("walk", "bike", "drive" 등)
            
        Returns:
            도로 네트워크 그래프
            
        Raises:
            GraphFetchError: 그래프 로딩 실패 시
        """
        pass
    
    @abstractmethod
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
            
        Raises:
            GraphFetchError: 그래프 로딩 실패 시
        """
        pass


class GraphFetchError(Exception):
    """그래프 데이터 로딩 실패 예외"""
    pass
