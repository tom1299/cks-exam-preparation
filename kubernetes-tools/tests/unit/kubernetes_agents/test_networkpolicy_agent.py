import uuid

from langchain_core.messages import AIMessage

from kubernetes_agents.networkpolicy_agent import nwp_agent
from kubernetes_tools import pods


class TestNWPAgent:

    def test_get_nwp_for_pod(self):
        namespace = "test-app2"
        backend_pods = pods.get_pods_by_labels({"app": "backend"}, namespace)
        backend_pod_name = backend_pods.items[0].metadata.name

        config = {"configurable": {"thread_id": f"test-{uuid.uuid4()}"}}

        response = nwp_agent.invoke(
            {"messages": [{"role": "user", "content": "Give me all network policy names associated with the pod "
                                                      f"name '{backend_pod_name}' in namespace {namespace}."}]},
            config=config
        )

        # TODO: Refactor tests to better isolate tool calls and responses.
        get_nwp_policies_invoked = False
        for message in response["messages"]:
            if isinstance(message, AIMessage) and not get_nwp_policies_invoked:
                ai_message: AIMessage = message
                assert ai_message.tool_calls is not None
                assert len(ai_message.tool_calls) ==1
                tool_call = ai_message.tool_calls[0]
                assert tool_call["name"] == "get_network_policies_for_pod"
                tool_call_args = tool_call["args"]
                assert tool_call_args["pod_name"] == backend_pod_name
                assert tool_call_args["namespace"] == namespace
                get_nwp_policies_invoked = True
            elif isinstance(message, AIMessage) and message.content is not None:
                assert "allow-dns" in message.content
                assert "deny-all" in message.content

        assert get_nwp_policies_invoked, "Expected get_network_policies_for_pod tool to be invoked"
