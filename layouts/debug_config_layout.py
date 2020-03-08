"The Debug Configurations Layout"
from tkinter import ttk


class DebugConfigLayout:
    "Allows you to edit menu.cfg file for debug configurations"

    def __init__(self, transfer_layout):
        self._transfer_layout = transfer_layout

    def dummy(self):
        "disables too few public methods warning from lint"

    def render(self, parent, **grid_options):
        "Renders the frame"
        debug_config_frame = ttk.Frame(parent)
        debug_config_frame.grid(**grid_options)

        btn = ttk.Button(debug_config_frame, text="afafasf")
        btn.grid(row=0, column=0)

        # Enable only if the target machine is windows
        self._transfer_layout.target_machine.get()

        return debug_config_frame
