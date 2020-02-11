"""A helper module for compiler"""
import sys
import os
import enum
import subprocess

LINKER_DFT_EXPAND_SIZE = 0x400000
try:
    WIDTH = int(os.environ['COLUMNS'])
except (KeyError, ValueError):
    WIDTH = 80
WIDTH -= 2

CONFIG_FILE_PATH = "s7p.cpu1500\\product_configuration\\" \
                   "{0}\\x86_0\\adn_config_{0}_x86_0.h"
LINKER_FILE_PATH = "s7p.cpu1500\\_link\\{0}\\x86_0.lk"
EXECUTABLE_FILE_PATH = "s7p.cpu1500\\bin\\{0}"
COMPILER_PATH = "s7p.cpu1500\\_gen"
COMPILER_NAME = "antmake.bat"
PARTIAL_COMPILE_POSTFIX = "_x86_0"


class _ConfigBase:
    def _set_attr(self, name, value, expected_type):
        if isinstance(value, expected_type):
            setattr(self, name, value)
        else:
            raise UnknownType(value, expected_type)

    def __str__(self):
        string = "{\n"
        for key, value in vars(self).copy().items():
            string += "    '{0}': {1},\n".format(key, value)
        string += "}"

        return string

    def __repr__(self):
        string = "{"
        for key, value in vars(self).copy().items():
            string += "'{0}': {1},".format(key, value)
        string += "}"

        return string


class CompilerConfig(_ConfigBase):
    "A class for Compiler configurations"
    # pylint: disable=too-few-public-methods

    def __init__(self, *, target_type, skip_build,
                 compile_type, parallel_compile,
                 partial_compile, edit_linker, expand_size, output):
        self._set_attr("target_type", target_type, TargetTypes)
        self.skip_build = skip_build
        self._set_attr("compile_type", compile_type, CompileTypes)
        self.parallel_compile = parallel_compile
        self.partial_compile = partial_compile
        self._set_attr("edit_linker", edit_linker, AutoBoolType)
        self.expand_size = expand_size
        self.output = output


class TransferConfig(_ConfigBase):
    "A class for Transfer configurations"
    # pylint: disable=too-few-public-methods

    def __init__(self, *, skip_transfer, target_machine,
                 cpu_type, ip_address, username, password,
                 destination, target_file, action, reboot):
        self.skip_transfer = skip_transfer
        self._set_attr("target_machine", target_machine, TargetMachines)
        self._set_attr("cpu_type", cpu_type, CPUTypes)
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.destination = destination
        self.target_file = target_file
        self._set_attr("action", action, CopyActions)
        self.reboot = reboot


class ExitCodes(enum.Enum):
    "The return codes and its means"
    UNKNOWN = -1
    SUCCESS = enum.auto()
    NO_SUCH_FILE = enum.auto()
    BUILD_FAILURE = enum.auto()
    UNKNOWN_TYPE = enum.auto()
    WINDOWS_PERMISSION_ERROR = enum.auto()
    WINDOWS_COPY_ERROR = enum.auto()
    WINDOWS_REBOOT_ERROR = enum.auto()
    UNKNOWN_LINUX_ERROR = enum.auto()
    LINUX_CONNECTION_ERROR = enum.auto()
    LINUX_COPY_ERROR = enum.auto()
    LINUX_REBOOT_ERROR = enum.auto()
    GIT_ERROR = enum.auto()
    ALREADY_RUNNING = enum.auto()


class UnknownType(Exception):
    "raises when an unknown type comes through"

    def __init__(self, type_, expected):
        super().__init__(
            "Unknown variable: {0!r} Expected instance of: {1}".format(
                type_, expected
            )
        )


class GeneralLockException(Exception):
    "base for all lock errors"


class AlreadyLocked(GeneralLockException):
    "raises when another instance is running"


class Lock:
    "locks the compiler"
    _is_locked = False

    @classmethod
    def _get_process_list(cls, filter_on):
        output = subprocess.check_output(["tasklist.exe", "-V"])
        instances = []
        for out in output.decode(errors="replace").splitlines():
            if filter_on in out:
                process = out.split()
                if "python" in " ".join(process[11:]):
                    instances.append(process[1])
        return instances

    @classmethod
    def is_locked(cls, program_name=sys.argv[0]):
        "returns the lock accuired or not"
        if cls._is_locked:
            return True

        running_instances = cls._get_process_list(filter_on=program_name)

        if len(running_instances) == 1:
            return False
        return True

    @classmethod
    def kill_all(cls, filter_on=sys.argv[0]):
        "kill all instances"
        pids = cls._get_process_list(filter_on)
        on_pid = os.getpid()

        for pid in pids:
            if pid == on_pid:
                continue

            subprocess.check_output(
                ["taskkill.exe", "/F", "/PID", pid]
            )

    @classmethod
    def lock(cls):
        "accuires the lock"
        if cls.is_locked():
            raise AlreadyLocked
        cls._is_locked = True

    @classmethod
    def unlock(cls):
        "releases the lock"
        cls._is_locked = False


class TargetTypes(enum.Enum):
    "Type of the possible targets"
    IPC = "winac_adonis"
    OC2 = "winac_adonis_bb"


class CompileTypes(enum.Enum):
    "Type of the possible compile options"
    UNOPTIMIZED = " -Dbuild.unoptimized=true"
    OPTIMIZED = ""
    LINK_ONLY = " -Dfinallinkonly=true"


class TargetMachines(enum.Enum):
    "Type of the possible environments"
    WINDOWS = "C:\\Boot\\Siemens\\SWCPU"
    LINUX = "/mnt/SWCPU/bin"


class AutoBoolType(enum.Enum):
    "Bool type in addition with auto"
    AUTO = -1
    ALWAYS = 0
    NEVER = 1


class CopyActions(enum.Enum):
    "Actions for copying executable file"
    KEEP_LAST = enum.auto()
    BACKUP = enum.auto()
    OVERWRITE = enum.auto()


class CPUTypes(enum.Enum):
    "Versions of CPU's and its names"
    STANDARD = "CPU.elf"
    FAILSAFE = "CPU_F.elf"
    STANDARD_1508 = "CPU_1508.elf"
    FAILSAFE_1508 = "CPU_1508_F.elf"
