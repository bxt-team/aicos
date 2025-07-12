from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from pathlib import Path
import uuid

from app.agents.crews.base_crew import BaseCrew
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI


class XApprovalAgent(BaseCrew):
    """Agent for reviewing and approving X (Twitter) posts."""
    
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3  # Lower temperature for consistent quality checks
        )
        self.results_path = Path("storage/x_approvals")
        self.results_path.mkdir(parents=True, exist_ok=True)
        self.pending_approvals = []
        self.approval_history = []
    
    def create_crew(self) -> Crew:
        """Create the X approval crew."""
        quality_reviewer = Agent(
            role="X (Twitter) Content Quality Reviewer",
            goal="Ensure all X posts meet quality standards, brand guidelines, and platform best practices",
            backstory="""You are an experienced X/Twitter content reviewer with a keen eye for 
            quality, brand consistency, and platform optimization. You understand what makes tweets 
            successful and can spot potential issues before they go live. You're well-versed in 
            X's community guidelines, best practices for engagement, and the nuances of the 7 Cycles 
            brand voice. You balance being thorough with being efficient, ensuring content is both 
            high-quality and timely. You can identify potential PR issues, ensure factual accuracy, 
            and optimize content for maximum impact while maintaining authenticity.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        return Crew(
            agents=[quality_reviewer],
            tasks=[],
            verbose=True
        )
    
    def submit_for_approval(self, posts: List[Dict[str, Any]], requester: str = "system") -> Dict[str, Any]:
        """Submit posts for approval review."""
        
        approval_request = {
            "id": str(uuid.uuid4()),
            "submitted_at": datetime.now().isoformat(),
            "requester": requester,
            "posts": posts,
            "status": "pending",
            "review_results": []
        }
        
        # Create review task
        review_task = Task(
            description=f"""Review the following X/Twitter posts for quality, compliance, and effectiveness.
            
            Posts to review:
            {json.dumps(posts, indent=2)}
            
            For each post, evaluate:
            
            1. Content Quality:
               - Grammar and spelling accuracy
               - Clarity and coherence
               - Character count optimization
               - Hook effectiveness
               - CTA strength
            
            2. Brand Alignment:
               - Consistency with 7 Cycles voice
               - Appropriate tone for the period
               - Authentic and relatable messaging
               - Proper representation of methodology
            
            3. Platform Optimization:
               - Hashtag relevance and count (2-3 optimal)
               - Formatting for readability
               - Thread structure (if applicable)
               - Visual suggestions appropriateness
               - Timing recommendations
            
            4. Engagement Potential:
               - Likelihood to spark conversation
               - Shareability factor
               - Save-worthy content
               - Viral potential indicators
            
            5. Compliance Check:
               - X community guidelines adherence
               - No misleading information
               - Appropriate for all audiences
               - No potential PR issues
            
            6. Technical Aspects:
               - Character count within limits
               - Proper thread numbering
               - Poll options clarity (if applicable)
               - Link formatting (if any)
            
            For each post provide:
            - Approval status (approved/needs_revision/rejected)
            - Quality score (1-10)
            - Specific feedback
            - Suggested improvements (if needed)
            - Risk assessment (low/medium/high)
            
            Be constructive in feedback while maintaining high standards.""",
            expected_output="Detailed review results for each post with actionable feedback",
            agent=self.crew.agents[0]
        )
        
        # Execute review
        self.crew.tasks = [review_task]
        result = self.crew.kickoff()
        
        # Process review results
        review_results = []
        for i, post in enumerate(posts):
            review_result = {
                "post_index": i,
                "post_content": post.get("content", ""),
                "post_type": post.get("type", "single"),
                "approval_status": "approved" if i % 3 != 2 else "needs_revision",  # Mock logic
                "quality_score": 8.5 - (i * 0.5),  # Mock decreasing scores
                "feedback": self._generate_feedback(post),
                "suggestions": self._generate_suggestions(post),
                "risk_level": "low" if i < 2 else "medium",
                "reviewed_at": datetime.now().isoformat()
            }
            review_results.append(review_result)
        
        approval_request["review_results"] = review_results
        approval_request["ai_review"] = str(result)
        approval_request["status"] = "reviewed"
        
        # Save to pending if any need revision
        if any(r["approval_status"] != "approved" for r in review_results):
            self.pending_approvals.append(approval_request)
        
        # Save approval request
        filename = f"x_approval_{approval_request['id']}.json"
        filepath = self.results_path / filename
        with open(filepath, 'w') as f:
            json.dump(approval_request, f, indent=2)
        
        return approval_request
    
    def _generate_feedback(self, post: Dict[str, Any]) -> str:
        """Generate specific feedback for a post."""
        feedback_templates = [
            "Strong hook and clear CTA. Well-optimized for engagement.",
            "Good use of the period theme. Consider adding more specific examples.",
            "Hashtags are relevant but could be more specific to increase reach.",
            "Thread structure is logical. Each tweet builds effectively on the previous.",
            "Poll options could be more balanced to encourage broader participation.",
            "Visual suggestion aligns well with content. Very shareable.",
            "Consider shortening for more impact. Some redundancy in message.",
            "Excellent emotional connection. This will resonate with the audience."
        ]
        
        # Return feedback based on post type
        if post.get("type") == "thread":
            return "Thread structure is well-organized. Strong narrative flow from opener to CTA."
        elif post.get("type") == "poll":
            return "Poll question is engaging. Options cover good range of responses."
        else:
            return feedback_templates[hash(post.get("content", "")) % len(feedback_templates)]
    
    def _generate_suggestions(self, post: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions for a post."""
        suggestions = []
        
        content = post.get("content", "")
        if len(content) > 250:
            suggestions.append("Consider shortening to leave room for engagement")
        
        hashtags = post.get("hashtags", [])
        if len(hashtags) > 3:
            suggestions.append("Reduce hashtags to 2-3 for optimal reach")
        elif len(hashtags) < 2:
            suggestions.append("Add 1-2 more relevant hashtags")
        
        if post.get("type") == "thread" and "thread_content" in post:
            if len(post["thread_content"]) > 7:
                suggestions.append("Consider breaking into two separate threads")
        
        if not any(char in content for char in ["?", "!", "🤔", "👇", "💭"]):
            suggestions.append("Add engagement prompt or question to encourage replies")
        
        return suggestions if suggestions else ["No improvements needed - ready to publish!"]
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests."""
        return [req for req in self.pending_approvals if req["status"] == "pending"]
    
    def process_approval_decision(self, approval_id: str, decisions: Dict[int, str]) -> Dict[str, Any]:
        """Process approval decisions for posts."""
        
        # Find the approval request
        approval_request = None
        for req in self.pending_approvals:
            if req["id"] == approval_id:
                approval_request = req
                break
        
        if not approval_request:
            return {"error": "Approval request not found"}
        
        # Update decisions
        for post_index, decision in decisions.items():
            if 0 <= post_index < len(approval_request["review_results"]):
                approval_request["review_results"][post_index]["final_decision"] = decision
                approval_request["review_results"][post_index]["decided_at"] = datetime.now().isoformat()
        
        # Update status
        all_approved = all(
            result.get("final_decision") == "approved" or result["approval_status"] == "approved"
            for result in approval_request["review_results"]
        )
        
        approval_request["status"] = "approved" if all_approved else "partially_approved"
        
        # Move to history
        self.approval_history.append(approval_request)
        self.pending_approvals.remove(approval_request)
        
        # Save updated request
        filename = f"x_approval_{approval_request['id']}_final.json"
        filepath = self.results_path / filename
        with open(filepath, 'w') as f:
            json.dump(approval_request, f, indent=2)
        
        return approval_request
    
    def get_approval_history(self) -> List[Dict[str, Any]]:
        """Get approval history."""
        return self.approval_history
    
    def simulate_telegram_approval(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulate Telegram bot approval process."""
        
        # Create Telegram-style message
        telegram_message = {
            "chat_id": "@sevencylesapproval",
            "message_type": "approval_request",
            "timestamp": datetime.now().isoformat(),
            "posts_count": len(posts),
            "preview": []
        }
        
        for i, post in enumerate(posts[:3]):  # Show first 3 posts
            preview = {
                "index": i + 1,
                "type": post.get("type", "single"),
                "preview": post.get("content", "")[:100] + "...",
                "period": post.get("period", "Unknown"),
                "quality_score": 8.5 - (i * 0.5)
            }
            telegram_message["preview"].append(preview)
        
        # Simulate bot response
        bot_response = {
            "approved_count": len(posts) - 1,
            "revision_needed": 1,
            "response_time": "2.3 seconds",
            "bot_message": "I've reviewed the posts. Most look great! One needs minor revision for better engagement.",
            "detailed_feedback": self.submit_for_approval(posts, "telegram_bot")
        }
        
        return {
            "telegram_request": telegram_message,
            "bot_response": bot_response
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the X approval agent is functioning properly."""
        try:
            # Test LLM connection
            test_response = self.llm.invoke("Test X approval agent connection")
            
            return {
                "status": "healthy",
                "agent": "XApprovalAgent",
                "llm_connected": bool(test_response),
                "storage_accessible": self.results_path.exists(),
                "pending_approvals": len(self.pending_approvals),
                "approval_history": len(self.approval_history)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent": "XApprovalAgent",
                "error": str(e)
            }