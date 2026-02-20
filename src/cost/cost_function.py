"""
비용 함수 구현
경로 평가를 위한 ShapeDistance, LengthPenalty, CrossingPenalty 계산
"""
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional

from src.domain.entities import Coordinate
from src.data.entities import Node, Edge, RoadGraph


@dataclass
class CostResult:
    """
    비용 계산 결과
    
    Attributes:
        shape_distance: 도형 거리 비용 (정규화)
        length_penalty: 길이 페널티 (정규화)
        crossing_penalty: 횡단보도 페널티 (정규화)
        total_cost: 가중치 적용된 총 비용
        path_length_km: 실제 경로 길이 (km)
        traffic_light_count: 신호등 개수
    """
    shape_distance: float
    length_penalty: float
    crossing_penalty: float
    total_cost: float
    path_length_km: float
    traffic_light_count: int


class ShapeDistanceCalculator:
    """
    Edge-Curve 거리 계산기
    
    각 엣지를 샘플링하여 목표 곡선과의 거리를 계산
    """
    
    def __init__(self, target_curve: List[Coordinate], target_distance_km: float):
        """
        Args:
            target_curve: 목표 도형 좌표 목록
            target_distance_km: 목표 거리 (정규화용)
        """
        if not target_curve or len(target_curve) < 2:
            raise ValueError("목표 곡선은 최소 2개 이상의 점이 필요합니다")
        if target_distance_km <= 0:
            raise ValueError("목표 거리는 양수여야 합니다")
        
        self.target_curve = target_curve
        self.target_distance_km = target_distance_km
    
    def calculate_edge_distance(self, node1: Node, node2: Node, min_samples: int = 3) -> float:
        """
        엣지와 목표 곡선 사이의 거리 계산
        
        Args:
            node1: 시작 노드
            node2: 끝 노드
            min_samples: 최소 샘플 포인트 수
            
        Returns:
            거리 합 (km)
        """
        samples = self._sample_edge_points(node1, node2, min_samples)
        
        total_distance = 0.0
        for sample in samples:
            min_dist = self._point_to_curve_distance(sample)
            total_distance += min_dist
        
        return total_distance / len(samples) if samples else 0.0
    
    def calculate_path_distance(self, path: List[int], graph: RoadGraph) -> float:
        """
        경로 전체의 도형 거리 계산
        
        Args:
            path: 노드 ID 목록
            graph: 도로 그래프
            
        Returns:
            총 거리 (km)
        """
        if len(path) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(len(path) - 1):
            node1 = graph.get_node(path[i])
            node2 = graph.get_node(path[i + 1])
            
            if node1 and node2:
                total_distance += self.calculate_edge_distance(node1, node2)
        
        return total_distance
    
    def calculate_normalized_distance(self, path: List[int], graph: RoadGraph) -> float:
        """
        정규화된 도형 거리 계산
        
        Args:
            path: 노드 ID 목록
            graph: 도로 그래프
            
        Returns:
            정규화된 거리 (0~1 범위 권장)
        """
        raw_distance = self.calculate_path_distance(path, graph)
        return raw_distance / self.target_distance_km
    
    def _sample_edge_points(
        self,
        node1: Node,
        node2: Node,
        min_samples: int = 3
    ) -> List[Coordinate]:
        """
        엣지를 샘플링하여 포인트 목록 반환
        
        Args:
            node1: 시작 노드
            node2: 끝 노드
            min_samples: 최소 샘플 수
            
        Returns:
            샘플 좌표 목록
        """
        samples = []
        
        for i in range(min_samples):
            t = i / (min_samples - 1) if min_samples > 1 else 0.5
            lat = node1.lat + t * (node2.lat - node1.lat)
            lng = node1.lng + t * (node2.lng - node1.lng)
            samples.append(Coordinate(lat=lat, lng=lng))
        
        return samples
    
    def _point_to_curve_distance(self, point: Coordinate) -> float:
        """
        점에서 목표 곡선까지의 최소 거리 계산
        
        Args:
            point: 대상 점
            
        Returns:
            최소 거리 (km)
        """
        min_distance = float('inf')
        
        for i in range(len(self.target_curve) - 1):
            seg_start = self.target_curve[i]
            seg_end = self.target_curve[i + 1]
            
            dist = self._point_to_segment_distance(point, seg_start, seg_end)
            min_distance = min(min_distance, dist)
        
        return min_distance
    
    def _point_to_segment_distance(
        self,
        point: Coordinate,
        seg_start: Coordinate,
        seg_end: Coordinate
    ) -> float:
        """
        점에서 선분까지의 최소 거리 (km)
        
        Args:
            point: 대상 점
            seg_start: 선분 시작점
            seg_end: 선분 끝점
            
        Returns:
            거리 (km)
        """
        # 선분 벡터
        dx = seg_end.lng - seg_start.lng
        dy = seg_end.lat - seg_start.lat
        
        # 선분 길이의 제곱
        seg_len_sq = dx * dx + dy * dy
        
        if seg_len_sq == 0:
            # 선분이 점인 경우
            return self._haversine_distance(point, seg_start)
        
        # 점을 선분에 투영
        t = max(0, min(1, (
            (point.lng - seg_start.lng) * dx +
            (point.lat - seg_start.lat) * dy
        ) / seg_len_sq))
        
        # 투영점 계산
        proj_lat = seg_start.lat + t * dy
        proj_lng = seg_start.lng + t * dx
        proj_point = Coordinate(lat=proj_lat, lng=proj_lng)
        
        return self._haversine_distance(point, proj_point)
    
    def _haversine_distance(self, p1: Coordinate, p2: Coordinate) -> float:
        """두 좌표 사이의 거리 (km)"""
        R = 6371  # 지구 반지름 (km)
        
        lat1, lng1 = math.radians(p1.lat), math.radians(p1.lng)
        lat2, lng2 = math.radians(p2.lat), math.radians(p2.lng)
        
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c


