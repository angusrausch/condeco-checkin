import os
from configparser import ConfigParser
import sys

def get_config(config_filename):
    if not os.path.isfile(config_filename): generate_ini(config_filename)
    config = ConfigParser()
    config.read(config_filename)
    address = config.get("DEFAULT", "Address")
    username = config.get("DEFAULT", "Username")
    password = config.get("DEFAULT", "Password")
    return (username, password), address

def generate_ini(filename):
    with open(filename, "x") as file:
        file.write("""\
[DEFAULT]
Address = https://boeing.condecosoftware.com/Login/Login.aspx
Username = f.m.l@boeing.com
Password = password
                   
[BOOKING]
Country = Australia
Location = 123 Albert Street
Group=L14 - General Desk
Floor=14
WorkspaceType=Desk
Desk=L14-D110
Days=Monday,Tuesday,Wednesday,Thursday,Friday
""")
        file.close()
        print(f"Generated config file as {filename}")
        sys.exit()

def get_booking_details(config_filename):
    config = ConfigParser()
    config.read(config_filename)
    
    bookings = []
    
    for section in config.sections():
        if section.startswith("BOOKING"):
            booking_details = {
                "Country": config.get(section, "Country"),
                "Location": config.get(section, "Location"),
                "Group": config.get(section, "Group"),
                "Floor": config.get(section, "Floor"),
                "WsType": config.get(section, "WorkspaceType"),
                "Desk": config.get(section, "Desk"),
                "Days": config.get(section, "Days").split(",")
            }
            bookings.append(booking_details)
    
    return bookings
