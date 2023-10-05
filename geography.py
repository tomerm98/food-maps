from dataclasses import dataclass
from typing import List

from overpy import Overpass, Node, Result

overpass = Overpass()
AMENITY_TYPES = ['pub', 'bar', 'cafe', 'restaurant', 'fast_food']


@dataclass
class Coordinates:
    latitude: float
    longitude: float


@dataclass
class Place:
    name: str
    type: str
    coordinates: Coordinates


def _get_node_coordinates(node: Node) -> Coordinates:
    return Coordinates(latitude=node.lat, longitude=node.lon)


def _extract_places(result: Result) -> List[Place]:
    return [
        Place(
            name=node.tags['name'],
            type=node.tags['amenity'],
            coordinates=_get_node_coordinates(node),
        )
        for node in result.nodes
        if 'name' in node.tags
    ]


def find_nearby_places(coordinates: Coordinates, radius: int) -> List[Place]:
    node_filters = '\n'.join(
        f'node(around:{radius},{coordinates.latitude},{coordinates.longitude})["amenity"="{amenity_type}"];'
        for amenity_type in AMENITY_TYPES
    )
    query = f"""
    [out:json];
    (
       {node_filters}
    );
    out body;
    """
    return _extract_places(overpass.query(query))


def find_places_by_area(name: str) -> List[Place]:
    node_filters = '\n'.join(
        f'node(area.searchArea)["amenity"="{amenity_type}"];'
        for amenity_type in AMENITY_TYPES
    )
    query = f"""
    [out:json];
    area[name="{name}"]->.searchArea;
    (
       {node_filters}
    );
    out body;
    """
    return _extract_places(overpass.query(query))


def get_area_coordinates(name: str) -> List[Coordinates]:
    query = f"""
    [out:json];
    relation[name="{name}"][type="boundary"];
    (._;>;);
    out body;
    """
    result = overpass.query(query)
    return [
        _get_node_coordinates(node)
        for way in result.ways
        for node in way.nodes
    ]
