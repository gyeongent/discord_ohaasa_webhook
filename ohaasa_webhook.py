import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import os

# --- [설정 영역] ---
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
TARGET_URL = "https://www.asahi.co.jp/ohaasa/week/horoscope/index.html"

SIGN_TRANSLATE = {
    "うお座": "물고기자리", "やぎ座": "염소자리", "さそり座": "전갈자리",
    "おとめ座": "처녀자리", "おうし座": "황소자리", "かに座": "게자리",
    "おひつじ座": "양자리", "みずが메座": "물병자리", "みず가め座": "물병자리", "みずがめ座": "물병자리",
    "いて座": "사수자리", "てんびん座": "천칭자리", "ふたご座": "쌍둥이자리", "しし座": "사자자리"
}

def get_fortune_data():
    # 💡 브라우저처럼 보이게 헤더 강화
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6",
        "Referer": "https://www.asahi.co.jp/ohaasa/",
    }
    
    try:
        # 세션을 사용하여 접속 유지
        session = requests.Session()
        response = session.get(TARGET_URL, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"로그: 접속 실패 코드 {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1차 시도: 제공된 클래스명 기반
        items = soup.select('.oa_horoscope_list li')
        
        # 2차 시도: 클래스명이 rank로 시작하는 모든 li 탐색
        if not items:
            items = soup.find_all('li', class_=lambda x: x and 'rank' in x)
            
        print(f"로그: 추출된 원본 아이템 개수 = {len(items)}")

        results = []
        for item in items:
            # 순위 찾기
            rank_el = item.select_one('.horo_rank') or item.find(class_='horo_rank')
            if not rank_el: continue
            rank = rank_el.text.strip()

            # 별자리 이름 (오타 sapn 및 span 대응)
            name_tag = item.select_one('.horo_name') or item.select_one('sapn') or item.select_one('span:not(.horo_rank)')
            if not name_tag: continue
            raw_sign = name_tag.text.strip()
            
            # 운세 내용
            detail_el = item.select_one('.horo_txt') or item.find('dd')
            detail = detail_el.text.strip().replace('\t', ' ') if detail_el else ""

            results.append({
                "rank": rank,
                "sign": SIGN_TRANSLATE.get(raw_sign, raw_sign),
                "detail": detail
            })
            
        return results
    except Exception as e:
        print(f"로그: 에러 발생 = {e}")
        return None

def send_to_discord(fortunes):
    if not WEBHOOK_URL:
        print("로그: 웹훅 URL이 없습니다.")
        return
    if not fortunes:
        print("로그: 보낼 데이터가 비어있습니다.")
        return

    kst = timezone(timedelta(hours=9))
    today_str = datetime.now(kst).strftime("%Y년 %m월 %d일")
    
    # 순위 정렬
    fortunes.sort(key=lambda x: int(x['rank']) if x['rank'].isdigit() else 99)

    embed = {
        "title": f"☀️ {today_str} 오하아사 별자리 운세",
        "description": f"아사히 방송 '굿!모닝' 운세입니다.\n[공
