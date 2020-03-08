"""
A simple client. Sends data to server
Receives the result and prints.
"""

import os
import socket
import ssl
import threading
import time

from communication.communication_base import to_file
from communication.cert.client_crt import CLIENT_KEY, CLIENT_CERT
from communication.cert.server_crt import SERVER_CERT

SERVER_SNI_HOSTNAME = 'erdogan.onal'


class Client:
    """A simple client."""

    def __init__(self, host: str, port: int):
        server_cert = to_file(SERVER_CERT)
        client_key = to_file(CLIENT_KEY)
        client_cert = to_file(CLIENT_CERT)

        context = ssl.create_default_context(
            ssl.Purpose.SERVER_AUTH, cafile=server_cert)
        context.load_cert_chain(certfile=client_cert, keyfile=client_key)

        self._stdout_client = context.wrap_socket(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM),
            server_side=False,
            server_hostname=SERVER_SNI_HOSTNAME
        )

        self._stdout_client.connect((host, port))

        self._is_active = False

        self._files = [
            server_cert,
            client_key,
            client_cert
        ]

        self._lock = threading.Lock()
        self._buffer = b''
        threading.Thread(
            target=self._recv,
            name=f"{__file__}::__init__",
            daemon=True,
        ).start()

    @property
    def buffer(self):
        "returns the current buffer"
        buffer = b''
        with self._lock:
            buffer, self._buffer = self._buffer, b''

        return buffer

    @buffer.setter
    def buffer(self, value: bytes):
        "appends given value to buffer"
        with self._lock:
            self._buffer += value
        return len(value)

    @property
    def client_object(self):
        "Return the actual client object"
        return self._stdout_client

    def send_command(self, command):
        "sends command to the server"
        if self._is_active:
            self._stdout_client.send(command)

    def readline(self):
        "yields first line from buffer"
        i = 0
        while self._is_active:
            i += 1
            with self._lock:
                buffer = self._buffer.splitlines()
                self._buffer = b"\n".join(buffer[1:])
            if buffer:
                yield b'\n' + buffer[0]
            else:
                time.sleep(0.1)

    def _recv(self):
        self._is_active = True
        while self._is_active:
            try:
                self.buffer = self._stdout_client.recv(1)
            except ConnectionError:
                self.buffer = b"\nConnection closed.\n"
                time.sleep(0.2)
                self._is_active = False

    def __del__(self):
        if hasattr(self, "_files"):
            for file in self._files:
                try:
                    os.unlink(file)
                except (FileNotFoundError, OSError):
                    pass
        self._is_active = False
        self._stdout_client.close()
