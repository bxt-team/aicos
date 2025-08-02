-- Fix department_assignments_view to use users table instead of auth.users
-- This is necessary because assignments reference the public users table IDs

-- Drop the existing view
DROP VIEW IF EXISTS department_assignments_view;

-- Recreate the view with correct table references
CREATE OR REPLACE VIEW department_assignments_view AS
SELECT 
    da.*,
    d.name as department_name,
    d.description as department_description,
    p.name as project_name,
    p.organization_id,
    CASE 
        WHEN da.assignee_type = 'member' THEN u.email
        ELSE NULL
    END as member_email,
    CASE 
        WHEN da.assignee_type = 'member' THEN u.name
        ELSE NULL
    END as member_full_name
FROM department_assignments da
JOIN departments d ON da.department_id = d.id
JOIN projects p ON d.project_id = p.id
LEFT JOIN users u ON da.assignee_type = 'member' AND da.assignee_id = u.id;

-- Grant permissions on the view
GRANT SELECT ON department_assignments_view TO authenticated;