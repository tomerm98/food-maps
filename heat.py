import folium
import geopandas as gpd
import numpy as np
from shapely import Polygon, Point
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

GRID_CELL_SIZE = 50
LAT_DEGREES = GRID_CELL_SIZE / 111000
LON_DEGREES = GRID_CELL_SIZE / 89000

POLYGON_COORDS = [
    (34.7774211, 32.097893),
    (34.7731725, 32.0983292),
    (34.765834, 32.078659),
    (34.7819701, 32.0710224),
    (34.7891799, 32.0710224),
    (34.7932569, 32.078659),
    (34.7956601, 32.0876765),
    (34.7938148, 32.097893),
    (34.7842875, 32.0961479),
    (34.7787515, 32.0961115),
    (34.7774211, 32.097893)
]

GPS_CRS = 'EPSG:4326'
METERS_CRS = "EPSG:3857"

polygon_frame = gpd.GeoDataFrame(geometry=[Polygon(POLYGON_COORDS)], crs=GPS_CRS)


coords = [(32.0853, 34.7818), (32.0850, 34.7820), (32.0860, 34.7815)]  # Example coordinates
places_frame = gpd.GeoDataFrame(geometry=[Point(x, y) for y, x in coords], crs=GPS_CRS)

# Create a grid of points that cover Tel Aviv
min_x, min_y, max_x, max_y = polygon_frame.geometry[0].bounds
x_range = np.arange(min_x, max_x, LON_DEGREES)
y_range = np.arange(min_y, max_y, LAT_DEGREES)
grid_points = [Point(x, y) for x in x_range for y in y_range]
grid_frame = gpd.GeoDataFrame(geometry=grid_points, crs=GPS_CRS)
grid_frame = grid_frame[grid_frame.geometry.within(polygon_frame.geometry[0])]


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
    colormap = plt.get_cmap("coolwarm")

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
            fill_opacity=0.3,
            weight=0,
        ).add_to(m)
    m.save('heatmap_grid.html')
