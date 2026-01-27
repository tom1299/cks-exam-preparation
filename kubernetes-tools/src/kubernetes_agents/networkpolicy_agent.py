from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

from kubernetes_tools.agent_tools import (
    get_network_policies_for_pod,
    contains_ingress_rule,
    contains_egress_rule
)

from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are a Kubernetes NetworkPolicy Agent. Your role is to retrieve
NetworkPolicies for Pods and to find out whether a pod matches their ingress or egress rules.
You have access to the following tools:

* Retrieve pod information by name and namespace
* Check if a network policy contains an ingress rule matching specified port, peer selector, and protocol
* Check if a network policy contains an egress rule matching specified port, peer selector, and protocol
"""

checkpointer = InMemorySaver()

tools = [
    get_network_policies_for_pod,
    contains_ingress_rule,
    contains_egress_rule
]

def create_nwp_agent(
    agent_model,
):
    pod_agent = create_agent(
        model=agent_model,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        checkpointer=checkpointer
    )
    return pod_agent

nwp_agent = create_nwp_agent(
    agent_model=init_chat_model(
        "gpt-5-nano",
        temperature=0,
        timeout=60,
        max_tokens=4000),
)
