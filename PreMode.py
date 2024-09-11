from flask import Flask, request, Response
import requests

app = Flask(__name__)

# The address to which you want to forward the requests
FORWARD_URL = 'https://78.158.168.230'  # Change this to your target URL

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def forward_request(path):
    # Get the original request method and data
    method = request.method
    data = request.get_data()
    headers = {key: value for key, value in request.headers if key != 'Host'}

    # Forward the request to the target URL
    response = requests.request(method, f"{FORWARD_URL}/{path}", data=data, headers=headers)

    # Return the response from the forwarded request
    return Response(response.content, status=response.status_code, headers=dict(response.headers))

if __name__ == '__main__':
    app.run(port=5000)  # You can change the port if needed
