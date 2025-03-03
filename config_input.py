import os
import sys
import yaml
import random
import string


def get_config(config_filename, user=None):
    """Fetch credentials from the YAML config file (assuming only one exists)."""
    if not os.path.isfile(config_filename):
        raise FileNotFoundError(f"Config file '{config_filename}' not found.")

    with open(config_filename, "r") as file:
        config = yaml.safe_load(file)

    # If user is provided, look for the corresponding credentials in the list
    if user:
        credentials = next(
            (cred for cred in config.get("CREDENTIALS", []) if cred.get("Key") == user or cred.get("Name") == user),
            None
        )
    else:
        # If no user is provided, and CREDENTIALS is a list, pick the first item
        credentials = config.get("CREDENTIALS", [{}])[0]

    if not credentials:
        raise ValueError("No credentials found in the configuration file.")

    # Returning credentials in the desired format
    return (credentials["Username"], credentials["Password"]), credentials["Address"], credentials["Name"]


def get_user_list(config_filename):
    """Extract all users from the YAML config file."""
    if not os.path.isfile(config_filename):
        generate_yaml(config_filename)

    with open(config_filename, "r") as file:
        config = yaml.safe_load(file)

    user_dict = {}
    for cred in config.get("CREDENTIALS"):
        key = cred.get("Key")
        if key:
            user_dict[key] = {
                "Address": cred["Address"],
                "Username": cred["Username"],
                "Password": cred["Password"],
                "Name": cred["Name"],
            }
    return user_dict


def get_webserver_config(config_filename):
    """Fetch web server configuration from YAML."""
    if not os.path.isfile(config_filename):
        generate_yaml(config_filename)

    with open(config_filename, "r") as file:
        config = yaml.safe_load(file)

    webserver = config.get("WEBSERVER", {})
    address = webserver.get("Address", "0.0.0.0")

    try:
        port = int(webserver.get("Port", 8888))
    except ValueError:
        print("Cannot parse port from config. Please ensure it is an integer.")
        sys.exit()

    return address, port

def create_user(filename):
    try:
        # Load existing YAML content
        with open(filename, 'r') as file:
            data = yaml.safe_load(file)
    except FileNotFoundError:
        generate_yaml(filename)
        with open(filename, 'r') as file:
            data = yaml.safe_load(file)
    except yaml.scanner.ScannerError:
        print("Malformed YAML detected\nPlease fix configuration file")
        sys.exit()

    if "CREDENTIALS" not in data:
        data["CREDENTIALS"] = []
    
    # Append the new credential
    random_key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    new_credentials = {
        "Address": "https://boeing.condecosoftware.com",
        "Username": "f.m.l@boeing.com",
        "Password": "",
        "Name": "First Last *MUST MATCH EXACTLY YOUR CONDECO NAME",
        "Key": random_key
    }
    data["CREDENTIALS"].append(new_credentials)
    
    # Write back to the file
    with open(filename, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)
    
    print("Credential added successfully.")
    print(f"""
Credential added successfully 
Please change {filename} to add user infromation
*** Do not modify key value ***
          """)
    sys.exit()

def generate_yaml(filename):
    """Generate a default YAML configuration file."""
    random_key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

    default_config = {
        "WEBSERVER": {
            "Address": "0.0.0.0",
            "Port": 8888
        },
        "CREDENTIALS": 
        {
            "Address": "https://boeing.condecosoftware.com",
            "Username": "f.m.l@boeing.com",
            "Password": "password",
            "Name": "First Last *MUST MATCH EXACTLY YOUR CONDECO NAME",
            "Key": random_key
        },
        "BOOKING": [
            {
                "Country": "Australia",
                "Location": "123 Albert Street",
                "Group": "L14 - General Desk",
                "Floor": "14",
                "WorkspaceType": "Desk",
                "Desk": "L14-D110",
                "Days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            }
        ]
    }

    with open(filename, "w") as file:
        yaml.dump(default_config, file, default_flow_style=False)

    print(f"Generated config file as {filename}")
    sys.exit()


def get_booking_details(config_filename):
    """Retrieve booking details from YAML config."""
    if not os.path.isfile(config_filename):
        generate_yaml(config_filename)

    with open(config_filename, "r") as file:
        config = yaml.safe_load(file)

    return config.get("BOOKING", [])
