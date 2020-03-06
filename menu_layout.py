"The Menu Layout"
import sys
import os
import json

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyperclip

from compiler_config import CONFIGURATIONS, CONFIG_FILE
from compiler_helper import TargetTypes, \
    CompileTypes, LINKER_DFT_EXPAND_SIZE, \
    AutoBoolType, TargetMachines, EXECUTABLE_FILE_PATH, \
    CopyActions, CPUTypes, ExitCodes, \
    CompilerConfig, TransferConfig, UnknownType
from layout_base import LayoutBase, \
    DEFAULT_USERNAME, DEFAULT_PASSWORD, \
    merge_line_by_line, Fore, COLORS
from compiler_layout import COMPILER_HELP
from transfer_layout import TRANSFER_HELP

HELP = merge_line_by_line(
    COMPILER_HELP,
    TRANSFER_HELP
)

ABOUT = """
{TITLE}The Compiler Tool\n
{INFO_CYAN}Author:{INFO_WHITE} Erdogan Onal<erdogan.onal@siemens.com>\n
{INFO_CYAN}Version:{INFO_WHITE} 1.0\n
""".format(**Fore.to_dict())

EXIT_CODES = '\n'.join(
    [
        Fore.CYAN +
        "Exit code: {0}".format(
            exit_code.value
        ).ljust(16) +
        "->    {0}".format(
            exit_code.name
        ) +
        Fore.RESET
        for exit_code in ExitCodes
    ]
)


