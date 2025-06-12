#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Libraries & File Paths -------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

library(readxl)
library(dplyr)
library(tidyr)
library(ggplot2)
library(lubridate)

lai_path <- './data/LAI_wetlands.xlsx'

df <- read_excel(lai_path, sheet=2) %>% 
  fill(Year)

long_df <- df %>% 
  pivot_longer(-c(Year, Wetland),
                names_to='Month',
                values_to='LAI')

rm(df)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Plot LAI timseries for each wetlands -------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
results = []

for (i in 0:51) {
  temp <- long_df %>% 
    filter(Wetland == i, !is.na(LAI)) %>%
    mutate(
      # Convert Month from abbreviation to number
      month_num = match(Month, month.abb),
      # Create Date object (first day of each month)
      date = make_date(Year, month_num, 1)
    )
  
  # Plot
  p <- ggplot(temp, aes(x=date, y=LAI)) +
    geom_line(color="red") +
    geom_point(color="maroon", size=4) +
    labs(
      title=paste("Wetland", i, "- LAI Timeseries"),
      x="Date", y="LAI"
    ) +
    theme_bw()
  
  early <- temp %>% filter(date <= '')
  
  print(p)
  
}

