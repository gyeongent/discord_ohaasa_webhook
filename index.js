const puppeteer = require('puppeteer');
const axios = require('axios');

// 별자리 번역 매핑
const signMap = {
    'おひつじ座': '양자리', 'おうし座': '황소자리', 'ふたご座': '쌍둥이자리',
    'かに座': '게자리', 'しし座': '사자자리', 'おとめ座': '처녀자리',
    'てんびん座': '천칭자리', 'さそり座': '전갈자리', 'いて座': '사수자리',
    'やぎ座': '염소자리', 'みずがめ座': '물병자리', 'うお座': '물고기자리'
};

async function run() {
    console.log("🚀 크롤링을 시작합니다...");
    
    const browser = await puppeteer.launch({
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    
    const page = await browser.newPage();

    try {
        await page.goto('https://www.asahi.co.jp/ohaasa/week/horoscope/', { 
            waitUntil: 'networkidle2',
            timeout: 60000 
        });

        const data = await page.evaluate((signMap) => {
            // 사이트에 표시된 실제 날짜 텍스트 (예: 2026.04.28)
            const dateText = document.querySelector('.oa_horoscope_date')?.innerText.trim() || 
                             document.querySelector('.date')?.innerText.trim() || 
                             new Date().toLocaleDateString();
            
            const list = [];
            // ul.oa_horoscope_list 구조 내부 파싱
            document.querySelectorAll('.oa_horoscope_list li').forEach((item) => {
                const rank = item.querySelector('.horo_rank')?.innerText || "";
                const rawSign = item.querySelector('sapn.horo_name')?.innerText || "";
                const content = item.querySelector('.horo_txt')?.innerText || "";
                
                if (rawSign) {
                    list.push({ 
                        rank: rank + "위", 
                        sign: signMap[rawSign] || rawSign, 
                        content: content.trim().replace(/\s+/g, ' ') 
                    });
                }
            });
            return { dateText, list };
        }, signMap);

        // --- GitHub Actions 로그 출력용 ---
        console.log(`\n📅 [사이트 기준 날짜: ${data.dateText}]`);
        console.log(`🕒 [수집 시각: ${new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })}]`);
        
        if (data.list.length === 0) {
            console.log("❌ 수집된 데이터가 없습니다. 사이트 구조를 확인하세요.");
        } else {
            console.table(data.list); // 로그에서 표 형태로 확인 가능
        }
        // -----------------------------

        // 디스코드 전송 로직
        const WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL;
        if (data.list.length > 0 && WEBHOOK_URL) {
            const description = data.list.map(i => `**${i.rank}: ${i.sign}**\n${i.content}`).join('\n');
            
            await axios.post(WEBHOOK_URL, {
                embeds: [{
                    title: `🔮 오하아사 별자리 운세 (${data.dateText})`,
                    description: description,
                    color: 5814783,
                    timestamp: new Date()
                }]
            });
            console.log("✅ 디스코드 웹훅 전송 성공!");
        } else if (!WEBHOOK_URL) {
            console.log("⚠️ DISCORD_WEBHOOK_URL 환경변수가 설정되지 않았습니다. 전송을 건너뜁니다.");
        }

    } catch (e) {
        console.error("❌ 실행 오류 발생:", e.message);
        process.exit(1); // 에러 발생 시 GitHub Actions에 실패 알림
    } finally {
        await browser.close();
        console.log("종료합니다.");
    }
}

run();
