import http.server
import socketserver
import app

# Define the function you want to serve
def my_function():
    return "Hello from my function!"

# Custom request handler class
class MyRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':  # Check if the path matches '/'
            self.send_response(200)  # Send a 200 OK response
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write((app.main('hello')).read())  # Send the function's output
        else:
            self.send_response(404)  # If the path doesn't match, send 404
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Not Found")

# Set up the HTTP server
PORT = 8000
with socketserver.TCPServer(("", PORT), MyRequestHandler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
