-- Create ideas table
CREATE TABLE IF NOT EXISTS ideas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE, -- NULL for company-level ideas
  user_id UUID NOT NULL REFERENCES auth.users(id),
  title TEXT NOT NULL,
  initial_description TEXT NOT NULL,
  refined_description TEXT,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'refining', 'validated', 'rejected', 'converted')),
  validation_score DECIMAL(3,2), -- 0.00 to 1.00
  validation_reasons JSONB,
  conversation_history JSONB DEFAULT '[]'::jsonb,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create idea_tasks junction table
CREATE TABLE IF NOT EXISTS idea_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  idea_id UUID NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
  task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(idea_id, task_id)
);

-- Create indexes
CREATE INDEX idx_ideas_organization_id ON ideas(organization_id);
CREATE INDEX idx_ideas_project_id ON ideas(project_id);
CREATE INDEX idx_ideas_user_id ON ideas(user_id);
CREATE INDEX idx_ideas_status ON ideas(status);
CREATE INDEX idx_ideas_created_at ON ideas(created_at);
CREATE INDEX idx_idea_tasks_idea_id ON idea_tasks(idea_id);
CREATE INDEX idx_idea_tasks_task_id ON idea_tasks(task_id);

-- Enable RLS
ALTER TABLE ideas ENABLE ROW LEVEL SECURITY;
ALTER TABLE idea_tasks ENABLE ROW LEVEL SECURITY;

-- RLS Policies for ideas table
-- Users can view ideas in their organizations
CREATE POLICY "Users can view ideas in their organizations" ON ideas
  FOR SELECT USING (
    organization_id IN (
      SELECT organization_id FROM organization_users 
      WHERE user_id = auth.uid()
    )
  );

-- Users can create ideas in their organizations
CREATE POLICY "Users can create ideas in their organizations" ON ideas
  FOR INSERT WITH CHECK (
    organization_id IN (
      SELECT organization_id FROM organization_users 
      WHERE user_id = auth.uid()
    ) AND user_id = auth.uid()
  );

-- Users can update their own ideas
CREATE POLICY "Users can update their own ideas" ON ideas
  FOR UPDATE USING (
    user_id = auth.uid() AND
    organization_id IN (
      SELECT organization_id FROM organization_users 
      WHERE user_id = auth.uid()
    )
  );

-- Users can delete their own ideas if not converted
CREATE POLICY "Users can delete their own non-converted ideas" ON ideas
  FOR DELETE USING (
    user_id = auth.uid() AND 
    status != 'converted' AND
    organization_id IN (
      SELECT organization_id FROM organization_users 
      WHERE user_id = auth.uid()
    )
  );

-- RLS Policies for idea_tasks table
-- Users can view idea_tasks for ideas in their organizations
CREATE POLICY "Users can view idea_tasks in their organizations" ON idea_tasks
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM ideas 
      WHERE ideas.id = idea_tasks.idea_id 
      AND ideas.organization_id IN (
        SELECT organization_id FROM organization_users 
        WHERE user_id = auth.uid()
      )
    )
  );

-- Users can create idea_tasks for their own ideas
CREATE POLICY "Users can create idea_tasks for their own ideas" ON idea_tasks
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM ideas 
      WHERE ideas.id = idea_tasks.idea_id 
      AND ideas.user_id = auth.uid()
    )
  );

-- Users can delete idea_tasks for their own ideas
CREATE POLICY "Users can delete idea_tasks for their own ideas" ON idea_tasks
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM ideas 
      WHERE ideas.id = idea_tasks.idea_id 
      AND ideas.user_id = auth.uid()
    )
  );

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_ideas_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at
CREATE TRIGGER update_ideas_updated_at
  BEFORE UPDATE ON ideas
  FOR EACH ROW
  EXECUTE FUNCTION update_ideas_updated_at();

-- Grant permissions
GRANT ALL ON ideas TO authenticated;
GRANT ALL ON idea_tasks TO authenticated;