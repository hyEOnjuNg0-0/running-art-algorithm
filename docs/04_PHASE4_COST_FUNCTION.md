## Phase 4: 비용 함수 구현

### 4.1 ShapeDistance 계산
- [x] **Edge-Curve 거리 계산**
  - Edge를 최소 3구간으로 샘플링
  - 각 샘플 포인트와 목표 곡선 C 사이 최소 거리 계산
  - 거리 합산

- [x] **정규화**
  - L_target(목표 거리)으로 나누어 정규화

### 4.2 LengthPenalty 계산
- [x] **경로 길이 계산**
  - 경로 내 모든 edge 길이 합산
  
- [x] **페널티 계산**
  - |실제 길이 - 목표 길이|
  - L_target으로 나누어 정규화

### 4.3 CrossingPenalty 계산
- [x] **횡단보도 카운트**
  - 경로 내 신호등/횡단보도 수 집계
  
- [x] **페널티 계산**
  - C_max = 입력 받은 허용 횡단보도 개수
  - max(0, 횡단보도 수 - C_max)
  - (C_max + 1)로 나누어 정규화

---

### 구현 완료

**구현 파일:**
- `src/cost/__init__.py` - 모듈 초기화
- `src/cost/cost_function.py` - 비용 함수 구현

**테스트 파일:**
- `tests/test_cost_function.py` - 26개 테스트 케이스

**주요 클래스:**
- `ShapeDistanceCalculator`: Edge-Curve 거리 계산
- `LengthPenaltyCalculator`: 경로 길이 페널티
- `CrossingPenaltyCalculator`: 횡단보도 페널티
- `CostCalculator`: 통합 비용 계산기
- `CostResult`: 비용 계산 결과 데이터 클래스