class Menu(LayoutBase):
    "The Menu Frame"

    def __init__(self, compile_layout, transfer_layout, console_layout, git_layout):
        super().__init__()
        self._compile_layout = compile_layout
        self._transfer_layout = transfer_layout
        self._console_layout = console_layout
        self._git_layout = git_layout
        self.menu_config = {}
        self._toggles = {}

    @staticmethod
    def _get_first_item(enumaration, attr="name"):
        return getattr(list(enumaration)[0], attr).replace("_", "-")

    def _verify_compiler_config(self, config):
        compiler_config = config["compiler"].copy()

        compiler_config["target_type"] = self._name_to_enum(
            compiler_config["target_type"], TargetTypes)
        compiler_config["compile_type"] = self._name_to_enum(
            compiler_config["compile_type"], CompileTypes)
        compiler_config["edit_linker"] = self._name_to_enum(
            compiler_config["edit_linker"], AutoBoolType)
        compiler_config["partial_compile"] = compiler_config["partial_compile_text"]
        del compiler_config["partial_compile_text"]

        try:
            CompilerConfig(**compiler_config)
        except UnknownType:
            raise KeyError

    def _verify_transfer_config(self, config):
        transfer_config = config["transfer"].copy()
        transfer_config["target_machine"] = self._name_to_enum(
            transfer_config["target_machine"], TargetMachines)
        transfer_config["cpu_type"] = self._name_to_enum(
            transfer_config["cpu_type"], CPUTypes)
        transfer_config["action"] = self._name_to_enum(
            transfer_config["action"], CopyActions)

        try:
            TransferConfig(**transfer_config)
        except UnknownType:
            raise KeyError

    def _verify(self, config):
        self._verify_compiler_config(config)
        self._verify_transfer_config(config)

    def _load(self, config):
        self._verify(config)

        self.menu_config = config["menu_config"]

        # set git layout first
        for key, value in config["git_config"].items():
            getattr(self._git_layout, key).set(value)

        # set compile layout then
        for key, value in config["compiler"].items():
            try:
                getattr(self._compile_layout, key).set(value)
            except AttributeError:
                setattr(self._compile_layout, key, value)

        # set transfer layout then
        for key, value in config["transfer"].items():
            getattr(self._transfer_layout, key).set(value)

        self._toggle()

    def _toggle(self):
        # finally, call toggles
        self._compile_layout.toggle_children_states(
            self._compile_layout.parent,
            self._compile_layout.skip_build,
        )

        self._transfer_layout.toggle_children_states(
            self._transfer_layout.parent,
            self._transfer_layout.skip_transfer,
            True
        )

        self._console_layout.clear_console()

        for function, args in self._toggles.items():
            function(*args)

    def _get_default_config(self):
        target_type = self._get_first_item(TargetTypes)
        compile_type = self._get_first_item(CompileTypes)
        edit_linker = self._get_first_item(AutoBoolType)

        target_machine = self._get_first_item(TargetMachines)
        cpu_type = self._get_first_item(CPUTypes)
        destination = self._get_first_item(TargetMachines, attr="value")
        target_file = os.path.join(EXECUTABLE_FILE_PATH.format(
            self._get_enum_value_from_name(target_type, TargetTypes)
        ), self._get_enum_value_from_name(
            self._transfer_layout.cpu_type.get(), CPUTypes))
        action = self._get_first_item(CopyActions)

        return {
            "menu_config": {
                "start_full_screen": True,
            },
            "git_config": {
                "git_path": os.path.dirname(os.path.abspath(sys.argv[0])),
            },
            "compiler": {
                "target_type": target_type,
                "skip_build": False,
                "compile_type": compile_type,
                "parallel_compile": True,
                "edit_linker": edit_linker,
                "expand_size": LINKER_DFT_EXPAND_SIZE,
                "output": "build_out.txt",
                "partial_compile": False,
                "partial_compile_text": []
            },
            "transfer": {
                "skip_transfer": False,
                "target_machine": target_machine,
                "cpu_type": cpu_type,
                "ip_address": "",
                "username": DEFAULT_USERNAME,
                "password": DEFAULT_PASSWORD,
                "destination": destination,
                "target_file": target_file,
                "action": action,
                "reboot": False
            }
        }

    def load(self, filename=CONFIG_FILE, use_defaults=False):
        "loads config from file"
        config = {}
        try:
            with open(filename, 'r') as file:
                config = json.loads(file.read())
        except (FileNotFoundError, json.JSONDecodeError):
            if use_defaults:
                config = self._get_default_config()
        except PermissionError:
            tk.messagebox.showerror(
                "Permission Denied",
                "Permission denied."
            )
            return {}

        try:
            os.chdir(config["git_config"]["git_path"])
        except (FileNotFoundError, OSError, KeyError):
            pass

        try:
            self._load(config)
        except KeyError:
            if use_defaults:
                self._load(self._get_default_config())
            tk.messagebox.showerror(
                "Loading Failure",
                "An error occured while loading configurations"
            )

        return config

    def _get_current_config(self):
        config = self._get_default_config()

        git_config = {}
        for key in config["git_config"]:
            attr = getattr(self._git_layout, key)
            try:
                git_config[key] = attr.get()
            except AttributeError:
                git_config[key] = attr

        compiler_config = {}
        for key in config["compiler"]:
            attr = getattr(self._compile_layout, key)
            try:
                compiler_config[key] = attr.get()
            except AttributeError:
                compiler_config[key] = attr

        transfer_config = {}
        for key in config["transfer"]:
            attr = getattr(self._transfer_layout, key)
            try:
                transfer_config[key] = attr.get()
            except AttributeError:
                transfer_config[key] = attr

        return {
            "general_config": CONFIGURATIONS.get_all(),
            "menu_config": self.menu_config,
            "git_config": git_config,
            "compiler": compiler_config,
            "transfer": transfer_config
        }

    def _save(self, no_messagebox=False):
        "saves the config to the file"
        config = self._get_current_config()
        try:
            config = json.dumps(config, indent=4)
        except json.JSONDecodeError:
            if not no_messagebox:
                tk.messagebox.showerror(
                    "Unknown failure!",
                    "Failed to decode the configuration"
                )
            return

        with open(CONFIG_FILE, 'w') as file:
            file.write(config)

        if not no_messagebox:
            tk.messagebox.showinfo(
                "Saved",
                "Configurations has been saved."
            )

    def _import(self):
        path = filedialog.askopenfilename()
        self.load(filename=path)

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension="*.*",
            filetypes=(
                ("JSON File", "*.json"),
                ("Text File", "*.txt"),
            )
        )

        config = json.dumps(self._get_current_config(), indent=4)

        with open(path, 'w') as file:
            file.write(config)

        messagebox.showinfo(
            "Operation success",
            "Configurations exported successfully!"
        )

    def _copy_output(self):
        # set clipboard data
        console_text = self._console_layout.text_widget.get(1.0, tk.END)
        pyperclip.copy(console_text)

    def _pause_screen(self, menu, index1, index2):
        menu.entryconfig(index1, foreground=COLORS["YELLOW"])
        menu.entryconfig(index2, foreground=COLORS["WHITE"])
        self._console_layout.file.pause()

    def _resume_screen(self, menu, index1, index2):
        menu.entryconfig(index1, foreground=COLORS["GREEN"])
        menu.entryconfig(index2, foreground=COLORS["WHITE"])
        self._console_layout.file.resume()

    def _reset(self):
        "resets the configurations to the defaults"
        default_config = self._get_default_config()
        self._load(default_config)
        # self._save(no_messagebox=True)

    def _to_console(self, message):
        self._console_layout.clear_console()
        self._console_layout.write(message)

    def _toggle_screen_state(self, menu, idx, need_toogle=False):
        try:
            full_screen = self.menu_config["start_full_screen"]
        except KeyError:
            return

        if need_toogle:
            self.menu_config["start_full_screen"] = not full_screen
        else:
            full_screen = not full_screen

        if full_screen:
            menu.entryconfig(idx, foreground=COLORS["WHITE"])
        else:
            menu.entryconfig(idx, foreground=COLORS["GREEN"])

        if need_toogle:
            messagebox.showwarning(
                "Configuration not saved yet!",
                "In order to change screen mode "
                "you need to save configurations. "
                "This mode will efect after restart"
            )

    def render(self, parent, **grid_options):
        "renders the menu frame"
        menu_bar = tk.Frame(parent)
        menu_bar.grid(**grid_options)

        file_menu = ttk.Menubutton(menu_bar, text="File")
        file_menu.grid(**self.get_next_position(
            row=False, column=False, pady=0
        ))

        self._render_file_menu(file_menu)
        self._render_screen_menu(menu_bar)
        self._render_config(menu_bar)
        self._render_help_menu(menu_bar)

        return menu_bar

    def _render_file_menu(self, file_menu):
        menu = tk.Menu(file_menu, tearoff=False, activeborderwidth=0)
        file_menu["menu"] = menu

        menu.add_command(
            label="Save", foreground="white",
            command=self._save,
        )
        menu.add_command(
            label="Save As", foreground="white",
            command=self._export,
        )
        menu.add_command(
            label="Import", foreground="white",
            command=self._import,
        )

        menu.add_separator()
        menu.add_command(
            label="Reset", foreground="white",
            command=self._reset
        )

        file_menu.menu = menu

    def _render_screen_menu(self, menu_bar):
        screen_menu = ttk.Menubutton(menu_bar, text="Screen")
        screen_menu.grid(**self.get_next_position(
            row=False, column=True, pady=0
        ))

        menu = tk.Menu(screen_menu, tearoff=False, activeborderwidth=0)
        screen_menu["menu"] = menu

        menu.add_command(
            label="Clear", foreground="white",
            command=self._console_layout.clear_console,
        )

        menu.add_command(
            label="Copy", foreground="white",
            command=self._copy_output,
        )

        menu.add_separator()
        menu.add_command(
            label="Pause", foreground="white",
            command=lambda: self._pause_screen(menu, 3, 4),
        )
        menu.add_command(
            label="Resume", foreground=COLORS["GREEN"],
            command=lambda: self._resume_screen(menu, 4, 3),
        )

        screen_menu.menu = menu

    def _render_config(self, menu_bar):
        help_menu = ttk.Menubutton(menu_bar, text="Configurations")
        help_menu.grid(**self.get_next_position(
            row=False, column=True, pady=0
        ))

        menu = tk.Menu(help_menu, tearoff=False, activeborderwidth=0)
        help_menu["menu"] = menu

        menu.add_command(
            label="Start full screen", foreground="white",
            command=lambda: self._toggle_screen_state(menu, 0, True),
        )

        self._toggles[self._toggle_screen_state] = (menu, 0)

        help_menu.menu = menu

    def _render_help_menu(self, menu_bar):
        help_menu = ttk.Menubutton(menu_bar, text="?")
        help_menu.grid(**self.get_next_position(
            row=False, column=True, pady=0
        ))

        menu = tk.Menu(help_menu, tearoff=False, activeborderwidth=0)
        help_menu["menu"] = menu

        menu.add_command(
            label="Help", foreground="white",
            command=lambda: self._to_console(HELP),
        )
        menu.add_command(
            label="Exit Codes", foreground="white",
            command=lambda: self._to_console(EXIT_CODES),
        )
        menu.add_separator()
        menu.add_command(
            label="About", foreground="white",
            command=lambda: self._to_console(ABOUT),
        )

        help_menu.menu = menu
