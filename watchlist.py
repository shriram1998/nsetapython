# This program can generate a table based on several ta inducators frequently used by traders, to have an overall view of the market
# Dependancies: 1. fno.csv(added along with this app) file 2.Talib library.You can check online or mail me for help on talib installation

from datetime import date
import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timedelta
from bs4 import BeautifulSoup
import talib as ta
import sys
import json
import requests
import nsepy
import os
import time
import math

os.chdir(os.path.dirname(os.path.abspath(__file__)))

endDate = datetime.today().date()
startDate = endDate-timedelta(days=55)

def SMAV(stockData): #SMAV - Simple Moving AVerage function
    for i in range(len(stockData)):
        try:
            data=nsepy.get_history(stockData.loc[i,'StockID'],start=startDate,end=endDate)['Volume'].rolling(window=10).mean().iloc[-1]
            #data=pd.DataFrame(pd.read_csv("..../stockID.csv"))  --> Use locally stored data for faster execution here and below
            stockData.loc[i,'10 Day Average']=data
        except:
            print('SMAV not found for ',stockData.loc[i,'StockID'])
    return stockData

def SR(stockData): #Support and Resistance
    url = "https://stock-financials.valuestocks.in/en/nse-stocks-support-and-resistance"
    try:
        html_content = requests.get(url).text
        soup = BeautifulSoup(html_content, "lxml")
        table = soup.find("table", attrs={"class": "table"})
        header = ['SNo', 'Item', 'Name', 'R2',
                  'R1', 'LTP', 'S1', 'S2', 'Top500']
        rows = table.tbody.find_all("tr")
        rowData = [re.text.replace('\n', ',')[1:-1].split(',') for re in rows]
        df = pd.DataFrame(data=rowData, columns=header)
    except:
        print("Error fetching and processing SR data from website")
    for i in range(len(stockData)):
        try:
            stockSR = df[df['Name'] == stockData.loc[i, 'Name']]
        except:
            print('SR data not available for', stockData.loc[i, 'Name'])
            continue
        try:
            stockData.loc[i, 'R1'] = float(stockSR.iloc[0]['R1'])
        except:
            print('Issue updating R1 data for ', stockData.loc[i, 'Name'])
        try:
            stockData.loc[i, 'R2'] = float(stockSR.iloc[0]['R2'])
        except:
            print('Issue updating R2 data for ', stockData.loc[i, 'Name'])
        try:
            stockData.loc[i, 'S1'] = float(stockSR.iloc[0]['S1'])
        except:
            print('Issue updating S1 data for ', stockData.loc[i, 'Name'])
        try:
            stockData.loc[i, 'S2'] = float(stockSR.iloc[0]['S2'])
        except:
            print('Issue updating S2 data for ', stockData.loc[i, 'Name'])
        #Calculating if the stock is in support or resistance zone
        try:
            Data =nsepy.get_history(stockData.loc[i,'StockID'],start=startDate,end=endDate)
            PDL = Data.iloc[-1]['Low']
            PDH = Data.iloc[-1]['High']
        except:
            print("Problem finding SR Strategy for",
                  stockData.loc[i, 'StockID'])
        try:
            if(((PDH >= stockData.loc[i, 'R1']) & (PDL < stockData.loc[i, 'R1'])) | ((PDL <= stockData.loc[i, 'S1']) & (PDH > stockData.loc[i, 'S1']))):
                stockData.loc[i, 'SRPDH'] = PDH
                stockData.loc[i, 'SRPDL'] = PDL
        except:
            print("Problem updating SR strategy data for ",
                  stockData.loc[i, 'StockID'])
    return stockData

def MACD(stockData): #Moving Average Convergence Divergence
    for i in range(len(stockData)):
        try:
            Data = nsepy.get_history(stockData.loc[i,'StockID'],start=startDate,end=endDate)
            #Data=pd.DataFrame(pd.read_csv(path))
            close = Data['Close'].values
        except:
            print("Problem finding Close data for ",
                  stockData.loc[i, 'StockID'])
        try:
            fast_ema = ta.EMA(close, 12)
            slow_ema = ta.EMA(close, 26)
            macd = fast_ema - slow_ema
            signal = ta.EMA(macd, 9)
            macdSignal = macd - signal
        except:
            print("Problem calculating MACD with talib for ",
                  stockData.loc[i, 'StockID'])
        try:
            stockData.loc[i, 'MACDU'] = macdSignal[-1] #MACD the previous day (ultimate day)
            stockData.loc[i, 'MACDPU'] = macdSignal[-2] #MACD the day before (penultimate day)
            if(macdSignal[-2] < 0 and macdSignal[-1] > 0):
                stockData.loc[i, 'MACDStrat'] = "Buy"
            if(macdSignal[-2] > 0 and macdSignal[-1] < 0):
                stockData.loc[i, 'MACDStrat'] = "Sell"
            if(macdSignal[-2] < 0 and macdSignal[-1] < 0 and macdSignal[-1] < macdSignal[-2]):
                stockData.loc[i, 'MACDStrat'] = "Neg D" #Negative Divergence
            if(macdSignal[-2] > 0 and macdSignal[-1] > 0 and macdSignal[-1] > macdSignal[-2]):
                stockData.loc[i, 'MACDStrat'] = "Pos D"
            if(macdSignal[-2] < 0 and macdSignal[-1] < 0 and macdSignal[-1] > macdSignal[-2]):
                stockData.loc[i, 'MACDStrat'] = "Neg C"
            if(macdSignal[-2] > 0 and macdSignal[-1] > 0 and macdSignal[-1] < macdSignal[-2]):
                stockData.loc[i, 'MACDStrat'] = "Pos C" #Postive Convergence
        except:
            print("Error updating macd of {}".format(
                stockData.loc[i, 'StockID']))
    return stockData

