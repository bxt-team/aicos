#!/usr/bin/env python3
"""
Test script for Instagram Analyzer Agent

This script tests the Instagram analyzer functionality including:
1. Account analysis
2. Strategy generation
3. Multiple account comparison
4. Data persistence

Usage:
python test_instagram_analyzer.py
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.agents.instagram_analyzer_agent import InstagramAnalyzerAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class InstagramAnalyzerTester:
    def __init__(self):
        """Initialize the tester with OpenAI API key"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.analyzer = InstagramAnalyzerAgent(self.openai_api_key)
        
        # Test accounts for analysis
        self.test_accounts = [
            "@garyvee",  # Business/Entrepreneurship
            "@thefitnesschef_",  # Fitness/Wellness
            "@mindfullyblonde",  # Wellness/Lifestyle
            "@7cyclesapp"  # Our target niche
        ]
        
        print("🚀 Instagram Analyzer Tester initialized")
        print(f"🔑 OpenAI API Key: {'✅ Set' if self.openai_api_key else '❌ Missing'}")
        print(f"🎯 Test accounts ready: {len(self.test_accounts)}")

    def print_section(self, title: str):
        """Print a formatted section header"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print('='*60)

    def print_result(self, success: bool, message: str, details: Dict[str, Any] = None):
        """Print formatted test result"""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {message}")
        
        if details:
            print("📋 Details:")
            for key, value in details.items():
                if isinstance(value, (dict, list)):
                    print(f"  {key}: {json.dumps(value, indent=2)[:200]}...")
                else:
                    print(f"  {key}: {value}")

    async def test_single_account_analysis(self):
        """Test analyzing a single Instagram account"""
        self.print_section("Single Account Analysis Test")
        
        test_account = self.test_accounts[0]  # @garyvee
        print(f"🎯 Testing account: {test_account}")
        
        try:
            result = self.analyzer.analyze_instagram_account(
                account_url_or_username=test_account,
                analysis_focus="comprehensive"
            )
            
            if result["success"]:
                analysis = result["analysis"]
                details = {
                    "account": analysis.get("account_username"),
                    "analysis_id": analysis.get("analysis_id"),
                    "focus": analysis.get("analysis_focus"),
                    "source": result.get("source"),
                    "content_types": analysis.get("content_analysis", {}).get("primary_content_types"),
                    "success_level": analysis.get("overall_assessment", {}).get("success_level")
                }
                self.print_result(True, f"Successfully analyzed {test_account}", details)
                return analysis.get("analysis_id")
            else:
                self.print_result(False, f"Failed to analyze {test_account}", {"error": result["error"]})
                return None
                
        except Exception as e:
            self.print_result(False, f"Exception during analysis", {"error": str(e)})
            return None

    async def test_strategy_generation(self, analysis_id: str):
        """Test generating strategy from analysis"""
        self.print_section("Strategy Generation Test")
        
        if not analysis_id:
            print("⚠️ Skipping strategy test - no analysis ID available")
            return None
        
        print(f"🎯 Generating strategy from analysis: {analysis_id}")
        
        try:
            result = self.analyzer.generate_strategy_from_analysis(
                analysis_id=analysis_id,
                target_niche="7cycles",
                account_stage="starting"
            )
            
            if result["success"]:
                strategy = result["strategy"]
                details = {
                    "strategy_id": strategy.get("strategy_id"),
                    "target_niche": strategy.get("target_niche"),
                    "account_stage": strategy.get("account_stage"),
                    "analyzed_account": strategy.get("analyzed_account"),
                    "content_types": strategy.get("content_strategy", {}).get("primary_content_types"),
                    "posting_frequency": strategy.get("posting_strategy", {}).get("recommended_frequency")
                }
                self.print_result(True, "Successfully generated strategy", details)
                return strategy.get("strategy_id")
            else:
                self.print_result(False, "Failed to generate strategy", {"error": result["error"]})
                return None
                
        except Exception as e:
            self.print_result(False, "Exception during strategy generation", {"error": str(e)})
            return None

    async def test_multiple_account_analysis(self):
        """Test analyzing multiple accounts for comparison"""
        self.print_section("Multiple Account Analysis Test")
        
        test_accounts = self.test_accounts[:3]  # Use first 3 accounts
        print(f"🎯 Testing comparative analysis of: {', '.join(test_accounts)}")
        
        try:
            result = self.analyzer.analyze_multiple_accounts(
                account_list=test_accounts,
                analysis_focus="comprehensive"
            )
            
            if result["success"]:
                comparative = result["comparative_analysis"]
                details = {
                    "analysis_id": comparative.get("comparative_analysis_id"),
                    "account_count": len(comparative.get("analyzed_accounts", [])),
                    "analyzed_accounts": comparative.get("analyzed_accounts"),
                    "failed_count": result.get("failed_count", 0),
                    "universal_strategies": comparative.get("common_success_factors", {}).get("universal_strategies"),
                    "best_practices": list(comparative.get("identified_best_practices", {}).keys())
                }
                self.print_result(True, f"Successfully compared {len(test_accounts)} accounts", details)
                return comparative.get("comparative_analysis_id")
            else:
                self.print_result(False, "Failed comparative analysis", {"error": result["error"]})
                return None
                
        except Exception as e:
            self.print_result(False, "Exception during comparative analysis", {"error": str(e)})
            return None

    async def test_data_persistence(self):
        """Test data storage and retrieval"""
        self.print_section("Data Persistence Test")
        
        try:
            # Test getting stored analyses
            result = self.analyzer.get_stored_analyses()
            
            if result["success"]:
                details = {
                    "total_analyses": len(result["analyses"]),
                    "total_strategies": len(result["strategies"]),
                    "recent_analyses": [a.get("account_username") for a in result["analyses"][-3:]],
                    "recent_strategies": [s.get("target_niche") for s in result["strategies"][-3:]]
                }
                self.print_result(True, "Successfully retrieved stored data", details)
                
                # Test specific strategy retrieval if we have any
                if result["strategies"]:
                    strategy_id = result["strategies"][-1].get("strategy_id")
                    strategy_result = self.analyzer.get_strategy_by_id(strategy_id)
                    
                    if strategy_result["success"]:
                        self.print_result(True, f"Successfully retrieved specific strategy", 
                                        {"strategy_id": strategy_id})
                    else:
                        self.print_result(False, "Failed to retrieve specific strategy", 
                                        {"error": strategy_result["error"]})
            else:
                self.print_result(False, "Failed to retrieve stored data", {"error": result["error"]})
                
        except Exception as e:
            self.print_result(False, "Exception during data persistence test", {"error": str(e)})

    async def test_error_handling(self):
        """Test error handling with invalid inputs"""
        self.print_section("Error Handling Test")
        
        # Test invalid account
        print("🎯 Testing invalid account analysis...")
        try:
            result = self.analyzer.analyze_instagram_account("")
            expected_failure = not result["success"]
            self.print_result(expected_failure, 
                            "Invalid account properly rejected" if expected_failure else "Invalid account incorrectly accepted",
                            {"error": result.get("error")})
        except Exception as e:
            self.print_result(True, "Exception properly caught for invalid account", {"error": str(e)})

        # Test invalid strategy generation
        print("🎯 Testing invalid strategy generation...")
        try:
            result = self.analyzer.generate_strategy_from_analysis("invalid_id")
            expected_failure = not result["success"]
            self.print_result(expected_failure,
                            "Invalid analysis ID properly rejected" if expected_failure else "Invalid analysis ID incorrectly accepted",
                            {"error": result.get("error")})
        except Exception as e:
            self.print_result(True, "Exception properly caught for invalid strategy", {"error": str(e)})

    async def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🧪 Starting Comprehensive Instagram Analyzer Tests")
        print(f"⏰ Test started at: {datetime.now().isoformat()}")
        
        # Test 1: Single account analysis
        analysis_id = await self.test_single_account_analysis()
        
        # Test 2: Strategy generation (depends on test 1)
        strategy_id = await self.test_strategy_generation(analysis_id)
        
        # Test 3: Multiple account analysis
        comparative_id = await self.test_multiple_account_analysis()
        
        # Test 4: Data persistence
        await self.test_data_persistence()
        
        # Test 5: Error handling
        await self.test_error_handling()
        
        # Summary
        self.print_section("Test Summary")
        print(f"✅ Single Analysis ID: {analysis_id or 'Failed'}")
        print(f"✅ Strategy ID: {strategy_id or 'Failed'}")
        print(f"✅ Comparative Analysis ID: {comparative_id or 'Failed'}")
        print(f"⏰ Test completed at: {datetime.now().isoformat()}")
        print("\n🎉 Instagram Analyzer testing completed!")

async def main():
    """Main test function"""
    try:
        tester = InstagramAnalyzerTester()
        await tester.run_comprehensive_test()
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())