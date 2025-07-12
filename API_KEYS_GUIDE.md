# API Keys Setup Guide for 7cycles-ai

This guide provides step-by-step instructions for obtaining all required API keys and tokens for the 7cycles-ai project.

## Required API Keys

### 1. OpenAI API Key
**Used for:** AI content generation, text processing, and language models

**Steps to obtain:**
1. Go to https://platform.openai.com/signup
2. Create an account or sign in
3. Navigate to https://platform.openai.com/api-keys
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)
6. Add to `.env`: `OPENAI_API_KEY=your-key-here`

**Pricing:** Pay-as-you-go, see https://openai.com/pricing

### 2. Pexels API Key
**Used for:** Image search and retrieval for visual content

**Steps to obtain:**
1. Go to https://www.pexels.com/join/
2. Create a free account
3. Navigate to https://www.pexels.com/api/
4. Click "Get Started" or "Your API Key"
5. Accept the terms and conditions
6. Copy your API key
7. Add to `.env`: `PEXELS_API_KEY=your-key-here`

**Pricing:** Free with rate limits (200 requests per hour, 20,000 per month)

### 3. ElevenLabs API Key
**Used for:** AI voice generation and text-to-speech

**Steps to obtain:**
1. Go to https://elevenlabs.io/
2. Click "Sign Up" and create an account
3. Navigate to your profile settings
4. Click on "API Keys" in the sidebar
5. Generate a new API key
6. Copy the key
7. Add to `.env`: `ELEVENLABS_API_KEY=your-key-here`

**Pricing:** Free tier available (10,000 characters/month), paid plans for more

### 4. Runway API Key
**Used for:** AI video generation

**Steps to obtain:**
1. Go to https://runwayml.com/
2. Create an account
3. Navigate to https://app.runwayml.com/
4. Go to Account Settings → API
5. Generate an API key
6. Copy the key
7. Add to `.env`: `RUNWAY_API_KEY=your-key-here`

**Note:** Runway API access may require a paid plan or special access request

### 5. Instagram Access Token & Business Account ID
**Used for:** Posting content to Instagram

**Prerequisites:**
- A Facebook Developer account
- An Instagram Business or Creator account
- A Facebook Page connected to your Instagram account

**Steps to obtain:**
1. **Create Facebook App:**
   - Go to https://developers.facebook.com/
   - Click "My Apps" → "Create App"
   - Choose "Business" type
   - Fill in app details

2. **Add Instagram Basic Display:**
   - In your app dashboard, click "Add Product"
   - Find "Instagram Basic Display" and click "Set Up"
   - Add Instagram Test Users

3. **Get Instagram Business Account ID:**
   - Go to Facebook Business Manager
   - Navigate to Business Settings → Instagram Accounts
   - Find your account and copy the ID

4. **Generate Access Token:**
   - Use Facebook Graph API Explorer: https://developers.facebook.com/tools/explorer/
   - Select your app
   - Request permissions: `instagram_basic`, `instagram_content_publish`, `pages_show_list`
   - Generate token
   - Exchange for long-lived token

5. **Add to `.env`:**
   ```
   INSTAGRAM_ACCESS_TOKEN=your-token-here
   INSTAGRAM_BUSINESS_ACCOUNT_ID=your-account-id-here
   ```

**Important:** Instagram tokens expire. You'll need to refresh them periodically.

### 6. Kling AI API Key (Optional)
**Used for:** Alternative AI video generation

**Steps to obtain:**
1. Go to https://klingai.com/
2. Sign up for an account
3. Navigate to API section in dashboard
4. Request API access (may require approval)
5. Once approved, generate API key
6. Add to `.env`: `KLINGAI_API_KEY=your-key-here`

**Note:** Kling AI API may have limited availability

### 7. ADB Path (Android Debug Bridge)
**Used for:** Android device testing and automation

**Steps to obtain:**
1. **Install Android Studio:**
   - Download from https://developer.android.com/studio
   - Install with default settings

2. **Locate ADB:**
   - **Windows:** `C:\Users\[username]\AppData\Local\Android\Sdk\platform-tools\adb.exe`
   - **macOS:** `/Users/[username]/Library/Android/sdk/platform-tools/adb`
   - **Linux:** `/home/[username]/Android/Sdk/platform-tools/adb`

3. **Alternative - Standalone installation:**
   - Download Platform Tools: https://developer.android.com/studio/releases/platform-tools
   - Extract to a directory
   - Use that path

4. **Add to `.env`:**
   ```
   ADB_PATH=/path/to/adb
   ```

## Environment File Setup

1. Copy the example file:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Fill in all the API keys obtained above

3. Additional optional configurations:
   ```
   # Redis configuration (if not using default)
   REDIS_HOST=localhost
   REDIS_PORT=6379
   
   # Frontend URL (if different from default)
   FRONTEND_URL=http://localhost:3000
   ```

## Verifying API Keys

After setting up all keys, you can verify them:

1. **Start the backend:**
   ```bash
   npm run dev-backend
   ```

2. **Check health endpoints:**
   - OpenAI: The Q&A agent should initialize without errors
   - Pexels: Try generating a visual post
   - ElevenLabs: Try generating audio
   - Instagram: Check Instagram posting endpoint

## Security Notes

- **Never commit** your `.env` file to version control
- Keep your API keys secure and rotate them regularly
- Use environment-specific keys for development/production
- Monitor API usage to avoid unexpected charges
- Some APIs have rate limits - implement proper error handling

## Troubleshooting

### Common Issues:
1. **"Invalid API Key" errors:** Double-check for extra spaces or missing characters
2. **Rate limit errors:** Check your API plan limits
3. **Instagram token expired:** Refresh using Graph API Explorer
4. **ADB not found:** Ensure path is absolute and adb is executable

### Getting Help:
- OpenAI: https://platform.openai.com/docs
- Pexels: https://www.pexels.com/api/documentation/
- ElevenLabs: https://docs.elevenlabs.io/
- Instagram API: https://developers.facebook.com/docs/instagram-api
- Runway: https://docs.runwayml.com/