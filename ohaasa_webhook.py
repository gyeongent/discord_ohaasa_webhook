import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import os

# --- [설정 영역] ---
# GitHub Secrets를 사용할 경우 os.environ.get 사용, 로컬 테스트 시 직접 URL 입력
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
TARGET_URL = "https://www.asahi.co.jp/ohaasa/week/horoscope/index.html"

SIGN_TRANSLATE = {
    "うお座": "물고기자리", "やぎ座": "염소자리", "さそり座": "전갈자리",
    "おとめ座": "처녀자리", "おうし座": "황소자리", "かに座": "게자리",
    "おひつじ座": "양자리", "みずがめ座": "물병자리", "いて座": "사수자리",
    "てん비ん座": "천칭자리", "てんびん座": "천칭자리", "ふたご座": "쌍둥이자리", "しし座": "사자자리"
}

def get_fortune_data():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('.oa_horoscope_list li')
        
        results = []
        for item in items:
            rank = item.select_one('.horo_rank').text.strip()
            name_tag = item.select_one('.horo_name') or item.select_one('sapn') or item.select_one('span:not(.horo_rank)')
            raw_sign = name_tag.text.strip()
            detail = item.select_one('.horo_txt').text.strip()
            
            results.append({
                "rank": rank,
                "sign": SIGN_TRANSLATE.get(raw_sign, raw_sign),
                "detail": detail
            })
        return results
    except Exception as e:
        print(f"추출 에러: {e}")
        return None

def send_to_discord(fortunes):
    if not fortunes: return
    kst = timezone(timedelta(hours=9))
    today_str = datetime.now(kst).strftime("%Y년 %m월 %d일")
    
    embed = {
        "title": f"☀️ {today_str} 오하아사 운세",
        "url": TARGET_URL,
        "color": 16766720,
        "fields": []
    }
    
    for f in fortunes:
        medal = "🥇" if f['rank'] == '1' else "🥈" if f['rank'] == '2' else "🥉" if f['rank'] == '3' else "🔹"
        embed["fields"].append({
            "name": f"{medal} {f['rank']}위: {f['sign']}",
            "value": f"💬 {f['detail']}",
            "inline": False
        })

    payload = {"embeds": [embed]}
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    data = get_fortune_data()
    if data:
        send_to_discord(data)
