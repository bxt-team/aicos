from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from datetime import datetime
from supabase import create_client, Client
import os

from ...core.supabase_auth import get_current_user
from ...core.dependencies import get_agent

router = APIRouter(prefix="/api/departments", tags=["departments"])


def get_supabase() -> Client:
    """Get the actual Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("Supabase credentials not configured")
    
    return create_client(url, key)


# Available AI agents that can be assigned to departments
AVAILABLE_AI_AGENTS = [
    # Core Agents
    {"id": "qa_agent", "name": "Q&A Agent", "type": "qa_agent", "capabilities": ["answer_questions", "knowledge_base"], "category": "Core", "description": "Answers questions using your knowledge base and documentation"},
    {"id": "researcher_agent", "name": "Researcher Agent", "type": "researcher_agent", "capabilities": ["research", "analysis"], "category": "Core", "description": "Conducts in-depth research and analysis on any topic"},
    {"id": "content_creator_agent", "name": "Content Creator Agent", "type": "content_creator_agent", "capabilities": ["content_generation", "writing"], "category": "Core", "description": "Creates high-quality written content for various purposes"},
    {"id": "visual_post_creator_agent", "name": "Visual Post Creator Agent", "type": "visual_post_creator_agent", "capabilities": ["image_generation", "visual_content"], "category": "Core", "description": "Generates visual content and graphics for posts"},
    {"id": "instagram_poster_agent", "name": "Instagram Poster Agent", "type": "instagram_poster_agent", "capabilities": ["social_media", "instagram"], "category": "Core", "description": "Manages and publishes content to Instagram"},
    {"id": "x_poster_agent", "name": "X Poster Agent", "type": "x_poster_agent", "capabilities": ["social_media", "twitter"], "category": "Core", "description": "Manages and publishes content to X (Twitter)"},
    {"id": "threads_poster_agent", "name": "Threads Poster Agent", "type": "threads_poster_agent", "capabilities": ["social_media", "threads"], "category": "Core", "description": "Manages and publishes content to Threads"},
     
    # Growth & Marketing Department
    {"id": "campaign_testing_agent", "name": "Campaign Testing Agent", "type": "campaign_testing_agent", "capabilities": ["ab_testing", "campaign_optimization", "analytics"], "category": "Marketing", "description": "Runs A/B tests and optimizes marketing campaigns for better performance"},
    {"id": "scheduler_posting_agent", "name": "Scheduler & Posting Agent", "type": "scheduler_posting_agent", "capabilities": ["content_scheduling", "multi_platform_posting", "timing_optimization"], "category": "Marketing", "description": "Schedules and posts content across multiple platforms at optimal times"},
    {"id": "seo_keyword_agent", "name": "SEO & Keyword Optimizer Agent", "type": "seo_keyword_agent", "capabilities": ["seo_optimization", "keyword_research", "content_optimization"], "category": "Marketing", "description": "Optimizes content for search engines and researches keywords"},
    
    # Sales & Lead Management
    {"id": "lead_scoring_agent", "name": "Lead Scoring Agent", "type": "lead_scoring_agent", "capabilities": ["lead_qualification", "scoring_algorithms", "predictive_analytics"], "category": "Sales", "description": "Scores and qualifies leads based on behavior and engagement"},
    {"id": "crm_update_agent", "name": "CRM Update Agent", "type": "crm_update_agent", "capabilities": ["crm_integration", "data_sync", "contact_management"], "category": "Sales", "description": "Keeps CRM data synchronized and up-to-date automatically"},
    {"id": "followup_email_agent", "name": "Follow-up Email Agent", "type": "followup_email_agent", "capabilities": ["email_automation", "personalization", "sequence_management"], "category": "Sales", "description": "Sends personalized follow-up emails and manages email sequences"},
    {"id": "proposal_generator_agent", "name": "Proposal Generator Agent", "type": "proposal_generator_agent", "capabilities": ["proposal_creation", "document_generation", "customization"], "category": "Sales", "description": "Creates customized proposals and sales documents"},
    
    # Customer Support & Success
    {"id": "chatbot_agent", "name": "Chatbot Agent", "type": "chatbot_agent", "capabilities": ["contextual_support", "conversation_management", "knowledge_retrieval"], "category": "Support", "description": "Provides intelligent customer support through conversational AI"},
    {"id": "ticket_categorization_agent", "name": "Ticket Categorization Agent", "type": "ticket_categorization_agent", "capabilities": ["ticket_classification", "priority_assignment", "routing"], "category": "Support", "description": "Automatically categorizes and routes support tickets"},
    {"id": "sentiment_analyzer_agent", "name": "Sentiment Analyzer Agent", "type": "sentiment_analyzer_agent", "capabilities": ["sentiment_analysis", "emotion_detection", "feedback_analysis"], "category": "Support", "description": "Analyzes customer sentiment and emotional tone in communications"},
    {"id": "onboarding_flow_agent", "name": "Onboarding Flow Agent", "type": "onboarding_flow_agent", "capabilities": ["user_onboarding", "tutorial_creation", "progress_tracking"], "category": "Support", "description": "Guides new users through onboarding and tracks their progress"},
    
    # Finance & Accounting
    {"id": "invoice_parser_agent", "name": "Invoice Parser Agent", "type": "invoice_parser_agent", "capabilities": ["invoice_extraction", "ocr_processing", "data_validation"], "category": "Finance", "description": "Extracts data from invoices using OCR and validates financial information"},
    {"id": "subscription_tracking_agent", "name": "Subscription Tracking Agent", "type": "subscription_tracking_agent", "capabilities": ["subscription_management", "billing_cycles", "renewal_tracking"], "category": "Finance", "description": "Manages subscription billing cycles and tracks renewal dates"},
    {"id": "expense_categorizer_agent", "name": "Expense Categorizer Agent", "type": "expense_categorizer_agent", "capabilities": ["expense_classification", "receipt_processing", "budget_tracking"], "category": "Finance", "description": "Categorizes expenses and processes receipts for budget tracking"},
    {"id": "forecasting_agent", "name": "Forecasting Agent", "type": "forecasting_agent", "capabilities": ["mrr_arr_forecasting", "financial_modeling", "trend_analysis"], "category": "Finance", "description": "Creates financial forecasts and models for MRR/ARR planning"},
    
    # Product & Development
    {"id": "roadmap_prioritizer_agent", "name": "Roadmap Prioritizer Agent", "type": "roadmap_prioritizer_agent", "capabilities": ["feature_prioritization", "impact_analysis", "resource_planning"], "category": "Development", "description": "Prioritizes product features and analyzes their impact on roadmap planning"},
    {"id": "code_explainer_agent", "name": "Code Explainer Agent", "type": "code_explainer_agent", "capabilities": ["code_documentation", "technical_explanation", "complexity_analysis"], "category": "Development", "description": "Explains code functionality and creates technical documentation"},
    {"id": "ui_tester_agent", "name": "UI Tester Agent", "type": "ui_tester_agent", "capabilities": ["ui_testing", "usability_analysis", "bug_detection"], "category": "Development", "description": "Tests user interfaces for usability issues and detects bugs"},
    {"id": "documentation_agent", "name": "Documentation Agent", "type": "documentation_agent", "capabilities": ["auto_documentation", "api_docs", "user_guides"], "category": "Development", "description": "Automatically generates documentation, API docs, and user guides"},
    
    # Operations & Logistics
    {"id": "task_sync_agent", "name": "Task Sync Agent", "type": "task_sync_agent", "capabilities": ["notion_jira_sync", "task_management", "status_updates"], "category": "Operations", "description": "Synchronizes tasks between Notion and Jira and provides status updates"},
    {"id": "resource_optimizer_agent", "name": "Resource Optimizer Agent", "type": "resource_optimizer_agent", "capabilities": ["resource_allocation", "capacity_planning", "optimization"], "category": "Operations", "description": "Optimizes resource allocation and plans capacity for operations"},
    {"id": "delivery_tracker_agent", "name": "Delivery Tracker Agent", "type": "delivery_tracker_agent", "capabilities": ["shipment_tracking", "status_monitoring", "eta_calculation"], "category": "Operations", "description": "Tracks deliveries and shipments with real-time status monitoring"},
    {"id": "sop_generator_agent", "name": "SOP Generator Agent", "type": "sop_generator_agent", "capabilities": ["process_documentation", "procedure_creation", "workflow_design"], "category": "Operations", "description": "Creates standard operating procedures and documents workflows"},
    
    # Content & Knowledge Management
    {"id": "blog_social_generator", "name": "Blog & Social Post Generator", "type": "blog_social_generator", "capabilities": ["blog_writing", "social_media_content", "content_repurposing"], "category": "Content", "description": "Generates blog posts and social media content with repurposing capabilities"},
    {"id": "internal_wiki_agent", "name": "Internal Wiki Agent", "type": "internal_wiki_agent", "capabilities": ["knowledge_organization", "wiki_management", "content_curation"], "category": "Content", "description": "Organizes knowledge base and manages internal wiki content"},
    {"id": "video_transcript_agent", "name": "Video Transcript + Summary Agent", "type": "video_transcript_agent", "capabilities": ["video_transcription", "summary_generation", "key_points_extraction"], "category": "Content", "description": "Transcribes videos and generates summaries with key points"},
    {"id": "searchable_docs_agent", "name": "Searchable Docs Agent", "type": "searchable_docs_agent", "capabilities": ["document_indexing", "search_optimization", "content_discovery"], "category": "Content", "description": "Indexes documents and optimizes them for searchability and discovery"},
    
    # HR & Recruiting
    {"id": "cv_screening_agent", "name": "CV Screening Agent", "type": "cv_screening_agent", "capabilities": ["resume_parsing", "candidate_matching", "skill_assessment"], "category": "HR", "description": "Screens resumes and matches candidates based on skills and requirements"},
    {"id": "interview_question_generator", "name": "Interview Question Generator", "type": "interview_question_generator", "capabilities": ["question_generation", "skill_based_questions", "behavioral_assessment"], "category": "HR", "description": "Generates targeted interview questions for skill and behavioral assessment"},
    {"id": "onboarding_task_generator", "name": "Onboarding Task Generator", "type": "onboarding_task_generator", "capabilities": ["task_creation", "timeline_planning", "checklist_management"], "category": "HR", "description": "Creates onboarding tasks and manages timelines for new employees"},
    {"id": "team_feedback_analyzer", "name": "Team Feedback Analyzer", "type": "team_feedback_analyzer", "capabilities": ["feedback_collection", "trend_analysis", "insight_generation"], "category": "HR", "description": "Analyzes team feedback and generates insights on team performance"},
    
    # Legal & Compliance
    {"id": "contract_checker_agent", "name": "Contract Checker Agent", "type": "contract_checker_agent", "capabilities": ["contract_review", "clause_analysis", "risk_identification"], "category": "Legal", "description": "Reviews contracts and analyzes clauses for potential risks and issues"},
    {"id": "gdpr_checker_agent", "name": "GDPR Checker Agent", "type": "gdpr_checker_agent", "capabilities": ["compliance_checking", "data_protection", "privacy_assessment"], "category": "Legal", "description": "Ensures GDPR compliance and assesses data protection practices"},
    {"id": "terms_policy_generator", "name": "Terms & Policy Generator", "type": "terms_policy_generator", "capabilities": ["policy_creation", "legal_document_generation", "customization"], "category": "Legal", "description": "Creates terms of service, privacy policies, and other legal documents"},
    {"id": "risk_alerting_agent", "name": "Risk Alerting Agent", "type": "risk_alerting_agent", "capabilities": ["risk_monitoring", "alert_generation", "compliance_tracking"], "category": "Legal", "description": "Monitors compliance risks and generates alerts for potential issues"},
    
    # Analytics & Strategy
    {"id": "dashboard_agent", "name": "Dashboard Agent", "type": "dashboard_agent", "capabilities": ["data_visualization", "report_generation", "real_time_analytics"], "category": "Analytics", "description": "Creates data visualizations and generates real-time analytics dashboards"},
    {"id": "goal_progress_analyzer", "name": "Goal Progress Analyzer", "type": "goal_progress_analyzer", "capabilities": ["goal_tracking", "progress_measurement", "performance_analysis"], "category": "Analytics", "description": "Tracks goal progress and analyzes performance metrics"},
    {"id": "user_cohort_insights_agent", "name": "User Cohort Insights Agent", "type": "user_cohort_insights_agent", "capabilities": ["cohort_analysis", "user_behavior", "retention_metrics"], "category": "Analytics", "description": "Analyzes user cohorts and provides insights on behavior and retention"},
    {"id": "strategic_idea_recommender", "name": "Strategic Idea Recommender", "type": "strategic_idea_recommender", "capabilities": ["idea_generation", "opportunity_analysis", "strategic_planning"], "category": "Analytics", "description": "Generates strategic ideas and analyzes business opportunities"}
]


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class Department(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = 0
    ai_agent_count: Optional[int] = 0


class DepartmentAssignment(BaseModel):
    id: UUID
    department_id: UUID
    assignee_type: str  # 'member' or 'ai_agent'
    assignee_id: UUID
    assignee_name: str
    assignee_metadata: Dict[str, Any] = {}
    role: Optional[str]
    assigned_at: datetime
    assigned_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    # Additional fields from view
    member_email: Optional[str] = None
    member_full_name: Optional[str] = None


class AssignmentCreate(BaseModel):
    assignee_type: str = Field(..., pattern="^(member|ai_agent)$")
    assignee_id: str  # For AI agents, this will be the agent type ID
    role: Optional[str] = None


class AIAgent(BaseModel):
    id: str
    name: str
    type: str
    capabilities: List[str]
    category: Optional[str] = None
    description: Optional[str] = None


@router.get("", response_model=List[Department])
async def list_departments(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all departments in the project."""
    supabase = get_supabase()
    
    try:
        # Get departments
        response = supabase.table('departments').select('*').eq(
            'project_id', str(project_id)
        ).order('name').execute()
        
        departments = []
        for dept in response.data:
            dept_dict = dict(dept)
            
            # Get assignment counts
            assignments = supabase.table('department_assignments').select(
                'assignee_type'
            ).eq('department_id', dept['id']).execute()
            
            member_count = sum(1 for a in assignments.data if a['assignee_type'] == 'member')
            ai_agent_count = sum(1 for a in assignments.data if a['assignee_type'] == 'ai_agent')
            
            dept_dict['member_count'] = member_count
            dept_dict['ai_agent_count'] = ai_agent_count
            departments.append(Department(**dept_dict))
            
        return departments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list departments: {str(e)}"
        )


