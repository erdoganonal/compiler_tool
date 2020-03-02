"The Console Layout"
import re

import tkinter as tk

from layout_base import Fore, COLORS


class Output:
    "Redirect to output the console which created by tkinter Text"
    _COLOR_DICT = {
        Fore.BLACK: {"foreground": COLORS["BLACK"]},
        Fore.RED: {"foreground": COLORS["RED"]},
        Fore.GREEN: {"foreground": COLORS["GREEN"]},
        Fore.YELLOW: {"foreground": COLORS["YELLOW"]},
        Fore.BLUE: {"foreground": COLORS["BLUE"]},
        Fore.MAGENTA: {"foreground": COLORS["MAGENTA"]},
        Fore.CYAN: {"foreground": COLORS["CYAN"]},
        Fore.WHITE: {"foreground": COLORS["WHITE"]},
        Fore.RESET: {"foreground": COLORS["WHITE"]},

        Fore.BOLD_BLACK: {"foreground": COLORS["BLACK"], "font": "bold"},
        Fore.BOLD_RED: {"foreground": COLORS["RED"], "font": "bold"},
        Fore.BOLD_GREEN: {"foreground": COLORS["GREEN"], "font": "bold"},
        Fore.BOLD_YELLOW: {"foreground": COLORS["YELLOW"], "font": "bold"},
        Fore.BOLD_BLUE: {"foreground": COLORS["BLUE"], "font": "bold"},
        Fore.BOLD_MAGENTA: {"foreground": COLORS["MAGENTA"], "font": "bold"},
        Fore.BOLD_CYAN: {"foreground": COLORS["CYAN"], "font": "bold"},
        Fore.BOLD_WHITE: {"foreground": COLORS["WHITE"], "font": "bold"},

        Fore.TITLE: {
            "foreground": COLORS["TITLE"],
            "font": (None, 18, "bold"), "justify": "center"},
        Fore.INFO_WHITE: {
            "foreground": COLORS["INFO_WHITE"],
            "font": (None, 14, "bold"), "justify": "center"},
        Fore.INFO_CYAN: {
            "foreground": COLORS["INFO_CYAN"],
            "font": (None, 14, "bold"), "justify": "center"},
    }

    def __init__(self, text_widget, stderr=False):
        self.text_widget = text_widget
        self.stderr = stderr
        self._config()
        self._is_paused = False
        self._cache = ''
        self._stream = None
        self._color = ''

    def pause(self):
        "Pauses the streaming"
        self._is_paused = True

    def resume(self):
        "Starts the steaming"
        self._is_paused = False
        self.write(self._cache)
        self._cache = ""

    @property
    def is_paused(self):
        "returns True if stream of console has been paused"
        return self._is_paused

    @property
    def stream(self):
        "The file where the console output will be written"
        return self._stream

    @stream.setter
    def stream(self, value):
        "the setter of the file path"
        if value is None:
            # streaming disable
            try:
                self._stream.close()
            except AttributeError:
                pass
            self._stream = None
            return

        self._stream = open(value, 'w')

    @staticmethod
    def _no_color(text):
        ansi_escape = re.compile(r'\x1B[\(\[][0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)

    def _config(self):
        for name, options in self._COLOR_DICT.items():
            self.text_widget.tag_config(name, **options)

    def _write(self, message):
        color = self._color
        regex = re.compile(r"\x1b\[[0-9]{0,2}")

        for char in message:
            # Entire colors starts with '\x1b'
            if char == '\x1b':
                color = '\x1b'
            # Then continue with '['
            elif color == '\x1b' and char == '[':
                color += char
            elif regex.match(color) and not color.endswith('m'):
                if char == 'm':
                    color += char
                else:
                    color += char
            else:
                if color == Fore.RESET:
                    color = ''
                elif color in self._COLOR_DICT:
                    self.text_widget.insert(tk.END, char, color)
                    continue

                self.text_widget.insert(tk.END, char, Fore.RESET)

        self._color = color

    def write(self, message):
        """The class must have write function to catch the
        output which comes through."""
        if self.is_paused:
            self._cache += message
            return

        if self.stream is not None:
            self.stream.write(self._no_color(message))
            self.stream.flush()

        self.text_widget.config(state=tk.NORMAL)

        if self.stderr:
            self.text_widget.insert(tk.END, message, Fore.RED)
        else:
            self._write(message)

        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)

    def flush(self):
        "No need to cache the output. Prints immediately."


class ConsoleLayout:
    "The Console Frame"

    def __init__(self):
        self.text_widget = None
        self._output = None

    def clear_console(self):
        "clears the console"
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete('1.0', tk.END)
        self.text_widget.config(state=tk.DISABLED)

    def render(self, parent, **grid_options):
        "Renders the frame"
        console_frame = tk.Frame(parent)
        console_frame.grid(**grid_options)
        console_frame.rowconfigure(0, weight=1)
        console_frame.columnconfigure(0, weight=1)

        vertical_scrool_bar = tk.Scrollbar(console_frame)
        self.text_widget = tk.Text(
            console_frame,
            yscrollcommand=vertical_scrool_bar.set
        )

        vertical_scrool_bar.config(command=self.text_widget.yview)

        self.text_widget.grid(
            row=0, column=0,
            sticky=tk.NSEW
        )
        vertical_scrool_bar.grid(row=0, column=1, sticky=tk.N+tk.S+tk.W)

        self._output = Output(self.text_widget)

        return console_frame

    @property
    def file(self):
        "returns the file where the output goes"
        return self._output

    def write(self, message):
        "writes the messages to the console"
        self._output.write(message)
