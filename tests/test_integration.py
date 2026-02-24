"""
통합 테스트
전체 파이프라인 테스트
"""
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock

from src.domain.entities import (
    BoundingBox, Shape, ShapeType, Constraints, 
    Coordinate, RouteInfo
)
from src.data.entities import Node, Edge, RoadGraph
from src.shape.processor import ShapeProcessor
from src.algorithm.route_finder import RouteFinder, RouteSearchConfig

# osmnx가 없을 경우를 대비한 조건부 import
try:
    from src.service.route_search_service import (
        RouteSearchService, SearchRequest, SearchResponse, 
        SearchStatus, create_search_request
    )
    HAS_OSMNX = True
except ImportError:
    HAS_OSMNX = False
    
    # Mock 클래스 정의
    class SearchStatus:
        IDLE = "idle"
        LOADING_DATA = "loading_data"
        PROCESSING_SHAPE = "processing_shape"
        SEARCHING_ROUTES = "searching_routes"
        FILTERING_RESULTS = "filtering_results"
        COMPLETED = "completed"
        ERROR = "error"


@pytest.mark.skipif(not HAS_OSMNX, reason="osmnx not installed")
class TestSearchRequest:
    """SearchRequest 생성 테스트"""
    
    def test_create_search_request_with_template(self):
        """템플릿 도형으로 요청 생성"""
        bbox_dict = {
            'north': 37.57,
            'south': 37.56,
            'east': 127.01,
            'west': 127.0
        }
        
        request = create_search_request(
            bbox_dict=bbox_dict,
            shape_type='heart',
            custom_points=[],
            target_distance=5.0,
            max_traffic_lights=3
        )
        
        assert request.bounding_box.north == 37.57
        assert request.bounding_box.south == 37.56
        assert request.shape.shape_type == ShapeType.HEART
        assert not request.shape.is_custom
        assert request.constraints.target_distance_km == 5.0
        assert request.constraints.max_traffic_lights == 3
    
    def test_create_search_request_with_custom_shape(self):
        """사용자 정의 도형으로 요청 생성"""
        bbox_dict = {
            'north': 37.57,
            'south': 37.56,
            'east': 127.01,
            'west': 127.0
        }
        
        custom_points = [
            {'x': 0.1, 'y': 0.1},
            {'x': 0.9, 'y': 0.1},
            {'x': 0.5, 'y': 0.9},
        ]
        
        request = create_search_request(
            bbox_dict=bbox_dict,
            shape_type='custom',
            custom_points=custom_points,
            target_distance=10.0,
            max_traffic_lights=5
        )
        
        assert request.shape.shape_type == ShapeType.CUSTOM
        assert request.shape.is_custom
        assert len(request.shape.points) == 3
        assert request.constraints.target_distance_km == 10.0


