"The client console layout"
import re
import threading
import tkinter as tk
from tkinter import messagebox

from layouts.layout_base import ICON_PATH, Output, configure, COLORS, normalize_text, Fore
from communication.client import Client

TKINTER_EVENT_CANCEL_CMD = "break"

CONNECTION_EXCEPTIONS = (
    ConnectionRefusedError,
    TimeoutError,
)

PROMPT_REGEX = re.compile(
    r"([A-Z]:.*>)",
    flags=re.MULTILINE
)


def _add_color(message):
    message = PROMPT_REGEX.sub(
        fr"{Fore.CYAN}\1{Fore.RESET}",
        message
    )
    return message


class ClientLayout:
    "The Console Frame"

    def __init__(self, context):
        self.text_widget = None
        self._output = None
        self._context = context
        self._client = None
        self._command = ''

    def _start_communication(self, root):
        self._output = Output(
            self.text_widget, read_only=False,
            apply=_add_color
        )
        for line in self._client.readline():
            self._output.write(normalize_text(line.decode()))

        self.destroy(root, prompt=True)

    def start_communication(self, root):
        "starts the server-client communication"
        threading.Thread(
            target=self._start_communication,
            args=(root,),
            name=f"{__file__}::start_communication",
            daemon=True,
        ).start()

    def destroy(self, root, prompt=False):
        "handle for destroying the console window"
        if self._client is not None:
            self._client.send_command(b"exit\n")
            self._client = None

        if prompt:
            self._output.write_after_ready(
                "\n\nPress any key to exit..."
            )
        else:
            self._output.text_widget = None
            root.destroy()

    def catch_char(self, root, event):
        "catches the char from event"
        if self._client is None:
            self.destroy(root)
            return TKINTER_EVENT_CANCEL_CMD

        if event.char in ("\n", "\r"):
            command, self._command = self._command + '\n', ''
            command = normalize_text(command)
            self._client.send_command(command.encode())
            return TKINTER_EVENT_CANCEL_CMD
        self._command += event.char
        return ""

    def render(self):
        "renders the frame"
        if self._client is not None:
            messagebox.showwarning(
                "Already opened",
                "The console already opened!"
            )
            return

        ip_address = self._context.transfer_layout.ip_address.get()

        try:
            self._client = Client(
                host=ip_address,
                port=12345
            )
        except CONNECTION_EXCEPTIONS as error:
            messagebox.showerror(
                "Connection failed",
                str(error)
            )
            return

        client_frame = tk.Tk()
        client_frame.title(f"Connected to {ip_address}")

        vertical_scrool_bar = tk.Scrollbar(client_frame)
        self.text_widget = tk.Text(
            client_frame,
            foreground=COLORS["WHITE"],
            yscrollcommand=vertical_scrool_bar.set
        )
        self.text_widget.bind(
            '<Key>', lambda event: self.catch_char(client_frame, event))

        vertical_scrool_bar.config(command=self.text_widget.yview)

        self.text_widget.grid(
            row=0, column=0,
            sticky=tk.NSEW
        )
        vertical_scrool_bar.grid(row=0, column=1, sticky=tk.N+tk.S+tk.W)
        client_frame.rowconfigure(0, weight=1)
        client_frame.columnconfigure(0, weight=1)

        client_frame.protocol(
            'WM_DELETE_WINDOW',
            lambda: self.destroy(client_frame)
        )
        client_frame.iconbitmap(ICON_PATH)
        configure(client_frame)
        self.start_communication(client_frame)
        client_frame.state("zoomed")
        client_frame.mainloop()
