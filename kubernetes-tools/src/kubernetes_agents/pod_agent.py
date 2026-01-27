from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

from kubernetes_tools.pods import (
    get_pods_by_labels
)

from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are a Kubernetes Pod Agent. Your role is to retrieve Pods information
based on label selector and namespace. You have access to the following tools:

* Retrieve pod information by labels and namespace
"""

checkpointer = InMemorySaver()

tools = [
    get_pods_by_labels
]

def create_pod_agent(
    agent_model,
):
    pod_agent = create_agent(
        model=agent_model,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        checkpointer=checkpointer
    )
    return pod_agent



agent = create_pod_agent(
    agent_model=init_chat_model(
        "gpt-5-nano",
        temperature=0,
        timeout=60,
        max_tokens=4000),
)
