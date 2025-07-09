#!/usr/bin/env python3
"""
Simple test for the ResearcherAgent without requiring LLM
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from backend.agents.researcher import ResearcherAgent

def test_researcher_agent():
    print("🔍 Testing ResearcherAgent Configuration...")
    
    # Test agent creation
    try:
        researcher_agent = ResearcherAgent()
        print("✅ ResearcherAgent initialized successfully")
        
        # Test tools
        print(f"📁 Directory tool: {researcher_agent.directory_tool.name}")
        print(f"📄 File tool: {researcher_agent.file_read_tool.name}")
        
        # Test agent creation
        agent = researcher_agent.create_agent()
        print(f"✅ Agent created: {agent.role}")
        print(f"🎯 Goal: {agent.goal}")
        print(f"🛠️ Tools: {[tool.name for tool in agent.tools]}")
        
        # Test task configuration
        tasks = researcher_agent.get_tasks()
        print(f"📋 Tasks configured: {len(tasks)}")
        for i, task in enumerate(tasks):
            print(f"   Task {i+1}: {task['description'][:100]}...")
        
        print("\n🎉 ResearcherAgent is properly configured!")
        return True
        
    except Exception as e:
        print(f"❌ ResearcherAgent test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_researcher_agent()
    if success:
        print("\n✅ ResearcherAgent is ready to use!")
        print("💡 To test with actual LLM, you need to:")
        print("   1. Set up OpenAI API key: export OPENAI_API_KEY=your_key")
        print("   2. Or configure another LLM provider in the agent")
        print("   3. Run a full crew with tasks")
    else:
        print("\n❌ ResearcherAgent needs fixes!")