class LengthPenaltyCalculator:
    """
    경로 길이 페널티 계산기
    
    목표 거리와 실제 거리의 차이를 페널티로 계산
    """
    
    def __init__(self, target_distance_km: float):
        """
        Args:
            target_distance_km: 목표 거리 (km)
        """
        if target_distance_km <= 0:
            raise ValueError("목표 거리는 양수여야 합니다")
        
        self.target_distance_km = target_distance_km
    
    def calculate_path_length(self, path: List[int], graph: RoadGraph) -> float:
        """
        경로의 총 길이 계산
        
        Args:
            path: 노드 ID 목록
            graph: 도로 그래프
            
        Returns:
            총 길이 (km)
        """
        if len(path) < 2:
            return 0.0
        
        total_length = 0.0
        for i in range(len(path) - 1):
            edge = graph.get_edge_between(path[i], path[i + 1])
            if edge:
                total_length += edge.length_km
        
        return total_length
    
    def calculate_penalty(self, path: List[int], graph: RoadGraph) -> float:
        """
        길이 페널티 계산
        
        Args:
            path: 노드 ID 목록
            graph: 도로 그래프
            
        Returns:
            페널티 (|실제 길이 - 목표 길이|)
        """
        actual_length = self.calculate_path_length(path, graph)
        return abs(actual_length - self.target_distance_km)
    
    def calculate_normalized_penalty(self, path: List[int], graph: RoadGraph) -> float:
        """
        정규화된 길이 페널티 계산
        
        Args:
            path: 노드 ID 목록
            graph: 도로 그래프
            
        Returns:
            정규화된 페널티 (0~1 범위 권장)
        """
        raw_penalty = self.calculate_penalty(path, graph)
        return raw_penalty / self.target_distance_km