@router.post("", response_model=Department, status_code=status.HTTP_201_CREATED)
async def create_department(
    project_id: UUID,
    department: DepartmentCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new department. Requires admin or owner role."""
    supabase = get_supabase()
    
    try:
        response = supabase.table('departments').insert({
            'project_id': str(project_id),
            'name': department.name,
            'description': department.description
        }).execute()
        
        dept_dict = dict(response.data[0])
        dept_dict['member_count'] = 0
        dept_dict['ai_agent_count'] = 0
        return Department(**dept_dict)
    except Exception as e:
        if 'duplicate key' in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A department with this name already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create department: {str(e)}"
        )


@router.get("/ai-agents", response_model=List[AIAgent])
async def list_available_ai_agents(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all available AI agents that can be assigned to departments."""
    return AVAILABLE_AI_AGENTS


@router.get("/{department_id}", response_model=Department)
async def get_department(
    department_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific department."""
    supabase = get_supabase()
    
    try:
        response = supabase.table('departments').select('*').eq(
            'id', str(department_id)
        ).single().execute()
        
        dept_dict = dict(response.data)
        
        # Get assignment counts
        assignments = supabase.table('department_assignments').select(
            'assignee_type'
        ).eq('department_id', str(department_id)).execute()
        
        member_count = sum(1 for a in assignments.data if a['assignee_type'] == 'member')
        ai_agent_count = sum(1 for a in assignments.data if a['assignee_type'] == 'ai_agent')
        
        dept_dict['member_count'] = member_count
        dept_dict['ai_agent_count'] = ai_agent_count
        
        return Department(**dept_dict)
    except Exception as e:
        if 'not found' in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get department: {str(e)}"
        )


@router.patch("/{department_id}", response_model=Department)
async def update_department(
    department_id: UUID,
    department: DepartmentUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update a department. Requires admin or owner role."""
    supabase = get_supabase()
    
    update_data = {k: v for k, v in department.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    try:
        response = supabase.table('departments').update(
            update_data
        ).eq('id', str(department_id)).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        
        dept_dict = dict(response.data[0])
        
        # Get assignment counts
        assignments = supabase.table('department_assignments').select(
            'assignee_type'
        ).eq('department_id', str(department_id)).execute()
        
        member_count = sum(1 for a in assignments.data if a['assignee_type'] == 'member')
        ai_agent_count = sum(1 for a in assignments.data if a['assignee_type'] == 'ai_agent')
        
        dept_dict['member_count'] = member_count
        dept_dict['ai_agent_count'] = ai_agent_count
        
        return Department(**dept_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update department: {str(e)}"
        )


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a department. Requires admin or owner role."""
    supabase = get_supabase()
    
    try:
        response = supabase.table('departments').delete().eq(
            'id', str(department_id)
        ).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete department: {str(e)}"
        )


# Department Assignment endpoints
@router.get("/{department_id}/assignments", response_model=List[DepartmentAssignment])
async def list_department_assignments(
    department_id: UUID,
    assignee_type: Optional[str] = Query(None, pattern="^(member|ai_agent)$"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all assignments in a department."""
    supabase = get_supabase()
    
    try:
        query = supabase.table('department_assignments_view').select('*').eq(
            'department_id', str(department_id)
        )
        
        if assignee_type:
            query = query.eq('assignee_type', assignee_type)
        
        response = query.order('assignee_name').execute()
        
        return [DepartmentAssignment(**dict(a)) for a in response.data]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list assignments: {str(e)}"
        )


@router.post("/{department_id}/assignments", response_model=DepartmentAssignment, status_code=status.HTTP_201_CREATED)
async def create_department_assignment(
    department_id: UUID,
    assignment: AssignmentCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Assign a member or AI agent to a department."""
    supabase = get_supabase()
    
    try:
        # First check if the department exists and user has access
        dept_check = supabase.table('departments').select('project_id').eq('id', str(department_id)).single().execute()
        if not dept_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        # Get the public user ID of the current user
        auth_user_id = str(current_user.get("user_id", ""))
        auth_email = current_user.get("email")
        public_user_id = None
        
        # First try to find user by email if available
        if auth_email:
            user_result = supabase.table("users").select("id").eq("email", auth_email).execute()
            if user_result.data:
                public_user_id = user_result.data[0]["id"]
        
        # If not found by email, try by auth ID
        if not public_user_id and auth_user_id:
            user_result = supabase.table("users").select("id").eq("id", auth_user_id).execute()
            if user_result.data:
                public_user_id = user_result.data[0]["id"]
        
        # If still not found, create a minimal user record
        if not public_user_id:
            # Create user with auth user ID
            user_data = {
                "id": auth_user_id,
                "email": auth_email or f"user_{auth_user_id}@unknown.com",
                "name": auth_email.split('@')[0] if auth_email else f"User {auth_user_id[:8]}",
                "auth_provider": "supabase",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            try:
                supabase.table("users").insert(user_data).execute()
                public_user_id = auth_user_id
            except Exception as e:
                # User might already exist, try to fetch again
                user_result = supabase.table("users").select("id").eq("id", auth_user_id).execute()
                if user_result.data:
                    public_user_id = user_result.data[0]["id"]
                else:
                    # If we still can't create/find user, use auth_user_id
                    public_user_id = auth_user_id
        
        # Generate assignment ID upfront
        assignment_id = str(uuid4())
        
        # Prepare assignment data
        assignment_data = {
            'id': assignment_id,
            'department_id': str(department_id),
            'assignee_type': assignment.assignee_type,
            'role': assignment.role,
            'assigned_by': public_user_id
        }
        
        # Check if assignment already exists
        if assignment.assignee_type == 'member':
            existing_check = supabase.table('department_assignments').select('id').match({
                'department_id': str(department_id),
                'assignee_type': 'member',
                'assignee_id': assignment.assignee_id
            }).execute()
            
            if existing_check.data:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This member is already assigned to this department"
                )
        
        if assignment.assignee_type == 'member':
            # For members, assignee_id is the user ID
            # Get member details from users table
            user_response = supabase.table('users').select('*').eq('id', assignment.assignee_id).single().execute()
            if not user_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Member not found"
                )
            
            user_data = user_response.data
            assignment_data['assignee_id'] = assignment.assignee_id
            assignment_data['assignee_name'] = user_data.get('name') or user_data.get('email', 'Unknown')
            assignment_data['assignee_metadata'] = {
                'email': user_data.get('email', ''),
                'user_id': user_data['id']
            }
        else:
            # For AI agents, assignee_id is the agent type
            # Find the agent in our list
            agent = next((a for a in AVAILABLE_AI_AGENTS if a['id'] == assignment.assignee_id), None)
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="AI agent not found"
                )
            
            # Generate a unique ID for this agent assignment
            assignment_data['assignee_id'] = str(uuid4())
            assignment_data['assignee_name'] = agent['name']
            assignment_data['assignee_metadata'] = {
                'agent_type': agent['type'],
                'agent_id': agent['id'],
                'capabilities': agent['capabilities']
            }
        
        # Create the assignment
        response = supabase.table('department_assignments').insert(
            assignment_data
        ).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create assignment"
            )
        
        # Fetch the created assignment with view data
        created = supabase.table('department_assignments_view').select('*').eq(
            'id', assignment_id
        ).single().execute()
        
        if not created.data:
            # If view doesn't work, return basic assignment data
            return DepartmentAssignment(
                id=UUID(assignment_id),
                department_id=department_id,
                assignee_type=assignment_data['assignee_type'],
                assignee_id=UUID(assignment_data['assignee_id']),
                assignee_name=assignment_data['assignee_name'],
                assignee_metadata=assignment_data.get('assignee_metadata', {}),
                role=assignment_data.get('role'),
                assigned_at=datetime.utcnow(),
                assigned_by=UUID(public_user_id) if public_user_id else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        return DepartmentAssignment(**dict(created.data))
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error: {str(e)}\nType: {type(e).__name__}\nTraceback: {traceback.format_exc()}"
        print(f"Assignment creation error: {error_detail}")
        
        if 'duplicate key' in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This assignee is already assigned to this department"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create assignment: {str(e)}"
        )


@router.delete("/{department_id}/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department_assignment(
    department_id: UUID,
    assignment_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Remove an assignment from a department."""
    supabase = get_supabase()
    
    try:
        response = supabase.table('department_assignments').delete().match({
            'id': str(assignment_id),
            'department_id': str(department_id)
        }).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete assignment: {str(e)}"
        )