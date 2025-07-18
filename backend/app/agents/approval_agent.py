"""Agent for managing the approval workflow of Threads posts."""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import asyncio
from enum import Enum

from crewai import Agent, Task, Crew
from langchain_community.llms import OpenAI

from .crews.base_crew import BaseCrew
from ..services.supabase_client import SupabaseClient, ThreadsPost

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Enum for approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ApprovalAgent(BaseCrew):
    """Agent that manages the approval workflow for Threads posts."""
    
    def __init__(self, openai_api_key: str, supabase_client: Optional[SupabaseClient] = None):
        """Initialize the Approval Agent."""
        super().__init__()
        
        # Initialize LLM
        self.llm = OpenAI(
            model="gpt-4o-mini",
            openai_api_key=openai_api_key,
            temperature=0.3
        )
        
        # Initialize Supabase client
        self.supabase = supabase_client or SupabaseClient()
        
        # Storage for approval records
        self.storage_dir = os.path.join(os.path.dirname(__file__), "../../static/threads_approvals")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Create agent
        self.agent = self.create_agent("threads_approval", llm=self.llm)
        
        # Simulated approval queue
        self.approval_queue = []
    
    async def request_approval(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Request approval for a batch of posts."""
        try:
            # Create approval task
            task = self.create_task(
                "threads_approval_request",
                self.agent,
                posts=json.dumps(posts, indent=2, ensure_ascii=False)
            )
            
            # Create crew and execute
            crew = self.create_crew(
                "threads_approval_crew",
                agents=[self.agent],
                tasks=[task]
            )
            
            result = crew.kickoff()
            
            # Parse approval assessment
            assessment = self._parse_approval_assessment(result, posts)
            
            # Create approval request
            approval_request = {
                "id": f"approval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "posts": posts,
                "assessment": assessment,
                "requested_at": datetime.now().isoformat(),
                "status": ApprovalStatus.PENDING.value
            }
            
            # Save approval request
            self._save_approval_request(approval_request)
            
            # Add to queue
            self.approval_queue.append(approval_request)
            
            # Update posts in database
            await self._update_posts_status(posts, "approval_requested")
            
            return {
                "success": True,
                "approval_request": approval_request,
                "message": "Approval request created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error requesting approval: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_approval_assessment(self, result: Any, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse the approval assessment from crew result."""
        try:
            # Parse the actual result from the AI agent if it's a string
            if isinstance(result, str):
                # Try to extract JSON from the result
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    try:
                        parsed_result = json.loads(json_match.group())
                        if "assessment" in parsed_result:
                            return parsed_result["assessment"]
                    except json.JSONDecodeError:
                        pass
            
            # If we couldn't parse the AI result, perform manual assessment
            assessment = {
                "overall_quality": "medium",
                "brand_alignment": True,
                "posts_assessment": []
            }
            
            for i, post in enumerate(posts):
                # Calculate quality score based on various factors
                quality_score = 7.0  # Base score
                issues = []
                recommendations = []
                
                # Content length check
                content_length = len(post["content"])
                if content_length < 50:
                    quality_score -= 2
                    issues.append("Content too short")
                    recommendations.append("Add more valuable content (aim for 100-300 characters)")
                elif content_length > 500:
                    quality_score -= 1
                    issues.append("Content might be too long")
                    recommendations.append("Consider shortening for better engagement")
                elif 100 <= content_length <= 300:
                    quality_score += 1  # Optimal length
                
                # Hashtag analysis
                hashtags = post.get("hashtags", [])
                hashtag_count = len(hashtags)
                if hashtag_count == 0:
                    quality_score -= 1
                    issues.append("No hashtags")
                    recommendations.append("Add 3-7 relevant hashtags")
                elif hashtag_count > 10:
                    quality_score -= 1.5
                    issues.append("Too many hashtags")
                    recommendations.append("Reduce to 5-10 hashtags for better reach")
                elif 3 <= hashtag_count <= 7:
                    quality_score += 0.5  # Optimal hashtag count
                
                # Call to action check
                has_cta = bool(post.get("call_to_action"))
                if not has_cta:
                    quality_score -= 0.5
                    recommendations.append("Add a clear call-to-action to drive engagement")
                else:
                    quality_score += 0.5
                
                # Visual prompt check
                has_visual = bool(post.get("visual_prompt"))
                if not has_visual:
                    recommendations.append("Consider adding visual content for higher engagement")
                else:
                    quality_score += 0.5
                
                # Period-specific checks
                period = post.get("period", 0)
                if period > 0:
                    quality_score += 0.5  # Has period context
                
                # Emoji usage (engagement booster)
                import re
                emoji_pattern = re.compile("["
                    u"\U0001F600-\U0001F64F"  # emoticons
                    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                    u"\U0001F680-\U0001F6FF"  # transport & map symbols
                    u"\U0001F1E0-\U0001F1FF"  # flags
                    "]+", flags=re.UNICODE)
                if emoji_pattern.search(post["content"]):
                    quality_score += 0.5
                else:
                    recommendations.append("Consider adding emojis for better engagement")
                
                # Cap the score between 1 and 10
                quality_score = max(1, min(10, quality_score))
                
                # Determine engagement potential based on score
                if quality_score >= 8:
                    engagement_potential = "high"
                elif quality_score >= 6:
                    engagement_potential = "medium"
                else:
                    engagement_potential = "low"
                
                # Determine approval recommendation
                if quality_score >= 7 and len(issues) <= 1:
                    approval_recommendation = ApprovalStatus.APPROVED.value
                elif quality_score >= 5:
                    approval_recommendation = ApprovalStatus.NEEDS_REVISION.value
                else:
                    approval_recommendation = ApprovalStatus.REJECTED.value
                
                post_assessment = {
                    "post_index": i,
                    "content_preview": post["content"][:100] + ("..." if len(post["content"]) > 100 else ""),
                    "quality_score": round(quality_score, 1),
                    "brand_alignment": True,  # Could be enhanced with brand guidelines check
                    "engagement_potential": engagement_potential,
                    "issues": issues,
                    "recommendations": recommendations,
                    "approval_recommendation": approval_recommendation
                }
                
                assessment["posts_assessment"].append(post_assessment)
            
            # Calculate overall metrics
            assessment["total_posts"] = len(posts)
            assessment["approved_count"] = sum(1 for p in assessment["posts_assessment"] 
                                             if p["approval_recommendation"] == ApprovalStatus.APPROVED.value)
            assessment["needs_revision_count"] = sum(1 for p in assessment["posts_assessment"] 
                                                   if p["approval_recommendation"] == ApprovalStatus.NEEDS_REVISION.value)
            assessment["rejected_count"] = sum(1 for p in assessment["posts_assessment"] 
                                             if p["approval_recommendation"] == ApprovalStatus.REJECTED.value)
            
            # Determine overall quality
            avg_score = sum(p["quality_score"] for p in assessment["posts_assessment"]) / len(posts) if posts else 0
            if avg_score >= 8:
                assessment["overall_quality"] = "high"
            elif avg_score >= 6:
                assessment["overall_quality"] = "medium"
            else:
                assessment["overall_quality"] = "low"
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error parsing approval assessment: {str(e)}")
            return {
                "overall_quality": "unknown",
                "posts_assessment": [],
                "error": str(e)
            }
    
    async def process_approval_decision(
        self,
        approval_id: str,
        decision: str,
        approver: str = "system",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process an approval decision."""
        try:
            # Find approval request
            approval_request = None
            for req in self.approval_queue:
                if req["id"] == approval_id:
                    approval_request = req
                    break
            
            if not approval_request:
                return {
                    "success": False,
                    "error": "Approval request not found"
                }
            
            # Update approval status
            approval_request["status"] = decision
            approval_request["approved_by"] = approver
            approval_request["approved_at"] = datetime.now().isoformat()
            approval_request["notes"] = notes
            
            # Update posts based on decision
            if decision == ApprovalStatus.APPROVED.value:
                await self._update_posts_status(approval_request["posts"], "approved")
                message = "Posts approved and ready for scheduling"
            elif decision == ApprovalStatus.REJECTED.value:
                await self._update_posts_status(approval_request["posts"], "rejected")
                message = "Posts rejected"
            else:
                await self._update_posts_status(approval_request["posts"], "needs_revision")
                message = "Posts need revision"
            
            # Save updated approval
            self._save_approval_request(approval_request)
            
            # Remove from queue if final decision
            if decision in [ApprovalStatus.APPROVED.value, ApprovalStatus.REJECTED.value]:
                self.approval_queue.remove(approval_request)
            
            return {
                "success": True,
                "approval_request": approval_request,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error processing approval decision: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests."""
        try:
            # Get from database
            pending_posts = await self.supabase.get_threads_posts(status="approval_requested")
            
            # Group by approval request
            grouped_approvals = []
            
            # Return current queue
            return [req for req in self.approval_queue if req["status"] == ApprovalStatus.PENDING.value]
            
        except Exception as e:
            logger.error(f"Error getting pending approvals: {str(e)}")
            return []
    
    def simulate_telegram_approval(self, approval_request: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate Telegram bot approval interface."""
        print("\n" + "="*50)
        print("🤖 TELEGRAM APPROVAL BOT")
        print("="*50)
        print(f"\nApproval Request: {approval_request['id']}")
        print(f"Total Posts: {approval_request['assessment']['total_posts']}")
        print(f"Requested at: {approval_request['requested_at']}")
        print(f"Overall Quality: {approval_request['assessment']['overall_quality']}")
        
        # Count recommendations by status
        approved = approval_request['assessment'].get('approved_count', 0)
        needs_revision = approval_request['assessment'].get('needs_revision_count', 0)
        rejected = approval_request['assessment'].get('rejected_count', 0)
        
        print(f"\nAssessment Summary:")
        print(f"✅ Approved: {approved}")
        print(f"📝 Needs Revision: {needs_revision}")
        print(f"❌ Rejected: {rejected}")
        
        for i, post_assessment in enumerate(approval_request['assessment']['posts_assessment']):
            print(f"\n--- Post {i+1} ---")
            print(f"Preview: {post_assessment['content_preview']}")
            print(f"Quality Score: {post_assessment['quality_score']}/10")
            print(f"Engagement Potential: {post_assessment['engagement_potential']}")
            print(f"Recommendation: {post_assessment['approval_recommendation']}")
            
            if post_assessment['issues']:
                print(f"⚠️ Issues: {', '.join(post_assessment['issues'])}")
            if post_assessment['recommendations']:
                print(f"💡 Recommendations: {', '.join(post_assessment['recommendations'])}")
        
        print("\n" + "-"*50)
        print("DECISION OPTIONS:")
        print("1. ✅ Approve all posts")
        print("2. ❌ Reject all posts")
        print("3. 📝 Request revisions")
        print("4. 🔍 View full posts")
        
        # Make intelligent decision based on assessment
        overall_quality = approval_request['assessment']['overall_quality']
        avg_score = sum(p['quality_score'] for p in approval_request['assessment']['posts_assessment']) / len(approval_request['assessment']['posts_assessment'])
        
        # Decision logic based on quality scores
        if overall_quality == "high" and approved > needs_revision + rejected:
            decision = ApprovalStatus.APPROVED.value
            notes = f"High quality posts with average score {avg_score:.1f}/10. All posts meet quality standards."
        elif needs_revision > approved + rejected:
            decision = ApprovalStatus.NEEDS_REVISION.value
            notes = f"Most posts need revision. Average score {avg_score:.1f}/10. Please address the recommendations."
        elif rejected > approved + needs_revision:
            decision = ApprovalStatus.REJECTED.value
            notes = f"Posts don't meet quality standards. Average score {avg_score:.1f}/10. Please regenerate with better content."
        else:
            # Mixed results - approve if average is good
            if avg_score >= 6.5:
                decision = ApprovalStatus.APPROVED.value
                notes = f"Mixed quality but acceptable overall. Average score {avg_score:.1f}/10."
            else:
                decision = ApprovalStatus.NEEDS_REVISION.value
                notes = f"Posts need improvement. Average score {avg_score:.1f}/10. Please revise based on recommendations."
        
        print(f"\n➡️ Bot Decision: {decision}")
        print(f"📋 Notes: {notes}")
        print("="*50 + "\n")
        
        return {
            "decision": decision,
            "approver": "telegram_bot",
            "notes": notes,
            "assessment_summary": {
                "overall_quality": overall_quality,
                "average_score": round(avg_score, 1),
                "approved_posts": approved,
                "revision_needed": needs_revision,
                "rejected_posts": rejected
            }
        }
    
    async def _update_posts_status(self, posts: List[Dict[str, Any]], status: str):
        """Update posts status in database."""
        try:
            # In real implementation, we would update each post in Supabase
            logger.info(f"Updating {len(posts)} posts to status: {status}")
            
            # Mock update for now
            for post in posts:
                if "id" in post:
                    await self.supabase.update_threads_post(
                        post["id"],
                        {
                            "status": status,
                            "updated_at": datetime.now().isoformat()
                        }
                    )
        except Exception as e:
            logger.error(f"Error updating posts status: {str(e)}")
    
    def _save_approval_request(self, approval_request: Dict[str, Any]):
        """Save approval request to storage."""
        filename = f"{approval_request['id']}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(approval_request, f, indent=2, ensure_ascii=False)
    
    def get_approval_history(self) -> List[Dict[str, Any]]:
        """Get approval history."""
        history = []
        
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.storage_dir, filename)
                    with open(filepath, 'r') as f:
                        history.append(json.load(f))
            
            # Sort by date
            history.sort(key=lambda x: x.get('requested_at', ''), reverse=True)
            
        except Exception as e:
            logger.error(f"Error loading approval history: {str(e)}")
        
        return history
    
    def health_check(self) -> Dict[str, Any]:
        """Check agent health status."""
        return {
            "status": "healthy",
            "agent": "ApprovalAgent",
            "storage_available": os.path.exists(self.storage_dir),
            "pending_approvals": len([req for req in self.approval_queue if req["status"] == ApprovalStatus.PENDING.value]),
            "total_in_queue": len(self.approval_queue),
            "supabase_connected": self.supabase.client is not None
        }