-- Fix register_user function to return proper structure
CREATE OR REPLACE FUNCTION register_user(
    p_email TEXT,
    p_name TEXT,
    p_password_hash TEXT,
    p_auth_provider TEXT DEFAULT 'email'
) RETURNS TABLE (user_id UUID) AS $$
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
    
    RETURN QUERY SELECT v_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create get_user_for_login function
CREATE OR REPLACE FUNCTION get_user_for_login(
    p_email TEXT
) RETURNS TABLE (
    id UUID,
    email TEXT,
    name TEXT,
    password_hash TEXT,
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
        u.password_hash,
        u.avatar_url,
        u.email_verified,
        u.created_at,
        u.updated_at
    FROM users u
    WHERE u.email = p_email 
    AND u.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- IMPORTANT: Note about auth.users relationship
-- This application uses its own users table (public.users) for user management
-- instead of relying on Supabase Auth (auth.users). This means:
-- 1. Users are created directly in public.users via the register_user function
-- 2. Authentication is handled by custom JWT tokens, not Supabase Auth
-- 3. There is NO foreign key constraint to auth.users
-- 4. The auth.uid() function in RLS policies references the custom JWT user ID

-- If you want to integrate with Supabase Auth in the future, you would need to:
-- 1. Create a trigger on auth.users to sync with public.users
-- 2. Update the RLS policies to use proper auth.uid() from Supabase Auth
-- 3. Modify the authentication flow to use Supabase Auth signUp/signIn