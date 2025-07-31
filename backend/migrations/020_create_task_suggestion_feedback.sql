-- Create task_suggestion_feedback table
CREATE TABLE IF NOT EXISTS task_suggestion_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    suggestion_session_id UUID NOT NULL,
    suggested_task JSONB NOT NULL,
    feedback_type VARCHAR(50) CHECK (feedback_type IN ('accepted', 'rejected', 'neutral')),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_task_feedback_goal_id ON task_suggestion_feedback(goal_id);
CREATE INDEX idx_task_feedback_user_id ON task_suggestion_feedback(user_id);
CREATE INDEX idx_task_feedback_session_id ON task_suggestion_feedback(suggestion_session_id);
CREATE INDEX idx_task_feedback_created_at ON task_suggestion_feedback(created_at DESC);

-- Enable RLS
ALTER TABLE task_suggestion_feedback ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own feedback
CREATE POLICY task_feedback_select ON task_suggestion_feedback
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM goals g
            JOIN projects p ON g.project_id = p.id
            JOIN project_members pm ON p.id = pm.project_id
            WHERE g.id = task_suggestion_feedback.goal_id
            AND pm.user_id = auth.uid()::uuid
        )
    );

-- Policy: Users can insert feedback for goals they have access to
CREATE POLICY task_feedback_insert ON task_suggestion_feedback
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM goals g
            JOIN projects p ON g.project_id = p.id
            JOIN project_members pm ON p.id = pm.project_id
            WHERE g.id = goal_id
            AND pm.user_id = auth.uid()::uuid
            AND pm.role IN ('owner', 'admin', 'member')
        )
    );

-- Policy: Users can update their own feedback
CREATE POLICY task_feedback_update ON task_suggestion_feedback
    FOR UPDATE USING (
        user_id = auth.uid()::uuid
        AND EXISTS (
            SELECT 1 FROM goals g
            JOIN projects p ON g.project_id = p.id
            JOIN project_members pm ON p.id = pm.project_id
            WHERE g.id = task_suggestion_feedback.goal_id
            AND pm.user_id = auth.uid()::uuid
        )
    );

-- Policy: Users can delete their own feedback
CREATE POLICY task_feedback_delete ON task_suggestion_feedback
    FOR DELETE USING (
        user_id = auth.uid()::uuid
        AND EXISTS (
            SELECT 1 FROM goals g
            JOIN projects p ON g.project_id = p.id
            JOIN project_members pm ON p.id = pm.project_id
            WHERE g.id = task_suggestion_feedback.goal_id
            AND pm.user_id = auth.uid()::uuid
            AND pm.role IN ('owner', 'admin')
        )
    );

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_task_feedback_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER task_feedback_updated_at
    BEFORE UPDATE ON task_suggestion_feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_task_feedback_updated_at();