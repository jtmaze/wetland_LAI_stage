# %%

import os
import pandas as pd

from WaterBalanceModel.wetland_model import WetlandModel

# main_dir = '/wetland_LAI_stage/'
# os.chdir(main_dir)

wl_path = './data/waterlevel_offsets_tracked_Spring2025.csv'
wl = pd.read_csv(wl_path)

# %%
wl = wl.rename(columns={'revised_depth': 'water_level'})
wl['Date'] = pd.to_datetime(wl['Date'])

# %%

wl['hour'] = wl['Date'].dt.floor('h')

wl_hourly = wl.groupby(['hour', 'Site_ID']).agg(
    {'water_level': 'mean',
     'flag': 'sum'}
).reset_index()

wl_hourly.rename(columns={'hour': 'Date'}, inplace=True)

# %%

wbm = WetlandModel(
    stage_df=wl_hourly,
    Site_ID='3_638',
    source_dem_path='TBD'
)

wbm.calc_hcrit(
    method='hydrograph',
    plot=True, 
    stage_filter=0,
    evening_cut=23,
    morning_cut=5
)

# %%