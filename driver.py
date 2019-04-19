# BUILTIN
import time
# PIP
from selenium import webdriver
# CUSTOM
import config


class NoDriverPresent(Exception):
    pass


class Driver:

    __slots__ = ('log_text', 'webdriver', 'is_logged_in')

    def __init__(self, log_text):
        self.log_text = log_text
        self.webdriver = None
        self.is_logged_in = False

    def start_driver(self):
        """
        Start a driver to be used for navigating and scraping pages.
        """
        if self.webdriver is None:
            self.webdriver = webdriver.Chrome(executable_path=config.chromedriver_path,
                                              chrome_options=config.chromedriver_options)
            self.log_text.newline('Started webdriver')
        else:
            self.log_text.newline("Webdriver already present, can't start")

    def quit_driver(self):
        """
        Quit the current driver, if needed.
        """
        if self.webdriver is not None:
            self.webdriver.quit()
            self.webdriver = None
            self.log_text.newline('Quit webdriver')
        else:
            self.log_text.newline("No webdriver started, can't quit")

    def main_login(self, username, password):
        """
        Log in to Instagram (to gain access to private profiles).
        """
        # Main login prompt
        login_url = 'https://www.instagram.com/accounts/login/'
        two_fa_url = 'https://www.instagram.com/accounts/login/two_factor'

        self.webdriver.get(login_url)
        self.log_text.newline('Got to IG login URL')
        time.sleep(0.5)

        iframe = self.webdriver.find_element_by_css_selector('iframe')
        self.webdriver.switch_to.frame(iframe)
        self.log_text.newline('Switched to iframe (login)')
        time.sleep(0.5)

        username_field = self.webdriver.find_element_by_xpath("//input[@name='username']")
        username_field.send_keys(username)

        password_field = self.webdriver.find_element_by_xpath("//input[@name='password']")
        password_field.send_keys(password)
        password_field.send_keys(u'\ue007')  # Enter to confirm

        self.log_text.newline('Entered login credentials and confirmed entries')
        self.log_text.newline('Waiting a little longer here...')
        time.sleep(2.5)

        # Login not successful, credentials are invalid
        if self.webdriver.current_url == login_url:
            self.log_text.newline('Login credentials invalid')
            credentials_valid, two_fa_needed = (False, None)
            return credentials_valid, two_fa_needed

        # Login successful, but 2FA needed
        if self.webdriver.current_url == two_fa_url:
            self.log_text.newline('Login credentials valid but 2FA is enabled')
            credentials_valid, two_fa_needed = (True, True)
            return credentials_valid, two_fa_needed

        # Login successful, got to main page
        credentials_valid, two_fa_needed = (True, False)
        return credentials_valid, two_fa_needed

    def two_fa_login(self, two_fa):
        """
        Complete the 2FA step of logging in to Instagram.
        """
        two_fa_url = 'https://www.instagram.com/accounts/login/two_factor'

        iframes = self.webdriver.find_elements_by_css_selector('iframe')
        if iframes:
            self.webdriver.switch_to.frame(iframes[0])
            self.log_text.newline('Switched to iframe (2FA)')
            time.sleep(0.5)

        verification_field = self.webdriver.find_element_by_xpath("//input[@name='verificationCode']")
        verification_field.send_keys(two_fa)
        verification_field.send_keys(u'\ue007')  # Enter to confirm

        self.log_text.newline('Entered 2FA verification code')
        self.log_text.newline('Waiting a little longer here...')
        time.sleep(2.5)

        login_complete = self.webdriver.current_url != two_fa_url
        if login_complete is True:
            self.log_text.newline('Login complete')
            self.log_text.newline('.')
        else:
            self.log_text.newline('2FA code is invalid')
        return login_complete
