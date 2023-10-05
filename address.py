from geopy import Location
from geopy.geocoders import Nominatim

from geography import find_nearby_places, Coordinates

ADDRESS = 'יונתן הופסי 6, תל אביב'
RADIUS = 300
locator = Nominatim(user_agent='food-maps')


def main():
    print(f'Finding coordinates for: {ADDRESS}')
    location: Location = locator.geocode(ADDRESS)
    if location is None:
        raise ValueError('Address not found')
    coordinates = Coordinates(latitude=location.latitude, longitude=location.longitude)
    print(f'Finding places in radius of {RADIUS} meters')
    places = find_nearby_places(coordinates, RADIUS)
    print(f"Found {len(places)} places")
    print('*********')
    for place in places:
        print(place.name)


if __name__ == "__main__":
    main()
