# test_debate_simple.py
from autogen import AssistantAgent, GroupChat, GroupChatManager
from config import llm_config

# Simple debate test without web search
researcher = AssistantAgent(
    name="Researcher",
    llm_config=llm_config,
    system_message="You provide factual information about topics."
)

pro = AssistantAgent(
    name="Pro_Analyst", 
    llm_config=llm_config,
    system_message="You argue IN FAVOR of topics."
)

con = AssistantAgent(
    name="Con_Analyst",
    llm_config=llm_config, 
    system_message="You argue AGAINST topics."
)

moderator = AssistantAgent(
    name="Moderator",
    llm_config=llm_config,
    system_message="You moderate debates."
)

groupchat = GroupChat(
    agents=[researcher, pro, con, moderator],
    messages=[],
    max_round=6,
)

manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

print("🤖 Testing simple debate without web search...")
moderator.initiate_chat(
    manager,
    message="Debate: Is homeschooling a good option? Keep it to 2 rounds each.",
)

print("✅ Simple debate test completed!")