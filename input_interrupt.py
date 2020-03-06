"""
#  All rights reserved
#  Istanbul - Turkey - 2019
#
#  Author :   Erdogan Onal
#  Date :     2019.11.07
"""
import sys
from io import StringIO
import re

from msvcrt import getch as getchar


__author__ = "Erdogan Onal"
__mail__ = "erdoganonal@windowslive.com"


JUMP_PATTERN = re.compile(rb"[\s-]")

# Keys
FUNCTION_KEY = b'\x00'
SPECIAL = b'\xe0'

# bind with FUNCTION_KEY
FUNCTION_1 = b'\x3b'
FUNCTION_2 = b'\x3c'
FUNCTION_3 = b'\x3d'
FUNCTION_4 = b'\x3e'
FUNCTION_5 = b'\x3f'
FUNCTION_6 = b'\x40'
FUNCTION_7 = b'\x41'
FUNCTION_8 = b'\x42'
FUNCTION_9 = b'\x43'
FUNCTION_10 = b'\x44'

# bind with SPECIAL
FUNCTION_11 = b'\x85'
FUNCTION_12 = b'\x86'

UP_ARROW = b'\x48'
DOWN_ARROW = b'\x50'
RIGHT_ARROW = b'\x4d'
LEFT_ARROW = b'\x4b'

CTRL_UP_ARROW = b'\x8d'
CTRL_DOWN_ARROW = b'\x91'
CTRL_LEFT_ARROW = b'\x73'
CTRL_RIGHT_ARROW = b'\x74'


HOME = b'\x47'
END = b'\x4f'
PAGE_UP = b'\x49'
PAGE_DOWN = b'\x51'
INSERT = b'\x52'
DELETE = b'\x53'

# bind directly
CTRL_A = b'\x01'
CTRL_B = b'\x02'
CTRL_C = b'\x03'
CTRL_D = b'\x04'
CTRL_E = b'\x05'
CTRL_V = b'\x16'
BACKSPACE = b'\x08'
TAB = b'\x09'
NEWLINE = b'\x0a'
CARRIAGE_RETURN = b'\x0d'
ESCAPE = b'\x1b'


LINE_TERMINATOR = CARRIAGE_RETURN


def main():
    "Main function for testing the module directly."

    custom_input = InputWithInterrupt()

    def handle_ctrl_v(obj):
        import win32clipboard

        win32clipboard.OpenClipboard()
        clipboard_data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()

        sys.stdout.write(clipboard_data)
        obj.position += len(clipboard_data)
        return obj.current_input + clipboard_data.encode(obj.encoding)
    custom_input.bind_char(CTRL_V, handle_ctrl_v)

    value = None
    while value != "exit":
        value = custom_input.input("Enter your test, type exit to exit: ")
        print("Entered value is: {0}".format(value))


def _seek_to_start(obj):
    for _ in range(len(obj.current_input)):
        _handle_left_arrow(obj)
    return obj.current_input


def _seek_to_end(obj):
    for _ in range(len(obj.current_input)):
        _handle_right_arrow(obj)

    return obj.current_input


def _handle_backspace(obj):
    obj.clean_line()

    if obj.position > len(obj.current_input):
        obj.position = len(obj.current_input)
    elif obj.position == 0:
        return b''

    obj.current_input = obj.current_input[:obj.position-1]  \
        + obj.current_input[obj.position:]
    obj.position -= 1

    sys.stdout.write(obj.current_input.decode(obj.encoding))
    for _ in range(len(obj.current_input) - obj.position):
        sys.stdout.write(BACKSPACE.decode(obj.encoding))

    return obj.current_input


def _handle_delete(obj):
    if obj.position == len(obj.current_input):
        return obj.current_input
    _handle_right_arrow(obj)

    return _handle_backspace(obj)


def _handle_ctrl_a(obj):
    return _seek_to_start(obj)


def _handle_ctrl_c(obj):
    raise KeyboardInterrupt


def _handle_ctrl_d(obj):
    raise EOFError


def _handle_ctrl_e(obj):
    return _seek_to_end(obj)


def _handle_line_terminator(obj):
    return obj.current_input


def _handle_esc(obj):
    obj.clean_line()
    obj.position = 0
    return b''


def _handle_tab(obj):
    def print_matches(matches):
        # Split the matches for increase readablity
        max_matches_per_line = 5
        chunks = [matches[i:i + max_matches_per_line]
                  for i in range(0, len(matches), max_matches_per_line)]

        # Display matches
        for match in chunks:
            sys.stdout.write('\n')
            for each in match:
                sys.stdout.write("{:<20}".format(each))
        sys.stdout.write('\n')

    try:
        last_input = obj.current_input.split()[-1].decode(obj.encoding)
        if obj.current_input.endswith(b' '):
            sys.stdout.write(obj.current_input.decode(obj.encoding))
            # Small trick for prevent code dublication
            raise IndexError
    except IndexError:
        print_matches(obj.auto_complates)
        return obj.current_input

    match_list = [match for match in obj.auto_complates
                  if match.startswith(last_input)]
    if len(match_list) == 1:
        complated_part = match_list[0].lstrip(last_input)

        sys.stdout.write(complated_part)
        obj.current_input = obj.current_input + \
            complated_part.encode(obj.encoding)
        obj.position = len(obj.current_input)
    elif match_list:
        print_matches(match_list)
        sys.stdout.write(obj.current_input.decode(obj.encoding))

    return obj.current_input


