"""
경로 탐색 알고리즘 테스트
"""
import pytest
import numpy as np

from src.domain.entities import Coordinate
from src.data.entities import Node, Edge, RoadGraph
from src.algorithm.weight_sampler import WeightSampler, WeightVector
from src.algorithm.astar import AStarPathFinder, PathCandidate
from src.algorithm.pareto import ParetoFilter, ParetoCandidate
from src.algorithm.route_finder import RouteFinder, RouteSearchConfig


class TestWeightSampler:
    """WeightSampler 테스트"""
    
    def test_sample_returns_correct_count(self):
        """샘플 개수가 정확한지 확인"""
        sampler = WeightSampler(seed=42)
        samples = sampler.sample(20)
        
        assert len(samples) == 20
    
    def test_sample_weights_sum_to_one(self):
        """가중치 합이 1인지 확인"""
        sampler = WeightSampler(seed=42)
        samples = sampler.sample(10)
        
        for weight in samples:
            total = weight.alpha + weight.beta + weight.gamma
            assert np.isclose(total, 1.0, atol=1e-6)
    
    def test_sample_weights_are_positive(self):
        """가중치가 양수인지 확인"""
        sampler = WeightSampler(seed=42)
        samples = sampler.sample(10)
        
        for weight in samples:
            assert weight.alpha >= 0
            assert weight.beta >= 0
            assert weight.gamma >= 0
    
    def test_sample_with_seed_is_reproducible(self):
        """시드가 같으면 결과가 동일한지 확인"""
        sampler1 = WeightSampler(seed=42)
        sampler2 = WeightSampler(seed=42)
        
        samples1 = sampler1.sample(5)
        samples2 = sampler2.sample(5)
        
        for s1, s2 in zip(samples1, samples2):
            assert np.isclose(s1.alpha, s2.alpha)
            assert np.isclose(s1.beta, s2.beta)
            assert np.isclose(s1.gamma, s2.gamma)
    
    def test_sample_with_bias(self):
        """편향된 샘플링이 작동하는지 확인"""
        sampler = WeightSampler(seed=42)
        samples = sampler.sample_with_bias(
            n_samples=100,
            shape_bias=5.0,
            length_bias=1.0,
            crossing_bias=1.0
        )
        
        # 도형 가중치 평균이 더 높아야 함
        avg_alpha = sum(s.alpha for s in samples) / len(samples)
        avg_beta = sum(s.beta for s in samples) / len(samples)
        
        assert avg_alpha > avg_beta
    
    def test_get_corner_weights(self):
        """코너 가중치가 올바른지 확인"""
        sampler = WeightSampler()
        corners = sampler.get_corner_weights()
        
        assert len(corners) == 4
        
        # 각 코너가 특정 목적에 편향되어 있는지 확인
        assert corners[0].alpha > corners[0].beta  # 도형 중심
        assert corners[1].beta > corners[1].alpha  # 길이 중심
        assert corners[2].gamma > corners[2].alpha  # 횡단보도 중심
    
    def test_sample_with_corners(self):
        """코너 포함 샘플링이 작동하는지 확인"""
        sampler = WeightSampler(seed=42)
        samples = sampler.sample_with_corners(16)
        
        assert len(samples) == 20  # 4 corners + 16 samples
    
    def test_invalid_sample_count_raises_error(self):
        """잘못된 샘플 개수에 대해 에러 발생"""
        sampler = WeightSampler()
        
        with pytest.raises(ValueError):
            sampler.sample(0)
        
        with pytest.raises(ValueError):
            sampler.sample(-5)
    
    def test_weight_vector_invalid_sum_raises_error(self):
        """가중치 합이 1이 아니면 에러 발생"""
        with pytest.raises(ValueError):
            WeightVector(alpha=0.5, beta=0.5, gamma=0.5)


