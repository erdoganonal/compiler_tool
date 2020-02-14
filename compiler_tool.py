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
import tkinter as tk

from layout_base import PAD, configure
from menu_layout import Menu
from git_layout import GitConfigLayout
from compiler_layout import CompileLayout
from transfer_layout import TransferLayout
# from debug_config_layout import DebugConfigLayout
from button_layout import ButtonLayout
from console_layout import ConsoleLayout


def render():
    "starts from here"

    # Create a main window
    main_window = tk.Tk()
    main_window.title("The Compiler Tool")

    # Create a frame for compiler and transfer layouts
    options_frame = tk.Frame(main_window)
    options_frame.grid_rowconfigure(0, weight=1)
    options_frame.grid_columnconfigure(0, weight=1)


    # get transfer layout
    transfer_layout = TransferLayout()

    # get git layout
    git_layout = GitConfigLayout(transfer_layout)

    # get compiler layout
    compile_layout = CompileLayout(transfer_layout)

    # get debug configurations layout
    # debug_config_layout = DebugConfigLayout(transfer_layout)

    # get console
    console_layout = ConsoleLayout()

    # get start button layout
    start_button = ButtonLayout(
        git_layout=git_layout,
        compile_layout=compile_layout,
        transfer_layout=transfer_layout,
        console_layout=console_layout
    )

    menu = Menu(compile_layout, transfer_layout, console_layout, git_layout)

    # Grid all
    menu.render(main_window, row=0, column=0, sticky=tk.NW)

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
    config = menu.load(use_defaults=True)

    if config["menu_config"]["start_full_screen"]:
        main_window.state("zoomed")
    main_window.mainloop()


if __name__ == "__main__":
    render()
