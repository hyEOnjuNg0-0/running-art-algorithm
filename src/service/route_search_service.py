"""
경로 탐색 서비스
UI → 데이터 → 알고리즘 → 결과 파이프라인 통합
"""
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Callable
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future

from src.domain.entities import (
    BoundingBox, Shape, ShapeType, Constraints, 
    RouteInfo, Coordinate, SearchResult
)
from src.data.entities import RoadGraph
from src.data.osm_repository import OSMGraphRepository
from src.data.repository import GraphFetchError
from src.data.cache_service import GraphCacheService
from src.shape.processor import ShapeProcessor
from src.algorithm.route_finder import RouteFinder, RouteSearchConfig


logger = logging.getLogger(__name__)


class SearchStatus(Enum):
    """탐색 상태"""
    IDLE = "idle"
    LOADING_DATA = "loading_data"
    PROCESSING_SHAPE = "processing_shape"
    SEARCHING_ROUTES = "searching_routes"
    FILTERING_RESULTS = "filtering_results"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SearchRequest:
    """
    경로 탐색 요청
    
    Attributes:
        bounding_box: 탐색 영역
        shape: 목표 도형
        constraints: 제약 조건
        start_point: 시작점 (선택)
    """
    bounding_box: BoundingBox
    shape: Shape
    constraints: Constraints
    start_point: Optional[Coordinate] = None


@dataclass
class SearchResponse:
    """
    경로 탐색 응답
    
    Attributes:
        routes: 탐색된 경로 목록
        status: 탐색 상태
        error_message: 에러 메시지 (있는 경우)
        search_area: 탐색 영역
        target_shape: 목표 도형
    """
    routes: List[RouteInfo] = field(default_factory=list)
    status: SearchStatus = SearchStatus.IDLE
    error_message: Optional[str] = None
    search_area: Optional[BoundingBox] = None
    target_shape: Optional[Shape] = None


