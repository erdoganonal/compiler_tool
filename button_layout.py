"The Button Layout"
import sys
import os
import time
import threading
import tempfile

import tkinter as tk
from tkinter import ttk

from compiler_config import CONFIGURATIONS
from compiler_helper import ExitCodes
from compiler_gui_support import start_operation, CompilerError
from layout_base import PAD, Fore

COMPILER_PROCESS_NAME = "compiler_process"


if CONFIGURATIONS.get('enable_multiprocessing', False):
    from multiprocessing import Process, active_children


class ButtonLayout:
    "The Button Frame"

    def __init__(self, *, git_layout, compile_layout, transfer_layout, console_layout):
        self._git_layout = git_layout
        self._compile_layout = compile_layout
        self._transfer_layout = transfer_layout
        self._console_layout = console_layout
        self._start_button = None
        self._cancel_button = None
        self._main_dir = os.getcwd()

    def start_button(self):
        "returns the start button"
        return self._start_button

    def cancel_button(self):
        "returns the start button"
        return self.cancel_button

    @staticmethod
    def _get_process():
        if CONFIGURATIONS.get('enable_multiprocessing', False):
            processes = active_children()
        else:
            processes = [thread for thread in threading.enumerate()
                         if thread.is_alive()]

        for process in processes:
            if process.name == COMPILER_PROCESS_NAME:
                return process
        return None

    @staticmethod
    def _start_operation(compiler_config, transfer_config, filename):
        # pylint: disable=broad-except
        file = open(filename, 'w')
        try:
            start_operation(
                compiler_config, transfer_config,
                stdout=file
            )
        except CompilerError as error:
            file.write(
                "\n{0}Operation finished with error code "
                "{1}\n".format(Fore.RED, error.exit_code.value)
            )
            file.flush()
        except Exception as error:
            file.write(
                "{0}{1}".format(Fore.RED, error)
            )
            file.flush()
            file.write(
                "\n{0}Operation finished with error code "
                "{1}\n".format(Fore.RED, ExitCodes.UNKNOWN.value)
            )
            file.flush()
        else:
            time.sleep(0.5)
            file.write(
                "\n{GREEN}Operation finished successfully.".format(
                    **Fore.to_dict()
                )
            )
            file.flush()
        finally:
            file.close()

    def _process_file_watcher(self, filename):
        need_break = False
        with open(filename, 'r') as file:
            while True:
                line = file.readline()
                if line:
                    self._console_layout.write(line)
                else:
                    time.sleep(0.5)
                process = self._get_process()
                if (process is None or not process.is_alive()) and not line:
                    # Wait a while
                    if need_break:
                        break
                    need_break = True

        os.unlink(filename)
        self._cancel_operation()

    def _start_operation_in_bg(self):
        compiler_config = self._compile_layout.get_current_config()
        if compiler_config is None:
            return

        transfer_config = self._transfer_layout.get_current_config()
        if transfer_config is None:
            return

        git_config = self._git_layout.get_current_config()
        if git_config is None:
            return

        self._start_button.configure(state=tk.DISABLED)
        self._cancel_button.configure(state=tk.NORMAL)

        output_file = self._compile_layout.output.get()
        if not os.path.isabs(output_file):
            output_file = os.path.abspath(os.path.join(
                os.path.dirname(sys.argv[0]),
                output_file
            ))

        self._console_layout.clear_console()

        filename = tempfile.NamedTemporaryFile().name
        with open(filename, 'w'):
            pass

        if CONFIGURATIONS.get('enable_multiprocessing', False):
            Process(
                target=self._start_operation,
                args=(compiler_config, transfer_config, filename,),
                name=COMPILER_PROCESS_NAME,
                daemon=True
            ).start()
        else:
            threading.Thread(
                target=self._start_operation,
                args=(compiler_config, transfer_config, filename,),
                name=COMPILER_PROCESS_NAME,
                daemon=True
            ).start()

        threading.Thread(
            target=self._process_file_watcher,
            args=(filename,),
            daemon=True
        ).start()

    def _cancel_operation(self, is_user=False):
        process = self._get_process()
        if process is not None:
            process.kill()
            process.join()
        self._start_button.configure(state=tk.NORMAL)
        self._cancel_button.configure(state=tk.DISABLED)

        if is_user:
            self._console_layout.write(
                "{0}\nOperation canceled by user!\n".format(Fore.RED)
            )

    def render(self, parent, **grid_options):
        "Renders the frame"
        button_frame = ttk.Frame(parent)
        button_frame.grid(**grid_options)

        self._start_button = ttk.Button(
            button_frame,
            text="Start",
            command=self._start_operation_in_bg
        )
        self._start_button.grid(row=0, column=0, pady=PAD)

        self._cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=lambda: self._cancel_operation(is_user=True),
            state=tk.DISABLED
        )
        if CONFIGURATIONS.get('enable_multiprocessing', False):
            self._cancel_button.grid(row=0, column=1, pady=PAD, padx=PAD)

        return button_frame