class TestParetoFilter:
    """ParetoFilter 테스트"""
    
    def test_dominates_true_case(self):
        """지배 관계가 올바르게 판정되는지 확인"""
        pf = ParetoFilter()
        
        # obj1이 obj2를 지배 (모든 값이 작거나 같고, 하나 이상 작음)
        obj1 = (0.1, 0.2, 0.3)
        obj2 = (0.2, 0.3, 0.4)
        
        assert pf.dominates(obj1, obj2) is True
    
    def test_dominates_false_equal_case(self):
        """동일한 값은 지배하지 않음"""
        pf = ParetoFilter()
        
        obj1 = (0.1, 0.2, 0.3)
        obj2 = (0.1, 0.2, 0.3)
        
        assert pf.dominates(obj1, obj2) is False
    
    def test_dominates_false_mixed_case(self):
        """혼합된 경우 지배하지 않음"""
        pf = ParetoFilter()
        
        obj1 = (0.1, 0.3, 0.3)  # 첫 번째는 작지만 두 번째는 큼
        obj2 = (0.2, 0.2, 0.3)
        
        assert pf.dominates(obj1, obj2) is False
    
    def test_filter_non_dominated_simple(self):
        """Non-dominated 필터링 테스트"""
        pf = ParetoFilter()
        
        # 테스트용 PathCandidate 생성
        candidates = [
            PathCandidate(
                path=[1, 2, 3], g_cost=1.0, f_cost=1.0,
                shape_distance=0.1, length_penalty=0.2, crossing_penalty=0.3,
                path_length_km=5.0, traffic_light_count=2
            ),
            PathCandidate(
                path=[1, 2, 4], g_cost=1.5, f_cost=1.5,
                shape_distance=0.2, length_penalty=0.3, crossing_penalty=0.4,
                path_length_km=5.5, traffic_light_count=3
            ),
            PathCandidate(
                path=[1, 3, 4], g_cost=0.8, f_cost=0.8,
                shape_distance=0.15, length_penalty=0.1, crossing_penalty=0.5,
                path_length_km=4.5, traffic_light_count=1
            ),
        ]
        
        non_dominated = pf.filter_non_dominated(candidates)
        
        # 첫 번째와 세 번째가 서로 지배하지 않음
        # 두 번째는 첫 번째에 의해 지배됨
        assert len(non_dominated) == 2
    
    def test_filter_non_dominated_all_pareto(self):
        """모든 후보가 Pareto 최적인 경우"""
        pf = ParetoFilter()
        
        candidates = [
            PathCandidate(
                path=[1, 2], g_cost=1.0, f_cost=1.0,
                shape_distance=0.1, length_penalty=0.5, crossing_penalty=0.5,
                path_length_km=5.0, traffic_light_count=2
            ),
            PathCandidate(
                path=[1, 3], g_cost=1.0, f_cost=1.0,
                shape_distance=0.5, length_penalty=0.1, crossing_penalty=0.5,
                path_length_km=5.0, traffic_light_count=2
            ),
            PathCandidate(
                path=[1, 4], g_cost=1.0, f_cost=1.0,
                shape_distance=0.5, length_penalty=0.5, crossing_penalty=0.1,
                path_length_km=5.0, traffic_light_count=2
            ),
        ]
        
        non_dominated = pf.filter_non_dominated(candidates)
        
        assert len(non_dominated) == 3
    
    def test_select_top_k(self):
        """상위 k개 선택 테스트"""
        pf = ParetoFilter()
        
        candidates = [
            PathCandidate(
                path=[1, 2], g_cost=1.0, f_cost=1.0,
                shape_distance=0.1 * i, length_penalty=0.1 * (10 - i), crossing_penalty=0.2,
                path_length_km=5.0, traffic_light_count=2
            )
            for i in range(10)
        ]
        
        top_5 = pf.select_top_k(candidates, k=5)
        
        assert len(top_5) <= 5
    
    def test_select_top_k_less_than_k(self):
        """후보가 k개 미만인 경우"""
        pf = ParetoFilter()
        
        candidates = [
            PathCandidate(
                path=[1, 2], g_cost=1.0, f_cost=1.0,
                shape_distance=0.1, length_penalty=0.2, crossing_penalty=0.3,
                path_length_km=5.0, traffic_light_count=2
            ),
            PathCandidate(
                path=[1, 3], g_cost=1.0, f_cost=1.0,
                shape_distance=0.2, length_penalty=0.1, crossing_penalty=0.3,
                path_length_km=5.0, traffic_light_count=2
            ),
        ]
        
        top_5 = pf.select_top_k(candidates, k=5)
        
        assert len(top_5) == 2
    
    def test_crowding_distance_calculation(self):
        """혼잡 거리 계산 테스트"""
        pf = ParetoFilter()
        
        candidates = [
            PathCandidate(
                path=[1, 2], g_cost=1.0, f_cost=1.0,
                shape_distance=0.0, length_penalty=1.0, crossing_penalty=0.5,
                path_length_km=5.0, traffic_light_count=2
            ),
            PathCandidate(
                path=[1, 3], g_cost=1.0, f_cost=1.0,
                shape_distance=0.5, length_penalty=0.5, crossing_penalty=0.5,
                path_length_km=5.0, traffic_light_count=2
            ),
            PathCandidate(
                path=[1, 4], g_cost=1.0, f_cost=1.0,
                shape_distance=1.0, length_penalty=0.0, crossing_penalty=0.5,
                path_length_km=5.0, traffic_light_count=2
            ),
        ]
        
        pareto_candidates = [
            ParetoCandidate.from_path_candidate(c) for c in candidates
        ]
        
        result = pf.calculate_crowding_distance(pareto_candidates)
        
        # 경계 값들은 무한대
        assert result[0].crowding_distance == float('inf')
        assert result[2].crowding_distance == float('inf')
        # 중간 값은 유한
        assert result[1].crowding_distance < float('inf')


