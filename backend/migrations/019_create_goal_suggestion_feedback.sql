-- Create goal suggestion feedback table
CREATE TABLE IF NOT EXISTS goal_suggestion_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    suggestion_session_id UUID NOT NULL, -- Groups feedback for a single suggestion session
    suggested_goal JSONB NOT NULL, -- The complete suggested goal data
    feedback_type TEXT NOT NULL CHECK (feedback_type IN ('accepted', 'rejected', 'modified')),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5), -- User rating of the suggestion
    feedback_text TEXT, -- Optional user comments
    modifications JSONB, -- If modified, what changes were made
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_goal_feedback_project_id ON goal_suggestion_feedback(project_id);
CREATE INDEX IF NOT EXISTS idx_goal_feedback_user_id ON goal_suggestion_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_goal_feedback_session_id ON goal_suggestion_feedback(suggestion_session_id);
CREATE INDEX IF NOT EXISTS idx_goal_feedback_created_at ON goal_suggestion_feedback(created_at DESC);

-- Enable Row Level Security
ALTER TABLE goal_suggestion_feedback ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY goal_feedback_select_policy ON goal_suggestion_feedback
    FOR SELECT USING (
        -- Users can see feedback for projects they have access to
        EXISTS (
            SELECT 1 FROM project_members 
            WHERE project_members.project_id = goal_suggestion_feedback.project_id 
            AND project_members.user_id = auth.uid()
        )
        OR EXISTS (
            SELECT 1 FROM projects p
            JOIN organization_members om ON om.organization_id = p.organization_id
            WHERE p.id = goal_suggestion_feedback.project_id
            AND om.user_id = auth.uid()
        )
    );

CREATE POLICY goal_feedback_insert_policy ON goal_suggestion_feedback
    FOR INSERT WITH CHECK (
        -- Users can insert feedback for projects they have access to
        user_id = auth.uid() AND
        EXISTS (
            SELECT 1 FROM project_members 
            WHERE project_members.project_id = goal_suggestion_feedback.project_id 
            AND project_members.user_id = auth.uid()
        )
        OR EXISTS (
            SELECT 1 FROM projects p
            JOIN organization_members om ON om.organization_id = p.organization_id
            WHERE p.id = goal_suggestion_feedback.project_id
            AND om.user_id = auth.uid()
        )
    );

-- Add comments for documentation
COMMENT ON TABLE goal_suggestion_feedback IS 'Tracks user feedback on AI-generated goal suggestions for improving future suggestions';
COMMENT ON COLUMN goal_suggestion_feedback.suggestion_session_id IS 'Groups feedback from a single suggestion session';
COMMENT ON COLUMN goal_suggestion_feedback.suggested_goal IS 'The complete AI-suggested goal data';
COMMENT ON COLUMN goal_suggestion_feedback.feedback_type IS 'Whether the suggestion was accepted, rejected, or modified';
COMMENT ON COLUMN goal_suggestion_feedback.rating IS 'User rating of suggestion quality (1-5)';
COMMENT ON COLUMN goal_suggestion_feedback.modifications IS 'JSON object showing what fields were modified if feedback_type is "modified"';