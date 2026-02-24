"""
경로 정보 카드 컴포넌트
검색된 경로들의 정보를 카드 형태로 표시
"""
import streamlit as st
from typing import List, Optional, Callable

from src.domain.entities import RouteInfo


# 경로별 색상 (map_view와 동일)
ROUTE_COLORS = [
    '#FF6B6B',  # 빨강
    '#4ECDC4',  # 청록
    '#45B7D1',  # 하늘
    '#96CEB4',  # 민트
    '#FFEAA7',  # 노랑
]


def render_route_cards(
    routes: List[RouteInfo],
    selected_route_id: Optional[int] = None,
    on_select: Optional[Callable[[int], None]] = None,
):
    """
    경로 정보 카드 목록 렌더링
    
    Args:
        routes: 표시할 경로 목록
        selected_route_id: 현재 선택된 경로 ID
        on_select: 경로 선택 시 호출될 콜백
    """
    if not routes:
        _render_empty_state()
        return
    
    st.subheader(f"🏃 추천 경로 ({len(routes)}개)")
    
    # 정렬 옵션
    sort_option = st.selectbox(
        "정렬 기준",
        options=["유사도 높은 순", "거리 짧은 순", "신호등 적은 순"],
        key="route_sort",
    )
    
    # 정렬 적용
    sorted_routes = _sort_routes(routes, sort_option)
    
    # 각 경로 카드 렌더링
    for i, route in enumerate(sorted_routes):
        _render_route_card(
            route=route,
            index=i,
            is_selected=(route.route_id == selected_route_id),
            on_select=on_select,
        )


def _render_empty_state():
    """경로가 없을 때 표시"""
    st.info(
        """
        🔍 **경로를 찾으려면:**
        1. 지도에서 원하는 영역을 선택하세요
        2. 사이드바에서 모양과 조건을 설정하세요
        3. '경로 찾기' 버튼을 클릭하세요
        """
    )


def _sort_routes(routes: List[RouteInfo], sort_option: str) -> List[RouteInfo]:
    """경로 정렬"""
    if sort_option == "유사도 높은 순":
        return sorted(routes, key=lambda r: r.shape_similarity, reverse=True)
    elif sort_option == "거리 짧은 순":
        return sorted(routes, key=lambda r: r.total_distance_km)
    elif sort_option == "신호등 적은 순":
        return sorted(routes, key=lambda r: r.traffic_light_count)
    return routes


def _render_route_card(
    route: RouteInfo,
    index: int,
    is_selected: bool,
    on_select: Optional[Callable[[int], None]],
):
    """개별 경로 카드 렌더링"""
    color = ROUTE_COLORS[index % len(ROUTE_COLORS)]
    
    # 카드 컨테이너
    with st.container():
        # 선택 상태에 따른 스타일링
        if is_selected:
            st.markdown(
                f"""
                <div style="
                    border-left: 4px solid {color};
                    padding-left: 12px;
                    background-color: rgba(0,0,0,0.05);
                    border-radius: 4px;
                    margin-bottom: 8px;
                ">
                """,
                unsafe_allow_html=True
            )
        
        # 경로 헤더
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(
                f"""
                <span style="
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    background-color: {color};
                    border-radius: 50%;
                    margin-right: 8px;
                "></span>
                <strong>{route.display_name}</strong>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            # 유사도 배지
            similarity_pct = route.shape_similarity * 100
            badge_color = _get_similarity_color(route.shape_similarity)
            st.markdown(
                f"""
                <span style="
                    background-color: {badge_color};
                    color: white;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 0.8em;
                ">{similarity_pct:.0f}%</span>
                """,
                unsafe_allow_html=True
            )
        
        # 경로 상세 정보
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="거리",
                value=f"{route.total_distance_km:.2f} km",
            )
        
        with col2:
            st.metric(
                label="신호등",
                value=f"{route.traffic_light_count}개",
            )
        
        with col3:
            st.metric(
                label="유사도",
                value=f"{similarity_pct:.1f}%",
            )
        
        # 선택 버튼
        button_label = "✓ 선택됨" if is_selected else "선택하기"
        button_type = "primary" if is_selected else "secondary"
        
        if st.button(
            button_label,
            key=f"select_route_{route.route_id}",
            type=button_type,
            use_container_width=True,
        ):
            if on_select:
                on_select(route.route_id)
            else:
                st.session_state.selected_route_id = route.route_id
        
        if is_selected:
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.divider()


def _get_similarity_color(similarity: float) -> str:
    """유사도에 따른 색상 반환"""
    if similarity >= 0.8:
        return '#27AE60'  # 녹색 (높음)
    elif similarity >= 0.6:
        return '#F39C12'  # 주황 (중간)
    else:
        return '#E74C3C'  # 빨강 (낮음)


def render_route_summary(routes: List[RouteInfo]):
    """경로 요약 정보"""
    if not routes:
        return
    
    st.markdown("---")
    st.subheader("📊 경로 요약")
    
    # 통계 계산
    avg_distance = sum(r.total_distance_km for r in routes) / len(routes)
    avg_lights = sum(r.traffic_light_count for r in routes) / len(routes)
    avg_similarity = sum(r.shape_similarity for r in routes) / len(routes)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("평균 거리", f"{avg_distance:.2f} km")
    
    with col2:
        st.metric("평균 신호등", f"{avg_lights:.1f}개")
    
    with col3:
        st.metric("평균 유사도", f"{avg_similarity:.1%}")
