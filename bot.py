import asyncio
from telegram import Bot
import aiohttp

BOT_TOKEN = "8787982429:AAGpfzIibK7e58YtvAl6g5m1EG2sZtEdFYA"
CHAT_ID = 6318865778

BASE_URL = "https://agropraktika.eu/vacancies"
CHECK_INTERVAL = 60
PAGES = 3

bot = Bot("8787982429:AAGpfzIibK7e58YtvAl6g5m1EG2sZtEdFYA")

previous_counts = {}

async def get_counts(session):
    counts = {}
    for page in range(1, PAGES + 1):
        url = f"{BASE_URL}?page={page}"
        async with session.get(url) as response:
            html = await response.text()
            counts[page] = html.count("Регистрация временно приостановлена")
    return counts


async def check():
    global previous_counts

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                current_counts = await get_counts(session)

                if not previous_counts:
                    previous_counts = current_counts
                else:
                    for page in current_counts:
                        if current_counts[page] < previous_counts[page]:
                            for _ in range(3):
                                await bot.send_message(
                                    chat_id=CHAT_ID,
                                    text=f"🚨 РЕГИСТРАЦИЯ ОТКРЫЛАСЬ!\nСтраница: {page}\n{BASE_URL}?page={page}"
                                )
                                await asyncio.sleep(1)

                    previous_counts = current_counts

            except Exception as e:
                await bot.send_message(chat_id=CHAT_ID, text=f"Ошибка: {e}")

            await asyncio.sleep(CHECK_INTERVAL)


async def main():
    await bot.send_message(chat_id=CHAT_ID, text="Бот запущен и следит за страницами")
    await check()


if __name__ == "__main__":
    asyncio.run(main())
