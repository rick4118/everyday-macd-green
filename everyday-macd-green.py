import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 設置 Streamlit 頁面標題
st.title("日 MACD「綠縮」股票篩選器")

# 計算日 EMA、DIF、MACD 與柱狀體 OSC
def compute_macd(df, fast=12, slow=26, signal=9):
    df['EMA_fast'] = df['Close'].ewm(span=fast, adjust=False).mean()
    df['EMA_slow'] = df['Close'].ewm(span=slow, adjust=False).mean()
    df['DIF'] = df['EMA_fast'] - df['EMA_slow']
    df['MACD'] = df['DIF'].ewm(span=signal, adjust=False).mean()
    df['OSC'] = df['DIF'] - df['MACD']
    return df

# 篩選邏輯
def find_macd_green_shrink_stocks_daily(ticker_list, start_date, end_date):
    result = []
    download_start = (pd.to_datetime(start_date) - pd.Timedelta(days=90)).strftime('%Y-%m-%d')

    for ticker in ticker_list:
        try: 
            df = yf.download(ticker, start=download_start, end=end_date, interval="1d", group_by="column", auto_adjust=True, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            if df.empty:
                continue

            df = compute_macd(df)
            df_filtered = df[(df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))]
            if len(df_filtered) < 3:
                continue
            recent = df_filtered.iloc[-3:].copy()
            osc_val = recent['OSC'].values.flatten()

            # 💡 判斷條件：綠縮（前一日與當日皆為綠柱 < 0，且當日負值變大、綠柱長度比前一日短，即當日 OSC 數值大於前一日）
            if osc_val[-2] < 0 and osc_val[-1] < 0 and osc_val[-1] > osc_val[-2]:
                result.append(ticker)
        except Exception as e:
            pass
    return result

# 側邊欄參數設定
st.sidebar.header("設定篩選參數")
tickers_input = st.sidebar.text_area(
    "輸入股票代碼 (以逗號分隔)",
    value="5230.TWO, 3178.TWO, 6902.TW, 5465.TWO, 6526.TW, 6426.TW, 3717.TW, 7792.TWO, 6620.TWO, 4960.TW"
)
ticker_list = [t.strip() for t in tickers_input.split(",") if t.strip()]

start_date = st.sidebar.date_input("開始日期", value=pd.to_datetime("2025-11-01"))
end_date = st.sidebar.date_input("結束日期", value=datetime.today())

if st.sidebar.button("開始篩選"):
    st.write(f"正在分析從 **{start_date}** 到 **{end_date}** 的數據...")
    with st.spinner("計算中，請稍候..."):
        selected_stocks = find_macd_green_shrink_stocks_daily(ticker_list, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    
    st.subheader("篩選結果")
    if selected_stocks:
        st.success(f"符合日 MACD「綠縮」的股票如下：")
        st.write(selected_stocks)
    else:
        st.warning("在設定的日期範圍內，沒有符合條件的股票。")
