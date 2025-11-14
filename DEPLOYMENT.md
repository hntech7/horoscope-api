# Vercel Deployment Guide

This guide will help you deploy your FastAPI Horoscope API to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI** (optional but recommended): Install with `npm i -g vercel`
3. **MongoDB Atlas**: Set up a MongoDB Atlas cluster for production database

## Files Created for Deployment

The following files have been created/configured for Vercel deployment:

- `vercel.json` - Vercel configuration file
- `api/index.py` - Entry point for Vercel serverless functions
- `.vercelignore` - Files to exclude from deployment

## Environment Variables

You need to set up the following environment variables in your Vercel project:

### Required Environment Variables

1. **MONGODB_URL** - Your MongoDB connection string (MongoDB Atlas recommended)

   ```
   mongodb+srv://username:password@cluster.mongodb.net/database_name?retryWrites=true&w=majority
   ```

2. **SECRET_KEY** - JWT secret key (generate a secure random string)

   ```
   your-super-secure-secret-key-here
   ```

3. **DATABASE_NAME** - Your MongoDB database name
   ```
   horoscope_db
   ```

### Optional Environment Variables

- **ACCESS_TOKEN_EXPIRE_MINUTES** - JWT token expiration (default: 30)
- **REFRESH_TOKEN_EXPIRE_DAYS** - Refresh token expiration (default: 7)
- **APP_NAME** - Application name (default: "Horoscope API")
- **APP_VERSION** - Application version (default: "1.0.0")

## Deployment Steps

### Method 1: Using Vercel CLI

1. Install Vercel CLI:

   ```bash
   npm i -g vercel
   ```

2. Login to Vercel:

   ```bash
   vercel login
   ```

3. Deploy from your project directory:

   ```bash
   vercel
   ```

4. Follow the prompts:
   - Link to existing project or create new one
   - Set up environment variables when prompted

### Method 2: Using Vercel Dashboard

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your Git repository
4. Vercel will automatically detect the configuration
5. Add environment variables in the project settings
6. Deploy

### Method 3: GitHub Integration

1. Push your code to GitHub
2. Connect your GitHub account to Vercel
3. Import the repository
4. Configure environment variables
5. Deploy

## Setting Environment Variables

### Via Vercel CLI:

```bash
vercel env add MONGODB_URL
vercel env add SECRET_KEY
vercel env add DATABASE_NAME
```

### Via Vercel Dashboard:

1. Go to your project settings
2. Navigate to "Environment Variables"
3. Add each variable for Production, Preview, and Development environments

## MongoDB Atlas Setup

1. Create a MongoDB Atlas account
2. Create a new cluster
3. Create a database user
4. Whitelist Vercel's IP addresses (or use 0.0.0.0/0 for all IPs)
5. Get your connection string
6. Replace `<password>` and `<dbname>` in the connection string

## Post-Deployment

After successful deployment:

1. **Test your API**: Visit your Vercel URL
2. **Check API documentation**: Visit `https://your-app.vercel.app/docs`
3. **Test endpoints**: Verify all your API endpoints work correctly
4. **Monitor logs**: Check Vercel function logs for any issues

## API Endpoints

Your deployed API will have the following endpoints:

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /docs` - API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation
- `POST /api/v1/auth/*` - Authentication endpoints
- `GET /api/v1/users/*` - User management endpoints
- `POST /api/v1/conversations/*` - Conversation endpoints
- `GET /api/v1/credits/*` - Credits management endpoints
- `GET /api/v1/analytics/*` - Analytics endpoints

## Troubleshooting

### Common Issues:

1. **Import Errors**: Make sure all dependencies are in `requirements.txt`
2. **Database Connection**: Verify MongoDB URL and network access
3. **Environment Variables**: Ensure all required env vars are set
4. **Cold Starts**: First request might be slow due to serverless cold starts
5. **Timeout Issues**: Vercel has a 10-second timeout for serverless functions

### Debugging:

1. Check Vercel function logs in the dashboard
2. Use `vercel logs` command to see recent logs
3. Test locally with `vercel dev`

## Performance Considerations

1. **Database Connections**: MongoDB connections are handled per request in serverless
2. **Cold Starts**: Consider implementing connection pooling if needed
3. **Caching**: Implement caching for frequently accessed data
4. **Rate Limiting**: Consider adding rate limiting for production

## Security Recommendations

1. **CORS**: Update CORS settings for production (remove wildcard)
2. **Environment Variables**: Never commit secrets to version control
3. **HTTPS**: Vercel provides HTTPS by default
4. **Database Security**: Use MongoDB Atlas security features
5. **JWT Secrets**: Use strong, unique secret keys

## Next Steps

1. Set up monitoring and alerting
2. Implement proper logging
3. Add rate limiting
4. Set up CI/CD pipeline
5. Configure custom domain (optional)

Your API is now ready for deployment on Vercel!
