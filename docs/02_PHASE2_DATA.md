## Phase 2: 데이터 레이어

### 2.1 OSM 데이터 처리
- [x] **OSM 데이터 다운로드/파싱**
  - osmnx 라이브러리 활용
  - bounding box 기반 필터링
  - point 중심 반경 기반 필터링

- [x] **그래프 구조 생성**
  - Node (교차로) 데이터 모델
    - id, 위도, 경도, 신호등 여부
  - Edge (도로) 데이터 모델
    - id, 시작 노드, 끝 노드
    - 길이, 도로 타입, 도로명, 일방통행 여부
  - RoadGraph: 노드/엣지 관리 및 인접 리스트

### 2.2 데이터 캐싱
- [x] 자주 사용되는 영역 데이터 캐싱 (pickle 기반)
- [x] 그래프 직렬화/역직렬화 (JSON 지원)

### 2.3 구현된 컴포넌트

| 파일 | 설명 |
|------|------|
| `src/data/entities.py` | Node, Edge, RoadGraph, RoadType 엔티티 |
| `src/data/repository.py` | GraphRepository 인터페이스 |
| `src/data/osm_repository.py` | OSMGraphRepository 구현체 |
| `src/data/cache_service.py` | GraphCacheService 캐싱 서비스 |

### 2.4 테스트
- `tests/test_data_entities.py`: 25개 테스트
- `tests/test_cache_service.py`: 11개 테스트