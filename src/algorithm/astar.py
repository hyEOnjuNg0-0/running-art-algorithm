"""
A* 경로 탐색 알고리즘
목표 도형을 따라가는 최적 경로 탐색
"""
import heapq
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple

from src.domain.entities import Coordinate
from src.data.entities import Node, Edge, RoadGraph
from src.cost.cost_function import CostCalculator


@dataclass
class PathCandidate:
    """
    경로 후보
    
    Attributes:
        path: 노드 ID 목록
        g_cost: 시작점부터 현재까지의 실제 비용
        f_cost: g_cost + 휴리스틱 (총 예상 비용)
        shape_distance: 도형 거리 (정규화)
        length_penalty: 길이 페널티 (정규화)
        crossing_penalty: 횡단보도 페널티 (정규화)
        path_length_km: 실제 경로 길이 (km)
        traffic_light_count: 신호등 개수
    """
    path: List[int]
    g_cost: float
    f_cost: float
    shape_distance: float = 0.0
    length_penalty: float = 0.0
    crossing_penalty: float = 0.0
    path_length_km: float = 0.0
    traffic_light_count: int = 0


@dataclass(order=True)
class PriorityItem:
    """우선순위 큐 아이템"""
    priority: float
    node_id: int = field(compare=False)
    path: List[int] = field(compare=False)
    g_cost: float = field(compare=False)
    path_length_km: float = field(compare=False)
    traffic_light_count: int = field(compare=False)


