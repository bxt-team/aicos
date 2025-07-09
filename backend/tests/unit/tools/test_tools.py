#!/usr/bin/env python3
"""
Simple test to check if the researcher tools can access knowledge files
"""
from crewai_tools import DirectoryReadTool, FileReadTool

def test_tools():
    print("🔧 Testing ResearcherAgent Tools...")
    
    # Test DirectoryReadTool
    print("\n1. Testing DirectoryReadTool...")
    directory_tool = DirectoryReadTool(directory='knowledge/')
    try:
        files = directory_tool.run()
        print(f"✅ Directory tool works! Found files:")
        print(files)
    except Exception as e:
        print(f"❌ Directory tool failed: {e}")
        return False
    
    # Test FileReadTool  
    print("\n2. Testing FileReadTool...")
    file_tool = FileReadTool()
    try:
        content = file_tool.run("knowledge/01_introduction_en.txt")
        print(f"✅ File tool works! Content preview:")
        print(content[:200] + "..." if len(content) > 200 else content)
    except Exception as e:
        print(f"❌ File tool failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_tools()
    if success:
        print("\n🎉 All tools working correctly!")
        print("The researcher agent should now be able to access knowledge files.")
    else:
        print("\n💥 Tool test failed!")