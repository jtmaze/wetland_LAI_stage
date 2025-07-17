# %% Libraries and File Paths

import os
import pandas as pd

from WaterBalanceModel.wetland_model import WetlandModel

main_dir = 'D:/wetland_LAI_stage/'
os.chdir(main_dir)

wl_path = './data/20170918_20190422_output.csv'
wl = pd.read_csv(wl_path)
print(wl.columns)

# %%

wl = wl.rename(
    columns={'Timestamp': 'Date',
             'Flag': 'flag',
             'waterLevel': 'water_level',
             'Site_Name': 'Site_ID'}
)

wl['flag'] = 0

# %%
#wl = wl.rename(columns={'revised_depth': 'water_level'})
wl['Date'] = pd.to_datetime(wl['Date'])

# %%

wl['hour'] = wl['Date'].dt.floor('h')

wl_hourly = wl.groupby(['hour', 'Site_ID']).agg(
    {'water_level': 'mean',
     'flag': 'sum'}
).reset_index()

wl_hourly.rename(columns={'hour': 'Date'}, inplace=True)

# Is upland ET and hydro gradients still causing night-time recession
# to be high at low water. 
wl_hourly_low_ET = wl_hourly[
    wl_hourly['Date'].dt.month.isin([10, 11, 12, 1, 2, 3])
]

# %%

wbm = WetlandModel(
    stage_df=wl_hourly,
    Site_ID='TI Wetland Well Shallow',
    source_dem_path='TBD'
)

wbm.calc_hcrit(
    method='hydrograph',
    plot=True, 
    stage_filter=0.15,
    evening_cut=21,
    morning_cut=8
)

# %%
