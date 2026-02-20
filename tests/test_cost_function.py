"""
비용 함수 테스트
Phase 4: ShapeDistance, LengthPenalty, CrossingPenalty
"""
import pytest
import math
from typing import List

from src.domain.entities import Coordinate
from src.data.entities import Node, Edge, RoadGraph, RoadType
from src.cost.cost_function import (
    CostCalculator,
    ShapeDistanceCalculator,
    LengthPenaltyCalculator,
    CrossingPenaltyCalculator,
    CostResult,
)


# ============================================================================
# 테스트 픽스처
# ============================================================================

@pytest.fixture
def simple_graph() -> RoadGraph:
    """간단한 테스트용 그래프 생성"""
    graph = RoadGraph()
    
    # 정사각형 형태의 노드 배치 (1km x 1km 대략적)
    # 위도 1도 ≈ 111km, 경도 1도 ≈ 88km (위도 37도 기준)
    nodes = [
        Node(id=1, lat=37.5, lng=127.0, has_traffic_light=False),
        Node(id=2, lat=37.5, lng=127.01, has_traffic_light=True),
        Node(id=3, lat=37.51, lng=127.01, has_traffic_light=False),
        Node(id=4, lat=37.51, lng=127.0, has_traffic_light=True),
    ]
    
    for node in nodes:
        graph.add_node(node)
    
    # 엣지 추가 (정사각형 경로)
    edges = [
        Edge(id=1, source_id=1, target_id=2, length_m=880.0, road_type=RoadType.RESIDENTIAL),
        Edge(id=2, source_id=2, target_id=3, length_m=1110.0, road_type=RoadType.RESIDENTIAL),
        Edge(id=3, source_id=3, target_id=4, length_m=880.0, road_type=RoadType.RESIDENTIAL),
        Edge(id=4, source_id=4, target_id=1, length_m=1110.0, road_type=RoadType.RESIDENTIAL),
    ]
    
    for edge in edges:
        graph.add_edge(edge)
    
    return graph


@pytest.fixture
def target_curve() -> List[Coordinate]:
    """목표 도형 (정사각형)"""
    return [
        Coordinate(lat=37.5, lng=127.0),
        Coordinate(lat=37.5, lng=127.01),
        Coordinate(lat=37.51, lng=127.01),
        Coordinate(lat=37.51, lng=127.0),
        Coordinate(lat=37.5, lng=127.0),  # 닫힌 도형
    ]


# ============================================================================
# ShapeDistanceCalculator 테스트
# ============================================================================

