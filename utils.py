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

from constants import stocks, tw_stocks

from FinMind.data import DataLoader
from loguru import logger

logger.disable("FinMind")  # silence FinMind's per-stock INFO logs
import tejapi
import yfinance as yf

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
        for stock in tw_stocks.keys():
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
    def load_from_yfinance(today: dt.date) -> pd.DataFrame:
        """
        Given today's date, return a DataFrame of daily prices for the DAX 40 stocks over the past year (same columns as the FinMind version)
        """
        raw = yf.download(
            list(stocks.keys()),
            start = (today - dt.timedelta(days=366)).strftime("%Y-%m-%d"),
            end = (today + dt.timedelta(days=1)).strftime("%Y-%m-%d"),  # end is exclusive
            group_by = 'ticker',
            auto_adjust = False,
            progress = False,
        )

        data = (raw.stack(level = 0, future_stack = True)
                .rename_axis(['date', 'stock_id'])
                .reset_index()
                .dropna(subset = ['Close'])
                .rename(columns = {
                    'Open': 'open',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'close',
                    'Volume': 'Trading_Volume'
                })
                [['stock_id', 'date', 'open', 'max', 'min', 'close', 'Trading_Volume']]
                )
        data['date'] = pd.to_datetime(data['date'])
        data['Trading_Volume'] = data['Trading_Volume'] / 1000

        return data


    @staticmethod
    @st.cache_data(persist = 'disk')
    def load_from_tej(today: dt.date) -> pd.DataFrame:
        """ 
        Given today's date, return a DataFrame of daily prices over the past year for selected Taiwan ETFs and the top 10 holdings of 0050
        """
        from dotenv import dotenv_values
        tejapi.ApiConfig.api_key = st.secrets['TEJ_APIKEY2']

        # * Use the TWSE/TPEx unadjusted daily price API to get one year of daily prices
        data_mon = tejapi.get("TRAIL/TAPRCD", 
                        mdate = {'gte': (today - dt.timedelta(days=366)).strftime("%Y-%m-%d"),
                                 'lte': today.strftime("%Y-%m-%d")
                                 },
                        coid = list(tw_stocks.keys()),            # Filter by coid; tw_stocks is the predefined stock list.
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
        
        return data_mon
    

if __name__ == "__main__":
    # Example usage
    data = LoadData.load_from_finmind(dt.datetime.today().date())
    print(data.head())