from dataclasses import dataclass
from typing import List, Union

import requests
from overpy import Overpass, Node, Result, Way, Element

AMENITY_FILTER = '["amenity"~"cafe|restaurant|bar|pub|fast_food"]'
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


def _get_element_location(element: Element) -> Location:
    if isinstance(element, Way):
        return Location(latitude=element.center_lat, longitude=element.center_lon)
    if isinstance(element, Node):
        return Location(latitude=element.lat, longitude=element.lon)
    raise ValueError(f'Unsupported element type {type(element)}')


def _extract_places(result: Result) -> List[Place]:
    elements = result.nodes + result.ways
    return [
        Place(
            name=element.tags['name'],
            type=element.tags['amenity'],
            location=_get_element_location(element),
        )
        for element in elements
        if 'name' in element.tags
    ]


def find_nearby_places(location: Location, radius: int) -> List[Place]:
    query = f"""
    [out:json];
    (
       nw(around:{radius},{location.latitude},{location.longitude}){AMENITY_FILTER};
    );
    out body center;
    """
    return _extract_places(overpass.query(query))


def find_places_by_area(name: str) -> List[Place]:
    query = f"""
    [out:json];
    area[name="{name}"]->.searchArea;
    (
       nw(area.searchArea){AMENITY_FILTER};
    );
    out body center;
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
