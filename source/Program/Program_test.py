import pytest
from datetime import datetime
from source.enums import AutoRestart, Signals
from Program import Program


@pytest.fixture
def valid_properties():
    return {
        "count": 2,
        "auto_start": False,
        "auto_restart": "ALWAYS",
        "exit_code": 1,
        "max_retry": 3,
        "stop_signal": "HUP",
        "stop_time": "10",
        "cmd": "echo 'Hello, World!'",
        "working_dir": "/path/to/working_dir",
        "stdout": "stdout.log",
        "stderr": "stderr.log",
        "umask": 22,
    }


def test_valid_initialization(valid_properties):
    program = Program("TestProgram", valid_properties)
    assert program.count == 2
    assert not program.auto_start
    assert program.auto_restart == AutoRestart.ALWAYS
    assert program.exit_code == 1
    assert isinstance(program.start_time, datetime)
    assert program.retries == 3
    assert program.stop_signal == Signals.HUP
    assert isinstance(program.stop_time, datetime)
    assert program.cmd == "echo 'Hello, World!'"
    assert program.working_dir == "/path/to/working_dir"
    assert program.stdout == "stdout.log"
    assert program.stderr == "stderr.log"
    assert program.umask == 22


def test_invalid_initialization_missing_cmd(valid_properties):
    del valid_properties["cmd"]
    with pytest.raises(ValueError) as e:
        Program("TestProgram", valid_properties)
    assert str(e.value) == "Program TestProgram has no cmd attribute"


def test_invalid_initialization_wrong_type(valid_properties):
    valid_properties["count"] = "not_an_integer"
    with pytest.raises(TypeError) as e:
        Program("TestProgram", valid_properties)
    assert (
        str(e.value)
        == "Invalid type for attribute count in TestProgram. Expected <class 'int'>, got <class 'str'>"
    )
