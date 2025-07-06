#!/usr/bin/env python3
"""
Test script to verify YAML-based CrewAI configuration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_yaml_loading():
    """Test loading YAML configurations"""
    try:
        from src.crews.base_crew import BaseCrew
        
        print("✓ Testing YAML configuration loading...")
        crew = BaseCrew()
        
        # Test agents config
        print(f"✓ Loaded {len(crew.agents_config)} agent configurations:")
        for agent_name in crew.agents_config.keys():
            print(f"  - {agent_name}")
        
        # Test tasks config
        print(f"✓ Loaded {len(crew.tasks_config)} task configurations:")
        for task_name in crew.tasks_config.keys():
            print(f"  - {task_name}")
        
        # Test crews config
        print(f"✓ Loaded {len(crew.crews_config)} crew configurations:")
        for crew_name in crew.crews_config.keys():
            print(f"  - {crew_name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error loading YAML configurations: {e}")
        return False

def test_qa_agent():
    """Test QA agent creation with YAML config"""
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("✗ OPENAI_API_KEY not found in environment variables")
            return False
        
        print("✓ Testing QA Agent with YAML configuration...")
        from src.agents.qa_agent import QAAgent
        
        qa_agent = QAAgent(openai_api_key)
        print("✓ QA Agent created successfully")
        
        # Test knowledge overview (quick test)
        print("✓ Testing knowledge overview...")
        result = qa_agent.get_knowledge_overview()
        if result["success"]:
            print("✓ Knowledge overview generated successfully")
            print(f"  Overview length: {len(result['overview'])} characters")
        else:
            print(f"✗ Knowledge overview failed: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing QA Agent: {e}")
        return False

def test_affirmations_agent():
    """Test Affirmations agent creation with YAML config"""
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("✗ OPENAI_API_KEY not found in environment variables")
            return False
        
        print("✓ Testing Affirmations Agent with YAML configuration...")
        from src.agents.affirmations_agent import AffirmationsAgent
        
        affirmations_agent = AffirmationsAgent(openai_api_key)
        print("✓ Affirmations Agent created successfully")
        
        # Test available periods
        print("✓ Testing available periods...")
        periods = affirmations_agent.get_available_periods()
        if periods["success"]:
            print(f"✓ Found {len(periods['period_types'])} period types")
            for period_type in periods["period_types"].keys():
                print(f"  - {period_type}")
        else:
            print("✗ Failed to get available periods")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing Affirmations Agent: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing YAML-based CrewAI Configuration")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: YAML loading
    if test_yaml_loading():
        tests_passed += 1
    print()
    
    # Test 2: QA Agent
    if test_qa_agent():
        tests_passed += 1
    print()
    
    # Test 3: Affirmations Agent
    if test_affirmations_agent():
        tests_passed += 1
    print()
    
    # Summary
    print("=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! YAML configuration is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)