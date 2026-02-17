# Deployment Guide

This document provides deployment instructions for the Spotify Data Tool, with a focus on serverless platforms.

## Session-Based State Management

The application uses **session-based state management** via secure cookies to ensure it works correctly in serverless environments where application state is not shared across instances.

### How It Works

1. When a user uploads their Spotify data, the application:
   - Extracts the data to a temporary directory
   - Creates a unique session ID
   - Signs the session ID using a secret key
   - Stores the session cookie in the user's browser

2. On subsequent requests:
   - The session cookie is sent with each request
   - The session ID is verified using the secret key
   - The user's data is loaded based on the session ID
   - Any serverless instance can handle the request

### Security Features

- **Signed Cookies**: Session IDs are signed using `itsdangerous` to prevent tampering
- **HttpOnly**: Cookies are marked HttpOnly to prevent JavaScript access
- **Secure Flag**: Automatically enabled in production (HTTPS) environments
- **SameSite Protection**: Set to "lax" for CSRF protection
- **7-Day Expiration**: Sessions expire after 7 days via cookie expiration

## Environment Variables

### Required for Production/Serverless

#### `SESSION_SECRET_KEY` (REQUIRED)

**Critical**: This must be set in all serverless deployments to ensure session cookies are valid across all instances.

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Set it in your deployment platform:
- **Vercel**: Add to environment variables in project settings
- **AWS Lambda**: Set in function configuration
- **Azure Functions**: Add to application settings

**Without this variable**, the application will fail to start in serverless environments.

### Optional

#### Local Development

When `SESSION_SECRET_KEY` is not set and the app is not running in a detected serverless environment, a random key is generated with a warning. This is fine for local development but **not suitable for production**.

## Deployment Platforms

### Vercel

1. Set environment variable:
   ```
   SESSION_SECRET_KEY=<your-secret-key>
   ```

2. Deploy using the included `vercel.json` configuration

3. The application will automatically:
   - Detect the Vercel environment
   - Enable secure cookies (HTTPS)
   - Use the shared secret key

### AWS Lambda

1. Set environment variable in Lambda function configuration:
   ```
   SESSION_SECRET_KEY=<your-secret-key>
   ```

2. Deploy your function

3. The application will automatically detect the Lambda environment

### Azure Functions

1. Add application setting:
   ```
   SESSION_SECRET_KEY=<your-secret-key>
   ```

2. Deploy your function

3. The application will automatically detect the Azure Functions environment

## Local Development

For local development, you don't need to set `SESSION_SECRET_KEY`. The application will:
- Generate a random key automatically
- Show a warning in logs
- Work correctly for single-instance testing

To test with a consistent key locally:
```bash
export SESSION_SECRET_KEY="local-dev-key-not-for-production"
python main.py
```

## Session Management

### Session Lifecycle

- **Creation**: When user uploads data
- **Expiration**: 7 days (cookie-based)
- **Cleanup**: On explicit reset or server shutdown
- **Invalid Session Handling**: Automatically cleaned up if data directory is missing

### Stateless Design

The session management is designed for stateless serverless architectures:
- Session data is stored in-memory per instance
- Cookie expiration handles session timeout
- No server-side session storage or database required
- Each serverless instance can serve any user with a valid cookie

### Limitations

- Sessions are per-user and not shared between users
- Uploading new data creates a new session (doesn't replace the old one automatically)
- Old sessions persist until cookie expires or user resets
- In serverless, temp directories are ephemeral and may be cleaned up by the platform

## Troubleshooting

### "SESSION_SECRET_KEY environment variable is required"

**Cause**: Running in a serverless environment without SESSION_SECRET_KEY set.

**Solution**: Set the SESSION_SECRET_KEY environment variable in your deployment platform.

### "No data loaded" errors in production

**Cause**: Likely due to missing or mismatched SESSION_SECRET_KEY across instances.

**Solution**: 
1. Verify SESSION_SECRET_KEY is set in environment variables
2. Ensure all instances use the same key
3. Check that cookies are being sent (browser developer tools)

### Cookies not working locally

**Cause**: Browser may be blocking cookies for localhost.

**Solution**:
- Use 127.0.0.1 instead of localhost
- Check browser console for cookie warnings
- Ensure you're not in incognito/private mode with strict settings

### Session expires too quickly

**Cause**: Cookie max_age is set to 7 days.

**Solution**: Adjust the `max_age` parameter in `main.py` line 243 if needed. Note that in serverless environments, temp directories may not persist this long.

## Testing

Run the test suite:
```bash
python -m pytest tests/test_upload.py -v
```

All tests should pass (17/17 for upload tests).

## Monitoring

Monitor for:
- Failed session verification (check logs for "Invalid session token signature")
- Missing SESSION_SECRET_KEY errors (app won't start)
- Orphaned temp directories (in long-running instances)

## Best Practices

1. **Always set SESSION_SECRET_KEY** in production
2. **Use HTTPS** in production (secure flag requires it)
3. **Monitor disk usage** for temp directories
4. **Consider implementing** server-side session expiration for long-lived deployments
5. **Keep the secret key secret** - don't commit it to version control

## Security Considerations

- Session IDs are cryptographically signed
- Cookies are httpOnly (JavaScript can't access)
- Secure flag ensures HTTPS-only transmission in production
- SameSite=lax provides CSRF protection
- No sensitive data is stored in cookies (only signed session ID)

## Support

For issues related to session management or deployment, check:
1. Application logs for warnings/errors
2. Browser console for cookie-related issues
3. Environment variable configuration
4. Serverless platform-specific logs
