import asyncio
import aiohttp
import os
import time
from bs4 import BeautifulSoup
from telegram import Bot
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

BASE_URL = "https://agropraktika.eu/vacancies"
PAGES = 3
CHECK_INTERVAL = 75

HEADERS = {"User-Agent": "Mozilla/5.0"}

bot = Bot(token=BOT_TOKEN)

previous_vacancies = set()
last_alert_time = {}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def parse_vacancies(html):
    soup = BeautifulSoup(html, "html.parser")
    vacancies = set()

    for item in soup.select("a[href*='vacanc']"):
        text = item.get_text(strip=True)
        href = item.get("href")
        if text:
            vacancies.add((text, href))

    return vacancies

async def fetch_page(session, page):
    url = f"{BASE_URL}?page={page}"

    async with session.get(url, headers=HEADERS) as r:
        html = await r.text()
        return parse_vacancies(html)

async def fetch_all(session):
    tasks = [fetch_page(session, i) for i in range(1, PAGES + 1)]
    results = await asyncio.gather(*tasks)

    all_vacancies = set()
    for r in results:
        all_vacancies |= r

    return all_vacancies

async def loop():
    global previous_vacancies

    async with aiohttp.ClientSession() as session:

        while True:
            try:
                log("Проверка сайта...")
                current = await fetch_all(session)

                if not previous_vacancies:
                    previous_vacancies = current
                    await bot.send_message(CHAT_ID, "🤖 Бот запущен")
                    continue

                new = current - previous_vacancies

                if new:
                    await bot.send_message(
                        CHAT_ID,
                        "🔥 Новые вакансии:\n\n" +
                        "\n".join([x[0] for x in list(new)[:10]])
                    )

                previous_vacancies = current

            except Exception as e:
                log(f"Ошибка: {e}")

            await asyncio.sleep(CHECK_INTERVAL)

async def main():
    await loop()

if __name__ == "__main__":
    asyncio.run(main())