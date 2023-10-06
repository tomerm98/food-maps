from food_maps.geography import find_nearby_places, get_address_location

ADDRESS = 'יונתן הופסי 6, תל אביב'
RADIUS = 300


def main():
    print(f'Finding coordinates for: {ADDRESS}')
    location = get_address_location(ADDRESS)
    print(f'Finding places in radius of {RADIUS} meters')
    places = find_nearby_places(location, RADIUS)
    print(f"Found {len(places)} places")
    print('*********')
    for place in places:
        print(place.name)


if __name__ == "__main__":
    main()
