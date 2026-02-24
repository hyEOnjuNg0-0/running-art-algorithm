## Phase 5: 경로 탐색 알고리즘

### 5.1 가중치 샘플링
- [x] **Dirichlet 분포 샘플링**
  - Dir(1, 1, 1)에서 20개 가중치 조합 생성
  - (α, β, γ) where α + β + γ = 1
  - 구현: `src/algorithm/weight_sampler.py`
    - `WeightVector`: 가중치 벡터 데이터 클래스
    - `WeightSampler`: Dirichlet 분포 기반 샘플러
    - 편향 샘플링 및 코너 가중치 지원

### 5.2 A* 알고리즘 구현
- [x] **휴리스틱 함수 설계**
  - 목표 곡선까지의 추정 거리
  - 남은 거리와 목표점까지 거리 기반 휴리스틱
  
- [x] **비용 함수 통합**
  - F(P) = α·f̃₁ + β·f̃₂ + γ·f̃₃
  - CostCalculator와 연동
  
- [x] **경로 탐색**
  - 각 (가중치, θ) 조합에 대해 최적 경로 탐색
  - 총 120개 후보 생성 (20 가중치 × 6 회전)
  - 구현: `src/algorithm/astar.py`
    - `PathCandidate`: 경로 후보 데이터 클래스
    - `AStarPathFinder`: A* 기반 경로 탐색기
    - 순환 경로 탐색 (`find_path`)
    - 목표점 경로 탐색 (`find_path_to_goal`)

### 5.3 Pareto Set 생성
- [x] **Pareto Dominance 판정**
  - 두 경로 간 지배 관계 판정 함수
  - 구현: `src/algorithm/pareto.py`
    - `dominates()`: 지배 관계 판정
  
- [x] **Non-dominated 경로 필터링**
  - 지배되지 않는 경로만 남김
  - `filter_non_dominated()`: Non-dominated 필터링
  
- [x] **상위 5개 선택**
  - Pareto set에서 최대 5개 경로 선택
  - 혼잡 거리(Crowding Distance) 기반 다양성 선택
  - `select_top_k()`: 상위 k개 선택

### 5.4 통합 경로 탐색기
- [x] **RouteFinder 구현**
  - 구현: `src/algorithm/route_finder.py`
    - `RouteSearchConfig`: 탐색 설정
    - `RouteFinder`: 통합 경로 탐색기
    - 가중치 샘플링 + A* 탐색 + Pareto 필터링
    - 병렬/순차 탐색 지원
    - RouteInfo 변환 기능