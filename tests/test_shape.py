"""
도형 처리 레이어 테스트
"""
import math
import pytest
from src.domain.entities import Coordinate, BoundingBox, Shape, ShapeType
from src.shape.templates import ShapeTemplate, ShapeTemplateRegistry
from src.shape.transformer import ShapeTransformer, TransformParams
from src.shape.processor import ShapeProcessor


class TestShapeTemplate:
    """ShapeTemplate 테스트"""
    
    def test_create_template(self):
        """템플릿 생성 테스트"""
        points = [(0, 1), (-1, -1), (1, -1)]
        template = ShapeTemplate(
            shape_type=ShapeType.DIGIT_0,
            points=points,
            name="0"
        )
        
        assert template.shape_type == ShapeType.DIGIT_0
        assert template.point_count == 3
        assert template.name == "0"
        assert template.closed is True
    
    def test_get_normalized_points(self):
        """정규화 좌표 반환 테스트"""
        points = [(0, 1), (-1, -1), (1, -1)]
        template = ShapeTemplate(shape_type=ShapeType.DIGIT_0, points=points)
        
        result = template.get_normalized_points()
        
        assert result == points
        # 원본 수정 방지 확인
        result.append((0, 0))
        assert template.point_count == 3


class TestShapeTemplateRegistry:
    """ShapeTemplateRegistry 테스트"""
    
    @pytest.fixture
    def registry(self) -> ShapeTemplateRegistry:
        return ShapeTemplateRegistry()
    
    def test_default_templates_exist(self, registry: ShapeTemplateRegistry):
        """기본 템플릿 존재 확인"""
        available = registry.get_available_types()
        
        assert ShapeType.CIRCLE in available
        assert ShapeType.HEART in available
        assert ShapeType.STAR in available
        # 숫자 템플릿 확인
        assert ShapeType.DIGIT_0 in available
        assert ShapeType.DIGIT_5 in available
        assert ShapeType.DIGIT_9 in available
    
    def test_get_circle_template(self, registry: ShapeTemplateRegistry):
        """원 템플릿 조회 테스트"""
        template = registry.get_template(ShapeType.CIRCLE)
        
        assert template is not None
        assert template.shape_type == ShapeType.CIRCLE
        assert template.point_count == 36
        assert template.name == "원"
    
    def test_get_heart_template(self, registry: ShapeTemplateRegistry):
        """하트 템플릿 조회 테스트"""
        template = registry.get_template(ShapeType.HEART)
        
        assert template is not None
        assert template.shape_type == ShapeType.HEART
        assert template.point_count == 50
    
    def test_get_star_template(self, registry: ShapeTemplateRegistry):
        """별 템플릿 조회 테스트"""
        template = registry.get_template(ShapeType.STAR)
        
        assert template is not None
        assert template.shape_type == ShapeType.STAR
        assert template.point_count == 10  # 5각 별 = 10개 점
    
    def test_get_nonexistent_template(self, registry: ShapeTemplateRegistry):
        """존재하지 않는 템플릿 조회 테스트"""
        template = registry.get_template(ShapeType.CUSTOM)
        
        assert template is None
    
    def test_register_custom_template(self, registry: ShapeTemplateRegistry):
        """커스텀 템플릿 등록 테스트"""
        custom = ShapeTemplate(
            shape_type=ShapeType.CUSTOM,
            points=[(0, 0), (1, 0), (1, 1)],
            name="커스텀"
        )
        
        registry.register_template(custom)
        
        result = registry.get_template(ShapeType.CUSTOM)
        assert result is not None
        assert result.name == "커스텀"


