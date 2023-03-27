import asyncio
import aiohttp
import logging
import websockets
import names
import datetime
import aiofile
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK


logging.basicConfig(level=logging.INFO)


async def request(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            result = await res.json()
            return result


async def exchange_for_days(num_of_dates: int):

    if num_of_dates >= 10:
        return 'Занадто багато днів для виводу'

    async with aiofile.AIOFile('log_exchange.txt', 'a') as f:
        log_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await f.write(f"{log_time}: команда 'exchange' виконана\n")

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


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distribute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distribute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message.startswith('exchange'):
                list_message = message.split(' ')
                exc = await exchange_for_days(int(list_message[1]))
                await self.send_to_clients(str(exc))
            elif message == 'Hi Server':
                await self.send_to_clients(f"{ws.name}: {message}")
                await self.send_to_clients('Привіт мої любі!')
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()


if __name__ == '__main__':
    asyncio.run(main())
