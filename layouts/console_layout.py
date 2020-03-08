"The Console Layout"
import re

import tkinter as tk

from layouts.layout_base import Fore, Output, get_rid_of_coloring

def _add_color(message):
    compile_header_regex = re.compile(
        r"Compiling fileset \".*\" in \".*\" for \".*\""
    )
    no_color_stripped_message = get_rid_of_coloring(message).strip()
    if no_color_stripped_message.startswith("###"):
        message = message.replace(Fore.RESET, '')
        message = f"{Fore.ORANGE}{message}{Fore.RESET}"
    elif no_color_stripped_message.startswith("compiling"):
        message = message.replace(Fore.RESET, '')
        message = f"{Fore.GREEN}{message}{Fore.RESET}"
    elif compile_header_regex.match(no_color_stripped_message):
        message = message.replace(Fore.RESET, '')
        message = f"{Fore.BOLD_WHITE}{message}{Fore.RESET}"
    return message

class ConsoleLayout:
    "The Console Frame"

    def __init__(self, context):
        self.text_widget = None
        self._output = None
        self._context = context

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

        self._output = Output(self.text_widget, apply=_add_color)

        return console_frame

    @property
    def file(self):
        "returns the file where the output goes"
        return self._output

    def __getattr__(self, key):
        try:
            return self.__getattribute__(key)
        except AttributeError:
            return getattr(self._output, key)
