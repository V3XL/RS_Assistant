import time
import argparse
import requests
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

# CONSTANT VARIABLES DO NOT CHANGE UNLESS NEEDED
runescape_login_url = "https://secure.runescape.com/m=weblogin/loginform.ws?mod=www&ssl=1&expired=0&dest=account_settings"
runescape_login_failed_url = "https://secure.runescape.com/m=weblogin/login.ws"
twitch_login_url = "https://www.twitch.tv/login"
runescape_site_key = "6Lcsv3oUAAAAAGFhlKrkRb029OHio098bbeyi_Hv"
twitch_site_key = "6Ld65QcTAAAAAMBbAE8dkJq4Wi4CsJy7flvKhYqX"

# CHANGE THESE VARIABLES
runescape_accounts_file = "accounts.txt"
twitch_accounts_file = "twaccounts.txt"
passed_accounts_file = "passed_prime_accounts.txt"
failed_twitch_accounts_file = "failed_twitch_accounts.txt"
failed_runescape_accounts_file = "failed_runescape_accounts.txt"
email_to_request = "email"
captcha_key = "2captcha_key"
launcher_name = "launcher.bat"
launcher_script_name = "scriptname"


# Loads the chromedriver at specified url
def get_driver():
    driv = webdriver.Chrome("./chromedriver.exe")
    driv.maximize_window()
    driv.set_page_load_timeout(60)
    return driv


# Return contents of a file
def file_information(file_name):
    try:
        with open(file_name) as f:
            lines = f.readlines()

        lines = [x.strip() for x in lines]

        return lines
    except FileNotFoundError:
        print("Could not find file source " + file_name + "\n")
        print("Exiting program...please check if the file is in the current directory.")
        exit(0)


# Gets the captcha id from in.php
def get_captcha_id(captcha_page_url, captcha_site_key):
    captcha_params = {
        "googlekey": captcha_site_key,
        "pageurl": captcha_page_url,
        "method": "userrecaptcha",
        "key": captcha_key,
        "invisible": "1"
    }

    # # Update the invisible param if not runescape captcha key
    # if runescape_site_key not in captcha_site_key:
    #     captcha_params.update({"invisible": "0"})

    # Post request to 2captcha api
    res = requests.post("http://2captcha.com/in.php", params=captcha_params)
    print(res.text)
    return res.text.split("|")[1]


# Gets the captcha token from res.php
def get_captcha_token(captcha_id):
    captcha_params = {
        "id": captcha_id,
        "action": "get",
        "key": captcha_key
    }

    # Get request to 2captcha api
    res = requests.get("http://2captcha.com/res.php", params=captcha_params)
    print(res)

    # Wait for valid request
    while "CAPCHA_NOT_READY" in res.text:
        print("Waiting for response from 2captcha api")
        time.sleep(5)
        res = requests.get("http://2captcha.com/res.php", params=captcha_params)

    return res.text.split("|")[1]


# Returns if we can stop the program
def can_move_to_next(driver, cur_url):
    page_source = driver.page_source

    return "submit_address" in cur_url \
           or "address_change" in cur_url \
           or "password-start-result" in cur_url \
           or "login.ws" in cur_url \
           or "https://www.runescape.com/unavailable" in cur_url \
           or "Please try again" in page_source \
           or "You now have access to your free membership in RuneScape and Old School RuneScape, plus all of the additional Twitch Prime loot." in page_source \
           or "Success" in page_source \
           or "Oops!" in page_source and "It looks like you haven't claimed your loot from Twitch yet." not in page_source \
           or "********" in page_source


