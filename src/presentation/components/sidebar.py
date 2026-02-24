"""
사이드바 컴포넌트
입력 컨트롤을 포함하는 사이드바 UI
"""
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from typing import Callable, Optional
import json

from src.domain.entities import ShapeType, Constraints, Shape, Coordinate


def render_sidebar(on_search: Optional[Callable] = None):
    """
    사이드바 렌더링
    
    Args:
        on_search: 검색 버튼 클릭 시 호출될 콜백 함수
    """
    with st.sidebar:
        st.title("🏃 러닝 코스 설정")
        
        # 1. 모양 선택 섹션
        _render_shape_section()
        
        st.divider()
        
        # 2. 제약 조건 섹션
        _render_constraints_section()
        
        st.divider()
        
        # 3. 검색 버튼
        _render_search_button(on_search)
        
        # 4. 선택된 영역 정보 표시
        _render_selection_info()


def _render_shape_section():
    """모양 선택 섹션"""
    st.subheader("📐 모양 선택")
    
    # 템플릿 선택
    shape_options = {
        ShapeType.HEART.value: "❤️ 하트",
        ShapeType.CIRCLE.value: "⭕ 원",
        ShapeType.STAR.value: "⭐ 별",
        ShapeType.DIGIT_0.value: "0️⃣ 숫자 0",
        ShapeType.DIGIT_1.value: "1️⃣ 숫자 1",
        ShapeType.DIGIT_2.value: "2️⃣ 숫자 2",
        ShapeType.DIGIT_3.value: "3️⃣ 숫자 3",
        ShapeType.DIGIT_4.value: "4️⃣ 숫자 4",
        ShapeType.DIGIT_5.value: "5️⃣ 숫자 5",
        ShapeType.DIGIT_6.value: "6️⃣ 숫자 6",
        ShapeType.DIGIT_7.value: "7️⃣ 숫자 7",
        ShapeType.DIGIT_8.value: "8️⃣ 숫자 8",
        ShapeType.DIGIT_9.value: "9️⃣ 숫자 9",
        ShapeType.CUSTOM.value: "✏️ 직접 그리기",
    }
    
    selected = st.selectbox(
        "모양 템플릿",
        options=list(shape_options.keys()),
        format_func=lambda x: shape_options[x],
        key="shape_type",
        help="원하는 러닝 코스 모양을 선택하세요"
    )
    
    # 직접 그리기 모드 - 사이드바 내 캔버스로 그리기
    if selected == ShapeType.CUSTOM.value:
        _render_shape_drawing_canvas()


def _render_shape_drawing_canvas():
    """사이드바 내 모양 직접 그리기 캔버스 (그림판 스타일)"""
    st.info("🖌️ 아래 캔버스에 원하는 모양을 그려주세요")
    
    # 그리기 모드 선택
    drawing_mode = st.radio(
        "그리기 도구",
        options=["freedraw", "line", "circle", "rect"],
        format_func=lambda x: {
            "freedraw": "✏️ 자유 그리기",
            "line": "📏 직선",
            "circle": "⭕ 원",
            "rect": "⬜ 사각형"
        }.get(x, x),
        horizontal=True,
        key="drawing_mode"
    )
    
    # 선 굵기
    stroke_width = st.slider("선 굵기", 1, 10, 3, key="stroke_width")
    
    # 캔버스 크기 (사이드바에 맞게 조정)
    canvas_size = 280
    
    # drawable canvas 생성
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # 채우기 색상
        stroke_width=stroke_width,
        stroke_color="#9B59B6",  # 보라색 선
        background_color="#FFFFFF",
        height=canvas_size,
        width=canvas_size,
        drawing_mode=drawing_mode,
        key="shape_canvas",
    )
    
    # 캔버스 데이터 처리
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data.get("objects", [])
        if objects:
            # 그려진 객체에서 좌표 추출
            all_points = _extract_points_from_canvas(objects, canvas_size)
            st.session_state.custom_points = all_points
            
            # 포인트 수 표시
            st.caption(f"✅ {len(all_points)}개의 점이 추출되었습니다")
        else:
            st.session_state.custom_points = []
    
    # 안내 메시지
    st.caption("💡 그린 모양이 러닝 코스의 형태가 됩니다")


def _extract_points_from_canvas(objects: list, canvas_size: int) -> list:
    """
    캔버스 객체에서 좌표점 추출
    
    Args:
        objects: 캔버스에서 그려진 객체 목록
        canvas_size: 캔버스 크기 (정규화용)
    
    Returns:
        정규화된 좌표점 목록 (0~1 범위)
    """
    all_points = []
    
    for obj in objects:
        obj_type = obj.get("type", "")
        
        if obj_type == "path":
            # 자유 그리기 또는 선의 경로 데이터
            path = obj.get("path", [])
            for cmd in path:
                if len(cmd) >= 3:
                    # path 명령어에서 좌표 추출 (M, L, Q 등)
                    x = cmd[1] if len(cmd) > 1 else 0
                    y = cmd[2] if len(cmd) > 2 else 0
                    all_points.append({
                        'x': x / canvas_size,
                        'y': y / canvas_size
                    })
        
        elif obj_type == "circle":
            # 원의 중심점과 둘레 점들
            left = obj.get("left", 0)
            top = obj.get("top", 0)
            radius = obj.get("radius", 0)
            
            # 원 둘레의 점들 생성 (16개 점)
            import math
            for i in range(16):
                angle = 2 * math.pi * i / 16
                x = left + radius + radius * math.cos(angle)
                y = top + radius + radius * math.sin(angle)
                all_points.append({
                    'x': x / canvas_size,
                    'y': y / canvas_size
                })
        
        elif obj_type == "rect":
            # 사각형의 꼭짓점
            left = obj.get("left", 0)
            top = obj.get("top", 0)
            width = obj.get("width", 0)
            height = obj.get("height", 0)
            
            # 사각형 꼭짓점 (시계 방향)
            corners = [
                (left, top),
                (left + width, top),
                (left + width, top + height),
                (left, top + height),
                (left, top),  # 시작점으로 돌아오기
            ]
            for x, y in corners:
                all_points.append({
                    'x': x / canvas_size,
                    'y': y / canvas_size
                })
        
        elif obj_type == "line":
            # 직선의 시작점과 끝점
            x1 = obj.get("x1", 0) + obj.get("left", 0)
            y1 = obj.get("y1", 0) + obj.get("top", 0)
            x2 = obj.get("x2", 0) + obj.get("left", 0)
            y2 = obj.get("y2", 0) + obj.get("top", 0)
            
            all_points.append({'x': x1 / canvas_size, 'y': y1 / canvas_size})
            all_points.append({'x': x2 / canvas_size, 'y': y2 / canvas_size})
    
    return all_points


