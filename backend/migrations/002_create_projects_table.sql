-- Create projects table
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
    FOR DELETE USING (true);