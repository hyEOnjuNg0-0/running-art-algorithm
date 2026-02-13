## Phase 1: UI 프로토타입 (Streamlit)

**상태**: ✅ 완료

### 1.1 기본 레이아웃 구성
- [x] Streamlit 프로젝트 초기 설정
- [x] 메인 페이지 레이아웃 설계
  - 사이드바: 입력 컨트롤
  - 메인 영역: 지도 시각화

### 1.2 입력 UI 구현
- [x] **지도 범위 선택**
  - Folium 또는 streamlit-folium을 사용한 지도 표시
  - 사각형 영역 선택 기능 (bounding box)
  - 선택된 좌표 표시 (위도/경도)

- [x] **모양 입력**
  - 템플릿 선택 방식 (미리 정의된 도형)
    - 템플릿 목록: 하트, 원, 사각형, 삼각형, 별
  - 사용자 지정 입력 방식 (직접 그리기)
    - streamlit-drawable-canvas를 사용한 그림판 스타일 캔버스
    - 그리기 도구: 자유 그리기, 직선, 원, 사각형
    - 선 굵기 조절 가능
    - 그린 도형에서 자동으로 좌표점 추출

- [x] **제약 조건 입력**
  - 목표 거리 (km) - 슬라이더 (1~42km)
  - 허용 신호등 개수 - 슬라이더 (0~20개)

### 1.3 출력 UI 구현
- [x] **결과 지도 시각화**
  - 최대 5개 경로를 지도 위에 표시
  - 각 경로별 색상 구분
  - 경로 선택 시 해당 경로 강조

- [x] **경로 정보 카드**
  - 각 경로별 정보 표시
    - 총 거리 (km)
    - 횡단보도/신호등 수
    - Shape 유사도 점수
  - 경로 선택 버튼
  - 정렬 기능 (유사도/거리/신호등)

### 1.4 UI 상태 관리
- [x] Session state를 활용한 상태 관리
- [x] 로딩 상태 표시 (스피너 + 프로그레스 바)
- [x] 에러 메시지 표시

---

## 구현 상세

### 파일 구조
```
src/presentation/
├── state.py              # 상태 관리
├── mock_data.py          # Mock 데이터 생성
└── components/
    ├── sidebar.py        # 사이드바 컴포넌트
    ├── map_view.py       # 지도 뷰 컴포넌트
    └── route_cards.py    # 경로 카드 컴포넌트
```

### 주요 컴포넌트

#### sidebar.py
- `render_sidebar()`: 전체 사이드바 렌더링
- `_render_shape_section()`: 모양 선택 UI
- `_render_constraints_section()`: 제약 조건 UI
- `_render_search_button()`: 검색 버튼

#### map_view.py
- `render_map()`: Folium 지도 렌더링
- Draw 플러그인으로 사각형 영역 선택만 지원
- 경로 시각화 (색상 구분, 팝업 정보)

#### route_cards.py
- `render_route_cards()`: 경로 카드 목록
- 정렬 기능 (유사도/거리/신호등)
- 선택 상태 시각적 표시

### Mock 데이터
Phase 1에서는 실제 알고리즘 대신 Mock 데이터를 사용:
- `generate_mock_routes()`: 하트/원 모양의 테스트 경로 생성
- 5개의 다양한 경로 (거리, 신호등, 유사도 다양)
