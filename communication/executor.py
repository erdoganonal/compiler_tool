"""
A basic console application
"""

import os
import subprocess
import time
import threading
import tempfile
from io import TextIOWrapper
from typing import TextIO


class IOWrapper(TextIOWrapper):
    "file object that write both the file and given file"

    def __init__(self, to_output, *args, watch=True, **kwargs):
        self._to_output = to_output

        temp_file = tempfile.NamedTemporaryFile().name
        self.__temp_file = open(temp_file, 'wb')
        super().__init__(self.__temp_file, *args, **kwargs)

        self._buffer = b''
        self.is_active = False
        self._lock = threading.Lock()

        if watch:
            self.watch()

    def watch(self):
        "reads the file and writes given file and buffer"
        if not self.is_active:
            self.is_active = True
            threading.Thread(
                target=self.__watch,
                daemon=True,
                name=str(self._to_output)
            ).start()

    def __watch(self):
        file = open(self.__temp_file.name, 'rb')
        while self.is_active:
            char = file.read()
            if not char:
                continue
            with self._lock:
                self._buffer += char
            try:
                self._to_output.write(char)
            except TypeError:
                self._to_output.write(char.decode())
            self._to_output.flush()
        file.close()

    def read(self):
        "reads the buffer and returns"
        with self._lock:
            buffer, self._buffer = self._buffer, b''
        return buffer

    def readline(self):
        "return the first line from the buffer"
        lines = self._buffer.splitlines()
        self._buffer = os.linesep.join(lines[1:])

        return lines[0]

    def close(self):
        "closes the file"
        self.__temp_file.close()
        try:
            os.unlink(self.__temp_file.name)
        except (FileNotFoundError, OSError, PermissionError):
            pass
        self.is_active = False

    def __del__(self):
        self.close()


class WindowsConsole:
    "Alters the console"

    def __init__(self,
                 stdin: TextIO = subprocess.PIPE,
                 stdout: TextIO = subprocess.PIPE,
                 stderr: TextIO = subprocess.PIPE,
                 **kwargs):
        self._console = subprocess.Popen(
            "cmd",
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            bufsize=1,
            **kwargs
        )

        self.stdout = stdout
        self.stderr = stderr

        self._handlers = (
            stdin, stdout, stderr
        )
        self._is_active = False

    @property
    def is_active(self):
        "Returns True if communication is active or not"
        return self._is_active

    def poll(self):
        "Returns True if communication is active or not"
        return self._console.poll()

    @property
    def stdin(self):
        "returns the stdin for Popen object"
        return self._console.stdin

    def communicate(self):
        "waits until the proccess ends."
        self._is_active = True
        while self._console.poll() is None:
            time.sleep(0.1)

        for handler in self._handlers:
            try:
                handler.close()
            except (AttributeError,):
                pass

        self._is_active = False
