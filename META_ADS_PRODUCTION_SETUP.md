# Meta Ads Production Setup Guide

This guide explains how to set up the Meta Ads Analytics Tool for production use with real-time data from the Meta Marketing API.

## Prerequisites

1. **Meta Business Account**: You need a Meta Business account with access to the ad accounts you want to analyze.
2. **Meta App**: Create a Meta app in the [Meta for Developers](https://developers.facebook.com/) portal.
3. **Ad Account Access**: Ensure your Meta app has access to the ad accounts containing the campaigns you want to analyze.

## Step 1: Create a Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Choose "Business" as the app type
4. Fill in the app details:
   - App Name: "7 Cycles Analytics" (or your preferred name)
   - App Contact Email: Your email
   - Business Account: Select your business account
5. Add the "Marketing API" product to your app

## Step 2: Configure App Permissions

1. In your app dashboard, go to "App Review" → "Permissions and Features"
2. Request the following permissions:
   - `ads_read` - Read access to ads
   - `ads_management` - Manage ads (if you need write access)
   - `business_management` - Manage business
   - `pages_read_engagement` - Read page engagement
   - `pages_show_list` - Show list of pages

## Step 3: Get Your Credentials

1. **App ID**: Found in your app's Basic Settings
2. **App Secret**: Found in your app's Basic Settings (click "Show")
3. **Access Token**: 
   - Go to [Meta Business Suite](https://business.facebook.com/)
   - Navigate to "Business Settings" → "System Users"
   - Create a system user or use existing one
   - Generate a system user access token with the required permissions
   - **Important**: For production, use a long-lived system user token, not a user access token
4. **Ad Account ID**: 
   - Go to Meta Ads Manager
   - The account ID is in the account dropdown (format: act_123456789)

## Step 4: Configure Environment Variables

Add these to your `.env` file:

```bash
# Meta Marketing API Configuration
META_APP_ID=your_app_id_here
META_APP_SECRET=your_app_secret_here
META_AD_ACCOUNT_ID=act_123456789  # Include the 'act_' prefix

# Optional: Default access token (not recommended for production)
# META_ACCESS_TOKEN=your_system_user_token_here
```

## Step 5: Install Dependencies

The Meta Business SDK is already added to requirements.txt:

```bash
cd backend
pip install -r requirements.txt
```

## Step 6: Using the Production API

### Option 1: Pass Access Token with Each Request (Recommended)

```bash
curl -X POST "http://localhost:8000/api/mobile-analytics/meta-ads/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "120227656917790066",
    "access_token": "your_access_token_here",
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    }
  }'
```

### Option 2: Use Frontend Interface

The frontend interface now includes an "Access Token" field when production mode is detected. Users can enter their access token along with the campaign ID.

## Step 7: Access Token Management

### Generating Long-Lived Tokens

1. **System User Token** (Recommended for server-side apps):
   ```bash
   # These tokens don't expire and are ideal for server applications
   # Generate via Business Manager → System Users
   ```

2. **Page Access Token** (For page-specific data):
   ```bash
   # Exchange short-lived user token for long-lived page token
   GET https://graph.facebook.com/v18.0/oauth/access_token?
     grant_type=fb_exchange_token&
     client_id={app-id}&
     client_secret={app-secret}&
     fb_exchange_token={short-lived-token}
   ```

### Token Security Best Practices

1. **Never commit tokens to version control**
2. **Use environment variables or secure key management systems**
3. **Implement token rotation for enhanced security**
4. **Monitor token usage and set up alerts for unusual activity**
5. **Use IP whitelisting in Meta App settings for additional security**

## Step 8: API Rate Limits

The Meta Marketing API has rate limits. The production implementation includes:

1. **Automatic retry logic** for rate limit errors
2. **Exponential backoff** for failed requests
3. **Error handling** with meaningful messages

### Rate Limit Guidelines:
- **Standard**: 200 calls per hour per ad account
- **Development**: Lower limits during development
- **Batch requests**: Use batch API for multiple operations

## Step 9: Testing Production Mode

1. **Check if production mode is available**:
   ```python
   # The tool will log whether it's in PRODUCTION or MOCK mode
   # Check backend logs for: "Meta Ads Tool initialized in PRODUCTION mode"
   ```

2. **Test with a real campaign**:
   ```bash
   # Get a real campaign ID from your Meta Ads Manager
   # Use the format: 120227656917790066 (numeric ID without act_ prefix)
   ```

3. **Verify data accuracy**:
   - Compare results with Meta Ads Manager
   - Check that metrics match
   - Verify date ranges are correct

## Step 10: Monitoring and Debugging

### Enable Debug Logging

```python
# In your .env file
LOG_LEVEL=DEBUG
```

### Common Issues and Solutions

1. **"Invalid OAuth 2.0 Access Token"**
   - Token has expired
   - Token doesn't have required permissions
   - Solution: Generate a new token with correct permissions

2. **"Application does not have permission for this action"**
   - App lacks required permissions
   - Solution: Request permissions in App Review

3. **"Invalid parameter"**
   - Campaign ID format is wrong
   - Solution: Use numeric campaign ID without prefixes

4. **"Rate limit exceeded"**
   - Too many API calls
   - Solution: Implement caching or reduce call frequency

## Production Features

The production implementation provides:

1. **Real-time campaign data** directly from Meta's servers
2. **Detailed performance metrics** including:
   - Impressions, clicks, CTR, CPC, CPM
   - Installs and cost per install
   - Reach and frequency
   - Conversion tracking

3. **Ad Set level analysis** with:
   - Targeting details
   - Performance by audience segment
   - Budget allocation insights

4. **Creative performance** including:
   - Format-specific metrics (video, image, carousel)
   - Creative fatigue detection
   - Engagement rates

5. **Actionable insights** with:
   - Performance ratings
   - Optimization recommendations
   - Budget reallocation suggestions

## Security Considerations

1. **Access Token Storage**:
   - Never store access tokens in code
   - Use environment variables or secure vaults
   - Implement token encryption at rest

2. **API Communication**:
   - All Meta API calls use HTTPS
   - Implement request signing if required
   - Log API calls but never log tokens

3. **User Permissions**:
   - Implement role-based access control
   - Audit token usage
   - Revoke unused tokens

## Support and Resources

- [Meta Marketing API Documentation](https://developers.facebook.com/docs/marketing-apis)
- [Meta Business Help Center](https://www.facebook.com/business/help)
- [API Changelog](https://developers.facebook.com/docs/marketing-api/changelog)
- [Rate Limiting Guide](https://developers.facebook.com/docs/graph-api/overview/rate-limiting)

## No Mock Mode Available

**Important**: The Meta Ads tool now operates in production mode only:
- Valid Meta API credentials are required
- Access token must be provided with each request
- The system will return errors if credentials are missing
- No test or mock data is available

This ensures that all analytics are based on real, accurate campaign data.