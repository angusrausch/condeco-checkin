# Condeco Checkin

## Automated booking and signin of Condeco Desks

### Setup 
- Setup virtual enviroment
    - TBD
- Install Selenium pip module
    - TBD

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

### Cron use
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

- For Checkin
    - Make a cron job with the following timings
        - ```0 7 * * 1-5 ```
            - This runs at 07:00 on Mondays - Fridays
        -  Use whole python path 
            - May use venv
                - TBD
        - Use whole path for script
        - Add in action parameter
            - ```--action checkin```
        - Add in config parameter
            - Add a ```--config xxx``` where xxx is replace with your config file whole path
            <small>This is required due to cron jobs not having enviroment knowledge</small>
        - Example
            ```5 0 * * 1 /bin/python3 /home/user/condeco-autobook/main.py --action checkin --config /home/user/condeco-autobook/checkin.ini```