class AStarPathFinder:
    """
    A* 기반 경로 탐색기
    
    목표 도형과 제약 조건을 고려하여 최적 경로 탐색
    """
    
    def __init__(
        self,
        graph: RoadGraph,
        target_curve: List[Coordinate],
        target_distance_km: float,
        max_crossings: int,
        weights: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    ):
        """
        Args:
            graph: 도로 그래프
            target_curve: 목표 도형 좌표 목록
            target_distance_km: 목표 거리 (km)
            max_crossings: 허용 최대 횡단보도 개수
            weights: (shape, length, crossing) 가중치 튜플
        """
        self.graph = graph
        self.target_curve = target_curve
        self.target_distance_km = target_distance_km
        self.max_crossings = max_crossings
        self.weights = weights
        
        self.cost_calculator = CostCalculator(
            target_curve=target_curve,
            target_distance_km=target_distance_km,
            max_crossings=max_crossings,
            weights=weights
        )
    
    def find_path(
        self,
        start_node_id: int,
        max_iterations: int = 10000
    ) -> Optional[PathCandidate]:
        """
        시작점에서 순환 경로 탐색 (시작점으로 돌아오는 경로)
        
        목표 거리 제한 없음 - ShapeDistance와 LengthPenalty로 최적 경로 선택
        
        Args:
            start_node_id: 시작 노드 ID
            max_iterations: 최대 반복 횟수
            
        Returns:
            최적 경로 후보 (없으면 None)
        """
        start_node = self.graph.get_node(start_node_id)
        if not start_node:
            return None
        
        # 우선순위 큐: (f_cost, node_id, path, g_cost, path_length, traffic_lights)
        open_set: List[PriorityItem] = []
        heapq.heappush(open_set, PriorityItem(
            priority=0.0,
            node_id=start_node_id,
            path=[start_node_id],
            g_cost=0.0,
            path_length_km=0.0,
            traffic_light_count=0
        ))
        
        # 방문 기록: (node_id, path_length_bucket) -> best_cost
        visited: Dict[Tuple[int, int], float] = {}
        
        best_candidate: Optional[PathCandidate] = None
        best_cost = float('inf')
        
        iterations = 0
        while open_set and iterations < max_iterations:
            iterations += 1
            
            current = heapq.heappop(open_set)
            current_node_id = current.node_id
            current_path = current.path
            current_g = current.g_cost
            current_length = current.path_length_km
            current_lights = current.traffic_light_count
            
            # 시작점으로 돌아온 순환 경로 발견 (최소 4개 노드 필요)
            # 거리 제한 없음 - ShapeDistance와 LengthPenalty가 최적 경로 결정
            if (current_node_id == start_node_id and 
                len(current_path) > 3):
                
                # 비용 계산 (ShapeDistance + LengthPenalty + CrossingPenalty)
                cost_result = self.cost_calculator.calculate(current_path, self.graph)
                
                if cost_result.total_cost < best_cost:
                    best_cost = cost_result.total_cost
                    best_candidate = PathCandidate(
                        path=current_path.copy(),
                        g_cost=current_g,
                        f_cost=cost_result.total_cost,
                        shape_distance=cost_result.shape_distance,
                        length_penalty=cost_result.length_penalty,
                        crossing_penalty=cost_result.crossing_penalty,
                        path_length_km=cost_result.path_length_km,
                        traffic_light_count=cost_result.traffic_light_count
                    )
                continue
            
            # 방문 체크 (거리 버킷 기준)
            length_bucket = int(current_length * 10)  # 100m 단위 버킷
            visit_key = (current_node_id, length_bucket)
            
            if visit_key in visited and visited[visit_key] <= current_g:
                continue
            visited[visit_key] = current_g
            
            # 이웃 노드 탐색
            current_node = self.graph.get_node(current_node_id)
            if not current_node:
                continue
            
            for neighbor_id in self.graph.get_neighbors(current_node_id):
                # 이미 경로에 있는 노드는 시작점만 허용
                if neighbor_id in current_path[1:]:
                    continue
                
                neighbor_node = self.graph.get_node(neighbor_id)
                if not neighbor_node:
                    continue
                
                edge = self.graph.get_edge_between(current_node_id, neighbor_id)
                if not edge:
                    continue
                
                # 새 경로 생성
                new_path = current_path + [neighbor_id]
                new_length = current_length + edge.length_km
                
                # 신호등 카운트
                new_lights = current_lights
                if neighbor_node.has_traffic_light and neighbor_id != start_node_id:
                    new_lights += 1
                
                # 엣지 비용 계산
                edge_cost = self.cost_calculator.calculate_edge_cost(
                    current_node, neighbor_node, edge, self.graph
                )
                new_g = current_g + edge_cost
                
                # 휴리스틱 계산
                h_cost = self._heuristic(neighbor_node, start_node, new_length)
                f_cost = new_g + h_cost
                
                heapq.heappush(open_set, PriorityItem(
                    priority=f_cost,
                    node_id=neighbor_id,
                    path=new_path,
                    g_cost=new_g,
                    path_length_km=new_length,
                    traffic_light_count=new_lights
                ))
        
        return best_candidate
    
    def find_path_to_goal(
        self,
        start_node_id: int,
        goal_node_id: int,
        max_iterations: int = 10000
    ) -> Optional[PathCandidate]:
        """
        시작점에서 목표점까지 경로 탐색
        
        Args:
            start_node_id: 시작 노드 ID
            goal_node_id: 목표 노드 ID
            max_iterations: 최대 반복 횟수
            
        Returns:
            최적 경로 후보 (없으면 None)
        """
        start_node = self.graph.get_node(start_node_id)
        goal_node = self.graph.get_node(goal_node_id)
        
        if not start_node or not goal_node:
            return None
        
        open_set: List[PriorityItem] = []
        heapq.heappush(open_set, PriorityItem(
            priority=0.0,
            node_id=start_node_id,
            path=[start_node_id],
            g_cost=0.0,
            path_length_km=0.0,
            traffic_light_count=0
        ))
        
        visited: Dict[int, float] = {}
        
        iterations = 0
        while open_set and iterations < max_iterations:
            iterations += 1
            
            current = heapq.heappop(open_set)
            current_node_id = current.node_id
            current_path = current.path
            current_g = current.g_cost
            current_length = current.path_length_km
            current_lights = current.traffic_light_count
            
            # 목표 도달
            if current_node_id == goal_node_id:
                cost_result = self.cost_calculator.calculate(current_path, self.graph)
                return PathCandidate(
                    path=current_path.copy(),
                    g_cost=current_g,
                    f_cost=cost_result.total_cost,
                    shape_distance=cost_result.shape_distance,
                    length_penalty=cost_result.length_penalty,
                    crossing_penalty=cost_result.crossing_penalty,
                    path_length_km=cost_result.path_length_km,
                    traffic_light_count=cost_result.traffic_light_count
                )
            
            # 방문 체크
            if current_node_id in visited and visited[current_node_id] <= current_g:
                continue
            visited[current_node_id] = current_g
            
            current_node = self.graph.get_node(current_node_id)
            if not current_node:
                continue
            
            for neighbor_id in self.graph.get_neighbors(current_node_id):
                if neighbor_id in current_path:
                    continue
                
                neighbor_node = self.graph.get_node(neighbor_id)
                if not neighbor_node:
                    continue
                
                edge = self.graph.get_edge_between(current_node_id, neighbor_id)
                if not edge:
                    continue
                
                new_path = current_path + [neighbor_id]
                new_length = current_length + edge.length_km
                
                new_lights = current_lights
                if neighbor_node.has_traffic_light:
                    new_lights += 1
                
                edge_cost = self.cost_calculator.calculate_edge_cost(
                    current_node, neighbor_node, edge, self.graph
                )
                new_g = current_g + edge_cost
                
                h_cost = self._simple_heuristic(neighbor_node, goal_node)
                f_cost = new_g + h_cost
                
                heapq.heappush(open_set, PriorityItem(
                    priority=f_cost,
                    node_id=neighbor_id,
                    path=new_path,
                    g_cost=new_g,
                    path_length_km=new_length,
                    traffic_light_count=new_lights
                ))
        
        return None
    
    def _heuristic(
        self,
        current_node: Node,
        goal_node: Node,
        current_length: float
    ) -> float:
        """
        휴리스틱 함수: 목표까지의 추정 비용
        
        Args:
            current_node: 현재 노드
            goal_node: 목표 노드 (시작점)
            current_length: 현재까지의 경로 길이
            
        Returns:
            추정 비용
        """
        # 목표점까지의 직선 거리
        dist_to_goal = current_node.distance_to(goal_node)
        
        # 남은 거리 추정
        remaining_distance = max(0, self.target_distance_km - current_length)
        
        # 목표 곡선까지의 거리 추정
        min_curve_dist = self._min_distance_to_curve(current_node)
        
        # 가중치 적용 휴리스틱
        h = (
            self.weights[0] * (min_curve_dist / self.target_distance_km) +
            self.weights[1] * (abs(remaining_distance - dist_to_goal) / self.target_distance_km)
        )
        
        return h * 0.5  # 휴리스틱 스케일 조정 (admissible 유지)
    
    def _simple_heuristic(self, current_node: Node, goal_node: Node) -> float:
        """단순 휴리스틱: 직선 거리 기반"""
        dist = current_node.distance_to(goal_node)
        return dist / self.target_distance_km * self.weights[1]
    
    def _min_distance_to_curve(self, node: Node) -> float:
        """노드에서 목표 곡선까지의 최소 거리"""
        min_dist = float('inf')
        
        for i in range(len(self.target_curve) - 1):
            p1 = self.target_curve[i]
            p2 = self.target_curve[i + 1]
            
            dist = self._point_to_segment_distance(
                node.lat, node.lng,
                p1.lat, p1.lng,
                p2.lat, p2.lng
            )
            min_dist = min(min_dist, dist)
        
        return min_dist
    
    def _point_to_segment_distance(
        self,
        px: float, py: float,
        x1: float, y1: float,
        x2: float, y2: float
    ) -> float:
        """점에서 선분까지의 거리 (km)"""
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return self._haversine(px, py, x1, y1)
        
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        
        return self._haversine(px, py, proj_x, proj_y)
    
    def _haversine(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """두 좌표 사이의 거리 (km)"""
        R = 6371
        
        lat1_r, lng1_r = math.radians(lat1), math.radians(lng1)
        lat2_r, lng2_r = math.radians(lat2), math.radians(lng2)
        
        dlat = lat2_r - lat1_r
        dlng = lng2_r - lng1_r
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
