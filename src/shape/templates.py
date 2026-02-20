"""
도형 템플릿 정의
기본 도형 및 알파벳/숫자 템플릿을 정규화 좌표로 저장
"""
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional

from src.domain.entities import ShapeType


@dataclass
class ShapeTemplate:
    """
    도형 템플릿
    
    정규화 좌표 (-1 ~ 1 범위)로 도형을 정의
    중심점은 (0, 0)
    """
    shape_type: ShapeType
    points: List[Tuple[float, float]]  # 정규화 좌표 (x, y) 목록
    name: str = ""
    closed: bool = True  # 닫힌 도형 여부
    
    @property
    def point_count(self) -> int:
        return len(self.points)
    
    def get_normalized_points(self) -> List[Tuple[float, float]]:
        """정규화 좌표 반환"""
        return self.points.copy()


class ShapeTemplateRegistry:
    """
    도형 템플릿 레지스트리
    
    미리 정의된 도형 템플릿을 관리
    """
    
    def __init__(self):
        self._templates: Dict[ShapeType, ShapeTemplate] = {}
        self._init_default_templates()
    
    def _init_default_templates(self):
        """기본 도형 템플릿 초기화"""
        self._templates[ShapeType.CIRCLE] = self._create_circle()
        self._templates[ShapeType.HEART] = self._create_heart()
        self._templates[ShapeType.STAR] = self._create_star()
        # 숫자 템플릿 (0~9)
        self._init_digit_templates()
    
    def get_template(self, shape_type: ShapeType) -> Optional[ShapeTemplate]:
        """템플릿 조회"""
        return self._templates.get(shape_type)
    
    def register_template(self, template: ShapeTemplate) -> None:
        """커스텀 템플릿 등록"""
        self._templates[template.shape_type] = template
    
    def get_available_types(self) -> List[ShapeType]:
        """사용 가능한 템플릿 타입 목록"""
        return list(self._templates.keys())
    
    def _create_circle(self, num_points: int = 36) -> ShapeTemplate:
        """원 템플릿 생성"""
        points = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = math.cos(angle)
            y = math.sin(angle)
            points.append((x, y))
        
        return ShapeTemplate(
            shape_type=ShapeType.CIRCLE,
            points=points,
            name="원",
            closed=True
        )
    
    def _create_heart(self, num_points: int = 50) -> ShapeTemplate:
        """하트 템플릿 생성 (파라메트릭 방정식 사용)"""
        points = []
        for i in range(num_points):
            t = 2 * math.pi * i / num_points
            # 하트 파라메트릭 방정식
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
            # 정규화 (-1 ~ 1)
            x = x / 17
            y = y / 17
            points.append((x, y))
        
        return ShapeTemplate(
            shape_type=ShapeType.HEART,
            points=points,
            name="하트",
            closed=True
        )
    
    def _create_star(self, num_points: int = 5) -> ShapeTemplate:
        """별 템플릿 생성"""
        points = []
        outer_radius = 0.9
        inner_radius = 0.4
        
        for i in range(num_points * 2):
            angle = math.pi / 2 + (2 * math.pi * i) / (num_points * 2)
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            points.append((x, y))
        
        return ShapeTemplate(
            shape_type=ShapeType.STAR,
            points=points,
            name="별",
            closed=True
        )


    def _init_digit_templates(self):
        """숫자 템플릿 초기화 (0~9)"""
        digit_data = self._get_digit_points()
        
        digit_types = [
            ShapeType.DIGIT_0, ShapeType.DIGIT_1, ShapeType.DIGIT_2,
            ShapeType.DIGIT_3, ShapeType.DIGIT_4, ShapeType.DIGIT_5,
            ShapeType.DIGIT_6, ShapeType.DIGIT_7, ShapeType.DIGIT_8,
            ShapeType.DIGIT_9
        ]
        
        for i, shape_type in enumerate(digit_types):
            self._templates[shape_type] = ShapeTemplate(
                shape_type=shape_type,
                points=digit_data[i],
                name=str(i),
                closed=False
            )
    
    def _get_digit_points(self) -> List[List[Tuple[float, float]]]:
        """
        숫자 0~9의 좌표점 반환
        한 붓 그리기 스타일로 정의 (러닝 코스에 적합)
        """
        return [
            # 0: 타원형 (시계 방향)
            self._create_oval_points(),
            
            # 1: 세로선 (위에서 아래로)
            [
                (-0.2, 0.6), (0, 0.8), (0, -0.8)
            ],
            
            # 2: 위에서 시작해서 아래로
            [
                (-0.5, 0.5), (-0.3, 0.8), (0.3, 0.8), (0.5, 0.5),
                (0.5, 0.2), (-0.5, -0.8), (0.5, -0.8)
            ],
            
            # 3: 위에서 아래로 두 개의 곡선
            [
                (-0.5, 0.8), (0.3, 0.8), (0.5, 0.5), (0.3, 0.1),
                (0, 0), (0.3, -0.1), (0.5, -0.5), (0.3, -0.8), (-0.5, -0.8)
            ],
            
            # 4: ㄱ자 형태 + 세로선
            [
                (0.3, -0.8), (0.3, 0.8), (-0.5, -0.2), (0.5, -0.2)
            ],
            
            # 5: 위에서 아래로
            [
                (0.5, 0.8), (-0.5, 0.8), (-0.5, 0.1), (0.3, 0.1),
                (0.5, -0.2), (0.5, -0.5), (0.3, -0.8), (-0.5, -0.8)
            ],
            
            # 6: 위에서 시작해서 아래 원
            [
                (0.3, 0.8), (-0.3, 0.8), (-0.5, 0.5), (-0.5, -0.5),
                (-0.3, -0.8), (0.3, -0.8), (0.5, -0.5), (0.5, -0.2),
                (0.3, 0), (-0.5, 0)
            ],
            
            # 7: 위에서 대각선으로
            [
                (-0.5, 0.8), (0.5, 0.8), (0, -0.8)
            ],
            
            # 8: 8자 형태 (위 원 -> 아래 원)
            [
                (0, 0.1), (-0.4, 0.3), (-0.4, 0.6), (0, 0.8),
                (0.4, 0.6), (0.4, 0.3), (0, 0.1),
                (-0.5, -0.2), (-0.5, -0.6), (0, -0.8),
                (0.5, -0.6), (0.5, -0.2), (0, 0.1)
            ],
            
            # 9: 위 원에서 아래로
            [
                (0.5, 0), (0.3, 0), (-0.5, 0.2), (-0.5, 0.5),
                (-0.3, 0.8), (0.3, 0.8), (0.5, 0.5), (0.5, -0.5),
                (0.3, -0.8), (-0.3, -0.8)
            ],
        ]
    
    def _create_oval_points(self, num_points: int = 24) -> List[Tuple[float, float]]:
        """타원형 점 생성 (숫자 0용)"""
        import math
        points = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points - math.pi / 2  # 상단에서 시작
            x = 0.5 * math.cos(angle)
            y = 0.8 * math.sin(angle)
            points.append((x, y))
        return points