# Login form handler runescape.com
def runescape_login(driver, username, password):
    # On runescape account login screen
    print("On the login page")
    username_field = driver.find_element_by_id("login-username")
    password_field = driver.find_element_by_id("login-password")

    print("Placing log in credentials")

    if username not in username_field.text:
        username_field.clear()
        print("Filling username data")
        username_field.send_keys(username)

    print("Filling password data")
    password_field.send_keys(password)

    if runescape_site_key in driver.page_source:
        # Generates the captcha token and executes javascript
        print("RecaptchaV2")

        captcha_id = get_captcha_id(runescape_login_url, runescape_site_key)
        captcha_token = get_captcha_token(captcha_id)
        driver.execute_script("document.getElementById('g-recaptcha-response').innerHTML = '"
                              + captcha_token + "'; onSubmit();")
        time.sleep(3)
        pass
    else:
        print("Clicking the login button")
        driver.find_element_by_id("du-login-submit").click()


# Add the specified email to the account(s)
def add_email_request(driver, cur_url, email, username, password):
    if cur_url == runescape_login_url:
        runescape_login(driver, username, password)
    elif "/account_settings" in cur_url:
        # main account settings page
        print("On the main account settings page")

        driver.find_element_by_link_text("Email and Communication Preferences").click()

    elif "email-register" in cur_url:
        disabled_last_email = False
        print("On the email change screen")

        if "set_address#" in cur_url:
            print("on cancel address form")

            print("Canceling email request")
            driver.find_element_by_id("cancel-request").click()

            disabled_last_email = True

        if "set_address?" in cur_url or disabled_last_email:
            print("On set email form")

            email_input = driver.find_element_by_id("your-email")
            email_input_confirm = driver.find_element_by_id("confirm-email")

            print("Sending email input")
            email_input.send_keys(email)
            email_input_confirm.send_keys(email)

            print("Selecting tos checkbox")
            driver.find_element_by_id("agree-terms-privacy").click()

            time.sleep(1)
            print("Submit information")
            driver.find_element_by_id("register-email").click()


# Add a password request to the account(s)
def add_password_request(driver, cur_url, username, password):
    if cur_url == runescape_login_url:
        runescape_login(driver, username, password)
    elif "/account_settings" in cur_url:
        # main account settings page
        print("On the main account settings page")

        driver.find_element_by_link_text("Change Password").click()
    elif "password_history" in cur_url:
        # Password request page
        print("On the password request page")

        time.sleep(1)
        print("Submit change password request")
        driver.find_element_by_link_text("CHANGE PASSWORD").click()


# Login form handler twitch.tv
def twitch_login(driver, username, password):
    # On twitch login page
    print("On twitch login page")
    # g-recaptcha-response-1
    if "Please complete the reCAPTCHA below." in driver.page_source:
        # Generates the captcha token and executes javascript
        print("Recaptcha")

        captcha_id = get_captcha_id(twitch_login_url, twitch_site_key)
        captcha_token = get_captcha_token(captcha_id)
        driver.execute_script("document.getElementById('g-recaptcha-response').innerHTML = '"
                              + captcha_token + "';")
        time.sleep(3)
        pass

    username_field = driver.find_element_by_xpath("//input[contains(@type,'text')]")
    password_field = driver.find_element_by_xpath("//input[contains(@type,'password')]")

    print("Placing log in credentials")

    if username not in username_field.text:
        username_field.clear()
        print("Filling username data")
        username_field.send_keys(username)

    print("Filling password data")
    password_field.send_keys(password)

    time.sleep(1)

    print("Clicking the login button")
    driver.find_element_by_xpath(
        "/html/body/div[2]/div/div/div/div/div/div[1]/div/div/div[3]/form/div/div[3]/button").click()
    time.sleep(3)


