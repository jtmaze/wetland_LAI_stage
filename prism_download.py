# %% 1.0 Libraries and File Paths

import ee
import geemap
import geopandas as gpd
from shapely.geometry import box
import pprint as pp

ee.Initialize()
ee.Authenticate()

bounds_path = './data/basin_boundaries/Final_Basins.shp'
watersheds = gpd.read_file(bounds_path)
total_bounds = watersheds.total_bounds
bbox_geom = box(*total_bounds)
bounds = gpd.GeoDataFrame(geometry=[bbox_geom], crs=watersheds.crs)
bounds = bounds.to_crs('EPSG:4326')

# %% 2.0 Functions

def convert_gpd_geom_to_ee(geom, crs):

    coords = list(geom.exterior.coords)
    coords_list = [[x, y] for x, y in coords]
    # For EPSG:4326, don't specify proj parameter (it's the default)
    if crs == 'EPSG:4326' or crs is None:
        ee_poly = ee.Geometry.Polygon(coords_list)
    else:
        # For other CRS, convert to ee.Projection
        ee_poly = ee.Geometry.Polygon(coords_list, proj=ee.Projection(crs))
    
    return ee_poly


def export_prism_timeseries(start_date, end_date, geom, scale=4_000):
    """
    Export the PRISM timeseries data averaged over the study region
    """
    prism = ee.ImageCollection('OREGONSTATE/PRISM/AN81d')
    prism_filtered = prism.filter(ee.Filter.date(start_date, end_date))
    variables = ['ppt', 'tmean', 'tmin', 'tmax']
    prism_vars = prism_filtered.select(variables)

    def reduce_image(image):
        """
        Helper function to calculate mean climate stats over the region
        """
        # NOTE: Does this reduce_image function weight edge cells appropriately?
        clipped = image.clip(geom)

        means = clipped.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geom,
            scale=scale,
            maxPixels=1e4
        )

        date = image.date().format('YYYY-MM-dd')

        return ee.Feature(None, { # No geometry
            'date': date, 
            'precip': means.get('ppt'),
            'temp': means.get('tmean'),
            'temp_min': means.get('tmin'),
            'temp_max': means.get('tmax')
        })

    # Run the helper function
    timeseries = prism_vars.map(reduce_image)

    export = ee.batch.Export.table.toDrive(
        collection=timeseries,
        description='PRISM_timeseries_Bradford',
        fileNamePrefix='PRISM_timeseries_Bradford',
        fileFormat='CSV'
    )
    export.start()

    print('Exporting')



# %% 3.0

bounds_geom = bounds.geometry.iloc[0]
ee_bounds = convert_gpd_geom_to_ee(bounds_geom, 'EPSG:4326')

#export_prism_timeseries(start_date='2019-12-01', end_date='2025-05-01', geom=ee_bounds, scale=4_000)

# %% 4.0 Cumulative precip plot

# Define your time interval
start_date = '2019-12-01'
end_date = '2025-05-01'

# Filter the PRISM ImageCollection for precipitation (ppt) images and date range
rainfall_ic = ee.ImageCollection('OREGONSTATE/PRISM/AN81d') \
    .filter(ee.Filter.date(start_date, end_date)) \
    .select('ppt')

# Calculate cumulative rainfall by summing all daily ppt images
cumulative_rainfall = rainfall_ic.sum().clip(ee_bounds)

# Get the min and max cumulative rainfall values over your study area for visualization
rain_stats = cumulative_rainfall.reduceRegion(
    reducer=ee.Reducer.minMax(),
    geometry=ee_bounds,
    scale=4000,  # PRISM native resolution
    maxPixels=1e9
)

rain_min = rain_stats.get('ppt_min').getInfo()
rain_max = rain_stats.get('ppt_max').getInfo()

print(f"Cumulative rainfall range: {rain_min:.1f} mm to {rain_max:.1f} mm")

# Create a geemap map instance
Map = geemap.Map()

# Add your study area bounds to the map
Map.addLayer(ee_bounds, {'color': 'red'}, 'Study Area Bounds')

# Define visualization parameters using the calculated min/max and a suitable palette
vis_params = {
    'min': rain_min,
    'max': rain_max,
    'palette': ['white', 'blue']
}

# Add the cumulative rainfall layer to your map
Map.addLayer(cumulative_rainfall, vis_params, 'Cumulative Rainfall')

# Add a colorbar to the map
Map.add_colorbar(vis_params, label='Cumulative Rainfall (mm)')

# Center the map on your study area
Map.centerObject(ee_bounds, zoom=8)

# Display the map
Map

# %% Average temperature plot

start_date = '2019-12-01'
end_date = '2025-05-01'

# Filter the PRISM ImageCollection for tmean and date range
temp_ic = ee.ImageCollection('OREGONSTATE/PRISM/AN81d') \
    .filter(ee.Filter.date(start_date, end_date)) \
    .select('tmean')

# Calculate the average temperature over all daily images
avg_temp = temp_ic.mean().clip(ee_bounds)

# Get the min and max average temperature values for visualization
temp_stats = avg_temp.reduceRegion(
    reducer=ee.Reducer.minMax(),
    geometry=ee_bounds,
    scale=4000,  # PRISM native resolution
    maxPixels=1e9
)

temp_min = temp_stats.get('tmean_min').getInfo()
temp_max = temp_stats.get('tmean_max').getInfo()

print(f"Average temperature range: {temp_min:.1f} °C to {temp_max:.1f} °C")

# Create a geemap map instance
Map = geemap.Map()

# Add the study area bounds
#Map.addLayer(ee_bounds, {'color': 'red'}, 'Study Area Bounds')

# Define visualization parameters
vis_params = {
    'min': temp_min,
    'max': temp_max,
    'palette': ['blue', 'white', 'red']
}

# Add the average temperature layer to the map
Map.addLayer(avg_temp, vis_params, 'Average Temperature')

# Add a colorbar
Map.add_colorbar(vis_params, label='Average Temp (°C)')

# Center and display
Map.centerObject(ee_bounds, 8)
Map

# %%
