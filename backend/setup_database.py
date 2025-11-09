#!/usr/bin/env python3
"""
Database Setup Script for BacktestMCP
=====================================

This script initializes the MongoDB database with:
- Required collections
- Indexes for optimal query performance
- Optional test user

Run this before starting the FastAPI server for the first time.

Usage:
    python setup_database.py
    
    # Or with custom MongoDB URL:
    MONGODB_URL=mongodb://localhost:27017 python setup_database.py
"""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(__file__))

from pymongo import AsyncMongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "BacktestMCP")

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(message):
    print(f"{Colors.BLUE}→{Colors.END} {message}")

def print_success(message):
    print(f"{Colors.GREEN}✓{Colors.END} {message}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠{Colors.END} {message}")

def print_error(message):
    print(f"{Colors.RED}✗{Colors.END} {message}")

def print_header(message):
    print(f"\n{Colors.BOLD}{message}{Colors.END}")
    print("=" * len(message))


async def setup_database():
    """Main setup function"""
    
    print_header("BacktestMCP Database Setup")
    print(f"MongoDB URL: {MONGODB_URL}")
    print(f"Database Name: {MONGODB_DB_NAME}\n")
    
    client = None
    
    try:
        # Connect to MongoDB
        print_step("Connecting to MongoDB...")
        client = AsyncMongoClient(MONGODB_URL)
        
        # Test connection
        await client.admin.command('ping')
        print_success("Connected to MongoDB successfully")
        
        # Get database
        db = client[MONGODB_DB_NAME]
        
        # Create collections
        print_header("Creating Collections")
        collections = ["users", "conversations", "strategies"]
        
        existing_collections = await db.list_collection_names()
        
        for collection in collections:
            if collection in existing_collections:
                print_warning(f"Collection '{collection}' already exists")
            else:
                await db.create_collection(collection)
                print_success(f"Created collection '{collection}'")
        
        # Create indexes
        print_header("Creating Indexes")
        
        # Users collection indexes
        print_step("Setting up users collection indexes...")
        try:
            await db.users.create_index("email", unique=True)
            print_success("Created unique index on users.email")
        except Exception as e:
            print_warning(f"Index users.email may already exist: {e}")
        
        try:
            await db.users.create_index("username", unique=True)
            print_success("Created unique index on users.username")
        except Exception as e:
            print_warning(f"Index users.username may already exist: {e}")
        
        # Conversations collection indexes
        print_step("Setting up conversations collection indexes...")
        await db.conversations.create_index("user_id")
        print_success("Created index on conversations.user_id")
        
        await db.conversations.create_index([("user_id", ASCENDING), ("updated_at", DESCENDING)])
        print_success("Created compound index on conversations.user_id + updated_at")
        
        await db.conversations.create_index("strategy_id")
        print_success("Created index on conversations.strategy_id")
        
        # Strategies collection indexes
        print_step("Setting up strategies collection indexes...")
        await db.strategies.create_index("user_id")
        print_success("Created index on strategies.user_id")
        
        await db.strategies.create_index("conversation_id")
        print_success("Created index on strategies.conversation_id")
        
        await db.strategies.create_index([("user_id", ASCENDING), ("updated_at", DESCENDING)])
        print_success("Created compound index on strategies.user_id + updated_at")
        
        await db.strategies.create_index("status")
        print_success("Created index on strategies.status")
        
        # Display collection stats
        print_header("Database Statistics")
        for collection in collections:
            count = await db[collection].count_documents({})
            print(f"  {collection}: {count} documents")
        
        # Ask if user wants to create a test user
        print_header("Test User Setup")
        print("Would you like to create a test user? (y/n): ", end="")
        
        # For non-interactive environments, skip this
        if sys.stdin.isatty():
            create_test_user = input().lower().strip() == 'y'
        else:
            create_test_user = False
            print("n (non-interactive mode)")
        
        if create_test_user:
            from app.utils.auth import hash_password
            
            test_user = {
                "username": "testuser",
                "email": "test@example.com",
                "password_hash": hash_password("password123"),
                "created_at": datetime.utcnow()
            }
            
            try:
                result = await db.users.insert_one(test_user)
                print_success(f"Created test user:")
                print(f"    Email: test@example.com")
                print(f"    Password: password123")
                print(f"    User ID: {result.inserted_id}")
            except Exception as e:
                print_warning(f"Could not create test user (may already exist): {e}")
        
        print_header("Setup Complete!")
        print(f"{Colors.GREEN}Database is ready to use!{Colors.END}")
        print(f"\nYou can now start the FastAPI server:")
        print(f"  cd backend")
        print(f"  uvicorn app.main:app --reload")
        
    except Exception as e:
        print_error(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        if client:
            print_step("Disconnected from MongoDB")


async def reset_database():
    """Reset the database (drop all collections)"""
    
    print_header("⚠️  WARNING: Database Reset")
    print("This will DELETE ALL DATA in the database!")
    print(f"Database: {MONGODB_DB_NAME}")
    print("\nAre you sure? Type 'DELETE' to confirm: ", end="")
    
    if sys.stdin.isatty():
        confirmation = input().strip()
    else:
        print("(non-interactive mode - skipping reset)")
        return
    
    if confirmation != "DELETE":
        print("Reset cancelled.")
        return
    
    client = None
    
    try:
        client = AsyncMongoClient(MONGODB_URL)
        await client.admin.command('ping')
        
        db = client[MONGODB_DB_NAME]
        
        print_step("Dropping all collections...")
        collections = await db.list_collection_names()
        
        for collection in collections:
            await db[collection].drop()
            print_success(f"Dropped collection '{collection}'")
        
        print_success("Database reset complete!")
        print("\nRun the setup again to recreate collections and indexes:")
        print("  python setup_database.py")
        
    except Exception as e:
        print_error(f"Reset failed: {e}")
        sys.exit(1)
    
    finally:
        pass  # Client will be garbage collected


def main():
    """Main entry point"""
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--reset":
            asyncio.run(reset_database())
        elif sys.argv[1] == "--help":
            print(__doc__)
            print("\nOptions:")
            print("  (no arguments)  Set up the database")
            print("  --reset         Reset the database (delete all data)")
            print("  --help          Show this help message")
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help to see available options")
            sys.exit(1)
    else:
        asyncio.run(setup_database())


if __name__ == "__main__":
    main()