class RouteSearchService:
    """
    경로 탐색 서비스
    
    전체 파이프라인을 통합하여 경로 탐색 수행
    """
    
    def __init__(
        self,
        use_cache: bool = True,
        cache_dir: str = ".cache/graphs"
    ):
        """
        Args:
            use_cache: 그래프 캐싱 사용 여부
            cache_dir: 캐시 디렉토리
        """
        self.repository = OSMGraphRepository()
        self.shape_processor = ShapeProcessor()
        self.use_cache = use_cache
        
        if use_cache:
            self.cache_service = GraphCacheService(cache_dir)
        else:
            self.cache_service = None
        
        self._current_status = SearchStatus.IDLE
        self._progress_callback: Optional[Callable[[SearchStatus, float], None]] = None
    
    def search(
        self,
        request: SearchRequest,
        progress_callback: Optional[Callable[[SearchStatus, float], None]] = None
    ) -> SearchResponse:
        """
        경로 탐색 수행
        
        Args:
            request: 탐색 요청
            progress_callback: 진행 상황 콜백 (status, progress 0~1)
            
        Returns:
            탐색 응답
        """
        self._progress_callback = progress_callback
        
        try:
            # 1. 데이터 로딩
            self._update_status(SearchStatus.LOADING_DATA, 0.0)
            graph = self._load_graph(request.bounding_box)
            self._update_status(SearchStatus.LOADING_DATA, 0.2)
            
            if graph.node_count == 0:
                return SearchResponse(
                    status=SearchStatus.ERROR,
                    error_message="선택한 영역에 도로 데이터가 없습니다"
                )
            
            # 2. 도형 처리
            self._update_status(SearchStatus.PROCESSING_SHAPE, 0.3)
            target_curve = self._process_shape(request.shape, request.bounding_box)
            self._update_status(SearchStatus.PROCESSING_SHAPE, 0.4)
            
            if len(target_curve) < 2:
                return SearchResponse(
                    status=SearchStatus.ERROR,
                    error_message="도형 처리에 실패했습니다"
                )
            
            # 3. 시작점 결정
            start_node_id = self._find_start_node(
                graph, target_curve, request.start_point
            )
            
            # 4. 경로 탐색
            self._update_status(SearchStatus.SEARCHING_ROUTES, 0.5)
            routes = self._search_routes(
                graph=graph,
                target_curve=target_curve,
                constraints=request.constraints,
                start_node_id=start_node_id
            )
            self._update_status(SearchStatus.SEARCHING_ROUTES, 0.9)
            
            # 5. 결과 정리
            self._update_status(SearchStatus.FILTERING_RESULTS, 0.95)
            
            # 6. 완료
            self._update_status(SearchStatus.COMPLETED, 1.0)
            
            return SearchResponse(
                routes=routes,
                status=SearchStatus.COMPLETED,
                search_area=request.bounding_box,
                target_shape=request.shape
            )
            
        except GraphFetchError as e:
            logger.error(f"그래프 로딩 실패: {e}")
            return SearchResponse(
                status=SearchStatus.ERROR,
                error_message=f"지도 데이터 로딩 실패: {str(e)}"
            )
        except Exception as e:
            logger.error(f"경로 탐색 실패: {e}")
            return SearchResponse(
                status=SearchStatus.ERROR,
                error_message=f"경로 탐색 중 오류 발생: {str(e)}"
            )
    
    def search_async(
        self,
        request: SearchRequest,
        progress_callback: Optional[Callable[[SearchStatus, float], None]] = None
    ) -> Future[SearchResponse]:
        """
        비동기 경로 탐색
        
        Args:
            request: 탐색 요청
            progress_callback: 진행 상황 콜백
            
        Returns:
            Future[SearchResponse]
        """
        executor = ThreadPoolExecutor(max_workers=1)
        return executor.submit(self.search, request, progress_callback)
    
    def _load_graph(self, bbox: BoundingBox, expand_ratio: float = 0.2) -> RoadGraph:
        """
        그래프 로딩 (캐시 우선)
        
        Args:
            bbox: 기본 탐색 영역
            expand_ratio: 영역 확장 비율 (기본 20%)
            
        Returns:
            확장된 영역의 도로 그래프
        """
        # 영역 확장 (경계 근처의 더 좋은 경로를 찾기 위해)
        expanded_bbox = bbox.expand(expand_ratio)
        logger.info(f"그래프 로딩 영역 확장: {expand_ratio*100:.0f}% 마진 적용")
        
        # 캐시 확인 (확장된 영역 기준)
        if self.use_cache and self.cache_service:
            cache_key = self.cache_service.get_cache_key(bbox=expanded_bbox)
            cached = self.cache_service.get(cache_key)
            if cached:
                logger.info("캐시에서 그래프 로딩")
                return cached
        
        # OSM에서 로딩
        logger.info("OSM에서 그래프 로딩")
        graph = self.repository.get_graph_by_bbox(expanded_bbox, network_type="walk")
        
        # 캐시 저장
        if self.use_cache and self.cache_service:
            self.cache_service.set(cache_key, graph)
        
        return graph
    
    def _process_shape(
        self,
        shape: Shape,
        bbox: BoundingBox
    ) -> List[Coordinate]:
        """도형 처리 및 지리 좌표 변환"""
        if shape.is_custom:
            # 사용자 정의 도형
            if not shape.points:
                return []
            
            # 정규화된 좌표를 지리 좌표로 변환
            processed = self.shape_processor.process_user_input(shape.points)
            
            # 좌표가 정규화된 형태인지 확인 (0~1 범위)
            if processed and all(0 <= p.lat <= 1 and 0 <= p.lng <= 1 for p in processed):
                # 정규화 좌표를 지리 좌표로 변환
                normalized = [(p.lng, p.lat) for p in processed]
                return self.shape_processor.transformer.normalize_to_geo(normalized, bbox)
            
            return processed
        else:
            # 템플릿 도형
            return self.shape_processor.template_to_geo(shape.shape_type, bbox)
    
    def _find_start_node(
        self,
        graph: RoadGraph,
        target_curve: List[Coordinate],
        start_point: Optional[Coordinate]
    ) -> Optional[int]:
        """시작 노드 결정"""
        if start_point:
            # 사용자 지정 시작점
            nearest = graph.find_nearest_node(start_point.lat, start_point.lng)
            return nearest.id if nearest else None
        
        if target_curve:
            # 도형의 첫 번째 점에서 가장 가까운 노드
            first_point = target_curve[0]
            nearest = graph.find_nearest_node(first_point.lat, first_point.lng)
            return nearest.id if nearest else None
        
        return None
    
    def _search_routes(
        self,
        graph: RoadGraph,
        target_curve: List[Coordinate],
        constraints: Constraints,
        start_node_id: Optional[int]
    ) -> List[RouteInfo]:
        """경로 탐색 수행"""
        config = RouteSearchConfig(
            n_weight_samples=20,
            n_rotations=6,
            max_iterations=10000,
            max_results=5,
            use_parallel=True,
            max_workers=4
        )
        
        finder = RouteFinder(graph=graph, config=config)
        
        routes = finder.find_routes(
            target_curve=target_curve,
            target_distance_km=constraints.target_distance_km,
            max_crossings=constraints.max_traffic_lights,
            start_node_id=start_node_id
        )
        
        return routes
    
    def _update_status(self, status: SearchStatus, progress: float):
        """상태 업데이트 및 콜백 호출"""
        self._current_status = status
        if self._progress_callback:
            self._progress_callback(status, progress)
    
    @property
    def current_status(self) -> SearchStatus:
        """현재 상태 반환"""
        return self._current_status


def create_search_request(
    bbox_dict: dict,
    shape_type: str,
    custom_points: List[dict],
    target_distance: float,
    max_traffic_lights: int
) -> SearchRequest:
    """
    UI 입력에서 SearchRequest 생성
    
    Args:
        bbox_dict: 바운딩 박스 딕셔너리 (north, south, east, west)
        shape_type: 도형 타입 문자열
        custom_points: 사용자 정의 점 목록
        target_distance: 목표 거리 (km)
        max_traffic_lights: 최대 신호등 수
        
    Returns:
        SearchRequest 객체
    """
    # BoundingBox 생성
    bbox = BoundingBox(
        north=bbox_dict['north'],
        south=bbox_dict['south'],
        east=bbox_dict['east'],
        west=bbox_dict['west']
    )
    
    # Shape 생성
    shape_type_enum = ShapeType(shape_type)
    points = []
    
    if shape_type_enum == ShapeType.CUSTOM and custom_points:
        points = [
            Coordinate(lat=p.get('y', 0), lng=p.get('x', 0))
            for p in custom_points
        ]
    
    shape = Shape(shape_type=shape_type_enum, points=points)
    
    # Constraints 생성
    constraints = Constraints(
        target_distance_km=target_distance,
        max_traffic_lights=max_traffic_lights
    )
    
    return SearchRequest(
        bounding_box=bbox,
        shape=shape,
        constraints=constraints
    )