class CrossingPenaltyCalculator:
    """
    횡단보도/신호등 페널티 계산기
    
    허용 개수를 초과하는 신호등에 대해 페널티 부과
    """
    
    def __init__(self, max_crossings: int):
        """
        Args:
            max_crossings: 허용 최대 횡단보도/신호등 개수
        """
        if max_crossings < 0:
            raise ValueError("허용 횡단보도 개수는 0 이상이어야 합니다")
        
        self.max_crossings = max_crossings
    
    def count_traffic_lights(self, path: List[int], graph: RoadGraph) -> int:
        """
        경로 내 신호등 개수 카운트 (시작점, 끝점 제외)
        
        Args:
            path: 노드 ID 목록
            graph: 도로 그래프
            
        Returns:
            신호등 개수
        """
        if len(path) <= 2:
            return 0
        
        count = 0
        # 중간 노드만 카운트 (시작점, 끝점 제외)
        for node_id in path[1:-1]:
            node = graph.get_node(node_id)
            if node and node.has_traffic_light:
                count += 1
        
        return count
    
    def calculate_penalty(self, path: List[int], graph: RoadGraph) -> float:
        """
        횡단보도 페널티 계산
        
        Args:
            path: 노드 ID 목록
            graph: 도로 그래프
            
        Returns:
            페널티 (max(0, 신호등 수 - 허용 개수))
        """
        count = self.count_traffic_lights(path, graph)
        return max(0, count - self.max_crossings)
    
    def calculate_normalized_penalty(self, path: List[int], graph: RoadGraph) -> float:
        """
        정규화된 횡단보도 페널티 계산
        
        Args:
            path: 노드 ID 목록
            graph: 도로 그래프
            
        Returns:
            정규화된 페널티
        """
        raw_penalty = self.calculate_penalty(path, graph)
        return raw_penalty / (self.max_crossings + 1)


class CostCalculator:
    """
    통합 비용 계산기
    
    ShapeDistance, LengthPenalty, CrossingPenalty를 통합하여 계산
    """
    
    def __init__(
        self,
        target_curve: List[Coordinate],
        target_distance_km: float,
        max_crossings: int,
        weights: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    ):
        """
        Args:
            target_curve: 목표 도형 좌표 목록
            target_distance_km: 목표 거리 (km)
            max_crossings: 허용 최대 횡단보도 개수
            weights: (shape, length, crossing) 가중치 튜플
        """
        self.shape_calculator = ShapeDistanceCalculator(target_curve, target_distance_km)
        self.length_calculator = LengthPenaltyCalculator(target_distance_km)
        self.crossing_calculator = CrossingPenaltyCalculator(max_crossings)
        self.weights = weights
        self.target_distance_km = target_distance_km
    
    def calculate(self, path: List[int], graph: RoadGraph) -> CostResult:
        """
        경로의 총 비용 계산
        
        Args:
            path: 노드 ID 목록
            graph: 도로 그래프
            
        Returns:
            CostResult 객체
            
        Raises:
            ValueError: 경로가 비어있거나 노드가 1개인 경우
        """
        if len(path) < 2:
            raise ValueError("경로는 최소 2개 이상의 노드가 필요합니다")
        
        # 각 비용 계산 (정규화)
        shape_distance = self.shape_calculator.calculate_normalized_distance(path, graph)
        length_penalty = self.length_calculator.calculate_normalized_penalty(path, graph)
        crossing_penalty = self.crossing_calculator.calculate_normalized_penalty(path, graph)
        
        # 가중치 적용 총 비용
        total_cost = (
            self.weights[0] * shape_distance +
            self.weights[1] * length_penalty +
            self.weights[2] * crossing_penalty
        )
        
        # 추가 정보
        path_length_km = self.length_calculator.calculate_path_length(path, graph)
        traffic_light_count = self.crossing_calculator.count_traffic_lights(path, graph)
        
        return CostResult(
            shape_distance=shape_distance,
            length_penalty=length_penalty,
            crossing_penalty=crossing_penalty,
            total_cost=total_cost,
            path_length_km=path_length_km,
            traffic_light_count=traffic_light_count
        )
    
    def calculate_edge_cost(
        self,
        node1: Node,
        node2: Node,
        edge: Edge,
        graph: RoadGraph
    ) -> float:
        """
        단일 엣지의 비용 계산 (A* 알고리즘용)
        
        Args:
            node1: 시작 노드
            node2: 끝 노드
            edge: 엣지
            graph: 도로 그래프
            
        Returns:
            엣지 비용
        """
        # 도형 거리
        shape_dist = self.shape_calculator.calculate_edge_distance(node1, node2)
        shape_cost = shape_dist / self.target_distance_km
        
        # 길이 (정규화)
        length_cost = edge.length_km / self.target_distance_km
        
        # 신호등 (도착 노드에 신호등이 있으면 페널티)
        crossing_cost = 0.0
        if node2.has_traffic_light:
            crossing_cost = 1.0 / (self.crossing_calculator.max_crossings + 1)
        
        return (
            self.weights[0] * shape_cost +
            self.weights[1] * length_cost +
            self.weights[2] * crossing_cost
        )
