# Supabase Authentication Fix Guide

## Issues Identified and Fixed

### 1. **Supabase Client Configuration**
- Added proper storage configuration
- Added debug mode for development
- Ensured PKCE flow is properly configured

### 2. **Auth Callback Handler**
- Enhanced to handle both OAuth code exchange and hash fragments
- Added proper error handling and logging
- Fixed session establishment from magic links and password reset tokens

### 3. **Password Reset Flow**
- Fixed token validation in BrandedResetPassword component
- Added proper session establishment from recovery tokens
- Enhanced error messages for expired/invalid tokens

### 4. **Debug Tool**
- Created AuthDebug component at `/auth-debug` for testing
- Allows testing magic links and password reset flows
- Shows current configuration and session status

## Required Supabase Configuration

### 1. Add these URLs to your Supabase project's redirect URLs:

Go to your Supabase Dashboard > Authentication > URL Configuration and add:

```
http://localhost:3000
http://localhost:3000/auth/callback
http://localhost:3000/reset-password
```

If you have a production domain, also add:
```
https://yourdomain.com
https://yourdomain.com/auth/callback
https://yourdomain.com/reset-password
```

### 2. Email Template Configuration (if needed)

For Magic Links, ensure your email template includes:
```html
<h2>Magic Link</h2>
<p>Follow this link to login:</p>
<p><a href="{{ .ConfirmationURL }}">Log In</a></p>
```

For Password Reset, ensure your email template includes:
```html
<h2>Reset Password</h2>
<p>Follow this link to reset the password for your user:</p>
<p><a href="{{ .ConfirmationURL }}">Reset Password</a></p>
```

## Testing the Fixes

1. **Test Magic Link:**
   - Go to `/auth-debug`
   - Click "Test Magic Link"
   - Enter an email address
   - Check email and click the link
   - Watch browser console for debug logs

2. **Test Password Reset:**
   - Go to `/auth-debug`
   - Click "Test Password Reset"
   - Enter an email address
   - Check email and click the link
   - You should be redirected to the password reset form

3. **Test Regular Login:**
   - Go to `/login`
   - Enter email and password
   - Should log in successfully

## Common Issues and Solutions

### "Token has expired or is invalid"
- Email links are single-use only
- If clicked twice, they become invalid
- Request a new link

### Redirected back to login after clicking email link
- Check browser console for errors
- Ensure redirect URLs are properly configured in Supabase
- Clear browser cache and cookies

### Session not persisting
- Check localStorage for `supabase.auth.token`
- Ensure cookies are not blocked
- Try clearing all sessions with the debug tool

## Environment Variables

Ensure these are set in your `.env` file:
```
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key
```

## Browser Console Commands for Debugging

```javascript
// Check current session
const { data: { session } } = await supabase.auth.getSession()
console.log('Current session:', session)

// Check auth state
supabase.auth.onAuthStateChange((event, session) => {
  console.log('Auth event:', event, session)
})

// Manually sign out
await supabase.auth.signOut()

// Clear all auth data
localStorage.clear()
sessionStorage.clear()
```