# %% 1.0 Libraries and file paths

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

prism_path = './data/PRISM_timeseries_Bradford.csv'
prism = pd.read_csv(prism_path).drop(columns=['system:index', '.geo'])
prism['date'] = pd.to_datetime(prism['date'])

# %% 2.0 Calculate extraterrestrial radiation with FAO-56 method

# 2.0 Calculate extraterrestrial radiation with FAO-56 method

# Constants
Gsc = 0.0820  # Solar constant (MJ/m²/min)
lat_deg = 29.94  # Latitude in degrees
phi = np.radians(lat_deg)  # Convert to radians

# 2.1 Calculate Julian day (day of year)
prism['julian_day'] = prism['date'].dt.dayofyear

# 2.2-2.5 Calculate solar parameters
prism['delta'] = 0.409 * np.sin(2 * np.pi / 365 * prism['julian_day'] - 1.39)  # Solar declination
prism['omega_s'] = np.arccos(-np.tan(phi) * np.tan(prism['delta']))  # Sunset hour angle
prism['dr'] = 1 + 0.33 * np.cos(2 * np.pi / 365 * prism['julian_day'])  # Inverse relative Earth-Sun distance

# 2.6 Calculate extraterrestrial radiation (Ra) in MJ/m²/day
prism['Ra'] = (
    (24 * 60 / np.pi) * Gsc * prism['dr'] * (
        prism['omega_s'] * np.sin(phi) * np.sin(prism['delta']) + 
        np.cos(phi) * np.cos(prism['delta']) * np.sin(prism['omega_s'])
    )
)

# %% 3.0 Calculate the PET with Hargreaves Method

k = 0.0023 # Vegitation-specific coefficient
k = 0.0023 * 0.4

prism['pet'] = (
    k * prism['Ra'] * (prism['temp'] + 17.8) * 
    (prism['temp_max'] - prism['temp_min'])**0.5
)

prism.drop(columns=['temp_max', 'temp_min', 'delta', 'omega_s', 'dr', 'Ra'], inplace=True)

del k, Gsc, lat_deg, phi, 

# plt.plot(prism['date'], prism['pet'])
# plt.xlabel('Date')
# plt.ylabel('PET (mm)')
# plt.title('Hargreaves PET (all years)')
# plt.show()

# temp = prism[(prism['date'] >= pd.to_datetime('2022-10-01')) & 
#             (prism['date'] < pd.to_datetime('2023-10-01'))]

# plt.plot(temp['date'], temp['pet'])
# plt.xlabel('Date')
# plt.ylabel('PET (mm)')
# plt.title('Hargreaves PET WY 2022')
# plt.show()

# %% 4.0 Calculate mean and cumulative PET and precip

# PET rolling calculations
prism['5d_mean_pet'] = prism['pet'].rolling(window=5, center=False, closed='both').mean()
prism['5d_cum_pet'] = prism['pet'].rolling(window=5, center=False, closed='both').sum()
prism['10d_mean_pet'] = prism['pet'].rolling(window=10, center=False, closed='both').mean()
prism['10d_cum_pet'] = prism['pet'].rolling(window=10, center=False, closed='both').sum()
prism['20d_mean_pet'] = prism['pet'].rolling(window=20, center=False, closed='both').mean()
prism['20d_cum_pet'] = prism['pet'].rolling(window=20, center=False, closed='both').sum()

# Precip rolling calculations
prism['5d_mean_precip'] = prism['precip'].rolling(window=5, center=False, closed='both').mean()
prism['5d_cum_precip'] = prism['precip'].rolling(window=5, center=False, closed='both').sum()
prism['10d_mean_precip'] = prism['precip'].rolling(window=10, center=False, closed='both').mean()
prism['10d_cum_precip'] = prism['precip'].rolling(window=10, center=False, closed='both').sum()
prism['20d_mean_precip'] = prism['precip'].rolling(window=20, center=False, closed='both').mean()
prism['20d_cum_precip'] = prism['precip'].rolling(window=20, center=False, closed='both').sum()

# Test plot to look at variability based on window sizes.

# early = pd.to_datetime('2023-07-01')
# late = pd.to_datetime('2023-12-31')

# temp = prism[(prism['date'] >= early) &
#              (prism['date'] <= late)]

# plt.plot(temp['date'], temp['5d_mean_pet'], color='blue', label='5-day mean PET')
# plt.plot(temp['date'], temp['10d_mean_pet'], color='orange', label='10-day mean PET')
# plt.plot(temp['date'], temp['20d_mean_pet'], color='red', label='20-day mean PET')
# plt.legend()
# plt.show()

# plt.plot(temp['date'], temp['5d_mean_precip'], color='blue', label='5-day mean precip')
# plt.plot(temp['date'], temp['10d_mean_precip'], color='orange', label='10-day mean precip')
# plt.plot(temp['date'], temp['20d_mean_precip'], color='red', label='20-day mean precip')
# plt.legend()
# plt.show()

# %% 5.0 Calculate cummulative water balances

prism['5d_cum_balance'] = prism['5d_cum_precip'] - prism['5d_cum_pet']
prism['10d_cum_balance'] = prism['10d_cum_precip'] - prism['10d_cum_pet']
prism['20d_cum_balance'] = prism['20d_cum_precip'] - prism['20d_cum_pet']

plt.plot(prism['date'], prism['20d_cum_balance'], color='orange', label='20-day cummulative P-PET')
plt.plot(prism['date'], prism['20d_cum_precip'], color='blue', label='20-day cummulative P')
plt.plot(prism['date'], prism['20d_cum_pet'], color='red', label='20-day cummulative PET')
plt.axhline(0, color='grey', linestyle='--', linewidth=0.8, label='Zero Line')  # Add grey horizontal line at zero
plt.legend()
plt.ylabel('Cummulative value (mm)')
plt.show()
# %% 6.0 Write the PRISM data to csv

prism.to_csv('./data/PRISM_water_balance.csv', index=False)

# %%
