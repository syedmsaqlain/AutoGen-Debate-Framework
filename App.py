from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
import os
from dotenv import load_dotenv
from main import create_debate_agents, get_web_search_urls, format_search_results
from autogen import GroupChat, GroupChatManager
from config import llm_config

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variable to store chat history
chat_history = []

class WebSocketManager:
    """Custom manager to send messages to web interface"""
    def __init__(self, socketio):
        self.socketio = socketio
        
    def send_message(self, agent_name, content):
        try:
            # Handle different message formats
            if isinstance(content, dict):
                message_text = content.get('content', str(content))
            else:
                message_text = str(content)
            
            # Clean and limit content
            message_text = message_text.strip()
            if len(message_text) > 2500:
                message_text = message_text[:2500] + "..."
            
            # Skip empty messages
            if not message_text or message_text.isspace():
                return
            
            message_data = {
                'sender': agent_name,
                'content': message_text,
                'timestamp': time.time()
            }
            
            # Send to web interface
            self.socketio.emit('agent_message', message_data)
            chat_history.append(message_data)
            
            # Also print to console for debugging
            print(f"WEB: {agent_name}: {message_text[:100]}...")
            
        except Exception as e:
            print(f"Error in send_message: {e}")

def run_debate(topic):
    """Run the debate and send messages to web interface"""
    try:
        websocket_manager = WebSocketManager(socketio)
        
        # Send initial message
        websocket_manager.send_message("System", f"🚀 Starting debate on: {topic}")
        time.sleep(1)
        
        # Perform web search first
        websocket_manager.send_message("System", "🔍 Researching topic...")
        try:
            search_results = get_web_search_urls(topic, max_results=4)
            research_summary = format_search_results(search_results)
            websocket_manager.send_message("Researcher", research_summary)
            websocket_manager.send_message("System", "✅ Research completed!")
        except Exception as e:
            error_msg = f"⚠️ Web search failed: {str(e)}. Using general knowledge."
            websocket_manager.send_message("System", error_msg)
            research_summary = error_msg
        time.sleep(1)
        
        # Create agents
        websocket_manager.send_message("System", "🤖 Initializing debate agents...")
        researcher, pro_analyst, con_analyst, synthesizer, moderator = create_debate_agents()
        time.sleep(1)
        
        # Create group chat
        groupchat = GroupChat(
            agents=[researcher, pro_analyst, con_analyst, synthesizer, moderator],
            messages=[],
            max_round=6,
            speaker_selection_method="round_robin",
            allow_repeat_speaker=True,
        )
        
        manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)
        
        # Start debate with research included
        moderator.initiate_chat(
            manager,
            message=f"""Let's debate the topic: {topic}

{research_summary}

**Debate Process:**
1. Researcher: Add additional insights from your knowledge
2. Pro_Analyst: Present arguments IN FAVOR based on the research
3. Con_Analyst: Present arguments AGAINST based on the research  
4. Open discussion: Respond to each other's points
5. Synthesizer: Provide a balanced summary

Keep responses focused and evidence-based. Let's begin!""",
            silent=True  # Don't print to console to avoid duplication
        )
        
        # Send all messages to web after completion
        for msg in groupchat.messages:
            if 'content' in msg and 'name' in msg:
                websocket_manager.send_message(msg['name'], msg['content'])
        
        websocket_manager.send_message("System", "✅ Debate completed successfully!")
        socketio.emit('debate_complete', {'status': 'success'})
        
    except Exception as e:
        error_msg = f'❌ Error: {str(e)}'
        print(f"Error in run_debate: {error_msg}")
        socketio.emit('agent_message', {
            'sender': 'System',
            'content': error_msg,
            'timestamp': time.time()
        })
        socketio.emit('debate_complete', {'status': 'error'})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_debate', methods=['POST'])
def start_debate():
    topic = request.json.get('topic', '').strip()
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    # Clear previous history
    global chat_history
    chat_history = []
    
    # Start debate in background thread
    thread = threading.Thread(target=run_debate, args=(topic,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'debate_started', 'topic': topic})

@app.route('/get_history')
def get_history():
    return jsonify(chat_history)

@app.route('/stop_debate', methods=['POST'])
def stop_debate():
    """Emergency endpoint to stop debate"""
    socketio.emit('agent_message', {
        'sender': 'System',
        'content': '⏹️ Debate stopped by user request',
        'timestamp': time.time()
    })
    return jsonify({'status': 'stopped'})

if __name__ == '__main__':
    print("🌐 Starting Web Interface...")
    print("📱 Open http://localhost:5000 in your browser")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)