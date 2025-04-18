import subprocess
from user import User
from payload_generator import Payload_Generator
import json
import requests
from datetime import datetime, timedelta
from custom_exceptions import AuthenticationError
from config_input import get_phone_ip
import traceback

class Checkin:
    def __init__(self, config, args = None, key = None):
        self.input_file = args.input_file if args.input_file else None
        self.output_file = args.output_file if args.output_file else None
        self.dry_run = args.dry_run
        self.booking_save = args.save_booking_info
        self.check_home = args.check_home
        self.config = config

        self.user = User(config, key)

        self.checkin()

    def checkin(self):
        if not self.user.logged_in[0]:
            raise AuthenticationError("User not logged in")
        if self.check_home: 
            if self.check_phone_is_home():
                print("Not checking in as User is found to be home")
                return
        bookings = self.get_upcoming_bookings()
        if bookings:
            try:
                payload_generator = Payload_Generator(bookings)
            except (KeyError, IndexError) as e:
                raise KeyError(f"Error in payload generation:\n")
                traceback.print_exc()
            else:
                if self.output_file:
                    with open(self.output_file, "w", encoding="utf-8") as file:
                            file.write("Checkin Output\n")
                            file.close()
                for payload in payload_generator.get_payloads():
                    if self.output_file:
                        contents = json.dumps(payload, indent=2)
                        with open(self.output_file, "a", encoding="utf-8") as file:
                            file.write(contents)
                    if self.dry_run:
                        if self.dry_run == "p":
                            print(json.dumps(payload))
                        elif self.dry_run == "f":
                            print(json.dumps(payload, indent=2))
                    if not self.output_file and not self.dry_run:
                        api_address = f"{self.user.address}/EnterpriseLite/api/Booking/ChangeBookingState?ClientId={self.user.user_id_long.split('=')[1]}"
                        headers = {
                            "Authorization": f"Bearer {self.user.elite_session_token}",
                            "Content-Type": "application/json; charset=utf-8"
                        }

                        checkin_response = self.user.session.put(api_address, json=payload, headers=headers)
                        checkin_response.raise_for_status()
                        self.success = (True)
                print("Successfully Checked In")
        else: 
            print("Bookings info request failed")

    def get_upcoming_bookings(self):
        # Debugger
        if self.input_file:
            try:
                with open(self.input_file, "r", encoding="utf-8") as file:
                    bookings = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error reading JSON file:")
                traceback.print_exc()
                exit()
        # Normal Operation
        else:
            try:
                api_url = f"{self.user.address}/EnterpriseLite/api/Booking/GetUpComingBookings"

                start_date, end_date = self.get_date_range()
                params = {"startDateTime": start_date, "endDateTime": end_date}

                response = self.user.session.get(api_url, params=params)
                response.raise_for_status()  

                bookings = response.json()
            except requests.RequestException as e:
                print("Error fetching upcoming bookings:")
                traceback.print_exc()
                exit()

        if self.booking_save:
            file =open(self.booking_save, "w")
            json.dump(bookings, file, indent=2)
            exit()

        if type(bookings) == dict:
            bookings = [bookings]
        if type(bookings) == list: 
            return bookings
        else:
            raise ValueError("Invalid or null return from request")
        
    def check_phone_is_home(self):
        try:
            phone_ip = get_phone_ip(self.config, self.user.credentials[0])
            ping_command = ["ping", phone_ip, "-c", "5"]
            ping_output = subprocess.run(ping_command, capture_output=True, text=True)
            if not any(loss in str(ping_output) for loss in ("100% packet loss", "100.0% packet loss")):
                return True
        except subprocess.SubprocessError as e: 
            print(f"ERROR checking ip is present (BACKUP TO CHECKIN):\n")
            traceback.print_exc()
        return False

    def get_date_range(self):
        today = datetime.today()
        yesterday = today - timedelta(days=1)
        
        start_date = yesterday.replace(hour=14, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=13, minute=59, second=59, microsecond=0)
        return start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")