class TestShapeDistanceCalculator:
    """Edge-Curve 거리 계산 테스트"""
    
    def test_edge_on_curve_returns_zero(self, simple_graph: RoadGraph, target_curve: List[Coordinate]):
        """엣지가 목표 곡선 위에 있으면 거리가 0"""
        calculator = ShapeDistanceCalculator(target_curve, target_distance_km=5.0)
        
        # 노드 1 -> 2 엣지는 목표 곡선의 첫 번째 세그먼트와 일치
        node1 = simple_graph.get_node(1)
        node2 = simple_graph.get_node(2)
        
        distance = calculator.calculate_edge_distance(node1, node2)
        
        assert distance < 0.001  # 거의 0
    
    def test_edge_far_from_curve_returns_positive(self, target_curve: List[Coordinate]):
        """엣지가 목표 곡선에서 멀면 양수 거리 반환"""
        calculator = ShapeDistanceCalculator(target_curve, target_distance_km=5.0)
        
        # 목표 곡선에서 떨어진 엣지
        node1 = Node(id=100, lat=37.55, lng=127.05, has_traffic_light=False)
        node2 = Node(id=101, lat=37.56, lng=127.06, has_traffic_light=False)
        
        distance = calculator.calculate_edge_distance(node1, node2)
        
        assert distance > 0
    
    def test_path_distance_accumulates(self, simple_graph: RoadGraph, target_curve: List[Coordinate]):
        """경로 전체 거리는 각 엣지 거리의 합"""
        calculator = ShapeDistanceCalculator(target_curve, target_distance_km=5.0)
        
        # 경로: 1 -> 2 -> 3
        path = [1, 2, 3]
        
        total_distance = calculator.calculate_path_distance(path, simple_graph)
        
        # 각 엣지 거리 합과 같아야 함
        node1 = simple_graph.get_node(1)
        node2 = simple_graph.get_node(2)
        node3 = simple_graph.get_node(3)
        
        edge1_dist = calculator.calculate_edge_distance(node1, node2)
        edge2_dist = calculator.calculate_edge_distance(node2, node3)
        
        assert abs(total_distance - (edge1_dist + edge2_dist)) < 0.001
    
    def test_normalized_distance(self, simple_graph: RoadGraph, target_curve: List[Coordinate]):
        """정규화된 거리는 target_distance로 나눈 값"""
        target_km = 5.0
        calculator = ShapeDistanceCalculator(target_curve, target_distance_km=target_km)
        
        path = [1, 2, 3]
        
        raw_distance = calculator.calculate_path_distance(path, simple_graph)
        normalized = calculator.calculate_normalized_distance(path, simple_graph)
        
        assert abs(normalized - raw_distance / target_km) < 0.001
    
    def test_edge_sampling_minimum_three_points(self, target_curve: List[Coordinate]):
        """엣지 샘플링은 최소 3개 포인트"""
        calculator = ShapeDistanceCalculator(target_curve, target_distance_km=5.0)
        
        node1 = Node(id=1, lat=37.5, lng=127.0, has_traffic_light=False)
        node2 = Node(id=2, lat=37.5, lng=127.001, has_traffic_light=False)  # 짧은 엣지
        
        samples = calculator._sample_edge_points(node1, node2, min_samples=3)
        
        assert len(samples) >= 3


# ============================================================================
# LengthPenaltyCalculator 테스트
# ============================================================================

class TestLengthPenaltyCalculator:
    """경로 길이 페널티 테스트"""
    
    def test_exact_length_returns_zero(self, simple_graph: RoadGraph):
        """목표 길이와 정확히 일치하면 페널티 0"""
        # 경로 1->2->3의 길이: 880 + 1110 = 1990m = 1.99km
        target_km = 1.99
        calculator = LengthPenaltyCalculator(target_distance_km=target_km)
        
        path = [1, 2, 3]
        penalty = calculator.calculate_penalty(path, simple_graph)
        
        assert penalty < 0.01  # 거의 0
    
    def test_shorter_path_returns_positive_penalty(self, simple_graph: RoadGraph):
        """목표보다 짧으면 양수 페널티"""
        target_km = 5.0  # 목표 5km
        calculator = LengthPenaltyCalculator(target_distance_km=target_km)
        
        path = [1, 2]  # 880m = 0.88km
        penalty = calculator.calculate_penalty(path, simple_graph)
        
        assert penalty > 0
    
    def test_longer_path_returns_positive_penalty(self, simple_graph: RoadGraph):
        """목표보다 길면 양수 페널티"""
        target_km = 1.0  # 목표 1km
        calculator = LengthPenaltyCalculator(target_distance_km=target_km)
        
        path = [1, 2, 3, 4, 1]  # 전체 순환: 약 3.98km
        penalty = calculator.calculate_penalty(path, simple_graph)
        
        assert penalty > 0
    
    def test_normalized_penalty(self, simple_graph: RoadGraph):
        """정규화된 페널티는 target_distance로 나눈 값"""
        target_km = 5.0
        calculator = LengthPenaltyCalculator(target_distance_km=target_km)
        
        path = [1, 2, 3]
        
        raw_penalty = calculator.calculate_penalty(path, simple_graph)
        normalized = calculator.calculate_normalized_penalty(path, simple_graph)
        
        assert abs(normalized - raw_penalty / target_km) < 0.001
    
    def test_path_length_calculation(self, simple_graph: RoadGraph):
        """경로 길이 계산 정확성"""
        calculator = LengthPenaltyCalculator(target_distance_km=5.0)
        
        path = [1, 2, 3]
        length = calculator.calculate_path_length(path, simple_graph)
        
        # 880m + 1110m = 1990m = 1.99km
        assert abs(length - 1.99) < 0.01


