"A base layout, includes common functions"
import os
import re
import enum

import tkinter as tk
from tkinter import ttk

from compiler_helper import UnknownType


CSI = '\033['

COLORS = {
    "BLACK": "black",
    "RED": "#F54D63",
    "GREEN": "#44eb38",
    "YELLOW": "#FCF645",
    "BLUE": "blue",
    "MAGENTA": "magenta",
    "CYAN": "cyan",
    "WHITE": "white",
    "RESET": "white",
    "BG":  "#404040",
    "TITLE": "#F54D63",
    "INFO_WHITE": "#A8BDC7",
    "INFO_CYAN": "cyan",
}


class Fore:
    "ANSI colors"
    BLACK = '\x1b[30m'
    RED = '\x1b[31m'
    GREEN = '\x1b[32m'
    YELLOW = '\x1b[33m'
    BLUE = '\x1b[34m'
    MAGENTA = '\x1b[35m'
    CYAN = '\x1b[36m'
    WHITE = '\x1b[37m'
    RESET = '\x1b[39m'

    # Custom colors
    BOLD_BLACK = '\x1b[40m'
    BOLD_RED = '\x1b[41m'
    BOLD_GREEN = '\x1b[42m'
    BOLD_YELLOW = '\x1b[43m'
    BOLD_BLUE = '\x1b[44m'
    BOLD_MAGENTA = '\x1b[45m'
    BOLD_CYAN = '\x1b[46m'
    BOLD_WHITE = '\x1b[47m'

    TITLE = '\x1b[50m'
    INFO_WHITE = '\x1b[51m'
    INFO_CYAN = '\x1b[52m'

    @classmethod
    def to_dict(cls):
        "returns a dictionary for formatting"
        dictionary = {}
        for key, value in vars(cls).items():
            try:
                if value.startswith(CSI):
                    dictionary[key] = value
            except AttributeError:
                pass
        return dictionary

    @staticmethod
    def no_color(text):
        "gets rid of coloring"
        ansi_escape = re.compile(r'\x1B[\(\[][0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)


DEFAULT_USERNAME = "pt1"
DEFAULT_PASSWORD = "pt1"

PAD = 25
INNER = int(PAD * 1.5)

PADDING = {
    "padx": (INNER, 0),
    "pady": (3, 3)
}

ENTRY_CONFIG = {
    "border": 5,
    "background": COLORS["BG"],
    "foreground": COLORS["WHITE"],
    "highlightbackground": COLORS["RED"]
}

IP_REGEX = re.compile(
    r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}"
    r"([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
)


def _colored(help_msg):
    if ":" in help_msg:
        help_msg = Fore.YELLOW + help_msg.replace(
            ":", ":{0}".format(Fore.CYAN)
        )
    else:
        help_msg = Fore.CYAN + help_msg

    help_msg = help_msg.replace("e.g.", "{0}e.g.".format(Fore.GREEN))

    return help_msg + Fore.RESET


def merge_line_by_line(*texts, offset=2):
    "Merges given text line by line"
    index = 0
    splitted = []
    total_count = 0
    max_lengths = 0
    for text in texts:
        lines = text.splitlines()
        max_length = max([len(line) for line in lines]) + offset
        splitted.append({
            "lines": lines,
            "max_length": max_length
        })
        max_lengths += max_length
        total_count += 1

    merged = ""
    max_lengths += offset * (total_count + 1) + (total_count - 1)
    seperator = Fore.MAGENTA + "#" * max_lengths + Fore.RESET
    while True:
        count = 0
        merged += Fore.MAGENTA + "#" + " " * offset + Fore.RESET
        for idx in range(total_count):
            lines = splitted[idx]
            try:
                merged += _colored(lines["lines"]
                                   [index].ljust(lines["max_length"]))
            except IndexError:
                count += 1
                merged += "".ljust(lines["max_length"])
            if idx == total_count - 1:
                merged += Fore.MAGENTA + "#" + Fore.RESET
            else:
                merged += Fore.MAGENTA + "|" + " " * offset + Fore.RESET
        merged += "\n"
        if count == total_count:
            break
        index += 1
    return seperator + "\n" + merged + seperator


def to_comma_string(enumeration):
    "Concats given enum names with comma"
    return ", ".join([item.name for item in enumeration][0:3])