class TestShapeTransformer:
    """ShapeTransformer 테스트"""
    
    @pytest.fixture
    def transformer(self) -> ShapeTransformer:
        return ShapeTransformer()
    
    @pytest.fixture
    def sample_bbox(self) -> BoundingBox:
        """서울 시청 근처 바운딩 박스"""
        return BoundingBox(
            north=37.58,
            south=37.56,
            east=126.99,
            west=126.97
        )
    
    def test_normalize_to_geo(self, transformer: ShapeTransformer, sample_bbox: BoundingBox):
        """정규화 좌표 -> 지리 좌표 변환 테스트"""
        normalized = [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)]
        
        result = transformer.normalize_to_geo(normalized, sample_bbox)
        
        assert len(result) == 5
        # 중심점 (0, 0) -> bbox 중심
        center = result[0]
        assert center.lat == pytest.approx(37.57, rel=1e-3)
        assert center.lng == pytest.approx(126.98, rel=1e-3)
    
    def test_rotate_90_degrees(self, transformer: ShapeTransformer):
        """90도 회전 테스트"""
        points = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        
        result = transformer.rotate(points, 90)
        
        # (1, 0) -> (0, 1)
        assert result[0][0] == pytest.approx(0, abs=1e-10)
        assert result[0][1] == pytest.approx(1, abs=1e-10)
    
    def test_rotate_180_degrees(self, transformer: ShapeTransformer):
        """180도 회전 테스트"""
        points = [(1, 0)]
        
        result = transformer.rotate(points, 180)
        
        # (1, 0) -> (-1, 0)
        assert result[0][0] == pytest.approx(-1, abs=1e-10)
        assert result[0][1] == pytest.approx(0, abs=1e-10)
    
    def test_scale(self, transformer: ShapeTransformer):
        """스케일링 테스트"""
        points = [(1, 1), (-1, -1)]
        
        result = transformer.scale(points, 2.0, 2.0)
        
        assert result[0] == pytest.approx((2, 2), rel=1e-10)
        assert result[1] == pytest.approx((-2, -2), rel=1e-10)
    
    def test_translate(self, transformer: ShapeTransformer):
        """이동 테스트"""
        points = [(0, 0), (1, 1)]
        
        result = transformer.translate(points, 5, 10)
        
        assert result[0] == (5, 10)
        assert result[1] == (6, 11)
    
    def test_apply_transform(self, transformer: ShapeTransformer):
        """복합 변환 테스트"""
        points = [(1, 0)]
        params = TransformParams(
            scale_x=2.0,
            scale_y=2.0,
            rotation_deg=90,
            translate_x=1,
            translate_y=1
        )
        
        result = transformer.apply_transform(points, params)
        
        # (1, 0) -> scale(2, 0) -> rotate(0, 2) -> translate(1, 3)
        assert result[0][0] == pytest.approx(1, abs=1e-10)
        assert result[0][1] == pytest.approx(3, abs=1e-10)
    
    def test_generate_rotations(self, transformer: ShapeTransformer):
        """6방향 회전 생성 테스트"""
        points = [(1, 0)]
        
        rotations = transformer.generate_rotations(points)
        
        assert len(rotations) == 6  # 0, 60, 120, 180, 240, 300도
    
    def test_geo_to_normalized(self, transformer: ShapeTransformer, sample_bbox: BoundingBox):
        """지리 좌표 -> 정규화 좌표 변환 테스트"""
        coords = [
            Coordinate(lat=37.57, lng=126.98),  # 중심
            Coordinate(lat=37.58, lng=126.98),  # 북쪽
        ]
        
        result = transformer.geo_to_normalized(coords, sample_bbox)
        
        # 중심점은 (0, 0)
        assert result[0][0] == pytest.approx(0, abs=1e-10)
        assert result[0][1] == pytest.approx(0, abs=1e-10)
        # 북쪽은 y = 1
        assert result[1][1] == pytest.approx(1, abs=1e-10)
    
    def test_calculate_bounding_box(self, transformer: ShapeTransformer):
        """바운딩 박스 계산 테스트"""
        points = [(0, 0), (2, 3), (-1, -2)]
        
        min_x, min_y, max_x, max_y = transformer.calculate_bounding_box(points)
        
        assert min_x == -1
        assert min_y == -2
        assert max_x == 2
        assert max_y == 3
    
    def test_fit_to_bbox(self, transformer: ShapeTransformer):
        """바운딩 박스에 맞추기 테스트"""
        points = [(-1, -1), (1, 1)]
        target_bbox = (0, 0, 10, 10)
        
        result = transformer.fit_to_bbox(points, target_bbox, maintain_aspect=True)
        
        # 중심이 (5, 5)로 이동
        center_x = (result[0][0] + result[1][0]) / 2
        center_y = (result[0][1] + result[1][1]) / 2
        assert center_x == pytest.approx(5, abs=0.1)
        assert center_y == pytest.approx(5, abs=0.1)


