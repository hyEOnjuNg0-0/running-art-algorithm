"""
데이터 레이어
OSM 데이터 처리 및 그래프 관리
"""
from src.data.entities import Node, Edge, RoadGraph, RoadType
from src.data.repository import GraphRepository, GraphFetchError
from src.data.cache_service import GraphCacheService

__all__ = [
    'Node',
    'Edge',
    'RoadGraph',
    'RoadType',
    'GraphRepository',
    'GraphFetchError',
    'GraphCacheService',
]


def get_osm_repository():
    """
    OSMGraphRepository 인스턴스 반환 (lazy import)
    osmnx가 설치되어 있을 때만 사용 가능
    """
    from src.data.osm_repository import OSMGraphRepository
    return OSMGraphRepository()
