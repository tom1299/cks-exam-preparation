## PyCharm
### Assign categories to folders
In order for this setup to work the folders src and test need to be classified:
https://www.jetbrains.com/help/pycharm/configuring-project-structure.html#mark-dir-settings

## Next steps
* [X] Refactor connectivity agent tools analogous to pod agent
* [X] Create test case analogous to pod agent for nwp agemt
* [X] Refactor connectivity agent tools analogous to connectivity agent
* [ ] Create multi agent setup with both pod and nwp agent
  * Use subagent with parallel tool calls: https://docs.langchain.com/oss/python/langchain/models#parallel-tool-calls ?
  * Use this example as reference: https://docs.langchain.com/oss/python/langchain/multi-agent/subagents
  * Parallel tool calls / agent invocations still block the main agent though.
* [ ] Examine why streaming in pod agent test does not work with anthropic model
* [ ] Use langchain agent evals for testing agents: https://github.com/langchain-ai/agentevals