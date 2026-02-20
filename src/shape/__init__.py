"""
도형 처리 레이어
템플릿 관리, 도형 변환, 사용자 입력 처리
"""
from src.shape.templates import ShapeTemplate, ShapeTemplateRegistry
from src.shape.transformer import ShapeTransformer
from src.shape.processor import ShapeProcessor

__all__ = [
    'ShapeTemplate',
    'ShapeTemplateRegistry',
    'ShapeTransformer',
    'ShapeProcessor',
]
