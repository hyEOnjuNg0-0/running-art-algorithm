"""
Mock 데이터
Phase 1 UI 테스트용 더미 데이터
"""
from typing import List
from src.domain.entities import RouteInfo, Coordinate


def generate_mock_routes(center_lat: float = 37.5665, center_lng: float = 126.9780) -> List[RouteInfo]:
    """
    테스트용 Mock 경로 데이터 생성
    
    Args:
        center_lat: 중심 위도
        center_lng: 중심 경도
    
    Returns:
        Mock 경로 목록 (최대 5개)
    """
    routes = []
    
    # 경로 1: 하트 모양 (높은 유사도)
    route1_coords = _generate_heart_coords(center_lat, center_lng, scale=0.01)
    routes.append(RouteInfo(
        route_id=1,
        coordinates=route1_coords,
        total_distance_km=5.2,
        traffic_light_count=3,
        shape_similarity=0.92,
    ))
    
    # 경로 2: 약간 변형된 하트
    route2_coords = _generate_heart_coords(center_lat + 0.002, center_lng + 0.002, scale=0.012)
    routes.append(RouteInfo(
        route_id=2,
        coordinates=route2_coords,
        total_distance_km=5.8,
        traffic_light_count=4,
        shape_similarity=0.85,
    ))
    
    # 경로 3: 원형에 가까운 경로
    route3_coords = _generate_circle_coords(center_lat - 0.003, center_lng + 0.001, radius=0.008)
    routes.append(RouteInfo(
        route_id=3,
        coordinates=route3_coords,
        total_distance_km=4.5,
        traffic_light_count=2,
        shape_similarity=0.72,
    ))
    
    # 경로 4: 다른 변형
    route4_coords = _generate_heart_coords(center_lat + 0.001, center_lng - 0.003, scale=0.009)
    routes.append(RouteInfo(
        route_id=4,
        coordinates=route4_coords,
        total_distance_km=4.8,
        traffic_light_count=5,
        shape_similarity=0.78,
    ))
    
    # 경로 5: 가장 짧은 경로
    route5_coords = _generate_circle_coords(center_lat - 0.001, center_lng - 0.002, radius=0.006)
    routes.append(RouteInfo(
        route_id=5,
        coordinates=route5_coords,
        total_distance_km=3.9,
        traffic_light_count=1,
        shape_similarity=0.65,
    ))
    
    return routes


def _generate_heart_coords(center_lat: float, center_lng: float, scale: float = 0.01) -> List[Coordinate]:
    """하트 모양 좌표 생성"""
    import math
    
    coords = []
    # 파라메트릭 하트 방정식
    for t in range(0, 360, 10):
        rad = math.radians(t)
        # 하트 방정식
        x = 16 * (math.sin(rad) ** 3)
        y = 13 * math.cos(rad) - 5 * math.cos(2 * rad) - 2 * math.cos(3 * rad) - math.cos(4 * rad)
        
        # 스케일 조정 및 중심 이동
        lat = center_lat + (y / 16) * scale
        lng = center_lng + (x / 16) * scale
        
        coords.append(Coordinate(lat=lat, lng=lng))
    
    # 시작점으로 돌아오기
    if coords:
        coords.append(coords[0])
    
    return coords


def _generate_circle_coords(center_lat: float, center_lng: float, radius: float = 0.01) -> List[Coordinate]:
    """원형 좌표 생성"""
    import math
    
    coords = []
    for t in range(0, 360, 10):
        rad = math.radians(t)
        lat = center_lat + radius * math.cos(rad)
        lng = center_lng + radius * math.sin(rad)
        coords.append(Coordinate(lat=lat, lng=lng))
    
    # 시작점으로 돌아오기
    if coords:
        coords.append(coords[0])
    
    return coords


def generate_mock_search_result():
    """Mock 검색 결과 생성"""
    from src.domain.entities import SearchResult, BoundingBox, Shape, ShapeType, Constraints
    
    return SearchResult(
        routes=generate_mock_routes(),
        search_area=BoundingBox(
            north=37.58,
            south=37.55,
            east=127.00,
            west=126.96,
        ),
        target_shape=Shape(shape_type=ShapeType.HEART),
        constraints=Constraints(
            target_distance_km=5.0,
            max_traffic_lights=5,
        ),
    )