def _handle_up_arrow(obj):
    if obj.vertical_position is None:
        obj.vertical_position = 0
    else:
        if obj.vertical_position < len(obj.inputs) - 1:
            obj.vertical_position += 1

    if obj.vertical_position >= len(obj.inputs):
        return b''

    previous_input = obj.inputs[obj.vertical_position]

    obj.position = len(obj.current_input)
    # Clean the whole line
    obj.clean_line()
    obj.position = len(previous_input)

    # Write the previous input
    sys.stdout.write(previous_input.decode(obj.encoding))

    return previous_input


def _handle_down_arrow(obj):
    if obj.vertical_position is None:
        if obj.inputs:
            obj.vertical_position = len(obj.inputs) - 1
        else:
            obj.vertical_position = 0
    else:
        if obj.vertical_position > 0:
            obj.vertical_position -= 1

    if obj.vertical_position >= len(obj.inputs):
        return b''

    previous_input = obj.inputs[obj.vertical_position]

    obj.position = len(obj.current_input)

    # Clean the whole line by sending delete
    obj.clean_line()

    obj.position = len(previous_input)

    # Write the previous input
    sys.stdout.write(previous_input.decode(obj.encoding))

    return previous_input


def _handle_right_arrow(obj):
    if obj.position < len(obj.current_input):
        sys.stdout.write(chr(obj.current_input[obj.position]))
        obj.position += 1

    return obj.current_input


def _handle_left_arrow(obj):
    if obj.position > 0:
        obj.position -= 1

        sys.stdout.write('\x08')

    return obj.current_input


def _handle_ctrl_up_arrow(obj):
    if not obj.inputs:
        return obj.current_input
    obj.vertical_position = len(obj.inputs) - 1
    return _handle_up_arrow(obj)


def _handle_ctrl_down_arrow(obj):
    obj.vertical_position = 0
    return _handle_down_arrow(obj)


def _handle_ctrl_right_arrow(obj):
    target_position = 0
    iterated_position = 0
    for part in JUMP_PATTERN.split(obj.current_input):
        if part:
            target_position = iterated_position
        iterated_position += len(part) + 1
        if target_position - 1 > obj.position:
            if part:
                break
    else:
        target_position = len(obj.current_input) + 1

    target_position -= 1
    for _ in range(target_position - obj.position):
        _handle_right_arrow(obj)

    obj.position = target_position
    return obj.current_input


def _handle_ctrl_left_arrow(obj):
    target_position = 0
    iterated_position = 0
    for part in JUMP_PATTERN.split(obj.current_input):
        if part:
            target_position = iterated_position
        iterated_position += len(part) + 1
        if iterated_position >= obj.position:
            break

    for _ in range(obj.position - target_position):
        _handle_left_arrow(obj)

    obj.position = target_position
    return obj.current_input


class InputExceptionBase(Exception):
    "Base exception for this module"


class UnbindedKeySequence(InputExceptionBase):
    "Raises when the key not in the binded sequence"

    def __init__(self, char1, char2):
        super().__init__(
            "Unbinded key in the sequence: {0}, {1}"
            "".format(char1, char2)
        )


class FunctionExpected(InputExceptionBase):
    "Raises when the given argument is not a function"

    def __init__(self, argument_name):
        super().__init__(
            "argument {0} should be function or function-like"
            "".format(argument_name)
        )