# Add twitch promotion to the account(s)
def add_prime_request(driver, cur_url, tw_user, tw_pass, rs_user, rs_pass):
    if cur_url == twitch_login_url:
        twitch_login(driver, tw_user, tw_pass)
    elif "Featured Channels" in driver.page_source or "twitch.tv/hi" in cur_url or "Discover" in driver.page_source:
        print("Just logged in and on main page.")
        time.sleep(1)
        if "twitch.tv/hi" in cur_url:
            driver.get("https://www.twitch.tv")
            time.sleep(3)

        print("Finding dropdown")
        driver.find_element_by_xpath(
            '//*[@id="root"]/div/div[2]/nav/div/div[3]/div[2]/div/div[1]/div[1]/div/div[1]/button').click()
        time.sleep(3)
        try:
            print("attempting to scroll down")
            actions = ActionChains(driver)
            actions.move_to_element(driver.find_element_by_xpath(
                '//*[@id="root"]/div/div[2]/nav/div/div[3]/div[2]/div/div/div[2]/div/div/div[2]/div/div[3]/div/div/div[1]/div[2]/div/div/div[2]/div[2]/div[2]/p')).perform()
            time.sleep(3)
            print("Selecting claim offer")
            driver.find_element_by_xpath(
                '/html/body/div[1]/div/div[2]/nav/div/div[3]/div[2]/div/div/div[2]/div/div/div[2]/div/div[3]/div/div/div[1]/div[2]/div/div/div[2]/div[3]/div[1]/div/div/button').click()
            time.sleep(3)
        except NoSuchElementException:
            print("Looks like it was already claimed.")
        driver.get("https://www.runescape.com/account/linked-accounts/twitch/redeem")
    elif "/oauth2/authorize" in cur_url:
        print("On twitch authorization page.")
        print("Clicking authorize button")
        driver.find_element_by_xpath("/html/body/div/div/div[6]/form/fieldset/button[1]").click()
    elif "/account/linked-accounts/twitch/redeem?" in cur_url:
        time.sleep(1)
        driver.find_element_by_xpath('//*[@id="l-vista__container"]/section/div/div/button').click()
        time.sleep(2)
    elif "account/linked-accounts" in cur_url:
        print("On the rs login page.")
        print("Clicking yes-log in button")
        driver.find_element_by_link_text("YES - LOG IN").click()
        time.sleep(1)
    elif "loginform.ws" in cur_url:
        runescape_login(driver, rs_user, rs_pass)


# Creates terminal launch file
def make_quantum_shell_script():
    # load rs account list
    runescape_account_list = file_information(runescape_accounts_file)
    index = 0
    length = len(runescape_account_list)

    with open(launcher_name, "w") as writer:
        while index in range(length):
            runescape_acccount_information = runescape_account_list[index].split(":")
            user = runescape_acccount_information[0]
            password = runescape_acccount_information[1]
            writer.write("java -jar launcher.jar -bot {} {} -world 301 -branch lemons -fps "
                         "20 -norender -interactv2 -script {}\n"
                         .format(user, password, launcher_script_name))
            writer.write("TIMEOUT 25\n")
            index += 1


