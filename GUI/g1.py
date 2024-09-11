import tkinter as tk
from tkinter import messagebox
import asyncio
import threading
import json
import logging
import aiohttp
from aiohttp import web

# Set up logging
logging.basicConfig(filename='proxy_server.log', level=logging.INFO, format='%(asctime)s - %(message)s')

class ProxyServerGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Proxy Server Control")

        # Target URL input
        tk.Label(master, text="Target URL:").pack(pady=5)
        self.target_url_entry = tk.Entry(master, width=50)
        self.target_url_entry.pack(pady=5)

        # Request Limit input
        tk.Label(master, text="Request Limit:").pack(pady=5)
        self.request_limit_entry = tk.Entry(master, width=10)
        self.request_limit_entry.pack(pady=5)

        # Port input
        tk.Label(master, text="Port:").pack(pady=5)
        self.port_entry = tk.Entry(master, width=10)
        self.port_entry.pack(pady=5)

        # Start and Stop buttons
        self.start_button = tk.Button(master, text="Start Server", command=self.start_server)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(master, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.pack(pady=10)

        # Log text area
        self.log_text = tk.Text(master, height=20, width=50)
        self.log_text.pack(pady=10)

        self.server_thread = None
        self.running = False

    def start_server(self):
        if not self.running:
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, "Starting server...\n")

            # Get configuration from input fields
            target_url = self.target_url_entry.get()
            request_limit = self.request_limit_entry.get()
            port = self.port_entry.get()

            # Validate inputs
            if not target_url or not request_limit.isdigit() or not port.isdigit():
                messagebox.showerror("Input Error", "Please enter valid Target URL, Request Limit, and Port.")
                self.running = False
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                return

            # Save configuration to a dictionary
            self.config = {
                'TARGET_URL': target_url,
                'REQUEST_LIMIT': int(request_limit),
                'PORT': int(port),
                'LOG_FILE': 'proxy_server.log'
            }

            self.server_thread = threading.Thread(target=self.run_server)
            self.server_thread.start()

    def stop_server(self):
        if self.running:
            self.running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.log_text.insert(tk.END, "Stopping server...\n")
            # Here you would implement logic to stop the server gracefully

    def run_server(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.start_aiohttp_server())
        except Exception as e:
            logging.error(f"Error starting server: {e}")
            self.log_text.insert(tk.END, f"Error starting server: {e}\n")
        finally:
            loop.close()

    async def start_aiohttp_server(self):
        app = await self.init_app()
        await web.run_app(app, port=self.config['PORT'])

    async def init_app(self) -> web.Application:
        app = web.Application()
        app.router.add_route('*', '/{path:.*}', self.handle_request)
        return app

    async def handle_request(self, request: web.Request) -> web.Response:
        # Implement your request handling logic here
        return web.Response(text="Request handled")

if __name__ == '__main__':
    root = tk.Tk()
    app = ProxyServerGUI(root)
    root.mainloop()
