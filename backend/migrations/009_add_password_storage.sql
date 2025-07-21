-- Add password storage to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email_password 
ON users(email) 
WHERE password_hash IS NOT NULL;

-- Update RLS policy to prevent password hash from being exposed
-- Drop existing select policy
DROP POLICY IF EXISTS users_select_own_policy ON users;

-- Create new select policy that excludes password_hash
CREATE POLICY users_select_own_policy ON users
    FOR SELECT USING (auth.uid() = id);

-- Note: We'll need to create a view that excludes password_hash for general queries
CREATE OR REPLACE VIEW users_safe AS
SELECT 
    id,
    email,
    name,
    avatar_url,
    auth_provider,
    auth_provider_id,
    email_verified,
    settings,
    last_login_at,
    created_at,
    updated_at,
    deleted_at
FROM users;

-- Grant access to the safe view
GRANT SELECT ON users_safe TO authenticated;

-- Create function for password verification (runs with security definer)
CREATE OR REPLACE FUNCTION verify_user_password(
    p_email TEXT,
    p_password_hash TEXT
) RETURNS TABLE (
    id UUID,
    email TEXT,
    name TEXT,
    avatar_url TEXT,
    email_verified BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id,
        u.email,
        u.name,
        u.avatar_url,
        u.email_verified,
        u.created_at,
        u.updated_at
    FROM users u
    WHERE u.email = p_email 
    AND u.password_hash = p_password_hash
    AND u.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function for user registration
CREATE OR REPLACE FUNCTION register_user(
    p_email TEXT,
    p_name TEXT,
    p_password_hash TEXT,
    p_auth_provider TEXT DEFAULT 'email'
) RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
BEGIN
    INSERT INTO users (
        email,
        name,
        password_hash,
        auth_provider,
        email_verified,
        created_at,
        updated_at
    ) VALUES (
        p_email,
        p_name,
        p_password_hash,
        p_auth_provider,
        FALSE,
        NOW(),
        NOW()
    ) RETURNING id INTO v_user_id;
    
    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;