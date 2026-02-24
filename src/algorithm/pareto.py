"""
Pareto 최적화
다목적 최적화를 위한 Pareto dominance 및 필터링
"""
from dataclasses import dataclass
from typing import List, Tuple, Optional

from src.algorithm.astar import PathCandidate


@dataclass
class ParetoCandidate:
    """
    Pareto 후보 경로
    
    Attributes:
        path_candidate: 원본 경로 후보
        objectives: 목적 함수 값 튜플 (shape_distance, length_penalty, crossing_penalty)
        rank: Pareto 순위 (0이 최상위)
        crowding_distance: 혼잡 거리 (다양성 측정)
    """
    path_candidate: PathCandidate
    objectives: Tuple[float, float, float]
    rank: int = 0
    crowding_distance: float = 0.0
    
    @classmethod
    def from_path_candidate(cls, candidate: PathCandidate) -> 'ParetoCandidate':
        """PathCandidate에서 ParetoCandidate 생성"""
        return cls(
            path_candidate=candidate,
            objectives=(
                candidate.shape_distance,
                candidate.length_penalty,
                candidate.crossing_penalty
            )
        )


class ParetoFilter:
    """
    Pareto 필터
    
    다목적 최적화에서 non-dominated 솔루션을 필터링
    """
    
    def dominates(
        self,
        obj1: Tuple[float, ...],
        obj2: Tuple[float, ...]
    ) -> bool:
        """
        obj1이 obj2를 지배하는지 판정
        
        지배 조건:
        - 모든 목적 함수에서 obj1 <= obj2
        - 적어도 하나의 목적 함수에서 obj1 < obj2
        
        Args:
            obj1: 첫 번째 목적 함수 값
            obj2: 두 번째 목적 함수 값
            
        Returns:
            obj1이 obj2를 지배하면 True
        """
        if len(obj1) != len(obj2):
            raise ValueError("목적 함수 차원이 일치해야 합니다")
        
        all_leq = True  # 모든 값이 작거나 같은지
        any_lt = False  # 적어도 하나가 작은지
        
        for v1, v2 in zip(obj1, obj2):
            if v1 > v2:
                all_leq = False
                break
            if v1 < v2:
                any_lt = True
        
        return all_leq and any_lt
    
    def filter_non_dominated(
        self,
        candidates: List[PathCandidate]
    ) -> List[ParetoCandidate]:
        """
        Non-dominated 경로만 필터링
        
        Args:
            candidates: 경로 후보 목록
            
        Returns:
            Pareto 최적 후보 목록
        """
        if not candidates:
            return []
        
        pareto_candidates = [
            ParetoCandidate.from_path_candidate(c) for c in candidates
        ]
        
        non_dominated = []
        
        for i, candidate in enumerate(pareto_candidates):
            is_dominated = False
            
            for j, other in enumerate(pareto_candidates):
                if i == j:
                    continue
                
                if self.dominates(other.objectives, candidate.objectives):
                    is_dominated = True
                    break
            
            if not is_dominated:
                non_dominated.append(candidate)
        
        return non_dominated
    
    def calculate_crowding_distance(
        self,
        candidates: List[ParetoCandidate]
    ) -> List[ParetoCandidate]:
        """
        혼잡 거리 계산 (다양성 측정)
        
        Args:
            candidates: Pareto 후보 목록
            
        Returns:
            혼잡 거리가 계산된 후보 목록
        """
        if len(candidates) <= 2:
            for c in candidates:
                c.crowding_distance = float('inf')
            return candidates
        
        n = len(candidates)
        n_objectives = len(candidates[0].objectives)
        
        # 초기화
        for c in candidates:
            c.crowding_distance = 0.0
        
        # 각 목적 함수별로 혼잡 거리 계산
        for m in range(n_objectives):
            # 목적 함수 값으로 정렬
            sorted_indices = sorted(
                range(n),
                key=lambda i: candidates[i].objectives[m]
            )
            
            # 경계값 설정
            candidates[sorted_indices[0]].crowding_distance = float('inf')
            candidates[sorted_indices[-1]].crowding_distance = float('inf')
            
            # 범위 계산
            obj_range = (
                candidates[sorted_indices[-1]].objectives[m] -
                candidates[sorted_indices[0]].objectives[m]
            )
            
            if obj_range == 0:
                continue
            
            # 중간 값들의 혼잡 거리 계산
            for i in range(1, n - 1):
                prev_idx = sorted_indices[i - 1]
                curr_idx = sorted_indices[i]
                next_idx = sorted_indices[i + 1]
                
                distance = (
                    candidates[next_idx].objectives[m] -
                    candidates[prev_idx].objectives[m]
                ) / obj_range
                
                candidates[curr_idx].crowding_distance += distance
        
        return candidates
    
    def select_top_k(
        self,
        candidates: List[PathCandidate],
        k: int = 5
    ) -> List[PathCandidate]:
        """
        상위 k개 경로 선택
        
        1. Non-dominated 필터링
        2. 혼잡 거리 계산
        3. 혼잡 거리 기준 상위 k개 선택
        
        Args:
            candidates: 경로 후보 목록
            k: 선택할 개수 (기본: 5)
            
        Returns:
            상위 k개 경로 후보
        """
        if not candidates:
            return []
        
        if len(candidates) <= k:
            return candidates
        
        # Non-dominated 필터링
        pareto_front = self.filter_non_dominated(candidates)
        
        if len(pareto_front) <= k:
            return [p.path_candidate for p in pareto_front]
        
        # 혼잡 거리 계산
        pareto_front = self.calculate_crowding_distance(pareto_front)
        
        # 혼잡 거리 기준 정렬 (내림차순 - 다양성 높은 순)
        pareto_front.sort(key=lambda x: x.crowding_distance, reverse=True)
        
        return [p.path_candidate for p in pareto_front[:k]]
    
    def get_pareto_ranks(
        self,
        candidates: List[PathCandidate]
    ) -> List[ParetoCandidate]:
        """
        모든 후보에 Pareto 순위 할당
        
        Args:
            candidates: 경로 후보 목록
            
        Returns:
            순위가 할당된 Pareto 후보 목록
        """
        if not candidates:
            return []
        
        pareto_candidates = [
            ParetoCandidate.from_path_candidate(c) for c in candidates
        ]
        
        remaining = list(range(len(pareto_candidates)))
        current_rank = 0
        
        while remaining:
            # 현재 남은 것들 중 non-dominated 찾기
            non_dominated_indices = []
            
            for i in remaining:
                is_dominated = False
                for j in remaining:
                    if i == j:
                        continue
                    if self.dominates(
                        pareto_candidates[j].objectives,
                        pareto_candidates[i].objectives
                    ):
                        is_dominated = True
                        break
                
                if not is_dominated:
                    non_dominated_indices.append(i)
            
            # 순위 할당
            for idx in non_dominated_indices:
                pareto_candidates[idx].rank = current_rank
            
            # 처리된 것들 제거
            remaining = [i for i in remaining if i not in non_dominated_indices]
            current_rank += 1
        
        return pareto_candidates
