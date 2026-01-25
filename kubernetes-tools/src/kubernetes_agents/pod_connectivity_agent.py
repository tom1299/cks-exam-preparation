from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

from kubernetes_tools.agent_tools import (
    get_pod_by_name,
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
1. First, identify the source and target pods
2. Get their IP addresses and check if target exposes the required port
3. Find all network policies that apply to both pods
4. Check if there are egress rules allowing traffic from source to target
5. Check if there are ingress rules allowing traffic into the target
6. If policies look correct, test actual connectivity using the test_pod_connectivity tool

Remember: In Kubernetes with NetworkPolicies, if a pod is selected by ANY policy,
then traffic is denied by default unless explicitly allowed.
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

config = {"configurable": {"thread_id": "1"}}

# TODO: Create unit tests.
# Use local simple llm (which supports function calling)
# Compare with Agent that has full access to kubectl as a tool.
if __name__ == "__main__":
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "Why does the connection between pod "
                                                  "labeled 'app: backend' and 'app: mysql' on "
                                                  "port 3306 using protocol TCP not work in namespace test-app?"}]},
        config=config
    )

    print("\n" + "="*80)
    print("AGENT RESPONSE:")
    print("="*80)
    for message in response["messages"]:
        if hasattr(message, 'content') and message.content:
            print(f"\n{message.type.upper()}: {message.content}")
    print("="*80)
