-- Add enhanced_data column to projects table
ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS enhanced_data JSONB DEFAULT NULL;

-- Add comment for documentation
COMMENT ON COLUMN projects.enhanced_data IS 'AI-generated enhanced project data including objectives, KPIs, milestones, etc.';