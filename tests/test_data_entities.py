"""
데이터 레이어 엔티티 테스트
"""
import pytest
from src.data.entities import Node, Edge, RoadGraph, RoadType


class TestNode:
    """Node 엔티티 테스트"""
    
    def test_create_node(self):
        """노드 생성 테스트"""
        node = Node(id=1, lat=37.5665, lng=126.9780)
        
        assert node.id == 1
        assert node.lat == 37.5665
        assert node.lng == 126.9780
        assert node.has_traffic_light is False
    
    def test_create_node_with_traffic_light(self):
        """신호등 있는 노드 생성 테스트"""
        node = Node(id=2, lat=37.5665, lng=126.9780, has_traffic_light=True)
        
        assert node.has_traffic_light is True
    
    def test_to_tuple(self):
        """튜플 변환 테스트"""
        node = Node(id=1, lat=37.5665, lng=126.9780)
        
        result = node.to_tuple()
        
        assert result == (37.5665, 126.9780)
    
    def test_distance_to_same_point(self):
        """같은 지점 거리 테스트"""
        node1 = Node(id=1, lat=37.5665, lng=126.9780)
        node2 = Node(id=2, lat=37.5665, lng=126.9780)
        
        distance = node1.distance_to(node2)
        
        assert distance == pytest.approx(0.0, abs=0.001)
    
    def test_distance_to_different_point(self):
        """다른 지점 거리 테스트 (서울시청 - 광화문)"""
        seoul_city_hall = Node(id=1, lat=37.5665, lng=126.9780)
        gwanghwamun = Node(id=2, lat=37.5759, lng=126.9769)
        
        distance = seoul_city_hall.distance_to(gwanghwamun)
        
        # 약 1km 정도 예상
        assert 0.5 < distance < 2.0
    
    def test_node_is_hashable(self):
        """노드 해시 가능 테스트 (frozen=True)"""
        node = Node(id=1, lat=37.5665, lng=126.9780)
        
        # set에 추가 가능해야 함
        node_set = {node}
        assert node in node_set


class TestEdge:
    """Edge 엔티티 테스트"""
    
    def test_create_edge(self):
        """엣지 생성 테스트"""
        edge = Edge(
            id=1,
            source_id=100,
            target_id=200,
            length_m=150.5
        )
        
        assert edge.id == 1
        assert edge.source_id == 100
        assert edge.target_id == 200
        assert edge.length_m == 150.5
        assert edge.road_type == RoadType.UNKNOWN
        assert edge.name is None
        assert edge.is_oneway is False
    
    def test_create_edge_with_all_attributes(self):
        """모든 속성을 가진 엣지 생성 테스트"""
        edge = Edge(
            id=1,
            source_id=100,
            target_id=200,
            length_m=500.0,
            road_type=RoadType.PRIMARY,
            name="세종대로",
            is_oneway=True
        )
        
        assert edge.road_type == RoadType.PRIMARY
        assert edge.name == "세종대로"
        assert edge.is_oneway is True
    
    def test_length_km(self):
        """길이 km 변환 테스트"""
        edge = Edge(id=1, source_id=100, target_id=200, length_m=1500.0)
        
        assert edge.length_km == pytest.approx(1.5, rel=1e-3)
    
    def test_edge_is_hashable(self):
        """엣지 해시 가능 테스트 (frozen=True)"""
        edge = Edge(id=1, source_id=100, target_id=200, length_m=100.0)
        
        edge_set = {edge}
        assert edge in edge_set


