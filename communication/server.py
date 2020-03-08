"""
A simple ssh-like module for windows.
"""
import sys
import os
import socket
import ssl
import time
import re
import threading

from typing import Union

from communication.communication_base import to_file, DEFAULT_PORT, SHUTDOWN_SERVER_CMD
from communication.executor import WindowsConsole, IOWrapper
from communication.cert.server_crt import SERVER_KEY, SERVER_CERT
from communication.cert.client_crt import CLIENT_CERT


BYTE_SPLIT_REGEX = re.compile(rb'.')


def main():
    "Starts the server"
    Server(
        host=socket.gethostbyaddr(socket.gethostname())[2][0],
        port=DEFAULT_PORT
    ).wait_connection()


def get_console():
    "Returns the console based on OS"
    if 'nt' in sys.builtin_module_names:
        return WindowsConsole
    raise NotImplementedError


class ConnectedClientInfo:
    "A class that contain connected client informations"

    def __init__(self, client: ssl.SSLSocket, ip_address: str, port: int):
        self.client = client
        self.ip_address = ip_address
        self.port = port
        self._buffer = b''
        self._lock = threading.Lock()

    @property
    def buffer(self):
        "returns the buffer and empties it"
        with self._lock:
            buffer, self._buffer = self._buffer, b''

        return buffer

    @buffer.setter
    def buffer(self, value: bytes):
        "appends given value to the buffer"
        with self._lock:
            self._buffer += value

        return len(value)

    def close(self):
        "closes the handlers"
        self.client.close()

    def __bool__(self):
        "If the object created, should return True"
        return True

    def __del__(self):
        self.close()


class Server:
    """A simple server."""

    def __init__(self, *, host: str, port: int, client_count: int = 1):
        server_cert = to_file(SERVER_CERT)
        server_key = to_file(SERVER_KEY)
        client_cert = to_file(CLIENT_CERT)

        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.verify_mode = ssl.CERT_REQUIRED

        self.context.load_cert_chain(certfile=server_cert, keyfile=server_key)
        self.context.load_verify_locations(cafile=client_cert)

        self._serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._serversocket.settimeout(5)

        self._serversocket.bind((host, port))
        self._serversocket.listen(client_count)

        self._close_server = False
        self._files = [
            server_cert, server_key, client_cert
        ]

        print("The server hostname is: {0}".format(host))
        print("Socket has been openned in port {0}".format(port))

    def wait_connection(self):
        "Waits for a connection"
        print("Waiting for connection")
        while not self._close_server:
            try:
                try:
                    connected_client = self.accept()
                except socket.timeout:
                    continue
            except KeyboardInterrupt:
                self._serversocket.close()
                sys.exit("Operation canceled by user")

            if connected_client:
                self.communicate(connected_client)

        try:
            self._serversocket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        print("Good bye!")
        self._serversocket.close()

    def accept(self):
        "Accepts the connection if client IP matches the pattern"
        server, (ip_address, port) = self._serversocket.accept()
        connection = self.context.wrap_socket(server, server_side=True)

        return ConnectedClientInfo(connection, ip_address, port)

    def communicate(self, connected_client: ConnectedClientInfo):
        "Starts the comminication between server and client in the background"
        print("Got a connection from {0}".format(connected_client.ip_address))

        devnull = open(os.devnull, 'wb')
        output = IOWrapper(to_output=devnull)

        console = get_console()(
            stdout=output,
            stderr=output
        )

        threading.Thread(
            target=self._communicate,
            args=(console, connected_client,),
            name=f"{__file__}::self._communicate",
            daemon=True
        ).start()

        threading.Thread(
            target=self._read_data_from_console,
            args=(console, connected_client,),
            name=f"{__file__}::self._read_data_from_console",
            daemon=True
        ).start()
        threading.Thread(
            target=self._write_data_to_client,
            args=(console, connected_client,),
            name=f"{__file__}::self._write_data_to_client",
            daemon=True
        ).start()
        threading.Thread(
            target=self._read_data_from_client,
            args=(console, connected_client,),
            name=f"{__file__}::self._read_data_from_client",
            daemon=True
        ).start()

    @staticmethod
    def _communicate(console: Union[WindowsConsole], connected_client: ConnectedClientInfo):
        console.communicate()

        time.sleep(1)
        connected_client.close()

        print("Connection closed for {0}".format(connected_client.ip_address))

        del console
        del connected_client

    @staticmethod
    def _read_data_from_console(
            console: Union[WindowsConsole],
            connected_client: ConnectedClientInfo):
        while console.is_active:
            console_out = console.stdout.read()
            if console_out:
                connected_client.buffer = console_out

    def _read_data_from_client(
            self,
            console: Union[WindowsConsole],
            connected_client: ConnectedClientInfo):
        close_server = False
        while console.is_active:
            try:
                data = connected_client.client.recv()
            except ConnectionError:
                break
            if data:
                if data.strip() == SHUTDOWN_SERVER_CMD:
                    data = b'exit\n'
                    close_server = True
                console.stdin.write(data)
                try:
                    console.stdin.flush()
                except OSError:
                    pass

        self._close_server = close_server

    @staticmethod
    def _write_data_to_client(
            console: Union[WindowsConsole],
            connected_client: ConnectedClientInfo):
        while console.is_active:
            buffer = connected_client.buffer
            buffer = buffer.split(b'\n')
            buffer = b'\n'.join(buffer[1:])
            if buffer:
                connected_client.client.send(buffer)


if __name__ == "__main__":
    main()
