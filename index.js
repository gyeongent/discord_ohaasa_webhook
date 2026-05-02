const puppeteer = require('puppeteer');
const axios = require('axios');

// 별자리 번역 매핑
const SIGN_TRANSLATE = {
    'おひつじ座': '양자리', 'おうし座': '황소자리', 'ふたご座': '쌍둥이자리',
    'かに座': '게자리', 'しし座': '사자자리', 'おとめ座': '처녀자리',
    'てんびん座': '천칭자리', 'さそり座': '전갈자리', 'いて座': '사수자리',
    'やぎ座': '염소자리', 'みずがめ座': '물병자리', 'うお座': '물고기자리',
    // tv-asahi는 이름이 짧게 나올 수 있어 추가 대응
    '牡羊座': '양자리', '牡牛座': '황소자리', '双子座': '쌍둥이자리',
    '蟹座': '게자리', '獅子座': '사자자리', '乙女座': '처녀자리',
    '天秤座': '천칭자리', '蠍座': '전갈자리', '射手座': '사수자리',
    '山羊座': '염소자리', '水瓶座': '물병자리', '魚座': '물고기자리'
};

async function run() {
    const now = new Date();
    // 한국 시간(KST) 기준으로 요일 계산 (GitHub Actions 서버 시간 대응)
    const kstNow = new Date(now.getTime() + (9 * 60 * 60 * 1000));
    const dayOfWeek = kstNow.getDay(); // 0: 일, 6: 토
    const isWeekend = (dayOfWeek === 0 || dayOfWeek === 6);

    // 평일/주말 타겟 설정
    const TARGET_URL = isWeekend 
        ? 'https://www.tv-asahi.co.jp/goodmorning/uranai/' 
        : 'https://www.asahi.co.jp/ohaasa/week/horoscope/';

    console.log(`🚀 ${isWeekend ? '주말(굿!모닝)' : '평일(오하아사)'} 모드 시작: ${TARGET_URL}`);

    const browser = await puppeteer.launch({
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage();

    try {
        await page.goto(TARGET_URL, { waitUntil: 'networkidle2', timeout: 60000 });

        const fortunes = await page.evaluate((isWeekend, signMap) => {
            const results = [];
            
            if (isWeekend) {
                // [주말] tv-asahi 굿!모닝 구조 (.rank-box li)
                const items = document.querySelectorAll('.rank-box li');
                items.forEach((li, index) => {
                    const rawSign = li.querySelector('span')?.innerText.trim() || "";
                    if (rawSign) {
                        results.push({
                            rank: index + 1,
                            sign: signMap[rawSign] || rawSign,
                            content: "행운의 아이템 등 상세 정보는 사이트를 확인하세요!"
                        });
                    }
                });
            } else {
                // [평일] 기존 오하아사 구조 (.oa_horoscope_list li)
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

        // 결과 출력 및 전송
        if (fortunes.length > 0) {
            console.table(fortunes);
            await sendDiscord(fortunes, TARGET_URL, isWeekend, kstNow);
        } else {
            console.log("❌ 데이터를 찾을 수 없습니다.");
        }

    } catch (e) {
        console.error("❌ 에러:", e.message);
    } finally {
        await browser.close();
    }
}

async function sendDiscord(fortunes, url, isWeekend, date) {
    const WEBHOOK_URL = process.env.DISCORD_WEBHOOK;
    if (!WEBHOOK_URL) return;

    const todayTag = `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`;
    
    let description = "";
    fortunes.forEach(f => {
        const medal = f.rank === 1 ? "🥇" : f.rank === 2 ? "🥈" : f.rank === 3 ? "🥉" : "🔹";
        description += `${medal} **${f.rank}위**: ${f.sign}\n${isWeekend ? '' : `> ${f.content}\n`}\n`;
    });

    const payload = {
        embeds: [{
            title: `✨ ${todayTag} ${isWeekend ? '굿!모닝' : '오하아사'} 별자리 운세`,
            url: url,
            description: description,
            color: isWeekend ? 16766720 : 5814783,
            footer: { text: isWeekend ? "TV 아사히 굿!모닝 기반" : "ABC 오하아사 기반" },
            timestamp: new Date()
        }]
    };

    await axios.post(WEBHOOK_URL, payload);
    console.log("✅ 디스코드 전송 완료!");
}

run();