def main():
    email_request = False
    password_request = False
    twitch_request = False
    launcher_request = False
    twitch_verify_request = False;
	twitch_request = False


    # Add mode specific arguments
    parser = argparse.ArgumentParser(description='Process program arguments to run modes.')
    parser.add_argument('--email', help='adds a email request to the account(s)')
    parser.add_argument('--password', help='adds a password request to the account(s)')
    parser.add_argument('--twitch', help='adds a twitch request to the account(s)')
    parser.add_argument('--launcher', help='adds a launcher request from the account list')
    parser.add_argument('--verify', help='Checks whether accounts are verified for prime loot')

    args = parser.parse_args()
    print(args)

    runescape_index = 0
    twitch_index = 0
    failed_tw_i = 0
    failed_rs_i = 0

    if args.email:
        print("email request enabled.")
        email_request = True
    elif args.password:
        print("password request enabled.")
        password_request = True
    elif args.twitch:
        print("twitch request enabled.")
        twitch_request = True
    elif args.launcher:
        print("launcher request enabled.")
        launcher_request = True
    elif args.verify:
        print("verify twitch request enabled.")
        twitch_verify_request = True

    # Load driver & account information
    if twitch_request or twitch_verify_request:
        url = twitch_login_url
    else:
        url = runescape_login_url

    driver = None

    if not launcher_request:
        driver = get_driver()
        driver.get(url)

    # load rs account list first index
    runescape_account_list = file_information(runescape_accounts_file)
    runescape_acccount_information = runescape_account_list[runescape_index].split(":")
    len_rs_list = len(runescape_account_list)
    print("# of runescape accounts:", len_rs_list)

    time.sleep(1)

    # Always start with the first in the list.
    rs_username = runescape_acccount_information[0]
    rs_password = runescape_acccount_information[1]

    twitch_account_list = None
    twitch_acccount_information = None
    tw_user = None
    tw_pass = None
    len_tw_list = 0

    if twitch_request:
        # load twitch account list first index
        twitch_account_list = file_information(twitch_accounts_file)
        twitch_acccount_information = twitch_account_list[twitch_index].split(":")
        len_tw_list = len(twitch_account_list)
        print("# of twitch accounts:", len_tw_list)

        # Always start with the first in the list.
        tw_user = twitch_acccount_information[0]
        tw_pass = twitch_acccount_information[1]

    time.sleep(1)

    if launcher_request:
        make_quantum_shell_script()

    # Run mode
    while email_request or password_request or twitch_request:
        cur_url = driver.current_url
        print(cur_url)

        if runescape_index > len_rs_list or (twitch_request and twitch_index > len_tw_list):
            print("Finished program..")
            driver.quit()
            break
        elif can_move_to_next(driver, cur_url):
            # Skip to next account

            with open(passed_accounts_file, "a") as f:
                print("Saving to file.")
                if not twitch_request:
                    f.write("{}:{}\n".format(rs_username, rs_password))
                elif twitch_request:
                    if "Please try again" in driver.page_source and cur_url == twitch_login_url:
                        print("Failed to login to twitch")
                        with open(failed_twitch_accounts_file, "a") as t:
                            t.write("#{} {}:{}\n".format(str(failed_tw_i), tw_user, tw_pass))
                        twitch_index += 1
                        failed_tw_i += 1
                    elif "Please try again" in driver.page_source and cur_url == runescape_login_failed_url:
                        print("Failed to login to runescape")
                        with open(failed_runescape_accounts_file, "a") as r:
                            r.write("#{} {}:{}\n".format(str(failed_rs_i), rs_username, rs_password))
                        runescape_index += 1
                        failed_rs_i += 1
                    else:
                        f.write(
                            "{}:{}:{}:{}:{}\n".format(rs_username, rs_password,
                                                      "SUCCESS WITH TWITCH & RUNESCAPE",
                                                      tw_user,
                                                      tw_pass))
                        twitch_index += 1
                        runescape_index += 1
                        print("Account met conditions..moving on")

            if twitch_index < len_tw_list:
                twitch_acccount_information = twitch_account_list[twitch_index].split(":")
                tw_user = twitch_acccount_information[0]
                tw_pass = twitch_acccount_information[1]
                print("Current account tw:", tw_user)

            if runescape_index < len_rs_list:
                runescape_acccount_information = runescape_account_list[runescape_index].split(":")
                rs_username = runescape_acccount_information[0]
                rs_password = runescape_acccount_information[1]
                print("Current account rs:", rs_username)

            if twitch_request or twitch_verify_request:
                driver.quit()
                driver = get_driver()

            driver.get(url)
            time.sleep(2)
            pass
        elif email_request:
            add_email_request(driver, cur_url, email_to_request, rs_username, rs_password)
        elif password_request:
            add_password_request(driver, cur_url, rs_username, rs_password)
        elif twitch_request:
            add_prime_request(driver, cur_url, tw_user, tw_pass, rs_username, rs_password)

        time.sleep(1)

    pass


if __name__ == "__main__":
    main()
    pass
