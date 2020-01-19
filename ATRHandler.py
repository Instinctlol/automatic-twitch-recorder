from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
import logging
from urllib.parse import urlparse
import hmac
import json
from jsonschema import validate, ValidationError

from daemon import Daemon


class ATRHandler(BaseHTTPRequestHandler):
    daemon = None
    schema_cmd = {
        "type": "object",
        "properties": {
            "cmd": {"type": "string"},
            "args": {"type": "array", "items": {"type": "string"}},
        },
    }

    def _set_response(self):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _set_bad_request(self, msg):
        self.send_response(HTTPStatus.BAD_REQUEST)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(msg.encode('utf-8'))

    def do_GET(self):
        """Handles GET requests, will send challenge back to twitch to register webhook.

           """
        query = urlparse(self.path).query
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        try:
            query_components = dict(qc.split("=") for qc in query.split("&"))
            challenge = query_components["hub.challenge"]
            # s = ''.join(x for x in challenge if x.isdigit())
            # print(s)
            # print(challenge)
            self.send_response(HTTPStatus.OK)
            self.end_headers()
            self.wfile.write(bytes(challenge, "utf-8"))
        except:
            query_components = None
            challenge = None
            self._set_response()
            self.wfile.write(bytes("Hello Stranger :)", "utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length).decode()  # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), post_data)

        if self.path == '/cmd/':
            payload = json.loads(post_data)
            try:
                validate(instance=payload, schema=self.schema_cmd)
                self.handle_cmd(payload)
                self._set_response()
                self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
            except ValidationError as validationerror:
                self._set_bad_request('Could not validate request payload for cmd:\n'+str(validationerror))
        else:
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
                    gg = hmac.new(Daemon.WEBHOOK_SECRET.encode(), post_data, algorithm)
                    if not hmac.compare_digest(hashval.encode(), gg.hexdigest().encode()):
                        raise ConnectionError("Hash missmatch.")
            else:
                raise ValueError("not all headers supplied.")
            self._set_response()
            self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

    def handle_cmd(self, post_data):
        """Handles POST requests on /cmd/. These contain a single command with optional arguments supplied by the user via GUI or CLI.

            Parameters:
            ----------
            post_data (dict): Contains the keys `cmd` and `args`.\n
            post_data['cmd'] (str): the command to execute. \n
            post_data['args'] (list): the arguments for the command.

           """
        cmd_executor = {
            'exit': self.cmd_exit,
            'start': self.cmd_start,
            'list': self.cmd_list,
            'remove': self.cmd_remove,
            'add': self.cmd_add,
            'time': self.cmd_time,
        }
        func = cmd_executor[post_data['cmd']]
        func(post_data['args'])

    def cmd_exit(self):
        self.server.exit()
        self._set_response()

    def cmd_start(self):
        self.server.start()
        self._set_response()

    def cmd_remove(self, args):
        try:
            self.server.remove_streamer(args[0])
        except:
            self._set_bad_request('Missing streamer in arguments.')

    def cmd_list(self):
        live, offline = self.server.get_streamers()
        self._set_response()
        msg = "Live: " + live + "\n" + \
              "Offline: " + offline \
                  .encode('utf-8')
        self.wfile.write(msg)

    def cmd_add(self, args):
        try:
            if len(args) > 1:
                self.server.add_streamer(args[0], args[1])
            else:
                self.server.add_streamer(args[0])
        except:
            self._set_bad_request('Missing streamer in arguments.')

    def cmd_time(self, args):
        try:
            self.server.check_interval = int(args[0])
        except ValueError:
            print('\'' + args[0] + '\' is not valid.')
