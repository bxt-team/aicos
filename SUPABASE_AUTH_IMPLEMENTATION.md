# Supabase Authentication Implementation Guide

This guide documents the complete Supabase authentication implementation for the aicos project, supporting all authentication methods including email/password, magic links, OAuth providers (Google, GitHub, Apple), and 2FA.

## Overview

The implementation provides:
- ✅ Email/Password authentication
- ✅ Magic link (passwordless) authentication  
- ✅ OAuth providers (Google, GitHub, Apple)
- ✅ Password reset functionality
- ✅ Two-factor authentication (2FA) with TOTP
- ✅ Protected routes and auth guards
- ✅ Backend JWT validation
- ✅ Hybrid auth support (migration from legacy system)

## Frontend Implementation

### 1. Supabase Client Setup

**File:** `frontend/src/lib/supabase.ts`
```typescript
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
    flowType: 'pkce',
  },
})
```

### 2. Auth Context

**File:** `frontend/src/contexts/SupabaseAuthContext.tsx`

Provides a complete auth context with all authentication methods:
- `signUp()` - Email/password registration
- `signIn()` - Email/password login
- `signInWithMagicLink()` - Passwordless login
- `signInWithGoogle/GitHub/Apple()` - OAuth providers
- `resetPassword()` - Send password reset email
- `updatePassword()` - Update password after reset
- MFA methods: `enrollMFA()`, `verifyMFA()`, `unenrollMFA()`

### 3. Auth Components

#### Login Component
**File:** `frontend/src/components/auth/SupabaseLogin.tsx`
- Tabbed interface for password and magic link login
- OAuth provider buttons
- Links to signup and password reset

#### Signup Component
**File:** `frontend/src/components/auth/SupabaseSignup.tsx`
- Email/password registration
- Password confirmation
- OAuth provider options

#### Password Reset
**Files:** 
- `frontend/src/components/auth/ForgotPassword.tsx` - Request reset link
- `frontend/src/components/auth/ResetPassword.tsx` - Set new password

#### 2FA Components
**Files:**
- `frontend/src/components/auth/MFAEnroll.tsx` - Enroll/manage 2FA
- `frontend/src/components/auth/MFAChallenge.tsx` - Verify 2FA code

#### Other Components
- `frontend/src/components/auth/AuthGuard.tsx` - Protected route wrapper
- `frontend/src/components/auth/AuthCallback.tsx` - OAuth callback handler
- `frontend/src/components/auth/AccountSettings.tsx` - User account management

### 4. Environment Variables

Add to your `.env` file:
```bash
REACT_APP_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your_anon_key_here
```

### 5. Usage Example

```typescript
// In your App.tsx
import { SupabaseAuthProvider } from './contexts/SupabaseAuthContext'
import { AuthGuard } from './components/auth/AuthGuard'

function App() {
  return (
    <SupabaseAuthProvider>
      <Routes>
        <Route path="/login" element={<SupabaseLogin />} />
        <Route path="/signup" element={<SupabaseSignup />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/dashboard" element={
          <AuthGuard>
            <Dashboard />
          </AuthGuard>
        } />
        <Route path="/secure-area" element={
          <AuthGuard requireMFA={true}>
            <SecureContent />
          </AuthGuard>
        } />
      </Routes>
    </SupabaseAuthProvider>
  )
}
```

## Backend Implementation

### 1. Supabase Auth Middleware

**File:** `backend/app/core/supabase_auth.py`

Provides JWT validation for Supabase tokens:
- `SupabaseAuth` - Main auth handler
- `get_current_user()` - Extract user from JWT
- `require_mfa()` - Require 2FA verification
- `get_user_from_supabase()` - Fetch user details

### 2. Auth Adapter (Migration Support)

**File:** `backend/app/core/auth_adapter.py`

