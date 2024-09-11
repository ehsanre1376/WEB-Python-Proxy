import http.server
import socketserver
import requests
import logging

# Set up logging
logging.basicConfig(filename='proxy.log', level=logging.INFO, format='%(asctime)s - %(message)s')

class Proxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.forward_request('GET')

    def do_POST(self):
        self.forward_request('POST')

    def forward_request(self, method):
        # Log the incoming request
        logging.info(f"Received {method} request for: {self.path}")

        # Define the target URL to forward requests to
        target_url = 'http://78.158.168.230' + self.path  # Change this to your target address

        # Prepare headers and data
        headers = {key: self.headers[key] for key in self.headers}
        data = None

        if method == 'POST':
            content_length = int(self.headers['Content-Length'])
            data = self.rfile.read(content_length)

        try:
            # Forward the request to the target URL
            if method == 'GET':
                response = requests.get(target_url, headers=headers)
            elif method == 'POST':
                response = requests.post(target_url, headers=headers, data=data)

            # Send the response back to the client
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
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
