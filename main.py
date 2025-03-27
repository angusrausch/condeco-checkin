import json
import sys
from config_input import get_config, get_booking_details, get_webserver_config, get_user_list, create_user
from book import Book
from checkin import Checkin
from humanise import humanise
import argparse
from time import sleep
import traceback
from datetime import datetime, timedelta
import socket
import select
from urllib.parse import urlparse, parse_qs
from custom_exceptions import AuthenticationError

class App:
    def __init__(self, args):
        self.args = args
        self.config = "signin.yaml" if not args.config else args.config
        if args.add_user:
            create_user(self.config)
        try:
            if args.listen:
                self.listen_for_activation()
            elif args.checkin:
                self.checkin()
            elif args.book:
                Book(self.config)
            else:
                print("Please select action [checkin, book]")
        except Exception as e:
            traceback.print_exc()

    def checkin(self):
        try:
            Checkin(self.config, self.args)
        except Exception as e:
            print(e)

    def listen_for_activation(self):
        good_response = f"""\
HTTP/1.1 200 OK\r
Content-Type: text/html\r
Set-Cookie: ServerName=Checkin\r
\r
<!doctype html>
<html>
<body style="background-color: green;">
</body>
</html>\r\n"""
        bad_response = f"""\
HTTP/1.1 200 OK\r
Content-Type: text/html\r
Set-Cookie: ServerName=Checkin\r
\r
<!doctype html>
<html>
<body style="background-color: red;">
</body>
</html>\r\n"""
        webserver_address = get_webserver_config(self.config)

        listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        listener_socket.bind(webserver_address)
        listener_socket.listen(1)
        print(f"Server listening @ {webserver_address[0]}:{webserver_address[1]}")

        while True:
            try:
                read_ready_sockets, _, _ = select.select([listener_socket], [], [], 1)

                for ready_socket in read_ready_sockets:
                    client_socket, client_address = ready_socket.accept()

                    client_data = client_socket.recv(4096).decode()
                    lines = client_data.split("\r\n")
                    request_line = lines[0]

                    parts = request_line.split()
                    if len(parts) > 1:
                        url = parts[1]

                        parsed_url = urlparse(url)
                        path = parsed_url.path  
                        query_params = parse_qs(parsed_url.query)

                        key_value = query_params.get("key", [None])[0]
                    http_response = bad_response
                    if path == "/checkin":
                        try:
                            user = get_user_list(self.config)[key_value]
                        except KeyError as e:
                            print(f"{datetime.now()}: key does not relate to user: {key_value}")
                        else:
                            try:
                                Checkin(config=self.config, args=self.args, key=key_value)
                            except AuthenticationError as e:
                                print(f"{datetime.now()}: {e}")
                            except KeyError as e:
                                print(f"{datetime.now()}: {e}")
                            except Exception as e:
                                print(f"{datetime.now()}: Failed to check in user\n{e}")
                            else:
                                http_response = good_response
                                print(f"{datetime.now()}: Checked in user: {user['Name']}")
                    else:
                        print(f"{datetime.now()}: Unknown Path: {path}")

                    client_socket.sendall(http_response.encode("utf-8"))

                    try:
                        client_socket.close()
                    except OSError:
                        pass
            except Exception as e:
                print(f"\n{datetime.now()}: An unhandled error occured: {e.__traceback__}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A Condeco auto checkin app.")
    parser.add_argument("--config", type=str, default="checkin.yaml", help="Path to the configuration file. Default is 'signin.ini'.")
    parser.add_argument("--checkin", action="store_true", help="Check into desk for the day")
    parser.add_argument("--book", action="store_true", help="Book desk - currently unavailable")
    parser.add_argument("--listen", action="store_true", help="Turn on server to listen for checkin")
    parser.add_argument("--add-user", action="store_true", help="Add additional user to config. For use with listen")
    parser.add_argument("--input-file", help="Debugger to run from a json file containing the json data")
    parser.add_argument("--output-file", help="Debugger to saved output to a file")
    parser.add_argument("--dry-run", default=False, nargs="?", const=True, help="Print output instead of sending to server | Use \"f\" to format as json in output")
    parser.add_argument("--save-booking-info", help="Saves the booking input as json")
    args = parser.parse_args()
    App(args)
