# Rate Limit Countdown Implementation

This implementation provides a live countdown timer for rate limit error messages in authentication components.

## Overview

When users encounter rate limit errors (e.g., "For security purposes, you can only request this after 26 seconds"), the error message will automatically display a live countdown that updates every second.

## Components

### 1. `useRateLimitCountdown` Hook
Location: `/frontend/src/hooks/useRateLimitCountdown.ts`

A custom React hook that:
- Parses error messages to extract the wait time in seconds
- Manages a countdown timer that updates every second
- Provides formatted countdown messages
- Supports an optional callback when countdown completes

### 2. `RateLimitError` Component
Location: `/frontend/src/components/auth/RateLimitError.tsx`

For branded auth pages (uses custom CSS):
- Automatically detects rate limit errors
- Shows a spinner with live countdown
- Falls back to regular error display for non-rate limit errors

### 3. `RateLimitAlert` Component
Location: `/frontend/src/components/auth/RateLimitAlert.tsx`

For Material-UI based auth pages:
- Uses MUI Alert component
- Shows circular progress indicator with countdown
- Switches to warning severity for rate limit errors

## Supported Error Patterns

The implementation recognizes these error message patterns:
- "after X seconds"
- "wait X seconds"
- "in X seconds"
- "X seconds remaining"
- "retry in X seconds"

## Usage Example

```tsx
// In a branded auth component
<RateLimitError 
  error={displayError} 
  onCountdownComplete={() => {
    // Optional: Clear error or enable retry button
  }}
/>

// In a Material-UI auth component
<RateLimitAlert 
  error={validationError || error?.message} 
  sx={{ mt: 2 }}
  onCountdownComplete={() => {
    // Optional: Clear error or enable retry button
  }}
/>
```

## Updated Components

The following auth components have been updated to use the countdown:

### Branded Components:
- `BrandedSupabaseLogin.tsx`
- `BrandedForgotPassword.tsx`
- `BrandedSupabaseSignup.tsx`
- `BrandedResetPassword.tsx`

### Material-UI Components:
- `SupabaseLogin.tsx`
- `ForgotPassword.tsx`
- `SupabaseSignup.tsx`

## Testing

A demo component is available at `/frontend/src/components/auth/RateLimitErrorDemo.tsx` for testing different error messages and seeing the countdown in action.

## How It Works

1. When an error is set, the component checks if it matches a rate limit pattern
2. If it does, it extracts the seconds and starts a countdown
3. The countdown updates every second, showing "Please wait X seconds..."
4. When the countdown reaches 0, an optional callback is triggered
5. For non-rate limit errors, the original error message is displayed as-is