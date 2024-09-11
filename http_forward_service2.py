'''
import os
import sys

service_directory = os.path.dirname(__file__)
source_directory = os.path.abspath(service_directory)
os.chdir(source_directory)
venv_base = os.path.abspath(os.path.join(source_directory, "..", "..", "venv"))
sys.path.append(".")
old_os_path = os.environ['PATH']
os.environ['PATH'] = os.path.join(venv_base, "Scripts")+ os.pathsep + old_os_path
site_packages = os.path.join(venv_base, "Lib", "site-packages")
prev_sys_path = list(sys.path)
import site
site.addsitedir(site_packages)
sys.real_prefix = sys.prefix
sys.prefix = venv_base
new_sys_path = list()
for item in list(sys.path):
    if item not in prev_sys_path:
        new_sys_path.append(item)
        sys.path.remove(item)
sys.path[:0] = new_sys_path



'''

import logging
import threading
import win32serviceutil
import win32service
import win32event
import servicemanager
import logging
import threading
import asyncio

import aiohttp

from aiohttp import web

class HttpForwardService(win32serviceutil.ServiceFramework):
    _svc_name_ = "HttpForwardService"
    _svc_display_name_ = "HTTP Forwarding Service"
    _svc_description_ = "A Windows service that forwards HTTP requests to another server."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        self.target_url = "http://example.com"  # Change this to your target URL
        self.setup_logging()
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_loop)
        self.thread.start()

    def setup_logging(self):
        logging.basicConfig(
            filename='C:\\Users\\EHSANRE\\OneDrive\\Project\\WEB-Python-Proxy\\logfile.log',  # Change to your desired log file path
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        self.loop.call_soon_threadsafe(self.loop.stop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                               servicemanager.PYS_SERVICE_STARTED,
                               (self._svc_name_, ''))
        self.main()

    def run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def forward_request(self, request):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=request.method,
                    url=self.target_url,
                    headers={key: value for (key, value) in request.headers.items() if key != 'Host'},
                    data=await request.read(),
                    allow_redirects=False
                ) as response:
                    return response.status, await response.read(), response.headers
        except Exception as e:
            logging.error(f"Error forwarding request: {e}")
            return 500, b"Internal Server Error", {}

    async def handle_request(self, request):
        status, body, headers = await self.forward_request(request)
        return web.Response(status=status, body=body, headers=headers)

    def main(self):
        app = web.Application()
        app.router.add_route('*', '/forward', self.handle_request)  # Change '/forward' to your desired endpoint
        runner = web.AppRunner(app)
        asyncio.run(runner.setup())
        site = web.TCPSite(runner, 'localhost', 8080)  # Change the host and port as needed
        asyncio.run(site.start())
        logging.info("Service is running and ready to forward requests.")
        while self.running:
            win32event.WaitForSingleObject(self.stop_event, 5000)  # Check for stop event every 5 seconds

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(HttpForwardService)
