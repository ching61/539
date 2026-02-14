import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
import os

class StatsEngine:
    """
    今彩539科學統計引擎
    負責從歷史開獎數據中提取各種統計資訊。
    """

    def __init__(self, data_filepath: str = 'lottery_data/lottery_data.csv'):
        self.data_filepath = data_filepath
        self.df = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """
        載入今彩539歷史數據，並進行初步處理。
        """
        if not os.path.exists(self.data_filepath):
            print(f"錯誤：找不到資料檔案 {self.data_filepath}。請先執行資料爬取。")
            return pd.DataFrame()

        df = pd.read_csv(self.data_filepath, dtype={'draw': str})
        
        # 將 'numbers' 字串轉換為整數列表
        df['numbers_list'] = df['numbers'].apply(lambda x: [int(n) for n in x.split(',')])
        
        # 確保 'ad_date' 是 datetime 格式並排序
        df['ad_date'] = pd.to_datetime(df['ad_date'])
        df = df.sort_values(by='ad_date', ascending=True).reset_index(drop=True)
        
        return df

    def get_latest_n_draws(self, n: int) -> pd.DataFrame:
        """
        獲取最新的 N 期開獎數據。
        """
        if self.df.empty:
            return pd.DataFrame()
        return self.df.tail(n)

    def calculate_frequency(self, num_draws: int = None) -> Dict[int, int]:
        """
        計算指定期數內每個號碼的出現頻率。
        如果 num_draws 為 None，則計算所有期數的頻率。
        """
        target_df = self.df
        if num_draws is not None:
            target_df = self.get_latest_n_draws(num_draws)
        
        if target_df.empty:
            return {}

        all_numbers = [num for sublist in target_df['numbers_list'] for num in sublist]
        frequency = pd.Series(all_numbers).value_counts().sort_index()
        
        # 確保所有號碼 (1-39) 都在結果中，未出現的頻率為 0
        full_range_freq = pd.Series(0, index=range(1, 40))
        full_range_freq.update(frequency)
        
        return full_range_freq.to_dict()

    def calculate_sum_analysis(self, num_draws: int = None) -> Dict[str, Any]:
        """
        計算指定期數內和值的統計分析。
        包括每期和值、平均和值、和值分佈。
        """
        target_df = self.df
        if num_draws is not None:
            target_df = self.get_latest_n_draws(num_draws)
        
        if target_df.empty:
            return {
                'sums': [],
                'mean_sum': None,
                'median_sum': None,
                'std_dev_sum': None,
                'min_sum': None,
                'max_sum': None
            }

        sums = target_df['numbers_list'].apply(sum)
        
        return {
            'sums': sums.tolist(),
            'mean_sum': sums.mean(),
            'median_sum': sums.median(),
            'std_dev_sum': sums.std(),
            'min_sum': sums.min(),
            'max_sum': sums.max()
        }

    def calculate_odd_even_big_small_ratios(self, num_draws: int = None) -> Dict[str, Any]:
        """
        計算指定期數內奇偶比和大小比的統計。
        大小號定義：1-19 為小，20-39 為大。
        """
        target_df = self.df
        if num_draws is not None:
            target_df = self.get_latest_n_draws(num_draws)
        
        if target_df.empty:
            return {
                'odd_even_ratios': [],
                'big_small_ratios': [],
                'odd_even_counts': {},
                'big_small_counts': {}
            }

        odd_even_ratios = []
        big_small_ratios = []
        odd_even_counts = {} # e.g., "3奇2偶": count
        big_small_counts = {} # e.g., "3大2小": count

        for _, row in target_df.iterrows():
            numbers = row['numbers_list']
            
            # 奇偶比
            odd_count = sum(1 for n in numbers if n % 2 != 0)
            even_count = 5 - odd_count
            odd_even_ratios.append(f"{odd_count}:{even_count}")
            odd_even_counts[f"{odd_count}奇{even_count}偶"] = odd_even_counts.get(f"{odd_count}奇{even_count}偶", 0) + 1

            # 大小比 (1-19 小, 20-39 大)
            small_count = sum(1 for n in numbers if 1 <= n <= 19)
            big_count = 5 - small_count
            big_small_ratios.append(f"{big_count}:{small_count}")
            big_small_counts[f"{big_count}大{small_count}小"] = big_small_counts.get(f"{big_count}大{small_count}小", 0) + 1
            
        return {
            'odd_even_ratios': odd_even_ratios,
            'big_small_ratios': big_small_ratios,
            'odd_even_distribution': dict(sorted(odd_even_counts.items())),
            'big_small_distribution': dict(sorted(big_small_counts.items()))
        }

    def analyze_consecutive_numbers(self, num_draws: int = None) -> Dict[str, Any]:
        """
        分析指定期數內的連號情況。
        """
        target_df = self.df
        if num_draws is not None:
            target_df = self.get_latest_n_draws(num_draws)
        
        if target_df.empty:
            return {'consecutive_patterns': {}, 'total_draws_with_consecutive': 0}

        consecutive_patterns = {} # e.g., "12,13": count
        total_draws_with_consecutive = 0

        for _, row in target_df.iterrows():
            numbers = sorted(row['numbers_list']) # 確保已排序
            has_consecutive = False
            for i in range(len(numbers) - 1):
                if numbers[i+1] - numbers[i] == 1:
                    pattern = f"{numbers[i]:02d},{numbers[i+1]:02d}"
                    consecutive_patterns[pattern] = consecutive_patterns.get(pattern, 0) + 1
                    has_consecutive = True
            if has_consecutive:
                total_draws_with_consecutive += 1
                
        return {
            'consecutive_patterns': dict(sorted(consecutive_patterns.items())),
            'total_draws_with_consecutive': total_draws_with_consecutive,
            'percentage_with_consecutive': (total_draws_with_consecutive / len(target_df)) * 100 if len(target_df) > 0 else 0
        }

    def analyze_last_digits(self, num_draws: int = None) -> Dict[int, int]:
        """
        分析指定期數內每個尾數的出現頻率。
        """
        target_df = self.df
        if num_draws is not None:
            target_df = self.get_latest_n_draws(num_draws)
        
        if target_df.empty:
            return {}

        all_last_digits = []
        for numbers in target_df['numbers_list']:
            all_last_digits.extend([n % 10 for n in numbers])
        
        last_digit_frequency = pd.Series(all_last_digits).value_counts().sort_index()
        
        # 確保所有尾數 (0-9) 都在結果中，未出現的頻率為 0
        full_range_freq = pd.Series(0, index=range(0, 10))
        full_range_freq.update(last_digit_frequency)
        
        return full_range_freq.to_dict()

