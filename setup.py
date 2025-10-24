# ============================================
# setup.py - Database Kurulum Script
# ============================================
"""
Database'i kurmak için bu script'i çalıştırın:
python setup.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import Project, Employee, Task, ProjectTeamMember, JiraSyncLog

def init_database():
    """Database'i oluştur ve tabloları kur"""
    print("=" * 60)
    print("🚀 PlanLLaMA Database Setup")
    print("=" * 60)
    
    with app.app_context():
        print("\n📋 Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        print("\n📊 Database schema:")
        print(f"   • projects")
        print(f"   • employees")
        print(f"   • tasks")
        print(f"   • project_team_members")
        print(f"   • jira_sync_logs")
        
        print("\n✨ Setup complete! You can now run the Flask app.")
        print("   Run: python app.py")
        print("=" * 60)

if __name__ == "__main__":
    init_database()