@pytest.mark.skipif(not HAS_OSMNX, reason="osmnx not installed")
class TestRouteSearchService:
    """RouteSearchService 테스트"""
    
    @pytest.fixture
    def mock_graph(self):
        """테스트용 Mock 그래프"""
        graph = RoadGraph()
        
        # 간단한 격자 그래프 생성
        for i in range(5):
            for j in range(5):
                node_id = i * 5 + j + 1
                lat = 37.56 + i * 0.002
                lng = 127.0 + j * 0.002
                graph.add_node(Node(
                    id=node_id, lat=lat, lng=lng,
                    has_traffic_light=(i + j) % 3 == 0
                ))
        
        edge_id = 1
        for i in range(5):
            for j in range(5):
                current = i * 5 + j + 1
                if j < 4:
                    graph.add_edge(Edge(
                        id=edge_id, source_id=current, 
                        target_id=current + 1, length_m=200
                    ))
                    edge_id += 1
                if i < 4:
                    graph.add_edge(Edge(
                        id=edge_id, source_id=current,
                        target_id=current + 5, length_m=200
                    ))
                    edge_id += 1
        
        return graph
    
    def test_service_initialization(self):
        """서비스 초기화 테스트"""
        service = RouteSearchService(use_cache=False)
        
        assert service.current_status == SearchStatus.IDLE
        assert service.repository is not None
        assert service.shape_processor is not None
    
    def test_service_with_cache(self):
        """캐시 사용 서비스 테스트"""
        service = RouteSearchService(use_cache=True, cache_dir=".test_cache")
        
        assert service.cache_service is not None
    
    @patch('src.service.route_search_service.OSMGraphRepository')
    def test_search_with_mock_repository(self, mock_repo_class, mock_graph):
        """Mock Repository로 검색 테스트"""
        # Repository Mock 설정
        mock_repo = MagicMock()
        mock_repo.get_graph_by_bbox.return_value = mock_graph
        mock_repo_class.return_value = mock_repo
        
        service = RouteSearchService(use_cache=False)
        service.repository = mock_repo
        
        request = SearchRequest(
            bounding_box=BoundingBox(
                north=37.57, south=37.56, east=127.01, west=127.0
            ),
            shape=Shape(shape_type=ShapeType.CIRCLE),
            constraints=Constraints(target_distance_km=1.0, max_traffic_lights=5)
        )
        
        response = service.search(request)
        
        # 응답 검증
        assert response.status in [SearchStatus.COMPLETED, SearchStatus.ERROR]
        assert response.search_area == request.bounding_box
    
    def test_search_with_empty_graph(self):
        """빈 그래프로 검색 테스트"""
        service = RouteSearchService(use_cache=False)
        
        # 빈 그래프 반환하도록 Mock
        empty_graph = RoadGraph()
        service.repository = MagicMock()
        service.repository.get_graph_by_bbox.return_value = empty_graph
        
        request = SearchRequest(
            bounding_box=BoundingBox(
                north=37.57, south=37.56, east=127.01, west=127.0
            ),
            shape=Shape(shape_type=ShapeType.HEART),
            constraints=Constraints(target_distance_km=5.0, max_traffic_lights=3)
        )
        
        response = service.search(request)
        
        assert response.status == SearchStatus.ERROR
        assert "도로 데이터가 없습니다" in response.error_message
    
    def test_progress_callback(self, mock_graph):
        """진행 상황 콜백 테스트"""
        service = RouteSearchService(use_cache=False)
        service.repository = MagicMock()
        service.repository.get_graph_by_bbox.return_value = mock_graph
        
        progress_updates = []
        
        def callback(status, progress):
            progress_updates.append((status, progress))
        
        request = SearchRequest(
            bounding_box=BoundingBox(
                north=37.57, south=37.56, east=127.01, west=127.0
            ),
            shape=Shape(shape_type=ShapeType.CIRCLE),
            constraints=Constraints(target_distance_km=1.0, max_traffic_lights=5)
        )
        
        service.search(request, progress_callback=callback)
        
        # 콜백이 호출되었는지 확인
        assert len(progress_updates) > 0
        
        # 진행률이 증가하는지 확인
        progresses = [p[1] for p in progress_updates]
        assert progresses[-1] >= progresses[0]


