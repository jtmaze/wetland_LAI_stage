# %% 1.0 Libraries and file paths

import pandas as pd

lai_summary_path = './data/wetland_lai_summary.csv'
wl_path = './data/waterlevel_offsets_tracked_Spring2025.csv'

lai = pd.read_csv(lai_summary_path)
lai_well_ids = lai['well_id'].unique()
wl = pd.read_csv(wl_path)
wl['Date'] = pd.to_datetime(wl['Date'])

# Aggregate hourly data to daily
wl_daily = wl.groupby([wl['Date'].dt.date, 'Site_ID']).agg({
    'revised_depth': 'mean',  # Mean water level for the day
    'flag': 'max',           # Preserve flags (if any day hour has flag, keep it)
    'notes': lambda x: ', '.join(x.dropna().unique()) if any(x.notna()) else None  # Combine notes
}).reset_index().rename(
    columns={'Site_ID': 'well_id'}
)

wl_daily['Date'] = pd.to_datetime(wl_daily['Date'])

wl_well_ids = wl_daily['well_id'].unique()

"""
Note, this code chunk is for mis-matched well_ids in LAI dataset
"""
unique_to_lai = set(lai_well_ids) - set(wl_well_ids)
unique_to_wl = set(wl_well_ids) - set(lai_well_ids)


# %% 2.0

def calculate_pti_stats(row, wl_df):
    """
    Calculate PTI statistics for a single row and return as a Series
    """
    well_id = row['well_id']
    change_dir = row['change_direction']
    # Still calculates water level change for wells with no observed LAI change date. 
    if pd.isna(change_dir):
        change_dt = pd.to_datetime(row['lai_split_date'])
    else:
        change_dt = pd.to_datetime(row['change_date'])
    
    
    # filter water level data for well
    wl_temp = wl_df[wl_df['well_id'] == well_id]
    
    if len(wl_temp) == 0:
        # Return NaN values if no water level data for well
        return pd.Series({
            'pre_observation_days': None,
            'pre_inundation_days': None,
            'post_observation_days': None,
            'post_inundation_days': None,
            'pre_pti': None,
            'post_pti': None
        })
    
    # Split into pre and post periods
    pre = wl_temp[wl_temp['Date'] < change_dt]
    post = wl_temp[wl_temp['Date'] > change_dt]
    
    # Calculate statistics
    pre_observation_days = len(pre)
    pre_inundation_days = len(pre[pre['revised_depth'] >= 0])
    post_observation_days = len(post)
    post_inundation_days = len(post[post['revised_depth'] >= 0])
    
    # Calculate PTI (Proportion Time Inundated)
    pre_pti = pre_inundation_days / pre_observation_days * 100 if pre_observation_days > 0 else None
    post_pti = post_inundation_days / post_observation_days * 100 if post_observation_days > 0 else None

    return pd.Series({
        'well_id': well_id,
        'pre_observation_days': pre_observation_days,
        'pre_inundation_days': pre_inundation_days,
        'post_observation_days': post_observation_days,
        'post_inundation_days': post_inundation_days,
        'pre_pti': pre_pti,
        'post_pti': post_pti,
    })

# %%

pti_stats = lai.apply(lambda row: calculate_pti_stats(row, wl_daily), axis=1)
lai = pd.merge(lai, pti_stats, how='left', on='well_id')

# %%
import matplotlib.pyplot as plt


# %%
