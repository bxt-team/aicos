-- Create organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    subscription_tier TEXT DEFAULT 'free',
    subscription_status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug);
CREATE INDEX IF NOT EXISTS idx_organizations_status ON organizations(subscription_status);
CREATE INDEX IF NOT EXISTS idx_organizations_deleted ON organizations(deleted_at) WHERE deleted_at IS NULL;

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE
    ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (will be updated after users table is created)
-- These are placeholder policies that will be replaced
CREATE POLICY organizations_select_policy ON organizations
    FOR SELECT USING (true);

CREATE POLICY organizations_insert_policy ON organizations
    FOR INSERT WITH CHECK (true);

CREATE POLICY organizations_update_policy ON organizations
    FOR UPDATE USING (true);

CREATE POLICY organizations_delete_policy ON organizations
    FOR DELETE USING (true);-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    UNIQUE(organization_id, slug)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_projects_org_slug ON projects(organization_id, slug);
CREATE INDEX IF NOT EXISTS idx_projects_active ON projects(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_projects_deleted ON projects(deleted_at) WHERE deleted_at IS NULL;

-- Create updated_at trigger
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE
    ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (will be updated after users table is created)
CREATE POLICY projects_select_policy ON projects
    FOR SELECT USING (true);

CREATE POLICY projects_insert_policy ON projects
    FOR INSERT WITH CHECK (true);

CREATE POLICY projects_update_policy ON projects
    FOR UPDATE USING (true);

CREATE POLICY projects_delete_policy ON projects
    FOR DELETE USING (true);-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    avatar_url TEXT,
    auth_provider TEXT DEFAULT 'email',
    auth_provider_id TEXT,
    email_verified BOOLEAN DEFAULT false,
    settings JSONB DEFAULT '{}',
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_provider ON users(auth_provider, auth_provider_id);
CREATE INDEX IF NOT EXISTS idx_users_deleted ON users(deleted_at) WHERE deleted_at IS NULL;

-- Create updated_at trigger
CREATE TRIGGER update_users_updated_at BEFORE UPDATE
    ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY users_select_own_policy ON users
    FOR SELECT USING (auth.uid() = id);

-- Users can only update their own data
CREATE POLICY users_update_own_policy ON users
    FOR UPDATE USING (auth.uid() = id);

-- System can insert new users (during signup)
CREATE POLICY users_insert_policy ON users
    FOR INSERT WITH CHECK (true);

-- Note: We'll need to update these policies after implementing auth functions-- Create organization_members table
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
    );-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    key_prefix TEXT NOT NULL,
    permissions JSONB DEFAULT '{}',
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    revoked_at TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX IF NOT EXISTS idx_api_keys_org ON api_keys(organization_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_expires ON api_keys(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_api_keys_revoked ON api_keys(revoked_at) WHERE revoked_at IS NULL;

-- Enable Row Level Security
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- API keys policies
CREATE POLICY api_keys_select_policy ON api_keys
    FOR SELECT USING (
        -- Users can see API keys they created or in their organizations
        created_by = auth.uid() OR
        organization_id IN (
            SELECT organization_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY api_keys_insert_policy ON api_keys
    FOR INSERT WITH CHECK (
        -- Users can create API keys for organizations they're members of
        created_by = auth.uid() AND
        EXISTS (
            SELECT 1 FROM organization_members 
            WHERE organization_id = NEW.organization_id 
            AND user_id = auth.uid()
            AND role IN ('owner', 'admin')
        )
    );

CREATE POLICY api_keys_update_policy ON api_keys
    FOR UPDATE USING (
        -- Only org admins/owners can update API keys
        EXISTS (
            SELECT 1 FROM organization_members 
            WHERE organization_id = api_keys.organization_id 
            AND user_id = auth.uid() 
            AND role IN ('owner', 'admin')
        )
    );

CREATE POLICY api_keys_delete_policy ON api_keys
    FOR DELETE USING (
        -- Only org admins/owners can delete API keys
        EXISTS (
            SELECT 1 FROM organization_members 
            WHERE organization_id = api_keys.organization_id 
            AND user_id = auth.uid() 
            AND role IN ('owner', 'admin')
        )
    );-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_org ON audit_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- Enable Row Level Security
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Audit logs policies
CREATE POLICY audit_logs_select_policy ON audit_logs
    FOR SELECT USING (
        -- Users can see audit logs for their organizations
        organization_id IN (
            SELECT organization_id FROM organization_members 
            WHERE user_id = auth.uid()
            AND role IN ('owner', 'admin')
        )
    );

-- Only system can insert audit logs
CREATE POLICY audit_logs_insert_policy ON audit_logs
    FOR INSERT WITH CHECK (false);

-- Audit logs are immutable
CREATE POLICY audit_logs_update_policy ON audit_logs
    FOR UPDATE USING (false);

CREATE POLICY audit_logs_delete_policy ON audit_logs
    FOR DELETE USING (false);

-- Create function for easy audit logging
CREATE OR REPLACE FUNCTION log_audit_event(
    p_action TEXT,
    p_resource_type TEXT,
    p_resource_id UUID DEFAULT NULL,
    p_organization_id UUID DEFAULT NULL,
    p_project_id UUID DEFAULT NULL,
    p_user_id UUID DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    v_audit_id UUID;
BEGIN
    INSERT INTO audit_logs (
        action,
        resource_type,
        resource_id,
        organization_id,
        project_id,
        user_id,
        metadata
    ) VALUES (
        p_action,
        p_resource_type,
        p_resource_id,
        p_organization_id,
        p_project_id,
        p_user_id,
        p_metadata
    ) RETURNING id INTO v_audit_id;
    
    RETURN v_audit_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;-- Update RLS policies after all tables are created

-- Drop placeholder policies for organizations
DROP POLICY IF EXISTS organizations_select_policy ON organizations;
DROP POLICY IF EXISTS organizations_insert_policy ON organizations;
DROP POLICY IF EXISTS organizations_update_policy ON organizations;
DROP POLICY IF EXISTS organizations_delete_policy ON organizations;

-- Create proper organization policies
CREATE POLICY organizations_select_policy ON organizations
    FOR SELECT USING (
        -- Users can see organizations they're members of
        id IN (
            SELECT organization_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY organizations_insert_policy ON organizations
    FOR INSERT WITH CHECK (
        -- Any authenticated user can create an organization
        auth.uid() IS NOT NULL
    );

CREATE POLICY organizations_update_policy ON organizations
    FOR UPDATE USING (
        -- Only org owners/admins can update
        EXISTS (
            SELECT 1 FROM organization_members 
            WHERE organization_id = organizations.id 
            AND user_id = auth.uid() 
            AND role IN ('owner', 'admin')
        )
    );

CREATE POLICY organizations_delete_policy ON organizations
    FOR DELETE USING (
        -- Only org owners can delete
        EXISTS (
            SELECT 1 FROM organization_members 
            WHERE organization_id = organizations.id 
            AND user_id = auth.uid() 
            AND role = 'owner'
        )
    );

-- Drop placeholder policies for projects
DROP POLICY IF EXISTS projects_select_policy ON projects;
DROP POLICY IF EXISTS projects_insert_policy ON projects;
DROP POLICY IF EXISTS projects_update_policy ON projects;
DROP POLICY IF EXISTS projects_delete_policy ON projects;

-- Create proper project policies
CREATE POLICY projects_select_policy ON projects
    FOR SELECT USING (
        -- Users can see projects in their organizations
        organization_id IN (
            SELECT organization_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY projects_insert_policy ON projects
    FOR INSERT WITH CHECK (
        -- Only org admins/owners can create projects
        EXISTS (
            SELECT 1 FROM organization_members 
            WHERE organization_id = NEW.organization_id 
            AND user_id = auth.uid() 
            AND role IN ('owner', 'admin')
        )
    );

CREATE POLICY projects_update_policy ON projects
    FOR UPDATE USING (
        -- Only org admins/owners can update projects
        EXISTS (
            SELECT 1 FROM organization_members 
            WHERE organization_id = projects.organization_id 
            AND user_id = auth.uid() 
            AND role IN ('owner', 'admin')
        )
    );

CREATE POLICY projects_delete_policy ON projects
    FOR DELETE USING (
        -- Only org admins/owners can delete projects
        EXISTS (
            SELECT 1 FROM organization_members 
            WHERE organization_id = projects.organization_id 
            AND user_id = auth.uid() 
            AND role IN ('owner', 'admin')
        )
    );

-- Create helper function to check user permissions
CREATE OR REPLACE FUNCTION user_has_permission(
    p_user_id UUID,
    p_organization_id UUID,
    p_project_id UUID DEFAULT NULL,
    p_required_role TEXT DEFAULT 'member'
) RETURNS BOOLEAN AS $$
BEGIN
    -- Check organization membership
    IF NOT EXISTS (
        SELECT 1 FROM organization_members 
        WHERE organization_id = p_organization_id 
        AND user_id = p_user_id
        AND (
            (p_required_role = 'owner' AND role = 'owner') OR
            (p_required_role = 'admin' AND role IN ('owner', 'admin')) OR
            (p_required_role = 'member' AND role IN ('owner', 'admin', 'member')) OR
            (p_required_role = 'viewer' AND role IN ('owner', 'admin', 'member', 'viewer'))
        )
    ) THEN
        RETURN FALSE;
    END IF;
    
    -- If project specified, check project membership (optional)
    IF p_project_id IS NOT NULL THEN
        -- Check if user has explicit project membership
        IF EXISTS (
            SELECT 1 FROM project_members 
            WHERE project_id = p_project_id 
            AND user_id = p_user_id
        ) THEN
            RETURN TRUE;
        END IF;
        
        -- Otherwise, rely on organization membership
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;-- Template for updating existing agent tables with multi-tenant support
-- This shows the pattern to apply to all agent-specific tables

-- Example: Update affirmations table
ALTER TABLE IF EXISTS agent_affirmation_items
    ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_affirmations_org_project 
    ON agent_affirmation_items(organization_id, project_id);

-- Enable RLS
ALTER TABLE agent_affirmation_items ENABLE ROW LEVEL SECURITY;

-- Create RLS policy template for agent tables
CREATE POLICY affirmations_multi_tenant_policy ON agent_affirmation_items
    FOR ALL USING (
        organization_id IN (
            SELECT organization_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
        AND (
            project_id IS NULL 
            OR project_id IN (
                SELECT id FROM projects 
                WHERE organization_id = agent_affirmation_items.organization_id
                AND (
                    -- User has org-level access
                    EXISTS (
                        SELECT 1 FROM organization_members 
                        WHERE organization_id = projects.organization_id 
                        AND user_id = auth.uid()
                    )
                    OR
                    -- User has project-level access
                    EXISTS (
                        SELECT 1 FROM project_members 
                        WHERE project_id = projects.id 
                        AND user_id = auth.uid()
                    )
                )
            )
        )
    );

-- Template function to add multi-tenant columns to any table
CREATE OR REPLACE FUNCTION add_multi_tenant_columns(table_name TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('
        ALTER TABLE %I
            ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
            ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
            ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id),
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()
    ', table_name);
    
    -- Create indexes
    EXECUTE format('
        CREATE INDEX IF NOT EXISTS idx_%I_org_project 
        ON %I(organization_id, project_id)
    ', table_name, table_name);
    
    -- Add updated_at trigger
    EXECUTE format('
        CREATE TRIGGER update_%I_updated_at BEFORE UPDATE
        ON %I FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    ', table_name, table_name);
    
    -- Enable RLS
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);
END;
$$ LANGUAGE plpgsql;

-- List of agent tables to update (add more as needed)
-- SELECT add_multi_tenant_columns('agent_content_items');
-- SELECT add_multi_tenant_columns('agent_instagram_posts');
-- SELECT add_multi_tenant_columns('agent_visual_posts');
-- SELECT add_multi_tenant_columns('agent_videos');
-- SELECT add_multi_tenant_columns('agent_workflows');-- Add password storage to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email_password 
ON users(email) 
WHERE password_hash IS NOT NULL;

-- Update RLS policy to prevent password hash from being exposed
-- Drop existing select policy
DROP POLICY IF EXISTS users_select_own_policy ON users;

-- Create new select policy that excludes password_hash
CREATE POLICY users_select_own_policy ON users
    FOR SELECT USING (auth.uid() = id);

-- Note: We'll need to create a view that excludes password_hash for general queries
CREATE OR REPLACE VIEW users_safe AS
SELECT 
    id,
    email,
    name,
    avatar_url,
    auth_provider,
    auth_provider_id,
    email_verified,
    settings,
    last_login_at,
    created_at,
    updated_at,
    deleted_at
FROM users;

-- Grant access to the safe view
GRANT SELECT ON users_safe TO authenticated;

-- Create function for password verification (runs with security definer)
CREATE OR REPLACE FUNCTION verify_user_password(
    p_email TEXT,
    p_password_hash TEXT
) RETURNS TABLE (
    id UUID,
    email TEXT,
    name TEXT,
    avatar_url TEXT,
    email_verified BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id,
        u.email,
        u.name,
        u.avatar_url,
        u.email_verified,
        u.created_at,
        u.updated_at
    FROM users u
    WHERE u.email = p_email 
    AND u.password_hash = p_password_hash
    AND u.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function for user registration
CREATE OR REPLACE FUNCTION register_user(
    p_email TEXT,
    p_name TEXT,
    p_password_hash TEXT,
    p_auth_provider TEXT DEFAULT 'email'
) RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
BEGIN
    INSERT INTO users (
        email,
        name,
        password_hash,
        auth_provider,
        email_verified,
        created_at,
        updated_at
    ) VALUES (
        p_email,
        p_name,
        p_password_hash,
        p_auth_provider,
        FALSE,
        NOW(),
        NOW()
    ) RETURNING id INTO v_user_id;
    
    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;