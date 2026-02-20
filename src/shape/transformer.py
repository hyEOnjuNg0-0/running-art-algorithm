"""
도형 변환기
스케일링, 회전, 좌표 변환 기능 제공
"""
import math
from dataclasses import dataclass
from typing import List, Tuple

from src.domain.entities import Coordinate, BoundingBox


@dataclass
class TransformParams:
    """변환 파라미터"""
    rotation_deg: float = 0.0  # 회전 각도 (도)
    scale_x: float = 1.0       # X축 스케일
    scale_y: float = 1.0       # Y축 스케일
    translate_x: float = 0.0   # X축 이동
    translate_y: float = 0.0   # Y축 이동


class ShapeTransformer:
    """
    도형 변환기
    
    정규화 좌표를 지리 좌표로 변환하고,
    스케일링, 회전 등의 변환을 수행
    """
    
    # 6방향 회전 각도 (60° 간격)
    ROTATION_ANGLES = [0, 60, 120, 180, 240, 300]
    
    def normalize_to_geo(
        self,
        normalized_points: List[Tuple[float, float]],
        bbox: BoundingBox
    ) -> List[Coordinate]:
        """
        정규화 좌표를 지리 좌표로 변환
        
        Args:
            normalized_points: 정규화 좌표 목록 (-1 ~ 1 범위)
            bbox: 대상 바운딩 박스
            
        Returns:
            지리 좌표 목록
        """
        center = bbox.center
        
        # bbox 크기 계산
        lat_range = (bbox.north - bbox.south) / 2
        lng_range = (bbox.east - bbox.west) / 2
        
        result = []
        for x, y in normalized_points:
            # 정규화 좌표를 지리 좌표로 변환
            # x -> 경도, y -> 위도
            lat = center.lat + y * lat_range
            lng = center.lng + x * lng_range
            result.append(Coordinate(lat=lat, lng=lng))
        
        return result
    
    def rotate(
        self,
        points: List[Tuple[float, float]],
        angle_deg: float,
        center: Tuple[float, float] = (0.0, 0.0)
    ) -> List[Tuple[float, float]]:
        """
        점들을 특정 각도로 회전
        
        Args:
            points: 좌표 목록
            angle_deg: 회전 각도 (도, 반시계 방향)
            center: 회전 중심
            
        Returns:
            회전된 좌표 목록
        """
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        cx, cy = center
        
        result = []
        for x, y in points:
            # 중심점 기준으로 이동
            dx = x - cx
            dy = y - cy
            # 회전 변환
            new_x = dx * cos_a - dy * sin_a + cx
            new_y = dx * sin_a + dy * cos_a + cy
            result.append((new_x, new_y))
        
        return result
    
    def scale(
        self,
        points: List[Tuple[float, float]],
        scale_x: float,
        scale_y: float,
        center: Tuple[float, float] = (0.0, 0.0)
    ) -> List[Tuple[float, float]]:
        """
        점들을 스케일링
        
        Args:
            points: 좌표 목록
            scale_x: X축 스케일 배율
            scale_y: Y축 스케일 배율
            center: 스케일 중심
            
        Returns:
            스케일된 좌표 목록
        """
        cx, cy = center
        
        result = []
        for x, y in points:
            new_x = cx + (x - cx) * scale_x
            new_y = cy + (y - cy) * scale_y
            result.append((new_x, new_y))
        
        return result
    
    def translate(
        self,
        points: List[Tuple[float, float]],
        dx: float,
        dy: float
    ) -> List[Tuple[float, float]]:
        """
        점들을 이동
        
        Args:
            points: 좌표 목록
            dx: X축 이동량
            dy: Y축 이동량
            
        Returns:
            이동된 좌표 목록
        """
        return [(x + dx, y + dy) for x, y in points]
    
    def apply_transform(
        self,
        points: List[Tuple[float, float]],
        params: TransformParams
    ) -> List[Tuple[float, float]]:
        """
        복합 변환 적용 (스케일 -> 회전 -> 이동 순서)
        
        Args:
            points: 좌표 목록
            params: 변환 파라미터
            
        Returns:
            변환된 좌표 목록
        """
        result = points
        
        # 1. 스케일링
        if params.scale_x != 1.0 or params.scale_y != 1.0:
            result = self.scale(result, params.scale_x, params.scale_y)
        
        # 2. 회전
        if params.rotation_deg != 0.0:
            result = self.rotate(result, params.rotation_deg)
        
        # 3. 이동
        if params.translate_x != 0.0 or params.translate_y != 0.0:
            result = self.translate(result, params.translate_x, params.translate_y)
        
        return result
    
    def generate_rotations(
        self,
        points: List[Tuple[float, float]],
        angles: List[float] = None
    ) -> List[List[Tuple[float, float]]]:
        """
        여러 각도로 회전된 도형 목록 생성
        
        Args:
            points: 원본 좌표 목록
            angles: 회전 각도 목록 (기본: 6방향)
            
        Returns:
            회전된 도형 목록
        """
        if angles is None:
            angles = self.ROTATION_ANGLES
        
        return [self.rotate(points, angle) for angle in angles]
    
    def geo_to_normalized(
        self,
        coordinates: List[Coordinate],
        bbox: BoundingBox
    ) -> List[Tuple[float, float]]:
        """
        지리 좌표를 정규화 좌표로 변환
        
        Args:
            coordinates: 지리 좌표 목록
            bbox: 기준 바운딩 박스
            
        Returns:
            정규화 좌표 목록 (-1 ~ 1 범위)
        """
        center = bbox.center
        lat_range = (bbox.north - bbox.south) / 2
        lng_range = (bbox.east - bbox.west) / 2
        
        # 0으로 나누기 방지
        if lat_range == 0:
            lat_range = 0.001
        if lng_range == 0:
            lng_range = 0.001
        
        result = []
        for coord in coordinates:
            x = (coord.lng - center.lng) / lng_range
            y = (coord.lat - center.lat) / lat_range
            result.append((x, y))
        
        return result
    
    def calculate_bounding_box(
        self,
        points: List[Tuple[float, float]]
    ) -> Tuple[float, float, float, float]:
        """
        점들의 바운딩 박스 계산
        
        Args:
            points: 좌표 목록
            
        Returns:
            (min_x, min_y, max_x, max_y)
        """
        if not points:
            return (0.0, 0.0, 0.0, 0.0)
        
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        
        return (min(xs), min(ys), max(xs), max(ys))
    
    def fit_to_bbox(
        self,
        points: List[Tuple[float, float]],
        target_bbox: Tuple[float, float, float, float],
        maintain_aspect: bool = True
    ) -> List[Tuple[float, float]]:
        """
        점들을 대상 바운딩 박스에 맞게 조정
        
        Args:
            points: 좌표 목록
            target_bbox: 대상 바운딩 박스 (min_x, min_y, max_x, max_y)
            maintain_aspect: 종횡비 유지 여부
            
        Returns:
            조정된 좌표 목록
        """
        if not points:
            return []
        
        # 현재 바운딩 박스
        curr_min_x, curr_min_y, curr_max_x, curr_max_y = self.calculate_bounding_box(points)
        curr_width = curr_max_x - curr_min_x
        curr_height = curr_max_y - curr_min_y
        
        # 대상 바운딩 박스
        tgt_min_x, tgt_min_y, tgt_max_x, tgt_max_y = target_bbox
        tgt_width = tgt_max_x - tgt_min_x
        tgt_height = tgt_max_y - tgt_min_y
        
        # 0으로 나누기 방지
        if curr_width == 0:
            curr_width = 0.001
        if curr_height == 0:
            curr_height = 0.001
        
        # 스케일 계산
        scale_x = tgt_width / curr_width
        scale_y = tgt_height / curr_height
        
        if maintain_aspect:
            scale = min(scale_x, scale_y)
            scale_x = scale_y = scale
        
        # 중심점 계산
        curr_center_x = (curr_min_x + curr_max_x) / 2
        curr_center_y = (curr_min_y + curr_max_y) / 2
        tgt_center_x = (tgt_min_x + tgt_max_x) / 2
        tgt_center_y = (tgt_min_y + tgt_max_y) / 2
        
        # 변환 적용
        result = []
        for x, y in points:
            new_x = (x - curr_center_x) * scale_x + tgt_center_x
            new_y = (y - curr_center_y) * scale_y + tgt_center_y
            result.append((new_x, new_y))
        
        return result
