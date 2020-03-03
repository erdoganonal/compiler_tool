"""
Compiles the files and done operation for given arguments.
"""

import sys
import os
import subprocess
import fileinput
import time
import glob

import paramiko
from colorama import Fore

from compiler_helper import CompileTypes, \
    TargetMachines, AutoBoolType, \
    ExitCodes, CopyActions, UnknownType, \
    CONFIG_FILE_PATH, LINKER_FILE_PATH, \
    CompilerConfig, TransferConfig, \
    COMPILER_PATH, COMPILER_NAME, PARTIAL_COMPILE_POSTFIX


class Colored:
    """
    Returns the colored result from given text,
    print functionalty may be used.
    """
    file = sys.stdout
    allow_color = True

    @classmethod
    def print_out(cls, color, *args, **kwargs):
        """Adds the given color into given text"""
        text = kwargs.pop("sep", " ").join(
            [str(arg) for arg in args]
        )

        if cls.allow_color:
            text = color + text + Fore.RESET

        kwargs["flush"] = True
        file = kwargs.pop("file", cls.file)

        print(text, file=file, **kwargs)

        return text

    @classmethod
    def info(cls, *args, **kwargs):
        """Adds green color into given text"""
        return cls.print_out(
            Fore.GREEN,
            *args,
            **kwargs
        )

    @classmethod
    def warning(cls, *args, **kwargs):
        """Adds yellow color into given text"""
        return cls.print_out(
            Fore.YELLOW,
            *args,
            **kwargs
        )

    @classmethod
    def error(cls, *args, **kwargs):
        """Adds red color into given text"""
        return cls.print_out(
            Fore.RED,
            *args,
            **kwargs
        )

    @classmethod
    def debug(cls, *args, **kwargs):
        """Adds blue color into given text"""
        return cls.print_out(
            Fore.BLUE,
            *args,
            **kwargs
        )

    @classmethod
    def verbose(cls, *args, **kwargs):
        """Adds blue color into given text"""
        return cls.print_out(
            Fore.CYAN,
            *args,
            **kwargs
        )

    @classmethod
    def default(cls, *args, **kwargs):
        """Adds the no color into given text"""
        return cls.print_out(
            Fore.RESET,
            *args,
            **kwargs
        )


class CompilerError(Exception):
    "Base exception for compiler component"

    def __init__(self, message, exit_code):
        super().__init__()
        self._exit_code = exit_code
        self._message = message

        if message:
            Colored.error(message)

    @property
    def exit_code(self):
        "get the return value of the result"
        return self._exit_code

    @property
    def message(self):
        "get the message of the result"
        return self._message


class WMIC:
    "Executes the commands via WMIC command with given credentials"

    def __init__(self, ip_address, username, password):
        self.ip_address = ip_address
        self.username = username
        self.password = password

        self._command = r'WMIC.exe ' \
            r'/node:{ip} /USER:"\{username}" ' \
            r'/PASSWORD:"{password}" ' \
            r'process call create "{{command}}"'.format(
                ip=ip_address,
                username=username,
                password=password
            )

    def execute(self, command, **kwargs):
        "Executes the given command on the system. Yields the output"
        popen = subprocess.Popen(
            self._command.format(command=command),
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=kwargs.pop("stderr", subprocess.PIPE),
            shell=True,
            universal_newlines=True,
            **kwargs
        )
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line
        popen.stdout.close()
        return_code = popen.wait()

        return return_code

    def execute2(self, command, exit_code, **kwargs):
        "Executes the given command on the system. Returns the output"
        try:
            output = subprocess.check_output(
                self._command.format(command=command),
                stdin=subprocess.PIPE,
                stderr=kwargs.pop("stderr", subprocess.PIPE),
                shell=True,
                universal_newlines=True,
                **kwargs
            )
            return output
        except subprocess.CalledProcessError as error:
            raise CompilerError(error.stderr, exit_code)


class SSH:
    "The SSH connection class"

    def __init__(self, hostname, username, password):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self._hostname = hostname
        self._username = username
        self._password = password

    def connect(self):
        "Connect to an SSH server"
        try:
            self.ssh.connect(
                hostname=self._hostname,
                username=self._username,
                password=self._password,
            )
        except paramiko.SSHException as error:
            raise CompilerError(error, ExitCodes.LINUX_CONNECTION_ERROR)

    def execute(self, command, exit_code=ExitCodes.UNKNOWN_LINUX_ERROR):
        "executes the command on the remote"
        _, stdout, stderr = self.ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()

        if error and exit_code is not None:
            raise CompilerError(error, exit_code)

        return output

    def close(self):
        "closes ssh connection"
        self.ssh.close()

    def open_sftp(self):
        "return sftp connection sftp"
        return self.ssh.open_sftp()


