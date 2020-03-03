"""
Target Type: Select the type of target.
             e.g., {target_types}
  Skip Build:  Skips build if checked.
    Compile Type: Select the type of compile.
                  e.g., {compile_types}
    Parallel Compile: Starts the compile with
                      parallel option.
    Edit Linker: Allows you to edit linker script,
                 and debug configurations.(Mode -> UART)
                 e.g., {edit_linker_options}
        Expand size: The amount for expanding linker script.
    Output: A filename that the output will be stored.
    Partial Compile: Compiles only the given paths and
                     links. Stops on error.
        Compile List: Opens a new window for partial
                      compile paths. New line seperated.
"""
import os

import tkinter as tk
from tkinter import ttk, messagebox

from compiler_helper import EXECUTABLE_FILE_PATH, \
    TargetTypes, CompileTypes, \
    AutoBoolType, CPUTypes, \
    CompilerConfig
from layout_base import LayoutBase, \
    to_comma_string, ENTRY_CONFIG, configure

COMPILER_HELP = __doc__.strip().format(
    target_types=to_comma_string(TargetTypes),
    compile_types=to_comma_string(CompileTypes),
    edit_linker_options=to_comma_string(AutoBoolType)
)


class CompileLayout(LayoutBase):
    "The Compiler Frame"
    # pylint: disable=too-many-instance-attributes

    def __init__(self, transfer_layout):
        super().__init__()
        self.target_type = None  # OC2, IPC
        self.skip_build = None
        self.compile_type = None  # Optimized, Unoptiomized, Link-Only
        self.parallel_compile = None
        self.edit_linker = None
        self.expand_size = None
        self.partial_compile = None
        self.partial_compile_text = []
        self.output = None
        self._transfer_layout = transfer_layout
        self.parent = None

    def _target_type_trace(self):
        # self.target_type.get()
        try:
            cpu_type = self._transfer_layout.cpu_type.get()
            target_type = self.target_type.get()
        except AttributeError:
            # Not rendered yet
            return

        path = os.path.join(
            EXECUTABLE_FILE_PATH.format(self._get_enum_value_from_name(
                target_type, TargetTypes
            )),
            self._get_enum_value_from_name(cpu_type, CPUTypes)
        )
        self._transfer_layout.target_file.set(path)

    def _compile_type_trace(self):
        pass

    def _edit_linker_types_trace(self, label, entry):
        if self.edit_linker.get() in (AutoBoolType.ALWAYS.name,):
            state = tk.NORMAL
        else:
            state = tk.DISABLED

        label.configure(state=state)
        entry.configure(state=state)

    def _partial_compile_trace(self, button):
        if self.partial_compile.get():
            state = tk.NORMAL
        else:
            state = tk.DISABLED

        button.configure(state=state)

    def _partial_compile_validate(self):
        if not self.partial_compile.get():
            return True

        non_empty_path_count = 0

        for path in self.partial_compile_text:
            if not path or path.strip().startswith('#'):
                continue

            build_xml_path = os.path.join(path, "build.xml")
            if not os.path.isfile(build_xml_path):
                messagebox.showerror(
                    "Invalid component path",
                    "The build.xml not exist for given path[{0}]".format(path)
                )
                return False
            non_empty_path_count += 1

        if not non_empty_path_count:
            messagebox.showerror(
                "Empty paths",
                "Partial compile selected but no path passed."
            )
            return False

        return True

    def validate(self):
        "Checks the validity of entire inputs"
        if self.skip_build.get():
            return True

        if not self._text_validator(self.output):
            messagebox.showerror(
                "Invalid Name",
                "Output file name is not valid"
            )
            return False

        if not self._number_validator(self.expand_size):
            messagebox.showerror(
                "Invalid Value",
                "Expand size should be number"
            )
            return False

        return self._partial_compile_validate()

    def get_command_line_string(self):
        "Returns the string that passed to the compiler script"
        if not self.validate():
            return None

        command_line = "--target {0} ".format(self.target_type.get())
        if self.skip_build.get():
            command_line += "--skip-build "
        else:
            command_line += "--compile-type {0} ".format(
                self.compile_type.get())
            if self.parallel_compile.get():
                command_line += "--parallel "
            if self.partial_compile.get():
                command_line += "--partial-compile "
                for path in set(self.partial_compile_text):
                    if not path.strip().startswith('#'):
                        command_line += "{0} ".format(path)

            command_line += "--edit-linker {0} ".format(self.edit_linker.get())
            if self.edit_linker.get() in (AutoBoolType.ALWAYS,):
                command_line += "--linker-expand-size {0} ".format(
                    self.expand_size.get())
            command_line += "--output {0} ".format(self.output.get())
        return command_line + " --non-interactive --force "

    def get_current_config(self):
        "Returns the string that passed to the compiler script"
        if not self.validate():
            return None

        partial_compile = []
        for path in self.partial_compile_text:
            if not path or path.strip().startswith('#'):
                continue
            partial_compile.append(path)

        return CompilerConfig(
            target_type=self._name_to_enum(
                self.target_type.get(), TargetTypes),
            skip_build=self.skip_build.get(),
            compile_type=self._name_to_enum(
                self.compile_type.get(), CompileTypes),
            parallel_compile=self.parallel_compile.get(),
            partial_compile=partial_compile if self.partial_compile.get() else None,
            edit_linker=self._name_to_enum(
                self.edit_linker.get(), AutoBoolType),
            expand_size=self.expand_size.get(),
            output=self.output.get()
        )

    def render(self, parent, **grid_options):
        "Renders the frame"
        compiler_frame = ttk.Frame(parent)
        compiler_frame.grid(**grid_options)

        target_types = self._check_iterable_type(TargetTypes)

        self.target_type = tk.StringVar(compiler_frame)
        targets_dropdown = ttk.OptionMenu(
            compiler_frame, self.target_type,
            target_types[0], *target_types
        )
        targets_dropdown.grid(**self.get_next_position(True, True))
        targets_dropdown.configure(**self._get_option_menu_style(target_types))
        self.target_type.trace("w", lambda x, y, z: self._target_type_trace())

        parent = self._render_skip_build_frame(compiler_frame)

        self._render_compile_types(parent)
        self._render_edit_linker(parent)
        self._render_output(parent)
        self._render_partial_compile(parent)

        self._target_type_trace()

        return compiler_frame

    def _render_skip_build_frame(self, master):
        self.parent = ttk.Frame(master)

        # Add a checkbox for skipping the build
        self.skip_build = tk.BooleanVar(master)
        skip_build = ttk.Checkbutton(
            master, text="Skip Build",
            variable=self.skip_build,
            command=lambda: self.toggle_children_states(
                self.parent, self.skip_build)
        )
        skip_build.grid(**self.get_next_position(
            row=True, column=False, inner=1
        ))
        self.parent.grid(**self.get_next_position(row=True, column=False))

        return self.parent

    def _render_compile_types(self, parent):
        # Add CompileType dropdown
        compile_types = self._check_iterable_type(CompileTypes)

        self.compile_type = tk.StringVar(parent)
        compiles_dropdown = ttk.OptionMenu(
            parent, self.compile_type, compile_types[0], *compile_types
        )
        compiles_dropdown.grid(**self.get_next_position(
            True, True, inner=2
        ))
        compiles_dropdown.configure(**self._get_option_menu_style(
            compile_types
        ))
        self.compile_type.trace(
            "w", lambda x, y, z: self._compile_type_trace()
        )

        self.parallel_compile = tk.BooleanVar(parent)
        parallel_compile = ttk.Checkbutton(
            parent, text="Parallel",
            variable=self.parallel_compile
        )
        parallel_compile.grid(**self.get_next_position(
            True, False, inner=2
        ))

    def _render_edit_linker(self, parent):
        # Add EditLinker dropdown
        edit_linker_types = self._check_iterable_type(AutoBoolType)

        self.edit_linker = tk.StringVar(parent)
        edit_linker = ttk.OptionMenu(
            parent, self.edit_linker, edit_linker_types[0], *edit_linker_types
        )
        edit_linker.grid(**self.get_next_position(
            True, False, inner=2
        ))
        edit_linker.configure(**self._get_option_menu_style(edit_linker_types))

        self.expand_size = tk.StringVar(parent)
        expand_size_label = ttk.Label(parent, text="Expand size")
        expand_size_label.grid(**self.get_next_position(
            True, False, inner=4
        ))

        expand_size_entry = tk.Entry(
            parent, textvariable=self.expand_size,
            **ENTRY_CONFIG
        )
        expand_size_entry.grid(**self.get_next_position(
            False, False, inner=7
        ))

        self.edit_linker.trace("w", lambda x, y, mode: self._edit_linker_types_trace(
            expand_size_label, expand_size_entry
        ))

        self._edit_linker_types_trace(expand_size_label, expand_size_entry)
        self._bind[self._edit_linker_types_trace] = [
            expand_size_label, expand_size_entry
        ]

        self.expand_size.trace("w", lambda x, y, z: self._number_validator(
            self.expand_size, expand_size_entry
        ))
        self._number_validator(self.expand_size, expand_size_entry)

    def _render_output(self, parent):
        self.output = tk.StringVar(parent)

        output_label = ttk.Label(parent, text="Output")
        output_label.grid(**self.get_next_position(
            row=True, column=False, inner=2
        ))

        output_entry = tk.Entry(
            parent, textvariable=self.output,
            **ENTRY_CONFIG
        )
        output_entry.grid(**self.get_next_position(
            row=False, column=False, inner=7
        ))
        self.output.trace("w", lambda x, y, z: self._text_validator(
            self.output, output_entry
        ))
        self._text_validator(self.output, output_entry)

    def _render_partial_compile(self, parent):
        self.partial_compile = tk.BooleanVar(parent)
        ttk.Checkbutton(
            parent, text="Partial Compile",
            variable=self.partial_compile
        ).grid(**self.get_next_position(
            row=True, column=False, inner=2
        ))

        button = ttk.Button(
            parent, text="+",
            command=self._render_partial_compile_entry
        )
        button.grid(**self.get_next_position(
            row=False, column=False, inner=7
        ))

        self.partial_compile.trace(
            "w", lambda x, y, z: self._partial_compile_trace(button)
        )
        self._partial_compile_trace(button)
        self._bind[self._partial_compile_trace] = [button]

    def _render_partial_compile_entry(self):
        def _safe_close(text_widget):
            text = text_widget.get(1.0, tk.END).strip('\n')
            self.partial_compile_text = text.splitlines()

            window.destroy()

        window = tk.Tk()
        window.title("Partial Compile")
        window.resizable(False, False)

        ttk.Label(
            window,
            text="Add component paths. Use newline for another component"
        ).grid(row=0, column=0)
        text = tk.Text(window, foreground="white")
        text.grid(row=1, column=0)
        text.insert(tk.END, '\n'.join(self.partial_compile_text))

        ttk.Button(window, text="Done", command=lambda: _safe_close(text)).grid(
            row=2, column=0
        )

        configure(window)
        window.mainloop()
