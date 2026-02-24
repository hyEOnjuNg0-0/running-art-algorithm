"""
지도 뷰 컴포넌트
Folium을 사용한 지도 시각화 및 상호작용
"""
import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from typing import List, Optional, Dict, Any

from src.domain.entities import RouteInfo, Coordinate, BoundingBox


# 경로별 색상 팔레트
ROUTE_COLORS = [
    '#FF6B6B',  # 빨강
    '#4ECDC4',  # 청록
    '#45B7D1',  # 하늘
    '#96CEB4',  # 민트
    '#FFEAA7',  # 노랑
]


def render_map(
    routes: Optional[List[RouteInfo]] = None,
    selected_route_id: Optional[int] = None,
    show_drawing_tools: bool = True,
) -> Dict[str, Any]:
    """
    메인 지도 렌더링
    
    Args:
        routes: 표시할 경로 목록
        selected_route_id: 강조할 경로 ID
        show_drawing_tools: 그리기 도구 표시 여부
    
    Returns:
        지도 상호작용 결과 (선택된 영역 등)
    """
    st.subheader("🗺️ 지도")
    
    # 지도 중심 및 줌 레벨
    center = st.session_state.get('map_center', [37.5665, 126.9780])
    zoom = st.session_state.get('map_zoom', 14)
    
    # Folium 지도 생성
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles='OpenStreetMap',
    )
    
    # 그리기 도구 추가 (사각형 범위 선택만 가능)
    if show_drawing_tools:
        draw = Draw(
            draw_options={
                'polyline': False,
                'polygon': False,
                'rectangle': True,  # 사각형 영역 선택만 허용
                'circle': False,
                'marker': False,
                'circlemarker': False,
            },
            edit_options={
                'edit': True,
                'remove': True,
            }
        )
        draw.add_to(m)
    
    # 경로 표시
    if routes:
        _add_routes_to_map(m, routes, selected_route_id)
    
    # 선택된 바운딩 박스 표시
    bbox = st.session_state.get('bounding_box')
    if bbox:
        _add_bounding_box_to_map(m, bbox)
    
    # 지도 렌더링
    map_data = st_folium(
        m,
        width=None,  # 컨테이너 너비에 맞춤
        height=500,
        returned_objects=["all_drawings", "last_active_drawing"],
        key="main_map",
    )
    
    # 지도 상호작용 결과 처리
    _process_map_interaction(map_data)
    
    return map_data


def _add_routes_to_map(
    m: folium.Map,
    routes: List[RouteInfo],
    selected_route_id: Optional[int]
):
    """경로들을 지도에 추가"""
    for i, route in enumerate(routes):
        color = ROUTE_COLORS[i % len(ROUTE_COLORS)]
        is_selected = route.route_id == selected_route_id
        
        # 경로 좌표 변환
        coords = [(c.lat, c.lng) for c in route.coordinates]
        
        # 선택된 경로는 더 두껍게 표시
        weight = 6 if is_selected else 3
        opacity = 1.0 if is_selected else 0.7
        
        # 경로 라인 추가
        folium.PolyLine(
            coords,
            color=color,
            weight=weight,
            opacity=opacity,
            popup=f"""
                <b>{route.display_name}</b><br>
                거리: {route.total_distance_km:.2f} km<br>
                신호등: {route.traffic_light_count}개<br>
                유사도: {route.shape_similarity:.1%}
            """,
            tooltip=route.display_name,
        ).add_to(m)
        
        # 시작점 마커
        if coords:
            folium.Marker(
                coords[0],
                popup=f"{route.display_name} 시작점",
                icon=folium.Icon(color='green', icon='play'),
            ).add_to(m)


def _add_bounding_box_to_map(m: folium.Map, bbox: Dict):
    """선택된 바운딩 박스 표시"""
    bounds = [
        [bbox['south'], bbox['west']],
        [bbox['north'], bbox['east']]
    ]
    
    folium.Rectangle(
        bounds=bounds,
        color='#3498DB',
        weight=2,
        fill=True,
        fill_opacity=0.1,
        popup="선택된 영역",
    ).add_to(m)


def _process_map_interaction(map_data: Dict[str, Any]):
    """지도 상호작용 결과 처리"""
    if not map_data:
        return
    
    # 그리기 결과 처리 (사각형 범위 선택만)
    last_drawing = map_data.get('last_active_drawing')
    if last_drawing:
        geometry = last_drawing.get('geometry', {})
        geo_type = geometry.get('type', '')
        
        # 사각형 영역 선택 처리
        if geo_type == 'Polygon':
            coords = geometry.get('coordinates', [[]])[0]
            if len(coords) >= 4:
                lats = [c[1] for c in coords]
                lngs = [c[0] for c in coords]
                
                st.session_state.bounding_box = {
                    'north': max(lats),
                    'south': min(lats),
                    'east': max(lngs),
                    'west': min(lngs),
                }


def render_map_instructions():
    """지도 사용 안내"""
    with st.expander("📖 지도 사용 방법", expanded=False):
        st.markdown("""
        **영역 선택하기**
        1. 지도 왼쪽의 사각형 도구(⬜)를 클릭
        2. 지도에서 드래그하여 원하는 영역 선택
        3. 선택된 영역 내에서 경로를 탐색합니다
        
        **경로 확인하기**
        - 경로 위에 마우스를 올리면 정보 표시
        - 경로를 클릭하면 상세 정보 팝업
        """)
