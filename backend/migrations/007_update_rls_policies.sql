-- Update RLS policies after all tables are created

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
$$ LANGUAGE plpgsql SECURITY DEFINER;