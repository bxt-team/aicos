-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Create knowledge_bases table
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    department_id UUID REFERENCES departments(id) ON DELETE CASCADE,
    agent_type TEXT, -- e.g., 'qa_agent', 'affirmations_agent', etc.
    name TEXT NOT NULL,
    description TEXT,
    file_type TEXT NOT NULL, -- 'pdf', 'txt', 'json', 'csv', 'docx'
    file_name TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_path TEXT NOT NULL, -- Supabase storage path
    vector_store_id TEXT, -- Reference to vector database (e.g., FAISS index)
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    CONSTRAINT knowledge_base_scope_check CHECK (
        -- Must belong to at least organization
        organization_id IS NOT NULL
    ),
    CONSTRAINT knowledge_base_hierarchy_check CHECK (
        -- If agent_type is set, must have either project_id or department_id
        (agent_type IS NULL) OR 
        (agent_type IS NOT NULL AND (project_id IS NOT NULL OR department_id IS NOT NULL))
    ),
    CONSTRAINT knowledge_base_department_project_check CHECK (
        -- If department_id is set, project_id must also be set
        (department_id IS NULL) OR 
        (department_id IS NOT NULL AND project_id IS NOT NULL)
    )
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_org ON knowledge_bases(organization_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_project ON knowledge_bases(project_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_department ON knowledge_bases(department_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_agent ON knowledge_bases(agent_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_active ON knowledge_bases(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_hierarchy ON knowledge_bases(organization_id, project_id, department_id, agent_type);

-- Create updated_at trigger
CREATE TRIGGER update_knowledge_bases_updated_at BEFORE UPDATE
    ON knowledge_bases FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;

-- RLS Policies for knowledge_bases
-- Select: Users can see knowledge bases in their organizations
CREATE POLICY knowledge_bases_select_policy ON knowledge_bases
    FOR SELECT USING (
        organization_id IN (
            SELECT om.organization_id 
            FROM organization_members om
            WHERE om.user_id = auth.uid()
        )
    );

-- Insert: Users with admin/owner role can create knowledge bases
CREATE POLICY knowledge_bases_insert_policy ON knowledge_bases
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = NEW.organization_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
        AND (
            -- If project_id is set, verify user has access to that project
            NEW.project_id IS NULL OR
            EXISTS (
                SELECT 1 FROM projects p
                WHERE p.id = NEW.project_id
                AND p.organization_id = NEW.organization_id
            )
        )
        AND (
            -- If department_id is set, verify it belongs to the project
            NEW.department_id IS NULL OR
            EXISTS (
                SELECT 1 FROM departments d
                WHERE d.id = NEW.department_id
                AND d.project_id = NEW.project_id
            )
        )
    );

-- Update: Admin/owner can update knowledge bases
CREATE POLICY knowledge_bases_update_policy ON knowledge_bases
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = knowledge_bases.organization_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

-- Delete: Admin/owner can delete knowledge bases
CREATE POLICY knowledge_bases_delete_policy ON knowledge_bases
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = knowledge_bases.organization_id
            AND om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

-- Create knowledge_base_embeddings table for vector storage metadata
CREATE TABLE IF NOT EXISTS knowledge_base_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding_vector VECTOR(1536), -- OpenAI embeddings dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(knowledge_base_id, chunk_index)
);

-- Create indexes for embeddings
CREATE INDEX IF NOT EXISTS idx_embeddings_kb ON knowledge_base_embeddings(knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON knowledge_base_embeddings USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);

-- Enable Row Level Security
ALTER TABLE knowledge_base_embeddings ENABLE ROW LEVEL SECURITY;

-- RLS Policies for embeddings (inherit from knowledge_bases)
CREATE POLICY embeddings_select_policy ON knowledge_base_embeddings
    FOR SELECT USING (
        knowledge_base_id IN (
            SELECT kb.id FROM knowledge_bases kb
            JOIN organization_members om ON kb.organization_id = om.organization_id
            WHERE om.user_id = auth.uid()
        )
    );

CREATE POLICY embeddings_insert_policy ON knowledge_base_embeddings
    FOR INSERT WITH CHECK (
        knowledge_base_id IN (
            SELECT kb.id FROM knowledge_bases kb
            JOIN organization_members om ON kb.organization_id = om.organization_id
            WHERE om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

CREATE POLICY embeddings_update_policy ON knowledge_base_embeddings
    FOR UPDATE USING (
        knowledge_base_id IN (
            SELECT kb.id FROM knowledge_bases kb
            JOIN organization_members om ON kb.organization_id = om.organization_id
            WHERE om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

CREATE POLICY embeddings_delete_policy ON knowledge_base_embeddings
    FOR DELETE USING (
        knowledge_base_id IN (
            SELECT kb.id FROM knowledge_bases kb
            JOIN organization_members om ON kb.organization_id = om.organization_id
            WHERE om.user_id = auth.uid()
            AND om.role IN ('owner', 'admin')
        )
    );

-- Create function to get applicable knowledge bases for a specific context
CREATE OR REPLACE FUNCTION get_applicable_knowledge_bases(
    p_organization_id UUID,
    p_project_id UUID DEFAULT NULL,
    p_department_id UUID DEFAULT NULL,
    p_agent_type TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    name TEXT,
    file_type TEXT,
    scope_level TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        kb.id,
        kb.name,
        kb.file_type,
        CASE 
            WHEN kb.agent_type IS NOT NULL AND kb.department_id IS NOT NULL THEN 'agent_department'
            WHEN kb.agent_type IS NOT NULL AND kb.project_id IS NOT NULL THEN 'agent_project'
            WHEN kb.department_id IS NOT NULL THEN 'department'
            WHEN kb.project_id IS NOT NULL THEN 'project'
            ELSE 'organization'
        END AS scope_level
    FROM knowledge_bases kb
    WHERE kb.is_active = true
    AND kb.organization_id = p_organization_id
    AND (
        -- Organization level knowledge bases
        (kb.project_id IS NULL AND kb.department_id IS NULL AND kb.agent_type IS NULL)
        OR
        -- Project level knowledge bases (if project_id provided)
        (p_project_id IS NOT NULL AND kb.project_id = p_project_id AND kb.department_id IS NULL AND kb.agent_type IS NULL)
        OR
        -- Department level knowledge bases (if department_id provided)
        (p_department_id IS NOT NULL AND kb.department_id = p_department_id AND kb.agent_type IS NULL)
        OR
        -- Agent-specific knowledge bases at project level
        (p_project_id IS NOT NULL AND p_agent_type IS NOT NULL AND 
         kb.project_id = p_project_id AND kb.agent_type = p_agent_type AND kb.department_id IS NULL)
        OR
        -- Agent-specific knowledge bases at department level
        (p_department_id IS NOT NULL AND p_agent_type IS NOT NULL AND 
         kb.department_id = p_department_id AND kb.agent_type = p_agent_type)
    )
    ORDER BY 
        CASE 
            WHEN kb.agent_type IS NOT NULL AND kb.department_id IS NOT NULL THEN 1
            WHEN kb.agent_type IS NOT NULL AND kb.project_id IS NOT NULL THEN 2
            WHEN kb.department_id IS NOT NULL THEN 3
            WHEN kb.project_id IS NOT NULL THEN 4
            ELSE 5
        END;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION get_applicable_knowledge_bases TO authenticated;