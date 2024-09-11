import aiohttp
import asyncio
import logging
import os
from aiohttp import web
import time
# Set up logging
logging.basicConfig(filename='proxy.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Configuration for the target URL
TARGET_URL = os.getenv('TARGET_URL', 'http://78.158.168.230')  # Change this to your desired target URL
REQUEST_LIMIT = int(os.getenv('REQUEST_LIMIT', 100))  # Max requests per minute

# Rate limiting settings
request_count = 0
request_start_time = time.time()

async def handle_request(request):
    global request_count, request_start_time
    check_rate_limit()

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
        except asyncio.TimeoutError:
            return web.Response(status=504, text="Gateway Timeout: The request took too long to complete.")
        except Exception as e:
            logging.error(f"Error forwarding {method} request to {full_target_url}: {e}")
            return web.Response(status=502, text="Bad Gateway: Error occurred while forwarding the request.")

def check_rate_limit():
    global request_count, request_start_time
    current_time = time.time()
    if current_time - request_start_time > 60:  # Reset every minute
        request_count = 0
        request_start_time = current_time

    if request_count >= REQUEST_LIMIT:
        raise web.HTTPTooManyRequests(text="Rate limit exceeded.")
    else:
        request_count += 1

async def handle_response(response):
    status = response.status
    content_type = response.headers.get('Content-Type', 'text/html')
    body = await response.read()

    logging.info(f"Forwarded to {response.url} with status code: {status} and response size: {len(body)} bytes")
    return web.Response(status=status, body=body, content_type=content_type)

async def init_app():
    app = web.Application()
    app.router.add_route('*', '/{path:.*}', handle_request)
    return app

if __name__ == '__main__':
    app = init_app()
    web.run_app(app, port=8080)
