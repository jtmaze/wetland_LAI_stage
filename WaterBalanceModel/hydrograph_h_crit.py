import pandas as pd
import numpy as np

from scipy.stats import linregress
import matplotlib.pyplot as plt

def calc_wetland_hcrit(
    Site_ID: str,
    wetland_hydrograph: pd.DataFrame,
    plot_hydrograph: bool,
    plot_stage_recession: bool
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

    evening_cut = 15
    morning_cut = 11
    # Take above-ground night-time data to calculate recession rate
    clean = wetland_hydrograph[wetland_hydrograph['water_level'] >= 0.05]
    night_mask = (clean['Date'].dt.hour >= evening_cut) | (clean['Date'].dt.hour <= morning_cut)
    clean = clean[night_mask]

    days = clean['Date'].dt.strftime('%Y-%m-%d').unique()

    # Empty df to store results
    results_df = pd.DataFrame(
        columns=['Date', 'next_date', 'slope']
    )

    for i in range(len(days) - 1):  # Fixed: use range() and subtract 1 to avoid index error
        
        day = pd.to_datetime(days[i])
        next_day = pd.to_datetime(days[i + 1])

        evening = clean[
            (clean['Date'].dt.date == day.date()) & 
            (clean['Date'].dt.hour >= evening_cut)
        ]
        
        morning = clean[
            (clean['Date'].dt.date == next_day.date()) &  
            (clean['Date'].dt.hour <= morning_cut)
        ]
        
        combined = pd.concat([evening, morning])['water_level'].reset_index(drop=True)
        x_indices = range(len(combined))
        hour_labels = np.concatenate([
                np.arange(evening_cut, 24), 
                np.arange(0, morning_cut + 1)  
            ])

        if i % 10_000_000 == 0 and len(combined) > 0:

            plt.figure(figsize=(8, 5))
            plt.plot(x_indices, combined, 'o', color='black', alpha=0.7)

            z = np.polyfit(x_indices, combined, 1)
            p = np.poly1d(z)
            plt.plot(x_indices, p(x_indices), '-', color='red', linewidth=2)

            if len(x_indices) >= len(hour_labels):
                step = len(x_indices) // len(hour_labels)
                if step == 0:
                    step = 1
                tick_positions = x_indices[::step]
                tick_labels = [f"{h:02d}:00" for h in hour_labels]
            else:
                # If we have fewer data points, just use all of them
                tick_positions = list(x_indices)
                # Create a subset of hour labels to match data points
                label_step = len(hour_labels) // len(x_indices) if len(x_indices) > 0 else 1
                if label_step == 0:
                    label_step = 1
                tick_labels = [f"{hour_labels[i]:02d}:00" for i in range(0, len(hour_labels), label_step)][:len(x_indices)]

            plt.xticks(tick_positions, tick_labels, rotation=45, ha='right')

            plt.title(f'Night-time Water Level - Day {day} to {next_day}')
            plt.xlabel('Time (Hours)')
            plt.ylabel('Water Level (meters)')
            plt.grid(True)
            plt.show()

        # Make a linear fit to estimate night-time recession m/hr
        if len(combined) == len(hour_labels) and len(combined) >= 2:
            result = linregress(
                x_indices,
                combined
            )
            slope = result.slope
        else:
            slope = None

        results_df = pd.concat([
            results_df,
            pd.DataFrame({
                'Date': [day.strftime('%Y-%m-%d')],
                'next_date': [next_day.strftime('%Y-%m-%d')],
                'slope': [slope],
            })
        ], ignore_index=True)


    results_df['Date'] = pd.to_datetime(results_df['Date']).dt.date

    daily_wl = wetland_hydrograph.groupby(wetland_hydrograph['Date'].dt.date).agg(
        {'water_level': 'mean'}
    ).reset_index()
    print(len(daily_wl))
    daily_wl = pd.merge(daily_wl, results_df, on='Date', how='left')

    print(daily_wl.head(10))
    # NOTE: Filtering slopes >= 0
    daily_wl = daily_wl[daily_wl['slope'] < 0]

    print(daily_wl.head(10))
    if plot_stage_recession:
        plt.figure(figsize=(10, 6))
        plt.scatter(
            daily_wl['water_level'], 
            daily_wl['slope'],
            alpha=0.7,
            edgecolor='k',
            s=50
        )
        plt.xlabel('Daily Mean Water Level (meters)')
        plt.ylabel('Night-time Water Level Recession Rate (m/hr)')

        
        
