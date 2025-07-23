-- Migration to add created_by columns to organizations and projects tables

-- Add created_by column to organizations table
ALTER TABLE organizations
ADD COLUMN created_by UUID REFERENCES auth.users(id);

-- Add created_by column to projects table  
ALTER TABLE projects
ADD COLUMN created_by UUID REFERENCES auth.users(id);

-- Optional: Add indexes for better query performance
CREATE INDEX idx_organizations_created_by ON organizations(created_by);
CREATE INDEX idx_projects_created_by ON projects(created_by);

-- Optional: Update existing rows to set created_by to the first admin/owner
-- This is just an example - adjust based on your needs
-- UPDATE organizations o
-- SET created_by = (
--     SELECT user_id 
--     FROM organization_members om
--     WHERE om.organization_id = o.id 
--     AND om.role = 'owner'
--     ORDER BY om.created_at ASC
--     LIMIT 1
-- );

-- UPDATE projects p
-- SET created_by = (
--     SELECT created_by 
--     FROM organizations o
--     WHERE o.id = p.organization_id
-- );