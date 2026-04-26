import requests
from bs4 import BeautifulSoup
import datetime
import os

# 1. 설정
TARGET_URL = "https://www.tv-asahi.co.jp/goodmorning/uranai/"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

# 별자리 한글 번역 딕셔너리
SIGN_TRANSLATE = {
    "おうし座": "황소자리", "おとめ座": "처녀자리", "야기座": "염소자리", # 원문 확인 필요
    "やぎ座": "염소자리", "かに座": "게자리", "さそ리座": "전갈자리", 
    "さそり座": "전갈자리", "うお座": "물고기자리", "てんびん座": "천칭자리", 
    "しし座": "사자자리", "みずがめ座": "물병자리", "いて座": "사수자리", 
    "おひつじ座": "양자리", "ふたご座": "쌍둥이자리"
}

def get_fortune_data():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # TARGET_URL을 함수 내부에서도 인식할 수 있도록 처리
        response = requests.get(TARGET_URL, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 제공해주신 rank-box 구조 기반 추출
        rank_list = soup.select('.rank-box li')
        
        if not rank_list:
            print("데이터를 찾을 수 없습니다. 클래스 명을 확인해 주세요.")
            return None

        results = []
        for index, li in enumerate(rank_list, start=1):
            span_tag = li.select_one('span')
            if span_tag:
                raw_sign = span_tag.text.strip()
                ko_sign = SIGN_TRANSLATE.get(raw_sign, raw_sign)
                results.append({
                    "rank": index,
                    "sign": ko_sign
                })
        return results
    except Exception as e:
        print(f"데이터 추출 중 에러 발생: {e}")
        return None

def send_to_discord(fortunes):
    if not fortunes:
        print("전송할 데이터가 없습니다.")
        return

    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    
    description = ""
    for f in fortunes:
        medal = "🥇" if f['rank'] == 1 else "🥈" if f['rank'] == 2 else "🥉" if f['rank'] == 3 else "🔹"
        description += f"{medal} **{f['rank']}위**: {f['sign']}\n"

    payload = {
        "embeds": [{
            "title": f"✨ {today} 오하아사 별자리 운세 순위",
            "url": TARGET_URL,
            "description": description,
            "color": 16766720,
            "footer": {"text": "TV 아사히 굿!모닝 운세 기반"}
        }]
    }

    res = requests.post(WEBHOOK_URL, json=payload)
    if res.status_code == 204:
        print("디스코드로 전송 완료!")
    else:
        print(f"디스코드 전송 실패: {res.status_code}")

if __name__ == "__main__":
    data = get_fortune_data()
    if data:
        send_to_discord(data)
