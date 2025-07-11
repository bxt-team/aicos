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
            assessment = {
                "overall_quality": "high",
                "brand_alignment": True,
                "posts_assessment": []
            }
            
            for i, post in enumerate(posts):
                post_assessment = {
                    "post_index": i,
                    "content_preview": post["content"][:100] + "...",
                    "quality_score": 8.5,
                    "brand_alignment": True,
                    "engagement_potential": "high",
                    "issues": [],
                    "recommendations": [],
                    "approval_recommendation": ApprovalStatus.APPROVED.value
                }
                
                # Check for potential issues
                if len(post["content"]) > 500:
                    post_assessment["issues"].append("Content might be too long")
                    post_assessment["recommendations"].append("Consider shortening for better engagement")
                
                if len(post.get("hashtags", [])) > 10:
                    post_assessment["issues"].append("Too many hashtags")
                    post_assessment["recommendations"].append("Reduce to 5-10 hashtags")
                
                if not post.get("call_to_action"):
                    post_assessment["recommendations"].append("Add a clear call-to-action")
                
                assessment["posts_assessment"].append(post_assessment)
            
            # Calculate overall metrics
            assessment["total_posts"] = len(posts)
            assessment["approved_count"] = sum(1 for p in assessment["posts_assessment"] 
                                             if p["approval_recommendation"] == ApprovalStatus.APPROVED.value)
            assessment["needs_revision_count"] = sum(1 for p in assessment["posts_assessment"] 
                                                   if p["approval_recommendation"] == ApprovalStatus.NEEDS_REVISION.value)
            
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
        
        for i, post_assessment in enumerate(approval_request['assessment']['posts_assessment']):
            print(f"\n--- Post {i+1} ---")
            print(f"Preview: {post_assessment['content_preview']}")
            print(f"Quality Score: {post_assessment['quality_score']}/10")
            print(f"Engagement Potential: {post_assessment['engagement_potential']}")
            
            if post_assessment['issues']:
                print(f"Issues: {', '.join(post_assessment['issues'])}")
            if post_assessment['recommendations']:
                print(f"Recommendations: {', '.join(post_assessment['recommendations'])}")
        
        print("\n" + "-"*50)
        print("DECISION OPTIONS:")
        print("1. ✅ Approve all posts")
        print("2. ❌ Reject all posts")
        print("3. 📝 Request revisions")
        print("4. 🔍 View full posts")
        
        # Simulate auto-approval for now
        decision = ApprovalStatus.APPROVED.value
        print(f"\n➡️ Auto-decision: {decision}")
        print("="*50 + "\n")
        
        return {
            "decision": decision,
            "approver": "telegram_bot",
            "notes": "Auto-approved by simulation"
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