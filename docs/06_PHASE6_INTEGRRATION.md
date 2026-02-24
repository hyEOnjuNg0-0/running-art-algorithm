## Phase 6: 통합 및 최적화

### 6.1 파이프라인 통합
- [x] **UI → 데이터 → 알고리즘 → 결과 파이프라인 연결**
  - 구현: `src/service/route_search_service.py`
    - `SearchRequest`: 탐색 요청 데이터 클래스
    - `SearchResponse`: 탐색 응답 데이터 클래스
    - `SearchStatus`: 탐색 상태 열거형
    - `RouteSearchService`: 통합 파이프라인 서비스
    - `create_search_request()`: UI 입력 → 요청 변환

- [x] **비동기 처리 (긴 연산 시 UI 블로킹 방지)**
  - `search_async()`: ThreadPoolExecutor 기반 비동기 탐색
  - 진행 상황 콜백 지원 (`progress_callback`)
  - UI에서 실시간 진행률 표시

### 6.2 성능 최적화
- [x] **그래프 캐싱**
  - `GraphCacheService`를 통한 파일 기반 캐싱
  - 동일 영역 재탐색 시 OSM 요청 생략

- [x] **병렬 탐색**
  - `RouteFinder`에서 ThreadPoolExecutor 활용
  - 가중치/회전 조합별 병렬 A* 탐색

- [x] **불필요한 재계산 방지**
  - 캐시 키 기반 중복 그래프 로딩 방지
  - 방문 노드 기록으로 중복 탐색 방지

### 6.3 테스트
- [x] **단위 테스트 작성**
  - 비용 함수 테스트: `test_cost_function.py`
  - 알고리즘 테스트: `test_algorithm.py`

- [x] **통합 테스트**
  - 구현: `tests/test_integration.py`
    - `TestSearchRequest`: 요청 생성 테스트
    - `TestRouteSearchService`: 서비스 테스트
    - `TestShapeProcessorIntegration`: 도형 처리 통합
    - `TestRouteFinderIntegration`: 경로 탐색 통합
    - `TestEndToEndPipeline`: E2E 파이프라인

- [x] **엣지 케이스 처리**
  - 빈 그래프 처리
  - 잘못된 입력 검증 (0 거리, 음수 신호등)
  - 매우 작은 바운딩 박스 처리

### 6.4 UI 통합
- [x] **app.py 업데이트**
  - 실제 검색 서비스 연동 (`use_real_search` 플래그)
  - 진행 상황 실시간 표시
  - 에러 처리 및 사용자 피드백