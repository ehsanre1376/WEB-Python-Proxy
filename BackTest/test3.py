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
            response = requests.get(target_url)
            self.send_response(response.status_code)
            self.send_header('Content-type', response.headers['Content-Type'])
            self.end_headers()
            self.wfile.write(response.content)

            # Log the response
            logging.info(f"Forwarded to {target_url} with status code: {response.status_code}")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Internal Server Error")
            logging.error(f"Error forwarding request: {e}")

    def do_POST(self):
        # Log the incoming request
        logging.info(f"Received POST request for: {self.path}")

        # Forward the request to the target address
        target_url = 'http://example.com' + self.path  # Change this to your target address
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            response = requests.post(target_url, data=post_data, headers=self.headers)
            self.send_response(response.status_code)
            self.send_header('Content-type', response.headers['Content-Type'])
            self.end_headers()
            self.wfile.write(response.content)

            # Log the response
            logging.info(f"Forwarded to {target_url} with status code: {response.status_code}")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Internal Server Error")
            logging.error(f"Error forwarding request: {e}")

# Set up the server
PORT = 8080
with socketserver.TCPServer(("", PORT), Proxy) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()
