import os
import sys
import json
import logging
import asyncio
import aiohttp
import servicemanager
import win32service
import win32serviceutil
from aiohttp import web
import time


# Load configuration from config.json
#with open('config.json') as config_file:
#    config = json.load(config_file)

# Set up logging
logging.basicConfig(filename="proxy.log"'''config['LOG_FILE']''', level=logging.INFO, format='%(asctime)s - %(message)s')

# Configuration for the target URL
TARGET_URL ="http://78.158.168.230"# config['TARGET_URL']
REQUEST_LIMIT =100# config['REQUEST_LIMIT']
PORT =8080# config['PORT']

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

async def init_app() -> web.Application:
    app = web.Application()
    app.router.add_route('*', '/{path:.*}', handle_request)
    return app

class AiohttpService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AiohttpService1"
    _svc_display_name_ = "Aiohttp Web Service1"
    _svc_description_ = "A simple aiohttp web service running as a Windows service1."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = asyncio.Event()
        self.loop = asyncio.get_event_loop()
        self.app = self.loop.run_until_complete(init_app())
        self.server = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.stop_event.set()
        if self.server:
            self.server.close()

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                               servicemanager.PYS_SERVICE_STARTED,
                               (self._svc_name_, ''))
        self.server = self.loop.run_until_complete(web.run_app(self.app, port=PORT))

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AiohttpService)
