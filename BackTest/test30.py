creat gui for this code 
import http.server
import socketserver
import requests
import logging

# Set up logging
logging.basicConfig(filename='proxy.log', level=logging.INFO, format='%(asctime)s - %(message)s')

class Proxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Log the incoming request
        logging.info(f"Received GET request for: {self.path}")

        # Forward the request to the target address
        target_url = 'http://78.158.168.230' + self.path  # Change this to your target address
        try:
            response = requests.get(target_url, timeout=10)  # Set a timeout for the request
            self.send_response(response.status_code)
            self.send_header('Content-type', response.headers.get('Content-Type', 'text/html'))
            self.end_headers()
            self.wfile.write(response.content)

            # Log the response
            logging.info(f"Forwarded to {target_url} with status code: {response.status_code}")
        except requests.Timeout:
            self.send_response(504)  # Gateway Timeout
            self.end_headers()
            self.wfile.write(b"Gateway Timeout: The request took too long to complete.")
            logging.error(f"Timeout error forwarding request to {target_url}")
        except requests.RequestException as e:
            self.send_response(502)  # Bad Gateway
            self.end_headers()
            self.wfile.write(b"Bad Gateway: Error occurred while forwarding the request.")
            logging.error(f"Error forwarding request to {target_url}: {e}")
        except Exception as e:
            self.send_response(500)  # Internal Server Error
            self.end_headers()
            self.wfile.write(b"Internal Server Error")
            logging.error(f"Unexpected error forwarding request to {target_url}: {e}")

    def do_POST(self):
        # Log the incoming request
        logging.info(f"Received POST request for: {self.path}")

        # Forward the request to the target address
        target_url = 'http://78.158.168.230' + self.path  # Change this to your target address
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            response = requests.post(target_url, data=post_data, headers=self.headers, timeout=10)  # Set a timeout
            self.send_response(response.status_code)
            self.send_header('Content-type', response.headers.get('Content-Type', 'text/html'))
            self.end_headers()
            self.wfile.write(response.content)

            # Log the response
            logging.info(f"Forwarded to {target_url} with status code: {response.status_code}")
        except requests.Timeout:
            self.send_response(504)  # Gateway Timeout
            self.end_headers()
            self.wfile.write(b"Gateway Timeout: The request took too long to complete.")
            logging.error(f"Timeout error forwarding POST request to {target_url}")
        except requests.RequestException as e:
            self.send_response(502)  # Bad Gateway
            self.end_headers()
            self.wfile.write(b"Bad Gateway: Error occurred while forwarding the request.")
            logging.error(f"Error forwarding POST request to {target_url}: {e}")
        except Exception as e:
            self.send_response(500)  # Internal Server Error
            self.end_headers()
            self.wfile.write(b"Internal Server Error")
            logging.error(f"Unexpected error forwarding POST request to {target_url}: {e}")

# Set up the server
PORT = 8080
with socketserver.TCPServer(("", PORT), Proxy) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()
