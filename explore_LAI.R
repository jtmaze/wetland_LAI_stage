#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Libraries & File Paths -------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

library(readxl)
library(dplyr)
library(tidyr)
library(ggplot2)
library(lubridate)
library(slider)

lai_path <- './data/LAI_Wetlands_Update.xlsx'

df <- read_excel(lai_path, sheet=2) %>% 
  fill(Year)

long_df <- df %>% 
  pivot_longer(-c(Year, Wetland, well_id),
                names_to='Month',
                values_to='LAI')

# NOTE: Crudely removing anomalously high LAI values
long_df$LAI[long_df$LAI > 5.5] <- NA_real_
#long_df$LAI[long_df$LAI < 0.2] <- NA_real_

rm(df)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Plot LAI timse series for each wetlands -------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

for (i in 0:51) {
  temp <- long_df %>% 
    filter(Wetland == i) %>%
    mutate(
      # Convert Month from abbreviation to number
      month_num = match(Month, month.abb),
      # Create Date object (first day of each month)
      date = make_date(Year, month_num, 1)
    )
  
  well_id <- unique(temp$well_id) # Grab the well_id, should only be one
  
  temp <- temp %>%
    mutate(
      roll5 = slide_dbl(
        .x = LAI,
        .f = ~mean(.x, na.rm = TRUE),
        .before = 2,
        .after = 2,
        .complete = FALSE # Always compute, even if insufficient rows
      ),
      roll9 = slide_dbl(
        .x = LAI,
        .f = ~mean(.x, na.rm = TRUE),
        .before = 4,
        .after = 4,
        .complete = FALSE
      ),
      roll_yr = slide_dbl(
        .x = LAI, 
        .f = ~mean(.x, na.rm = TRUE),
        .before = 6,
        .after = 5, 
        .complete = FALSE
      )
    )
  
  temp <- temp %>% 
    filter(date < '2025-05-02')
#   
#   # Plot
  p <- ggplot(temp, aes(x=date)) +
    geom_point(aes(y = LAI, color="LAI")) +
    geom_line(aes(y = roll5, color="5-month")) + 
    geom_line(aes(y = roll9, color="9-month")) +
    geom_line(aes(y = roll_yr, color="1-year")) +
    scale_color_manual(
      name = NULL, 
      values = c('LAI' = 'red', '5-month' = 'blue', '9-month' = 'green', '1-year' = 'orange')
    ) +
    labs(
      title=paste("Wetland", i, "ID:", well_id, "- LAI Timeseries"),
      x="Date", y="LAI"
    ) +
    theme_bw()
#   
#   early <- temp %>% filter(date <= '')
#   
   print(p)
#   
}

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Calculate LAI change based on visually determined observation dates-------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

