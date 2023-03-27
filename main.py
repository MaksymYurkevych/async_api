import aiohttp
import asyncio
import platform
import datetime
from sys import argv


async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    print(f"Error status: {resp.status} for {url}")
        except aiohttp.ClientConnectorError as err:
            print(f'Connection error: {url}', str(err))


async def main(num_of_dates: int):
    start = datetime.datetime.today()
    date_list = [start.date() - datetime.timedelta(days=x) for x in range(num_of_dates)]
    final_result = ""
    for date in date_list:
        correct_date = date.strftime("%d.%m.%Y")
        result = await request(f'https://api.privatbank.ua/p24api/exchange_rates?json&date={correct_date}')
        if result:
            exc, = list(filter(lambda el: el["currency"] == 'USD', result["exchangeRate"]))
            final_result += f"Дата: {correct_date} USD Продаж {exc['saleRateNB']}, Покупка {exc['purchaseRate']}\n"
        else:
            return 'Not found'
    return final_result

if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    if int(argv[1]) <= 10:
        print(asyncio.run(main(int(argv[1]))))
    else:
        print("Number of days should be less than 10")

