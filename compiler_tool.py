"""
#-----------------------------------------------------------------------#
#-----------------------------------------------------------------------#
#                                  <menu>                               #
#-----------------------------------------------------------------------#
# Target Type: <dropdown>            | Transfer: <checkbox>             #
# Skip Build:  <checkbox>            |     Target Type: <dropdown>      #
#     Compile Type:      <dropdown>  |     IP Address:  <input>         #
#     Parallel Compile:  <checkbox>  |     Username:    <default_value> #
#     Edit Linker:       <checkbox>  |     Password:    <default_value> #
#         Size:     <default_value>  |     Destination: <default_value> #
#     Output:       <default_value>  |     Target File: <default_value> #
#     Partial Compile:   <checkbox>  |     Action:      <dropdown>      #
#         List      <list>           |     Reboot:      <checkbox>      #
#-----------------------------------------------------------------------#
#                                <button>                               #
#-----------------------------------------------------------------------#
#                                <console>                              #
#-----------------------------------------------------------------------#
"""
import sys
import tkinter as tk
import multiprocessing

from layouts.layout_base import PAD, configure, CONTEXT, ICON_PATH
from layouts.menu_layout import Menu
from layouts.git_layout import GitConfigLayout
from layouts.compiler_layout import CompileLayout
from layouts.transfer_layout import TransferLayout
# from layouts.debug_config_layout import DebugConfigLayout
from layouts.button_layout import ButtonLayout
from layouts.console_layout import ConsoleLayout


def main():
    "starts from here"
    multiprocessing.freeze_support()

    render()


def handle_destroy(root, *windows):
    "Closes given windows and the main window"
    for window in windows:
        window.destroy()

    root.destroy()


def render():
    "renders the main window"

    # Create a main window
    main_window = tk.Tk()
    main_window.title("The Compiler Tool")

    # Create a frame for compiler and transfer layouts
    options_frame = tk.Frame(main_window)
    options_frame.grid_rowconfigure(0, weight=1)
    options_frame.grid_columnconfigure(0, weight=1)

    # get transfer layout
    transfer_layout = TransferLayout(CONTEXT)

    # get git layout
    git_layout = GitConfigLayout(CONTEXT)

    # get compiler layout
    compile_layout = CompileLayout(CONTEXT)

    # get debug configurations layout
    # debug_config_layout = DebugConfigLayout(transfer_layout)

    # get console
    console_layout = ConsoleLayout(CONTEXT)

    # get start button layout
    start_button = ButtonLayout(CONTEXT)

    menu_layout = Menu(CONTEXT)

    CONTEXT.register(
        compile_layout=compile_layout,
        transfer_layout=transfer_layout,
        button_layout=start_button,
        git_layout=git_layout,
        menu_layout=menu_layout,
        console_layout=console_layout,
    )
    if not CONTEXT:
        for key, value in CONTEXT.__dict__.items():
            if not value:
                print(f"{key} is not registered")
        return

    # Grid all
    menu_layout.render(main_window, row=0, column=0, sticky=tk.NW)

    git_layout.render(
        main_window, row=1,
        padx=(PAD, PAD), columnspan=3, sticky=tk.NSEW
    )

    options_frame.grid(row=2, column=0, sticky=tk.NSEW)
    compile_layout.render(
        options_frame,
        row=0, column=0,
        sticky=tk.NW, padx=(PAD, 0)
    )
    transfer_layout.render(
        options_frame,
        row=0, column=1,
        sticky=tk.NW, padx=(PAD, 0)
    )
    # debug_config_layout.render(
    #     options_frame,
    #     row=0, column=2,
    #     sticky=tk.NW, padx=(PAD, 0)
    # )

    start_button.render(main_window, row=3, columnspan=2, sticky=tk.N)

    console_layout.render(
        main_window, row=4, pady=(0, PAD),
        padx=(PAD, PAD), columnspan=3, sticky=tk.NSEW
    )

    column_count, row_count = main_window.grid_size()
    for row in range(row_count):
        main_window.grid_rowconfigure(row, weight=1)

    for col in range(column_count):
        main_window.grid_columnconfigure(col, weight=1)

    configure(main_window)
    config = menu_layout.load(use_defaults=True)

    if config["global_config"]["start_full_screen"]:
        main_window.state("zoomed")

    main_window.protocol(
        'WM_DELETE_WINDOW',
        lambda: handle_destroy(
            main_window,
            compile_layout,
        )
    )
    main_window.iconbitmap(ICON_PATH)
    main_window.mainloop()


if __name__ == "__main__":
    # pylint:disable=broad-except
    try:
        main()
    except Exception as error:
        if hasattr(sys, "_MEIPASS"):
            # If file created by pyinstaller and
            # in case of no console, write the error
            # to the file
            with open("compiler_tool_crash.log", "w") as log:
                log.write(str(error))
        raise
