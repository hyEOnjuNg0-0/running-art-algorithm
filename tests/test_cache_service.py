"""
그래프 캐싱 서비스 테스트
"""
import json
import pytest
import tempfile
from pathlib import Path

from src.data.entities import Node, Edge, RoadGraph, RoadType
from src.data.cache_service import GraphCacheService
from src.domain.entities import BoundingBox


class TestGraphCacheService:
    """GraphCacheService 테스트"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """임시 캐시 디렉토리"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def cache_service(self, temp_cache_dir) -> GraphCacheService:
        """테스트용 캐시 서비스"""
        return GraphCacheService(cache_dir=temp_cache_dir)
    
    @pytest.fixture
    def sample_graph(self) -> RoadGraph:
        """테스트용 샘플 그래프"""
        graph = RoadGraph()
        
        graph.add_node(Node(id=1, lat=37.56, lng=126.97))
        graph.add_node(Node(id=2, lat=37.57, lng=126.97))
        graph.add_node(Node(id=3, lat=37.57, lng=126.98, has_traffic_light=True))
        
        graph.add_edge(Edge(
            id=1, source_id=1, target_id=2, length_m=100.0,
            road_type=RoadType.RESIDENTIAL, name="테스트로"
        ))
        graph.add_edge(Edge(
            id=2, source_id=2, target_id=3, length_m=150.0,
            road_type=RoadType.FOOTWAY, is_oneway=True
        ))
        
        return graph
    
    def test_get_cache_key_bbox(self, cache_service: GraphCacheService):
        """바운딩 박스 기반 캐시 키 생성 테스트"""
        bbox = BoundingBox(north=37.58, south=37.55, east=127.00, west=126.96)
        
        key1 = cache_service.get_cache_key(bbox=bbox, network_type="walk")
        key2 = cache_service.get_cache_key(bbox=bbox, network_type="walk")
        key3 = cache_service.get_cache_key(bbox=bbox, network_type="bike")
        
        assert key1 == key2  # 동일 파라미터는 동일 키
        assert key1 != key3  # 다른 network_type은 다른 키
    
    def test_get_cache_key_point(self, cache_service: GraphCacheService):
        """지점 기반 캐시 키 생성 테스트"""
        key1 = cache_service.get_cache_key(lat=37.56, lng=126.97, distance_m=1000)
        key2 = cache_service.get_cache_key(lat=37.56, lng=126.97, distance_m=1000)
        key3 = cache_service.get_cache_key(lat=37.56, lng=126.97, distance_m=2000)
        
        assert key1 == key2
        assert key1 != key3
    
    def test_set_and_get(self, cache_service: GraphCacheService, sample_graph: RoadGraph):
        """캐시 저장 및 조회 테스트"""
        cache_key = "test_key"
        
        # 저장
        result = cache_service.set(cache_key, sample_graph)
        assert result is True
        
        # 조회
        loaded_graph = cache_service.get(cache_key)
        
        assert loaded_graph is not None
        assert loaded_graph.node_count == sample_graph.node_count
        assert loaded_graph.edge_count == sample_graph.edge_count
    
    def test_get_nonexistent(self, cache_service: GraphCacheService):
        """존재하지 않는 캐시 조회 테스트"""
        result = cache_service.get("nonexistent_key")
        
        assert result is None
    
    def test_delete(self, cache_service: GraphCacheService, sample_graph: RoadGraph):
        """캐시 삭제 테스트"""
        cache_key = "test_delete_key"
        
        cache_service.set(cache_key, sample_graph)
        assert cache_service.get(cache_key) is not None
        
        # 삭제
        result = cache_service.delete(cache_key)
        assert result is True
        
        # 삭제 후 조회
        assert cache_service.get(cache_key) is None
    
    def test_clear_all(self, cache_service: GraphCacheService, sample_graph: RoadGraph):
        """전체 캐시 삭제 테스트"""
        # 여러 캐시 저장
        cache_service.set("key1", sample_graph)
        cache_service.set("key2", sample_graph)
        cache_service.set("key3", sample_graph)
        
        # 전체 삭제
        count = cache_service.clear_all()
        
        assert count == 3
        assert cache_service.get("key1") is None
        assert cache_service.get("key2") is None
        assert cache_service.get("key3") is None
    
    def test_get_cache_stats(self, cache_service: GraphCacheService, sample_graph: RoadGraph):
        """캐시 통계 테스트"""
        cache_service.set("key1", sample_graph)
        cache_service.set("key2", sample_graph)
        
        stats = cache_service.get_cache_stats()
        
        assert stats["file_count"] == 2
        assert stats["total_size_mb"] >= 0