def _configure(widget):
    properties = {
        "background": COLORS["BG"],
    }

    if isinstance(widget, (ttk.Frame, ttk.Label, ttk.Checkbutton, ttk.OptionMenu, ttk.Menubutton)):
        properties.update(foreground="#6ccae0", font=(None, 9, "bold"))
        style = ttk.Style(widget)
        style.configure(widget.winfo_class(), **properties)
    elif isinstance(widget, (ttk.Button)):
        pass
    else:
        widget.configure(**properties)


def configure(widget):
    "Set some configurations for given widget and its children"
    _configure(widget)
    for child in widget.winfo_children():
        configure(child)


class LayoutBase:
    "A base layout, includes common functions"

    def __init__(self):
        self._grid_props = {"row": 0, "column": 0, "sticky": tk.NW}
        self._bind = {}

    def toggle_children_states(self, widget, attr, skip_first=False):
        "toggles the state of each child. Checks for their parents too"
        if attr.get():
            state = tk.DISABLED
        else:
            state = tk.NORMAL

        for child in widget.winfo_children():
            if skip_first:
                skip_first = False
                continue
            child.configure(state=state)

        # Check for parents
        if not attr.get():
            for function, args in self._bind.items():
                function(*args)

    def get_next_position(self, row, column, inner=0, **kwargs):
        "Returns the current grid values for this component"
        if row:
            self._grid_props["row"] += 1

        if column:
            self._grid_props["column"] += 1

        return_value = self._grid_props.copy()
        if inner:
            return_value["padx"] = (inner * INNER, 0)

        return_value["pady"] = (5, 0)

        if kwargs:
            return_value.update(kwargs)

        return return_value

    @staticmethod
    def _get_enum_value_from_name(name, enum_list):
        for item in enum_list:
            if item.name == name.replace("-", "_"):
                return item.value

        raise UnknownType(name, enum_list)

    @staticmethod
    def _enum_to_name(enum_list):
        return [value.name for value in enum_list]

    @staticmethod
    def _name_to_enum(name, enums):
        name = name.replace("-", "_")
        for item in enums:
            if item.name == name:
                return item
        return None

    @staticmethod
    def _check_iterable_type(iterable):
        temp_list = []
        for item in iterable:
            if isinstance(item, (str, int, bytes)):
                temp_list.append(str(item))
            elif isinstance(item, enum.Enum):
                temp_list.append(item.name.replace("_", "-"))
            else:
                raise ValueError("{!r} is not supported.".format(item))

        return temp_list

    @staticmethod
    def _entry_config_on_variable(is_valid, entry):
        if entry is not None:
            if is_valid:
                entry.config(foreground=COLORS["GREEN"])
            else:
                entry.config(foreground=COLORS["RED"])

    def _ip_address_validator(self, variable, entry=None):
        is_valid_ip = bool(IP_REGEX.match(variable.get()))
        self._entry_config_on_variable(is_valid_ip, entry)

        return is_valid_ip

    def _text_validator(self, variable, entry=None):
        is_valid_text = bool(variable.get())
        self._entry_config_on_variable(is_valid_text, entry)
        return is_valid_text

    def _file_validator(self, variable, entry=None):
        is_valid_file = os.path.isfile(variable.get())
        self._entry_config_on_variable(is_valid_file, entry)
        return is_valid_file

    def _number_validator(self, variable, entry=None):
        is_number = False
        try:
            int(variable.get())
        except ValueError:
            is_number = False
        else:
            is_number = True

        self._entry_config_on_variable(is_number, entry)

        return is_number

    @staticmethod
    def _get_option_menu_style(option_list):
        style = {}
        width = max([len(i) for i in option_list])

        style["width"] = int(width) + 2  # add some offset

        return style


class TextWidgetWrapper:
    "A wrapper for text widget to insert colored text"
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

    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.config()

    def __getattr__(self, value):
        try:
            return self.__getattribute__(value)
        except AttributeError:
            return getattr(self.text_widget, value)

    @staticmethod
    def _no_color(text):
        ansi_escape = re.compile(r'\x1B[\(\[][0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)

    def config(self):
        "configure tags"
        for name, options in self._COLOR_DICT.items():
            self.text_widget.tag_config(name, **options)
