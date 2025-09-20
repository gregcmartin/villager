import platform
import subprocess

from config import Master


def pyeval(python_codeblock: str):
    """
    A python playground!
    :param python_codeblock:
    :param python:
    :return:
    """
    return eval(python_codeblock)


def os_execute_cmd(system_command: str):
    """
    Execute system command here!
    :param system_command: The command to be executed in the system shell.
    :return: A tuple containing the stdout, stderr, and return code of the command.
    """
    try:
        result = subprocess.run(
            system_command,
            shell=True,
            text=True,
            capture_output=True,
            encoding=Master.get('misc').get('shell_encode'),
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return None, str(e), -1
