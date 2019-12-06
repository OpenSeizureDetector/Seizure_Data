#!/usr/bin/env python
#
#
# MIT License - analyse_datafile
#
# Copyright (c) 2019 Graham Jones
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

# Checks:
# Used spreadsheet to check accMean and AccSd calculations.

import argparse
from datetime import datetime
import time
import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

def readFile(fname):
    "reads the file and returns a pandas dataframe for the data"
    print("readFile - fname=%s" % fname)

    powThresh = 100.

    df = pd.read_csv(fname, skipinitialspace=True)

    # Convert date string into datetime.
    df.iloc[:,0]=pd.to_datetime(df.iloc[:,0])

    #print(df)
    #print(df.dtypes)

    columnsArr=['datetime',
                 '1Hz','2Hz','3Hz','4Hz','5Hz',
                 '6Hz','7Hz','8Hz','9Hz','10Hz',
                 'specPow', 'roiPow', 'sampleFreq', 'statusStr', 'HR']
    for i in range(1,126):
        #print(i)
        columnsArr.append('d%03d' % i)

    df.columns = columnsArr

    df['AccMean'] = df.iloc[:,16:141].mean(axis=1)
    avAcc = df['AccMean'].mean()
    print(avAcc)
    df['AccMean'] = df['AccMean'] - avAcc
    df['AccSd'] = df.iloc[:,16:141].std(axis=1)
    df['roiRatio'] = 10.*df['roiPow'] / df['specPow']
    df['roiRatio2'] = df['roiRatio'] * (df['specPow'] > powThresh)
    df['thresh'] = df['roiRatio']
    df['thresh'] = 54.

    # Calculate time from start of file in hours
    startTs = df.iloc[0,0]
    df['timefromstart'] = (df['datetime'] - startTs).dt.total_seconds()/3600.

    df.set_index(['datetime'])
    #print(df.dtypes)
    #print(df)
    return(df)
    


def getTimeSlice(df,startDate, endDate):
    print("getTImeSlice(): startDate=%s, endDate=%s" % (startDate, endDate))
    startDatetime = pd.to_datetime(startDate)
    endDatetime = pd.to_datetime(endDate)
    mask = (df['datetime'] > startDatetime) & (df['datetime'] <= endDatetime)
    dfs = df.loc[mask].copy()
    # Calculate time from start of file in minutes
    startTs = dfs.iloc[0,0]
    dfs['mins'] = (df['datetime'] - startTs).dt.total_seconds()/60.
    avAcc = dfs['AccMean'].mean()
    dfs['AccMean'] = dfs['AccMean'] - avAcc

    return(dfs)


def getAlarmPoints(df, warnings=False):
    if (warnings):
        mask = (df['statusStr']=="WARNING")
    else:
        mask = (df['statusStr']=="ALARM")
    dfa = df.loc[mask].copy()
    dfa['alarm'] = dfa['roiRatio']
    dfa['warning'] = dfa['roiRatio']
    return(dfa)

def plotData(df, title="", saveFile=False):
    dfAlarm = getAlarmPoints(df,False)
    #print(dfAlarm)

    dfWarn = getAlarmPoints(df,True)
    #print(dfWarn)

    fig, ax = plt.subplots(3,1)
    df.plot(kind='line',x='datetime',y='AccMean', ax=ax[0])
    ax[0].set_xlabel("")
    ax[0].set_xticklabels([])
    df.plot(kind='line',x='datetime',y='roiPow', color='blue', ax=ax[1])
    df.plot(kind='line',x='datetime',y='specPow', color='red',  ax=ax[1])
    ax[1].set_xlabel("")
    ax[1].set_xticklabels([])
    df.plot(kind='line',x='datetime',y='roiRatio2', ax=ax[2])
    df.plot(kind='line',x='datetime',y='thresh', color='red', ax=ax[2])
    if (len(dfAlarm.index)>0):
        dfAlarm.plot(kind='line',x='datetime',y='alarm', style='o', markersize=7,ax=ax[2])
    else:
        print("No Alarm points to plot")
    if (len(dfWarn.index)>0):
        dfWarn.plot(kind='line',x='datetime',y='warning', style='.', markersize=7,ax=ax[2])
    else:
        print("No Warning points to plot")
    ax[2].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    fig.suptitle(title, fontsize=12)

    if (saveFile):
        plt.savefig("analyse_datafile.png", papertype="A4")
    else:
        plt.show()



if __name__ == "__main__":
    print("analyse_datafile.__main__()")


    parser = argparse.ArgumentParser(description='OpenSeizureDetector Data file analyser')
    parser.add_argument('inFile', 
                        help='Data file to analyse')
    parser.add_argument('--saveFile', dest='saveFile', action='store_true',
                        help='Save the graphs to a file rather than displaying on screen')

    parser.add_argument('--startDate',
                        help='start Date (dd-mm-yyyy hh:mm) of period for detailed analysis')
    parser.add_argument('--endDate',
                        help='end date (dd-mm-yyyy hh:mm) of period for detailed analysis')
    parser.add_argument('--title',
                        help='Plot title')

    argsNamespace = parser.parse_args()
    args = vars(argsNamespace)
    print(args)
    startDate = args['startDate']
    endDate = args['endDate']
    saveFile = args['saveFile']
    title=args['title']

    df = readFile(args['inFile'])
    #print(df)

    dfSlice = getTimeSlice(df,startDate, endDate)
    print("dfSlice=")
    print(dfSlice)

    plotData(dfSlice, saveFile=saveFile, title=title)

    
    print("analyse_datafile complete")
