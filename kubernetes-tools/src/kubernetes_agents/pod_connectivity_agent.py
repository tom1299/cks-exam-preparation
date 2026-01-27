from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

from kubernetes_tools.agent_tools import (
    get_pod_by_name,
    get_pods_by_labels,
    get_pod_ip_addresses,
    check_pod_exposes_port,
    get_network_policies_for_pod,
    check_network_policy_allows_ingress,
    check_network_policy_allows_egress,
    test_pod_connectivity
)

from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are a Kubernetes Pod Connectivity Agent. Your role is to assist users in diagnosing
connectivity issues between pods within the same namespace. You have access to various tools to:

* Retrieve pod details by name and namespace
* Get pod IP addresses
* Check if pods expose specific ports
* Fetch network policies affecting pods
* Check for specific ingress and egress rules in network policies
* Test connectivity between pods using ephemeral debug containers with netcat

When analyzing connectivity issues:
1. First, get the source and target pods by their name / labels and namespace
2. Check whether the target pod exposes the required port
3. Get their IP addresses
4. Find all network policies that apply to both pods
5. Check if there are egress rules allowing traffic from source to target
6. Check if there are ingress rules allowing traffic into the target
7. If policies look correct, test actual connectivity using the test_pod_connectivity tool
"""

model = init_chat_model(
    "claude-sonnet-4-5-20250929",
    temperature=0,
    timeout=60,
    max_tokens=4000
)

checkpointer = InMemorySaver()

tools = [
    get_pod_by_name,
    get_pods_by_labels,
    get_pod_ip_addresses,
    check_pod_exposes_port,
    get_network_policies_for_pod,
    check_network_policy_allows_ingress,
    check_network_policy_allows_egress,
    test_pod_connectivity
]

agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=tools,
    checkpointer=checkpointer
)
