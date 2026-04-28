const puppeteer = require("puppeteer");
const axios = require("axios");

const signMap = {
  おひつじ座: "양자리",
  おうし座: "황소자리",
  ふたご座: "쌍둥이자리",
  かに座: "게자리",
  しし座: "사자자리",
  おとめ座: "처녀자리",
  てんびん座: "천칭자리",
  さそ리座: "전갈자리",
  いて座: "사수자리",
  やぎ座: "염소자리",
  みずがめ座: "물병자리",
  うお座: "물고기자리",
};

async function deploy() {
  const browser = await puppeteer.launch({
    headless: "new",
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
    ],
  });

  const page = await browser.newPage();

  try {
    await page.goto("https://www.asahi.co.jp/ohaasa/week/horoscope/", {
      waitUntil: "networkidle2",
    });

    const data = await page.evaluate((signMap) => {
      const siteDate =
        document.querySelector(".horoscope_date, .date")?.innerText.trim() ||
        "오늘";
      const list = [];
      const items = document.querySelectorAll(".oa_horoscope_list li");

      items.forEach((item) => {
        const rank = item.querySelector(".horo_rank")?.innerText || "";
        const rawSign = item.querySelector("sapn.horo_name")?.innerText || "";
        const content = item.querySelector(".horo_txt")?.innerText || "";

        if (rawSign) {
          list.push(
            `**${rank}위: ${signMap[rawSign] || rawSign}**\n${content.trim().replace(/\s+/g, " ")}`,
          );
        }
      });
      return { siteDate, list };
    }, signMap);

    if (data.list.length > 0) {
      await sendDiscord(data.siteDate, data.list);
    }
  } catch (error) {
    console.error("배포 실행 중 에러:", error);
  } finally {
    await browser.close();
  }
}

async function sendDiscord(dateInfo, list) {
  const WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL;
  if (!WEBHOOK_URL) return;

  const payload = {
    embeds: [
      {
        title: `🔮 오하아사 별자리 운세 (${dateInfo})`,
        description: list.join("\n\n"),
        color: 5814783,
        timestamp: new Date(),
      },
    ],
  };

  await axios.post(WEBHOOK_URL, payload);
}

deploy();