class TestGraphJsonSerialization:
    """그래프 JSON 직렬화 테스트"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """임시 캐시 디렉토리"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def cache_service(self, temp_cache_dir) -> GraphCacheService:
        """테스트용 캐시 서비스"""
        return GraphCacheService(cache_dir=temp_cache_dir)
    
    @pytest.fixture
    def sample_graph(self) -> RoadGraph:
        """테스트용 샘플 그래프"""
        graph = RoadGraph()
        
        graph.add_node(Node(id=1, lat=37.56, lng=126.97))
        graph.add_node(Node(id=2, lat=37.57, lng=126.97, has_traffic_light=True))
        
        graph.add_edge(Edge(
            id=1, source_id=1, target_id=2, length_m=100.0,
            road_type=RoadType.RESIDENTIAL, name="테스트로"
        ))
        
        return graph
    
    def test_export_to_json(self, cache_service: GraphCacheService, sample_graph: RoadGraph, temp_cache_dir):
        """JSON 내보내기 테스트"""
        filepath = Path(temp_cache_dir) / "test_graph.json"
        
        result = cache_service.export_to_json(sample_graph, str(filepath))
        
        assert result is True
        assert filepath.exists()
        
        # JSON 내용 확인
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1
        assert data["edges"][0]["name"] == "테스트로"
    
    def test_import_from_json(self, cache_service: GraphCacheService, sample_graph: RoadGraph, temp_cache_dir):
        """JSON 가져오기 테스트"""
        filepath = Path(temp_cache_dir) / "test_graph.json"
        
        # 먼저 내보내기
        cache_service.export_to_json(sample_graph, str(filepath))
        
        # 가져오기
        loaded_graph = cache_service.import_from_json(str(filepath))
        
        assert loaded_graph is not None
        assert loaded_graph.node_count == sample_graph.node_count
        assert loaded_graph.edge_count == sample_graph.edge_count
        
        # 노드 속성 확인
        node2 = loaded_graph.get_node(2)
        assert node2 is not None
        assert node2.has_traffic_light is True
    
    def test_import_nonexistent_file(self, cache_service: GraphCacheService):
        """존재하지 않는 파일 가져오기 테스트"""
        result = cache_service.import_from_json("nonexistent.json")
        
        assert result is None
    
    def test_roundtrip_preserves_data(self, cache_service: GraphCacheService, temp_cache_dir):
        """JSON 왕복 변환 데이터 보존 테스트"""
        # 복잡한 그래프 생성
        original = RoadGraph()
        original.add_node(Node(id=100, lat=37.5665, lng=126.9780, has_traffic_light=True))
        original.add_node(Node(id=200, lat=37.5700, lng=126.9800))
        original.add_edge(Edge(
            id=1, source_id=100, target_id=200, length_m=500.5,
            road_type=RoadType.PRIMARY, name="세종대로", is_oneway=True
        ))
        
        filepath = Path(temp_cache_dir) / "roundtrip.json"
        
        # 내보내기 후 가져오기
        cache_service.export_to_json(original, str(filepath))
        loaded = cache_service.import_from_json(str(filepath))
        
        # 검증
        assert loaded is not None
        
        node100 = loaded.get_node(100)
        assert node100.lat == 37.5665
        assert node100.lng == 126.9780
        assert node100.has_traffic_light is True
        
        edges = loaded.get_edges_from(100)
        assert len(edges) == 1
        assert edges[0].length_m == 500.5
        assert edges[0].road_type == RoadType.PRIMARY
        assert edges[0].name == "세종대로"
        assert edges[0].is_oneway is True
