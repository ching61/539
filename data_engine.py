import requests
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import urllib3

# Disable SSL warnings globally as per the original script's approach
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DailyCashCrawler:
    """今彩539資料爬蟲類別"""
    
    def __init__(self):
        self.base_url = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.verify = False # Ignore SSL certificate verification
    
    def crawl_daily_cash(self, year_month: str, page_num: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """爬取今彩539資料"""
        url = f"{self.base_url}/Daily539Result"
        params = {
            'month': year_month,
            'pageNum': page_num,
            'pageSize': page_size
        }
        
        try:
            print(f"正在爬取今彩539資料: {year_month}, 頁數: {page_num}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('rtCode') == 0:
                return data.get('content', {})
            else:
                print(f"API 錯誤: {data.get('rtMsg', '未知錯誤')}")
                return {}
                
        except requests.exceptions.RequestException as e:
            print(f"請求今彩539資料失敗: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"解析今彩539 JSON 失敗: {e}")
            return {}
    
    def process_daily_cash_data(self, raw_data: List[Dict]) -> List[Dict]:
        """處理今彩539資料格式，返回列表以便於轉換為DataFrame"""
        processed_list = []
        
        for item in raw_data:
            try:
                lottery_date_str = item['lotteryDate'].replace('T00:00:00', '')
                lottery_date = datetime.fromisoformat(lottery_date_str)
                tw_year = lottery_date.year - 1911
                
                period = str(item['period'])
                
                draw_numbers = item['drawNumberAppear']
                numbers = sorted(draw_numbers[:5])
                
                processed_list.append({
                    'draw': period,
                    'date': f"{tw_year}/{lottery_date.month:02d}/{lottery_date.day:02d}",
                    'ad_date': lottery_date.strftime('%Y-%m-%d'), # For sorting and internal use
                    'numbers': ','.join(f"{n:02d}" for n in numbers), # Format as "01,02,03,04,05"
                    'price': 8000000,
                    'lottery_type': 'daily_cash'
                })
                
            except (KeyError, ValueError, IndexError) as e:
                print(f"處理今彩539資料錯誤: {e}, 項目: {item}")
                continue
        
        return processed_list
    
    def get_existing_data_df(self, filepath: str) -> pd.DataFrame:
        """讀取現有CSV資料為DataFrame"""
        if os.path.exists(filepath):
            try:
                df = pd.read_csv(filepath, dtype={'draw': str}) # Ensure 'draw' is read as string
                # Convert 'ad_date' back to datetime for proper comparison
                df['ad_date'] = pd.to_datetime(df['ad_date'])
                return df
            except Exception as e:
                print(f"讀取現有CSV資料失敗: {e}")
                return pd.DataFrame()
        return pd.DataFrame()
    
    def get_latest_ad_date(self, df: pd.DataFrame) -> datetime:
        """從DataFrame中找到最新日期 (AD calendar)"""
        if not df.empty and 'ad_date' in df.columns:
            return df['ad_date'].max().to_pydatetime() # Convert Timestamp to datetime.datetime
        return None
    
    def crawl_and_save_daily_cash(self, start_year: int = 2014, start_month: int = 1):
        """智能爬取今彩539資料並儲存到CSV"""
        output_dir = 'lottery_data'
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, 'lottery_data.csv')
        
        existing_df = self.get_existing_data_df(filepath)
        latest_date_ad = self.get_latest_ad_date(existing_df)
        
        current_date = datetime.now()
        
        if latest_date_ad:
            # 從最新資料的月份開始爬取（確保不遺漏）
            start_crawl_date = latest_date_ad.replace(day=1)
            print(f"📊 檢測到現有資料，最新日期: {latest_date_ad.strftime('%Y-%m-%d')}")
            print(f"🎯 增量更新：從 {start_crawl_date.strftime('%Y-%m')} 開始爬取新資料")
        else:
            start_crawl_date = datetime(start_year, start_month, 1)
            print(f"🆕 首次爬取今彩539資料，從 {start_year}-{start_month:02d} 開始")
        
        all_new_records = []
        new_count = 0
        
        current_month_iter = start_crawl_date
        while current_month_iter <= current_date:
            year_month = f"{current_month_iter.year}-{current_month_iter.month:02d}"
            
            try:
                raw_content = self.crawl_daily_cash(year_month)
                if raw_content and 'daily539Res' in raw_content:
                    processed_list = self.process_daily_cash_data(raw_content['daily539Res'])
                    
                    for record in processed_list:
                        # Only add if it's newer than the latest existing record
                        # Or if there's no existing data
                        if latest_date_ad is None or datetime.fromisoformat(record['ad_date']) > latest_date_ad:
                            all_new_records.append(record)
                            new_count += 1
                    
                    if processed_list: # Only print if there was data for the month
                        print(f"✅ {year_month}: 處理了 {len(processed_list)} 筆資料")
                
                time.sleep(1) # Avoid frequent requests
                
            except Exception as e:
                print(f"❌ 爬取 {year_month} 失敗: {e}")
            
            # Move to the next month
            if current_month_iter.month == 12:
                current_month_iter = current_month_iter.replace(year=current_month_iter.year + 1, month=1)
            else:
                current_month_iter = current_month_iter.replace(month=current_month_iter.month + 1)
        
        if all_new_records:
            new_df = pd.DataFrame(all_new_records)
            
            # Combine existing and new data, remove duplicates based on 'draw' and sort by 'ad_date'
            combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['draw'])
            
            # CRITICAL FIX: Ensure 'ad_date' column is uniformly datetime before sorting
            combined_df['ad_date'] = pd.to_datetime(combined_df['ad_date'])
            
            # Now sort
            combined_df = combined_df.sort_values(by='ad_date').reset_index(drop=True)
            
            # Save to CSV
            combined_df.to_csv(filepath, index=False, encoding='utf-8')
            print(f"\n🎉 今彩539資料更新完成！")
            print(f"📈 本次新增 {new_count} 筆記錄，總計 {len(combined_df)} 筆")
            print(f"✅ 資料已儲存到: {filepath}")
        elif not existing_df.empty:
            print(f"\n🎉 今彩539資料已是最新，無需更新。總計 {len(existing_df)} 筆記錄")
        else:
            print(f"\n⚠️ 未能獲取任何今彩539資料。")

def main():
    crawler = DailyCashCrawler()
    crawler.crawl_and_save_daily_cash()

if __name__ == "__main__":
    main()
