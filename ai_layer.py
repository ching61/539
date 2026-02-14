import os
import google.generativeai as genai
from stats_engine import StatsEngine
from typing import Dict, Any

class AILayer:
    """
    Gemini AI 互動層
    負責將統計數據注入 Gemini 模型並獲取分析結果。
    """

    def __init__(self, stats_engine: StatsEngine):
        self.stats_engine = stats_engine
        self.model = None
        self.chat = None

    def configure_api_key(self, api_key: str = None):
        """
        配置 Google Gemini API 金鑰。
        優先使用傳入的 api_key，若無則嘗試從環境變數 'GOOGLE_API_KEY' 讀取。
        """
        key = api_key or os.getenv('GOOGLE_API_KEY')
        if not key:
            raise ValueError("API key not provided. Please pass it as an argument or set the 'GOOGLE_API_KEY' environment variable.")
        
        try:
            genai.configure(api_key=key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            print("✅ Gemini API 金鑰已成功配置。")
        except Exception as e:
            print(f"❌ 配置 Gemini API 金鑰時發生錯誤: {e}")
            self.model = None

    def _generate_analysis_prompt(self, num_draws: int = 30) -> str:
        """
        生成用於 AI 分析的詳細提示 (Prompt)。
        """
        if self.stats_engine.df.empty:
            return "錯誤：無法生成提示，因為沒有可用的統計數據。"

        # 獲取統計數據
        freq = self.stats_engine.calculate_frequency(num_draws=num_draws)
        sum_analysis = self.stats_engine.calculate_sum_analysis(num_draws=num_draws)
        ratios = self.stats_engine.calculate_odd_even_big_small_ratios(num_draws=num_draws)
        consecutive = self.stats_engine.analyze_consecutive_numbers(num_draws=num_draws)
        last_digits = self.stats_engine.analyze_last_digits(num_draws=num_draws)

        # 排序頻率以找到熱門和冷門號碼
        sorted_freq = sorted(freq.items(), key=lambda item: item[1])
        hot_numbers = [f"{item[0]:02d}" for item in sorted_freq[-5:]] # Top 5
        cold_numbers = [f"{item[0]:02d}" for item in sorted_freq[:5]] # Bottom 5

        # 找到最常見的奇偶比和大小比
        common_odd_even = max(ratios['odd_even_distribution'], key=ratios['odd_even_distribution'].get)
        common_big_small = max(ratios['big_small_distribution'], key=ratios['big_small_distribution'].get)
        
        # 找到最熱門的尾數
        hot_last_digits = sorted(last_digits.items(), key=lambda item: item[1], reverse=True)
        hot_last_digits_str = ", ".join([str(item[0]) for item in hot_last_digits[:3]])


        prompt = f"""
您是一位專業的樂透數據分析師，專精於「今彩539」。請根據以下最近 {num_draws} 期的統計數據，提供您的專業分析與見解。請用繁體中文回答。

--- 數據摘要 (最近 {num_draws} 期) ---
- **熱門號碼 (出現最多次)**: {', '.join(hot_numbers)}
- **冷門號碼 (出現最少次)**: {', '.join(cold_numbers)}
- **和值趨勢**: 平均和值為 {sum_analysis['mean_sum']:.2f}，近期和值在 {sum_analysis['min_sum']} 到 {sum_analysis['max_sum']} 之間波動。
- **奇偶比趨勢**: 最常見的奇偶比為「{common_odd_even}」。
- **大小比趨勢** (1-19為小, 20-39為大): 最常見的大小比為「{common_big_small}」。
- **連號趨勢**: 最近 {num_draws} 期中，有 {consecutive['total_draws_with_consecutive']} 期出現連號，佔比約 {consecutive['percentage_with_consecutive']:.2f}%。
- **尾數趨勢**: 最熱門的尾數為 {hot_last_digits_str}。

--- 分析任務 ---
請根據以上數據，完成以下三項任務：

1.  **總結趨勢**: 請用 2-3 句話，以專業且易懂的方式，總結近期的主要趨勢。
2.  **提供建議**: 基於「排除低機率極端組合」的原則（例如，避免全奇/全偶、全大/全小、和值過高/過低），並結合上述數據，請提供 2 組 (每組 5 個號碼) 具有參考價值的選號建議。
3.  **說明理由**: 簡要說明您提供這 2 組號碼的理由，例如您是如何平衡熱門/冷門號碼，或如何考慮奇偶/大小比的。
"""
        return prompt

    def get_ai_analysis(self, num_draws: int = 30) -> str:
        """
        獲取 AI 對統計數據的分析，並啟動一個新的對話會話。
        返回初始的 AI 分析文本。
        """
        if not self.model:
            return "錯誤：Gemini 模型未配置。請先設定 API 金鑰。"

        analysis_prompt = self._generate_analysis_prompt(num_draws)
        if analysis_prompt.startswith("錯誤"):
            return analysis_prompt
            
        try:
            print("正在向 Gemini API 發送請求，啟動對話會話，請稍候...")
            # Start a new chat session with the analysis prompt directly
            self.chat = self.model.start_chat(history=[])
            response = self.chat.send_message(analysis_prompt)
            return response.text
        except Exception as e:
            return f"❌ 與 Gemini API 互動時發生錯誤: {e}"

    def send_chat_message(self, message: str) -> str:
        """
        向活躍的對話會話發送訊息並獲取 AI 的回應。
        """
        if not self.chat:
            return "錯誤：對話會話未啟動。請先獲取 AI 分析以啟動對話。"
        try:
            response = self.chat.send_message(message)
            return response.text
        except Exception as e:
            return f"❌ 與 Gemini API 對話時發生錯誤: {e}"

# 範例使用
if __name__ == "__main__":
    # 確保 lottery_data/lottery_data.csv 存在
    if not os.path.exists('lottery_data/lottery_data.csv'):
        print("錯誤：找不到 lottery_data/lottery_data.csv。")
        print("請先執行 python data_engine.py 來生成數據。")
    else:
        # 1. 創建統計引擎實例
        stats_engine = StatsEngine()
        
        # 2. 創建 AI 互動層實例
        ai_layer = AILayer(stats_engine)

        # 3. 配置 API 金鑰
        try:
            # 嘗試從環境變數讀取，如果沒有則提示使用者輸入
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                api_key = input("請輸入您的 Google API Key: ")
            
            ai_layer.configure_api_key(api_key)

            # 4. 獲取 AI 分析
            if ai_layer.model:
                initial_analysis = ai_layer.get_ai_analysis(num_draws=30)
                print("\n--- Gemini AI 分析報告 (近30期) ---")
                print(initial_analysis)

                if ai_layer.chat:
                    print("\n--- 進入對話模式 ---")
                    while True:
                        user_query = input("你的問題 (輸入 'exit' 結束): ")
                        if user_query.lower() == 'exit':
                            break
                        response = ai_layer.send_chat_message(user_query)
                        print(f"AI: {response}")
                else:
                    print("無法啟動對話會話。")

        except ValueError as e:
            print(f"錯誤: {e}")
        except Exception as e:
            print(f"發生未預期的錯誤: {e}")
