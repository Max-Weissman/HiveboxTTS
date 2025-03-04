from flask import Flask, request, make_response
import app

server = Flask(__name__)

@server.route("/", methods=['POST'])
def hello_world():
    data = (app.main(request.get_json()['question'])).read()
    response = make_response(data)
    response.headers.set('Content-Type', 'application/octet-stream')
    return response

if __name__ == '__main__':
    server.run()