import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from data_engine import DailyCashCrawler
from stats_engine import StatsEngine
from ai_layer import AILayer
import time
from typing import Dict
import sys

# Set matplotlib font to support Chinese characters conditionally
if sys.platform == "win32":
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']  # For Windows
else:
    plt.rcParams['font.sans-serif'] = ['Noto Sans CJK TC', 'Noto Sans CJK JP', 'Noto Sans CJK SC', 'Noto Sans CJK KR', 'Noto Sans CJK', 'WenQuanYi Zen Hei', 'DejaVu Sans', 'sans-serif'] # For Linux/macOS (Streamlit Cloud)
plt.rcParams['axes.unicode_minus'] = False # To handle negative signs correctly

# --- Streamlit App Configuration ---
st.set_page_config(
    page_title="今彩539 智慧統計與 AI 預測助手",
    page_icon="🎲",
    layout="wide"
)

# --- Helper Functions ---
@st.cache_data
def load_and_process_data():
    """Load data from CSV and perform initial processing."""
    crawler = DailyCashCrawler()
    # Ensure data is up-to-date before loading
    crawler.crawl_and_save_daily_cash() 
    
    # Load the updated data
    if os.path.exists('lottery_data/lottery_data.csv'):
        df = pd.read_csv('lottery_data/lottery_data.csv', dtype={'draw': str})
        df['numbers_list'] = df['numbers'].apply(lambda x: [int(n) for n in x.split(',')])
        df['ad_date'] = pd.to_datetime(df['ad_date'])
        df = df.sort_values(by='ad_date', ascending=True).reset_index(drop=True)
        return df
    return pd.DataFrame()

def display_frequency_chart(data: Dict[int, int], title: str):
    """Display a bar chart for number frequency."""
    if not data:
        st.warning("沒有頻率數據可供顯示。")
        return

    numbers = list(data.keys())
    counts = list(data.values())

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(numbers, counts, color='skyblue')
    ax.set_xlabel("號碼")
    ax.set_ylabel("出現次數")
    ax.set_title(title)
    ax.set_xticks(numbers)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    st.pyplot(fig)
    plt.close(fig)

def display_distribution_chart(data: Dict[str, int], title: str):
    """Display a bar chart for distribution (e.g., odd/even, big/small)."""
    if not data:
        st.warning("沒有分佈數據可供顯示。")
        return

    labels = list(data.keys())
    counts = list(data.values())

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(labels, counts, color='lightcoral')
    ax.set_xlabel("模式")
    ax.set_ylabel("出現次數")
    ax.set_title(title)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    st.pyplot(fig)
    plt.close(fig)

# --- Main Application ---
st.title("🎲 今彩539 智慧統計與 AI 預測助手")

# --- Sidebar ---
st.sidebar.header("設定")
api_key = st.sidebar.text_input("輸入您的 Google API Key", type="password", key="gemini_api_key")

# Data Update Button
if st.sidebar.button("更新今彩539資料"):
    with st.spinner("正在更新資料，請稍候..."):
        df_data = load_and_process_data()
        if not df_data.empty:
            st.sidebar.success(f"資料更新完成！總計 {len(df_data)} 筆記錄。")
        else:
            st.sidebar.error("資料更新失敗。")

# Load data (and update if necessary)
df_data = load_and_process_data()

if df_data.empty:
    st.error("無法載入今彩539歷史資料。請檢查網路連線或稍後再試。")
