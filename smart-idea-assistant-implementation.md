# Smart Idea Assistant Implementation

## Overview
Implement a conversational AI-powered idea capture and validation system that transforms raw ideas into actionable tasks at both company and project levels.

## User Story
As a user, I want to write down my ideas through a conversational interface that helps refine, validate, and transform them into structured tasks, so that good ideas don't get lost and are properly evaluated before implementation.

## Technical Requirements

### 1. Database Schema
```sql
-- New tables needed
CREATE TABLE ideas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  project_id UUID REFERENCES projects(id), -- NULL for company-level ideas
  user_id UUID REFERENCES auth.users(id),
  title TEXT NOT NULL,
  initial_description TEXT NOT NULL,
  refined_description TEXT,
  status TEXT CHECK (status IN ('draft', 'refining', 'validated', 'rejected', 'converted')),
  validation_score DECIMAL(3,2), -- 0.00 to 1.00
  validation_reasons JSONB,
  conversation_history JSONB,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE idea_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  idea_id UUID REFERENCES ideas(id),
  task_id UUID REFERENCES tasks(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add RLS policies
CREATE POLICY "Users can view ideas in their organizations" ON ideas
  FOR SELECT USING (
    organization_id IN (
      SELECT organization_id FROM organization_users 
      WHERE user_id = auth.uid()
    )
  );
```

### 2. New CrewAI Agent: IdeaAssistant

**Location**: `backend/app/agents/crews/idea_assistant_crew.py`

**Capabilities**:
- Conversational refinement of ideas
- Context-aware validation
- Task breakdown generation
- Feasibility analysis

**Configuration**: `backend/app/agents/config/idea_assistant.yaml`
```yaml
agents:
  idea_refiner:
    role: "Idea Refinement Specialist"
    goal: "Transform raw ideas into well-structured, actionable proposals"
    backstory: "Expert at asking the right questions to clarify and enhance ideas"
    
  idea_validator:
    role: "Strategic Idea Validator"
    goal: "Assess idea feasibility and alignment with business goals"
    backstory: "Experienced strategist who evaluates ideas against multiple criteria"
    
  task_generator:
    role: "Task Breakdown Specialist"
    goal: "Convert validated ideas into structured, actionable tasks"
    backstory: "Expert at breaking down complex ideas into manageable tasks"

tasks:
  refine_idea:
    description: "Engage in conversation to refine and clarify the idea"
    agent: idea_refiner
    
  validate_idea:
    description: "Validate idea against business context and feasibility"
    agent: idea_validator
    
  generate_tasks:
    description: "Create task breakdown for approved ideas"
    agent: task_generator
```

### 3. API Endpoints

**New Router**: `backend/app/api/routers/ideas.py`

```python
POST   /api/ideas                    # Create new idea
GET    /api/ideas                    # List ideas (with filters)
GET    /api/ideas/{id}               # Get idea details
POST   /api/ideas/{id}/refine        # Continue refinement conversation
POST   /api/ideas/{id}/validate      # Trigger validation
POST   /api/ideas/{id}/convert       # Convert to tasks
DELETE /api/ideas/{id}               # Delete idea
```

### 4. Frontend Components

**New Components**:
- `IdeaAssistant.tsx` - Main conversational interface
- `IdeaBoard.tsx` - Visual overview of all ideas
- `IdeaDetail.tsx` - Full idea view with conversation history

**UI Flow**:
1. User clicks "New Idea" button (available at company and project levels)
2. Chat interface opens with initial prompt
3. User describes idea in natural language
4. AI asks clarifying questions
5. Conversation continues until idea is refined
6. User triggers validation
7. AI presents validation results with score and reasons
8. If approved, user can convert to tasks

### 5. Conversation Flow

**Phase 1: Initial Capture**
```
AI: "What's your idea? Feel free to describe it in your own words."
User: "We should create a customer loyalty program"
```

**Phase 2: Clarification**
```
AI: "Interesting! A loyalty program could drive retention. Let me understand better:
- What specific behaviors do you want to reward?
- Who is the target customer segment?
- What's the main business goal?"
```

**Phase 3: Context Integration**
```
AI: "I see you're working on [Project Name]. This loyalty program could align with your current goal of [pulled from project data]. Would this be for all customers or specific to this project's audience?"
```

**Phase 4: Refinement**
```
AI: "Based on our discussion, here's the refined idea:
'Implement a points-based loyalty program targeting premium customers, rewarding purchase frequency and social sharing, with the goal of increasing customer lifetime value by 20%.'
Does this capture your vision?"
```

**Phase 5: Validation**
```
AI: "Validation Results:
✅ Alignment Score: 0.85/1.0
✅ Feasibility: High
✅ Resource Requirements: Medium
⚠️ Considerations: Requires integration with payment system

Recommendation: Proceed with implementation planning"
```

**Phase 6: Task Generation**
```
AI: "I've broken this down into 8 tasks:
1. Research loyalty program platforms (2 days)
2. Define point earning rules (1 day)
3. Design reward tiers (1 day)
...
Would you like me to create these tasks in your project?"
```

### 6. Integration Points

**With Existing Systems**:
- Pull company/project context from database
- Use existing task management system
- Integrate with workflow system for task execution
- Leverage existing CrewAI infrastructure

**Data Sources for Validation**:
- Company goals and KPIs
- Project objectives and constraints
- Historical task completion data
- Resource availability
- Market/competitor analysis (via research agents)

### 7. Implementation Phases

**Phase 1 (MVP)**:
- Basic idea capture and storage
- Simple refinement conversation
- Manual validation process
- Basic task creation

**Phase 2**:
- Full conversational AI refinement
- Automated validation scoring
- Context integration
- Task breakdown generation

**Phase 3**:
- Learning from outcomes
- Idea similarity detection
- Team collaboration features
- Analytics dashboard

### 8. Success Metrics

- **Idea Quality**: Validation score improvement from initial to refined
- **Conversion Rate**: % of ideas converted to tasks
- **Task Success**: % of generated tasks completed successfully
- **Time Saved**: Reduction in idea-to-implementation time
- **User Engagement**: Number of ideas submitted per user/month

### 9. Technical Considerations

**Performance**:
- Store conversation history efficiently in JSONB
- Implement pagination for idea lists
- Cache validation results

**Security**:
- Enforce RLS policies for multi-tenant isolation
- Validate user permissions for company vs project ideas
- Sanitize all user inputs

**AI Cost Management**:
- Implement token limits per conversation
- Use smaller models for simple clarifications
- Batch validation requests

### 10. Testing Strategy

**Unit Tests**:
- Idea CRUD operations
- Validation logic
- Task generation algorithms

**Integration Tests**:
- Full conversation flow
- Context retrieval
- Task creation in existing system

**E2E Tests**:
- Complete user journey from idea to tasks
- Multi-tenant isolation
- Permission checks

## Acceptance Criteria

- [ ] Users can create ideas at company or project level
- [ ] AI engages in natural conversation to refine ideas
- [ ] Ideas are validated with clear scoring and reasoning
- [ ] Validated ideas can be converted to structured tasks
- [ ] All data respects multi-tenant boundaries
- [ ] Conversation history is preserved and viewable
- [ ] Ideas can be filtered by status, score, and level
- [ ] Generated tasks integrate with existing workflow system