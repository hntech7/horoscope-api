# Horoscope API

A FastAPI-based horoscope API with Google and Apple OAuth authentication.

## Features

- Google OAuth login
- Apple OAuth login
- JWT token-based authentication
- User registration and profile management
- SQLite database with SQLAlchemy ORM
- Automatic user creation on first login
- RESTful API endpoints

## User Model

The API supports users with the following attributes:

- `language` (required): User's preferred language
- `name` (required): User's display name
- `userId` (required): Unique user identifier
- `email` (optional): User's email address
- `birthDate` (optional): User's birth date (YYYY-MM-DD)
- `birthTime` (optional): User's birth time (HH:MM)
- `zodiacSign` (optional): User's zodiac sign
- `occupation` (optional): User's occupation
- `profileImage` (optional): User's profile image URL

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**

   Update the `.env` file with your OAuth credentials:

   ```env
   # JWT Settings
   SECRET_KEY=your-super-secret-key-change-this-in-production

   # Google OAuth
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret

   # Apple OAuth
   APPLE_CLIENT_ID=your-apple-client-id
   APPLE_TEAM_ID=your-apple-team-id
   APPLE_KEY_ID=your-apple-key-id
   APPLE_PRIVATE_KEY_PATH=./apple_private_key.p8
   ```

3. **Run the application:**

   ```bash
   python run.py
   ```

   Or using uvicorn directly:

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Authentication

#### Google Login

```http
POST /api/v1/auth/google/login
Content-Type: application/json

{
  "token": "google_oauth_token",
  "language": "en"
}
```

#### Apple Login

```http
POST /api/v1/auth/apple/login
Content-Type: application/json

{
  "identity_token": "apple_identity_token",
  "authorization_code": "apple_authorization_code",
  "language": "en",
  "name": "User Name (optional)",
  "email": "user@example.com (optional)"
}
```

#### Get Current User

```http
GET /api/v1/auth/me
Authorization: Bearer <jwt_token>
```

### User Management

#### Get User Profile

```http
GET /api/v1/users/profile
Authorization: Bearer <jwt_token>
```

#### Update User Profile

```http
PUT /api/v1/users/profile
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Updated Name",
  "birth_date": "1990-01-01",
  "birth_time": "10:30",
  "zodiac_sign": "Capricorn",
  "occupation": "Developer"
}
```

#### Delete User Profile

```http
DELETE /api/v1/users/profile
Authorization: Bearer <jwt_token>
```

## Authentication Flow

1. **First-time users:**

   - User authenticates with Google/Apple
   - API verifies the OAuth token
   - New user account is created automatically
   - JWT token is returned

2. **Returning users:**

   - User authenticates with Google/Apple
   - API verifies the OAuth token
   - Existing user is found by OAuth ID
   - JWT token is returned

3. **API Access:**
   - Include JWT token in Authorization header: `Bearer <token>`
   - Token expires after 30 minutes (configurable)

## Development

### Project Structure

```
cosmo-ai-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # JWT authentication
│   ├── oauth.py             # OAuth providers
│   ├── crud.py              # Database operations
│   └── routers/
│       ├── __init__.py
│       ├── auth.py          # Authentication endpoints
│       └── users.py         # User management endpoints
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── run.py                   # Application startup script
└── README.md               # This file
```

### API Documentation

Once the server is running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## OAuth Setup

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add your domain to authorized origins
6. Copy Client ID and Client Secret to `.env`

### Apple OAuth Setup

1. Go to [Apple Developer Portal](https://developer.apple.com/)
2. Create an App ID with Sign In with Apple capability
3. Create a Services ID for web authentication
4. Generate a private key for Sign In with Apple
5. Configure your domain and return URLs
6. Add credentials to `.env`

## Security Notes

- Change the `SECRET_KEY` in production
- Use HTTPS in production
- Configure CORS properly for your frontend domain
- Store OAuth credentials securely
- Implement rate limiting for production use

## Database

The application uses SQLite by default. The database file (`horoscope.db`) will be created automatically when you first run the application.

For production, consider switching to PostgreSQL or MySQL by updating the `DATABASE_URL` in your `.env` file.
# horoscope-api
# horoscope-api
