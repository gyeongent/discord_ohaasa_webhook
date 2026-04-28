import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import os

# --- [설정 영역] ---
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
# 아사히 방송의 주간 운세 페이지
TARGET_URL = "https://www.asahi.co.jp/ohaasa/week/horoscope/index.html"

SIGN_TRANSLATE = {
    "うお座": "물고기자리", "やぎ座": "염소자리", "さそ리座": "전갈자리", "さそり座": "전갈자리",
    "おとめ座": "처녀자리", "おうし座": "황소자리", "かに座": "게자리",
    "おひつじ座": "양자리", "みずがめ座": "물병자리", "いて座": "사수자리",
    "てんびん座": "천칭자리", "ふたご座": "쌍둥이자리", "しし座": "사자자리"
}

def get_fortune_data():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        # 1. 페이지를 제대로 가져왔는지 확인
        if response.status_code != 200:
            print(f"로그: 사이트 접속 실패 (상태코드: {response.status_code})")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. 모든 <li> 태그 중에서 rank가 포함된 클래스를 가진 것들을 다 찾음
        items = soup.find_all('li', class_=lambda x: x and 'rank' in x)
        
        # 만약 위 방법으로 실패하면 다른 패턴 시도
        if not items:
            items = soup.select('.oa_horoscope_list li')

        print(f"로그: 찾은 아이템 개수 = {len(items)}")

        results = []
        for item in items:
            try:
                # 순위 추출
                rank_el = item.find(class_='horo_rank') or item.find('span')
                rank = rank_el.text.strip() if rank_el else "0"

                # 별자리 이름 (sapn 오타 및 일반 span 대응)
                name_tag = item.find(class_='horo_name') or item.find('sapn') or item.find('span', class_=None)
                raw_sign = name_tag.text.strip() if name_tag else "알수없음"
                
                # 운세 내용
                detail_el = item.find(class_='horo_txt') or item.find('dd')
                detail = detail_el.text.strip().replace('\t', ' ') if detail_el else ""

                if raw_sign != "알수없음":
                    results.append({
                        "rank": rank,
                        "sign": SIGN_TRANSLATE.get(raw_sign, raw_sign),
                        "detail": detail
                    })
            except:
                continue
                
        # 순위 숫자로 정렬 (데이터가 뒤섞여 나올 경우 대비)
        results.sort(key=lambda x: int(x['rank']) if x['rank'].isdigit() else 99)
        return results

    except Exception as e:
        print(f"로그: 에러 발생 = {e}")
        return None

def send_to_discord(fortunes):
    if not WEBHOOK_URL:
        print("로그: DISCORD_WEBHOOK이 설정되지 않았습니다.")
        return
    if not fortunes:
        print("로그: 전송할 데이터가 없습니다.")
        return

    kst = timezone(timedelta(hours=9))
    today_str = datetime.now(kst).strftime("%Y년 %m월 %d일")
    
    embed = {
        "title": f"☀️ {today_str} 오하아사 별자리 운세",
        "description": f"[운세 페이지 바로가기]({TARGET_URL})",
        "color": 16766720,
        "fields": []
    }
    
    for f in fortunes[:12]:
        medal = "🥇" if f['rank'] == '1' else "🥈" if f['rank'] == '2' else "🥉" if f['rank'] == '3' else "🔹"
        embed["fields"].append({
            "name": f"{medal} {f['rank']}위: {f['sign']}",
            "value": f"{f['detail']}",
            "inline": False
        })

    payload = {"embeds": [embed]}
    res = requests.post(WEBHOOK_URL, json=payload)
    print(f"로그: 최종 전송 결과 코드 = {res.status_code}")

if __name__ == "__main__":
    data = get_fortune_data()
    send_to_discord(data)
