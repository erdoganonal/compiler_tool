"""
A simple client. Sends data to server
Receives the result and prints.
"""

import sys
import os
import socket
import ssl
import threading
import time
import msvcrt

from communication_base import to_file, \
    DEFAULT_PORT, SHUTDOWN_SERVER_CMD, \
    DEFAULT_ENCODING
from cert.client_crt import CLIENT_KEY, CLIENT_CERT
from cert.server_crt import SERVER_CERT
from input_interrupt import InputWithInterrupt

SERVER_SNI_HOSTNAME = 'erdogan.onal'


def main():
    "Starts from here"
    Client(
        host=socket.gethostbyaddr(socket.gethostname())[2][0],
        port=DEFAULT_PORT,
    ).start_communication()


class Client:
    """A simple client."""

    def __init__(self, host: str = None, port: int = None):
        if host is None:
            host = socket.gethostbyaddr(socket.gethostname())[2][0]

        if port is None:
            port = DEFAULT_PORT

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

        self._host = host
        self._port = port
        self._is_active = True

        self._files = [
            server_cert,
            client_key,
            client_cert
        ]

    @classmethod
    def _get_command(cls, encode: bool = False):
        command = "{0}\n".format(input()).encode(DEFAULT_ENCODING)
        if encode:
            return command
        return command.decode(DEFAULT_ENCODING)

    @property
    def host(self):
        "The hostname of the client"
        return self._host

    @property
    def port(self):
        "The port of the client"
        return self._port

    @property
    def client_object(self):
        "Return the actual client object"
        return self._stdout_client

    def start_communication(self):
        "Starts the communication"
        print(
            "\n\nConnected to the host. Enjoy the console :)\n\n"
            "Type 'exit' to close the client.\n"
            "Type '{0}' to close the client and"
            " server as well.\n\n"
            "".format(SHUTDOWN_SERVER_CMD.decode(DEFAULT_ENCODING))
        )

        threading.Thread(
            target=self._read_data_from_console,
            name="_read_stdout_from_console",
            daemon=True,
        ).start()

        threading.Thread(
            target=self._send_commands,
            name="_send_commands",
            daemon=True,
        ).start()

        while self._is_active:
            time.sleep(0.5)

    def _send_commands(self):
        custom_input = InputWithInterrupt()
        custom_input.add_auto_complate(
            "shutdown-server"
        )
        while self._is_active:
            try:
                command = (custom_input.input() + '\n').encode()
            except KeyboardInterrupt:
                command = '\n'
            if self._is_active:
                self._stdout_client.send(command)

    def _send_commands1(self):
        command = b''
        while self._is_active:
            char = msvcrt.getch()
            command += char
            if char == b'\r':
                char += b'\n'
                command += b'\n'
                if self._is_active:
                    self._stdout_client.send(command)
                command = b''
            try:
                print(char.decode(), end='', flush=True)
            except UnicodeDecodeError:
                pass

    def _read_data_from_console(self):
        while self._is_active:
            try:
                buffer = self._stdout_client.recv(1).decode()
                sys.stdout.write(buffer)
                sys.stdout.flush()
            except ConnectionError:
                print("Connection closed.")
                self._is_active = False
                sys.exit()

    def __del__(self):
        if hasattr(self, "_files"):
            for file in self._files:
                try:
                    os.unlink(file)
                except (FileNotFoundError, OSError):
                    pass
        self._is_active = False
        self._stdout_client.close()


if __name__ == "__main__":
    main()
