# %%

import os
import pandas as pd

from WaterBalanceModel.wetland_model import WetlandModel

main_dir = 'D:/wetland_LAI_stage/'
os.chdir(main_dir)

wl_path = './data/waterlevel_offsets_tracked_Spring2025.csv'
wl = pd.read_csv(wl_path)

# %%
wl = wl.rename(columns={'revised_depth': 'water_level'})
wl['Date'] = pd.to_datetime(wl['Date'])

# %%

wbm = WetlandModel(
    stage_df=wl,
    Site_ID='6_93',
    source_dem_path='TBD'
)

wbm.calc_hcrit(
    method='hydrograph',
    plot=True
)
# %%
