"""
가중치 샘플링
Dirichlet 분포를 사용하여 다양한 가중치 조합 생성
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class WeightVector:
    """
    가중치 벡터
    
    Attributes:
        alpha: 도형 거리 가중치
        beta: 길이 페널티 가중치
        gamma: 횡단보도 페널티 가중치
    """
    alpha: float
    beta: float
    gamma: float
    
    def __post_init__(self):
        total = self.alpha + self.beta + self.gamma
        if not np.isclose(total, 1.0, atol=1e-6):
            raise ValueError(f"가중치 합이 1이어야 합니다 (현재: {total})")
    
    def to_tuple(self) -> Tuple[float, float, float]:
        """튜플 형태로 반환"""
        return (self.alpha, self.beta, self.gamma)


class WeightSampler:
    """
    Dirichlet 분포 기반 가중치 샘플러
    
    Dir(1, 1, 1)에서 가중치 조합을 샘플링하여
    다양한 탐색 방향을 생성
    """
    
    def __init__(self, seed: int = None):
        """
        Args:
            seed: 랜덤 시드 (재현성을 위해)
        """
        self.rng = np.random.default_rng(seed)
    
    def sample(self, n_samples: int = 20) -> List[WeightVector]:
        """
        Dirichlet 분포에서 가중치 샘플링
        
        Args:
            n_samples: 샘플 개수 (기본: 20)
            
        Returns:
            WeightVector 목록
        """
        if n_samples <= 0:
            raise ValueError("샘플 개수는 양수여야 합니다")
        
        # Dir(1, 1, 1) - 균등 Dirichlet 분포
        alpha = np.array([1.0, 1.0, 1.0])
        samples = self.rng.dirichlet(alpha, size=n_samples)
        
        return [
            WeightVector(alpha=s[0], beta=s[1], gamma=s[2])
            for s in samples
        ]
    
    def sample_with_bias(
        self,
        n_samples: int = 20,
        shape_bias: float = 1.0,
        length_bias: float = 1.0,
        crossing_bias: float = 1.0
    ) -> List[WeightVector]:
        """
        편향된 Dirichlet 분포에서 가중치 샘플링
        
        Args:
            n_samples: 샘플 개수
            shape_bias: 도형 거리 편향 (>1: 더 중요)
            length_bias: 길이 페널티 편향
            crossing_bias: 횡단보도 페널티 편향
            
        Returns:
            WeightVector 목록
        """
        if n_samples <= 0:
            raise ValueError("샘플 개수는 양수여야 합니다")
        if any(b <= 0 for b in [shape_bias, length_bias, crossing_bias]):
            raise ValueError("편향 값은 양수여야 합니다")
        
        alpha = np.array([shape_bias, length_bias, crossing_bias])
        samples = self.rng.dirichlet(alpha, size=n_samples)
        
        return [
            WeightVector(alpha=s[0], beta=s[1], gamma=s[2])
            for s in samples
        ]
    
    def get_corner_weights(self) -> List[WeightVector]:
        """
        극단적인 가중치 조합 반환 (코너 케이스)
        
        Returns:
            도형 중심, 길이 중심, 횡단보도 중심 가중치
        """
        return [
            WeightVector(alpha=0.8, beta=0.1, gamma=0.1),  # 도형 중심
            WeightVector(alpha=0.1, beta=0.8, gamma=0.1),  # 길이 중심
            WeightVector(alpha=0.1, beta=0.1, gamma=0.8),  # 횡단보도 중심
            WeightVector(alpha=0.34, beta=0.33, gamma=0.33),  # 균형
        ]
    
    def sample_with_corners(self, n_samples: int = 16) -> List[WeightVector]:
        """
        코너 가중치를 포함한 샘플링
        
        Args:
            n_samples: 추가 샘플 개수 (코너 4개 + n_samples)
            
        Returns:
            WeightVector 목록
        """
        corners = self.get_corner_weights()
        additional = self.sample(n_samples)
        return corners + additional
