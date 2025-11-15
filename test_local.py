#!/usr/bin/env python3
"""
Local test script to verify the API works before deploying to Vercel
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_imports():
    """Test if all imports work correctly"""
    try:
        print("Testing imports...")
        
        # Test basic imports
        from app.config import settings
        print(f"✓ Config loaded: {settings.app_name}")
        
        # Test database import
        from app.database import connect_to_mongo, db
        print("✓ Database imports successful")
        
        # Test router imports
        from app.routers import auth, users, conversations, credits, analytics
        print("✓ Router imports successful")
        
        # Test FastAPI app creation
        from api.index import app
        print("✓ FastAPI app created successfully")
        
        print("\n✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_connection():
    """Test database connection"""
    try:
        print("\nTesting database connection...")
        from app.database import connect_to_mongo, db
        
        await connect_to_mongo()
        if db.client:
            print("✓ Database connection successful")
            # Test a simple operation
            await db.client.admin.command('ping')
            print("✓ Database ping successful")
            return True
        else:
            print("❌ Database client not initialized")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting local API tests...\n")
    
    # Test imports
    imports_ok = await test_imports()
    if not imports_ok:
        print("\n❌ Import tests failed. Fix imports before deploying.")
        return False
    
    # Test database connection
    db_ok = await test_database_connection()
    if not db_ok:
        print("\n⚠️  Database connection failed. Check your MONGODB_URL environment variable.")
        print("The API might still work for endpoints that don't require database access.")
    
    print("\n" + "="*50)
    if imports_ok and db_ok:
        print("✅ All tests passed! Your API should work on Vercel.")
    elif imports_ok:
        print("⚠️  Imports OK but database connection failed.")
        print("Check your Vercel environment variables.")
    else:
        print("❌ Tests failed. Fix the issues before deploying.")
    
    print("\n📝 Next steps:")
    print("1. Make sure all environment variables are set in Vercel dashboard")
    print("2. Deploy to Vercel: vercel --prod")
    print("3. Test the deployed API endpoints")

if __name__ == "__main__":
    asyncio.run(main())
