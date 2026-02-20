## Phase 3: 도형 처리

### 3.1 템플릿 관리
- [x] **Polyline 템플릿 정의**
  - 기본 도형 템플릿: 원, 하트, 별
  - 숫자 템플릿: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
  - 정규화 좌표 (-1 ~ 1 범위) 기반
  - ShapeTemplateRegistry로 관리

### 3.2 사용자 입력 도형 처리
- [x] **좌표점 → Polyline 변환**
  - 중복 점 제거
  - Douglas-Peucker 알고리즘으로 점 단순화
  - 이동 평균 기반 스무딩 (선택적)
  - 균등 간격 재샘플링

### 3.3 도형 변환
- [x] **스케일링**
  - 사용자 지정 bounding box에 맞게 크기 조정
  - 템플릿: 정규화 좌표 → 지리 좌표
  - fit_to_bbox로 종횡비 유지 스케일링
  
- [x] **회전**
  - 6방향 (60° 간격) 회전 변환
  - θ ∈ {0°, 60°, 120°, 180°, 240°, 300°}
  - generate_rotations로 모든 변형 생성

- [x] **좌표 변환**
  - 템플릿 좌표 → 지리 좌표 변환 (normalize_to_geo)
  - 지리 좌표 → 정규화 좌표 변환 (geo_to_normalized)
  - 복합 변환 지원 (apply_transform)

### 3.4 구현된 컴포넌트

| 파일 | 설명 |
|------|------|
| `src/shape/templates.py` | ShapeTemplate, ShapeTemplateRegistry |
| `src/shape/transformer.py` | ShapeTransformer, TransformParams |
| `src/shape/processor.py` | ShapeProcessor |

### 3.5 테스트
- `tests/test_shape.py`: 29개 테스트