"""
경로 탐색 통합 모듈
가중치 샘플링, A* 탐색, Pareto 필터링을 통합
"""
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed


from src.domain.entities import Coordinate, RouteInfo
from src.data.entities import RoadGraph
from src.shape.transformer import ShapeTransformer
from src.algorithm.weight_sampler import WeightSampler, WeightVector
from src.algorithm.astar import AStarPathFinder, PathCandidate
from src.algorithm.pareto import ParetoFilter

logger = logging.getLogger(__name__)

@dataclass
class RouteSearchConfig:
    """
    경로 탐색 설정
    
    Attributes:
        n_weight_samples: 가중치 샘플 개수
        n_rotations: 도형 회전 개수
        max_iterations: A* 최대 반복 횟수
        max_results: 최대 결과 개수
        use_parallel: 병렬 처리 사용 여부
        max_workers: 병렬 처리 워커 수
    """
    n_weight_samples: int = 20
    n_rotations: int = 6
    max_iterations: int = 10000
    max_results: int = 5
    use_parallel: bool = True
    max_workers: int = 4


class RouteFinder:
    """
    경로 탐색기
    
    다양한 가중치와 도형 회전을 조합하여
    최적의 러닝 코스를 탐색
    """
    
    def __init__(
        self,
        graph: RoadGraph,
        config: RouteSearchConfig = None
    ):
        """
        Args:
            graph: 도로 그래프
            config: 탐색 설정
        """
        self.graph = graph
        self.config = config or RouteSearchConfig()
        
        self.weight_sampler = WeightSampler()
        self.pareto_filter = ParetoFilter()
        self.transformer = ShapeTransformer()
    
    def find_routes(
        self,
        target_curve: List[Coordinate],
        target_distance_km: float,
        max_crossings: int,
        start_node_id: Optional[int] = None
    ) -> List[RouteInfo]:
        """
        최적 경로 탐색
        
        Args:
            target_curve: 목표 도형 좌표
            target_distance_km: 목표 거리 (km)
            max_crossings: 허용 최대 횡단보도 개수
            start_node_id: 시작 노드 ID (없으면 자동 선택)
            
        Returns:
            RouteInfo 목록 (최대 max_results개)
        """
        logger.info(f"경로 탐색 시작: 목표거리={target_distance_km}km, 최대횡단={max_crossings}")
        logger.info(f"그래프 정보: {self.graph.node_count}개 노드, {self.graph.edge_count}개 엣지")
        
        if not target_curve or len(target_curve) < 2:
            logger.warning("목표 도형이 비어있거나 점이 부족합니다")
            return []
        
        logger.info(f"목표 도형: {len(target_curve)}개 점")
        
        # 시작 노드 결정
        if start_node_id is None:
            start_node = self._find_start_node(target_curve)
            if not start_node:
                logger.warning("시작 노드를 찾을 수 없습니다")
                return []
            start_node_id = start_node
        
        logger.info(f"시작 노드: {start_node_id}")
        
        # 가중치 샘플링
        weights = self.weight_sampler.sample_with_corners(
            self.config.n_weight_samples - 4
        )
        logger.info(f"가중치 샘플: {len(weights)}개")
        
        # 도형 회전 생성
        rotated_curves = self._generate_rotated_curves(target_curve)
        logger.info(f"회전 변형: {len(rotated_curves)}개")
        
        # 모든 조합에 대해 경로 탐색
        all_candidates: List[PathCandidate] = []
        total_combinations = len(rotated_curves) * len(weights)
        logger.info(f"탐색할 조합 수: {total_combinations}개")
        
        if self.config.use_parallel:
            all_candidates = self._search_parallel(
                rotated_curves, weights, target_distance_km,
                max_crossings, start_node_id
            )
        else:
            all_candidates = self._search_sequential(
                rotated_curves, weights, target_distance_km,
                max_crossings, start_node_id
            )
        
        logger.info(f"A* 탐색 결과: {len(all_candidates)}개 후보 경로 발견")
        
        # Pareto 필터링
        top_candidates = self.pareto_filter.select_top_k(
            all_candidates, self.config.max_results
        )
        
        logger.info(f"Pareto 필터링 후: {len(top_candidates)}개 경로")
        
        # RouteInfo로 변환
        return self._to_route_infos(top_candidates)
    
    def _find_start_node(self, target_curve: List[Coordinate]) -> Optional[int]:
        """
        목표 곡선에서 시작점에 가장 가까운 교차로 노드 찾기
        
        순환 경로를 만들려면 이웃이 2개 이상인 노드(교차로)에서 시작해야 함
        """
        if not target_curve:
            return None
        
        start_coord = target_curve[0]
        
        # 이웃이 2개 이상인 노드(교차로) 중에서 가장 가까운 노드 찾기
        best_node = None
        best_distance = float('inf')
        
        for node in self.graph.nodes.values():
            neighbor_count = len(self.graph.get_neighbors(node.id))
            
            # 이웃이 2개 이상인 노드만 고려 (순환 경로 가능)
            if neighbor_count < 2:
                continue
            
            distance = node.distance_to_coord(start_coord.lat, start_coord.lng)
            if distance < best_distance:
                best_distance = distance
                best_node = node
        
        if best_node:
            logger.info(f"시작 노드 선택: {best_node.id} (이웃 {len(self.graph.get_neighbors(best_node.id))}개, 거리 {best_distance:.3f}km)")
            return best_node.id
        
        # 교차로가 없으면 가장 가까운 노드 사용 (fallback)
        logger.warning("교차로 노드를 찾을 수 없어 가장 가까운 노드 사용")
        nearest = self.graph.find_nearest_node(start_coord.lat, start_coord.lng)
        return nearest.id if nearest else None
    
    def _generate_rotated_curves(
        self,
        target_curve: List[Coordinate]
    ) -> List[List[Coordinate]]:
        """도형을 여러 각도로 회전"""
        # 좌표를 정규화 좌표로 변환
        center_lat = sum(c.lat for c in target_curve) / len(target_curve)
        center_lng = sum(c.lng for c in target_curve) / len(target_curve)
        
        # 간단한 변환 (위도/경도 -> x/y)
        normalized = [
            (c.lng - center_lng, c.lat - center_lat)
            for c in target_curve
        ]
        
        # 회전 각도
        angles = [0, 60, 120, 180, 240, 300][:self.config.n_rotations]
        
        rotated_curves = []
        for angle in angles:
            rotated = self.transformer.rotate(normalized, angle)
            # 다시 지리 좌표로 변환
            geo_coords = [
                Coordinate(lat=center_lat + y, lng=center_lng + x)
                for x, y in rotated
            ]
            rotated_curves.append(geo_coords)
        
        return rotated_curves
    
    def _search_sequential(
        self,
        rotated_curves: List[List[Coordinate]],
        weights: List[WeightVector],
        target_distance_km: float,
        max_crossings: int,
        start_node_id: int
    ) -> List[PathCandidate]:
        """순차 탐색"""
        candidates = []
        
        for curve in rotated_curves:
            for weight in weights:
                candidate = self._search_single(
                    curve, weight, target_distance_km,
                    max_crossings, start_node_id
                )
                if candidate:
                    candidates.append(candidate)
        
        return candidates
    
    def _search_parallel(
        self,
        rotated_curves: List[List[Coordinate]],
        weights: List[WeightVector],
        target_distance_km: float,
        max_crossings: int,
        start_node_id: int
    ) -> List[PathCandidate]:
        """병렬 탐색"""
        candidates = []
        
        # 작업 목록 생성
        tasks = [
            (curve, weight)
            for curve in rotated_curves
            for weight in weights
        ]
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(
                    self._search_single,
                    curve, weight, target_distance_km,
                    max_crossings, start_node_id
                ): (curve, weight)
                for curve, weight in tasks
            }
            
            for future in as_completed(futures):
                try:
                    candidate = future.result()
                    if candidate:
                        candidates.append(candidate)
                except Exception:
                    pass
        
        return candidates
    
    def _search_single(
        self,
        target_curve: List[Coordinate],
        weight: WeightVector,
        target_distance_km: float,
        max_crossings: int,
        start_node_id: int
    ) -> Optional[PathCandidate]:
        """단일 조합에 대한 경로 탐색"""
        pathfinder = AStarPathFinder(
            graph=self.graph,
            target_curve=target_curve,
            target_distance_km=target_distance_km,
            max_crossings=max_crossings,
            weights=weight.to_tuple()
        )
        
        return pathfinder.find_path(
            start_node_id=start_node_id,
            max_iterations=self.config.max_iterations
        )
    
    def _to_route_infos(
        self,
        candidates: List[PathCandidate]
    ) -> List[RouteInfo]:
        """PathCandidate를 RouteInfo로 변환"""
        route_infos = []
        
        for i, candidate in enumerate(candidates):
            # 노드 ID를 좌표로 변환
            coordinates = []
            for node_id in candidate.path:
                node = self.graph.get_node(node_id)
                if node:
                    coordinates.append(Coordinate(lat=node.lat, lng=node.lng))
            
            # 도형 유사도 계산 (shape_distance의 역수)
            shape_similarity = 1.0 / (1.0 + candidate.shape_distance)
            
            route_info = RouteInfo(
                route_id=i + 1,
                coordinates=coordinates,
                total_distance_km=candidate.path_length_km,
                traffic_light_count=candidate.traffic_light_count,
                shape_similarity=shape_similarity
            )
            route_infos.append(route_info)
        
        return route_infos
    
    def find_routes_with_details(
        self,
        target_curve: List[Coordinate],
        target_distance_km: float,
        max_crossings: int,
        start_node_id: Optional[int] = None
    ) -> Tuple[List[RouteInfo], List[PathCandidate]]:
        """
        상세 정보와 함께 경로 탐색
        
        Returns:
            (RouteInfo 목록, PathCandidate 목록) 튜플
        """
        if not target_curve or len(target_curve) < 2:
            return [], []
        
        if start_node_id is None:
            start_node = self._find_start_node(target_curve)
            if not start_node:
                return [], []
            start_node_id = start_node
        
        weights = self.weight_sampler.sample_with_corners(
            self.config.n_weight_samples - 4
        )
        
        rotated_curves = self._generate_rotated_curves(target_curve)
        
        if self.config.use_parallel:
            all_candidates = self._search_parallel(
                rotated_curves, weights, target_distance_km,
                max_crossings, start_node_id
            )
        else:
            all_candidates = self._search_sequential(
                rotated_curves, weights, target_distance_km,
                max_crossings, start_node_id
            )
        
        top_candidates = self.pareto_filter.select_top_k(
            all_candidates, self.config.max_results
        )
        
        route_infos = self._to_route_infos(top_candidates)
        
        return route_infos, top_candidates
