from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import hmac
from urllib.parse import urlparse


class ATRHandler(BaseHTTPRequestHandler):
    secret = 'automaticTwitchRecorder'

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        query = urlparse(self.path).query
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        try:
            query_components = dict(qc.split("=") for qc in query.split("&"))
            challenge = query_components["hub.challenge"]
            # s = ''.join(x for x in challenge if x.isdigit())
            # print(s)
            # print(challenge)
            self.send_response(200, None)
            self.end_headers()
            self.wfile.write(bytes(challenge, "utf-8"))
        except:
            query_components = None
            challenge = None
            self.send_response(200, None)
            self.end_headers()
            self.wfile.write(bytes("Hello Stranger :)", "utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), post_data.decode('utf-8'))
        if 'Content-Type' in self.headers:
            content_type = str(self.headers['Content-Type'])
        else:
            raise ValueError("not all headers supplied.")
        if 'X-Hub-Signature' in self.headers:
            hub_signature = str(self.headers['X-Hub-Signature'])
            algorithm, hashval = hub_signature.split('=')
            print(hashval)
            print(algorithm)
            if post_data and algorithm and hashval:
                gg = hmac.new(self.secret.encode(), post_data, algorithm)
                if not hmac.compare_digest(hashval.encode(), gg.hexdigest().encode()):
                    raise ConnectionError("Hash missmatch.")
        else:
            raise ValueError("not all headers supplied.")
        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))


def run(server_class=HTTPServer, handler_class=ATRHandler, port=1234):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
