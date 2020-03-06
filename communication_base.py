"""Base for server and client"""
import sys
import tempfile

DEFAULT_PORT = 12345
SHUTDOWN_SERVER_CMD = b"shutdown-server"
DEFAULT_ENCODING = sys.getdefaultencoding()


def to_file(text: str):
    "writes given text in a file"
    file = tempfile.NamedTemporaryFile(delete=False)
    file.write(text)
    file.flush()

    filename = file.name
    file.close()

    return filename
