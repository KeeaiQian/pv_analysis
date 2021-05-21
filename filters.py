# -*- coding: utf-8 -*-
"""
Created on Tue Jul 21 14:50:47 2020

@author: QIAN XINYUE
"""


import pandas as pd
import numpy as np


#pearson sliding window

def pearson_rolling(x, y, w=12):
    from scipy.stats import pearsonr
    
    corr = pd.DataFrame(index=x.index, columns=['corr', 'corr_rolling'])
    for i in range(w-1,len(x)):
        cx = x[np.array(range(i-w+1,i+1))]
        cy = y[np.array(range(i-w+1,i+1))]
        r = pearsonr(cx, cy)[0]
        corr.loc[i,'corr'] = r
    
    for i in range(w-1, len(x)-w+1):
        clist = corr.loc[range(i,i+w),'corr'].tolist()
        clist.sort(reverse=True)
        corr.loc[i,'corr_rolling'] = sum(clist[(int(w/6)-1):(int(w/3)+1)]) / (int(w/3)-int(w/6)+2)
    return corr


#ratio smoothness filter
    
def ratio_smoothness(timestamp, irr, ratio, threshold=0.15, continu=4):
    import datetime
    timestamp = pd.to_datetime(timestamp, format='%Y/%m/%d %H:%M')
    
    fluc = pd.Series(False, index=irr.index)
    fluc[range(1,len(irr))] = abs(ratio.diff())>threshold
    
    count = pd.Series(0, index=irr.index)
    cont = pd.Series(False, index=irr.index)
    for i in range(1,len(irr)):
        if (fluc[i] == True) | (timestamp[i] - timestamp[i-1] !=datetime.timedelta(minutes=5)):
            count[i] = 0
        else:
            count[i] = count[i-1] + 1
        if (count[i] == continu):
            cont[np.array(range(i-continu+1,i+1))] = True
        elif (count[i] > continu):
            cont[i] = True
    return cont


#first order difference filter
    
def fod(poa, DC_current, isc, t_low=0.025, t_high=0.03, sep=50):
    fod = pd.Series(index=poa.index)
    fod[range(1,len(poa))] = poa.diff()
    cur_fod = pd.Series(index=poa.index)
    cur_fod[range(1,len(poa))] = DC_current.diff()
    
    diff = abs(cur_fod / isc - fod / 1000 * 0.9)
    include = pd.Series(index=poa.index)
    include[fod<sep] = diff[fod<50]<t_low
    include[fod>=sep] = diff[fod>=50]<t_high
    return include


#calculating daily mean & 70% percentile

def daily(poa, timestamp, x, is_clear_sky=None, quantile=0.7, min_day=10, clear_sky=10, overcast=150):
    timestamp = pd.to_datetime(timestamp, format='%Y/%m/%d %H:%M')
    days = pd.DataFrame(columns=['year', 'day'])
    days['year'] = timestamp.dt.year
    days['month'] = timestamp.dt.month
    days['day'] = timestamp.dt.day
    daydata = days.drop_duplicates()
    daydata.reset_index(drop=True, inplace=True)
    days['totday'] = timestamp.dt.dayofyear   
    days['poa'] = poa
    days['x'] = x
    days['product'] = days['poa'] * days['x']   
    
    daydata[str(quantile*100)+'%quantile'] = days.groupby(by=['year','totday'])['x'].quantile(quantile).reset_index(drop=True)
    a = days.groupby(by=['year','totday'])['poa','product'].sum().reset_index(drop=True)
    daydata['mean_weitd'] = a['product'] / a['poa']
    if str(type(is_clear_sky))!="<class 'NoneType'>":
        days['is_clear_sky'] = is_clear_sky+0
        daydata['clearsky'] = (days.groupby(by=['year','totday'])['is_clear_sky'].sum()>clear_sky).reset_index(drop=True)
    daydata['overcast'] = (days.groupby(by=['year','totday'])['poa'].mean()<overcast).reset_index(drop=True)
    daydata['count'] = days.groupby(by=['year','totday'])['day'].count().reset_index(drop=True)
    return daydata


#daily 70% quantile for each irradiance level

def stratified_daily(poa, timestamp, x, quantile=0.7, min_dp_num=10):
    timestamp = pd.to_datetime(timestamp, format='%Y/%m/%d %H:%M')
    days = pd.DataFrame(columns=['year', 'day'])
    days['year'] = timestamp.dt.year
    days['month'] = timestamp.dt.month
    days['day'] = timestamp.dt.day
    days['totday'] = timestamp.dt.dayofyear + (days['year']-2019)*366
    daydata = days.drop_duplicates()
    daydata.reset_index(drop=True, inplace=True)   
    days['poa'] = poa
    days['x'] = x
        
    for i in days.totday.unique():
        cdata = days[days.totday==i]
        cdata = cdata.reset_index(drop=True)
        totday = cdata.loc[0,'totday']
        if (len(cdata[cdata.poa>800]) > min_dp_num):
            cd= cdata[cdata.poa>800]
            daydata.loc[daydata.totday==totday, 'c1'] = cd.x.quantile(quantile)
        if (len(cdata[(cdata.poa>600) & (cdata.poa<800)]) > min_dp_num):
            cd= cdata[(cdata.poa>600) & (cdata.poa<800)]
            daydata.loc[daydata.totday==totday, 'c2'] = cd.x.quantile(quantile)
        if (len(cdata[(cdata.poa>400) & (cdata.poa<600)]) > min_dp_num):
            cd= cdata[(cdata.poa>400) & (cdata.poa<600)]
            daydata.loc[daydata.totday==totday, 'c3'] = cd.x.quantile(quantile)
        if (len(cdata[(cdata.poa>200) & (cdata.poa<400)]) > min_dp_num):
            cd= cdata[(cdata.poa>200) & (cdata.poa<400)]
            daydata.loc[daydata.totday==totday, 'c4'] = cd.x.quantile(quantile)
            
    daydata = daydata.drop(['totday'], axis=1)
    return daydata


def dw_rolling(x, y, w=12):
    import statsmodels.api as sm
    import statsmodels.stats.api as sms
    
    dw = pd.DataFrame(index=x.index, columns=['dw', 'dw_rolling'])
    for i in range(w-1,len(x)):
        cx = x[np.array(range(i-w+1,i+1))]
        cy = y[np.array(range(i-w+1,i+1))]
        cX = sm.add_constant(cx)
        model = sm.OLS(cy, cX)
        results = model.fit()
        ols_resid = results.resid
        dw.loc[i,'dw'] = sms.durbin_watson(results.resid)
    
    for i in range(w-1, len(x)-w+1):
        clist = dw.loc[range(i,i+w),'dw'].tolist()
        clist.sort(reverse=True)
        dw.loc[i,'dw_rolling'] = sum(clist[(int(w/6)-1):(int(w/3)+1)]) / (int(w/3)-int(w/6)+2)
    return dw


def butter_lowpass_filter(data, cutoff, fs, order):
    from scipy.signal import butter,filtfilt
    
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y
