import uuid

from langchain_core.messages import AIMessage

from kubernetes_agents.debug_connectivity_agent import debug_connectivity_agent
from kubernetes_tools import pods


class TestDebugConnectivityAgent:

    def test_port_exposed(self):
        namespace = "test-app"

        config = {"configurable": {"thread_id": f"test-{uuid.uuid4()}"}}

        response = debug_connectivity_agent.invoke(
            {"messages": [{"role": "user", "content": f"Does the pod labeled 'app: backend' in namespace "
                           f"{namespace} expose port 3306 using protocol TCP?"}]},
            config=config
        )

        tool_calls = ["get_pods_by_labels"]

        # TODO: Agent does not use tool call check_pod_exposes_port. LLM seems to answer directly.
        # Can we enforce tool usage ?
        # TODO: Find out to force tool usage instead of direct LLM answer.
        # tool_calls = ["get_pods_by_labels",
        #               "check_pod_exposes_port"]

        tool_call_counter = 0
        for message in response["messages"]:
            if isinstance(message, AIMessage) and tool_call_counter < len(tool_calls):
                ai_message: AIMessage = message
                assert ai_message.tool_calls is not None
                assert len(ai_message.tool_calls) ==1
                tool_call = ai_message.tool_calls[0]
                assert tool_call["name"] == tool_calls[tool_call_counter]
                tool_call_counter += 1

        assert len(tool_calls) == tool_call_counter, "Actual tool call count does not match expected tool call count"

        print(response)

    def test_connectivity_working(self):
        namespace = "test-app"

        config = {"configurable": {"thread_id": f"test-{uuid.uuid4()}"}}

        response = debug_connectivity_agent.invoke(
            {"messages": [{"role": "user", "content": "Test connectivity between pod "
                           "labeled 'app: backend' and 'app: mysql' on "
                           f"port 3306 using protocol TCP in namespace {namespace}."}]},
            config=config
        )

        # TODO: Refactor tests to better isolate tool calls and responses.
        tool_calls = ["get_pods_by_labels",
                      "check_pod_exposes_port",
                      "test_pod_connectivity"]

        tool_call_counter = 0
        for message in response["messages"]:
            if isinstance(message, AIMessage) and len(message.tool_calls) > 0:
                ai_message: AIMessage = message
                assert ai_message.tool_calls is not None
                tool_call = ai_message.tool_calls[0]
                print(f"{tool_call_counter}. tool called: {tool_call}")
                assert tool_call["name"] in tool_calls
                tool_call_counter += 1

        assert len(tool_calls) == tool_call_counter, "Actual tool call count does not match expected tool call count"

        final_response = response["messages"][-1].content.lower()
        assert "success" in final_response or "succeeded" in final_response, "Expected connectivity test to be successful"
