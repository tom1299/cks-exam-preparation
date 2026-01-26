from kubernetes_agents.pod_connectivity_agent import agent

class TestPodConnectivityAgent:

    def test_check_pod_connectivity_working(self):
        # Test the method that checks pod connectivity
        pass

    def test_check_pod_connectivity_not_working(self):
        config = {"configurable": {"thread_id": "1"}}

        # Use local simple llm (which supports function calling)
        # Compare with Agent that has full access to kubectl as a tool.
        response = agent.invoke(
            {"messages": [{"role": "user", "content": "Why does the connection between pod "
                                                      "labeled 'app: backend' and 'app: mysql' on "
                                                      "port 3306 using protocol TCP not work in namespace test-app?"}]},
            config=config
        )

        print("\n" + "=" * 80)
        print("AGENT RESPONSE:")
        print("=" * 80)
        for message in response["messages"]:
            if hasattr(message, 'content') and message.content:
                print(f"\n{message.type.upper()}: {message.content}")
        print("=" * 80)


