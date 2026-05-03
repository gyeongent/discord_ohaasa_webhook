const puppeteer = require('puppeteer');
const axios = require('axios');

const SIGN_TRANSLATE = {
    'おひつじ座': '양자리', 'おうし座': '황소자리', 'ふたご座': '쌍둥이자리',
    'かに座': '게자리', 'しし座': '사자자리', 'おとめ座': '처녀자리',
    'てんびん座': '천칭자리', 'さそり座': '전갈자리', 'いて座': '사수자리',
    'やぎ座': '염소자리', 'みずがめ座': '물병자리', 'うお座': '물고기자리',
    '牡羊座': '양자리', '牡牛座': '황소자리', '双子座': '쌍둥이자리',
    '蟹座': '게자리', '獅子座': '사자자리', '乙女座': '처녀자리',
    '天秤座': '천칭자리', '蠍座': '전갈자리', '射手座': '사수자리',
    '山羊座': '염소자리', '水瓶座': '물병자리', '魚座': '물고기자리'
};

async function run() {
    const now = new Date();
    // 한국 시간 기준 요일 계산
    const kstNow = new Date(now.getTime() + (9 * 60 * 60 * 1000));
    const dayOfWeek = kstNow.getDay(); 
    const isWeekend = (dayOfWeek === 0 || dayOfWeek === 6);

    const TARGET_URL = isWeekend 
        ? 'https://www.tv-asahi.co.jp/goodmorning/uranai/' 
        : 'https://www.asahi.co.jp/ohaasa/week/horoscope/';

    console.log(`[1] 모드 확인: ${isWeekend ? '주말' : '평일'}`);
    console.log(`[2] 접속 URL: ${TARGET_URL}`);

    const browser = await puppeteer.launch({
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage();

    try {
        await page.goto(TARGET_URL, { waitUntil: 'networkidle2', timeout: 60000 });
        console.log(`[3] 페이지 로드 완료`);

        const fortunes = await page.evaluate((isWeekend, signMap) => {
            const results = [];
            if (isWeekend) {
                // 주말 사이트 구조 강화 (li와 dl 모두 탐색)
                const items = document.querySelectorAll('.rank-box li, .rank-box dl');
                items.forEach((li, index) => {
                    const signTag = li.querySelector('span, dt, .name');
                    const rawSign = signTag ? signTag.innerText.trim() : "";
                    if (rawSign) {
                        results.push({
                            rank: index + 1,
                            sign: signMap[rawSign] || rawSign,
                            content: "행운의 아이템 등 상세 정보는 사이트를 확인하세요!"
                        });
                    }
                });
            } else {
                const items = document.querySelectorAll('.oa_horoscope_list li');
                items.forEach((li) => {
                    const rank = li.querySelector('.horo_rank')?.innerText || "";
                    const rawSign = li.querySelector('sapn.horo_name')?.innerText || "";
                    const content = li.querySelector('.horo_txt')?.innerText || "";
                    if (rawSign) {
                        results.push({
                            rank: parseInt(rank),
                            sign: signMap[rawSign] || rawSign,
                            content: content.trim().replace(/\s+/g, ' ')
                        });
                    }
                });
            }
            return results;
        }, isWeekend, SIGN_TRANSLATE);

        console.log(`[4] 데이터 수집 개수: ${fortunes.length}개`);

        if (fortunes.length > 0) {
            console.table(fortunes);
            await sendDiscord(fortunes, TARGET_URL, isWeekend, kstNow);
        } else {
            console.log("❌ [경고] 수집된 데이터가 0개입니다. 선택자를 확인해야 합니다.");
        }

    } catch (e) {
        console.error("❌ [에러] 실행 중 오류 발생:", e.message);
    } finally {
        await browser.close();
        console.log("[6] 브라우저 종료");
    }
}

async function sendDiscord(fortunes, url, isWeekend, date) {
    const WEBHOOK_URL = process.env.DISCORD_WEBHOOK;
    
    if (!WEBHOOK_URL) {
        console.log("⚠️ [경고] DISCORD_WEBHOOK 환경변수가 없습니다.");
        return;
    }

    console.log(`[5] 디스코드 전송 시도 중...`);

    const todayTag = `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`;
    let description = "";
    fortunes.slice(0, 12).forEach(f => {
        const medal = f.rank === 1 ? "🥇" : f.rank === 2 ? "🥈" : f.rank === 3 ? "🥉" : "🔹";
        description += `${medal} **${f.rank}위**: ${f.sign}\n${isWeekend ? '' : `> ${f.content}`}`;
    });

    try {
        await axios.post(WEBHOOK_URL, {
            embeds: [{
                title: `✨ ${todayTag} ${isWeekend ? '굿!모닝' : '오하아사'} 별자리 운세`,
                url: url,
                description: description,
                color: isWeekend ? 16766720 : 5814783,
                timestamp: new Date()
            }]
        });
        console.log("✅ 디스코드 전송 완료!");
    } catch (error) {
        console.error("❌ [디스코드 전송 에러]:", error.response ? error.response.status : error.message);
    }
}

run();