class TestShapeProcessorIntegration:
    """ShapeProcessor 통합 테스트"""
    
    def test_template_to_geo_circle(self):
        """원 템플릿 변환 테스트"""
        processor = ShapeProcessor()
        bbox = BoundingBox(north=37.57, south=37.56, east=127.01, west=127.0)
        
        coords = processor.template_to_geo(ShapeType.CIRCLE, bbox)
        
        assert len(coords) > 0
        # 모든 좌표가 bbox 내에 있는지 확인
        for coord in coords:
            assert bbox.south <= coord.lat <= bbox.north
            assert bbox.west <= coord.lng <= bbox.east
    
    def test_template_to_geo_heart(self):
        """하트 템플릿 변환 테스트"""
        processor = ShapeProcessor()
        bbox = BoundingBox(north=37.57, south=37.56, east=127.01, west=127.0)
        
        coords = processor.template_to_geo(ShapeType.HEART, bbox)
        
        assert len(coords) > 0
    
    def test_generate_all_rotations(self):
        """모든 회전 변형 생성 테스트"""
        processor = ShapeProcessor()
        bbox = BoundingBox(north=37.57, south=37.56, east=127.01, west=127.0)
        
        rotations = processor.generate_all_rotations(ShapeType.STAR, bbox)
        
        assert len(rotations) == 6  # 6방향 회전
        for rotation in rotations:
            assert len(rotation) > 0
    
    def test_process_user_input(self):
        """사용자 입력 처리 테스트"""
        processor = ShapeProcessor()
        
        # 사용자가 그린 점들 (중복 포함)
        points = [
            Coordinate(lat=37.56, lng=127.0),
            Coordinate(lat=37.56, lng=127.0),  # 중복
            Coordinate(lat=37.565, lng=127.005),
            Coordinate(lat=37.57, lng=127.01),
        ]
        
        processed = processor.process_user_input(points)
        
        # 중복이 제거되었는지 확인
        assert len(processed) < len(points)


class TestRouteFinderIntegration:
    """RouteFinder 통합 테스트"""
    
    @pytest.fixture
    def test_graph(self):
        """테스트용 그래프"""
        graph = RoadGraph()
        
        # 원형 그래프 생성
        import math
        center_lat, center_lng = 37.565, 127.005
        radius = 0.005
        n_points = 16
        
        for i in range(n_points):
            angle = 2 * math.pi * i / n_points
            lat = center_lat + radius * math.sin(angle)
            lng = center_lng + radius * math.cos(angle)
            graph.add_node(Node(
                id=i + 1, lat=lat, lng=lng,
                has_traffic_light=(i % 4 == 0)
            ))
        
        # 원형 엣지
        for i in range(n_points):
            next_i = (i + 1) % n_points
            graph.add_edge(Edge(
                id=i + 1, source_id=i + 1, target_id=next_i + 1,
                length_m=300
            ))
        
        return graph
    
    def test_route_finder_with_circle_shape(self, test_graph):
        """원형 도형으로 경로 탐색"""
        processor = ShapeProcessor()
        bbox = BoundingBox(north=37.57, south=37.56, east=127.01, west=127.0)
        
        target_curve = processor.template_to_geo(ShapeType.CIRCLE, bbox)
        
        config = RouteSearchConfig(
            n_weight_samples=5,
            n_rotations=2,
            max_iterations=1000,
            max_results=3,
            use_parallel=False
        )
        
        finder = RouteFinder(graph=test_graph, config=config)
        
        routes = finder.find_routes(
            target_curve=target_curve,
            target_distance_km=2.0,
            max_crossings=5
        )
        
        # 결과 검증 (경로가 없을 수도 있음)
        for route in routes:
            assert route.route_id > 0
            assert len(route.coordinates) >= 2


