import aiohttp
import asyncio
import logging
import time
import win32serviceutil
import win32service
import win32event
import servicemanager
from aiohttp import web

# Configuration settings
LOG_FILE = "C:\\Users\\EHSANRE\\OneDrive\\Project\\WEB-Python-Proxy\\Install\\logfile.log"  # Change this to your desired log file path
TARGET_URL = "http://78.158.168.230"  # Change this to your target URL
REQUEST_LIMIT = 100  # Set your request limit
PORT = 8080  # Set the port for the server
PERIODIC_TASK_INTERVAL = 60  # Set the interval for the periodic task

# Set up logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

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

class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MyAiohttpService"
    _svc_display_name_ = "My Aiohttp Service"
    _svc_description_ = "This service runs an aiohttp web server."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.loop = asyncio.get_event_loop()
        self.app = self.loop.run_until_complete(init_app())
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        logging.info("Service is stopping...")

    def SvcDoRun(self):
        logging.info("Service is starting...")
        self.loop.create_task(self.run_periodic_task())  # Start the periodic task
        web.run_app(self.app, port=PORT)

    async def run_periodic_task(self):
        while self.running:
            logging.info("Performing periodic task...")
            # You can add your task logic here
            await asyncio.sleep(PERIODIC_TASK_INTERVAL)  # Sleep for the specified interval


    # Your main service logic here
    # Sleep for a while to avoid busy-waiting
if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(MyService)
    # Run the application directly for debugging
    app = asyncio.run(init_app())
    asyncio.run(web.run_app(app, port=PORT))
    
