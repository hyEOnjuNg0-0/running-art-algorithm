## 디렉토리 구조

```
RAcourse-Algorithm/
├── app.py                              # Streamlit 메인 애플리케이션
├── requirements.txt                    # 의존성 패키지 목록
│
├── docs/
│   ├── 00_PLAN.md                      # 프로젝트 계획 및 진행 상태
│   ├── 01_PHASE1_UI.md                 # Phase 1: UI 프로토타입 명세
│   ├── 02_PHASE2_DATA.md               # Phase 2: 데이터 레이어 명세
│   ├── 03_PHASE3_SHAPE.md              # Phase 3: 도형 처리 명세
│   ├── 04_PHASE4_COST_FUNCTION.md      # Phase 4: 비용 함수 명세
│   ├── 05_PHASE5_ALGO.md               # Phase 5: 알고리즘 명세
│   ├── 06_PHASE6_INTEGRRATION.md       # Phase 6: 통합 명세
│   ├── OUTLINE.md                      # 프로젝트 전체 개요
│   ├── STRUCTURE.md                    # 디렉토리 구조 (현재 파일)
│   └── TECHSPEC.md                     # 사용 기술 스택
│
├── src/
│   ├── __init__.py
│   │
│   ├── data/                           # 데이터 레이어 (OSM 데이터 처리)
│   │   ├── __init__.py                 # 모듈 초기화 및 공개 API
│   │   ├── entities.py                 # 데이터 엔티티 정의
│   │   │                               # - Node: 교차로/노드 (id, 위도, 경도, 신호등)
│   │   │                               # - Edge: 도로/엣지 (시작/끝 노드, 길이, 타입)
│   │   │                               # - RoadGraph: 도로 네트워크 그래프
│   │   │                               # - RoadType: 도로 타입 열거형
│   │   ├── repository.py               # Repository 인터페이스 정의
│   │   │                               # - GraphRepository: 그래프 조회 추상 인터페이스
│   │   │                               # - GraphFetchError: 조회 실패 예외
│   │   ├── osm_repository.py           # OSM Repository 구현
│   │   │                               # - OSMGraphRepository: osmnx 활용 구현체
│   │   │                               # - bbox/point 기반 그래프 조회
│   │   └── cache_service.py            # 그래프 캐싱 서비스
│   │                                   # - 파일 기반 캐싱 (pickle)
│   │                                   # - JSON 직렬화/역직렬화
│   │
│   ├── shape/                          # 도형 처리 레이어
│   │   ├── __init__.py                 # 모듈 초기화 및 공개 API
│   │   ├── templates.py                # 도형 템플릿 정의
│   │   │                               # - ShapeTemplate: 정규화 좌표 기반 템플릿
│   │   │                               # - ShapeTemplateRegistry: 템플릿 레지스트리
│   │   │                               # - 기본 도형: 원, 사각형, 삼각형, 하트, 별
│   │   ├── transformer.py              # 도형 변환기
│   │   │                               # - 정규화 좌표 ↔ 지리 좌표 변환
│   │   │                               # - 회전, 스케일링, 이동 변환
│   │   │                               # - 6방향 회전 생성
│   │   └── processor.py                # 도형 처리기
│   │                                   # - 템플릿 → 지리 좌표 변환
│   │                                   # - 사용자 입력 처리 (단순화, 스무딩)
│   │                                   # - 도형 길이 계산, 재샘플링
│   │
│   ├── domain/                         # 도메인 레이어 (핵심 비즈니스 로직)
│   │   ├── __init__.py
│   │   └── entities.py                 # 도메인 엔티티 정의
│   │                                   # - Coordinate: 위도/경도 좌표
│   │                                   # - BoundingBox: 지도 범위
│   │                                   # - Shape: 모양 정보
│   │                                   # - Constraints: 제약 조건
│   │                                   # - RouteInfo: 경로 정보
│   │                                   # - SearchResult: 검색 결과
│   │
│   └── presentation/                   # 프레젠테이션 레이어 (UI)
│       ├── __init__.py
│       ├── state.py                    # UI 상태 관리 (session_state)
│       ├── mock_data.py                # Mock 데이터 (Phase 1 테스트용)
│       │
│       └── components/                 # UI 컴포넌트
│           ├── __init__.py
│           ├── sidebar.py              # 사이드바 (입력 컨트롤)
│           │                           # - 모양 선택 (템플릿/직접 그리기)
│           │                           # - 제약 조건 (거리, 신호등)
│           │                           # - 검색 버튼
│           ├── map_view.py             # 지도 뷰 (Folium)
│           │                           # - 영역 선택 도구
│           │                           # - 경로 시각화
│           │                           # - 직접 그리기 기능
│           └── route_cards.py          # 경로 정보 카드
│                                       # - 경로별 상세 정보
│                                       # - 정렬 및 선택 기능
│
└── tests/
    ├── __init__.py
    ├── test_entities.py                # 도메인 엔티티 테스트
    ├── test_data_entities.py           # 데이터 레이어 엔티티 테스트
    ├── test_cache_service.py           # 캐싱 서비스 테스트
    └── test_shape.py                   # 도형 처리 테스트