# ============================================================================
# CrossingPenaltyCalculator 테스트
# ============================================================================

class TestCrossingPenaltyCalculator:
    """횡단보도/신호등 페널티 테스트"""
    
    def test_no_traffic_lights_returns_zero(self, simple_graph: RoadGraph):
        """신호등이 없으면 페널티 0"""
        calculator = CrossingPenaltyCalculator(max_crossings=5)
        
        # 노드 1, 3은 신호등 없음
        path = [1, 3]  # 직접 연결은 없지만 테스트용
        
        # 신호등 개수만 세는 테스트
        count = calculator.count_traffic_lights(path, simple_graph)
        
        # 시작점과 끝점은 제외하고 중간 노드만 카운트
        # path [1, 3]에서 중간 노드 없음
        assert count == 0
    
    def test_count_traffic_lights_in_path(self, simple_graph: RoadGraph):
        """경로 내 신호등 개수 카운트"""
        calculator = CrossingPenaltyCalculator(max_crossings=5)
        
        # 경로 1 -> 2 -> 3 -> 4
        # 노드 2, 4는 신호등 있음
        # 시작점(1)과 끝점(4)은 제외, 중간 노드 2, 3 중 2만 신호등
        path = [1, 2, 3, 4]
        count = calculator.count_traffic_lights(path, simple_graph)
        
        # 중간 노드: 2(신호등), 3(없음) -> 1개
        assert count == 1
    
    def test_within_limit_returns_zero_penalty(self, simple_graph: RoadGraph):
        """허용 범위 내면 페널티 0"""
        calculator = CrossingPenaltyCalculator(max_crossings=5)
        
        path = [1, 2, 3, 4]  # 신호등 1개 (노드 2)
        penalty = calculator.calculate_penalty(path, simple_graph)
        
        assert penalty == 0
    
    def test_exceeds_limit_returns_positive_penalty(self, simple_graph: RoadGraph):
        """허용 범위 초과 시 양수 페널티"""
        calculator = CrossingPenaltyCalculator(max_crossings=0)  # 신호등 0개 허용
        
        path = [1, 2, 3, 4]  # 신호등 1개
        penalty = calculator.calculate_penalty(path, simple_graph)
        
        assert penalty > 0
    
    def test_normalized_penalty(self, simple_graph: RoadGraph):
        """정규화된 페널티는 (max_crossings + 1)로 나눈 값"""
        max_crossings = 2
        calculator = CrossingPenaltyCalculator(max_crossings=max_crossings)
        
        path = [1, 2, 3, 4]
        
        raw_penalty = calculator.calculate_penalty(path, simple_graph)
        normalized = calculator.calculate_normalized_penalty(path, simple_graph)
        
        expected = raw_penalty / (max_crossings + 1)
        assert abs(normalized - expected) < 0.001


# ============================================================================
# CostCalculator 통합 테스트
# ============================================================================