class TestRoadGraph:
    """RoadGraph 엔티티 테스트"""
    
    @pytest.fixture
    def sample_graph(self) -> RoadGraph:
        """테스트용 샘플 그래프"""
        graph = RoadGraph()
        
        # 노드 추가
        graph.add_node(Node(id=1, lat=37.56, lng=126.97))
        graph.add_node(Node(id=2, lat=37.57, lng=126.97))
        graph.add_node(Node(id=3, lat=37.57, lng=126.98, has_traffic_light=True))
        
        # 엣지 추가
        graph.add_edge(Edge(id=1, source_id=1, target_id=2, length_m=100.0))
        graph.add_edge(Edge(id=2, source_id=2, target_id=3, length_m=150.0))
        
        return graph
    
    def test_create_empty_graph(self):
        """빈 그래프 생성 테스트"""
        graph = RoadGraph()
        
        assert graph.node_count == 0
        assert graph.edge_count == 0
    
    def test_add_node(self):
        """노드 추가 테스트"""
        graph = RoadGraph()
        node = Node(id=1, lat=37.56, lng=126.97)
        
        graph.add_node(node)
        
        assert graph.node_count == 1
        assert graph.get_node(1) == node
    
    def test_add_edge(self):
        """엣지 추가 테스트"""
        graph = RoadGraph()
        graph.add_node(Node(id=1, lat=37.56, lng=126.97))
        graph.add_node(Node(id=2, lat=37.57, lng=126.97))
        
        edge = Edge(id=1, source_id=1, target_id=2, length_m=100.0)
        graph.add_edge(edge)
        
        assert graph.edge_count == 1
    
    def test_get_neighbors_bidirectional(self, sample_graph: RoadGraph):
        """양방향 인접 노드 조회 테스트"""
        # 노드 1의 이웃
        neighbors_1 = sample_graph.get_neighbors(1)
        assert 2 in neighbors_1
        
        # 노드 2의 이웃 (양방향이므로 1, 3 모두 포함)
        neighbors_2 = sample_graph.get_neighbors(2)
        assert 1 in neighbors_2
        assert 3 in neighbors_2
    
    def test_get_neighbors_oneway(self):
        """일방통행 인접 노드 조회 테스트"""
        graph = RoadGraph()
        graph.add_node(Node(id=1, lat=37.56, lng=126.97))
        graph.add_node(Node(id=2, lat=37.57, lng=126.97))
        
        # 일방통행 엣지
        graph.add_edge(Edge(id=1, source_id=1, target_id=2, length_m=100.0, is_oneway=True))
        
        # 1 -> 2 가능
        assert 2 in graph.get_neighbors(1)
        # 2 -> 1 불가능
        assert 1 not in graph.get_neighbors(2)
    
    def test_get_edges_from(self, sample_graph: RoadGraph):
        """특정 노드에서 출발하는 엣지 조회 테스트"""
        edges = sample_graph.get_edges_from(2)
        
        # 노드 2에서 출발하는 엣지 (2->3)와 양방향으로 도착하는 엣지 (1->2)
        assert len(edges) == 2
    
    def test_get_edge_between(self, sample_graph: RoadGraph):
        """두 노드 사이 엣지 조회 테스트"""
        edge = sample_graph.get_edge_between(1, 2)
        
        assert edge is not None
        assert edge.source_id == 1
        assert edge.target_id == 2
    
    def test_get_edge_between_reverse(self, sample_graph: RoadGraph):
        """역방향 엣지 조회 테스트 (양방향 도로)"""
        edge = sample_graph.get_edge_between(2, 1)
        
        assert edge is not None
    
    def test_get_edge_between_not_found(self, sample_graph: RoadGraph):
        """존재하지 않는 엣지 조회 테스트"""
        edge = sample_graph.get_edge_between(1, 3)
        
        assert edge is None
    
    def test_get_traffic_light_nodes(self, sample_graph: RoadGraph):
        """신호등 노드 조회 테스트"""
        traffic_nodes = sample_graph.get_traffic_light_nodes()
        
        assert len(traffic_nodes) == 1
        assert traffic_nodes[0].id == 3
    
    def test_get_bounding_box(self, sample_graph: RoadGraph):
        """바운딩 박스 조회 테스트"""
        north, south, east, west = sample_graph.get_bounding_box()
        
        assert north == pytest.approx(37.57, rel=1e-3)
        assert south == pytest.approx(37.56, rel=1e-3)
        assert east == pytest.approx(126.98, rel=1e-3)
        assert west == pytest.approx(126.97, rel=1e-3)
    
    def test_get_bounding_box_empty_graph(self):
        """빈 그래프 바운딩 박스 테스트"""
        graph = RoadGraph()
        
        bbox = graph.get_bounding_box()
        
        assert bbox == (0.0, 0.0, 0.0, 0.0)
    
    def test_find_nearest_node(self, sample_graph: RoadGraph):
        """가장 가까운 노드 찾기 테스트"""
        # 노드 1 (37.56, 126.97) 근처 좌표
        nearest = sample_graph.find_nearest_node(lat=37.561, lng=126.971)
        
        assert nearest is not None
        assert nearest.id == 1
    
    def test_find_nearest_node_empty_graph(self):
        """빈 그래프에서 가장 가까운 노드 찾기 테스트"""
        graph = RoadGraph()
        
        nearest = graph.find_nearest_node(lat=37.56, lng=126.97)
        
        assert nearest is None


class TestRoadType:
    """RoadType 열거형 테스트"""
    
    def test_road_types_exist(self):
        """도로 타입 존재 확인"""
        assert RoadType.PRIMARY.value == "primary"
        assert RoadType.SECONDARY.value == "secondary"
        assert RoadType.RESIDENTIAL.value == "residential"
        assert RoadType.FOOTWAY.value == "footway"
        assert RoadType.PATH.value == "path"
        assert RoadType.UNKNOWN.value == "unknown"
