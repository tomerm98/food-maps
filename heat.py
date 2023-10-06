from enum import Enum
from functools import partial
from typing import List, Iterator, Callable, Tuple

from folium import Map, Rectangle, Circle
from geopandas import GeoDataFrame
from geopy import Point as GeographicPoint
from matplotlib.colors import LogNorm, to_hex
from matplotlib.pyplot import get_cmap as get_color_map
from pandas import Series
from shapely import Polygon, Point as GeometricPoint

from geography import find_places_by_area, get_area_borders, move_point, Direction, Place, get_address_location

AREA_NAME = 'תל אביב-יפו'
GRID_CELL_SIZE = 50
NEARBY_PLACE_RADIUS = 800
PLACES_COLUMN = 'places'


# TODO create package

class CRS:
    GPS = 'EPSG:4326'
    METERS = "EPSG:3857"


def to_geometric_point(point: GeographicPoint) -> GeometricPoint:
    return GeometricPoint(point.longitude, point.latitude)


def to_geographic_point(point: GeometricPoint) -> GeographicPoint:
    return GeographicPoint(latitude=point.y, longitude=point.x)


def get_polygon_grid(polygon: Polygon) -> Iterator[GeometricPoint]:
    """
    Creates points inside the given polygon, spaced out by GRID_CELL_SIZE
    """
    min_lon, min_lat, max_lon, max_lat = polygon.bounds
    current_point = GeographicPoint(latitude=min_lat, longitude=min_lon)
    while current_point.latitude <= max_lat:
        while current_point.longitude <= max_lon:
            geometric_point = to_geometric_point(current_point)
            if polygon.contains(geometric_point):
                yield geometric_point
            current_point = move_point(point=current_point, meters=GRID_CELL_SIZE, direction=Direction.EAST)
        current_point.longitude = min_lon
        current_point = move_point(point=current_point, meters=GRID_CELL_SIZE, direction=Direction.NORTH)


def get_places_column(grid_frame: GeoDataFrame, places: List[Place]) -> Series:
    places_geometric_points = [to_geometric_point(place.location) for place in places]
    places_frame = GeoDataFrame(geometry=places_geometric_points, crs=CRS.GPS).to_crs(CRS.METERS)

    def count_nearby_places(point: GeometricPoint) -> int:
        buffer = point.buffer(NEARBY_PLACE_RADIUS)
        intersection = places_frame.intersects(buffer)
        return len(places_frame[intersection])

    return grid_frame.to_crs(CRS.METERS).geometry.apply(count_nearby_places)


def get_color_picker(max_value: int) -> Callable[[int], str]:
    norm = LogNorm(vmin=1, vmax=max_value)
    color_map = get_color_map('coolwarm')

    def pick_color(value: int) -> str:
        return to_hex(color_map(norm(value) or 0))

    return pick_color


def get_grid_cell_bounds(grid_point: GeographicPoint) -> Tuple[GeographicPoint, GeographicPoint]:
    move_grid_point = partial(move_point, meters=GRID_CELL_SIZE / 2)
    return (
        move_grid_point(move_grid_point(grid_point, direction=Direction.NORTH), direction=Direction.EAST),
        move_grid_point(move_grid_point(grid_point, direction=Direction.SOUTH), direction=Direction.WEST),
    )


def main():
    print(f'Getting area data for: {AREA_NAME}')
    area_center = get_address_location(AREA_NAME)
    area_border = get_area_borders(AREA_NAME)
    area_polygon = Polygon([to_geometric_point(point) for point in area_border])

    print('Creating grid points')
    grid_points = list(get_polygon_grid(area_polygon))
    grid_frame = GeoDataFrame(geometry=grid_points, crs=CRS.GPS)

    print('Finding places in the area')
    places = find_places_by_area(AREA_NAME)
    grid_frame[PLACES_COLUMN] = get_places_column(grid_frame, places)
    max_places_count = grid_frame[PLACES_COLUMN].max()
    pick_color = get_color_picker(max_places_count)

    print('Building map')
    heat_map = Map(location=(area_center.latitude, area_center.longitude))

    for _, row in grid_frame.iterrows():
        places_count = row[PLACES_COLUMN]
        Rectangle(
            bounds=[
                (point.latitude, point.longitude)
                for point in get_grid_cell_bounds(to_geographic_point(row.geometry))
            ],
            location=(row.geometry.y, row.geometry.x),
            color=pick_color(places_count),
            fill=True,
            fill_opacity=0.6,
            tooltip=places_count,
            weight=0,
        ).add_to(heat_map)
    print('Saving map')
    heat_map.save('heatmap_grid.html')


if __name__ == '__main__':
    main()
