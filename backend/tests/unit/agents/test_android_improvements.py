#!/usr/bin/env python3
"""Test script to verify Android testing improvements."""

import asyncio
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from backend.agents.android_testing_agent import AndroidTestingAgent


async def test_improvements():
    """Test the improved Android testing functionality."""
    print("Testing Android Testing Agent Improvements")
    print("=" * 50)
    
    # Initialize the agent
    api_key = os.environ.get("OPENAI_API_KEY", "test-key")
    agent = AndroidTestingAgent(api_key)
    
    # Test 1: Check improved UI dump method
    print("\n1. Testing improved UI dump retrieval...")
    ui_dump = await agent._get_ui_dump()
    
    if ui_dump:
        print(f"✓ UI dump retrieved successfully: {len(ui_dump)} bytes")
    else:
        print("✗ Failed to retrieve UI dump")
        return
    
    # Test 2: Check improved element parsing
    print("\n2. Testing improved element parsing...")
    elements = agent._parse_clickable_elements_improved(ui_dump)
    
    print(f"✓ Found {len(elements)} interactive elements")
    
    # Show details of first 5 elements
    print("\nFirst 5 interactive elements found:")
    for i, elem in enumerate(elements[:5]):
        print(f"\n{i+1}. {elem['class']}")
        print(f"   Position: {elem['center']}")
        print(f"   Size: {elem['size'][0]}x{elem['size'][1]}px")
        print(f"   Text: '{elem['text']}'")
        print(f"   Description: '{elem['content_desc']}'")
        print(f"   ID: '{elem['resource_id']}'")
        print(f"   Clickable: {elem['clickable']}, Enabled: {elem['enabled']}")
    
    # Test 3: Show comparison with old regex method
    print("\n3. Comparing with old regex method...")
    import re
    old_pattern = r'<node[^>]*clickable="true"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*/>'
    old_matches = re.findall(old_pattern, ui_dump)
    print(f"Old regex method: {len(old_matches)} elements")
    print(f"New XML method: {len(elements)} elements")
    print(f"Improvement: {len(elements) - len(old_matches)} more elements detected")
    
    print("\n✓ All tests completed successfully!")


async def main():
    """Main function."""
    # Check if ADB is available
    result = os.system("adb devices > /dev/null 2>&1")
    if result != 0:
        print("Error: ADB not found. Please install Android SDK tools.")
        sys.exit(1)
    
    # Check if a device is connected
    import subprocess
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    if "device" not in result.stdout or len(result.stdout.strip().split('\n')) < 2:
        print("Error: No Android device/emulator connected.")
        print("Please connect a device or start an emulator.")
        sys.exit(1)
    
    await test_improvements()


if __name__ == "__main__":
    asyncio.run(main())