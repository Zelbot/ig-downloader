# PIP
from selenium import webdriver


chromedriver_path = '/absolute/path/to/chromedriver'

chromedriver_options = webdriver.ChromeOptions()
chromedriver_options.add_argument('window-size=1200x600')

desired_capabilities = {'loggingPrefs': {'browser': 'INFO'}}

headers = {'User-Agent': ('Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:69.0)'
                          ' Gecko/20100101 Firefox/69.0')}


tumblr_ascii_logo = (
    '<!--'
    '\n       .o                                8888       8888'
    '\n      .88                                8888       8888'
    '\n    o8888oo  ooo  oooo  ooo. .oo.  .oo.   888oooo.   888  oooo d8b'
    '\n    ""888""  888  "888  "888P"Y88bP"Y88b  d88\' `88b  888  "888""8P'
    '\n      888    888   888   888   888   888  888   888  888   888'
    '\n      888 .  888   888   888   888   888  888.  888  888   888'
    '\n      "888Y  `V88V"V8P\' o888o o888o o888o 88`bod8P\' o888o d888b'
    '\n'
    '\n                                                                        -->'
)