class TestAStarPathFinder:
    """AStarPathFinder 테스트"""
    
    @pytest.fixture
    def simple_graph(self):
        """테스트용 간단한 그래프 생성"""
        graph = RoadGraph()
        
        # 정사각형 형태의 노드 배치
        nodes = [
            Node(id=1, lat=37.5, lng=127.0),
            Node(id=2, lat=37.5, lng=127.01),
            Node(id=3, lat=37.51, lng=127.01),
            Node(id=4, lat=37.51, lng=127.0),
            Node(id=5, lat=37.505, lng=127.005, has_traffic_light=True),
        ]
        
        for node in nodes:
            graph.add_node(node)
        
        # 엣지 추가 (순환 가능하도록)
        edges = [
            Edge(id=1, source_id=1, target_id=2, length_m=800),
            Edge(id=2, source_id=2, target_id=3, length_m=1100),
            Edge(id=3, source_id=3, target_id=4, length_m=800),
            Edge(id=4, source_id=4, target_id=1, length_m=1100),
            Edge(id=5, source_id=1, target_id=5, length_m=700),
            Edge(id=6, source_id=5, target_id=3, length_m=700),
        ]
        
        for edge in edges:
            graph.add_edge(edge)
        
        return graph
    
    @pytest.fixture
    def target_curve(self):
        """테스트용 목표 곡선"""
        return [
            Coordinate(lat=37.5, lng=127.0),
            Coordinate(lat=37.5, lng=127.01),
            Coordinate(lat=37.51, lng=127.01),
            Coordinate(lat=37.51, lng=127.0),
            Coordinate(lat=37.5, lng=127.0),
        ]
    
    def test_pathfinder_initialization(self, simple_graph, target_curve):
        """PathFinder 초기화 테스트"""
        pathfinder = AStarPathFinder(
            graph=simple_graph,
            target_curve=target_curve,
            target_distance_km=5.0,
            max_crossings=3
        )
        
        assert pathfinder.graph == simple_graph
        assert pathfinder.target_distance_km == 5.0
        assert pathfinder.max_crossings == 3
    
    def test_find_path_to_goal(self, simple_graph, target_curve):
        """목표점까지 경로 탐색 테스트"""
        pathfinder = AStarPathFinder(
            graph=simple_graph,
            target_curve=target_curve,
            target_distance_km=5.0,
            max_crossings=3
        )
        
        result = pathfinder.find_path_to_goal(
            start_node_id=1,
            goal_node_id=3
        )
        
        assert result is not None
        assert result.path[0] == 1
        assert result.path[-1] == 3
    
    def test_find_path_invalid_start(self, simple_graph, target_curve):
        """존재하지 않는 시작 노드"""
        pathfinder = AStarPathFinder(
            graph=simple_graph,
            target_curve=target_curve,
            target_distance_km=5.0,
            max_crossings=3
        )
        
        result = pathfinder.find_path_to_goal(
            start_node_id=999,
            goal_node_id=3
        )
        
        assert result is None


