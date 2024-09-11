import aiohttp
import asyncio
import logging
import json
import os
import time
from aiohttp import web

# Load configuration from config.json
with open('config.json') as config_file:
    config = json.load(config_file)

# Set up logging
logging.basicConfig(filename=config['LOG_FILE'], level=logging.INFO, format='%(asctime)s - %(message)s')

# Configuration for the target URL
TARGET_URL = config['TARGET_URL']
REQUEST_LIMIT = config['REQUEST_LIMIT']
PORT = config['PORT']
PERIODIC_TASK_INTERVAL = config.get('PERIODIC_TASK_INTERVAL', 60)  # Default to 60 seconds

class RateLimiter:
    def __init__(self, limit: int):
        self.limit = limit
        self.request_count = 0
        self.request_start_time = time.time()

    def check_rate_limit(self):
        current_time = time.time()
        if current_time - self.request_start_time > 60:  # Reset every minute
            self.request_count = 0
            self.request_start_time = current_time

        if self.request_count >= self.limit:
            raise web.HTTPTooManyRequests(text="Rate limit exceeded.")
        else:
            self.request_count += 1

rate_limiter = RateLimiter(REQUEST_LIMIT)

async def handle_request(request: web.Request) -> web.Response:
    rate_limiter.check_rate_limit()

    method = request.method
    path = request.path
    full_target_url = TARGET_URL + path

    logging.info(f"Received {method} request for: {path}")

    async with aiohttp.ClientSession() as session:
        try:
            if method == 'GET':
                async with session.get(full_target_url) as response:
                    return await handle_response(response)
            elif method == 'POST':
                data = await request.read()
                async with session.post(full_target_url, data=data) as response:
                    return await handle_response(response)
            else:
                return web.Response(status=405, text="Method Not Allowed")
        except asyncio.TimeoutError:
            return web.Response(status=504, text="Gateway Timeout: The request took too long to complete.")
        except Exception as e:
            logging.error(f"Error forwarding {method} request to {full_target_url}: {e}")
            return web.Response(status=502, text="Bad Gateway: Error occurred while forwarding the request.")

async def handle_response(response: aiohttp.ClientResponse) -> web.Response:
    status = response.status
    content_type = response.headers.get('Content-Type', 'text/html')
    body = await response.read()

    logging.info(f"Forwarded to {response.url} with status code: {status} and response size: {len(body)} bytes")
    return web.Response(status=status, body=body, content_type=content_type)

async def periodic_task():
    while True:
        # Perform the periodic task here
        logging.info("Performing periodic task...")
        # You can add your task logic here

        await asyncio.sleep(PERIODIC_TASK_INTERVAL)  # Sleep for the specified interval

async def init_app() -> web.Application:
    app = web.Application()
    app.router.add_route('*', '/{path:.*}', handle_request)
    return app

if __name__ == '__main__':
    app = init_app()
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_task())  # Start the periodic task
    try:
        web.run_app(app, port=PORT)
    except KeyboardInterrupt:
        logging.info("Server shutting down.")
