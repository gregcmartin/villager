import json
import inspect
import re
from typing import Callable, Dict
from jsmin import jsmin

import loguru

from scheduler.core.tools.common_tool import pyeval, os_execute_cmd


class FunctionJSONConverter:
    @staticmethod
    def function_to_json(func: Callable):
        """
        Converts a function to a JSON string containing its metadata.

        Args:
            func (Callable): The function to convert.

        Returns:
            str: A JSON string containing the function's metadata.
        """
        if not callable(func):
            raise ValueError("Input must be a callable function.")

        # Get function signature
        sig = inspect.signature(func)

        # Prepare JSON-compatible dictionary
        func_data = {
            "name": func.__name__,
            "docstring": inspect.getdoc(func) or "",
            "parameters": [
                {
                    "name": param.name,
                    "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else None,
                }
                for param in sig.parameters.values()
            ],
            "return_type": str(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else None
        }

        return func_data

    @staticmethod
    def json_to_function(json_str: str) -> Dict:
        """
        Parses a JSON string containing function metadata.

        Args:
            json_str (str): The JSON string to parse.

        Returns:
            Dict: A dictionary containing the function's metadata.
        """
        try:
            func_data = json.loads(json_str)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string.")

        # Validate the JSON structure
        required_keys = {"name", "parameters"}
        if not required_keys.issubset(func_data):
            raise ValueError(f"JSON must contain the keys: {required_keys}")

        return {
            "name": func_data["name"],
            "parameters": [
                {
                    "value": param["value"],
                }
                for param in func_data["parameters"]
            ]
        }


class ToolsManager:
    def __init__(self):
        self.converter = FunctionJSONConverter()
        self.func_list = []

    def register_func(self, function: Callable):
        """
        Register a function to the tools manager.
        :param function:
        :return:
        """
        self.func_list.append({'jsonify': self.converter.function_to_json(function), 'func': function})

    def list_func(self):
        """
        List the func pools.
        :return:
        """
        return self.func_list

    def list_func_json(self):
        """
        Return jsonify func list.
        :return:
        """
        return [jsonify_help['jsonify'] for jsonify_help in self.func_list]

    def NLP_unserialize(self, json_str: str):
        """
        Get a function from a JSON string.
        用户可能输入:
        {"name":"plus_a_b","parameters":{"a":123,"b":234}}
        那么我们则需要从注册的函数池里找到这个函数然后直接调用
        :param json_str:
        :return:
        """
        json_str = jsmin(json_str)
        func_data = json.loads(json_str)
        func_name = func_data["name"]
        func_params = func_data.get("parameters", {})
        loguru.logger.debug(f"Parsed function: {func_name} with parameters: {func_params}")
        for item in self.func_list:
            if item["jsonify"]["name"] == func_name:
                loguru.logger.debug(f"Found function: {item['jsonify']}")
                function = item["func"]
                break
        else:
            raise ValueError(f"Function '{func_name}' not found in the registered functions.")

        # Call the function with the provided parameters
        try:
            func_result = function(**func_params)
            loguru.logger.debug(f"Function invoked successfully: {func_name} with result: {func_result}")
            return func_result
        except TypeError as e:
            raise ValueError(f"Error calling function '{func_name}': {e}")


def extract_json_strings(input_string):
    """
    Extract all valid JSON strings from a given input string.

    Args:
        input_string (str): The input string containing potential JSON strings.

    Returns:
        list: A list of valid JSON objects parsed from the input string.
    """
    json_objects = []
    decoder = json.JSONDecoder()
    idx = 0

    while idx < len(input_string):
        try:
            obj, end = decoder.raw_decode(input_string[idx:])
            json_objects.append(obj)
            idx += end
        except json.JSONDecodeError:
            idx += 1

    return json_objects


def extract_json_with_positions(input_string):
    """
    Extract all valid JSON strings along with their positions from a given input string.

    Args:
        input_string (str): The input string containing potential JSON strings.

    Returns:
        list: A list of tuples, each containing a JSON object as a string, its start index, and its end index.
    """
    results = []

    for match in re.finditer("%%(.*?)%%", input_string, flags=re.DOTALL):
        start, end = match.span()
        match_str = match.group(1)
        results.append((match_str, match.group()))

    return results

