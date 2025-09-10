import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from config import llm_config, get_web_search_urls
import re

def format_search_results(results):
    """Format search results for the debate"""
    if not results or (isinstance(results, list) and len(results) == 0):
        return "No recent research data available. Please use general knowledge."
    
    formatted = "📊 Recent Research Findings:\n\n"
    if isinstance(results, list):
        for i, result in enumerate(results, 1):
            formatted += f"{i}. {result.get('title', 'No title')}\n"
            formatted += f"   Source: {result.get('href', 'No URL')}\n"
            formatted += f"   Summary: {result.get('body', 'No content')[:150]}...\n\n"
    else:
        formatted = str(results)
    
    return formatted

def create_debate_agents():
    """Create debate agents with manual web search integration"""
    
    # Researcher with manual web search capability
    researcher = AssistantAgent(
        name="Researcher",
        system_message="""You are a research assistant. Provide ONLY key facts about the topic.
        MAXIMUM: 50 words. Be extremely concise. No opinions.""",
        llm_config=llm_config,
    )
    
    # Pro Analyst Agent
    pro_analyst = AssistantAgent(
        name="Pro_Analyst",
        system_message="""You argue IN FAVOR of the topic. Present ONLY 2 main arguments.
        MAXIMUM: 20 words. Be concise and factual. No fluff.""",
        llm_config=llm_config,
    )
    
    # Con Analyst Agent
    con_analyst = AssistantAgent(
        name="Con_Analyst",
        system_message="""You argue AGAINST the topic. Present ONLY 2 main arguments.
        MAXIMUM: 20 words. Be concise and factual. No fluff.""",
        llm_config=llm_config,
    )
    
    # Synthesizer Agent
    synthesizer = AssistantAgent(
        name="Synthesizer",
        system_message="""You provide a balanced summary. Cover both perspectives briefly.
        MAXIMUM: 25 words. Be extremely concise. Structure: 1) For, 2) Against, 3) Conclusion.""",
        llm_config=llm_config,
    )
    
    # Moderator Agent
    moderator = AssistantAgent(
        name="Moderator",
        system_message="""You are a debate moderator. Your role is to:
        1. Initiate the discussion by asking the researcher to gather information
        2. Facilitate the debate between the pro and con analysts
        3. Ensure the conversation remains productive and on-topic
        4. Request a final summary from the synthesizer when appropriate
        5. Keep responses concise and focused""",
        llm_config=llm_config,
    )
    
    return researcher, pro_analyst, con_analyst, synthesizer, moderator

def main():
    """Main function to run the debate system"""
    print("Initializing Debate Agents...")
    
    # Create agents
    researcher, pro_analyst, con_analyst, synthesizer, moderator = create_debate_agents()
    
    # Create group chat
    groupchat = GroupChat(
        agents=[researcher, pro_analyst, con_analyst, synthesizer, moderator],
        messages=[],
        max_round=3,  # Enough for good discussion without being too long
        speaker_selection_method="round_robin",
        allow_repeat_speaker=True,
    )
    
    manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)
    
    # Start conversation
    print("\n🤖 Debate System Ready!")
    print("💡 Enter a topic for debate (or 'quit' to exit):")
    
    while True:
        topic = input("\nTopic: ").strip()
        if topic.lower() in ['quit', 'exit', 'q']:
            break
            
        if not topic:
            print("Please enter a topic.")
            continue
            
        print(f"\n🎯 Starting debate on: {topic}")
        print("=" * 60)
        
        # First, perform web search manually
        print("🔍 Researching topic...")
        try:
            search_results = get_web_search_urls(topic, max_results=4)
            research_summary = format_search_results(search_results)
            print("✅ Research completed successfully!")
        except Exception as e:
            research_summary = f"⚠️ Web search unavailable. Using general knowledge. Error: {str(e)}"
            print(f"❌ Research error: {e}")
        
        # Initiate the conversation with research included
        try:
            moderator.initiate_chat(
                manager,
                message=f"""Let's debate the topic: {topic}

{research_summary}

**Debate Process:**
1. Researcher: Add any additional insights or context from your knowledge
2. Pro_Analyst: Present 2-3 strong arguments IN FAVOR based on the research
3. Con_Analyst: Present 2-3 strong arguments AGAINST based on the research  
4. Open discussion: Respond to each other's points constructively
5. Synthesizer: Provide a balanced 3-paragraph summary of key arguments

**Guidelines:**
- Keep responses focused and evidence-based
- Reference the research findings when possible
- Maintain respectful and constructive dialogue
- Aim for 2-3 paragraphs per response

Let the debate begin! 🎤""",
            )
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            print("💡 Please check your API key and internet connection.")
            
        print("=" * 60)
        print("✅ Debate completed!\n")

if __name__ == "__main__":
    main()