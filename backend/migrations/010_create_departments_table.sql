-- Create departments table
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, name)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_departments_project ON departments(project_id);
CREATE INDEX IF NOT EXISTS idx_departments_name ON departments(name);

-- Create updated_at trigger
CREATE TRIGGER update_departments_updated_at BEFORE UPDATE
    ON departments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;

-- RLS Policies for departments
-- Select: Users can see departments in projects they have access to
CREATE POLICY departments_select_policy ON departments
    FOR SELECT USING (
        project_id IN (
            SELECT p.id FROM projects p
            JOIN organization_members om ON p.organization_id = om.organization_id
            WHERE om.user_id = auth.uid()
        )
    );

-- Insert: Only org admins/owners can create departments
CREATE POLICY departments_insert_policy ON departments
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM projects p
            JOIN organization_members om ON p.organization_id = om.organization_id
            WHERE p.id = NEW.project_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

-- Update: Only org admins/owners can update departments
CREATE POLICY departments_update_policy ON departments
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM projects p
            JOIN organization_members om ON p.organization_id = om.organization_id
            WHERE p.id = departments.project_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

-- Delete: Only org admins/owners can delete departments
CREATE POLICY departments_delete_policy ON departments
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM projects p
            JOIN organization_members om ON p.organization_id = om.organization_id
            WHERE p.id = departments.project_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );