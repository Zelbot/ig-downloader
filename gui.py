# BUILTIN
import inspect
import re
import tkinter as tk
from tkinter import ttk
# PIP
from bs4 import BeautifulSoup
# CUSTOM
from driver import Driver
from scraping import Scraper

LIGHT_GREY = "#e1e1ff"  # (225, 225, 255)
ALT_GREY = '#dcdcdc'  # (220, 220, 220)
MID_GREY = "#afafaf"  # (175, 175, 175)
DARK_GREY = '#555555'  # (85, 85, 85)


class Application:
    """
    Main window of the program.
    """
    window_width = 1000
    window_height = 600

    border_width = 5
    border_color = 'black'

    __slots__ = (
        'root',
        'left_frame', 'url_label', 'url_entry', 'check_button', 'url_check_label', 'start_dl_button',
        'mid_frame', 'url_tracking_label', 'url_tracking_text',
        'right_frame', 'log_text',
        'bottom_frame', 'download_tracking_label', 'download_tracking_bar',
        'scraper', 'driver', 'login', 'extraction_methods'
    )

    def __init__(self, root):
        self.root = root

        self.left_frame = tk.Frame()
        self.url_label = tk.Label()
        self.url_entry = tk.Entry()
        self.check_button = tk.Button()
        self.url_check_label = tk.Label()
        self.start_dl_button = tk.Button()
        self.setup_left_frame()

        self.mid_frame = tk.Frame()
        self.url_tracking_label = tk.Label()
        self.url_tracking_text = ScrollText()
        self.setup_mid_frame()

        self.right_frame = tk.Frame()
        self.log_text = ScrollText()
        self.setup_right_frame()

        self.bottom_frame = tk.Frame()
        self.download_tracking_label = tk.Label()
        self.download_tracking_bar = ttk.Progressbar()
        self.setup_bottom_frame()

        # Initialise classes here so we can pass the logging widget
        self.scraper = Scraper(self.log_text)
        self.driver = Driver(self.log_text)
        self.driver.start_driver()  # Start webdriver to be used for scraping
        self.login = None
        self.extraction_methods = {}

    def setup_left_frame(self):
        """
        Set up the left frame of the application's window.
        """
        self.left_frame = tk.Frame(
            self.root,
            bg=MID_GREY,
            width=self.window_width / 3,
            height=self.window_height - self.border_width * 40,
            highlightbackground=self.border_color,
            highlightcolor=self.border_color,
            highlightthickness=self.border_width,
        )
        self.left_frame.grid(row=0, column=0)
        self.left_frame.grid_propagate(False)  # Keep the frame from automatically resizing

        self.url_label = tk.Label(
            self.left_frame,
            bg=MID_GREY,
            text='Enter URLs:',
            font=('Arial', 15, 'bold')
        )
        self.url_label.place(relx=0.5, rely=0.3, anchor='center')

        self.url_entry = tk.Entry(
            self.left_frame,
            width=int(self.left_frame.winfo_reqwidth() * 0.1),
            borderwidth=3,
        )
        self.url_entry.bind('<Return>', lambda e: self.check_url(self.url_entry))
        self.url_entry.place(relx=0.5, rely=0.4, anchor='center')

        self.check_button = tk.Button(
            self.left_frame,
            text='OK',
            bg='black',
            fg='white',
            activebackground=DARK_GREY,
            font=('Arial', 12),
            cursor='hand2'
        )
        self.check_button.bind('<ButtonRelease-1>', lambda e: self.check_url(self.url_entry))
        self.check_button.place(relx=0.5, rely=0.5, anchor='center')

        self.url_check_label = tk.Label(
            self.left_frame,
            bg=MID_GREY,
            font=('Arial', 12)
        )
        self.url_check_label.place(relx=0.5, rely=0.6, anchor='center')

        self.start_dl_button = tk.Button(
            self.left_frame,
            text='Start Downloading',
            bg='black',
            fg='white',
            activebackground=DARK_GREY,
            font=('Arial', 12),
            cursor='hand2'
        )
        self.start_dl_button.bind('<ButtonRelease-1>', self.download_files)
        self.start_dl_button.place(relx=0.5, rely=0.7, anchor='center')

    def setup_mid_frame(self):
        """
        Set up the middle frame of the application's window.
        """
        self.mid_frame = tk.Frame(
            self.root,
            bg=MID_GREY,
            width=self.window_width / 3,
            height=self.window_height - self.border_width * 40,
            highlightbackground=self.border_color,
            highlightcolor=self.border_color,
            highlightthickness=self.border_width,
        )
        self.mid_frame.grid(row=0, column=1)
        self.mid_frame.grid_propagate(False)
        # Keep the frame border from disappearing by adding weights
        self.mid_frame.rowconfigure(1, weight=1)
        self.mid_frame.columnconfigure(0, weight=1)

        self.url_tracking_label = tk.Label(
            self.mid_frame,
            bg=MID_GREY,
            text='Saved URLs:',
            font=('Arial', 15, 'bold'),
        )
        self.url_tracking_label.place(relx=0.5, rely=0.04, anchor='center')
        # Retroactively scale the mid_frame's first row to make space for the tracking label
        self.mid_frame.rowconfigure(0, weight=1, minsize=self.url_tracking_label.winfo_reqheight())

        self.url_tracking_text = ScrollText(
            self.mid_frame,
            bg=MID_GREY,
            font=('Arial', 10),
            borderwidth=0,
        )
        self.url_tracking_text.grid(row=1, column=0, sticky='ew')

    def setup_right_frame(self):
        """
        Set up the right frame of the application's window.
        """
        self.right_frame = tk.Frame(
            self.root,
            bg=MID_GREY,
            width=self.window_width / 3,
            height=self.window_height - self.border_width * 40,
            highlightbackground=self.border_color,
            highlightcolor=self.border_color,
            highlightthickness=self.border_width,
        )
        self.right_frame.grid(row=0, column=2)
        self.right_frame.grid_propagate(False)
        self.right_frame.columnconfigure(0, weight=1)
        self.right_frame.rowconfigure(0, weight=1)

        self.log_text = ScrollText(
            self.right_frame,
            bg=MID_GREY,
            font=('Arial', 10),
            borderwidth=0,
        )
        self.log_text.grid(sticky='nsew')

    def setup_bottom_frame(self):
        """
        Set up the bottom frame of the application's window.
        """
        self.bottom_frame = tk.Frame(
            self.root,
            bg=MID_GREY,
            width=self.window_width,
            height=self.border_width * 40,
            highlightbackground=self.border_color,
            highlightcolor=self.border_color,
            highlightthickness=self.border_width,
        )
        self.bottom_frame.grid(row=1, column=0, columnspan=3)
        self.bottom_frame.grid_propagate(False)

        self.download_tracking_label = tk.Label(
            self.bottom_frame,
            bg=MID_GREY,
            text='Downloaded 0 / 0 files',
            font=('Arial', 15, 'bold')
        )
        self.download_tracking_label.place(relx=0.5, rely=0.2, anchor='center')

        style = ttk.Style()
        # ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')
        style.theme_use('alt')
        style.configure('black.Horizontal.TProgressbar', foreground='red', background='black')
        self.download_tracking_bar = ttk.Progressbar(
            self.bottom_frame,
            style='black.Horizontal.TProgressbar',
            orient='horizontal',
            length=self.window_width * 0.8,
            mode='determinate',
        )
        self.download_tracking_bar.place(relx=0.5, rely=0.5, anchor='center')

    def check_url(self, entry):
        """
        Check the entered text of the given entry to see if it's accepted
        (link to .jpg, .png, .gif, or an Instagram post).
        Then process the URL as needed.
        """
        text = entry.get().strip()
        if not text:
            return

        # Make sure only posts are specified, not user's pages
        ig_url_re = re.compile(r'^https://www\.instagram\.com/p/.+/')
        general_img_re = re.compile(r'^https?://.+\..+\..+\.(?:jpg|png|gif)')
        imgur_re = re.compile(r'^https://imgur\.com/(?:.)+$(?<!(png|gif|jpg))')

        youtube_re = re.compile('https://(?:www\.)?youtube\.com/watch\?v=.+')
        yt_re = re.compile(r'https://youtu\.be/.+')

        # Map URLs to the methods needed to extract the images in them
        # All of these methods take a single argument, the URL/text
        exprs = {
            ig_url_re: self.process_ig_url,
            general_img_re: self.process_general_url,
            imgur_re: self.process_imgur_url,
            youtube_re: self.process_yt_url,
            yt_re: self.process_yt_url,
        }

        if not any(regex.match(text) for regex in exprs.keys()):
            self.url_check_label.configure(text='ERR: URL not accepted', fg='red')
            return

        if text in self.scraper.image_links or text in self.scraper.display_links:
            self.url_check_label.configure(text='WARN: URL already added.', fg='brown')
            return

        # In case a URL gets ctrl+v'd into the entry multiple times
        if any(link in text for link in self.scraper.image_links + self.scraper.display_links):
            self.url_check_label.configure(text='WARN: URL already added.', fg='brown')
            return

        self.url_check_label.configure(text='OK: URL accepted', fg='black')
        self.process_url(exprs, text)

        entry.delete(0, tk.END)

    def process_url(self, exprs, url):
        """
        Differentiate between links to images and links to Instagram posts.
        Extract images from Instagram posts if needed.
        """
        for regex in exprs.keys():
            # Guaranteed to happen for at least one regex
            if regex.match(url):
                extraction_method = exprs[regex]
                extraction_method(url)
                break

        self.scraper.display_links.append(url)
        self.url_tracking_text.display_these_lines(self.scraper.display_links)
        self.download_tracking_label.configure(
            text=f'Downloaded 0 / {len(self.scraper.download_links)} files'
        )

        self.log_text.newline('URL processing complete')
        self.log_text.newline('.')

    def process_general_url(self, url):
        """
        Append a link directly pointing to an image to the lists
        as no further actions are needed.
        """
        self.scraper.download_links.append(url)
        self.scraper.image_links.append(url)
        self.log_text.newline('Added singular image:')
        self.log_text.newline(f' -  {url}')

    def process_ig_url(self, url):
        """
        Prepare data and handle extraction of images of Instagram posts.
        """
        self.driver.webdriver.get(url)
        self.log_text.newline('Got URL')
        soup = BeautifulSoup(self.driver.webdriver.page_source, features='html.parser')
        data = self.scraper.get_data(soup)
        self.log_text.newline('Extracted JSON data')

        if self.scraper.is_private(data) and self.driver.is_logged_in is False:
            def show_root(_):
                """
                Needed for the pos arg getting passed with tkinter bindings.
                """
                self.root.deiconify()
                # self.process_url(url)
                self.process_ig_url(url)
                # Not unbinding here would lead to an infinite loop
                # of calling the above function again and again
                self.login.unbind('<Destroy>')

            self.log_text.newline('Login initiated')
            self.create_login_window()
            self.root.withdraw()
            self.login.bind('<Destroy>', show_root)
            return

        # Logging for IG links is done inside of this function already
        self.scraper.extract_ig_images(data)
        self.scraper.image_links.append(url)

    def process_imgur_url(self, url):
        """
        Prepare data needed for extracting images from an Imgur link
        and then actually extract them.
        """
        self.driver.webdriver.get(url)
        self.log_text.newline('Got URL')
        soup = BeautifulSoup(self.driver.webdriver.page_source, features='html.parser')
        self.scraper.extract_imgur_images(soup)

    def process_yt_url(self, url):
        """
        Simply call the scraper's method to keep the method class uniform here.
        """
        self.scraper.extract_yt_images(url)

    def download_files(self, _):
        """
        Wrapper to call the scraper's download method,
        to avoid arg weirdness with tkinter widget bindings.
        Also reset the tracking attributes.
        """
        if not self.scraper.download_links:
            return

        self.scraper.download_files(dl_bar=self.download_tracking_bar)
        self.log_text.newline('Downloading finished')

        self.scraper.download_links = []
        self.scraper.display_links = []

        self.download_tracking_bar['maximum'] = 0
        self.download_tracking_bar['value'] = 0

        self.download_tracking_label.configure(
            text='Downloaded 0 / 0 files'
        )

        self.url_tracking_text.clear_text()

        self.log_text.newline('Reset tracking widgets')
        self.log_text.newline('.')

    def create_login_window(self):
        """
        Create a login window.
        """
        self.login = LoginWindow(self.driver)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_x = int(screen_width / 2 - self.login.window_width * 0.5)
        window_y = int(screen_height * 0.25)

        self.login.title('Login')
        self.login.geometry(f'{self.login.window_width}x{self.login.window_height}'
                            f'+{window_x}+{window_y}')
        self.login.resizable(width=False, height=False)


