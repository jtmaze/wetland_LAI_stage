import pandas as pd
import geopandas as gpd
import numpy as np

from hydrograph_h_crit import calc_wetland_hcrit


class WetlandModel:
    """
    A class constructing a wetland-specific water balance model derived from
    Klammler et al 2020's https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2020WR027581
    reduced complexity model. The key features are:
    1) ET is stage dependent
    2) Sy is also stage dependent
    3) Dischage is dependent on spill elevation
    """

    def __init__(self,
                 stage_df: pd.DataFrame,
                 wetland_basin_gdf: gpd.GeoDataFrame,
                 Site_ID: str,
                 source_dem_path: str):
        
        # Store as instance variable
        self.site_id = Site_ID
        self.wetland_basin = wetland_basin_gdf[wetland_basin_gdf['Site_ID'] == Site_ID]
        self.dem_path = source_dem_path

        stage = stage_df[stage_df['Site_ID'] == Site_ID]
        stage = stage[stage['Flag'] == 0] 
        self.stage = stage

    def calc_hcrit(
            self,
            method: str,
            plot: bool = True
    ):
        """
        Calculate the spill elevation (h_crit) for the wetland.
        
        Parameters:
            method: str - Method to use for calculation ('hydrograph' or other methods)
            plot: bool - Whether to display plots during calculation
        
        Returns:
            float: The calculated h_crit value
        """
        
        h_crit = None
        
        if method == "hydrograph":
            h_crit = calc_wetland_hcrit(
                Site_ID = self.site_id,
                wetland_hydrograph = self.stage,
                plot_hydrograph = plot
            )
        elif method == "dem":
            pass
        else: 
            raise ValueError(f"Unknown method: {method}. Available methods: 'hydrograph', 'custom'")
            

        self.h_crit = h_crit
        
        return h_crit