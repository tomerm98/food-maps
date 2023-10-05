from dataclasses import dataclass
from typing import List

import overpy
from geopy import Location

overpass = overpy.Overpass()
AMENITY_TYPES = ['pub', 'bar', 'cafe', 'restaurant', 'fast_food']


@dataclass
class Place:
    name: str
    type: str
    latitude: float
    longitude: float


def find_places(location: Location, radius: int) -> List[Place]:
    node_filters = '\n'.join(
        f'node(around:{radius},{location.latitude},{location.longitude})["amenity"="{amenity_type}"];'
        for amenity_type in AMENITY_TYPES
    )
    query = f"""[out:json];
     (
        {node_filters}
     );
     out body;"""
    result = overpass.query(query)
    return [
        Place(name=node.tags['name'], type=node.tags['amenity'], latitude=node.lat, longitude=node.lon)
        for node in result.nodes
        if 'name' in node.tags
    ]