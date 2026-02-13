"""
도메인 엔티티 테스트
"""
import pytest
from src.domain.entities import (
    Coordinate, BoundingBox, Shape, ShapeType,
    Constraints, RouteInfo
)


class TestCoordinate:
    """Coordinate 엔티티 테스트"""
    
    def test_create_coordinate(self):
        """좌표 생성 테스트"""
        coord = Coordinate(lat=37.5665, lng=126.9780)
        
        assert coord.lat == 37.5665
        assert coord.lng == 126.9780
    
    def test_to_tuple(self):
        """튜플 변환 테스트"""
        coord = Coordinate(lat=37.5665, lng=126.9780)
        
        result = coord.to_tuple()
        
        assert result == (37.5665, 126.9780)


class TestBoundingBox:
    """BoundingBox 엔티티 테스트"""
    
    def test_create_bounding_box(self):
        """바운딩 박스 생성 테스트"""
        bbox = BoundingBox(north=37.58, south=37.55, east=127.00, west=126.96)
        
        assert bbox.north == 37.58
        assert bbox.south == 37.55
        assert bbox.east == 127.00
        assert bbox.west == 126.96
    
    def test_center(self):
        """중심 좌표 계산 테스트"""
        bbox = BoundingBox(north=37.58, south=37.55, east=127.00, west=126.96)
        
        center = bbox.center
        
        assert center.lat == pytest.approx(37.565, rel=1e-3)
        assert center.lng == pytest.approx(126.98, rel=1e-3)
    
    def test_contains_inside(self):
        """범위 내 좌표 포함 테스트"""
        bbox = BoundingBox(north=37.58, south=37.55, east=127.00, west=126.96)
        coord = Coordinate(lat=37.565, lng=126.98)
        
        assert bbox.contains(coord) is True
    
    def test_contains_outside(self):
        """범위 외 좌표 테스트"""
        bbox = BoundingBox(north=37.58, south=37.55, east=127.00, west=126.96)
        coord = Coordinate(lat=37.60, lng=126.98)  # 북쪽 범위 초과
        
        assert bbox.contains(coord) is False


class TestShape:
    """Shape 엔티티 테스트"""
    
    def test_create_template_shape(self):
        """템플릿 모양 생성 테스트"""
        shape = Shape(shape_type=ShapeType.HEART)
        
        assert shape.shape_type == ShapeType.HEART
        assert shape.points == []
        assert shape.is_custom is False
    
    def test_create_custom_shape(self):
        """사용자 정의 모양 생성 테스트"""
        points = [
            Coordinate(lat=37.56, lng=126.97),
            Coordinate(lat=37.57, lng=126.98),
            Coordinate(lat=37.56, lng=126.99),
        ]
        shape = Shape(shape_type=ShapeType.CUSTOM, points=points)
        
        assert shape.shape_type == ShapeType.CUSTOM
        assert len(shape.points) == 3
        assert shape.is_custom is True


class TestConstraints:
    """Constraints 엔티티 테스트"""
    
    def test_create_constraints(self):
        """제약 조건 생성 테스트"""
        constraints = Constraints(
            target_distance_km=5.0,
            max_traffic_lights=5
        )
        
        assert constraints.target_distance_km == 5.0
        assert constraints.max_traffic_lights == 5
        assert constraints.distance_tolerance == 0.1  # 기본값
    
    def test_custom_tolerance(self):
        """사용자 정의 허용 오차 테스트"""
        constraints = Constraints(
            target_distance_km=10.0,
            max_traffic_lights=3,
            distance_tolerance=0.15
        )
        
        assert constraints.distance_tolerance == 0.15


class TestRouteInfo:
    """RouteInfo 엔티티 테스트"""
    
    def test_create_route_info(self):
        """경로 정보 생성 테스트"""
        coords = [
            Coordinate(lat=37.56, lng=126.97),
            Coordinate(lat=37.57, lng=126.98),
        ]
        route = RouteInfo(
            route_id=1,
            coordinates=coords,
            total_distance_km=5.2,
            traffic_light_count=3,
            shape_similarity=0.85
        )
        
        assert route.route_id == 1
        assert len(route.coordinates) == 2
        assert route.total_distance_km == 5.2
        assert route.traffic_light_count == 3
        assert route.shape_similarity == 0.85
    
    def test_display_name(self):
        """표시 이름 테스트"""
        route = RouteInfo(
            route_id=3,
            coordinates=[],
            total_distance_km=5.0,
            traffic_light_count=2,
            shape_similarity=0.9
        )
        
        assert route.display_name == "경로 3"
