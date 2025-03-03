# Condeco Checkin

## Automated booking and signin of Condeco Desks

### Setup 
- Setup virtual enviroment
    - Have python installed
    - Setup virtual enviroment
        - Windows 
            - Create enviroment ```py -m venv venv```
            - Activate enviroment ```venv\scripts\activate```
            - Install pip modules ```pip3 install -r requirements.txt```
        - Unix
            - Create enviroment ```python3 -m venv venv```
            - Activate enviroment ```source venv/bin/activate```
            - Install pip modules ```pip3 install -r requirements.txt```

### Simple use
 - Setup config file
    - Run 
        - Windows ```py main.py```
        - Unix ```python3 main.py```
    - Open generated `checkin.ini` file and make following changes
        - Change username and password to match your credentials
        - Open Condeco web app
            - Navigate to 'Personal spaces', 'Booking grid'
            - Copy the top dropdown text EXACTLY to match the corrosponding fields in .ini file
            - Scroll to the desk and copy desk id, 'Lxx-Dxx'
        - Select which days to book for
- To book desks run 
    - Windows ```py main.py --book```
    - Unix ```python3 main.py --book```
- To checkin to desk run
    - Windows ```py main.py --checkin```
    - Unix ```python3 main.py --checkin```

### Add addtional users
For listener use
- Run ```py/python3 main.py --add-user```
- Edit the YAML file to contain correct credentials for that user
*DO NOT EDIT THE KEY

### Cron use
*** Use at your own risk. Check with manager before enabling auto checkin ***
- Cron use is identical other than not having knowledge of enviroment
- Follow above steps to setup config file
- For booking 
    - Make a cron job with the following timings
        - ```5 0 * * 1 ```
            - This runs at 00:05 on Monday mornings
        -  Use whole python path 
            - May use venv
                - TBD
        - Use whole path for script
        - Add in action parameter
            - ```--action book```
        - Add in config parameter
            - Add a ```--config xxx``` where xxx is replace with your config file whole path
            <small>This is required due to cron jobs not having enviroment knowledge</small>
        - Example
            ```5 0 * * 1 /bin/python3 /home/user/condeco-autobook/main.py --action book --config /home/user/condeco-autobook/checkin.ini```

- For Check in
    - Make a cron job with the following timings
        - ```0 7 * * 1-5 ```
            - This runs at 07:00 on Mondays - Fridays
        -  Use whole python path 
        - Use whole path for script
        - Add in action parameter
            - ```--action checkin```
        - Add in config parameter
            - Add a ```--config xxx``` where xxx is replace with your config file whole path
            <small>This is required due to cron jobs not having enviroment knowledge</small>
        - Example
            ```5 0 * * 1 /bin/python3 /home/user/condeco-autobook/main.py --action checkin --config /home/user/condeco-autobook/checkin.ini```

### Listen for checkin
*** Use at your own risk. Check with manager before enabling auto checkin ***
This option allows you to have your server setup to listen to HTTP requests and can sign in the user when it recieves a request. This can be set with different ports and can be multitenanted using the Credential Key to check in each user. 
This is done by access `address:port/checkin?key=credential_key` in a web browser. On Iphone this can setup with a shortcut to open the website and an automation to run when arriving at work.
To set this up you must set the script to run as a system service on linux to always be listening for requests
- Setting up a system service (Linux Only)
    - Create a service file
        ```sudo vim /etc/systemd/system/condeco-checkin.service```
        - Put contents in file 
        ```
            [Unit]
            Description=Condeco Checkin Service
            After=network.target

            [Service]
            ExecStart=[full directory path]/venv/bin/python3 [full directory path]/main.py --listen
            WorkingDirectory=[full directory path]
            Restart=always
            User=[user]
            Group=[group or user]

            [Install]
            WantedBy=multi-user.target
        ```
    - Reload systemctl daemon
        ```sudo systemctl daemon-reload```
    - Enable system service
        ```sudo systemctl enable condeco-checkin.service```
    - Start system service
        ```sudo systemctl start condeco-checkin.service```
    - Test from local network by going to `[ip]:[port]/checkin?key=[key]` on your web browser

To access when away from home either setup a port forwarding rule in router and use DDNS to have constant hostname or use persistent VPN connection