class TestShapeProcessor:
    """ShapeProcessor 테스트"""
    
    @pytest.fixture
    def processor(self) -> ShapeProcessor:
        return ShapeProcessor()
    
    @pytest.fixture
    def sample_bbox(self) -> BoundingBox:
        return BoundingBox(
            north=37.58,
            south=37.56,
            east=126.99,
            west=126.97
        )
    
    def test_template_to_geo(self, processor: ShapeProcessor, sample_bbox: BoundingBox):
        """템플릿 -> 지리 좌표 변환 테스트"""
        result = processor.template_to_geo(ShapeType.CIRCLE, sample_bbox)
        
        assert len(result) == 36
        # 모든 좌표가 bbox 내에 있어야 함
        for coord in result:
            assert sample_bbox.south <= coord.lat <= sample_bbox.north
            assert sample_bbox.west <= coord.lng <= sample_bbox.east
    
    def test_template_to_geo_with_rotation(self, processor: ShapeProcessor, sample_bbox: BoundingBox):
        """회전된 템플릿 변환 테스트"""
        result_0 = processor.template_to_geo(ShapeType.DIGIT_7, sample_bbox, rotation_deg=0)
        result_45 = processor.template_to_geo(ShapeType.DIGIT_7, sample_bbox, rotation_deg=45)
        
        # 회전 후 좌표가 달라야 함
        assert result_0[0].lat != result_45[0].lat or result_0[0].lng != result_45[0].lng
    
    def test_digit_templates(self, processor: ShapeProcessor, sample_bbox: BoundingBox):
        """숫자 템플릿 변환 테스트"""
        for digit in range(10):
            shape_type = getattr(ShapeType, f"DIGIT_{digit}")
            result = processor.template_to_geo(shape_type, sample_bbox)
            
            assert len(result) > 0, f"숫자 {digit} 템플릿이 비어있음"
    
    def test_generate_all_rotations(self, processor: ShapeProcessor, sample_bbox: BoundingBox):
        """모든 회전 변형 생성 테스트"""
        rotations = processor.generate_all_rotations(ShapeType.HEART, sample_bbox)
        
        assert len(rotations) == 6
        for rotation in rotations:
            assert len(rotation) == 50  # 하트 템플릿 점 개수
    
    def test_process_user_input_removes_duplicates(self, processor: ShapeProcessor):
        """중복 점 제거 테스트"""
        points = [
            Coordinate(lat=37.56, lng=126.97),
            Coordinate(lat=37.56, lng=126.97),  # 중복
            Coordinate(lat=37.57, lng=126.98),
        ]
        
        result = processor.process_user_input(points, simplify=False)
        
        assert len(result) == 2
    
    def test_process_user_input_simplifies(self, processor: ShapeProcessor):
        """점 단순화 테스트"""
        # 직선 위의 점들
        points = [
            Coordinate(lat=37.56, lng=126.97),
            Coordinate(lat=37.565, lng=126.975),  # 중간점 (직선 위)
            Coordinate(lat=37.57, lng=126.98),
        ]
        
        result = processor.process_user_input(points, simplify=True, tolerance=0.001)
        
        # 직선 위의 중간점은 제거됨
        assert len(result) <= 3
    
    def test_shape_to_geo_template(self, processor: ShapeProcessor, sample_bbox: BoundingBox):
        """Shape 객체 (템플릿) 변환 테스트"""
        shape = Shape(shape_type=ShapeType.STAR)
        
        result = processor.shape_to_geo(shape, sample_bbox)
        
        assert len(result) == 10
    
    def test_shape_to_geo_custom(self, processor: ShapeProcessor, sample_bbox: BoundingBox):
        """Shape 객체 (사용자 정의) 변환 테스트"""
        custom_points = [
            Coordinate(lat=37.56, lng=126.97),
            Coordinate(lat=37.57, lng=126.98),
        ]
        shape = Shape(shape_type=ShapeType.CUSTOM, points=custom_points)
        
        result = processor.shape_to_geo(shape, sample_bbox)
        
        # 사용자 정의는 그대로 반환 (이미 지리 좌표)
        assert len(result) == 2
    
    def test_calculate_shape_length(self, processor: ShapeProcessor):
        """도형 길이 계산 테스트"""
        # 약 1km 거리의 두 점
        points = [
            Coordinate(lat=37.5665, lng=126.9780),
            Coordinate(lat=37.5755, lng=126.9780),  # 북쪽으로 약 1km
        ]
        
        length = processor.calculate_shape_length(points)
        
        assert 0.5 < length < 1.5  # 약 1km
    
    def test_resample_points(self, processor: ShapeProcessor):
        """점 재샘플링 테스트"""
        points = [
            Coordinate(lat=37.56, lng=126.97),
            Coordinate(lat=37.58, lng=126.99),
        ]
        
        result = processor.resample_points(points, num_points=5)
        
        assert len(result) == 5
        # 첫 점과 마지막 점은 유지
        assert result[0].lat == points[0].lat
        assert result[-1].lat == points[-1].lat


class TestIntegration:
    """통합 테스트"""
    
    def test_full_workflow_template(self):
        """템플릿 도형 전체 워크플로우 테스트"""
        processor = ShapeProcessor()
        bbox = BoundingBox(north=37.58, south=37.56, east=126.99, west=126.97)
        
        # 1. 하트 템플릿 선택
        shape = Shape(shape_type=ShapeType.HEART)
        
        # 2. 지리 좌표로 변환
        coords = processor.shape_to_geo(shape, bbox)
        
        # 3. 검증
        assert len(coords) > 0
        assert all(isinstance(c, Coordinate) for c in coords)
        
        # 4. 길이 계산
        length = processor.calculate_shape_length(coords)
        assert length > 0
    
    def test_full_workflow_custom(self):
        """사용자 정의 도형 전체 워크플로우 테스트"""
        processor = ShapeProcessor()
        bbox = BoundingBox(north=37.58, south=37.56, east=126.99, west=126.97)
        
        # 1. 사용자가 그린 점들
        user_points = [
            Coordinate(lat=37.56, lng=126.97),
            Coordinate(lat=37.565, lng=126.975),
            Coordinate(lat=37.57, lng=126.98),
            Coordinate(lat=37.575, lng=126.985),
            Coordinate(lat=37.58, lng=126.99),
        ]
        
        # 2. Shape 객체 생성
        shape = Shape(shape_type=ShapeType.CUSTOM, points=user_points)
        
        # 3. 처리 및 변환
        coords = processor.shape_to_geo(shape, bbox)
        
        # 4. 검증
        assert len(coords) > 0
        
        # 5. 길이 계산
        length = processor.calculate_shape_length(coords)
        assert length > 0
