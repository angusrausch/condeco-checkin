from config_input import get_config, get_booking_details
import requests
from bs4 import BeautifulSoup
from humanise import humanise
import argparse
from time import sleep
import traceback

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
            for booking in bookings:
                payload = self.create_payload(booking)
                api_address = f"{self.address}/EnterpriseLite/api/Booking/ChangeBookingState?ClientId={self.user_id_long.split("=")[1]}"
                # checkin_response = self.session.put(api_address, data=payload)
                # checkin_response = self.session.put(api_address, json=payload)
                headers = {
                    "Authorization": f"Bearer {self.elite_session_token}",
                    "Content-Type": "application/json; charset=utf-8"
                }

                checkin_response = self.session.put(api_address, json=payload, headers=headers)
                # print(checkin_response.text)
                checkin_response.raise_for_status()
                # print("Response Body:", checkin_response.text)
                for key, value in payload.items(): print(f"{key}: {value}")
                # print("\n\nResponse Code:", checkin_response.status_code)
                # checkin_json = checkin_response.json()
                # for key, value in checkin_json.items(): print(f"{key}: {value}")
                # print("Check-in completed successfully.\n")
                print("\n\n")
        else: 
            print("Bookings info request failed")

    def get_upcoming_bookings(self):
        try:
            # Define the API endpoint
            api_url = f"{self.address}/EnterpriseLite/api/Booking/GetUpComingBookings"

            # Set the date range
            start_date = "2025-02-24 14:00:00"
            end_date = "2025-02-25 13:59:59"
            params = {"startDateTime": start_date, "endDateTime": end_date}

            # Make the request (session must have the authentication cookies)
            response = self.session.get(api_url, params=params)
            response.raise_for_status()  # Raise an error for bad responses

            # Parse JSON response
            bookings = response.json()
            return bookings
        except requests.RequestException as e:
            print("Error fetching upcoming bookings:", e)

    def create_payload(self, booking):
        payload = booking.copy()  # Make a copy to avoid modifying the original booking
        
        # Set default values for some fields
        payload["bookingStatus"] = 1
        payload["isWorkplace"] = True
        payload["languageId"] = 1
        payload["isAllDayBooking"] = True

        booked_by = {
            "userId": self.user_id,
            "name": self.name,
            "requestorEmail": self.credentials[0]
        }
        payload["bookedBy"] = booked_by

        # Now wrap everything into the "booking" key dynamically from the original data
        payload["booking"] = {
            "IsAllowedWithinCancelBeforeLimit": False,  # You can calculate or assign this based on your logic
            "amReleased": None,  # You can modify based on your business rules
            "approved": False,  # Modify accordingly
            "assetURL": None,  # Assign it dynamically if needed
            "blindManaged": False,  # Set based on the booking's state if needed
            "bookedBy": booked_by,
            "bookedFor": booking.get("bookedFor", None),
            "bookedLocation": booking.get("bookedLocation", "Unknown Location"),  # Dynamically take from booking
            "bookedResourceItemId": booking.get("bookedResourceItemId", 0),
            "bookedResourceName": booking.get("bookedResourceName", "Unknown Resource"),
            "bookingId": booking.get("bookingId", 0),
            "bookingItemId": booking.get("bookingItemId", 0),
            "bookingMetadata": booking.get("bookingMetadata", {}),
            "bookingSource": booking.get("bookingSource", 0),
            "bookingStatus": booking.get("bookingStatus", 0),
            "bookingTitle": booking.get("bookingTitle", ""),
            "bookingType": booking.get("bookingType", 0),
            "businessUnitId": booking.get("businessUnitId", 0),
            "changedByUserId": booking.get("changedByUserId", 0),
            "disableWebCheckIn": booking.get("disableWebCheckIn", False),
            "enableDeskCheckinLocationTimeZone": booking.get("enableDeskCheckinLocationTimeZone", 1),
            "enableMeetingSpacesFloorPlan": booking.get("enableMeetingSpacesFloorPlan", True),
            "enableSelfCertificationOnLocation": booking.get("enableSelfCertificationOnLocation", False),
            "encryptedQuerstringReviewSummary": booking.get("encryptedQuerstringReviewSummary", None),
            "endDateTime": booking.get("endDateTime", ""),
            "endDateTimeUtc": booking.get("endDateTimeUtc", ""),
            "enterpriseBookingSource": booking.get("enterpriseBookingSource", 0),
            "fdCheckedIn": booking.get("fdCheckedIn", None),
            "fdReleased": booking.get("fdReleased", None),
            "floor": booking.get("floor", ""),
            "floorName": booking.get("floorName", ""),
            "floorPlanOnMap": booking.get("floorPlanOnMap", True),
            "hasValidNoticeForExtend": booking.get("hasValidNoticeForExtend", True),
            "individuallyEdited": booking.get("individuallyEdited", False),
            "isWorkplace": booking.get("isWorkplace", None),
            "locationId": booking.get("locationId", 0),
            "locationTimeZone": booking.get("locationTimeZone", ""),
            "managedForAdmin": booking.get("managedForAdmin", False),
            "minutesToExtend": booking.get("minutesToExtend", None),
            "parentBookingId": booking.get("parentBookingId", None),
            "pendingOnGrid": booking.get("pendingOnGrid", False),
            "pmReleased": booking.get("pmReleased", None),
            "preventSpecificSpaceRequests": booking.get("preventSpecificSpaceRequests", False),
            "qrCodeEnabled": booking.get("qrCodeEnabled", False),
            "recurrenceID": booking.get("recurrenceID", 0),
            "requestedBy": booking.get("requestedBy", None),
            "resourceStatus": booking.get("resourceStatus", 0),
            "selfCertificationContent": booking.get("selfCertificationContent", ""),
            "selfCertificationDisagreeContent": booking.get("selfCertificationDisagreeContent", ""),
            "startDateTime": booking.get("startDateTime", ""),
            "startDateTimeUtc": booking.get("startDateTimeUtc", ""),
            "timeZoneId": booking.get("timeZoneId", ""),
            "updateDateTime": booking.get("updateDateTime", None),
            "updateDateTimeUtc": booking.get("updateDateTimeUtc", None),
            "vcId": booking.get("vcId", None),
            "waitList": booking.get("waitList", False),
            "wsTypeId": booking.get("wsTypeId", 2)
        }

        return payload



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A Condeco auto checkin app.")
    parser.add_argument("--config", type=str, default="checkin.ini", help="Path to the configuration file. Default is 'signin.ini'.")
    parser.add_argument("--action", type=str, help="Action to complete: Options: Book, Checkin")

    args = parser.parse_args()
    if not args.action: print("Action is required, please input action with --action")
    App(config = args.config, action = args.action)
