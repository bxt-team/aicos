#!/usr/bin/env python3
"""
Test script for the ResearcherAgent
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from backend.agents.researcher import ResearcherAgent
from crewai import Crew, Task
from textwrap import dedent

def test_researcher_agent():
    """Test the researcher agent with a simple task"""
    print("🔍 Testing ResearcherAgent...")
    
    # Create the researcher agent
    researcher_agent = ResearcherAgent()
    researcher = researcher_agent.create_agent()
    
    print(f"✅ Agent created: {researcher.role}")
    print(f"📁 Tools available: {[tool.name for tool in researcher.tools]}")
    
    # Create a simple test task
    test_task = Task(
        description=dedent("""
            Test the knowledge base access by:
            1. Using DirectoryReadTool to list files in knowledge directory
            2. Reading one file (01_introduction_en.txt) using FileReadTool
            3. Summarize what you found in a brief report
        """),
        expected_output="A brief summary of the directory contents and the introduction file content",
        agent=researcher,
        output_file="test_research_output.txt"
    )
    
    # Create crew and run the task
    crew = Crew(
        agents=[researcher],
        tasks=[test_task],
        verbose=True
    )
    
    print("\n🚀 Running test task...")
    try:
        result = crew.kickoff()
        print(f"\n✅ Test completed successfully!")
        print(f"📄 Result: {result}")
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_researcher_agent()
    if success:
        print("\n🎉 ResearcherAgent test passed!")
    else:
        print("\n💥 ResearcherAgent test failed!")