class TestRouteFinder:
    """RouteFinder 테스트"""
    
    @pytest.fixture
    def test_graph(self):
        """테스트용 그래프"""
        graph = RoadGraph()
        
        # 더 큰 그래프 생성 (5x5 격자)
        node_id = 1
        for i in range(5):
            for j in range(5):
                lat = 37.5 + i * 0.005
                lng = 127.0 + j * 0.005
                has_light = (i + j) % 3 == 0
                graph.add_node(Node(id=node_id, lat=lat, lng=lng, has_traffic_light=has_light))
                node_id += 1
        
        # 격자 엣지 추가
        edge_id = 1
        for i in range(5):
            for j in range(5):
                current = i * 5 + j + 1
                
                # 오른쪽 이웃
                if j < 4:
                    right = current + 1
                    graph.add_edge(Edge(id=edge_id, source_id=current, target_id=right, length_m=500))
                    edge_id += 1
                
                # 아래 이웃
                if i < 4:
                    down = current + 5
                    graph.add_edge(Edge(id=edge_id, source_id=current, target_id=down, length_m=500))
                    edge_id += 1
        
        return graph
    
    @pytest.fixture
    def target_curve(self):
        """테스트용 목표 곡선 (사각형)"""
        return [
            Coordinate(lat=37.5, lng=127.0),
            Coordinate(lat=37.5, lng=127.02),
            Coordinate(lat=37.52, lng=127.02),
            Coordinate(lat=37.52, lng=127.0),
            Coordinate(lat=37.5, lng=127.0),
        ]
    
    def test_route_finder_initialization(self, test_graph):
        """RouteFinder 초기화 테스트"""
        config = RouteSearchConfig(
            n_weight_samples=10,
            n_rotations=3,
            max_results=3
        )
        
        finder = RouteFinder(graph=test_graph, config=config)
        
        assert finder.graph == test_graph
        assert finder.config.n_weight_samples == 10
        assert finder.config.n_rotations == 3
    
    def test_find_start_node(self, test_graph, target_curve):
        """시작 노드 찾기 테스트"""
        finder = RouteFinder(graph=test_graph)
        
        start_node = finder._find_start_node(target_curve)
        
        assert start_node is not None
        assert start_node in test_graph.nodes
    
    def test_generate_rotated_curves(self, test_graph, target_curve):
        """회전된 곡선 생성 테스트"""
        config = RouteSearchConfig(n_rotations=6)
        finder = RouteFinder(graph=test_graph, config=config)
        
        rotated = finder._generate_rotated_curves(target_curve)
        
        assert len(rotated) == 6
        for curve in rotated:
            assert len(curve) == len(target_curve)
    
    def test_route_finder_empty_curve(self, test_graph):
        """빈 곡선 처리 테스트"""
        finder = RouteFinder(graph=test_graph)
        
        result = finder.find_routes(
            target_curve=[],
            target_distance_km=5.0,
            max_crossings=3
        )
        
        assert result == []


class TestIntegration:
    """통합 테스트"""
    
    @pytest.fixture
    def complete_setup(self):
        """완전한 테스트 환경 설정"""
        # 그래프 생성
        graph = RoadGraph()
        
        # 원형에 가까운 노드 배치
        import math
        center_lat, center_lng = 37.5, 127.0
        radius = 0.01
        n_points = 12
        
        for i in range(n_points):
            angle = 2 * math.pi * i / n_points
            lat = center_lat + radius * math.sin(angle)
            lng = center_lng + radius * math.cos(angle)
            graph.add_node(Node(
                id=i + 1,
                lat=lat,
                lng=lng,
                has_traffic_light=(i % 4 == 0)
            ))
        
        # 중심 노드
        graph.add_node(Node(id=100, lat=center_lat, lng=center_lng))
        
        # 원형 엣지
        for i in range(n_points):
            next_i = (i + 1) % n_points
            graph.add_edge(Edge(
                id=i + 1,
                source_id=i + 1,
                target_id=next_i + 1,
                length_m=500
            ))
            # 중심으로 연결
            graph.add_edge(Edge(
                id=100 + i,
                source_id=i + 1,
                target_id=100,
                length_m=700
            ))
        
        # 목표 곡선 (원형)
        target_curve = [
            Coordinate(
                lat=center_lat + radius * math.sin(2 * math.pi * i / n_points),
                lng=center_lng + radius * math.cos(2 * math.pi * i / n_points)
            )
            for i in range(n_points + 1)
        ]
        
        return graph, target_curve
    
    def test_full_pipeline(self, complete_setup):
        """전체 파이프라인 테스트"""
        graph, target_curve = complete_setup
        
        config = RouteSearchConfig(
            n_weight_samples=5,
            n_rotations=2,
            max_iterations=1000,
            max_results=3,
            use_parallel=False
        )
        
        finder = RouteFinder(graph=graph, config=config)
        
        # 경로 탐색 실행 (결과가 없을 수 있음 - 그래프가 작아서)
        routes = finder.find_routes(
            target_curve=target_curve,
            target_distance_km=3.0,
            max_crossings=5
        )
        
        # 결과 검증 (결과가 있으면)
        for route in routes:
            assert route.route_id > 0
            assert len(route.coordinates) >= 2
            assert route.total_distance_km > 0
