import asyncio
import aiohttp
from telegram import Bot

BOT_TOKEN = "8787982429:AAGpfzIibK7e58YtvAl6g5m1EG2sZtEdFYA"
CHAT_ID = 6318865778

BASE_URL = "https://agropraktika.eu/vacancies"
PAGES = 3
CHECK_INTERVAL = 60

bot = Bot("8787982429:AAGpfzIibK7e58YtvAl6g5m1EG2sZtEdFYA")

previous_state = {}


async def is_closed(html: str) -> bool:
    return "Регистрация временно приостановлена" in html


async def get_page_state(session, page):
    url = f"{BASE_URL}?page={page}"

    try:
        async with session.get(url) as r:

            if r.status == 403:
                print(f"403 на странице {page} — пропуск")
                return None

            html = await r.text()
            return await is_closed(html)   # ✅ FIX

    except Exception as e:
        print(f"Ошибка страницы {page}: {e}")
        return None


async def get_state(session):
    state = {}

    for page in range(1, PAGES + 1):
        result = await get_page_state(session, page)

        if result is None:
            continue

        state[page] = result

    return state


async def check():
    global previous_state

    async with aiohttp.ClientSession() as session:
        while True:
            current_state = await get_state(session)

            if not current_state:
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            if not previous_state:
                previous_state = current_state
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            for page, current_value in current_state.items():

                prev_value = previous_state.get(page)

                if prev_value is True and current_value is False:
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=(
                            f"🚨 ВАКАНСИЯ ОТКРЫЛАСЬ!\n"
                            f"Страница: {page}\n"
                            f"{BASE_URL}?page={page}"
                        )
                    )

            # ⚠️ аккуратное обновление (не ломаем None/403 данные)
            previous_state = {
                **previous_state,
                **current_state
            }

            await asyncio.sleep(CHECK_INTERVAL)


async def main():
    await bot.send_message(
        chat_id=CHAT_ID,
        text="✅ Бот запущен и отслеживает вакансии"
    )
    await check()


if __name__ == "__main__":
    asyncio.run(main())