def _render_constraints_section():
    """제약 조건 입력 섹션"""
    st.subheader("⚙️ 제약 조건")
    
    # 목표 거리
    target_distance = st.slider(
        "목표 거리 (km)",
        min_value=1.0,
        max_value=42.0,
        value=st.session_state.get('target_distance', 5.0),
        step=0.5,
        key="target_distance",
        help="원하는 러닝 거리를 설정하세요"
    )
    
    # 거리 표시
    st.caption(f"선택된 거리: {target_distance:.1f} km")
    
    # 허용 신호등 개수
    max_traffic_lights = st.slider(
        "최대 신호등 수",
        min_value=0,
        max_value=20,
        value=st.session_state.get('max_traffic_lights', 5),
        step=1,
        key="max_traffic_lights",
        help="경로에 포함될 수 있는 최대 신호등/횡단보도 수"
    )
    
    st.caption(f"허용 신호등: 최대 {max_traffic_lights}개")


def _render_search_button(on_search: Optional[Callable]):
    """검색 버튼"""
    st.subheader("🔍 경로 탐색")
    
    # 검색 조건 요약
    shape_type = st.session_state.get('shape_type', ShapeType.HEART.value)
    distance = st.session_state.get('target_distance', 5.0)
    lights = st.session_state.get('max_traffic_lights', 5)
    
    shape_names = {
        ShapeType.HEART.value: "하트",
        ShapeType.CIRCLE.value: "원",
        ShapeType.STAR.value: "별",
        ShapeType.DIGIT_0.value: "숫자 0",
        ShapeType.DIGIT_1.value: "숫자 1",
        ShapeType.DIGIT_2.value: "숫자 2",
        ShapeType.DIGIT_3.value: "숫자 3",
        ShapeType.DIGIT_4.value: "숫자 4",
        ShapeType.DIGIT_5.value: "숫자 5",
        ShapeType.DIGIT_6.value: "숫자 6",
        ShapeType.DIGIT_7.value: "숫자 7",
        ShapeType.DIGIT_8.value: "숫자 8",
        ShapeType.DIGIT_9.value: "숫자 9",
        ShapeType.CUSTOM.value: "사용자 정의",
    }
    
    st.caption(f"모양: {shape_names.get(shape_type, '미선택')}")
    st.caption(f"거리: {distance:.1f}km / 신호등: {lights}개 이하")
    
    # 검색 버튼
    search_disabled = st.session_state.get('bounding_box') is None
    
    if st.button(
        "🚀 경로 찾기",
        type="primary",
        use_container_width=True,
        disabled=search_disabled,
        help="지도에서 영역을 먼저 선택해주세요" if search_disabled else "클릭하여 경로 탐색 시작"
    ):
        if on_search:
            on_search()
        else:
            # Mock 검색 (Phase 1에서는 더미 데이터 사용)
            st.session_state.is_loading = True
            st.rerun()
    
    if search_disabled:
        st.warning("⚠️ 지도에서 영역을 선택해주세요")


def _render_selection_info():
    """선택된 영역 정보 표시"""
    bbox = st.session_state.get('bounding_box')
    
    if bbox:
        st.divider()
        st.subheader("📍 선택된 영역")
        
        with st.expander("좌표 정보", expanded=False):
            st.text(f"북: {bbox.get('north', 0):.6f}°")
            st.text(f"남: {bbox.get('south', 0):.6f}°")
            st.text(f"동: {bbox.get('east', 0):.6f}°")
            st.text(f"서: {bbox.get('west', 0):.6f}°")


def get_current_constraints() -> Constraints:
    """현재 설정된 제약 조건 반환"""
    return Constraints(
        target_distance_km=st.session_state.get('target_distance', 5.0),
        max_traffic_lights=st.session_state.get('max_traffic_lights', 5)
    )


def get_current_shape() -> Shape:
    """현재 선택된 모양 반환"""
    shape_type_str = st.session_state.get('shape_type', ShapeType.HEART.value)
    shape_type = ShapeType(shape_type_str)
    
    points = []
    if shape_type == ShapeType.CUSTOM:
        custom_points = st.session_state.get('custom_points', [])
        # 정규화된 좌표 (x, y: 0~1 범위)를 Coordinate로 변환
        # 실제 위경도 변환은 Phase 3에서 bounding box 기준으로 수행
        points = [Coordinate(p.get('y', 0), p.get('x', 0)) if isinstance(p, dict) 
                  else p for p in custom_points]
    
    return Shape(shape_type=shape_type, points=points)
