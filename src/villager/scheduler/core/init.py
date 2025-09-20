import loguru
from kink import di
from langchain_openai import ChatOpenAI

from config import Master


class global_llm:
    def __enter__(self):
        loguru.logger.info("Initializing global LLM instance...")
        llm = ChatOpenAI(
            model=Master.get("default_model"),
            base_url=Master.get("openai_api_endpoint"),
            api_key=Master.get("openai_api_key"),
            temperature=0.95,
        )
        di['llm'] = llm
        loguru.logger.success(f"Global LLM initialized: {llm}")
        return llm

    def __exit__(self, exc_type, exc_val, exc_tb):
        ...
