"""
도메인 엔티티 정의
러닝 코스 추천 시스템의 핵심 데이터 구조
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum


class ShapeType(Enum):
    """미리 정의된 도형 템플릿 타입"""
    HEART = "heart"
    CIRCLE = "circle"
    SQUARE = "square"
    TRIANGLE = "triangle"
    STAR = "star"
    CUSTOM = "custom"  # 사용자 직접 그리기


@dataclass
class Coordinate:
    """위도/경도 좌표"""
    lat: float  # 위도
    lng: float  # 경도
    
    def to_tuple(self) -> Tuple[float, float]:
        return (self.lat, self.lng)


@dataclass
class BoundingBox:
    """지도 범위를 나타내는 사각형 영역"""
    north: float  # 북쪽 위도 (최대)
    south: float  # 남쪽 위도 (최소)
    east: float   # 동쪽 경도 (최대)
    west: float   # 서쪽 경도 (최소)
    
    @property
    def center(self) -> Coordinate:
        """중심 좌표 반환"""
        return Coordinate(
            lat=(self.north + self.south) / 2,
            lng=(self.east + self.west) / 2
        )
    
    def contains(self, coord: Coordinate) -> bool:
        """좌표가 범위 내에 있는지 확인"""
        return (self.south <= coord.lat <= self.north and
                self.west <= coord.lng <= self.east)


@dataclass
class Shape:
    """사용자가 선택한 모양"""
    shape_type: ShapeType
    points: List[Coordinate] = field(default_factory=list)  # 사용자 정의 시 좌표점 목록
    
    @property
    def is_custom(self) -> bool:
        return self.shape_type == ShapeType.CUSTOM


@dataclass
class Constraints:
    """경로 제약 조건"""
    target_distance_km: float  # 목표 거리 (km)
    max_traffic_lights: int    # 허용 최대 신호등 개수
    distance_tolerance: float = 0.1  # 거리 허용 오차 (기본 10%)


@dataclass
class RouteInfo:
    """경로 정보"""
    route_id: int
    coordinates: List[Coordinate]  # 경로 좌표 목록
    total_distance_km: float       # 총 거리
    traffic_light_count: int       # 신호등/횡단보도 수
    shape_similarity: float        # 도형 유사도 점수 (0~1)
    
    @property
    def display_name(self) -> str:
        return f"경로 {self.route_id}"


@dataclass
class SearchResult:
    """경로 탐색 결과"""
    routes: List[RouteInfo]
    search_area: BoundingBox
    target_shape: Shape
    constraints: Constraints
