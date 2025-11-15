# Vercel Deployment Guide

## Issues Fixed

1. **Removed FastAPI lifespan events** - Vercel serverless functions don't support lifespan events properly
2. **Added database connection middleware** - Database connections are now handled per request for serverless compatibility
3. **Simplified entry point** - The `api/index.py` now exports the FastAPI app directly
4. **Added function timeout** - Set maxDuration to 30 seconds in vercel.json

## Environment Variables Setup

You need to set these environment variables in your Vercel dashboard:

### Required Environment Variables

1. Go to your Vercel project dashboard
2. Navigate to Settings → Environment Variables
3. Add the following variables:

```
MONGODB_URL=mongodb+srv://admin:h1MiNtwQXzeFy6qL@hnix.vltkime.mongodb.net/?retryWrites=true&w=majority&appName=HNIX
DATABASE_NAME=horoscope_db
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
APP_NAME=Horoscope API
APP_VERSION=1.0.0
```

**Important**: Make sure to set these for all environments (Production, Preview, Development)

## Deployment Steps

1. **Set Environment Variables** (as described above)

2. **Deploy to Vercel**:

   ```bash
   vercel --prod
   ```

3. **Test the deployment**:
   - Visit your Vercel URL
   - Check the root endpoint: `https://your-app.vercel.app/`
   - Check the health endpoint: `https://your-app.vercel.app/health`
   - Check the API docs: `https://your-app.vercel.app/docs`

## Testing Endpoints

After deployment, test these endpoints:

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /docs` - API documentation
- `POST /api/v1/auth/social-login` - Social login

## Common Issues and Solutions

### 1. Database Connection Issues

- Ensure MONGODB_URL is correctly set in Vercel environment variables
- Check that your MongoDB Atlas cluster allows connections from all IPs (0.0.0.0/0) or add Vercel's IP ranges

### 2. Import Errors

- All imports are now properly structured for serverless deployment
- The PYTHONPATH is set in vercel.json

### 3. Function Timeout

- Set maxDuration to 30 seconds in vercel.json for database operations

### 4. CORS Issues

- CORS is configured to allow all origins for development
- Update the allow_origins list for production security

## Security Recommendations

1. **Change the SECRET_KEY** - Use a strong, unique secret key for production
2. **Update CORS settings** - Restrict allow_origins to your frontend domains
3. **Environment Variables** - Never commit sensitive data to your repository

## Monitoring

After deployment, monitor:

- Function logs in Vercel dashboard
- Database connection metrics in MongoDB Atlas
- API response times and error rates

## Local Testing

Run the test script before deploying:

```bash
python3 test_local.py
```

This will verify all imports and database connections work correctly.
