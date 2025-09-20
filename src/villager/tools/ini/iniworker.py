import configparser

import loguru


project_level_config = configparser.ConfigParser(interpolation=configparser.Interpolation())


@loguru.logger.catch
def get_config_ini():
    """
    config.ini read/writer context manager
    :return:
    """

    # if config.ini is not exist, create it.
    with open("config.ini", "a") as f:
        pass
    if not project_level_config.sections():
        project_level_config["master"] = {
            "openai_api_key": "YOUR_API_KEY",
            "openai_endpoint": "https://api.aabao.vip/v1",
            "openai_proxy": ""
        }
        with open("config.ini", "w") as f:
            project_level_config.write(f)
        loguru.logger.warning("config.ini is empty, writing default content.")
    project_level_config.read("config.ini")
    yield project_level_config
    loguru.logger.debug("config.ini loaded.")

    # if config.ini's content is empty, write default content:
    # [master]
    # openai_api_key = YOUR_API_KEY
    # openai_endpoint = https://api.aabao.vip/v1
    # openai_proxy =


if __name__ == '__main__':
    get_config_ini()
    # output all of the config.ini content with jsonify
    import json

    data = {section: dict(project_level_config[section]) for section in project_level_config.sections()}
    print(json.dumps(data, indent=4))
