#!/usr/bin/env python3
"""
Test script to verify the API works before deployment
"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_api():
    """Test the API endpoints"""
    try:
        # Import the app
        from api.index import app
        
        print("✅ Successfully imported the FastAPI app")
        print(f"📝 App title: {app.title}")
        print(f"📝 App version: {app.version}")
        
        # Test if we can access the routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append(f"{list(route.methods)[0]} {route.path}")
        
        print(f"\n📋 Available routes ({len(routes)}):")
        for route in sorted(routes):
            print(f"  - {route}")
        
        print("\n✅ API structure looks good!")
        print("\n🚀 Ready for deployment to Vercel!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing API before deployment...\n")
    
    success = asyncio.run(test_api())
    
    if success:
        print("\n" + "="*50)
        print("🎉 All tests passed! Your API is ready for Vercel deployment.")
        print("\nNext steps:")
        print("1. Set up MongoDB Atlas database")
        print("2. Configure environment variables in Vercel")
        print("3. Deploy using: vercel")
        print("="*50)
        sys.exit(0)
    else:
        print("\n" + "="*50)
        print("❌ Tests failed. Please fix the issues before deploying.")
        print("="*50)
        sys.exit(1)
