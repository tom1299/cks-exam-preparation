from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

from kubernetes_tools.agent_tools import (
    get_pods_by_labels,
    get_pod_ip_addresses,
    check_pod_exposes_port,
    test_pod_connectivity
)

from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are a Kubernetes Pod connectivity agent. Your role is to
test connectivity between pods.
You have access to the following tools:

* Get Poods by labels and namespace
* Find out whether a pod exposes a specific port
* Test connectivity between pods using ephemeral debug containers with netcat

For testing connectivity between pods, follow these steps:
1. First, get the target pod by its labels and namespace
2. Check whether the target pod exposes the required port
3. If not exposed, report that connectivity cannot be tested
4. If the port is exposed, get the IP address of the target pod
5. Test the pods connectivity from the source pod to the target pods IP, port and protocol
"""

checkpointer = InMemorySaver()

tools = [
    # TODO: Add get_pod_by_name if needed in future and see whether in
    # a multi agent environment get_pods_by_labels could be delegated to Pod Agent
    get_pods_by_labels,
    # Removed since agent always used pod spec itself to get the ip address
    # TODO: Can tool calls be forced ?
    # get_pod_ip_addresses,
    check_pod_exposes_port,
    test_pod_connectivity
]

def create_debug_connectivity_agent(
    agent_model,
):
    agent = create_agent(
        model=agent_model,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        checkpointer=checkpointer
    )
    return agent

debug_connectivity_agent = create_debug_connectivity_agent(
    agent_model=init_chat_model(
        "gpt-5-nano",
        temperature=0,
        timeout=60,
        max_tokens=4000),
)
