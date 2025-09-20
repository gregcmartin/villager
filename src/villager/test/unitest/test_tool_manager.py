import random

from scheduler.core.tools.common_tool import pyeval, os_execute_cmd
from scheduler.toolschain.tools_manager import ToolsManager, extract_json_with_positions


def test_ToolsManager():
    puzzle = ""
    p1 = random.randint(-100, 100)
    p2 = random.randint(-100, 100)
    correct_res = p1 * p2
    puzzle = f"{p1}*{p2}"
    TM = ToolsManager()
    TM.register_func(pyeval)
    TM.register_func(os_execute_cmd)
    jsons = extract_json_with_positions(
        """
        huh?%%%%{
        "name": "pyeval",
    "parameters": {
        "python_codeblock": "%s"
    }
}%%%%
        """ % puzzle)
    assert len(jsons) > 0
    for it in jsons:
        res = TM.NLP_unserialize(it[0])
        print("result: %s" % res)
        assert res == correct_res