def execute(command, **kwargs):
    "Executes the given command on the system. Yields the output"
    popen = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=kwargs.pop("stderr", subprocess.PIPE),
        shell=True,
        universal_newlines=True,
        **kwargs
    )
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line, None
    popen.stdout.close()
    popen.wait()

    yield '', popen.returncode


def start_operation(compiler_config, transfer_config, stdout=sys.stdout):
    "the main function for compiler tool"
    if not isinstance(compiler_config, CompilerConfig):
        raise UnknownType(compiler_config, CompilerConfig)

    if not isinstance(transfer_config, TransferConfig):
        raise UnknownType(transfer_config, TransferConfig)

    Colored.file = stdout

    if compiler_config.skip_build:
        Colored.warning("\nBuild skipped.\n")
    else:
        start_compile(compiler_config)

    if transfer_config.skip_transfer:
        Colored.warning("\nTransfer skipped.\n")
    else:
        start_transfer(transfer_config)


def start_compile(compiler_config):
    "Starts the compile"

    compile_string = get_compile_string(compiler_config)

    if (not compiler_config.compile_type == CompileTypes.LINK_ONLY
            and compiler_config.partial_compile):

        for path in compiler_config.partial_compile:
            Colored.info("Build started for {0}".format(
                os.path.basename(path)
            ))
            output = _compile(compile_string, path=path)
            if "BUILD SUCCESSFUL" in output:
                Colored.info("Build successful for {0}\n".format(
                    os.path.basename(path)
                ))
            else:
                raise CompilerError("Build failed.", ExitCodes.BUILD_FAILURE)

        if compiler_config.compile_type in (
                CompileTypes.UNOPTIMIZED_AND_LINK,
                CompileTypes.OPTIMIZED_AND_LINK,
                CompileTypes.LINK_ONLY
        ):
            # Final link
            Colored.info("Final linking")
            final_link_command = compiler_config.target_type.value + CompileTypes.LINK_ONLY.value
            output = _compile(final_link_command)
        else:
            Colored.warning("\nFinal link skipped.\n")
    else:
        Colored.info("Build started")
        output = _compile(compile_string)

    if "BUILD SUCCESSFUL" not in output:
        raise CompilerError("Build failed.", ExitCodes.BUILD_FAILURE)

    Colored.info("Build successful!")


def _compile(compile_string, *, path=None):
    main_path = os.getcwd()

    if path is None:
        # Full compile
        os.chdir(os.path.join(
            os.getcwd(),
            COMPILER_PATH
        ))

        compiler_real_path = COMPILER_NAME
    else:
        # Partial compile
        os.chdir(path)
        compiler_real_path = os.path.join(
            main_path,
            COMPILER_PATH,
            COMPILER_NAME
        )
    command = "{0} {1}".format(compiler_real_path, compile_string)

    output = ""
    for line, _ in execute(command, stderr=subprocess.STDOUT):
        output += line
        Colored.default(line, end='')

    os.chdir(main_path)

    return output


def _subprocess(command, exit_code, **kwargs):
    try:
        output = subprocess.check_output(
            command,
            stdin=subprocess.PIPE,
            stderr=kwargs.pop("stderr", subprocess.PIPE),
            shell=True,
            universal_newlines=True,
            **kwargs
        )
        return output
    except subprocess.CalledProcessError as error:
        if exit_code is None:
            return error.output
        raise CompilerError(error.output, exit_code)


def start_transfer(transfer_config):
    "Copies files to the target if necessary"

    if transfer_config.target_machine == TargetMachines.WINDOWS:
        transfer_config.destination += r"\CPU.elf*"
        _win_copy_file(transfer_config)
    if transfer_config.target_machine == TargetMachines.LINUX:
        transfer_config.destination += "/CPU.elf"
        _linux_copy_file(transfer_config)


