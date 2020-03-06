"""
Skip Transfer: Skips transfer if checked.
  Target Type: The OS of the target machine.
               e.g., {target_machines}
  CPU Type: Select type of the CPU.elf
            e.g., {cpu_types}
  Action: The action that will be applied
          to the targer file on remote.
          e.g., {actions}
  IP Address: IP Address of the target
  Username: Username of the target
  Password: Password of the target
  Destination: Destination path where
               the file will be placed
  Target File: Path of file to be transferred
  Reboot: Reboots the target after transfer
          is done, if checked.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from compiler_helper import TransferConfig, \
    TargetMachines, CopyActions, CPUTypes
from layout_base import LayoutBase, \
    to_comma_string, ENTRY_CONFIG, PAD

TRANSFER_HELP = __doc__.strip().format(
    target_machines=to_comma_string(TargetMachines),
    cpu_types=to_comma_string(CPUTypes),
    actions=to_comma_string(CopyActions),
)


class TransferLayout(LayoutBase):
    "The Transfer Frame"
    # pylint: disable=too-many-instance-attributes

    def __init__(self, context):
        super().__init__()
        self.skip_transfer = None
        self.context = context
        self.target_machine = None  # Linux, Windows
        self.cpu_type = None  # Standard, failsafe...
        self.ip_address = None
        self.username = None
        self.password = None
        self.destination = None
        self.target_file = None
        self.action = None
        self.reboot = None

        self.inputs = None
        self.parent = None

    def _target_machine_trace(self):
        self.destination.set(self._get_enum_value_from_name(
            self.target_machine.get(), TargetMachines
        ))

    def _action_trace(self):
        pass

    def _cpu_type_trace(self):
        filename = self._get_enum_value_from_name(
            self.cpu_type.get(), CPUTypes
        )

        current_value = self.target_file.get().split("\\")
        current_value[-1] = filename

        self.target_file.set('\\'.join(current_value))

    def _destination_validator(self, variable, entry=None):
        if not bool(variable.get()):
            self._entry_config_on_variable(False, entry)

        if self.target_machine.get() == TargetMachines.WINDOWS.name:
            try:
                _, _ = variable.get().split(":")
            except ValueError:
                self._entry_config_on_variable(False, entry)
                return False

        self._entry_config_on_variable(True, entry)
        return True

    def validate(self):
        "Checks the validity of entire inputs"
        if self.inputs is None:
            raise RuntimeError("Widget not rendered yet")

        if self.skip_transfer.get():
            return True

        for inp in self.inputs:
            variable = inp[0]
            name = inp[1]
            validator = inp[2]

            if not validator(variable):
                messagebox.showerror(
                    "Invalid input",
                    "The format of {0} is not valid".format(name)
                )
                return False
        return True

    def get_command_line_string(self):
        "Returns the string that passed to the compiler script"
        if not self.validate():
            return None

        command_line = " "

        if self.skip_transfer.get():
            return command_line

        command_line = "transfer "
        command_line += "--target-type {0} ".format(self.target_machine.get())
        command_line += "--ip-address {0} ".format(self.ip_address.get())
        command_line += "--username {0} ".format(self.username.get())
        command_line += "--password {0} ".format(self.password.get())
        command_line += "--destination {0} ".format(self.destination.get())
        command_line += "--executable-file {0} ".format(self.target_file.get())
        command_line += "--action {0} ".format(self.action.get())
        if self.reboot.get():
            command_line += "--reboot "

        return command_line

    def get_current_config(self):
        "Returns the string that passed to the compiler script"
        if not self.validate():
            return None

        return TransferConfig(
            skip_transfer=self.skip_transfer.get(),
            target_machine=self._name_to_enum(
                self.target_machine.get(), TargetMachines
            ),
            cpu_type=self._name_to_enum(self.cpu_type.get(), CPUTypes),
            ip_address=self.ip_address.get(),
            username=self.username.get(),
            password=self.password.get(),
            destination=self.destination.get(),
            target_file=self.target_file.get(),
            action=self._name_to_enum(self.action.get(), CopyActions),
            reboot=self.reboot.get()
        )

    def render(self, parent, **grid_options):
        "Renders the frame"
        transfer_frame = tk.Frame(parent)
        transfer_frame.grid(**grid_options)

        self.parent = ttk.Frame(transfer_frame)
        self.parent.grid(**self.get_next_position(
            False, False
        ))

        # Add a checkbox for skipping the transfer
        self.skip_transfer = tk.BooleanVar(transfer_frame)
        skip_transfer = ttk.Checkbutton(
            self.parent, text="Skip Transfer",
            variable=self.skip_transfer,
            command=lambda: self.toggle_children_states(
                self.parent, self.skip_transfer, True
            ))
        skip_transfer.grid(**self.get_next_position(
            row=False, column=False, inner=1
        ))

        self._render_target_machine(self.parent)
        self._render_cpu_type(self.parent)
        self._render_action(self.parent)
        self._render_inputs(self.parent)
        self._render_reboot(self.parent)

        return transfer_frame

    def _render_target_machine(self, parent):
        self.target_machine = tk.StringVar(parent)
        target_machines = self._check_iterable_type(TargetMachines)
        target_machines_dropdown = ttk.OptionMenu(
            parent, self.target_machine, target_machines[0], *target_machines
        )
        target_machines_dropdown.grid(**self.get_next_position(
            row=True, column=False, inner=2
        ))
        target_machines_dropdown.configure(
            **self._get_option_menu_style(target_machines))
        self.target_machine.trace(
            "w", lambda x, y, z: self._target_machine_trace())

    def _render_cpu_type(self, parent):
        self.cpu_type = tk.StringVar(parent)
        cpu_types = self._check_iterable_type(CPUTypes)
        cpu_types_dropdown = ttk.OptionMenu(
            parent, self.cpu_type, cpu_types[0], *cpu_types
        )
        cpu_types_dropdown.grid(**self.get_next_position(
            row=False, column=False, inner=5
        ))
        cpu_types_dropdown.configure(
            **self._get_option_menu_style(cpu_types)
        )
        self.cpu_type.trace(
            "w", lambda x, y, z: self._cpu_type_trace()
        )

    def _render_inputs(self, parent):
        # variable, text, validator, default value
        self.ip_address = tk.StringVar(parent)
        self.username = tk.StringVar(parent)
        self.password = tk.StringVar(parent)
        self.destination = tk.StringVar(parent)
        self.target_file = tk.StringVar(parent)

        self.inputs = [
            [self.ip_address, "IP Address", self._ip_address_validator],
            [self.username, "Username", self._text_validator],
            [self.password, "Password", self._text_validator],
            [self.destination, "Destination", self._destination_validator],
            [self.target_file, "Target File", self._file_validator],
        ]

        for inp in self.inputs:
            self._render_input(parent, *inp)

        self._target_machine_trace()

    def _render_input(self, parent, variable, text, validator):
        ttk.Label(parent, text=text).grid(**self.get_next_position(
            row=True, column=False, inner=2
        ))
        entry = tk.Entry(
            parent, textvariable=variable,
            **ENTRY_CONFIG, width=int(2.5 * PAD)
        )

        # Add some pad to to right side
        position = self.get_next_position(row=False, column=False, inner=5)
        position["padx"] = (position["padx"][0], PAD)
        entry.grid(**position)

        variable.trace("w", lambda x, y, z: validator(variable, entry))

    def _render_action(self, parent):
        self.action = tk.StringVar(parent)
        actions = self._check_iterable_type(CopyActions)
        action_dropdown = ttk.OptionMenu(
            parent, self.action, actions[0], *actions
        )
        action_dropdown.grid(**self.get_next_position(
            row=False, column=False, inner=9
        ))
        action_dropdown.configure(**self._get_option_menu_style(actions))
        self.action.trace("w", lambda x, y, z: self._action_trace())

    def _render_reboot(self, parent):
        self.reboot = tk.BooleanVar(parent)
        ttk.Checkbutton(
            parent, text="Reboot",
            variable=self.reboot
        ).grid(**self.get_next_position(
            row=True, column=False, inner=2
        ))
