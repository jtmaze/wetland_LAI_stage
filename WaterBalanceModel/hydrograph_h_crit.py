import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def calc_wetland_hcrit(
    Site_ID: str,
    wetland_hydrograph: pd.DataFrame,
    plot_hydrograph: bool,
):  

    if plot_hydrograph:
        # Make a copy of the dataframe to avoid modifying the original
        plot_df = wetland_hydrograph.copy()

        fig, ax = plt.subplots(figsize=(10, 5))

        # plot the water level time series
        ax.plot(
            plot_df['Date'], 
            plot_df['water_level'], 
            color='tab:blue', 
            label='Water Level'
        )

        # set titles and labels
        ax.set_title(f"Hydrograph for {Site_ID}")
        ax.set_xlabel('Date')
        ax.set_ylabel('Water Level (meters)')

        # optional styling
        ax.legend()
        ax.grid(True)

        # adjust layout and show
        plt.tight_layout()
        plt.show()

    evening_cut = 20
    morning_cut = 9
    # Take above-ground night-time data to calculate recession rate
    clean = wetland_hydrograph[wetland_hydrograph['water_level'] >= 0.05]
    night_mask = (clean['Date'].dt.hour >= evening_cut) | (clean['Date'].dt.hour <= morning_cut)
    clean = clean[night_mask]

    days = clean['Date'].dt.strftime('%Y-%m-%d').unique()

    for i in range(len(days) - 1):  # Fixed: use range() and subtract 1 to avoid index error
        
        day = pd.to_datetime(days[i])
        next_day = pd.to_datetime(days[i + 1])

        evening = clean[
            (clean['Date'].dt.date == day.date()) & 
            (clean['Date'].dt.hour >= evening_cut)
        ]
        
        morning = clean[
            (clean['Date'].dt.date == next_day.date()) &  # Fixed: syntax error
            (clean['Date'].dt.hour <= morning_cut)
        ]
        
        combined = pd.concat([evening, morning])['water_level'].reset_index(drop=True)

        if i % 50 == 0 and len(combined) > 0:

            # Plot the water level from combined, where the index is just the observation points
            plt.figure(figsize=(8, 5))
            x = np.concatenate([
                np.arange(evening_cut, 24),
                np.arange(0, morning_cut)
            ])
            plt.plot(x, combined, 'o', color='black', alpha=0.7)
            
            # Add red trendline
            z = np.polyfit(range(len(combined)), combined, 1)
            p = np.poly1d(z)
            plt.plot(x, p(range(len(combined))), '-', color='red', linewidth=2)
            
            plt.title(f'Night-time Water Level - Day {day} to {next_day}')
            plt.xlabel('Observation Points')
            plt.ylabel('Water Level (meters)')
            plt.grid(True)
            plt.show()


