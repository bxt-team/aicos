-- Create tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    priority VARCHAR(50) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    assigned_to_type VARCHAR(50) CHECK (assigned_to_type IN ('member', 'agent')),
    assigned_to_id UUID,
    created_by_type VARCHAR(50) NOT NULL DEFAULT 'user',
    created_by_id UUID,
    due_date DATE,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_tasks_goal_id ON tasks(goal_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to_type, assigned_to_id);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);

-- Enable RLS
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view tasks in their projects
CREATE POLICY tasks_select ON tasks
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM goals g
            JOIN projects p ON g.project_id = p.id
            JOIN project_members pm ON p.id = pm.project_id
            WHERE g.id = tasks.goal_id
            AND pm.user_id = auth.uid()::uuid
        )
    );

-- Policy: Users can create tasks in goals they have access to
CREATE POLICY tasks_insert ON tasks
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM goals g
            JOIN projects p ON g.project_id = p.id
            JOIN project_members pm ON p.id = pm.project_id
            WHERE g.id = goal_id
            AND pm.user_id = auth.uid()::uuid
            AND pm.role IN ('owner', 'admin', 'member')
        )
    );

-- Policy: Users can update tasks in their projects
CREATE POLICY tasks_update ON tasks
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM goals g
            JOIN projects p ON g.project_id = p.id
            JOIN project_members pm ON p.id = pm.project_id
            WHERE g.id = tasks.goal_id
            AND pm.user_id = auth.uid()::uuid
            AND pm.role IN ('owner', 'admin', 'member')
        )
    );

-- Policy: Users can delete tasks if they're owners/admins
CREATE POLICY tasks_delete ON tasks
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM goals g
            JOIN projects p ON g.project_id = p.id
            JOIN project_members pm ON p.id = pm.project_id
            WHERE g.id = tasks.goal_id
            AND pm.user_id = auth.uid()::uuid
            AND pm.role IN ('owner', 'admin')
        )
    );

-- Create task_history table
CREATE TABLE IF NOT EXISTS task_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    actor_type VARCHAR(50) NOT NULL,
    actor_id UUID,
    actor_name VARCHAR(255),
    old_value JSONB,
    new_value JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for task_history
CREATE INDEX idx_task_history_task_id ON task_history(task_id);
CREATE INDEX idx_task_history_created_at ON task_history(created_at DESC);

-- Enable RLS on task_history
ALTER TABLE task_history ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view history for tasks they have access to
CREATE POLICY task_history_select ON task_history
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM tasks t
            JOIN goals g ON t.goal_id = g.id
            JOIN projects p ON g.project_id = p.id
            JOIN project_members pm ON p.id = pm.project_id
            WHERE t.id = task_history.task_id
            AND pm.user_id = auth.uid()::uuid
        )
    );

-- Policy: System can insert history records
CREATE POLICY task_history_insert ON task_history
    FOR INSERT WITH CHECK (true);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_tasks_updated_at();

-- Function to log task changes
CREATE OR REPLACE FUNCTION log_task_changes()
RETURNS TRIGGER AS $$
DECLARE
    changes JSONB = '{}';
    old_val JSONB;
    new_val JSONB;
BEGIN
    -- Determine action
    IF TG_OP = 'INSERT' THEN
        INSERT INTO task_history (
            task_id, action, actor_type, actor_id, new_value, created_at
        ) VALUES (
            NEW.id, 'created', NEW.created_by_type, NEW.created_by_id, 
            jsonb_build_object(
                'title', NEW.title,
                'status', NEW.status,
                'priority', NEW.priority
            ),
            NOW()
        );
    ELSIF TG_OP = 'UPDATE' THEN
        -- Check what changed
        IF OLD.status IS DISTINCT FROM NEW.status THEN
            changes = changes || jsonb_build_object('status', jsonb_build_object('old', OLD.status, 'new', NEW.status));
        END IF;
        IF OLD.priority IS DISTINCT FROM NEW.priority THEN
            changes = changes || jsonb_build_object('priority', jsonb_build_object('old', OLD.priority, 'new', NEW.priority));
        END IF;
        IF OLD.assigned_to_id IS DISTINCT FROM NEW.assigned_to_id THEN
            changes = changes || jsonb_build_object('assigned_to', jsonb_build_object('old', OLD.assigned_to_id, 'new', NEW.assigned_to_id));
        END IF;
        IF OLD.due_date IS DISTINCT FROM NEW.due_date THEN
            changes = changes || jsonb_build_object('due_date', jsonb_build_object('old', OLD.due_date, 'new', NEW.due_date));
        END IF;
        
        -- Only log if something changed
        IF changes != '{}' THEN
            INSERT INTO task_history (
                task_id, action, actor_type, actor_id, old_value, created_at
            ) VALUES (
                NEW.id, 'updated', 'user', auth.uid()::uuid, changes, NOW()
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to log task changes
CREATE TRIGGER log_task_changes_trigger
    AFTER INSERT OR UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION log_task_changes();