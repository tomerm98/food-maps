from geopy.geocoders import Nominatim
from place import find_places

ADDRESS = 'יונתן הופסי 6, תל אביב'
RADIUS = 300
locator = Nominatim(user_agent='food-maps')


def main():
    print(f'Finding coordinates for: {ADDRESS}')
    location = locator.geocode(ADDRESS)
    if location is None:
        raise ValueError('Address not found')
    print(f'Finding places in radius of {RADIUS} meters')
    places = find_places(location, RADIUS)
    print(f"Found {len(places)} places")
    print('*********')
    for place in places:
        print(place.name)


if __name__ == "__main__":
    main()
