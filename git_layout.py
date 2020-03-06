"The GitConfig Layout"
import os
import subprocess

import tkinter as tk
from tkinter import ttk, messagebox

from layout_base import LayoutBase, \
    ENTRY_CONFIG, INNER, PAD

PADDING = int(PAD/2)
WINAC_GIT = "WinAC_Plus"


class GitConfigLayout(LayoutBase):
    "The GitConfig Frame"

    def __init__(self, context):
        super().__init__()
        self.git_path = None
        self._context = context

    @staticmethod
    def is_valid_git_path(path):
        "checks the given path is valid for WinAC"
        current_path = os.getcwd()
        winac_path = os.path.join(path, WINAC_GIT)
        try:
            os.chdir(winac_path)
        except (FileNotFoundError, OSError):
            return False

        try:
            output = subprocess.check_output(
                "git ls-remote --get-url",
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                universal_newlines=True,
            ).strip()
        except subprocess.CalledProcessError:
            return False
        else:
            if output.endswith(WINAC_GIT + ".git"):
                return True
            return False
        finally:
            os.chdir(current_path)

    def _git_path_validator(self, variable, entry=None):
        is_valid_folder = self.is_valid_git_path(variable.get())
        self._entry_config_on_variable(is_valid_folder, entry)
        if is_valid_folder:
            os.chdir(variable.get())
        else:
            os.chdir(os.getenv("tmp"))
        self._context.transfer_layout.target_file.set(
            self._context.transfer_layout.target_file.get()
        )
        return is_valid_folder

    def validate(self):
        "Checks the validity of entire inputs"
        if not self.is_valid_git_path(self.git_path.get()):
            messagebox.showerror(
                "Invalid Path",
                "Given path is not a valid git path"
            )
            return False

        return True

    def get_current_config(self):
        "Returns the string that passed to the compiler script"
        if not self.validate():
            return None

        return {
            "git_path": self.git_path.get()
        }

    def render(self, parent, **grid_options):
        "Renders the frame"
        git_frame = ttk.Frame(parent)
        git_frame.grid(**grid_options)

        self.git_path = tk.StringVar(git_frame)
        git_path_label = ttk.Label(git_frame, text="Git Path")
        git_path_label.grid(
            row=0, column=0,
            sticky=tk.NW, pady=(PADDING, 0)
        )

        git_path_entry = tk.Entry(
            git_frame, textvariable=self.git_path,
            **ENTRY_CONFIG, width=int(2.5 * PAD)
        )
        git_path_entry.grid(
            row=0, column=0,
            padx=(2 * INNER, 0),
            sticky=tk.NW, pady=(PADDING, 0),
        )

        self.git_path.trace("w", lambda x, y, z: self._git_path_validator(
            self.git_path, git_path_entry
        ))

        return git_frame
