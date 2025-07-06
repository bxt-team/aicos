#!/usr/bin/env python3
"""
Example usage of the Write and Hashtag Research Agent

This script demonstrates how to use the Write and Hashtag Research Agent
to create Instagram posts with affirmations for the 7 Cycles periods.
"""

import os
import sys
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

from src.agents.write_hashtag_research_agent import WriteHashtagResearchAgent

def main():
    """Main function to demonstrate the agent usage"""
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ ERROR: Please set your OPENAI_API_KEY environment variable")
        print("You can do this by creating a .env file in the project root with:")
        print("OPENAI_API_KEY=your_openai_api_key_here")
        return
    
    print("🌟 Write and Hashtag Research Agent Demo")
    print("=" * 50)
    
    # Initialize the agent
    try:
        agent = WriteHashtagResearchAgent(api_key)
        print("✅ Agent initialized successfully!\n")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Example: Create an Instagram post for different periods
    examples = [
        {
            "affirmation": "Ich strahle Selbstvertrauen und Authentizität aus",
            "period_name": "Image",
            "style": "empowering"
        },
        {
            "affirmation": "Ich begrüße Veränderungen als Chance für mein Wachstum",
            "period_name": "Veränderung", 
            "style": "inspirational"
        },
        {
            "affirmation": "Meine Kreativität fließt frei und inspiriert mich täglich",
            "period_name": "Kreativität",
            "style": "artistic"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"📱 Example {i}: {example['period_name']} Period")
        print(f"💭 Affirmation: {example['affirmation']}")
        print(f"🎨 Style: {example['style']}")
        print("-" * 50)
        
        # Generate the Instagram post
        result = agent.generate_instagram_post(
            affirmation=example['affirmation'],
            period_name=example['period_name'],
            style=example['style']
        )
        
        if result['success']:
            post = result['post']
            
            # Display the generated post
            print(f"🎯 Generated Instagram Post:")
            print(f"🌈 Period Color: {post['period_color']}")
            print(f"⏰ Best Posting Time: {post['optimal_posting_time']}")
            print()
            
            print("📝 POST TEXT:")
            print(post['post_text'])
            print()
            
            print(f"🏷️ HASHTAGS ({len(post['hashtags'])}):")
            hashtag_text = " ".join(post['hashtags'])
            print(hashtag_text)
            print()
            
            print("📞 CALL-TO-ACTION:")
            print(post['call_to_action'])
            print()
            
            print("📈 ENGAGEMENT STRATEGIES:")
            for strategy in post['engagement_strategies']:
                print(f"  • {strategy}")
            print()
            
            print("✅ Post generated successfully!")
            
        else:
            print(f"❌ Failed to generate post: {result.get('error', 'Unknown error')}")
        
        print("=" * 50)
        print()
    
    # Show available periods
    print("📋 Available 7 Cycles Periods:")
    periods = ["Image", "Veränderung", "Energie", "Kreativität", "Erfolg", "Entspannung", "Umsicht"]
    for period in periods:
        print(f"  • {period}")
    
    print("\n🎉 Demo completed!")
    print("\nTo use this agent in your own code:")
    print("1. Initialize: agent = WriteHashtagResearchAgent(your_api_key)")
    print("2. Generate post: result = agent.generate_instagram_post(affirmation, period_name, style)")
    print("3. Access the generated content in result['post']")

if __name__ == "__main__":
    main()