import asyncio
import aiohttp
import os
from telegram import Bot
from datetime import datetime

# =====================
# CONFIG
# =====================

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "BOT_TOKEN"

BASE_URL = "https://agropraktika.eu/vacancies"
CHECK_INTERVAL = 60

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "ru-RU,ru;q=0.9"
}

bot = Bot(token=BOT_TOKEN)

# память статуса страниц
previous_status = {}

# =====================
# LOG
# =====================

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# =====================
# FETCH WITH ANTI 403 RETRY
# =====================

async def fetch_page(session, page):
    url = f"{BASE_URL}?page={page}"

    for attempt in range(3):
        try:
            async with session.get(url, headers=HEADERS, timeout=20) as r:

                if r.status == 403:
                    log(f"403 на странице {page}, попытка {attempt+1}/3")
                    await asyncio.sleep(120)  # 2 минуты ожидания
                    continue

                if r.status != 200:
                    log(f"Ошибка HTTP {r.status} на странице {page}")
                    return None

                return await r.text()

        except Exception as e:
            log(f"Ошибка страницы {page}: {e}")
            await asyncio.sleep(10)

    log(f"Страница {page} пропущена (много 403)")
    return None

# =====================
# CHECK STATUS
# =====================

def is_closed(html):
    return "регистрация временно приостановлена" in html.lower()

# =====================
# MAIN LOOP
# =====================

async def loop():
    global previous_status

    async with aiohttp.ClientSession() as session:

        await bot.send_message(CHAT_ID, "🤖 Бот запущен (anti-403 версия)")

        while True:
            try:
                log("Проверка сайта...")

                for page in range(1, 3):

                    html = await fetch_page(session, page)

                    if not html:
                        continue

                    current_closed = is_closed(html)
                    prev_closed = previous_status.get(page)

                    # было закрыто → стало открыто
                    if prev_closed is True and current_closed is False:
                        log(f"🔥 ОТКРЫЛАСЬ регистрация на странице {page}")

                        await bot.send_message(
                            CHAT_ID,
                            f"🚨 РЕГИСТРАЦИЯ ОТКРЫЛАСЬ!\n"
                            f"Страница: {page}\n"
                            f"{BASE_URL}?page={page}"
                        )

                    previous_status[page] = current_closed

                log("цикл завершён")

            except Exception as e:
                log(f"Критическая ошибка: {e}")

            await asyncio.sleep(CHECK_INTERVAL)

# =====================
# START
# =====================

async def main():
    await loop()

if __name__ == "__main__":
    asyncio.run(main())