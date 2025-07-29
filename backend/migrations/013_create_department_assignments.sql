-- Create department_assignments table to link both members and AI agents to departments
CREATE TABLE IF NOT EXISTS department_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    assignee_type TEXT NOT NULL CHECK (assignee_type IN ('member', 'ai_agent')),
    assignee_id UUID NOT NULL, -- either user_id for members or a unique ID for AI agents
    assignee_name TEXT NOT NULL, -- Display name for the assignee
    assignee_metadata JSONB DEFAULT '{}', -- Additional metadata (e.g., agent type, capabilities)
    role TEXT, -- Optional role within the department
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(department_id, assignee_type, assignee_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_dept_assignments_dept ON department_assignments(department_id);
CREATE INDEX IF NOT EXISTS idx_dept_assignments_assignee ON department_assignments(assignee_type, assignee_id);
CREATE INDEX IF NOT EXISTS idx_dept_assignments_type ON department_assignments(assignee_type);

-- Create updated_at trigger
CREATE TRIGGER update_dept_assignments_updated_at BEFORE UPDATE
    ON department_assignments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE department_assignments ENABLE ROW LEVEL SECURITY;

-- RLS Policies for department_assignments
-- Select: Users can see assignments in their organization
CREATE POLICY dept_assignments_select_policy ON department_assignments
    FOR SELECT USING (
        department_id IN (
            SELECT d.id FROM departments d
            JOIN projects p ON d.project_id = p.id
            JOIN organization_members om ON p.organization_id = om.organization_id
            WHERE om.user_id = auth.uid()
        )
    );

-- Insert: Only org admins/owners can create assignments
CREATE POLICY dept_assignments_insert_policy ON department_assignments
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM departments d
            JOIN projects p ON d.project_id = p.id
            JOIN organization_members om ON p.organization_id = om.organization_id
            WHERE d.id = NEW.department_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

-- Update: Only org admins/owners can update assignments
CREATE POLICY dept_assignments_update_policy ON department_assignments
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM departments d
            JOIN projects p ON d.project_id = p.id
            JOIN organization_members om ON p.organization_id = om.organization_id
            WHERE d.id = department_assignments.department_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

-- Delete: Only org admins/owners can delete assignments
CREATE POLICY dept_assignments_delete_policy ON department_assignments
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM departments d
            JOIN projects p ON d.project_id = p.id
            JOIN organization_members om ON p.organization_id = om.organization_id
            WHERE d.id = department_assignments.department_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

-- Create a view for easier querying of assignments with full details
CREATE OR REPLACE VIEW department_assignments_view AS
SELECT 
    da.*,
    d.name as department_name,
    d.description as department_description,
    p.name as project_name,
    p.organization_id,
    CASE 
        WHEN da.assignee_type = 'member' THEN u.email
        ELSE NULL
    END as member_email,
    CASE 
        WHEN da.assignee_type = 'member' THEN u.raw_user_meta_data->>'full_name'
        ELSE NULL
    END as member_full_name
FROM department_assignments da
JOIN departments d ON da.department_id = d.id
JOIN projects p ON d.project_id = p.id
LEFT JOIN auth.users u ON da.assignee_type = 'member' AND da.assignee_id = u.id;

-- Grant permissions on the view
GRANT SELECT ON department_assignments_view TO authenticated;