def RSI(stockData):
    for i in range(len(stockData)):
        try:
            Data =nsepy.get_history(stockData.loc[i,'StockID'],start=startDate,end=endDate)
            #Data=pd.DataFrame(pd.read_csv(path))
            close = Data['Close'].values
        except:
            print("Problem finding Close data for ",
                  stockData.loc[i, 'StockID'])
        try:
            rsi = ta.RSI(close)
        except Exception as e:
            print("Problem calculating RSI with talib for ",
                  stockData.loc[i, 'StockID'])
            print(e)
        try:
            stockData.loc[i, 'RSI'] = rsi[-1]
        except:
            print("Error updating rsi of {} ".format(
                stockData.loc[i, 'StockID']))
    return stockData #Rising Strength Index

def Bounce(stockData): #Daily Swing uptrend/downtrend indicator
    for i in range(len(stockData)):
        try:
            Data = nsepy.get_history(stockData.loc[i,'StockID'],start=startDate,end=endDate)
            #Data=pd.DataFrame(pd.read_csv(path))
            LTP=Data.iloc[-1]['Close']
        except:
            print('Data unavailable for calculating trend for',
                  stockData.loc[i, 'StockID'])
            continue
        Data['HT-1'] = Data['High'].shift(1)
        Data['HT-2'] = Data['High'].shift(2)
        Data['LT-1'] = Data['Low'].shift(1)
        Data['LT-2'] = Data['Low'].shift(2)
        HighDF = Data[(Data['HT-1'] > Data['High']) &
                      (Data['HT-1'] > Data['HT-2'])]
        LowDF = Data[(Data['LT-1'] < Data['Low']) &
                     (Data['LT-1'] < Data['LT-2'])]
        if((HighDF['HT-1'].iloc[-1] > HighDF['HT-1'].iloc[-2]) & (LowDF['LT-1'].iloc[-1] > LowDF['LT-1'].iloc[-2]) & (LTP > LowDF['LT-1'].iloc[-1])):
            stockData.loc[i, 'Trend'] = "Uptrend"
        if((HighDF['HT-1'].iloc[-1] < HighDF['HT-1'].iloc[-2]) & (LowDF['LT-1'].iloc[-1] < LowDF['LT-1'].iloc[-2]) & (LTP < HighDF['HT-1'].iloc[-1])):
            stockData.loc[i, 'Trend'] = "Downtrend" #Previous swing high's date
    return stockData

def PCR(stockData): #Put to call ratio taling OI data and volume into consideration
    url = "https://www.bloombergquint.com/feapi/markets/options/put-call-ratio?security-type=stock&limit=200"
    try:
        content = requests.get(url).json()['put-call-ratio']
        df = pd.DataFrame(content)
    except:
        print("Error fetching PCR data from API")
    for i in range(len(stockData)):
        try:
            stockPCR = df[df['symbol'] == stockData.loc[i, 'StockID']]
        except Exception as e:
            print(e)
        try:
            stockData.loc[i,
                          'PCROI_C'] = stockPCR['pcr-open-interest-current'].iloc[0]
        except:
            print('PCROI_C not available for', stockData.loc[i, 'StockID'])
        try:
            stockData.loc[i,
                          'PCROI_CH'] = stockPCR['pcr-open-interest-change'].iloc[0]
        except:
            print('PCROI_CH data not available for',
                  stockData.loc[i, 'StockID'])
        try:
            stockData.loc[i, 'PCRV_C'] = stockPCR['pcr-volume-current'].iloc[0]
        except:
            print('PCRV_C data not available for ',
                  stockData.loc[i, 'StockID'])
        try:
            stockData.loc[i, 'PCRV_CH'] = stockPCR['pcr-volume-change'].iloc[0]
        except:
            print('PCRV_CH data not available for ',
                  stockData.loc[i, 'StockID'])
    return stockData

def Candlestick(stockData): #Recognise candlestick data using ta library
    candle_names = ta.get_function_groups()['Pattern Recognition']
    for i in range(len(stockData)):
        try:
            data = nsepy.get_history(stockData.loc[i,'StockID'],start=startDate,end=endDate)
            #data=pd.DataFrame(pd.read_csv(path))
            data=data[['Open','High','Low','Close']].iloc[-10:]
            o=data['Open']
            h=data['High']
            l=data['Low']
            c=data['Close']
            for candle in candle_names:
                try:
                    data[candle] = getattr(ta, candle)(o,h,l,c)
                except:
                    pass
            data.drop(['Open','High','Low','Close'],inplace=True,axis=1)
            try:
                for j in range(len(data)):
                    #You are welcome to implement a different candlestick score pattern when more than one pattern is present by prioritizing some candles too
                    score=sum(data[data!=0].iloc[j].dropna())/100
                    data.loc[j,'Pattern']=','.join(data[data!=0].iloc[j].dropna().index.to_list()).replace('CDL','')
                    if(score>0):
                        data.loc[j,'Score']=3
                    if(score<0):
                        data.loc[j,'Score']=-3
                data.drop(candle_names,inplace=True,axis=1)
                stockData.loc[i,'Candlestick Pattern']=data.iloc[-1]['Pattern']
                stockData.loc[i,'Candlestick Score']=data.iloc[-1]['Score']
            except:
                pass
        except:
            print("Error in candlestick for", stockData.loc[i,'StockID'])
    return stockData

stockList=pd.DataFrame(pd.read_csv("./fno.csv")) #List of fno stocks in nse
stockData=Candlestick(SMAV(SR(PCR(RSI(MACD(Bounce(stockList)))))))
stockData.to_csv('./Watchlist on '+str(datetime.today().date())+'.csv', index=False)