class TestCostCalculator:
    """통합 비용 계산기 테스트"""
    
    def test_calculate_all_costs(self, simple_graph: RoadGraph, target_curve: List[Coordinate]):
        """모든 비용 계산"""
        calculator = CostCalculator(
            target_curve=target_curve,
            target_distance_km=5.0,
            max_crossings=5
        )
        
        path = [1, 2, 3, 4]
        result = calculator.calculate(path, simple_graph)
        
        assert isinstance(result, CostResult)
        assert result.shape_distance >= 0
        assert result.length_penalty >= 0
        assert result.crossing_penalty >= 0
    
    def test_cost_result_has_all_components(self, simple_graph: RoadGraph, target_curve: List[Coordinate]):
        """CostResult에 모든 구성요소 포함"""
        calculator = CostCalculator(
            target_curve=target_curve,
            target_distance_km=5.0,
            max_crossings=5
        )
        
        path = [1, 2, 3]
        result = calculator.calculate(path, simple_graph)
        
        assert hasattr(result, 'shape_distance')
        assert hasattr(result, 'length_penalty')
        assert hasattr(result, 'crossing_penalty')
        assert hasattr(result, 'total_cost')
    
    def test_total_cost_is_weighted_sum(self, simple_graph: RoadGraph, target_curve: List[Coordinate]):
        """총 비용은 가중치 합"""
        weights = (1.0, 1.0, 1.0)
        calculator = CostCalculator(
            target_curve=target_curve,
            target_distance_km=5.0,
            max_crossings=5,
            weights=weights
        )
        
        path = [1, 2, 3]
        result = calculator.calculate(path, simple_graph)
        
        expected_total = (
            weights[0] * result.shape_distance +
            weights[1] * result.length_penalty +
            weights[2] * result.crossing_penalty
        )
        
        assert abs(result.total_cost - expected_total) < 0.001
    
    def test_custom_weights(self, simple_graph: RoadGraph, target_curve: List[Coordinate]):
        """커스텀 가중치 적용"""
        weights = (2.0, 0.5, 1.5)
        calculator = CostCalculator(
            target_curve=target_curve,
            target_distance_km=5.0,
            max_crossings=5,
            weights=weights
        )
        
        path = [1, 2, 3]
        result = calculator.calculate(path, simple_graph)
        
        expected_total = (
            weights[0] * result.shape_distance +
            weights[1] * result.length_penalty +
            weights[2] * result.crossing_penalty
        )
        
        assert abs(result.total_cost - expected_total) < 0.001
    
    def test_empty_path_raises_error(self, simple_graph: RoadGraph, target_curve: List[Coordinate]):
        """빈 경로는 에러"""
        calculator = CostCalculator(
            target_curve=target_curve,
            target_distance_km=5.0,
            max_crossings=5
        )
        
        with pytest.raises(ValueError):
            calculator.calculate([], simple_graph)
    
    def test_single_node_path_raises_error(self, simple_graph: RoadGraph, target_curve: List[Coordinate]):
        """단일 노드 경로는 에러"""
        calculator = CostCalculator(
            target_curve=target_curve,
            target_distance_km=5.0,
            max_crossings=5
        )
        
        with pytest.raises(ValueError):
            calculator.calculate([1], simple_graph)


# ============================================================================
# 엣지 케이스 테스트
# ============================================================================

class TestEdgeCases:
    """엣지 케이스 테스트"""
    
    def test_zero_target_distance(self, target_curve: List[Coordinate]):
        """목표 거리 0은 에러"""
        with pytest.raises(ValueError):
            LengthPenaltyCalculator(target_distance_km=0.0)
    
    def test_negative_target_distance(self, target_curve: List[Coordinate]):
        """음수 목표 거리는 에러"""
        with pytest.raises(ValueError):
            LengthPenaltyCalculator(target_distance_km=-1.0)
    
    def test_negative_max_crossings(self):
        """음수 허용 횡단보도는 에러"""
        with pytest.raises(ValueError):
            CrossingPenaltyCalculator(max_crossings=-1)
    
    def test_empty_target_curve(self):
        """빈 목표 곡선은 에러"""
        with pytest.raises(ValueError):
            ShapeDistanceCalculator(target_curve=[], target_distance_km=5.0)
    
    def test_single_point_target_curve(self):
        """단일 점 목표 곡선은 에러"""
        with pytest.raises(ValueError):
            ShapeDistanceCalculator(
                target_curve=[Coordinate(lat=37.5, lng=127.0)],
                target_distance_km=5.0
            )
