import folium
import geopandas as gpd
import numpy as np
from shapely import Polygon, Point
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from geography import find_places_by_area, get_area_coordinates

AREA_NAME = 'תל אביב-יפו'
GRID_CELL_SIZE = 100
LAT_DEGREES = GRID_CELL_SIZE / 111000
LON_DEGREES = GRID_CELL_SIZE / 89000

GPS_CRS = 'EPSG:4326'
METERS_CRS = "EPSG:3857"


area_coordinates = get_area_coordinates(AREA_NAME)
area_frame = gpd.GeoDataFrame(geometry=[Polygon([(c.longitude, c.latitude) for c in area_coordinates])], crs=GPS_CRS)


places = find_places_by_area(AREA_NAME)
places_points = [Point(place.coordinates.longitude, place.coordinates.latitude) for place in places]
places_frame = gpd.GeoDataFrame(geometry=places_points, crs=GPS_CRS)

# Create a grid of points that cover Tel Aviv
min_x, min_y, max_x, max_y = area_frame.geometry[0].bounds
x_range = np.arange(min_x, max_x, LON_DEGREES)
y_range = np.arange(min_y, max_y, LAT_DEGREES)
grid_points = [Point(x, y) for x in x_range for y in y_range]
grid_frame = gpd.GeoDataFrame(geometry=grid_points, crs=GPS_CRS)
grid_frame = grid_frame[grid_frame.geometry.within(area_frame.geometry[0])]


# Project to coordinate system in meters for accurate distance calculation
places_frame = places_frame.to_crs(METERS_CRS)
grid_frame = grid_frame.to_crs(METERS_CRS)


# Calculate the number of restaurants within 500m for each grid point
def count_nearby_places(point):
    buffer = point.buffer(500)
    return len(places_frame[places_frame.intersects(buffer)])


if __name__ == '__main__':
    grid_frame["restaurant_count"] = grid_frame.geometry.apply(count_nearby_places)

    # Project back to WGS84 for mapping
    grid_frame = grid_frame.to_crs(GPS_CRS)

    # Create Folium map
    m = folium.Map(location=[32.0853, 34.7818], zoom_start=14)

    # Normalize the restaurant_count column
    max_count = grid_frame["restaurant_count"].max()
    min_count = grid_frame["restaurant_count"].min()
    norm = plt.Normalize(min_count, max_count)

    # Choose a colormap
    colormap = plt.get_cmap("PuRd")

    # Add heatmap
    for _, row in grid_frame.iterrows():
        color = mcolors.to_hex(colormap(norm(row['restaurant_count'])))
        folium.Rectangle(
            bounds=[
                (row.geometry.y + LAT_DEGREES / 2, row.geometry.x + LON_DEGREES / 2),
                (row.geometry.y - LAT_DEGREES / 2, row.geometry.x - LON_DEGREES / 2),
            ],
            location=(row.geometry.y, row.geometry.x),
            color=color,
            fill=True,
            fill_opacity=0.6,
            weight=0,
        ).add_to(m)
    m.save('heatmap_grid.html')
