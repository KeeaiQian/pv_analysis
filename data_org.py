# -*- coding: utf-8 -*-
"""
Created on Mon Sep 14 13:41:24 2020

@author: QIAN XINYUE
"""


import pandas as pd
import numpy as np


def irr_clearsky(timestamp, lat, lon, tz, alt):
    from pvlib.location import Location
    
    timestamp = pd.to_datetime(timestamp, format='%Y/%m/%d %H:%M')
    loc = Location(lat, lon, tz=tz, altitude=alt)
    time_local = timestamp.dt.tz_localize(tz)
    time_local.index = pd.to_datetime(time_local)
    csky = loc.get_clearsky(time_local.index)
    csky.reset_index(drop=True, inplace=True)
    
    colNameDict1 = {'ghi':'ghi_clearsky', 'dhi':'dhi_clearsky', 
                    'dni':'dni_clearsky'}
    csky.rename(columns=colNameDict1, inplace=True)
    return csky


def g_extra(doy, sun_zenith):
    import math
    da = (2 * math.pi / 365) * (doy - 1)
    re = 1.000110 + 0.034221*np.cos(np.array(da)) + 0.001280*np.sin(np.array(da)) + 0.00719*np.cos(2*np.array(da)) + 0.000077*np.sin(2*np.array(da))
    g_extra = np.round(1361.1 * re * np.cos(np.radians(np.array(sun_zenith))), 2)
    g_extra = pd.Series(g_extra)
    g_extra[sun_zenith>=90] = 0
    return g_extra
    

def engerer2(ghi, lon, g_extra, ghi_clearsky, timestamp, sun_zenith, equation_of_time):
    eng = pd.DataFrame()
    eng['kt'] = ghi / g_extra 
    eng['ktc'] = ghi_clearsky / g_extra
    eng['delta_ktc'] = eng['ktc'] - eng['kt']
    
    #calculate apparent solar time
    timestamp = pd.to_datetime(timestamp, format='%Y/%m/%d %H:%M')
    decimal_time = pd.Series(index=timestamp.index)
    for j in timestamp.index:
        decimal_time[j] = timestamp[j].hour + timestamp[j].minute / 60   
    lsn = 12 - lon / 15 - 1 * (equation_of_time / 60)
    hour_angle = (decimal_time - lsn) * 15
    hour_angle[hour_angle>=180] = hour_angle[hour_angle>=180] - 360
    hour_angle[hour_angle<=-180] = hour_angle[hour_angle<=-180] + 360
    eng['ast'] = hour_angle / 15 + 12
    eng.loc[eng.ast<0,'ast'] = abs(eng.loc[eng.ast<0,'ast'])
    
    eng['kde'] = 1 - ghi_clearsky / ghi
    eng.loc[eng.kde<0,'kde'] = 0
    
    #engerer2
    k = 0.09394 + (1-0.09394) / (1 + np.exp(np.array(-4.5771 + 8.4641*eng['kt'] + 0.01001*eng['ast'] + 0.003975*sun_zenith - 4.3921*eng['delta_ktc']))) + np.array(0.3933*eng['kde'])
    k[k>1] = 1
    return pd.Series(k)


def poaCal(ghi, k, sun_zenith, doy, tilt, azimuth, sun_azimuth):
    import pvlib
    from pvlib.tools import cosd
    
    dhi_est = pd.Series(k * ghi)
    dni_est = pd.Series((ghi - dhi_est) / cosd(sun_zenith))
    dni_extra = pvlib.irradiance.get_extra_radiation(doy, method='asce')
    
    airmass_relative = pvlib.atmosphere.get_relative_airmass(sun_zenith, model='kastenyoung1989')
    aoi = pvlib.irradiance.aoi(tilt, azimuth, sun_zenith, sun_azimuth)
    poa_sky_diffuse = pvlib.irradiance.perez(tilt, azimuth, dhi_est, dni_est, 
                                             dni_extra, sun_zenith, sun_azimuth, 
                                             airmass_relative)
    poa_ground_diffuse = pvlib.irradiance.get_ground_diffuse(tilt, ghi)
    poa = np.abs(cosd(aoi)) * dni_est + poa_sky_diffuse + poa_ground_diffuse
    poa[poa<=0] = 0.001
    return poa


def VoltageRatio(DC_voltage, Voc, poa, Tmod, Ns, tempCoeff=-0.03, n=1):
    k = 1.381 * 10 ** (-23)
    q = 1.6 * 10 ** (-19)
    vratio1 = DC_voltage / Voc
    Gpoa = np.array(poa)
    vratio2 = DC_voltage / (Voc + Voc*tempCoeff*(Tmod-25) + k*Tmod*Ns*n/q*np.log(Gpoa/1000))    
    result = pd.DataFrame(columns=['voltage_ratio_stc', 'voltage_ratio_expected'])
    result['voltage_ratio_stc'] = vratio1
    result['voltage_ratio_expected'] = vratio2
    return result


def CurrentRatio(DC_current, Isc, poa, Tmod, tempCoeff=0.0005):
    iratio1 = DC_current / Isc
    iratio2 = DC_current / (poa/1000*(Isc+Isc*tempCoeff*(Tmod-25)))    
    result = pd.DataFrame(columns=['current_ratio_stc', 'current_ratio_expected'])
    result['current_ratio_stc'] = iratio1
    result['current_ratio_expected'] = iratio2
    return result