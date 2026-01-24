import pandas as pd

import asyncio
import sys

try:
    from asyncio import DefaultEventLoopPolicy
    asyncio.set_event_loop_policy(DefaultEventLoopPolicy())
except Exception:
    pass

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from constants import stocks

from FinMind.data import DataLoader
import tejapi

import pandas as pd
import datetime as dt
import streamlit as st



class LoadData:

    @staticmethod
    def load_from_csv(file_path: str) -> pd.DataFrame:
        """Load data from a CSV file into a pandas DataFrame."""
        return pd.read_csv(file_path)
    
    @staticmethod
    @st.cache_data(persist = 'disk')
    def load_from_finmind(today: dt.date) -> pd.DataFrame:
        api = DataLoader()
        # api.login_by_token(api_token = dotenv_values(".env")['FINMIND_APIKEY'])
        api.login_by_token(api_token = st.secrets['FINMIND_APIKEY'])

        data = pd.DataFrame()
        for stock in stocks.keys():
            df = api.taiwan_stock_daily(
                stock_id = stock,
                start_date = (today - dt.timedelta(days=366)).strftime("%Y-%m-%d"),
                end_date = today.strftime("%Y-%m-%d")
            )
            data = pd.concat([data, df], axis=0)

        data['date'] = pd.to_datetime(data['date'])
        data['Trading_Volume'] = data['Trading_Volume'] / 1000

        return data
    

    @staticmethod
    @st.cache_data(persist = 'disk')
    def load_from_tej(today: dt.date) -> pd.DataFrame:
        """ 
        輸入當日日期，回傳特定 ETF 與 0050 前 10 大成分股之近一年每日股價資料 DataFrame
        """

        from dotenv import dotenv_values
        # tejapi.ApiConfig.api_key = dotenv_values(".env")['TEJ_APIKEY2']
        tejapi.ApiConfig.api_key = st.secrets['TEJ_APIKEY2']


        # * 使用上市(櫃)未調整股價(日) API，取得一年內股票每日股價資料
        data_mon = tejapi.get("TRAIL/TAPRCD", 
                        mdate = {'gte': (today - dt.timedelta(days=366)).strftime("%Y-%m-%d"),
                                 'lte': today.strftime("%Y-%m-%d")
                                 },
                        coid = list(stocks.keys()),            # 使用 coid 欄位篩選股票。stocks 為預先定義之股票代碼列表。
                        opts = {'columns': [
                            'coid', 'mdate', 'open_d', 'high_d', 'low_d', 'close_d', 'volume'
                            ]
                        },
                        paginate = True)
        
        
        data_mon = data_mon.rename(columns = {
                    'coid': 'stock_id',
                    'mdate': 'date',
                    'open_d': 'open',
                    'high_d': 'max',
                    'low_d': 'min',
                    'close_d': 'close',
                    'volume': 'Trading_Volume'
                })
        
        data_mon.to_csv('tej.csv')

        return data_mon
    

if __name__ == "__main__":
    # Example usage
    data = LoadData.load_from_finmind(dt.datetime.today().date())
    print(data.head())