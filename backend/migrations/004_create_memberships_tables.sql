-- Create organization_members table
CREATE TABLE IF NOT EXISTS organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    invited_by UUID REFERENCES users(id),
    invited_at TIMESTAMP DEFAULT NOW(),
    accepted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_org_members_org_user ON organization_members(organization_id, user_id);
CREATE INDEX IF NOT EXISTS idx_org_members_user_orgs ON organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_org_members_role ON organization_members(role);

-- Create updated_at trigger
CREATE TRIGGER update_org_members_updated_at BEFORE UPDATE
    ON organization_members FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create project_members table
CREATE TABLE IF NOT EXISTS project_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'member', 'viewer')),
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, user_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_project_members_project_user ON project_members(project_id, user_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user_projects ON project_members(user_id);

-- Create updated_at trigger
CREATE TRIGGER update_project_members_updated_at BEFORE UPDATE
    ON project_members FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_members ENABLE ROW LEVEL SECURITY;

-- Organization members policies
CREATE POLICY org_members_select_policy ON organization_members
    FOR SELECT USING (
        user_id = auth.uid() OR 
        organization_id IN (
            SELECT organization_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY org_members_insert_policy ON organization_members
    FOR INSERT WITH CHECK (
        -- Only org admins/owners can add members
        EXISTS (
            SELECT 1 FROM organization_members 
            WHERE organization_id = NEW.organization_id 
            AND user_id = auth.uid() 
            AND role IN ('owner', 'admin')
        )
    );

CREATE POLICY org_members_update_policy ON organization_members
    FOR UPDATE USING (
        -- Only org admins/owners can update members
        EXISTS (
            SELECT 1 FROM organization_members 
            WHERE organization_id = organization_members.organization_id 
            AND user_id = auth.uid() 
            AND role IN ('owner', 'admin')
        )
    );

CREATE POLICY org_members_delete_policy ON organization_members
    FOR DELETE USING (
        -- Only org admins/owners can remove members
        EXISTS (
            SELECT 1 FROM organization_members 
            WHERE organization_id = organization_members.organization_id 
            AND user_id = auth.uid() 
            AND role IN ('owner', 'admin')
        )
    );

-- Project members policies
CREATE POLICY project_members_select_policy ON project_members
    FOR SELECT USING (
        user_id = auth.uid() OR 
        project_id IN (
            SELECT p.id FROM projects p
            JOIN organization_members om ON p.organization_id = om.organization_id
            WHERE om.user_id = auth.uid()
        )
    );

CREATE POLICY project_members_insert_policy ON project_members
    FOR INSERT WITH CHECK (
        -- Only org/project admins can add members
        EXISTS (
            SELECT 1 FROM projects p
            JOIN organization_members om ON p.organization_id = om.organization_id
            WHERE p.id = NEW.project_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

CREATE POLICY project_members_update_policy ON project_members
    FOR UPDATE USING (
        -- Only org/project admins can update members
        EXISTS (
            SELECT 1 FROM projects p
            JOIN organization_members om ON p.organization_id = om.organization_id
            WHERE p.id = project_members.project_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

CREATE POLICY project_members_delete_policy ON project_members
    FOR DELETE USING (
        -- Only org/project admins can remove members
        EXISTS (
            SELECT 1 FROM projects p
            JOIN organization_members om ON p.organization_id = om.organization_id
            WHERE p.id = project_members.project_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );