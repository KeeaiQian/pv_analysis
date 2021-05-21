Package 'pvanalysis'

When using this package, make sure that all series correspond to the same series of timestamp and are sorted by time.
Also make sure that the index of all input series are from 0 to len-1. 

pvanalysis
    |--__init__.py
    |--data_org.py
        |--irr_clearsky
        |--g_extra
        |--engerer2
        |--poaCal
        |--VoltageRatio
        |--CurrentRatio
    |--filters.py
        |--pearson_rolling
        |--ratio_smoothness
        |--fod
        |--daily
        |--stratified_daily
        |--dw_rolling
        |--butter_lowpass_filter

data_org.irr_clearsky
Description
    Calculate clear sky irrdiance.
Input
    irr_clearsky(timestamp, lat, lon, tz, alt)
Output
    dataset containing 3 columns: 'ghi_clearsky', 'dhi_clearsky', 'dni_clearsky' corresponding to the time points in timestamp

data_org.g_extra
Description
    Calculate extraterrestrial irradiance.
Input
    g_extra(doy, sun_zenith)  #doy for 'day of year'
Output
    a series of extraterrestrial irradiance corresponding to the days in doy

data_org.engerer2
Description
    Engerer2 decomposition model for calculating diffuse fraction.
Input
    engerer2(ghi, lon, g_extra, ghi_clearky, timestamp, sun_zenith, equation_of_time)  
    #sun_zenith and equation_of_time can be obtained from pvlib.solarposition.get_solarposition() function
Output
    a series of diffuse fraction corresponding to the time points in timestamp

data_org.poaCal
Description
    Perez model for calculating POA irradiance from GHI with diffuse fraction.
Input
    poaCal(ghi, k, sun_zenith, doy, tilt, azimuth, sun_azimuth)
Output
    a series of POA readings corresponding to the imput GHI readings

data_org.VoltageRatio
Description
    Calculate voltage ratio.
Input
    VoltageRatio(DC_voltage, Voc, poa, Tmod, Ns, tempCoeff=-0.03, n=1)  
    #Ns=cellPerModule*moduleNum
Output
    dataset containing 2 columns: 'voltage_ratio_stc' and 'voltage_ratio_expected', corresponding to the voltage measurements in DC_voltage

data_org.CurrentRatio
Description
    Calculate current ratio.
Input
    CurrentRatio(DC_current, Isc, poa, Tmod, tempCoeff=0.0005)
Output
    dataset containing 2 columns: 'current_ratio_stc' and 'current_ratio_expected', corresponding to the current measurements in DC_current

filters.pearson_rolling
Description
    Pearson sliding window algorithm.
Input
    pearson_rolling(x, y, w=12)  
    #w for window size, x should be a series, x & y should have no null values
Output
    dataset containing 2 columns: 'corr' and 'corr_rolling', 'corr' is the value for one window only, 'corr_rolling' is the average of top 1/6-1/3 from all windows     
    here, 'corr' corresponds to the pearson correlation coefficient of the window that ends with each data point in x & y

filters.ratio_smoothness
Description
    Find datapoints with stable Iratio/PR for a period of time.
Input
    ratio_smoothness(timestamp, irr, ratio, threshold=0.15, continu=4)  
    #timestamp, irr and ratio are 3 series with same legnth
Output
    a series of Boolean value indicating whether a datapoint is in a stable time period 

filters.fod
Decription
    Use first order difference filter to determine abnormal datapoints.
Input
    fod(poa, DC_current, isc, t_low=0.025, t_high=0.03, sep=50)  
    #t_low and t_high are thresholds, t_low for poa_fod<sep and t_high for poa_fod>=sep
Output
    a series of Boolean value indicating whether a datapoint is normal

filters.daily
Description
    Calculate daily weighted mean (weighted on poa) and (default) 70% quantile for a certain parameter.
    Also, determines whether each day is a clear sky day or overcast day.
Input
    daily(poa, timestamp, x, is_clear_sky=None, quantile=0.7, clear_sky=10, overcast=150)
    #if a day has more than (clear_sky) datapoints marked as 'clear sky', then that day is considered as a clear sky day
    #if a the mean POA irradiance for a day is lower than (overcast), it is regarded as an overcast day
Output
    a dataframe containing columns 'year', 'month', 'day', 'quantile', 'weighted mean', 'clearsky', 'overcast', 'count'
    'count' shows how many datapoints there are in the input for each day

filters.strtified_daily
Description
    Calculate daily (default) 70% quantile for a certain parameter for different irradiance levels.
Input
    stratified_daily(poa, timestamp, x, quantile=0.7, min_dp_num=10)
    #min_dp_num means that only when there are more datapoints than this number in one day for one irradiance level, the 70% quantile will be calculated
Output
    a dataframe containing 'year', 'month', 'day', 'c1', 'c2', 'c3', 'c4'
    'c1', 'c2', 'c3', 'c4' corresponds to the daily quantile for irradiance levels 'poa>800', '600<poa<800', '400<poa<600' and '200<poa<400'

filters.dw_rolling
Description
    Sliding Window Durbin Watson statistic.
Input
    dw_rolling(x, y, w=12)  
    #w for window size, x should be a series, x & y should have no null values
Output
    dataset containing 2 columns: 'dw' and 'dw_rolling', 'dw' is the value for one window only, 'dw_rolling' is the average of top 1/6-1/3 from all windows     
    here, 'dw' corresponds to the DW statstic of the window that ends with each data point in x & y

filters.butter_lowpass_filter
Description
    Low pass filter for smoothing data.
Input
    butter_lowpass_filter(data, cutoff, fs, order)  
    #fs for the sampling frequency of the digital system.
    #data is in numpy,array form
Output
    Smoothed data in array form.

























































