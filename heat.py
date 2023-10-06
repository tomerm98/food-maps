import folium
from folium.plugins import HeatMap
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely import Polygon, Point
import matplotlib.colors as mcolors
from geography import find_places_by_area, get_area_polygon

AREA_NAME = 'תל אביב-יפו'
GRID_CELL_SIZE = 50
LAT_DEGREES = GRID_CELL_SIZE / 111000
LON_DEGREES = GRID_CELL_SIZE / 89000  # TODO replace magic number to make this work on other areas in the word

GPS_CRS = 'EPSG:4326'
METERS_CRS = "EPSG:3857"


# Calculate the number of restaurants within 500m for each grid point


def test():
    area_coordinates = get_area_polygon(AREA_NAME)
    area_frame = gpd.GeoDataFrame(geometry=[Polygon([(c.longitude, c.latitude) for c in area_coordinates])],
                                  crs=GPS_CRS)

    places = find_places_by_area(AREA_NAME)
    places_points = [Point(place.location.longitude, place.location.latitude) for place in places]
    places_frame = gpd.GeoDataFrame(geometry=places_points, crs=GPS_CRS)

    # Create a grid of points that cover Tel Aviv
    min_x, min_y, max_x, max_y = area_frame.geometry[0].bounds
    x_range = np.arange(min_x, max_x, LON_DEGREES)
    y_range = np.arange(min_y, max_y, LAT_DEGREES)
    grid_points = [Point(x, y) for x in x_range for y in y_range]
    grid_frame = gpd.GeoDataFrame(geometry=grid_points, crs=GPS_CRS)
    grid_frame = grid_frame[grid_frame.geometry.within(area_frame.geometry[0])]

    def count_nearby_places(point):
        buffer = point.buffer(500)
        return len(places_frame[places_frame.intersects(buffer)])

    # Project to coordinate system in meters for accurate distance calculation
    places_frame = places_frame.to_crs(METERS_CRS)
    grid_frame: gpd.GeoDataFrame = grid_frame.to_crs(METERS_CRS)
    grid_frame["places"] = grid_frame.geometry.apply(count_nearby_places)
    grid_frame.to_file('grid')


if __name__ == '__main__':
    # Project back to WGS84 for mapping
    test()
    print('Loading frame')
    grid_frame = gpd.GeoDataFrame.from_file('grid').to_crs(GPS_CRS)
    print('Normalizing data')
    max_count = grid_frame["places"].max()
    min_count = grid_frame["places"].min()
    norm = mcolors.LogNorm(vmin=1, vmax=max_count)
    print('Building map')
    m = folium.Map(location=[32.0853, 34.7818], zoom_start=14)
    colormap = plt.get_cmap("coolwarm")
    for _, row in grid_frame.iterrows():
        color = mcolors.to_hex(colormap(norm(row['places']) or 0))
        folium.Rectangle(
            bounds=[
                (row.geometry.y + LAT_DEGREES / 2, row.geometry.x + LON_DEGREES / 2),
                (row.geometry.y - LAT_DEGREES / 2, row.geometry.x - LON_DEGREES / 2),
            ],
            location=(row.geometry.y, row.geometry.x),
            color=color,
            fill=True,
            fill_opacity=0.6,
            tooltip=row['places'],
            weight=0,
        ).add_to(m)
    print('Saving map')
    m.save('heatmap_grid.html')
