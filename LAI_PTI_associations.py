# %% 1.0 Libraries and file paths

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


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

# %%
print(len(wl_daily))
wl_daily = wl_daily[wl_daily['flag'] == 0]
print(len(wl_daily))

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

    pti_nominal_difference = post_pti - pre_pti
    pti_relative_difference = pti_nominal_difference / ((post_pti + pre_pti) * 0.5) * 100

    return pd.Series({
        'well_id': well_id,
        'pre_observation_days': pre_observation_days,
        'pre_inundation_days': pre_inundation_days,
        'post_observation_days': post_observation_days,
        'post_inundation_days': post_inundation_days,
        'pre_pti': pre_pti,
        'post_pti': post_pti,
        'pti_diff': pti_nominal_difference,
        'pti_relative_diff': pti_relative_difference
    })

# %%

pti_stats = lai.apply(lambda row: calculate_pti_stats(row, wl_daily), axis=1)
lai = pd.merge(lai, pti_stats, how='left', on='well_id')

# %%
lai_plot = lai[lai['well_id'] != '13_410'].copy()
lai_plot = lai_plot[
    (lai_plot['pre_inundation_days'].fillna(0) > 20) & (lai_plot['post_inundation_days'].fillna(0) > 20)
]

lai_plot['change_direction'] = lai_plot['change_direction'].fillna('No Change')
# Create a manual mapping for change_direction categories with specific colors
color_mapping = {'U': 'blue', 'No Change': 'green', 'D': 'red'}
colors = lai_plot['change_direction'].map(color_mapping)

# Create scatter plot using the assigned colors
scatter = plt.scatter(
    lai_plot['lai_magnitude'],
    lai_plot['pti_relative_diff'],
    c=colors
)

# Add well_id labels for clarity
for x, y, wid in zip(lai_plot['lai_magnitude'], lai_plot['pti_relative_diff'], lai_plot['well_id']):
    plt.text(x, y, str(wid), fontsize=8)

# Create custom legend using matplotlib patches
import matplotlib.patches as mpatches
legend_handles = [mpatches.Patch(color=color, label=label) for label, color in color_mapping.items()]

# Move legend completely off the grid (below the plot area)
plt.legend(handles=legend_handles, title="LAI Change", loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3)

plt.title('LAI change vs. change in PTI')
plt.xlabel('LAI Magnitude')
plt.ylabel('PTI Relative Difference (%)')

# %%
# Filter for decreasing LAI points
lai_plot = lai_plot[(lai_plot['change_direction'] == 'D') & (lai_plot['change_rate'] == 'rapid')]

# Create scatter plot
scatter = plt.scatter(
    lai_plot['lai_magnitude'],
    lai_plot['pti_relative_diff'],
    c='red'
)

# Calculate linear regression
x = lai_plot['lai_magnitude']
y = lai_plot['pti_relative_diff']
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

# Plot regression line
x_line = np.linspace(min(x), max(x), 100)
y_line = slope * x_line + intercept
plt.plot(x_line, y_line, 'k--')

# Add statistics to plot
stat_text = f'Slope: {slope:.2f}\nR²: {r_value**2:.2f}\np-value: {p_value:.4f}'
plt.text(0.75, 0.95, stat_text, transform=plt.gca().transAxes, 
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))

# Add point labels
for x, y, wid in zip(lai_plot['lai_magnitude'], lai_plot['pti_relative_diff'], lai_plot['well_id']):
    plt.text(x, y, str(wid), fontsize=8)

plt.title('LAI change vs. change in PTI (LAI Decrease Sites)')
plt.xlabel('LAI Magnitude')
plt.ylabel('PTI Relative Difference (%)')

# %%

"""
Potentially use proportion z-tests to determine significance of PTI increase.
"""