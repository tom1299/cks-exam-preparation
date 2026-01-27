from pytest import fixture
from langchain.chat_models import init_chat_model


@fixture(scope="module")
def openai_model():
    return init_chat_model(
        "gpt-5-nano",
        temperature=0,
        timeout=60,
        max_tokens=4000,
    )


@fixture(scope="module")
def anthropic_model():
    return init_chat_model(
        "claude-sonnet-4-5-20250929",
        temperature=0,
        timeout=60,
        max_tokens=4000,
    )
