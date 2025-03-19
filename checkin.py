from user import User
from payload_generator import Payload_Generator
import json
import requests
from datetime import datetime, timedelta
from custom_exceptions import AuthenticationError

class Checkin:
    def __init__(self, config, args = None, key = None):
        self.input_file = args.input_file if args.input_file else None
        self.output_file = args.output_file if args.output_file else None
        self.dry_run = args.dry_run
        self.booking_save = args.save_booking_info

        self.user = User(config, key)

        self.checkin()

    def checkin(self):
        if not self.user.logged_in[0]:
            raise AuthenticationError("User not logged in")
        bookings = self.get_upcoming_bookings()
        if bookings:
            try:
                payload_generator = Payload_Generator(bookings)
            except (KeyError, IndexError) as e:
                raise KeyError(f"Error in payload generation:\n{e.with_traceback()}")
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
                        if self.dry_run == "f":
                            print(json.dumps(payload, indent=2))
                        else: 
                            print(json.dumps(payload))
                    if not self.output_file and not self.dry_run:
                        api_address = f"{self.user.address}/EnterpriseLite/api/Booking/ChangeBookingState?ClientId={self.user.user_id_long.split('=')[1]}"
                        headers = {
                            "Authorization": f"Bearer {self.user.elite_session_token}",
                            "Content-Type": "application/json; charset=utf-8"
                        }

                        checkin_response = self.user.session.put(api_address, json=payload, headers=headers)
                        checkin_response.raise_for_status()
                        self.success = (True)
        else: 
            print("Bookings info request failed")

    def get_upcoming_bookings(self):
        # Debugger
        if self.input_file:
            try:
                with open(self.input_file, "r", encoding="utf-8") as file:
                    bookings = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error reading JSON file: {e}")
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
                raise requests.RequestException()
            except requests.RequestException as e:
                raise requests.RequestException(f"Error fetching upcoming bookings: {e}")

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
        

    def get_date_range(self):
        today = datetime.today()
        yesterday = today - timedelta(days=1)
        
        start_date = yesterday.replace(hour=14, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=13, minute=59, second=59, microsecond=0)
        return start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")
