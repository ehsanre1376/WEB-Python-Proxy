import aiohttp
import asyncio
from aiohttp import web
import concurrent.futures

FORWARD_URL = 'http://google.com'  # Change this to your target URL

async def forward_request(request):
    async with aiohttp.ClientSession() as session:
        if request.method == 'POST':
            data = await request.json()
            async with session.post(FORWARD_URL, json=data) as response:
                response_data = await response.json()
                return web.json_response(response_data, status=response.status)
        else:
            params = request.query
            async with session.get(FORWARD_URL, params=params) as response:
                response_data = await response.json()
                return web.json_response(response_data, status=response.status)

async def init_app():
    app = web.Application()
    app.router.add_route('*', forward_request)
    return app

def run_app():
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    web.run_app(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    # Use ThreadPoolExecutor to run the app in a separate thread
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_app)
        try:
            while True:
                asyncio.sleep(1)  # Keep the main thread alive
        except KeyboardInterrupt:
            print("Shutting down the server...")