# 範例使用
if __name__ == "__main__":
    # 確保 data_engine.py 已經執行並生成了 lottery_data/lottery_data.csv
    # 如果沒有，請先執行 python data_engine.py
    
    stats_engine = StatsEngine()

    if not stats_engine.df.empty:
        print("--- 今彩539 統計分析報告 ---")
        print(f"總計 {len(stats_engine.df)} 期資料。")

        # 頻率分析
        print("\n--- 號碼頻率分析 (所有期數) ---")
        freq_all = stats_engine.calculate_frequency()
        for num, count in freq_all.items():
            print(f"號碼 {num:02d}: {count} 次")
        
        print("\n--- 號碼頻率分析 (近 30 期) ---")
        freq_30 = stats_engine.calculate_frequency(num_draws=30)
        for num, count in freq_30.items():
            print(f"號碼 {num:02d}: {count} 次")

        # 和值分析
        print("\n--- 和值分析 (所有期數) ---")
        sum_analysis_all = stats_engine.calculate_sum_analysis()
        print(f"平均和值: {sum_analysis_all['mean_sum']:.2f}")
        print(f"中位數和值: {sum_analysis_all['median_sum']:.2f}")
        print(f"和值標準差: {sum_analysis_all['std_dev_sum']:.2f}")
        print(f"最小和值: {sum_analysis_all['min_sum']}")
        print(f"最大和值: {sum_analysis_all['max_sum']}")

        # 奇偶/大小比分析
        print("\n--- 奇偶/大小比分析 (所有期數) ---")
        ratios_all = stats_engine.calculate_odd_even_big_small_ratios()
        print("奇偶比分佈:")
        for pattern, count in ratios_all['odd_even_distribution'].items():
            print(f"  {pattern}: {count} 次")
        print("大小比分佈:")
        for pattern, count in ratios_all['big_small_distribution'].items():
            print(f"  {pattern}: {count} 次")
            
        # 連號分析
        print("\n--- 連號分析 (所有期數) ---")
        consecutive_analysis_all = stats_engine.analyze_consecutive_numbers()
        print(f"總共有 {consecutive_analysis_all['total_draws_with_consecutive']} 期出現連號 ({consecutive_analysis_all['percentage_with_consecutive']:.2f}%)")
        print("連號模式分佈:")
        for pattern, count in consecutive_analysis_all['consecutive_patterns'].items():
            print(f"  {pattern}: {count} 次")

        # 尾數分析
        print("\n--- 尾數頻率分析 (所有期數) ---")
        last_digits_all = stats_engine.analyze_last_digits()
        for digit, count in last_digits_all.items():
            print(f"尾數 {digit}: {count} 次")
            
    else:
        print("無法進行統計分析，因為沒有載入任何資料。\n")
