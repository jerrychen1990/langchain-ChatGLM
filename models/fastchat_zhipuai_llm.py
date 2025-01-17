from abc import ABC
import requests
from typing import Optional, List
from langchain.llms.base import LLM

from models.loader import LoaderCheckPoint
from models.base import (RemoteRpcModel,
                         AnswerResult)
from typing import (
    Collection,
    Dict
)


def _build_message_template() -> Dict[str, str]:
    """
    :return: 结构
    """
    return {
        "role": "",
        "content": "",
    }


class FastChatZhipuLLM(RemoteRpcModel, LLM, ABC):
    model_name: str = "chatglm_lite"
    max_token: int = 10000
    temperature: float = 0.01
    checkPoint: LoaderCheckPoint = None
    top_p = 0.9
    history = []
    history_len: int = 10

    def __init__(self, checkPoint: LoaderCheckPoint = None):
        super().__init__()
        self.checkPoint = checkPoint

    @property
    def _llm_type(self) -> str:
        return "FastChatZhipu"

    @property
    def _check_point(self) -> LoaderCheckPoint:
        return self.checkPoint

    @property
    def _history_len(self) -> int:
        return self.history_len

    def set_history_len(self, history_len: int = 10) -> None:
        self.history_len = history_len

    @property
    def _api_key(self) -> str:
        pass

    @property
    def _api_base_url(self) -> str:
        return self.api_base_url

    def set_api_key(self, api_key: str):
        pass

    def set_api_base_url(self, api_base_url: str):
        self.api_base_url = api_base_url

    def call_model_name(self, model_name):
        self.model_name = model_name

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        print(f"__call:{prompt}")
        try:
            import zhipuai
            import os
            # Not support yet
            zhipuai.api_key = os.environ["ZHIPU_API_KEY"]
        except ImportError:
            raise ValueError(
                "Could not import zhipuai python package. "
                "Please install it with `pip install openai`."
            )
        # create a chat completion
        prompt = self.build_message_list(prompt)
        response = zhipuai.model_api.invoke(
            model=self.model_name,
            prompt=prompt
        )
        print(response)
        resp = response["data"]["choices"][0]["content"]
        if resp[0] == '"' and resp[-1] == '"':
            resp = resp[1:-1]
        print(f"response:{resp}")
        print(f"+++++++++++++++++++++++++++++++++++")
        return resp

    # 将历史对话数组转换为文本格式
    def build_message_list(self, query) -> Collection[Dict[str, str]]:
        build_message_list: Collection[Dict[str, str]] = []
        history = self.history[-self.history_len:] if self.history_len > 0 else []
        for i, (old_query, response) in enumerate(history):
            user_build_message = _build_message_template()
            user_build_message['role'] = 'user'
            user_build_message['content'] = old_query
            system_build_message = _build_message_template()
            system_build_message['role'] = 'system'
            system_build_message['content'] = response
            build_message_list.append(user_build_message)
            build_message_list.append(system_build_message)

        user_build_message = _build_message_template()
        user_build_message['role'] = 'user'
        user_build_message['content'] = query
        build_message_list.append(user_build_message)
        return build_message_list

    def generatorAnswer(self, prompt: str,
                        history: List[List[str]] = [],
                        streaming: bool = False):

        try:
            import zhipuai
            import os
            # Not support yet
            zhipuai.api_key = os.environ["ZHIPU_API_KEY"]
        except ImportError:
            raise ValueError(
                "Could not import zhipuai python package. "
                "Please install it with `pip install openai`."
            )
        # create a chat completion
        prompt = self.build_message_list(prompt)
        response = zhipuai.model_api.invoke(
            model=self.model_name,
            prompt=prompt
        )

        history += [[prompt, response["data"]["choices"][0]["content"]]]
        answer_result = AnswerResult()
        answer_result.history = history
        resp = response["data"]["choices"][0]["content"]
        if resp[0] == '"' and resp[-1] == '"':
            resp = resp[1:-1]
        answer_result.llm_output = {"answer": resp}
        yield answer_result
