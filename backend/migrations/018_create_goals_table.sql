-- Create goals table
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    target_date DATE,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_goals_project_id ON goals(project_id);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
CREATE INDEX IF NOT EXISTS idx_goals_target_date ON goals(target_date);

-- Create updated_at trigger
CREATE TRIGGER update_goals_updated_at BEFORE UPDATE
    ON goals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY goals_select_policy ON goals
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM project_members 
            WHERE project_members.project_id = goals.project_id 
            AND project_members.user_id = auth.uid()
        )
        OR EXISTS (
            SELECT 1 FROM projects p
            JOIN organization_members om ON om.organization_id = p.organization_id
            WHERE p.id = goals.project_id
            AND om.user_id = auth.uid()
        )
    );

CREATE POLICY goals_insert_policy ON goals
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM project_members 
            WHERE project_members.project_id = goals.project_id 
            AND project_members.user_id = auth.uid()
            AND project_members.role IN ('owner', 'admin', 'member')
        )
        OR EXISTS (
            SELECT 1 FROM projects p
            JOIN organization_members om ON om.organization_id = p.organization_id
            WHERE p.id = goals.project_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

CREATE POLICY goals_update_policy ON goals
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM project_members 
            WHERE project_members.project_id = goals.project_id 
            AND project_members.user_id = auth.uid()
            AND project_members.role IN ('owner', 'admin', 'member')
        )
        OR EXISTS (
            SELECT 1 FROM projects p
            JOIN organization_members om ON om.organization_id = p.organization_id
            WHERE p.id = goals.project_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

CREATE POLICY goals_delete_policy ON goals
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM project_members 
            WHERE project_members.project_id = goals.project_id 
            AND project_members.user_id = auth.uid()
            AND project_members.role IN ('owner', 'admin')
        )
        OR EXISTS (
            SELECT 1 FROM projects p
            JOIN organization_members om ON om.organization_id = p.organization_id
            WHERE p.id = goals.project_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

-- Add comment for documentation
COMMENT ON TABLE goals IS 'Project goals/objectives with progress tracking';
COMMENT ON COLUMN goals.status IS 'Goal status: active, completed, or archived';
COMMENT ON COLUMN goals.progress IS 'Goal progress percentage (0-100)';