def _windows_grant_permissions(transfer_config, access_path):
    Colored.info("Granting access permissions")

    return_code = None
    access_generator = execute("net use {access_path} /USER:{username} {password}".format(
        access_path=access_path,
        username=transfer_config.username,
        password=transfer_config.password
    ), stderr=subprocess.STDOUT)
    for _, return_code in access_generator:
        pass

    if return_code != ExitCodes.SUCCESS.value:
        raise CompilerError(
            "Failed to access the target. Make sure firewall disabled.",
            ExitCodes.WINDOWS_PERMISSION_ERROR
        )


def _windows_copy_action_handler(transfer_config, access_path):
    if (transfer_config.action == CopyActions.BACKUP
            or transfer_config.action == CopyActions.KEEP_LAST):
        filename = access_path + "\\" + \
            os.path.basename(transfer_config.target_file)
        backup_file = filename + time.strftime("_%Y%m%d_%H%M%S")

        _subprocess(
            "move {0} {1}".format(filename, backup_file),
            exit_code=None
        )

        if transfer_config.action == CopyActions.KEEP_LAST:
            files = glob.glob("{0}*".format(filename))
            for file_ in files:
                if backup_file != file_:
                    _subprocess(
                        "del {0}".format(file_),
                        exit_code=None
                    )
    elif transfer_config.action == CopyActions.OVERWRITE:
        # No need to take any action
        pass
    else:
        raise UnknownType(transfer_config.action, CopyActions)


def _win_reboot_handler(transfer_config):
    wmic = WMIC(
        ip_address=transfer_config.ip_address,
        username=transfer_config.username,
        password=transfer_config.password
    )
    wmic.execute2(
        r"C:\Program Files (x86)\Siemens\Automation\CPU "
        r"150xS\bin\CPU_Control.exe /allowreboot",
        exit_code=ExitCodes.WINDOWS_CONTROL_TOOL_ERROR
    )
    wmic.execute2(
        "shutdown /r /t 0",
        exit_code=ExitCodes.WINDOWS_REBOOT_ERROR
    )


def _win_copy_file(transfer_config):
    drive, folder = transfer_config.destination.split(':')

    Colored.info("Trying to access path over shared folder")
    try:
        _subprocess(
            r"dir \\{hostname}\{drive}".format(
                hostname=transfer_config.ip_address,
                drive=drive.lower(),
            ),
            exit_code=ExitCodes.WINDOWS_PERMISSION_ERROR
        )
    except CompilerError:
        Colored.warning("Could not connect over shared folder.\n")
        use_wmic = True
    else:
        use_wmic = False

    if use_wmic:
        access_path = r"\\{hostname}\{drive}$\{folder}".format(
            hostname=transfer_config.ip_address,
            drive=drive.lower(),
            folder=folder.strip('\\')
        )
    else:
        access_path = r"\\{hostname}\{drive}\{folder}".format(
            hostname=transfer_config.ip_address,
            drive=drive.lower(),
            folder=folder.strip('\\')
        )

    if use_wmic:
        _windows_grant_permissions(transfer_config, access_path)

    Colored.info("Access granted\n")

    _windows_copy_action_handler(transfer_config, access_path)

    # /Y option overwrites the file if exist
    output = _subprocess(
        "xcopy {path} {access_path} /Y".format(
            path=transfer_config.target_file.replace('/', '\\'),
            access_path=access_path,
        ),
        exit_code=ExitCodes.WINDOWS_COPY_ERROR,
    )

    Colored.info(output)

    if transfer_config.reboot:
        _win_reboot_handler(transfer_config)


def _linux_copy_action_handler(transfer_config, ssh, destination):
    if (transfer_config.action == CopyActions.BACKUP
            or transfer_config.action == CopyActions.KEEP_LAST):
        backup_file = destination + time.strftime("_%Y%m%d_%H%M%S")
        if transfer_config.action == CopyActions.KEEP_LAST:
            try:
                files = ssh.execute("ls {0}*".format(destination))
            except CompilerError:
                pass
            else:
                filename = destination.split("/")[-1]
                for file in files.split():
                    if file.split("/")[-1] != filename:
                        ssh.execute(
                            "sudo rm -f {0}".format(file),
                            exit_code=None
                        )
        ssh.execute("sudo mv {0} {1}".format(destination, backup_file))
    elif transfer_config.action == CopyActions.OVERWRITE:
        # No need to take any action
        pass
    else:
        raise CompilerError('', ExitCodes.UNKNOWN_LINUX_ERROR)


