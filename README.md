## Installation

This program mostly works by using Selenium, specifically a Chrome driver.  
It is **required** that you download a Chrome driver binary and specify the path to it in the config.

Other than that, it is recommended to set up a virtual env and install the required modules:  
```bash
python -m venv venv
source venv/bin/activate  
python -m pip install -r requirements.txt  
```
LPT: If you want to find out what to put in your config, `grep "config\." *.py` makes it a lot easier.

## Sidenote
This started out as a way to ease the downloads of images uploaded to Instagram (hence the name),
but support for a couple more websites has been added along the way.  
If you're curious as to what URLs will be accepted, you can take a look at the regex collection inside of the
Application class's \_\_init\_\_ method (located in gui.py).
