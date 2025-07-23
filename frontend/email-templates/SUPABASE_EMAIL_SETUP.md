# AICOS Email Templates - Supabase Setup Guide

This guide explains how to implement the AICOS branded email templates in your Supabase Dashboard.

## Overview

The email templates in this directory have been designed to match the AICOS brand identity with:
- AICOS logo and brand colors (#2f80ed primary blue)
- Professional gradient backgrounds
- Responsive design for mobile and desktop
- Dark mode support
- "Where AI runs your business." tagline

## Templates Included

1. **confirmation-email.html** - Email verification for new signups
2. **magic-link-email.html** - Passwordless login emails
3. **password-reset-email.html** - Password reset requests
4. **email-change-email.html** - Email address change confirmations

## Setup Instructions

### Step 1: Access Supabase Dashboard

1. Log in to your Supabase Dashboard at https://app.supabase.com
2. Select your project
3. Navigate to **Authentication** → **Email Templates** in the sidebar

### Step 2: Configure Email Templates

For each template type, you'll need to:

1. Select the template type from the dropdown
2. Toggle "Enable custom email" to ON
3. Copy the entire HTML content from the corresponding file
4. Paste it into the template editor
5. Click "Save"

### Step 3: Template Variables

Each template uses Supabase's template variables. Here's what's available for each:

#### Confirmation Email
- `{{ .ConfirmationURL }}` - The verification link
- `{{ .Email }}` - User's email address

#### Magic Link
- `{{ .MagicLink }}` - The magic link URL
- `{{ .Email }}` - User's email address
- `{{ .RequestLocation }}` - Location where request originated (optional)
- `{{ .RequestTime }}` - Time of request (optional)

#### Password Reset
- `{{ .ResetLink }}` - The password reset link
- `{{ .Email }}` - User's email address

#### Email Change
- `{{ .ConfirmationLink }}` - The confirmation link
- `{{ .OldEmail }}` - Current email address
- `{{ .NewEmail }}` - New email address

### Step 4: Logo Configuration

The templates reference a logo URL that needs to be updated:

1. Upload your logo to a public CDN or your Supabase Storage bucket
2. Replace `https://raw.githubusercontent.com/yourusername/aicos/main/logo.svg` with your actual logo URL in all templates

Alternatively, you can convert the logo to a base64 data URL:
1. Use a tool to convert your logo.svg to base64
2. Replace the logo src with: `data:image/svg+xml;base64,[your-base64-string]`

### Step 5: Email Settings

In **Authentication** → **Settings**:

1. Configure your SMTP settings if using custom SMTP
2. Set appropriate rate limits
3. Configure allowed email domains if needed
4. Set the "Site URL" for proper link generation

### Step 6: Testing

Before going live:

1. Use Supabase's "Send test email" feature
2. Test each template type:
   - Sign up with a new email
   - Request a magic link
   - Request a password reset
   - Change email address
3. Check rendering on different email clients
4. Verify links work correctly

## Customization Options

### Brand Colors
The main brand color `#2f80ed` is used throughout. To change:
- Find and replace `#2f80ed` with your primary color
- Update hover state `#2570dd` accordingly

### Typography
The templates use:
- Headers: Inter font
- Body: IBM Plex Sans font
- Fallback to system fonts for better compatibility

### Dark Mode
Templates include basic dark mode support. Email clients that support `prefers-color-scheme` will show adapted colors.

## Troubleshooting

### Images Not Loading
- Ensure logo URL is publicly accessible
- Consider using base64 encoding for better reliability
- Check Content Security Policy settings

### Styling Issues
- Some email clients strip certain CSS
- Inline styles are used for maximum compatibility
- Test in multiple email clients

### Variable Not Rendering
- Ensure you're using the exact variable syntax
- Check Supabase documentation for available variables
- Variables are case-sensitive

## Best Practices

1. **Keep HTML under 100KB** - Large emails may be clipped
2. **Test thoroughly** - Email rendering varies widely
3. **Use alt text** - Add descriptive alt text to images
4. **Monitor deliverability** - Check spam scores
5. **Update links** - Ensure all links use HTTPS

## Support

For issues with:
- **Templates**: Check this documentation
- **Supabase**: Refer to Supabase email documentation
- **Styling**: Test in email preview tools like Litmus or Email on Acid

## Additional Resources

- [Supabase Email Templates Docs](https://supabase.com/docs/guides/auth/auth-email-templates)
- [Email Client CSS Support](https://www.campaignmonitor.com/css/)
- [MJML Email Framework](https://mjml.io/) - For future template updates