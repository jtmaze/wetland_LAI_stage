# %% 1.0 Libraries and file paths
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

prism_path = './data/PRISM_water_balance.csv'
water_level_path = './data/waterlevel_offsets_tracked_Spring2025.csv'

# %% 2.0

prism = pd.read_csv(prism_path)
prism['date'] = pd.to_datetime(prism['date'], utc=True)
wl = pd.read_csv(water_level_path)
wl['Date'] = pd.to_datetime(wl['Date'])

# %% 3.0

site = '14_610'

test = wl[wl['Site_ID'] == site]
test = test[['Date', 'revised_depth', 'flag', 'notes']]
test = test.sort_values('Date')

# %% 4.0

plt.plot(test['Date'], test['revised_depth'])
plt.axvline(pd.Timestamp('2024-01-30'), color='red', linestyle='--', label='Clear Cut')
plt.legend()
plt.ylabel('Stage (m)')
plt.title(f'Well {site} Hydrograph')
plt.xticks(rotation=45)  # Rotate x-ticks for better readability

# Boxplot with identical dimensions
cutoff_date = pd.to_datetime('2023-07-21', utc=True)
# Create boolean column for pre/post logging
test['pre_logging'] = test['Date'] < cutoff_date
pre_log = test[test['pre_logging']]
post_log = test[~test['pre_logging']]

test['above_ground'] = test['revised_depth'] >= 0

# Create a new figure for the boxplot
plt.figure(figsize=(8, 6))
boxdata = [pre_log['revised_depth'], post_log['revised_depth']]
plt.boxplot(boxdata, labels=[f'Pre-logging', 'Post-logging'])
plt.ylabel('Stage (m)')
plt.title(f'Well {site} Water Level - Pre vs Post Logging')
plt.grid(axis='y', linestyle='--', alpha=0.7)


# %%

test_wb = pd.merge(test, prism, how='left', left_on='Date', right_on='date')
test_wb = test_wb[test_wb['flag'] == 0]
test_wb['5d_depth_change'] = test_wb['revised_depth'].diff(periods=5) / 5
print(test_wb.columns)

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