@pytest.mark.skipif(not HAS_OSMNX, reason="osmnx not installed")
class TestEndToEndPipeline:
    """End-to-End 파이프라인 테스트"""
    
    @pytest.fixture
    def complete_graph(self):
        """완전한 테스트 그래프"""
        graph = RoadGraph()
        
        # 10x10 격자 그래프
        for i in range(10):
            for j in range(10):
                node_id = i * 10 + j + 1
                lat = 37.56 + i * 0.001
                lng = 127.0 + j * 0.001
                graph.add_node(Node(
                    id=node_id, lat=lat, lng=lng,
                    has_traffic_light=(i + j) % 5 == 0
                ))
        
        edge_id = 1
        for i in range(10):
            for j in range(10):
                current = i * 10 + j + 1
                if j < 9:
                    graph.add_edge(Edge(
                        id=edge_id, source_id=current,
                        target_id=current + 1, length_m=100
                    ))
                    edge_id += 1
                if i < 9:
                    graph.add_edge(Edge(
                        id=edge_id, source_id=current,
                        target_id=current + 10, length_m=100
                    ))
                    edge_id += 1
        
        return graph
    
    def test_full_pipeline_with_mock_data(self, complete_graph):
        """전체 파이프라인 테스트 (Mock 데이터)"""
        # 1. 요청 생성
        bbox_dict = {
            'north': 37.57,
            'south': 37.56,
            'east': 127.01,
            'west': 127.0
        }
        
        request = create_search_request(
            bbox_dict=bbox_dict,
            shape_type='circle',
            custom_points=[],
            target_distance=0.5,
            max_traffic_lights=10
        )
        
        # 2. 서비스 생성 및 Mock 설정
        service = RouteSearchService(use_cache=False)
        service.repository = MagicMock()
        service.repository.get_graph_by_bbox.return_value = complete_graph
        
        # 3. 검색 수행
        response = service.search(request)
        
        # 4. 결과 검증
        assert response.status in [SearchStatus.COMPLETED, SearchStatus.ERROR]
        
        if response.status == SearchStatus.COMPLETED:
            # 경로가 있으면 검증
            for route in response.routes:
                assert isinstance(route, RouteInfo)
                assert route.total_distance_km > 0
    
    def test_pipeline_with_custom_shape(self, complete_graph):
        """사용자 정의 도형으로 파이프라인 테스트"""
        # 삼각형 모양의 사용자 정의 점
        custom_points = [
            {'x': 0.5, 'y': 0.1},
            {'x': 0.9, 'y': 0.9},
            {'x': 0.1, 'y': 0.9},
            {'x': 0.5, 'y': 0.1},  # 닫힌 도형
        ]
        
        bbox_dict = {
            'north': 37.57,
            'south': 37.56,
            'east': 127.01,
            'west': 127.0
        }
        
        request = create_search_request(
            bbox_dict=bbox_dict,
            shape_type='custom',
            custom_points=custom_points,
            target_distance=0.5,
            max_traffic_lights=5
        )
        
        service = RouteSearchService(use_cache=False)
        service.repository = MagicMock()
        service.repository.get_graph_by_bbox.return_value = complete_graph
        
        response = service.search(request)
        
        assert response.status in [SearchStatus.COMPLETED, SearchStatus.ERROR]


class TestEdgeCases:
    """엣지 케이스 테스트"""
    
    @pytest.mark.skipif(not HAS_OSMNX, reason="osmnx not installed")
    def test_very_small_bounding_box(self):
        """매우 작은 바운딩 박스"""
        service = RouteSearchService(use_cache=False)
        
        # 매우 작은 영역
        small_graph = RoadGraph()
        small_graph.add_node(Node(id=1, lat=37.565, lng=127.005))
        
        service.repository = MagicMock()
        service.repository.get_graph_by_bbox.return_value = small_graph
        
        request = SearchRequest(
            bounding_box=BoundingBox(
                north=37.5651, south=37.5650, east=127.0051, west=127.0050
            ),
            shape=Shape(shape_type=ShapeType.CIRCLE),
            constraints=Constraints(target_distance_km=5.0, max_traffic_lights=3)
        )
        
        response = service.search(request)
        
        # 노드가 1개뿐이므로 경로를 찾을 수 없음
        assert response.status == SearchStatus.ERROR or len(response.routes) == 0
    
    def test_zero_target_distance(self):
        """목표 거리가 0인 경우"""
        # 0 거리는 허용되지 않아야 함
        with pytest.raises(ValueError):
            Constraints(target_distance_km=0.0, max_traffic_lights=5)
    
    def test_negative_traffic_lights(self):
        """음수 신호등 개수"""
        # 음수 신호등은 허용되지 않아야 함
        with pytest.raises(ValueError):
            Constraints(target_distance_km=5.0, max_traffic_lights=-1)