Supports both legacy JWT and Supabase auth during migration:
- `get_current_user_hybrid()` - Try Supabase first, fall back to legacy
- `require_authenticated_user()` - Require auth from either system
- `migrate_endpoint_to_supabase()` - Decorator for gradual migration

### 3. Example Protected Routes

**File:** `backend/app/api/routers/supabase_protected.py`

```python
from app.core.supabase_auth import get_current_user, require_mfa

@router.get("/me")
async def get_current_user_info(
    user: Dict[str, Any] = Depends(get_current_user)
):
    return {"user_id": user["user_id"], "email": user["email"]}

@router.get("/secure")
async def secure_endpoint(
    user: Dict[str, Any] = Depends(require_mfa)
):
    return {"message": "MFA verified"}
```

### 4. Migration Strategy

For existing endpoints, use the auth adapter:

```python
from app.core.auth_adapter import require_authenticated_user

@router.get("/legacy-endpoint")
async def my_endpoint(
    user: User = Depends(require_authenticated_user)
):
    # Works with both auth systems
    return {"user": user.email}
```

## Supabase Dashboard Configuration

### 1. Enable Authentication Providers

1. Go to Authentication > Providers in Supabase Dashboard
2. Enable:
   - Email (enabled by default)
   - Google OAuth
   - GitHub OAuth  
   - Apple OAuth

### 2. Configure OAuth Providers

For each provider, you'll need:
- **Google**: Client ID and Secret from Google Cloud Console
- **GitHub**: OAuth App Client ID and Secret
- **Apple**: Service ID, Team ID, Key ID, and Private Key

### 3. Configure Redirect URLs

Add to allowed redirect URLs:
- `http://localhost:3000/auth/callback`
- `https://your-domain.com/auth/callback`

### 4. Email Templates

Customize email templates for:
- Confirmation emails
- Magic link emails
- Password reset emails

## Security Considerations

### 1. Environment Variables

Never commit credentials. Use environment variables:
```bash
# Frontend (.env)
REACT_APP_SUPABASE_URL=...
REACT_APP_SUPABASE_ANON_KEY=...

# Backend (.env)
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_KEY=...
```

### 2. Row Level Security (RLS)

Enable RLS on all tables and create policies:
```sql
-- Example: Users can only see their own data
CREATE POLICY "Users can view own data" ON user_content
  FOR SELECT USING (auth.uid() = user_id);
```

### 3. MFA Enforcement

For sensitive operations, require MFA:
```typescript
// Frontend
<AuthGuard requireMFA={true}>
  <SensitiveComponent />
</AuthGuard>

// Backend
@router.post("/sensitive-action")
async def sensitive_action(user = Depends(require_mfa)):
    ...
```

## Testing

### Manual Testing Checklist

- [ ] Sign up with email/password
- [ ] Confirm email
- [ ] Sign in with email/password
- [ ] Sign in with magic link
- [ ] Sign in with Google
- [ ] Sign in with GitHub
- [ ] Sign in with Apple
- [ ] Reset password flow
- [ ] Enable 2FA
- [ ] Sign in with 2FA
- [ ] Disable 2FA
- [ ] Protected routes redirect to login
- [ ] MFA-required routes prompt for 2FA

### Common Issues

1. **OAuth redirect issues**: Ensure redirect URLs are correctly configured
2. **JWT validation fails**: Check that you're using the correct Supabase keys
3. **MFA QR code not working**: Ensure frontend URL is correct in QR generation
4. **Magic links not working**: Check email settings and spam folders

## Next Steps

1. **Migration Plan**: Gradually migrate existing users
2. **Enhanced Security**: Add device tracking, session management
3. **Social Features**: Link multiple auth providers to one account
4. **Analytics**: Track auth events and user behavior
5. **Compliance**: Add GDPR-compliant data handling

## Resources

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Supabase JavaScript Client](https://supabase.com/docs/reference/javascript/auth-signup)
- [JWT.io](https://jwt.io/) - Debug JWTs
- [2FA Apps](https://authy.com/, https://1password.com/)