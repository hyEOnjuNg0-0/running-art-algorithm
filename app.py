"""
RAcourse-Algorithm 메인 애플리케이션
러닝 코스 추천 시스템 - Streamlit UI
"""
import streamlit as st
import time
import logging

# 페이지 설정 (가장 먼저 호출되어야 함)
st.set_page_config(
    page_title="러닝 코스 추천",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.presentation.state import init_session_state, set_loading, set_error, clear_error
from src.presentation.components.sidebar import render_sidebar
from src.presentation.components.map_view import render_map, render_map_instructions
from src.presentation.components.route_cards import render_route_cards, render_route_summary
from src.presentation.mock_data import generate_mock_routes
from src.service.route_search_service import (
    RouteSearchService, SearchStatus, create_search_request
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """메인 애플리케이션 진입점"""
    # 세션 상태 초기화
    init_session_state()
    
    # 헤더
    st.title("🏃 러닝 코스 추천 시스템")
    st.caption("원하는 모양의 러닝 코스를 찾아보세요!")
    
    # 에러 메시지 표시
    _render_error_message()
    
    # 사이드바 렌더링
    render_sidebar(on_search=_handle_search)
    
    # 메인 콘텐츠 영역
    _render_main_content()


def _render_error_message():
    """에러 메시지 표시"""
    error_msg = st.session_state.get('error_message')
    if error_msg:
        st.error(f"⚠️ {error_msg}")
        if st.button("닫기", key="close_error"):
            clear_error()
            st.rerun()


def _render_main_content():
    """메인 콘텐츠 영역 렌더링"""
    # 로딩 상태 처리
    if st.session_state.get('is_loading'):
        _render_loading_state()
        return
    
    # 2열 레이아웃: 지도 | 경로 카드
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 지도 사용 안내
        render_map_instructions()
        
        # 지도 렌더링
        routes = st.session_state.get('routes', [])
        selected_route_id = st.session_state.get('selected_route_id')
        
        render_map(
            routes=routes,
            selected_route_id=selected_route_id,
            show_drawing_tools=True,
        )
    
    with col2:
        # 경로 카드 렌더링
        routes = st.session_state.get('routes', [])
        selected_route_id = st.session_state.get('selected_route_id')
        
        render_route_cards(
            routes=routes,
            selected_route_id=selected_route_id,
            on_select=_handle_route_select,
        )
        
        # 경로 요약
        if routes:
            render_route_summary(routes)


def _render_loading_state():
    """로딩 상태 표시"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        
        # 실제 검색 수행 여부 확인
        use_real_search = st.session_state.get('use_real_search', False)
        
        if use_real_search:
            _perform_real_search()
        else:
            _perform_mock_search()


def _perform_real_search():
    """실제 경로 탐색 수행"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    info_text = st.empty()
    
    status_messages = {
        SearchStatus.LOADING_DATA: "🗺️ 지도 데이터 로딩 중...",
        SearchStatus.PROCESSING_SHAPE: "📐 도형 분석 중...",
        SearchStatus.SEARCHING_ROUTES: "🔍 경로 탐색 중...",
        SearchStatus.FILTERING_RESULTS: "⚡ 결과 최적화 중...",
        SearchStatus.COMPLETED: "✅ 완료!",
        SearchStatus.ERROR: "❌ 오류 발생",
    }
    
    status_info = {
        SearchStatus.LOADING_DATA: "💡 첫 로딩 시 OpenStreetMap에서 데이터를 가져옵니다 (오래 걸릴 수 있습니다)",
        SearchStatus.PROCESSING_SHAPE: "",
        SearchStatus.SEARCHING_ROUTES: "💡 최적의 경로를 탐색하고 있습니다...",
        SearchStatus.FILTERING_RESULTS: "",
    }
    
    def update_progress(status: SearchStatus, progress: float):
        status_text.text(status_messages.get(status, "처리 중..."))
        progress_bar.progress(min(progress, 1.0))
        info = status_info.get(status, "")
        if info:
            info_text.caption(info)
        else:
            info_text.empty()
    
    try:
        # 검색 요청 생성
        bbox = st.session_state.get('bounding_box')
        shape_type = st.session_state.get('shape_type', 'heart')
        custom_points = st.session_state.get('custom_points', [])
        target_distance = st.session_state.get('target_distance', 5.0)
        max_traffic_lights = st.session_state.get('max_traffic_lights', 5)
        
        request = create_search_request(
            bbox_dict=bbox,
            shape_type=shape_type,
            custom_points=custom_points,
            target_distance=target_distance,
            max_traffic_lights=max_traffic_lights
        )
        
        # 서비스 호출
        service = RouteSearchService(use_cache=True)
        response = service.search(request, progress_callback=update_progress)
        
        if response.status == SearchStatus.COMPLETED:
            st.session_state.routes = response.routes
            if not response.routes:
                set_error("조건에 맞는 경로를 찾지 못했습니다. 영역을 넓히거나 조건을 완화해보세요.")
        else:
            set_error(response.error_message or "경로 탐색에 실패했습니다")
        
    except Exception as e:
        logger.error(f"검색 실패: {e}")
        set_error(f"경로 탐색 중 오류가 발생했습니다: {str(e)}")
    
    finally:
        st.session_state.is_loading = False
        st.session_state.use_real_search = False
        st.rerun()


def _perform_mock_search():
    """Mock 검색 수행 (테스트용)"""
    with st.spinner("🔍 최적의 경로를 찾고 있습니다..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        steps = [
            "지도 데이터 로딩 중...",
            "도형 분석 중...",
            "경로 탐색 중...",
            "최적화 중...",
            "결과 정리 중...",
        ]
        
        for i, step in enumerate(steps):
            status_text.text(step)
            progress_bar.progress((i + 1) * 20)
            time.sleep(0.3)
        
        status_text.text("완료!")
        time.sleep(0.2)
    
    # Mock 데이터로 결과 설정
    center = st.session_state.get('map_center', [37.5665, 126.9780])
    mock_routes = generate_mock_routes(center[0], center[1])
    st.session_state.routes = mock_routes
    st.session_state.is_loading = False
    st.rerun()


def _handle_search():
    """검색 버튼 클릭 핸들러"""
    # 입력 검증
    bbox = st.session_state.get('bounding_box')
    
    if not bbox:
        set_error("지도에서 영역을 먼저 선택해주세요")
        return
    
    # 실제 검색 사용 여부 설정
    st.session_state.use_real_search = True
    
    # 검색 시작
    clear_error()
    set_loading(True)
    st.rerun()


def _handle_route_select(route_id: int):
    """경로 선택 핸들러"""
    st.session_state.selected_route_id = route_id
    st.rerun()


# 커스텀 CSS
def _apply_custom_styles():
    """커스텀 스타일 적용"""
    st.markdown("""
    <style>
    /* 메인 컨테이너 패딩 조정 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 사이드바 스타일 */
    .css-1d391kg {
        padding-top: 1rem;
    }
    
    /* 카드 스타일 */
    .stMetric {
        background-color: rgba(0, 0, 0, 0.02);
        padding: 10px;
        border-radius: 8px;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        border-radius: 8px;
    }
    
    /* 지도 컨테이너 */
    iframe {
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    _apply_custom_styles()
    main()
