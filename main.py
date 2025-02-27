import json
from config_input import get_config, get_booking_details
from payload_generator import generate_payload, generate_secondary_payload
import requests
from bs4 import BeautifulSoup
from humanise import humanise
import argparse
from time import sleep
import traceback
from datetime import datetime, timedelta

class App:
    def __init__(self, config="signin.ini", action = ""):
        try:
            self.credentials, self.address, self.name = get_config(config)
            self.config = config
            if (login_message := self.login()) != True:
                print(login_message[1])
            if action == "book":
                pass
                # self.book()
            elif action == "checkin":
                self.checkin()
        except Exception as e:
            traceback.print_exc()

    def login(self):
        self.session = requests.Session()
        
        login_url = f"{self.address}/login/login.aspx"
        response = self.session.get(login_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        view_state = soup.find("input", {"name": "__VIEWSTATE"})["value"]
        view_state_generator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"]
        event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]
        
        # Prepare login payload
        payload = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": view_state,
            "__VIEWSTATEGENERATOR": view_state_generator,
            "__EVENTVALIDATION": event_validation,
            "txtUserName": self.credentials[0],
            "txtPassword": self.credentials[1],
            "btnLogin": "Sign+In"
        }
        
        # Perform login
        login_response = self.session.post(login_url, data=payload)
        login_response.raise_for_status()
        
        # Extract UserId from HTML response
        user_id_marker = "var int_userID = "
        user_id_start = login_response.text.find(user_id_marker) + len(user_id_marker)
        user_id_end = login_response.text.find(";", user_id_start)
        self.user_id = login_response.text[user_id_start:user_id_end].strip()
        
        if not self.user_id:
            return (False, "Could not extract UserId from HTML")
        
        # Extract userIdLong from cookies
        self.user_id_long = self.session.cookies.get("CONDECO")
        
        if not self.user_id_long:
            return (False, "CONDECO cookie was not retrieved.")
        
        # Retrieve token for Enterprise login
        ent_login_url = f"{self.address}/EnterpriseLiteLogin.aspx"
        ent_response = self.session.get(ent_login_url)
        ent_response.raise_for_status()
        
        soup = BeautifulSoup(ent_response.text, "html.parser")
        token = soup.find("input", {"name": "token"})["value"]
        
        # Authenticate into Enterprise
        auth_url = f"{self.address}/enterpriselite/auth"
        auth_response = self.session.post(auth_url, data={"token": token})
        auth_response.raise_for_status()
        
        self.elite_session_token = self.session.cookies.get("EliteSession")
        if not self.elite_session_token:
            return (False, "EliteSession cookie was not retrieved.")
        
        # Set authorization header
        self.session.headers.update({"Authorization": f"Bearer {self.elite_session_token}"})
        
        return True

    def checkin(self):
        bookings = self.get_upcoming_bookings()
        if bookings:
            primary_payload = generate_payload(bookings)
            secondary_payload = generate_secondary_payload(bookings[1])
            for payload in (secondary_payload, primary_payload):
                # print("\n")
                # print(json.dumps(payload))
                # print("\n")
                api_address = f"{self.address}/EnterpriseLite/api/Booking/ChangeBookingState?ClientId={self.user_id_long.split("=")[1]}"
                headers = {
                    "Authorization": f"Bearer {self.elite_session_token}",
                    "Content-Type": "application/json; charset=utf-8"
                }

                checkin_response = self.session.put(api_address, json=payload, headers=headers)
                checkin_response.raise_for_status()
            
        else: 
            print("Bookings info request failed")

    def get_upcoming_bookings(self):
        try:
            # Define the API endpoint
            api_url = f"{self.address}/EnterpriseLite/api/Booking/GetUpComingBookings"

            # Set the date range
            start_date, end_date = self.get_date_range()
            # Start date needs to be yesterday 14:00:00 end date is today 13:59:59
            # start_date = "2025-02-26 14:00:00" 
            # end_date = "2025-02-27 13:59:59"
            params = {"startDateTime": start_date, "endDateTime": end_date}

            # Make the request (session must have the authentication cookies)
            response = self.session.get(api_url, params=params)
            response.raise_for_status()  # Raise an error for bad responses

            # Parse JSON response
            bookings = response.json()
            # print(json.dumps(bookings))
            return bookings
        except requests.RequestException as e:
            print("Error fetching upcoming bookings:", e)

    def get_date_range(self):
        today = datetime.today()
        yesterday = today - timedelta(days=1)
        
        start_date = yesterday.replace(hour=14, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=13, minute=59, second=59, microsecond=0)
        
        return start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A Condeco auto checkin app.")
    parser.add_argument("--config", type=str, default="checkin.ini", help="Path to the configuration file. Default is 'signin.ini'.")
    parser.add_argument("--action", type=str, help="Action to complete: Options: Book, Checkin")

    args = parser.parse_args()
    if not args.action: print("Action is required, please input action with --action")
    App(config = args.config, action = args.action)
