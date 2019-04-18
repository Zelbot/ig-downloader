# BUILTIN
import tkinter as tk
# CUSTOM
from gui import Application


def main():
    """
    Instance the GUI class and start the main loop.
    """
    # Scraper and Driver are initialized inside of Application's __init__
    root = tk.Tk()
    app = Application(root)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_x = int(screen_width / 2 - app.window_width * 0.5)
    window_y = int(screen_height * 0.1)

    root.title('IG Downloader - Github/Zelbot')
    root.geometry(f'{app.window_width}x{app.window_height}'
                  f'+{window_x}+{window_y}')
    root.configure(background=app.border_color)
    root.resizable(width=False, height=False)

    root.mainloop()


if __name__ == '__main__':
    main()
