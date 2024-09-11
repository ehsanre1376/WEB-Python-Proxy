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

class Proxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global request_count, request_start_time
        self.check_rate_limit()

        # Log the incoming request
        logging.info(f"Received GET request for: {self.path}")

        # Construct the full target URL
        full_target_url = TARGET_URL + self.path
        try:
            response = requests.get(full_target_url, timeout=10)
            self.send_response(response.status_code)
            self.send_header('Content-type', response.headers.get('Content-Type', 'text/html'))
            self.send_header('Access-Control-Allow-Origin', '*')  # CORS header
            self.end_headers()
            self.wfile.write(response.content)

            # Log the response
            logging.info(f"Forwarded to {full_target_url} with status code: {response.status_code}")
        except requests.Timeout:
            self.send_response(504)
            self.end_headers()
            self.wfile.write(b"Gateway Timeout: The request took too long to complete.")
            logging.error(f"Timeout error forwarding request to {full_target_url}")
        except requests.RequestException as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(b"Bad Gateway: Error occurred while forwarding the request.")
            logging.error(f"Error forwarding request to {full_target_url}: {e}")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Internal Server Error")
            logging.error(f"Unexpected error forwarding request to {full_target_url}: {e}")

    def do_POST(self):
        global request_count, request_start_time
        self.check_rate_limit()

        # Log the incoming request
        logging.info(f"Received POST request for: {self.path}")

        # Construct the full target URL
        full_target_url = TARGET_URL + self.path
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            response = requests.post(full_target_url, data=post_data, headers=self.headers, timeout=10)
            self.send_response(response.status_code)
            self.send_header('Content-type', response.headers.get('Content-Type', 'text/html'))
            self.send_header('Access-Control-Allow-Origin', '*')  # CORS header
            self.end_headers()
            self.wfile.write(response.content)

            # Log the response
            logging.info(f"Forwarded to {full_target_url} with status code: {response.status_code}")
        except requests.Timeout:
            self.send_response(504)
            self.end_headers()
            self.wfile.write(b"Gateway Timeout: The request took too long to complete.")
            logging.error(f"Timeout error forwarding POST request to {full_target_url}")
        except requests.RequestException as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(b"Bad Gateway: Error occurred while forwarding the request.")
            logging.error(f"Error forwarding POST request to {full_target_url}: {e}")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Internal Server Error")
            logging.error(f"Unexpected error forwarding POST request to {full_target_url}: {e}")

    def check_rate_limit(self):
        global request_count, request_start_time
        current_time = time.time()
        if current_time - request_start_time > 60:  # Reset every minute
            request_count = 0
            request_start_time = current_time

        if request_count >= REQUEST_LIMIT:
            self.send_response(429)  # Too Many Requests
            self.end_headers()
            self.wfile.write(b"Too Many Requests: Rate limit exceeded.")
            logging.warning("Rate limit exceeded.")
            self.stop()
        else:
            request_count += 1

# Set up the server
PORT = 8080
with socketserver.TCPServer(("", PORT), Proxy) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()
