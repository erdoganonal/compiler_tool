"The Button Layout"
import os
import time
import threading

import tkinter as tk
from tkinter import ttk

from compiler_helper import ExitCodes
from compiler_gui_support import start_operation, CompilerError
from layout_base import PAD, Fore


class ButtonLayout:
    "The Button Frame"

    def __init__(self, *, git_layout, compile_layout, transfer_layout, console_layout):
        self._git_layout = git_layout
        self._compile_layout = compile_layout
        self._transfer_layout = transfer_layout
        self._console_layout = console_layout
        self._button = None
        self._is_active = False
        self._main_dir = os.getcwd()

    @property
    def button(self):
        "returns the button"
        return self._button

    def _start_operation(self):
        log_reader_thread = None
        self._is_active = True

        compiler_config = self._compile_layout.get_current_config()
        if compiler_config is None:
            return

        transfer_config = self._transfer_layout.get_current_config()
        if transfer_config is None:
            return

        git_config = self._git_layout.get_current_config()
        if git_config is None:
            return

        self._button.configure(state=tk.DISABLED)
        try:
            with open(self._compile_layout.output.get(), 'w'):
                pass
            log_reader_thread = threading.Thread(target=self._read_output)
            log_reader_thread.setDaemon(True)
            log_reader_thread.start()

            self._console_layout.clear_console()

            # pylint: disable=broad-except
            try:
                start_operation(
                    compiler_config, transfer_config,
                    stdout=self._console_layout.file
                )
            except CompilerError as error:
                self._console_layout.write(
                    "{0}\nOperation finished with error code "
                    "{1}\n".format(Fore.RED, error.exit_code)
                )
            except Exception as err:
                self._console_layout.write(
                    "{0}{1}".format(Fore.RED, err)
                )
                self._console_layout.write(
                    "{0}\nOperation finished with error code "
                    "{1}\n".format(Fore.RED, ExitCodes.UNKNOWN)
                )
            else:
                time.sleep(0.5)
                self._console_layout.write(
                    "\n{GREEN}Operation finished successfully.".format(
                        **Fore.to_dict()
                    )
                )
        finally:
            self._is_active = False
            if log_reader_thread:
                log_reader_thread.join()
            self._button.configure(state=tk.NORMAL)

    def _read_output(self):
        file = open(self._compile_layout.output.get(), 'r')
        while self._is_active:
            try:
                line = file.readline()
                if not line or not line.endswith('\n'):
                    time.sleep(0.1)
                    continue
                print(line, end='')
            except ValueError:
                continue
            except KeyboardInterrupt:
                break

        file.close()

    def _start_operation_in_bg(self):
        threading.Thread(target=self._start_operation, daemon=True).start()

    def render(self, parent, **grid_options):
        "Renders the frame"
        button_frame = ttk.Frame(parent)
        button_frame.grid(**grid_options)

        self._button = ttk.Button(
            button_frame,
            text="Start",
            command=self._start_operation_in_bg
        )
        self._button.grid(row=0, column=0, pady=PAD)

        return button_frame
