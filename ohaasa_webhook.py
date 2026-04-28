import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import os

# 1. 설정
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
TARGET_URL = "https://www.asahi.co.jp/ohaasa/week/horoscope/index.html"

# 별자리 번역 (데이터 누락 방지용)
SIGN_TRANSLATE = {
    "うお座": "물고기자리", "やぎ座": "염소자리", "さそり座": "전갈자리",
    "おとめ座": "처녀자리", "おうし座": "황소자리", "かに座": "게자리",
    "おひつじ座": "양자리", "みず가め座": "물병자리", "みずがめ座": "물병자리",
    "いて座": "사수자리", "てんびん座": "천칭자리", "ふたご座": "쌍둥이자리", "しし座": "사자자리"
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
            # 랭킹 추출
            rank_el = item.select_one('.horo_rank')
            if not rank_el: continue
            rank = rank_el.text.strip()

            # 별자리 이름 추출 (HTML상의 'sapn' 오타와 일반 'span' 모두 대응)
            name_tag = item.select_one('.horo_name') or item.select_one('sapn') or item.select_one('span:not(.horo_rank)')
            raw_sign = name_tag.text.strip() if name_tag else "알 수 없음"
            
            # 상세 내용 추출
            detail_el = item.select_one('.horo_txt')
            detail = detail_el.text.strip().replace('\t', ' ') if detail_el else ""

            results.append({
                "rank": rank,
                "sign": SIGN_TRANSLATE.get(raw_sign, raw_sign),
                "detail": detail
            })
        return results
    except Exception as e:
        print(f"데이터 추출 중 에러: {e}")
        return None

def send_to_discord(fortunes):
    if not fortunes or not WEBHOOK_URL:
        print("데이터가 없거나 웹훅 URL이 설정되지 않았습니다.")
        return

    # 한국 시간 설정
    kst = timezone(timedelta(hours=9))
    today_str = datetime.now(kst).strftime("%Y년 %m월 %d일")
    
    # 1~3위와 나머지를 분리하거나 전체를 깔끔하게 임베드로 구성
    embed = {
        "title": f"☀️ {today_str} 오하아사 별자리 운세",
        "description": "오늘의 운세 순위입니다.",
        "url": TARGET_URL,
        "color": 16766720,
        "fields": []
    }
    
    for f in fortunes:
        medal = "🥇" if f['rank'] == '1' else "🥈" if f['rank'] == '2' else "🥉" if f['rank'] == '3' else "🔹"
        embed["fields"].append({
            "name": f"{medal} {f['rank']}위: {f['sign']}",
            "value": f"{f['detail']}",
            "inline": False
        })

    payload = {"embeds": [embed]}
    res = requests.post(WEBHOOK_URL, json=payload)
    print(f"전송 결과: {res.status_code}")

if __name__ == "__main__":
    data = get_fortune_data()
    send_to_discord(data)
