from dataclasses import dataclass
from typing import List

import requests
from overpy import Overpass, Node, Result

AMENITY_TYPES = ['pub', 'bar', 'cafe', 'restaurant', 'fast_food']
NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'

overpass = Overpass()


@dataclass
class Location:
    latitude: float
    longitude: float


@dataclass
class Place:
    name: str
    type: str
    location: Location


def _get_node_location(node: Node) -> Location:
    return Location(latitude=node.lat, longitude=node.lon)


def _extract_places(result: Result) -> List[Place]:
    return [
        Place(
            name=node.tags['name'],
            type=node.tags['amenity'],
            location=_get_node_location(node),
        )
        for node in result.nodes
        if 'name' in node.tags
    ]


def find_nearby_places(location: Location, radius: int) -> List[Place]:
    node_filters = '\n'.join(
        f'node(around:{radius},{location.latitude},{location.longitude})["amenity"="{amenity_type}"];'
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


def get_address_location(address: str) -> Location:
    response = requests.get(NOMINATIM_URL, params={'q': address, 'format': 'json'})
    data = response.json()[0]
    return Location(latitude=data['lat'], longitude=data['lon'])


def get_area_polygon(name: str) -> List[Location]:
    response = requests.get(NOMINATIM_URL, params={'q': name, 'format': 'json', 'polygon_geojson': 1})
    data = response.json()[0]['geojson']['coordinates'][0]
    return [Location(latitude=lat, longitude=lon) for lon, lat in data]
