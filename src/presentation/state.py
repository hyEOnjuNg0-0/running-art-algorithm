"""
UI 상태 관리
Streamlit session_state를 활용한 애플리케이션 상태 관리
"""
import streamlit as st
from typing import Optional, List
from dataclasses import dataclass, field

from src.domain.entities import (
    BoundingBox, Shape, ShapeType, Constraints, 
    RouteInfo, Coordinate
)


@dataclass
class AppState:
    """애플리케이션 전체 상태"""
    # 입력 상태
    bounding_box: Optional[BoundingBox] = None
    selected_shape: Optional[Shape] = None
    constraints: Optional[Constraints] = None
    
    # 그리기 모드 상태
    is_drawing_mode: bool = False
    drawing_points: List[Coordinate] = field(default_factory=list)
    
    # 결과 상태
    routes: List[RouteInfo] = field(default_factory=list)
    selected_route_id: Optional[int] = None
    
    # UI 상태
    is_loading: bool = False
    error_message: Optional[str] = None


def init_session_state():
    """세션 상태 초기화"""
    if 'app_state' not in st.session_state:
        st.session_state.app_state = AppState()
    
    # 개별 상태 키 초기화 (컴포넌트 간 통신용)
    defaults = {
        'bounding_box': None,
        'shape_type': ShapeType.HEART.value,
        'custom_points': [],
        'target_distance': 5.0,
        'max_traffic_lights': 5,
        'routes': [],
        'selected_route_id': None,
        'is_loading': False,
        'error_message': None,
        'is_drawing_mode': False,
        'map_center': [37.5665, 126.9780],  # 서울 시청 기본값
        'map_zoom': 14,
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def get_state() -> AppState:
    """현재 상태 반환"""
    return st.session_state.app_state


def set_loading(is_loading: bool):
    """로딩 상태 설정"""
    st.session_state.is_loading = is_loading


def set_error(message: Optional[str]):
    """에러 메시지 설정"""
    st.session_state.error_message = message


def clear_error():
    """에러 메시지 초기화"""
    st.session_state.error_message = None


def set_routes(routes: List[RouteInfo]):
    """경로 결과 설정"""
    st.session_state.routes = routes


def select_route(route_id: Optional[int]):
    """경로 선택"""
    st.session_state.selected_route_id = route_id


def toggle_drawing_mode():
    """그리기 모드 토글"""
    st.session_state.is_drawing_mode = not st.session_state.is_drawing_mode
    if not st.session_state.is_drawing_mode:
        st.session_state.custom_points = []


def add_drawing_point(lat: float, lng: float):
    """그리기 포인트 추가"""
    st.session_state.custom_points.append(Coordinate(lat, lng))


def clear_drawing_points():
    """그리기 포인트 초기화"""
    st.session_state.custom_points = []


def set_bounding_box(bbox: BoundingBox):
    """바운딩 박스 설정"""
    st.session_state.bounding_box = bbox
