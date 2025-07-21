-- Create api_keys table
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
    );