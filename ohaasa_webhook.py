import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import os
import re

# --- [설정 영역] ---
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
TARGET_URL = "https://www.asahi.co.jp/ohaasa/week/horoscope/index.html"

SIGN_TRANSLATE = {
    "うお座": "물고기자리", "やぎ座": "염소자리", "さそり座": "전갈자리",
    "おとめ座": "처녀자리", "おう시座": "황소자리", "おうし座": "황소자리", "かに座": "게자리",
    "おひつじ座": "양자리", "みずがめ座": "물병자리", "いて座": "사수자리",
    "てんびん座": "천칭자리", "ふたご座": "쌍둥이자리", "しし座": "사자자리"
}

def get_fortune_data():
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja-JP,ja;q=0.9",
    }
    
    try:
        # 💡 모바일 페이지 레이아웃 시도 (차단 우회 확률 높음)
        response = requests.get(TARGET_URL, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        
        if "403 Forbidden" in response.text or response.status_code == 403:
            print("로그: 서버에서 봇 접속을 차단했습니다(403).")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 💡 랭킹 박스 자체를 먼저 찾고 그 안의 li를 검색
        container = soup.find('ul', class_='oa_horoscope_list') or soup.find('div', class_='horoscope_box')
        if container:
            items = container.find_all('li')
        else:
            # 컨테이너가 없으면 모든 li 중 rank 클래스가 있는 것 검색
            items = soup.find_all('li', class_=re.compile(r'rank'))

        print(f"로그: 최종 시도 아이템 개수 = {len(items)}")

        results = []
        for item in items:
            # 순위 (텍스트가 없으면 클래스명에서 숫자 추출)
            rank_el = item.find(class_='horo_rank')
            if rank_el:
                rank = rank_el.text.strip()
            else:
                class_names = "".join(item.get('class', []))
                match = re.search(r'rank(\d+)', class_names)
                rank = match.group(1) if match else "0"

            # 별자리 이름
            name_tag = item.find(class_='horo_name') or item.find('sapn') or item.find('span')
            if not name_tag: continue
            raw_sign = name_tag.text.strip()
            
            # 내용
            detail_el = item.find(class_='horo_txt') or item.find('dd')
            detail = detail_el.text.strip() if detail_el else ""

            if rank != "0":
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
        print("로그: 웹훅 URL 없음")
        return
    if not fortunes:
        # 💡 실패 시 관리자에게 알림을 주도록 설정 (선택 사항)
        print("로그: 추출 실패 - 사이트 구조 변경 혹은 차단됨")
        return

    kst = timezone(timedelta(hours=9))
    today_str = datetime.now(kst).strftime("%Y년 %m월 %d일")
    
    # 중복 제거 및 정렬
    unique_fortunes = {f['rank']: f for f in fortunes}.values()
    sorted_fortunes = sorted(unique_fortunes, key=lambda x: int(x['rank']))

    embed = {
        "title": f"☀️ {today_str} 오하아사 운세",
        "url": TARGET_URL,
        "color": 16766720,
        "fields": []
    }
    
    for f in sorted_fortunes:
        medal = "🥇" if f['rank'] == '1' else "🥈" if f['rank'] == '2' else "🥉" if f['rank'] == '3' else "🔹"
        embed["fields"].append({
            "name": f"{medal} {f['rank']}위: {f['sign']}",
            "value": f"{f['detail']}",
            "inline": False
        })

    requests.post(WEBHOOK_URL, json={"embeds": [embed]})
    print("로그: 디스코드 전송 시도 완료")

if __name__ == "__main__":
    data = get_fortune_data()
    send_to_discord(data)
