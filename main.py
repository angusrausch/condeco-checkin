from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config_input import get_config, get_booking_details
from humanise import humanise
import argparse
from time import sleep
import traceback

class App:
    def __init__(self, config="signin.ini", action = ""):
        action = action.lower()
        self.driver = webdriver.Firefox()
        try:
            self.credentials, self.address = get_config(config)
            self.config = config
            self.login()
            if action == "book":
                self.book()
            elif action == "checkin":
                self.checkin()
        except Exception as e:
            traceback.print_exc()
        self.driver.close()

    def login(self):
        self.driver.get(self.address + "/login")
        username_field = self.driver.find_element(By.NAME, 'txtUserName')
        password_field = self.driver.find_element(By.NAME, 'txtPassword')
        login_button = self.driver.find_element(By.NAME, 'btnLogin')
        
        humanise(0)
        username_field.send_keys(self.credentials[0])
        humanise(0)
        password_field.send_keys(self.credentials[1])
        login_button.click()
        humanise(2)
    
    def book(self):
        bookings_details = get_booking_details(self.config)
        for booking_detail in bookings_details:
            nav_frame = self.driver.find_element(By.ID, "leftNavigation")
            main_frame = self.driver.find_element(By.ID, "mainDisplayFrame")
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(nav_frame)
            self.driver.find_element(By.ID, "DeskBookingHeader").click()
            self.driver.find_element(By.ID, "li_bookingGrid_desk").click()
            humanise(5)
            for key, value in booking_detail.items():
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(main_frame)
                if key in ("Desk", "Days"): continue
                selection_box = Select(self.driver.find_element(By.ID, 'cmb'+key))
                selection_box.select_by_visible_text(value)
                humanise(3)
            backend_room_id = self.get_room_id(booking_detail["Desk"])

    def get_room_id(self, room_name):
        room_element = self.driver.find_element(By.XPATH, f"//th//strong[text()='{room_name}']/ancestor::th")
        room_id = room_element.find_element(By.XPATH, ".//a").get_attribute("data-room-id")
        return room_id

    def checkin(self):
        main_frame = self.driver.find_element(By.ID, "mainDisplayFrame")
        humanise(10, 360)
        self.driver.switch_to.frame(main_frame)
        button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Check in')]"))
        )
        button.click()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A Selenium automation script with argument passing.")
    parser.add_argument("--config", type=str, default="checkin.ini", help="Path to the configuration file. Default is 'signin.ini'.")
    parser.add_argument("--action", type=str, help="Action to complete: Options: Book, Checkin")

    args = parser.parse_args()
    if not args.action: print("Action is required, please input action with --action")
    App(config = args.config, action = args.action)
