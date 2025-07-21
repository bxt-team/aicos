-- Template for updating existing agent tables with multi-tenant support
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
-- SELECT add_multi_tenant_columns('agent_workflows');