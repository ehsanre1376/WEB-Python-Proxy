from flask import Flask, request, Response
import requests
import logging
from requests.exceptions import RequestException

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Default address to which you want to forward the requests
DEFAULT_FORWARD_URL = 'http://78.158.168.230'  # Change this to your target URL

@app.route('/')
def home():
    return "Welcome to the Flask Proxy!"

@app.route('/forward', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/forward/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def forward_request(path):
    # Get the original request method and data
    method = request.method
    data = request.get_data()
    headers = {key: value for key, value in request.headers if key != 'Host'}
    params = request.args  # Get query parameters

    # Optionally allow dynamic forwarding URL via query parameter
    forward_url = request.args.get('forward_url', DEFAULT_FORWARD_URL)

    # Log the request details
    logging.info(f"Forwarding {method} request to {forward_url}/{path} with data: {data} and headers: {headers}")

    try:
        # Create a new session object for each request
        with requests.Session() as session:
            # Forward the request to the target URL with a timeout
            response = session.request(method, f"{forward_url}/{path}", data=data, headers=headers, params=params, timeout=10)

        # Log the response details
        logging.info(f"Received response with status code {response.status_code}")

        # Stream the response back to the client
        return Response(response.iter_content(chunk_size=1024), status=response.status_code, headers=dict(response.headers))
    
    except RequestException as e:
        logging.error(f"Error forwarding request: {e}")
        return Response(f"Error forwarding request: {str(e)}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Run in debug mode