class LoginWindow(tk.Toplevel):
    """
    Separate login window.
    """
    window_width = 200
    window_height = 150

    __slots__ = (
        'driver', 'username', 'password', 'two_fa',
        'frame', 'username_label', 'username_entry',
        'password_label', 'password_entry',
        'two_fa_label', 'two_fa_entry',
        'confirm_button',
    )

    def __init__(self, driver):
        tk.Toplevel.__init__(self)

        self.driver = driver

        self.username = ''
        self.password = ''
        self.two_fa = ''

        self.frame = tk.Frame(
            self,
            bg=MID_GREY,
            width=self.window_width,
            height=self.window_height,
            highlightthickness=0,
        )

        for i in range(5):
            self.frame.rowconfigure(i, minsize=self.window_height / 5, weight=1)
            self.frame.columnconfigure(i, minsize=self.window_width / 5, weight=1)

        self.frame.grid_propagate(False)
        self.frame.grid(row=0, column=0, sticky='nsew')
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.username_label = tk.Label(
            self.frame,
            bg=MID_GREY,
            font=('Arial', 10),
            text='Username'
        )
        self.username_label.grid(row=0, column=1, columnspan=3, sticky='ew')

        self.username_entry = tk.Entry(self.frame, borderwidth=3)
        self.username_entry.grid(row=1, column=0, columnspan=5, sticky='ew')
        self.username_entry.bind('<Return>', self.main_login)

        self.password_label = tk.Label(
            self.frame,
            bg=MID_GREY,
            font=('Arial', 10),
            text='Password'
        )
        self.password_label.grid(row=2, column=1, columnspan=3, sticky='ew')

        self.password_entry = tk.Entry(self.frame, borderwidth=3, show='*')
        self.password_entry.grid(row=3, column=0, columnspan=5, sticky='ew')
        self.password_entry.bind('<Return>', self.main_login)

        self.two_fa_label = tk.Label(self.frame, bg=MID_GREY, text='2FA')
        self.two_fa_entry = tk.Entry(self.frame)
        self.two_fa_entry.bind('<Return>', self.two_fa_login)

        self.confirm_button = tk.Button(
            self.frame,
            text='OK',
            bg='black',
            fg='white',
            activebackground=DARK_GREY,
            font=('Arial', 12),
            cursor='hand2'
        )
        self.confirm_button.bind('<ButtonRelease-1>', self.main_login)
        self.confirm_button.grid(row=4, column=2, sticky='ew')

        # Using this in a @property results in a RecursionError for some reason
        # So we do it here but in ugly :(
        self.widgets = [value for attr, value in inspect.getmembers(self)
                        if isinstance(value, tk.Widget)]

    def show_two_fa(self):
        """
        Switch from username and password entry to only the 2FA entry.
        """
        for widget in self.widgets:
            if isinstance(widget, tk.Frame):
                continue
            widget.grid_forget()

        self.confirm_button.bind('<ButtonRelease-1>', self.two_fa_login)

        self.two_fa_label.grid(row=1, column=1, columnspan=3, sticky='ew')
        self.two_fa_entry.grid(row=2, column=0, columnspan=5, sticky='ew')
        self.confirm_button.grid(row=3, column=2, sticky='ew')

    def get_login(self):
        """
        Get the texts entered into the username and password entries.
        """
        self.username = self.username_entry.get()
        self.password = self.password_entry.get()

    def get_two_fa(self):
        """
        Get the text entered into the 2FA entry.
        """
        self.two_fa = self.two_fa_entry.get()

    def main_login(self, _):
        """
        Actually log in to Instagram.
        """
        self.get_login()
        if not self.username or not self.password:
            return

        credentials_valid, two_fa_needed = self.driver.main_login(self.username, self.password)

        if credentials_valid is False:
            self.username_label.configure(fg='red')
            self.password_label.configure(fg='red')
            return

        if two_fa_needed is True:
            self.show_two_fa()
            return

        # 2FA not needed, login successful
        self.driver.is_logged_in = True
        self.destroy()

    def two_fa_login(self, _):
        """
        Complete the 2FA step of logging in.
        """
        self.get_two_fa()
        if not self.two_fa:
            return

        login_complete = self.driver.two_fa_login(self.two_fa)
        if login_complete is True:
            self.driver.is_logged_in = True
            self.destroy()
            return

        # Pressing the button to resend the 2FA code is unreliable
        # So we log in again using the already acquired credentials
        # To get another 2FA code sent to us
        self.two_fa_label.configure(fg='red')
        self.driver.main_login(self.username, self.password)


class ScrollText(tk.Text):
    """
    Subclass tk.Text so we can get a text widget
    and create methods that make it easier to use.
    """
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)
        self.configure(state='disabled')

    def newline(self, string):
        """
        Append a string to the already present text.
        """
        content = self.get(1.0, tk.END)
        to_insert = f'{content.strip()}\n{string.strip()}'

        self.configure(state='normal')
        self.delete(1.0, tk.END)
        self.insert(tk.INSERT, f'{to_insert.strip()}')
        self.yview(tk.END)
        self.configure(state='disabled')

    def clear_text(self):
        """
        Delete all text of the widget.
        """
        self.configure(state='normal')
        self.delete(1.0, tk.END)
        self.configure(state='disabled')

    def display_these_lines(self, lines):
        """
        Clear all text and display the given lines.
        """
        self.configure(state='normal')
        self.delete(1.0, tk.END)

        if isinstance(lines, list):
            self.insert(tk.INSERT, '\n'.join([f' {index+1} - {line}'
                                              for index, line in enumerate(lines)]))
        elif isinstance(lines, str):
            self.insert(tk.INSERT, lines)
        else:
            raise TypeError(f'Expected str or list, got {type(lines)} instead.')

        self.yview(tk.END)
        self.configure(state='disabled')
