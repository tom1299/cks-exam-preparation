import uuid

from langchain_core.messages import AIMessage
from kubernetes_agents.pod_agent import agent

class TestPodAgent:

    def test_get_pod_information_for_existing_pod(self):
        config = {"configurable": {"thread_id": f"test-{uuid.uuid4()}"}}

        response = agent.invoke(
            {"messages": [{"role": "user", "content": "Give me all image names of containers in the pod "
                                                      "labeled 'app: backend' in namespace test-app."
                                                      "Do not include ephemeral containers."}]},
            config=config
        )

        # TODO: Refactor tests to better isolate tool calls and responses.
        get_pods_tool_invoked = False
        for message in response["messages"]:
            if isinstance(message, AIMessage) and not get_pods_tool_invoked:
                ai_message: AIMessage = message
                assert ai_message.tool_calls is not None
                assert len(ai_message.tool_calls) ==1
                tool_call = ai_message.tool_calls[0]
                assert tool_call["name"] == "get_pods_by_labels"
                tool_call_args = tool_call["args"]
                assert tool_call_args["labels"] == {"app": "backend"}
                assert tool_call_args["namespace"] == "test-app"
                get_pods_tool_invoked = True
            elif isinstance(message, AIMessage) and message.content is not None:
                assert "python:3.9-slim" in message.content

        assert get_pods_tool_invoked, "Expected get_pods_by_labels tool to be invoked"
