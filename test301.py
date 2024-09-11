import http.server
import socketserver
import requests
import logging
import time

# Set up logging
logging.basicConfig(filename='proxy.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Configuration for the target URL
TARGET_URL = 'http://78.158.168.230'  # Change this to your desired target URL

# Rate limiting settings
REQUEST_LIMIT = 100  # Max requests per minute
request_count = 0
request_start_time = time.time()

# HTTP Status Codes
HTTP_STATUS = {
    'OK': 200,
    'BAD_GATEWAY': 502,
    'GATEWAY_TIMEOUT': 504,
    'TOO_MANY_REQUESTS': 429,
    'INTERNAL_SERVER_ERROR': 500
}

class Proxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.handle_request('GET')

    def do_POST(self):
        self.handle_request('POST')

    def handle_request(self, method):
        global request_count, request_start_time
        self.check_rate_limit()

        # Log the incoming request
        logging.info(f"Received {method} request for: {self.path}")

        # Construct the full target URL
        full_target_url = TARGET_URL + self.path
        try:
            if method == 'GET':
                response = requests.get(full_target_url, timeout=10)
            else:  # POST
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                response = requests.post(full_target_url, data=post_data, headers=self.headers, timeout=10)

            self.send_response(response.status_code)
            self.send_header('Content-type', response.headers.get('Content-Type', 'text/html'))
            self.send_header('Access-Control-Allow-Origin', '*')  # CORS header
            self.end_headers()
            self.wfile.write(response.content)

            # Log the response
            logging.info(f"Forwarded to {full_target_url} with status code: {response.status_code}")
        except requests.Timeout:
            self.send_error(HTTP_STATUS['GATEWAY_TIMEOUT'], "The request took too long to complete.")
            logging.error(f"Timeout error forwarding {method} request to {full_target_url}")
        except requests.RequestException as e:
            self.send_error(HTTP_STATUS['BAD_GATEWAY'], "Error occurred while forwarding the request.")
            logging.error(f"Error forwarding {method} request to {full_target_url}: {e}")
        except Exception as e:
            self.send_error(HTTP_STATUS['INTERNAL_SERVER_ERROR'], "Internal Server Error")
            logging.error(f"Unexpected error forwarding {method} request to {full_target_url}: {e}")

    def check_rate_limit(self):
        global request_count, request_start_time
        current_time = time.time()
        if current_time - request_start_time > 60:  # Reset every minute
            request_count = 0
            request_start_time = current_time

        if request_count >= REQUEST_LIMIT:
            self.send_error(HTTP_STATUS['TOO_MANY_REQUESTS'], "Rate limit exceeded.")
            logging.warning("Rate limit exceeded.")
            self.stop()
        else:
            request_count += 1

# Set up the server
PORT = 8080
with socketserver.TCPServer(("", PORT), Proxy) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()
