import pandas as pd 
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
import datetime as dt

from utils import LoadData
from constants import stocks

st.set_page_config(
    page_title = "Taiwan ETFs Dashboard",
    page_icon = "🧊",
    layout = "wide",
    initial_sidebar_state = "expanded"
)
with open("style.css") as style_sheet:
            st.markdown(f"<style>{style_sheet.read()}</style>", unsafe_allow_html = True)


# ------------------------------------------------------------------------------------------------------
# * Load Data
try:
    tej_data = LoadData.load_from_tej(dt.datetime.today().date())
    # data = LoadData.load_from_finmind(dt.datetime.today().date())
except Exception as e:
    st.error(f"Error loading data: {e}")
    tej_data = LoadData.load_from_csv('tej.csv')

try:
    finmind_data = LoadData.load_from_finmind(dt.datetime.today().date())
except Exception as e:
    st.error(f"Error loading data: {e}")
    finmind_data = LoadData.load_from_csv('finmind_etf_20250101_20250123.csv')


# ------------------------------------------------------------------------------------------------------
# * Select Source
cols = st.columns((1/3, 1/3, 1/3))
with cols[0].container(border = True, height=100):
    source = st.pills("資料來源（預設為 TEJ）", ["FinMind", "TEJ 台灣經濟新報"], selection_mode = 'single')


if source == "FinMind":
    data = finmind_data
else:
    data = tej_data

with cols[1].container(border = True, height=100):
    st.markdown(f"""
        <div class="data-pair-container">
            <div class="data-block">
                <span class="data-number date">{data['date'].max().strftime("%Y-%m-%d")}</span>
                <span class="data-label time">最新資料日期</span>
            </div>
        </div>""", unsafe_allow_html = True)
    
with cols[2].container(border = True, height=100):
    st.markdown(f"""
        <div class="data-pair-container">
            <div class="data-block">
                <span class="data-number date">{len(data)}</span>
                <span class="data-label time">資料總筆數</span>
            </div>
        </div>""", unsafe_allow_html = True)


# ------------------------------------------------------------------------------------------------------
# * Top 5 Gainers K Bar (one day)
def calculate_change(group):
    # 檢查是否有足夠的資料列
    if len(group) < 2:
        return None 
    return {
        "stock_id": group.name,
        "change": (group.iloc[1]['close'] - group.iloc[0]['close']) / group.iloc[0]['close'] * 100
    }

@st.fragment
def top_kbar(df):
    df['date'] = pd.to_datetime(df['date'])
    most_recents = (df[df['date'] > df['date'].max() - pd.Timedelta(days=2)]
                    .sort_values(by=['stock_id', 'date'], ascending=True)
                    )
    changes = (most_recents
     .groupby("stock_id")
     .apply(calculate_change, include_groups = False)
    )
    top5 = changes.sort_values(by = 'change', scending=False).head(5)

    st.subheader("最近一日漲幅前五名股票 K 線圖")
    with st.container(border = True):
        cols = st.columns((0.2, 0.2, 0.2, 0.2, 0.2))
    for stock_id, col in zip(top5.index, cols):

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        stock_data = most_recents[(most_recents['stock_id'] == stock_id) & (most_recents['date'] == most_recents['date'].max())]
        fig.add_trace(go.Candlestick(
                                    x=stock_data['date'],
                                    name='Price',
                                    open=stock_data['open'],
                                    high=stock_data['max'],
                                    low=stock_data['min'],
                                    close=stock_data['close'],
                                    increasing_line_color= 'red', decreasing_line_color= '#21CC54'
                                    ), secondary_y=True)
        fig.update_layout(xaxis_rangeslider_visible = False,
                          margin=dict(l=0, r=0, t=0, b=0), height = 200)
        with col:
            st.markdown(f"##### {stock_id} - {stocks[stock_id]}")
            
            st.plotly_chart(fig, config={'displayModeBar': False})


# ------------------------------------------------------------------------------------------------------
# * Single K bar (One year)
@st.fragment
def single_kbar(df):
    st.subheader("單一標的 K 線圖與成交量")
    cols_1 = st.columns((0.2, 0.8))

    with cols_1[0]:
        with st.container(border = True, height = 180):
            stock = st.selectbox("選擇標的", list(stocks.keys()),
                                format_func = lambda x: f"{x} - {stocks[x]}"
                                )
            df = df[df['stock_id'] == stock]
            
        
            opts = st.pills("指標", ['價格 K 線', '成交量'], selection_mode = 'multi', default = ['價格 K 線', '成交量'])

        with st.container(border = True, height = 253):

            df = df.sort_values(by='date', ascending=True)
            most_recents = df.iloc[len(df)-2:len(df), :]
            
            st.metric("**:gray[最近一日成交量 (千股)]**", 
                      most_recents.iloc[1]['Trading_Volume'],
                      most_recents.iloc[1]['Trading_Volume'] - most_recents.iloc[0]['Trading_Volume'],
                      delta_color = "inverse",
                      format = "localized"
                      )
            st.metric("**:gray[最近一日收盤價]**", 
                      most_recents.iloc[1]['close'],
                      most_recents.iloc[1]['close'] - most_recents.iloc[0]['close'],
                      delta_color = "inverse",
                      format = "localized"
                      )


    with cols_1[1].container(border = True, height = 450):

        st.markdown(f"##### {stock} -{stocks[stock]}")

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        if "成交量"  in opts:

            fig.add_trace(go.Bar(x=df['date'], 
                                 y=df['Trading_Volume'], 
                                 marker_color="#7DACEE", 
                                 name='Volume', 
                                 opacity =0.5), secondary_y=False)

        if "價格 K 線" in opts:
            fig.add_trace(go.Candlestick(
                                        x=df['date'],
                                        name='Price',
                                        open=df['open'],
                                        high=df['max'],
                                        low=df['min'],
                                        close=df['close'],
                                        increasing_line_color= 'red', decreasing_line_color= '#21CC54'
                                        ), secondary_y=True)


        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height = 360)
        st.plotly_chart(fig, config={'displayModeBar': False})



# ------------------------------------------------------------------------------------------------------
# * Normalized Close Price Comparison
@st.fragment 
def peer_comparison(df):
    st.subheader("多重標的標準化收盤價比較圖（以所選期間起始日收盤價為基準）")

    cols_2 = st.columns((0.2, 0.8))

    with cols_2[0]:
        with st.container(border = True, height = 400):
            selected_stocks = st.multiselect("選擇標的", list(stocks.keys()),
                                            default=["0050", "00663L"]
                                            )

            window = st.pills("選擇時間區間", [30, 90, 180, 365], default = 365, format_func= lambda x: ['1 month', '3 months', '6 months', '1 year'][[30, 90, 180, 365].index(x)])
    


    
    

    with cols_2[1].container(border = True, height = 400):
        if window is None:
            st.warning("請選擇一個時間區間") 
        else:
            df = df[df['date'] >= df['date'].max() - pd.Timedelta(days=window)]
            df = df[df['stock_id'].isin(selected_stocks)]
            df = (df.groupby('stock_id')
                .apply(lambda group: (group.sort_values(by='date', ascending=True)
                                        .assign(close = lambda x: x['close'] / x['close'].iloc[0])
                                        )
                    )
                    .reset_index(drop=True)
                )
            df = df.sort_values(by='date', ascending=True)

            
            
            fig = px.line(df, x='date', y='close', color='stock_id')
            fig.update_layout(margin=dict(t=0), height = 380)
            st.plotly_chart(fig, config={'displayModeBar': False})

top_kbar(data)
single_kbar(data)
peer_comparison(data)
