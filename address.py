from decimal import Decimal
from functools import partial
from typing import Iterator, List, Optional, TypedDict

import geopy.distance
from googleplaces import GooglePlaces, geocode_location, Place, GooglePlacesSearchResult, GooglePlacesError
from googleplaces.types import TYPE_CAFE, TYPE_BAR, TYPE_RESTAURANT
from retry import retry

API_KEY = 'AIzaSyB14kaOq4UcUnuI4i36RIzjgNFWcs2i6PA'
client = GooglePlaces(API_KEY)
LOCATION = 'כיכר רבין, תל אביב'
LANGUAGE = 'iw'  # hebrew
RADIUS = 50


class GeoLocation(TypedDict):
    lat: Decimal
    lng: Decimal


def geolocation_to_coordinates(geolocation: GeoLocation) -> tuple:
    return geolocation['lat'], geolocation['lng']


def get_distance(geoloc1: GeoLocation, geoloc2: GeoLocation) -> float:
    coordinates1 = geolocation_to_coordinates(geoloc1)
    coordinates2 = geolocation_to_coordinates(geoloc2)
    return geopy.distance.geodesic(coordinates1, coordinates2).meters


@retry(GooglePlacesError, tries=10, delay=5, jitter=5)
def _run_nearby_search(
    geolocation: GeoLocation,
    place_type: str,
    page_token: Optional[str] = None
) -> GooglePlacesSearchResult:
    return client.nearby_search(
        lat_lng=geolocation,
        rankby='distance',
        types=[place_type],
        language=LANGUAGE,
        pagetoken=page_token,
    )


def find_places(geolocation: GeoLocation, place_type: str) -> Iterator[Place]:
    print('- Fetching places')
    result = _run_nearby_search(geolocation=geolocation, place_type=place_type)
    yield from result.places

    while result.has_next_page_token:
        print('- Fetching more places')
        result = _run_nearby_search(geolocation=geolocation, place_type=place_type, page_token=result.next_page_token)
        yield from result.places


def find_places_by_radius(geolocation: GeoLocation, place_type: str, radius: float) -> Iterator[Place]:
    # We are not using the 'radius' param of the Google api because it's stupid and doesn't actually work
    for place in find_places(geolocation=geolocation, place_type=place_type):
        distance = get_distance(geolocation, place.geo_location)
        if distance > radius:
            break
        yield place


def dedup_places(places: List[Place]) -> List[Place]:
    id_to_place = {p.place_id: p for p in places}
    return list(id_to_place.values())


def main():
    location = LOCATION
    radius = RADIUS
    print(f'Finding coordinates for: {location}')
    geolocation = geocode_location(location=location, api_key=API_KEY)
    print(f'Finding places in radius of {radius} meters')
    find_places_nearby = partial(find_places_by_radius, geolocation=geolocation, radius=radius)
    print('Fetching coffee shops')
    coffee_shops = list(find_places_nearby(place_type=TYPE_CAFE))
    print('Fetching restaurants')
    restaurants = list(find_places_nearby(place_type=TYPE_RESTAURANT))
    print('Fetching bars')
    bars = list(find_places_nearby(place_type=TYPE_BAR))
    print()
    print(f"Found {len(coffee_shops)} coffee shops, {len(restaurants)} restaurants, {len(bars)} bars")
    total_places = dedup_places(coffee_shops + restaurants + bars)
    print(f'Total {len(total_places)} unique places')
    print('*****')
    print()
    for place in total_places:
        print(place.name)


if __name__  == "_main_":
    main()