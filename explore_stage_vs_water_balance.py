# %% 1.0 Libraries and file paths
import pandas as pd
from scipy import stats
from scipy.stats import gaussian_kde
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

prism_path = './data/PRISM_water_balance.csv'
water_level_path = './data/waterlevel_offsets_tracked_Spring2025.csv'

# %% 2.0 Read the data

prism = pd.read_csv(prism_path)
prism['date'] = pd.to_datetime(prism['date'])
wl = pd.read_csv(water_level_path)
wl['Date'] = pd.to_datetime(wl['Date'])

# Aggregate hourly data to daily
# For water level, typically we use mean, max, or min depending on your needs
wl_daily = wl.groupby([wl['Date'].dt.date, 'Site_ID']).agg({
    'revised_depth': 'mean',  # Mean water level for the day
    'flag': 'max',           # Preserve flags (if any day hour has flag, keep it)
    'notes': lambda x: ', '.join(x.dropna().unique()) if any(x.notna()) else None  # Combine notes
}).reset_index()

# Convert Date back to datetime
wl_daily['Date'] = pd.to_datetime(wl_daily['Date'])

# %% 3.0 Filter for the site, clean merge with PRISM

site = '14_610'
clear_cut_date = pd.Timestamp('2024-01-30')
# Define water balance period as a variable
wb_period = '10d_cum_balance'  # Can be changed to '5d_cum_balance', '20d_cum_balance', etc.

test = wl_daily[wl_daily['Site_ID'] == site]
test = test[['Date', 'revised_depth', 'flag', 'notes']]
test = test.sort_values('Date')

# Create boolean column for pre/post logging
test['pre_logging'] = test['Date'] < clear_cut_date

# %% 4.0

plt.plot(test['Date'], test['revised_depth'])
plt.axvline(clear_cut_date, color='red', linestyle='--', label='Clear Cut')
plt.legend()
plt.ylabel('Stage (m)')
plt.title(f'Well {site} Hydrograph')
plt.xticks(rotation=45)  # Rotate x-ticks for better readability

# Get period number for display purposes
period_days = int(wb_period.split('d')[0])

pre_log = test[test['pre_logging']]
post_log = test[~test['pre_logging']]

test['above_ground'] = test['revised_depth'] >= 0

# %% 
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

# First subplot for stage data with KDE plots
# Calculate KDE for pre and post logging data
pre_kde = gaussian_kde(pre_log['revised_depth'].dropna())
post_kde = gaussian_kde(post_log['revised_depth'].dropna())

# Create x values for plotting
x_stage = np.linspace(min(pre_log['revised_depth'].min(), post_log['revised_depth'].min()),
                      max(pre_log['revised_depth'].max(), post_log['revised_depth'].max()),
                      1000)

# Plot KDE curves
ax1.plot(x_stage * 1000, pre_kde(x_stage), color='green', label='Pre-logging', linewidth=2)
ax1.plot(x_stage* 1000, post_kde(x_stage), color='tan', label='Post-logging', linewidth=2)
ax1.axvline(pre_log['revised_depth'].mean() * 1000, color='green', linestyle='--', linewidth=2, label=f'Pre mean: {pre_log["revised_depth"].mean()*1000:.3f}')
ax1.axvline(post_log['revised_depth'].mean() * 1000, color='tan', linestyle='--', linewidth=2, label=f'Post mean: {post_log["revised_depth"].mean()*1000:.3f}')
ax1.set_xlabel('Stage (mm)')
ax1.set_ylabel('Density')
ax1.set_title('Water Level Distribution')
ax1.legend()
ax1.grid(axis='y', linestyle='--', alpha=0.7)

# Second subplot for water balance data with KDE plots (will use the merged data later)
test_wb = pd.merge(test, prism, how='left', left_on='Date', right_on='date')
test_wb = test_wb[test_wb['flag'] == 0]
test_wb['5d_depth_change'] = test_wb['revised_depth'].diff(periods=5) / 5
pre_log_wb = test_wb[test_wb['pre_logging']]
post_log_wb = test_wb[~test_wb['pre_logging']]

pre_wb_kde = gaussian_kde(pre_log_wb[wb_period].dropna())
post_wb_kde = gaussian_kde(post_log_wb[wb_period].dropna())

x_wb = np.linspace(min(pre_log_wb[wb_period].min(), post_log_wb[wb_period].min()),
                   max(pre_log_wb[wb_period].max(), post_log_wb[wb_period].max()),
                   1000)

ax2.plot(x_wb, pre_wb_kde(x_wb), color='green', label='Pre-logging', linewidth=2)
ax2.plot(x_wb, post_wb_kde(x_wb), color='tan', label='Post-logging', linewidth=2)
ax2.axvline(pre_log_wb[wb_period].mean(), color='green', linestyle='--', linewidth=2, label=f'Pre mean: {pre_log_wb[wb_period].mean():.1f}')
ax2.axvline(post_log_wb[wb_period].mean(), color='tan', linestyle='--', linewidth=2, label=f'Post mean: {post_log_wb[wb_period].mean():.1f}')
ax2.set_xlabel(f'{period_days}-day Cumulative Water Balance (mm)')
ax2.set_ylabel('Density')
ax2.set_title('Climatic Water Balance (P-PET)')
ax2.legend()
ax2.grid(axis='y', linestyle='--', alpha=0.7)

plt.suptitle(f'Well {site} - Pre vs Post Logging Comparison')
plt.tight_layout()

# %%

f_stat, p_val = stats.f_oneway(pre_log['revised_depth'],
                               post_log['revised_depth'])

print('Stage ANOVA/Mann-Whitney Results')
print(f'ANOVA p-value: {p_val:.5f}')
u, p = stats.mannwhitneyu(pre_log['revised_depth'], post_log['revised_depth'], alternative='two-sided')
print(f"Mann–Whitney U p = {p:.5f}")


print('----------------------------------------------------')
f_stat, p_val = stats.f_oneway(pre_log_wb[wb_period],
                               post_log_wb[wb_period])

print(f'{period_days}-day Climate Water Balance ANOVA/Mann-Whitney Results')
print(f'ANOVA p-value: {p_val:.5f}')
u, p = stats.mannwhitneyu(pre_log_wb[wb_period], post_log_wb[wb_period], alternative='two-sided')
print(f"Mann–Whitney U p = {p:.5f}")


# %%

plt.figure(figsize=(7, 7))
#test_wb_below = test_wb[~test_wb['above_ground']]
# Separate the data based on logging period
test_wb_below = test_wb.copy()
pre_data = test_wb_below[test_wb_below['pre_logging']]
post_data = test_wb_below[~test_wb_below['pre_logging']]

# Plot each group separately with a label for the legend
plt.scatter(
    x=pre_data['10d_cum_balance'], 
    y=pre_data['revised_depth'], 
    color='red', 
    alpha=0.8,
    s=2,
    label='Pre-logging'
)
plt.scatter(
    x=post_data['10d_cum_balance'], 
    y=post_data['revised_depth'], 
    color='blue', 
    alpha=0.8,
    s=2,
    label='Post-logging'
)

plt.xlabel('10-day Cumulative Water Balance (mm)')
plt.ylabel('Stage (meters)')
#plt.ylim(-0.005, 0.005)
plt.legend()

# %%



# %%
