#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 1.0 Libraries & File Paths -------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
library(readxl)
library(dplyr)
library(tidyr)
library(ggplot2)
library(stringr)
library(lubridate)
library(slider)

lai_path <- './data/LAI_Wetlands_Update.xlsx'

df <- read_excel(lai_path, sheet=2) %>% 
  fill(Year)

long_df <- df %>% 
  pivot_longer(-c(Year, Wetland, well_id),
                names_to='Month',
                values_to='LAI')

# NOTE: Crudely removing anomalously high and low LAI values
long_df$LAI[long_df$LAI > 5.5] <- NA_real_
long_df$LAI[long_df$LAI < 0.2] <- NA_real_

long_df <- long_df %>%
  mutate(
    # Convert Month from abbreviation to number
    month_num = match(Month, month.abb),
    # Create Date object (first day of each month)
    date = make_date(Year, month_num, 1)
  )

rm(df)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 2.0 Visually determine LAI change date for each wetland -----------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# NOTE could implement algorithmic change detection later. 

for (i in 0:51) {
  temp <- long_df %>% 
    filter(Wetland == i)
  
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
# 3.0 Calculate LAI change based on visually determined observation dates-------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# 3.1 Data prep
# ----------------------------------------------------------------------

lai_change_path <- './data/LAI_change_dates.xlsx'
lai_change <- read_excel(lai_change_path)

# Reformat well_id column for join
long_df <- long_df %>% 
  mutate(well_id = str_replace_all(well_id, '-', '_'))

# Join the estimated change dates with main df. 
# Format
long_df <- long_df %>% 
  left_join(lai_change, by='well_id') %>% 
  mutate(
    date = make_date(Year, month_num, 1)
  )

unique_well_ids <- unique(long_df$well_id)

# 3.2 Change magnitude calculations
# ----------------------------------------------------------------------

well_summaries <- list()

for (i in unique_well_ids) {
  
  temp <- long_df %>% filter(well_id == i)
  change_direction <- unique(temp$change)
  change_str <- unique(temp$change_date)
  change_dt <- mdy(change_str)
  change_rate <- unique(temp$change_rate)
  
  if (change_str != 'None') {
    
    # Split the well's LAI data into pre and post logging
    # NOTE: Unsure whether LAI mean or moving average means are better?
    pre <- temp %>% filter(date < change_dt)
    pre_mean <- mean(pre$LAI, na.rm=TRUE)
    post <- temp %>% filter(date >= change_dt)
    post_mean <- mean(post$LAI, na.rm=TRUE)
  
  } else { # If there's not a clear change date, just grab the midpoint of timeseries
    
    begin_date <- temp %>% pull(date) %>% first()
    end_date <- temp %>% pull(date) %>% last()
    mid_date <- begin_date + as.integer((end_date - begin_date) / 2)
    
    pre_mean <- temp %>% 
      filter(date < mid_date) %>%
      pull(LAI) %>% 
      mean(na.rm=TRUE)
    post_mean <- temp %>% 
      filter(date >= mid_date) %>% 
      pull(LAI) %>% 
      mean(na.rm=TRUE)
  }
  
  lai_magnitude <- post_mean - pre_mean
  
  out <- data.frame(
    well_id=i,
    change_direction=change_direction,
    change_date=change_str,
    pre_lai=pre_mean,
    post_lai=post_mean,
    lai_magnitude=lai_magnitude,
    change_rate=change_rate
  )
  
  well_summaries[[length(well_summaries) + 1]] <- out
  
}

summary_df <- bind_rows(well_summaries)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 4.0 Quick visualization and write export --------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ggplot(summary_df, aes(x = lai_magnitude, fill=change_direction)) +
  geom_histogram(bins = 20, color = "black") +
  labs(title = "Wetland LAI Change Magnitudes (colored by direction)") + 
  theme_bw() +
  theme(panel.grid = element_blank()) +
  labs(x = "Magnitude of logging change (Post-Pre LAI)")

write.csv(summary_df, './data/wetland_lai_summary.csv', row.names=FALSE)