def _linux_copy_file(transfer_config):
    basename = os.path.basename(transfer_config.target_file)
    temp_file = "/tmp/" + basename

    # Retrieve the filename and add it to the path
    destination = transfer_config.destination + "/" + basename

    ssh = SSH(
        hostname=transfer_config.ip_address,
        username=transfer_config.username,
        password=transfer_config.password
    )

    ssh.connect()

    _linux_copy_action_handler(transfer_config, ssh, destination)

    sftp = ssh.open_sftp()

    Colored.info("\nFile transfering to {0}".format(destination))
    try:
        sftp.put(transfer_config.target_file, temp_file)
        ssh.execute(
            "sudo mv {0} {1}".format(temp_file, destination),
            exit_code=ExitCodes.LINUX_COPY_ERROR
        )
        ssh.execute(
            "ls -la {0}".format(destination),
            exit_code=ExitCodes.LINUX_COPY_ERROR
        )
    except (paramiko.SSHException, FileNotFoundError, CompilerError) as error:
        sftp.close()
        ssh.close()
        raise CompilerError(error, ExitCodes.LINUX_COPY_ERROR)

    Colored.info("Transfer complated.")

    try:
        if transfer_config.reboot:
            ssh.execute("sudo reboot")
    except paramiko.SSHException as error:
        sftp.close()
        ssh.close()
        raise CompilerError(error, ExitCodes.LINUX_REBOOT_ERROR)

    sftp.close()
    ssh.close()


def _is_linker_editted(linker_file):
    current_path = os.getcwd()

    os.chdir("s7p.cpu1500")

    try:
        output = _subprocess(
            "git diff {0}".format(linker_file),
            exit_code=ExitCodes.GIT_ERROR
        )
    finally:
        os.chdir(current_path)

    return bool(output)


def _need_edit_linker(linker_file, edit_linker):
    if edit_linker is AutoBoolType.ALWAYS:
        return True

    if edit_linker is AutoBoolType.AUTO:
        return not _is_linker_editted(linker_file)

    if edit_linker is AutoBoolType.NEVER:
        return False

    raise UnknownType(edit_linker, AutoBoolType)


def _edit_linker(linker_file, expand_size):
    "Edits the linker script"

    output = fileinput.input(linker_file, inplace=True)
    for line in output:
        if "code (ARXL)" in line:
            current_size = line.split("=")[2].strip()
            expanded_size = "{0:X}".format(
                int(current_size, base=16) + expand_size
            ).zfill(8)

            line = line.replace(current_size, "0x{0}".format(expanded_size))
        if "data (AWL)" in line:
            current_size = line.split("=")[1].strip().split()[0].strip()
            expanded_size = "{0:X}".format(
                int(current_size, base=16) + expand_size
            ).zfill(7)

            line = line.replace(current_size, "0x{0}".format(expanded_size))
        print(line, end='')
    output.close()


def do_unoptimized_modifications(compiler_config):
    "Edits config file and linker"
    linker_file = os.path.join(
        os.getcwd(),
        LINKER_FILE_PATH.format(compiler_config.target_type.value)
    )
    if _need_edit_linker(linker_file, compiler_config.edit_linker):
        _edit_linker(linker_file, int(compiler_config.expand_size))

    # Edit for debugging
    config_file = os.path.join(
        os.getcwd(),
        CONFIG_FILE_PATH.format(compiler_config.target_type.value)
    )

    output = fileinput.input(config_file, inplace=True)
    for line in output:
        if "#define ADN_ADB_COMM_MODE" in line:
            line = line.replace(
                "ADN_ADB_COMM_MODE_SHM",
                "ADN_ADB_COMM_MODE_UART"
            )
        if "#define ADN_ADB_SUPPORT_COMM_SHM" in line:
            line = line.replace("YES", "NO")
        print(line, end='')
    output.close()


def get_compile_string(compiler_config):
    "Returns the compile string and its options"
    if compiler_config.partial_compile:
        compile_param = compiler_config.target_type.value + \
            PARTIAL_COMPILE_POSTFIX + compiler_config.compile_type.value
    else:
        compile_param = compiler_config.target_type.value + \
            compiler_config.compile_type.value

    if compiler_config.parallel_compile:
        compile_param += " -Dbuild.parallel=true"

    if compiler_config.compile_type in (
            CompileTypes.UNOPTIMIZED,
            CompileTypes.UNOPTIMIZED_AND_LINK
    ):
        # If unoptimized options selected,
        # some modiffication might be needed
        do_unoptimized_modifications(compiler_config)

    return compile_param
