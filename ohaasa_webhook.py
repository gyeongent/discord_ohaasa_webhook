import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import os

# --- [설정 영역] ---
# GitHub Secrets에서 가져오되, 실패 시 None
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
TARGET_URL = "https://www.asahi.co.jp/ohaasa/week/horoscope/index.html"

# 별자리 번역 딕셔너리 (웹사이트 원문 오타 대응)
SIGN_TRANSLATE = {
    "うお座": "물고기자리", "やぎ座": "염소자리", "さそり座": "전갈자리",
    "おとめ座": "처녀자리", "おうし座": "황소자리", "かに座": "게자리",
    "おひつじ座": "양자리", "みずがめ座": "물병자리", "いて座": "사수자리",
    "てんびん座": "천칭자리", "ふたご座": "쌍둥이자리", "しし座": "사자자리"
}

def get_fortune_data():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 제공하신 클래스 .oa_horoscope_list 내의 li 추출
        items = soup.select('.oa_horoscope_list li')
        print(f"로그: 찾은 아이템 개수 = {len(items)}") # 디버깅용 로그

        results = []
        for item in items:
            rank_el = item.select_one('.horo_rank')
            if not rank_el: continue
            
            rank = rank_el.text.strip()
            # sapn 또는 span 모두 찾기
            name_tag = item.select_one('.horo_name') or item.select_one('sapn') or item.select_one('span:not(.horo_rank)')
            raw_sign = name_tag.text.strip() if name_tag else "미확인"
            
            detail_el = item.select_one('.horo_txt')
            detail = detail_el.text.strip().replace('\t', ' ') if detail_el else "내용 없음"

            results.append({
                "rank": rank,
                "sign": SIGN_TRANSLATE.get(raw_sign, raw_sign),
                "detail": detail
            })
        return results
    except Exception as e:
        print(f"로그: 크롤링 중 에러 발생 = {e}")
        return None

def send_to_discord(fortunes):
    # 상세 디버깅 로그
    if not WEBHOOK_URL:
        print("로그: 에러 - DISCORD_WEBHOOK 환경변수가 비어있습니다. GitHub Secrets를 확인하세요.")
        return
    if not fortunes:
        print("로그: 에러 - 추출된 운세 데이터가 없습니다. TARGET_URL 구조를 확인하세요.")
        return

    kst = timezone(timedelta(hours=9))
    today_str = datetime.now(kst).strftime("%Y년 %m월 %d일")
    
    embed = {
        "title": f"☀️ {today_str} 오하아사 별자리 운세",
        "description": "오늘의 운세 순위입니다.",
        "url": TARGET_URL,
        "color": 16766720,
        "fields": []
    }
    
    # 디스코드 글자수 제한 방지를 위해 상위 12개만
    for f in fortunes[:12]:
        medal = "🥇" if f['rank'] == '1' else "🥈" if f['rank'] == '2' else "🥉" if f['rank'] == '3' else "🔹"
        embed["fields"].append({
            "name": f"{medal} {f['rank']}위: {f['sign']}",
            "value": f"{f['detail']}",
            "inline": False
        })

    payload = {"embeds": [embed]}
    res = requests.post(WEBHOOK_URL, json=payload)
    print(f"로그: 전송 시도 결과 코드 = {res.status_code}")

if __name__ == "__main__":
    data = get_fortune_data()
    send_to_discord(data)
