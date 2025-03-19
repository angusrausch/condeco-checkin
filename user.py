from bs4 import BeautifulSoup
import requests
from config_input import get_user_list, get_config
from custom_exceptions import AuthenticationError

class User:
    def __init__(self, config, key = None):
        self.credentials, self.address, self.name = get_config(config, key)

        self.session = requests.Session()
        
        login_url = f"{self.address}/login/login.aspx"
        response = self.session.get(login_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        view_state = soup.find("input", {"name": "__VIEWSTATE"})["value"]
        view_state_generator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"]
        event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]
        
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
        
        login_response = self.session.post(login_url, data=payload)
        login_response.raise_for_status()
        
        user_id_marker = "var int_userID = "
        user_id_start = login_response.text.find(user_id_marker) + len(user_id_marker)
        user_id_end = login_response.text.find(";", user_id_start)
        self.user_id = login_response.text[user_id_start:user_id_end].strip()
        
        if not self.user_id:
            self.logged_in = (False, "Could not extract UserId from HTML")
        
        self.user_id_long = self.session.cookies.get("CONDECO")
        
        if not self.user_id_long:
            self.logged_in =  (False, "CONDECO cookie was not retrieved.")
        
        ent_login_url = f"{self.address}/EnterpriseLiteLogin.aspx"
        ent_response = self.session.get(ent_login_url)
        ent_response.raise_for_status()
        
        soup = BeautifulSoup(ent_response.text, "html.parser")
        try:
            token = soup.find("input", {"name": "token"})["value"]
        except TypeError as e:
            raise AuthenticationError(f"Failed to authenticate: {e}")

        auth_url = f"{self.address}/enterpriselite/auth"
        auth_response = self.session.post(auth_url, data={"token": token})
        auth_response.raise_for_status()
        
        self.elite_session_token = self.session.cookies.get("EliteSession")
        if not self.elite_session_token:
            self.logged_in = (False, "EliteSession cookie was not retrieved.")
        
        self.session.headers.update({"Authorization": f"Bearer {self.elite_session_token}"})
        
        self.logged_in = (True, False)