class InputWithInterrupt():
    "A simple full custimized class for reading inputs"
    inputs = []
    auto_complates = []
    learn = True

    def __init__(self, encoding=None):
        self.position = 0
        self.vertical_position = None
        self.current_input = b''
        self.encoding = encoding or sys.getdefaultencoding()

        self._char_registry = {}
        self._char_sequence_registry = {}

        self._auto_bind()

    @staticmethod
    def _check_char(char):
        if not isinstance(char, bytes):
            raise ValueError("only bytes or byte-likes excepted")

    @classmethod
    def add_auto_complate(cls, *args):
        "Adds given string(s) in the complate list"
        for arg in args:
            cls.auto_complates.append(arg)

    def _check_callable(self, callable_, validate):
        if not callable(callable_):
            raise FunctionExpected("on_press")

        if validate:
            # Test the callable
            stdout = sys.stdout
            sys.stdout = StringIO()
            try:
                callable_(self)
            finally:
                sys.stdout = stdout

    def bind_char(self, char, on_press, validate=True):
        "bind the character to the given function"
        self._check_callable(on_press, validate)
        self._check_char(char)

        self._char_registry[char] = on_press

    def unbind_char(self, char):
        "Unbind the character from binded function"
        self._char_registry.pop(char)

    def bind_char_sequence(self, char1, char2, on_press, validate=True):
        "bind the character sequence to the given function"
        self._check_callable(on_press, validate)
        self._check_char(char1)
        self._check_char(char2)

        try:
            self._char_sequence_registry[char1][char2] = on_press
        except KeyError:
            self._char_sequence_registry[char1] = {}
            self._char_sequence_registry[char1][char2] = on_press

    def unbind_char_sequence(self, char1, char2):
        "Unbind the character sequence from binded function"
        self._char_sequence_registry[char1].pop(char2)

    def get_char_handler(self, char):
        "Returns the handler function for given character"
        return self._char_registry.get(char, None)

    def get_char_sequence_handler(self, char):
        "Returns the handler function for given character sequence"
        on_key_function = self._char_sequence_registry.get(char, None)
        if on_key_function is not None:
            new_char = getchar()
            try:
                return on_key_function[new_char]
            except KeyError:
                raise UnbindedKeySequence(char, new_char)
        return None

    def _bind_special_char(self, char, on_press):
        self.bind_char_sequence(SPECIAL, char, on_press)

    def _bind_function_keys(self, char, on_press):
        self.bind_char_sequence(FUNCTION_KEY, char, on_press)

    def _auto_bind(self):
        self.bind_char(BACKSPACE, _handle_backspace)
        self.bind_char(CTRL_A, _handle_ctrl_a)
        # raises KeyboardInterrupt exception, if called
        self.bind_char(CTRL_C, _handle_ctrl_c, validate=False)
        # raises EOFError exception, if called
        self.bind_char(CTRL_D, _handle_ctrl_d, validate=False)
        self.bind_char(CTRL_E, _handle_ctrl_e)
        self.bind_char(LINE_TERMINATOR, _handle_line_terminator)
        self.bind_char(ESCAPE, _handle_esc)
        self.bind_char(TAB, _handle_tab)

        self._bind_special_char(UP_ARROW, _handle_up_arrow)
        self._bind_special_char(DOWN_ARROW, _handle_down_arrow)
        self._bind_special_char(RIGHT_ARROW, _handle_right_arrow)
        self._bind_special_char(LEFT_ARROW, _handle_left_arrow)
        self._bind_special_char(CTRL_RIGHT_ARROW, _handle_ctrl_right_arrow)
        self._bind_special_char(CTRL_LEFT_ARROW, _handle_ctrl_left_arrow)
        self._bind_special_char(CTRL_UP_ARROW, _handle_ctrl_up_arrow)
        self._bind_special_char(CTRL_DOWN_ARROW, _handle_ctrl_down_arrow)
        self._bind_special_char(DELETE, _handle_delete)
        self._bind_special_char(END, _seek_to_end)
        self._bind_special_char(HOME, _seek_to_start)
        self._bind_special_char(PAGE_UP, _handle_ctrl_up_arrow)
        self._bind_special_char(PAGE_DOWN, _handle_ctrl_down_arrow)

        self._bind_special_char(FUNCTION_11, lambda obj: obj.current_input)
        self._bind_special_char(FUNCTION_12, lambda obj: obj.current_input)

    def set_defaults(self):
        "Set all settings to the default"
        self.position = 0
        self.vertical_position = None
        self.current_input = b''

        self.inputs = []
        self._char_registry = {}
        self._char_sequence_registry = {}

        self._auto_bind()

    def _handle_char(self, char):
        on_press = self.get_char_sequence_handler(char)
        if on_press:
            return on_press(self)

        on_press = self.get_char_handler(char)
        if on_press:
            return on_press(self)

        temp_input = list(self.current_input)
        temp_input.insert(self.position, ord(char))

        for idx in range(self.position, len(self.current_input) + 1):
            sys.stdout.write(chr(temp_input[idx]))

        for _ in range(len(self.current_input) - self.position):
            sys.stdout.write('\x08')

        self.position += 1

        return bytes(temp_input)

    def clean_line(self):
        "Cleans the line"
        length = len(self.current_input)

        for _ in range(self.position):
            sys.stdout.write(BACKSPACE.decode(self.encoding))

        for _ in range(length):
            sys.stdout.write(' ')

        for _ in range(length):
            sys.stdout.write(BACKSPACE.decode(self.encoding))

    def input(self, message=''):
        "Reads from stdin until newline"
        char = b''
        self.current_input = b''
        self.position = 0
        self.vertical_position = None
        sys.stdout.write(message)
        sys.stdout.flush()
        while char != LINE_TERMINATOR:
            char = getchar()
            self.current_input = self._handle_char(char)
            sys.stdout.flush()

        sys.stdout.write('\n')
        sys.stdout.flush()

        self.current_input = self.current_input.strip(LINE_TERMINATOR)
        if (not self.inputs
                or self.inputs[0] != self.current_input
                and self.current_input):
            self.inputs.insert(0, self.current_input)
            if self.learn:
                self.add_auto_complate(
                    self.current_input.decode(self.encoding))
        return self.current_input.decode(self.encoding)


def cinput(message=''):
    "Customized input"
    return InputWithInterrupt().input(message)


if __name__ == "__main__":
    main()
