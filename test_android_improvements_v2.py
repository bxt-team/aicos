#!/usr/bin/env python3
"""Test script to verify Android testing improvements."""

import asyncio
import os
import json
from src.agents.android_testing_agent import AndroidTestingAgent


async def test_android_app_improvements():
    """Test the improved Android testing agent."""
    
    # Initialize the agent
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    agent = AndroidTestingAgent(openai_api_key)
    
    # APK path - update this to your test APK
    apk_path = "/path/to/your/test.apk"
    
    print("=" * 60)
    print("Testing Android App Testing Improvements")
    print("=" * 60)
    print(f"APK: {apk_path}")
    print("\nImprovements implemented:")
    print("1. Screenshot captured for every unique screen")
    print("2. Automatic text field filling with sample data")
    print("3. Better screen change detection")
    print("4. Improved navigation tracking")
    print("=" * 60)
    
    # Check if APK exists
    if not os.path.exists(apk_path):
        print(f"\nError: APK file not found at {apk_path}")
        print("Please update the apk_path variable with a valid APK path")
        return
    
    try:
        # Run the test
        print("\nStarting Android app test...")
        result = await agent.test_android_app(apk_path)
        
        if result["success"]:
            print("\n✅ Test completed successfully!")
            
            # Display results
            print(f"\nTest ID: {result['test_id']}")
            print(f"Package: {result['package_name']}")
            
            nav_info = result.get('navigation', {})
            print(f"\nNavigation Results:")
            print(f"  - Screens accessed: {nav_info.get('screens_accessed', 0)}")
            print(f"  - Actions performed: {nav_info.get('actions_performed', 0)}")
            print(f"  - Crashes detected: {nav_info.get('crashes_detected', 0)}")
            
            # List screenshots
            screenshot_dir = agent.screenshot_dir
            test_screenshots = [f for f in os.listdir(screenshot_dir) 
                              if f.startswith(f"{result['test_id']}_") and f.endswith(".png")]
            
            print(f"\nScreenshots captured: {len(test_screenshots)}")
            
            # Group screenshots by type
            screen_shots = [f for f in test_screenshots if "_screen_" in f]
            action_shots = [f for f in test_screenshots if "_action_" in f]
            filled_shots = [f for f in test_screenshots if "_filled_fields" in f]
            
            print(f"  - Unique screens: {len(screen_shots)}")
            print(f"  - Action results: {len(action_shots)}")
            print(f"  - Fields filled: {len(filled_shots)}")
            
            if screen_shots:
                print("\nScreen screenshots:")
                for shot in sorted(screen_shots):
                    print(f"  - {shot}")
            
            # Check if text fields were filled
            if filled_shots:
                print("\n✅ Text fields were automatically filled!")
            else:
                print("\n⚠️  No text fields were found or filled")
            
            # Performance info
            perf = result.get('performance', {}).get('metrics', {})
            if perf:
                print(f"\nPerformance Metrics:")
                print(f"  - Startup time: {perf.get('startup_time_ms', 0)/1000:.2f}s")
                if 'memory_usage_mb' in perf:
                    print(f"  - Memory usage: {perf['memory_usage_mb']:.1f} MB")
                if 'cpu_usage_percent' in perf:
                    print(f"  - CPU usage: {perf['cpu_usage_percent']}%")
            
            # Save detailed results
            results_file = f"android_test_results_{result['test_id']}.json"
            with open(results_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nDetailed results saved to: {results_file}")
            
        else:
            print(f"\n❌ Test failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Android Testing Agent - Improvement Test")
    print("This test verifies:")
    print("1. Screenshots are taken for every unique screen")
    print("2. Text input fields are automatically filled")
    print("3. Better tracking of screens visited")
    print()
    
    asyncio.run(test_android_app_improvements())