else:
    stats_engine = StatsEngine(data_filepath='lottery_data/lottery_data.csv') # Re-initialize to ensure latest data
    
    st.subheader("📊 資料概覽")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("總期數", len(df_data))
    with col2:
        st.metric("最新開獎日期", df_data['ad_date'].max().strftime('%Y-%m-%d'))
    with col3:
        st.metric("最早開獎日期", df_data['ad_date'].min().strftime('%Y-%m-%d'))

    st.markdown("---")

    # --- Statistical Analysis ---
    st.subheader("📈 統計分析")

    # Display Latest 5 Draws
    st.write("#### 最近五期開獎號碼")
    latest_5_draws_df = stats_engine.get_latest_n_draws(5)
    if not latest_5_draws_df.empty:
        # Sort by date in descending order (most recent first)
        latest_5_draws_df = latest_5_draws_df.sort_values(by='ad_date', ascending=False).reset_index(drop=True)
        
        for index, row in latest_5_draws_df.iterrows():
            draw_num = row['draw']
            draw_date = row['date']
            numbers = row['numbers'] # This is already formatted as "01,02,..."
            
            st.markdown(f"**期數**: {draw_num} &nbsp; **日期**: {draw_date} &nbsp; **號碼**: <big><span style='font-weight:bold; color:#FF4B4B;'>{numbers}</span></big>", unsafe_allow_html=True)
        st.markdown("---")
    else:
        st.info("沒有最新的開獎號碼數據。")


    # Frequency Analysis
    st.write("#### 號碼頻率分析")
    freq_all = stats_engine.calculate_frequency()
    display_frequency_chart(freq_all, "所有期數號碼頻率")

    st.write("#### 近期號碼頻率分析 (近30期)")
    freq_30 = stats_engine.calculate_frequency(num_draws=30)
    display_frequency_chart(freq_30, "近30期號碼頻率")

    # Sum Analysis
    st.write("#### 和值分析")
    sum_analysis = stats_engine.calculate_sum_analysis()
    st.write(f"平均和值: **{sum_analysis['mean_sum']:.2f}**")
    st.write(f"中位數和值: **{sum_analysis['median_sum']:.2f}**")
    st.write(f"和值標準差: **{sum_analysis['std_dev_sum']:.2f}**")
    st.write(f"和值範圍: **{sum_analysis['min_sum']} - {sum_analysis['max_sum']}**")

    # Odd/Even and Big/Small Ratios
    st.write("#### 奇偶/大小比分析")
    ratios = stats_engine.calculate_odd_even_big_small_ratios()
    col_oe, col_bs = st.columns(2)
    with col_oe:
        display_distribution_chart(ratios['odd_even_distribution'], "奇偶比分佈")
    with col_bs:
        display_distribution_chart(ratios['big_small_distribution'], "大小比分佈")

    # Consecutive Numbers
    st.write("#### 連號模式分佈 (所有期數)")
    consecutive_analysis = stats_engine.analyze_consecutive_numbers()
    st.write(f"總共有 **{consecutive_analysis['total_draws_with_consecutive']}** 期出現連號 ({consecutive_analysis['percentage_with_consecutive']:.2f}%)")
    
    # Format the consecutive patterns for better readability
    if consecutive_analysis['consecutive_patterns']:
        df_consecutive = pd.DataFrame(
            consecutive_analysis['consecutive_patterns'].items(),
            columns=['連號組合', '出現次數']
        ).sort_values(by='出現次數', ascending=False).reset_index(drop=True)
        st.dataframe(df_consecutive)
    else:
        st.info("沒有找到任何連號模式。")

    # Last Digits
    st.write("#### 尾數頻率分析")
    last_digits = stats_engine.analyze_last_digits()
    display_frequency_chart(last_digits, "尾數頻率")

    st.markdown("---")

    # --- AI Interaction Layer ---
    st.subheader("🤖 Gemini AI 智慧分析與選號建議")

    if "ai_layer" not in st.session_state:
        st.session_state.ai_layer = AILayer(stats_engine)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not api_key:
        st.warning("請在左側邊欄輸入您的 Google API Key 以啟用 AI 功能。")
    else:
        try:
            st.session_state.ai_layer.configure_api_key(api_key)
            if st.session_state.ai_layer.model:
                if st.button("獲取 AI 分析與選號建議", key="get_ai_analysis_button"):
                    with st.spinner("AI 正在分析中，請稍候..."):
                        initial_analysis = st.session_state.ai_layer.get_ai_analysis(num_draws=30)
                        st.session_state.messages.append({"role": "assistant", "content": initial_analysis})
                        # Rerun to display the analysis and chat interface
                        st.rerun()
                
                # Display chat messages
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                # Chat input
                if prompt := st.chat_input("向 AI 提問"):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    with st.chat_message("assistant"):
                        with st.spinner("AI 思考中..."):
                            response = st.session_state.ai_layer.send_chat_message(prompt)
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})

            else:
                st.error("AI 模型配置失敗，請檢查您的 API Key。")
        except Exception as e:
            st.error(f"AI 功能初始化失敗: {e}")

st.markdown("---")
st.caption("⚠️ 免責聲明：本專案僅供數據科學研究使用。彩券具隨機性，統計分析無法保證中獎，請理性投注。")
