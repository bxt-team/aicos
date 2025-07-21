-- Create audit_logs table
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
$$ LANGUAGE plpgsql SECURITY DEFINER;