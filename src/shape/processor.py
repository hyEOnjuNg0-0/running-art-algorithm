"""
사용자 입력 도형 처리기
노이즈 제거, 점 단순화, Polyline 변환
"""
import math
from typing import List, Tuple, Optional

from src.domain.entities import Coordinate, BoundingBox, Shape, ShapeType
from src.shape.templates import ShapeTemplate, ShapeTemplateRegistry
from src.shape.transformer import ShapeTransformer


class ShapeProcessor:
    """
    도형 처리기
    
    사용자 입력 도형을 처리하고, 템플릿을 지리 좌표로 변환
    """
    
    def __init__(self):
        self.registry = ShapeTemplateRegistry()
        self.transformer = ShapeTransformer()
    
    def process_user_input(
        self,
        points: List[Coordinate],
        simplify: bool = True,
        smooth: bool = False,
        tolerance: float = 0.0001
    ) -> List[Coordinate]:
        """
        사용자 입력 좌표 처리
        
        Args:
            points: 사용자가 그린 좌표점 목록
            simplify: 점 단순화 여부
            smooth: 스무딩 적용 여부
            tolerance: 단순화 허용 오차
            
        Returns:
            처리된 좌표 목록
        """
        if len(points) < 2:
            return points
        
        result = points
        
        # 1. 중복 점 제거
        result = self._remove_duplicates(result)
        
        # 2. 점 단순화 (Douglas-Peucker 알고리즘)
        if simplify and len(result) > 3:
            result = self._simplify_points(result, tolerance)
        
        # 3. 스무딩 (선택적)
        if smooth and len(result) > 2:
            result = self._smooth_points(result)
        
        return result
    
    def template_to_geo(
        self,
        shape_type: ShapeType,
        bbox: BoundingBox,
        rotation_deg: float = 0.0
    ) -> List[Coordinate]:
        """
        템플릿을 지리 좌표로 변환
        
        Args:
            shape_type: 도형 타입
            bbox: 대상 바운딩 박스
            rotation_deg: 회전 각도 (도)
            
        Returns:
            지리 좌표 목록
        """
        template = self.registry.get_template(shape_type)
        if template is None:
            return []
        
        points = template.get_normalized_points()
        
        # 회전 적용
        if rotation_deg != 0.0:
            points = self.transformer.rotate(points, rotation_deg)
        
        # 지리 좌표로 변환
        return self.transformer.normalize_to_geo(points, bbox)
    
    def generate_all_rotations(
        self,
        shape_type: ShapeType,
        bbox: BoundingBox
    ) -> List[List[Coordinate]]:
        """
        모든 회전 변형 생성 (6방향)
        
        Args:
            shape_type: 도형 타입
            bbox: 대상 바운딩 박스
            
        Returns:
            6방향 회전된 지리 좌표 목록들
        """
        template = self.registry.get_template(shape_type)
        if template is None:
            return []
        
        points = template.get_normalized_points()
        rotations = self.transformer.generate_rotations(points)
        
        return [
            self.transformer.normalize_to_geo(rotated, bbox)
            for rotated in rotations
        ]
    
    def shape_to_geo(
        self,
        shape: Shape,
        bbox: BoundingBox,
        rotation_deg: float = 0.0
    ) -> List[Coordinate]:
        """
        Shape 객체를 지리 좌표로 변환
        
        Args:
            shape: Shape 객체
            bbox: 대상 바운딩 박스
            rotation_deg: 회전 각도
            
        Returns:
            지리 좌표 목록
        """
        if shape.is_custom:
            # 사용자 정의 도형은 이미 지리 좌표
            return self.process_user_input(shape.points)
        else:
            # 템플릿 도형은 변환 필요
            return self.template_to_geo(shape.shape_type, bbox, rotation_deg)
    
    def _remove_duplicates(
        self,
        points: List[Coordinate],
        threshold: float = 1e-8
    ) -> List[Coordinate]:
        """중복 점 제거"""
        if not points:
            return []
        
        result = [points[0]]
        for point in points[1:]:
            last = result[-1]
            dist = math.sqrt(
                (point.lat - last.lat) ** 2 +
                (point.lng - last.lng) ** 2
            )
            if dist > threshold:
                result.append(point)
        
        return result
    
    def _simplify_points(
        self,
        points: List[Coordinate],
        tolerance: float
    ) -> List[Coordinate]:
        """
        Douglas-Peucker 알고리즘으로 점 단순화
        
        Args:
            points: 좌표 목록
            tolerance: 허용 오차
            
        Returns:
            단순화된 좌표 목록
        """
        if len(points) <= 2:
            return points
        
        # 가장 먼 점 찾기
        max_dist = 0.0
        max_idx = 0
        
        start = points[0]
        end = points[-1]
        
        for i in range(1, len(points) - 1):
            dist = self._perpendicular_distance(points[i], start, end)
            if dist > max_dist:
                max_dist = dist
                max_idx = i
        
        # 허용 오차보다 크면 재귀적으로 분할
        if max_dist > tolerance:
            left = self._simplify_points(points[:max_idx + 1], tolerance)
            right = self._simplify_points(points[max_idx:], tolerance)
            return left[:-1] + right
        else:
            return [start, end]
    
    def _perpendicular_distance(
        self,
        point: Coordinate,
        line_start: Coordinate,
        line_end: Coordinate
    ) -> float:
        """점에서 선분까지의 수직 거리"""
        dx = line_end.lng - line_start.lng
        dy = line_end.lat - line_start.lat
        
        # 선분 길이
        line_len = math.sqrt(dx * dx + dy * dy)
        if line_len == 0:
            return math.sqrt(
                (point.lat - line_start.lat) ** 2 +
                (point.lng - line_start.lng) ** 2
            )
        
        # 수직 거리 계산
        dist = abs(
            dy * point.lng - dx * point.lat +
            line_end.lng * line_start.lat - line_end.lat * line_start.lng
        ) / line_len
        
        return dist
    
    def _smooth_points(
        self,
        points: List[Coordinate],
        window_size: int = 3
    ) -> List[Coordinate]:
        """
        이동 평균으로 스무딩
        
        Args:
            points: 좌표 목록
            window_size: 윈도우 크기 (홀수)
            
        Returns:
            스무딩된 좌표 목록
        """
        if len(points) <= window_size:
            return points
        
        half = window_size // 2
        result = []
        
        for i in range(len(points)):
            start = max(0, i - half)
            end = min(len(points), i + half + 1)
            
            avg_lat = sum(p.lat for p in points[start:end]) / (end - start)
            avg_lng = sum(p.lng for p in points[start:end]) / (end - start)
            
            result.append(Coordinate(lat=avg_lat, lng=avg_lng))
        
        return result
    
    def calculate_shape_length(self, points: List[Coordinate]) -> float:
        """
        도형의 총 길이 계산 (km)
        
        Args:
            points: 좌표 목록
            
        Returns:
            총 길이 (km)
        """
        if len(points) < 2:
            return 0.0
        
        total = 0.0
        for i in range(len(points) - 1):
            total += self._haversine_distance(points[i], points[i + 1])
        
        return total
    
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
    
    def resample_points(
        self,
        points: List[Coordinate],
        num_points: int
    ) -> List[Coordinate]:
        """
        점 개수 재샘플링 (균등 간격)
        
        Args:
            points: 원본 좌표 목록
            num_points: 목표 점 개수
            
        Returns:
            재샘플링된 좌표 목록
        """
        if len(points) < 2 or num_points < 2:
            return points
        
        # 총 길이 계산
        total_length = self.calculate_shape_length(points)
        if total_length == 0:
            return points
        
        # 균등 간격으로 샘플링
        segment_length = total_length / (num_points - 1)
        
        result = [points[0]]
        accumulated = 0.0
        current_idx = 0
        
        for i in range(1, num_points - 1):
            target_dist = i * segment_length
            
            while current_idx < len(points) - 1:
                seg_dist = self._haversine_distance(
                    points[current_idx], points[current_idx + 1]
                )
                
                if accumulated + seg_dist >= target_dist:
                    # 이 세그먼트 내에서 보간
                    ratio = (target_dist - accumulated) / seg_dist if seg_dist > 0 else 0
                    lat = points[current_idx].lat + ratio * (
                        points[current_idx + 1].lat - points[current_idx].lat
                    )
                    lng = points[current_idx].lng + ratio * (
                        points[current_idx + 1].lng - points[current_idx].lng
                    )
                    result.append(Coordinate(lat=lat, lng=lng))
                    break
                else:
                    accumulated += seg_dist
                    current_idx += 1
        
        result.append(points[-1])
        return result
