# ============================================
# seed_data.py - Test Verisi Oluşturma
# ============================================
"""
Test verisi eklemek için:
python seed_data.py
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import Project, Employee, Task, ProjectTeamMember

def seed_database():
    """Test verisi ekle"""
    print("=" * 60)
    print("🌱 Seeding PlanLLaMA Database")
    print("=" * 60)
    
    with app.app_context():
        # Mevcut verileri temizle (opsiyonel)
        # db.drop_all()
        # db.create_all()
        
        print("\n👥 Creating employees...")
        
        employees_data = [
            {
                "employee_id": "e14",
                "name": "Yavuz K.",
                "role": "Backend Engineer",
                "timezone": "Europe/Istanbul",
                "capacity_hours_per_week": 40,
                "current_load_hours": 18,
                "skills": [
                    {"name": "python", "level": 5},
                    {"name": "fastapi", "level": 5},
                    {"name": "redis", "level": 4}
                ],
                "languages": ["tr", "en"],
                "email": "yavuz.k@codelllama.ai",
                "jira_account_id": "5f9c-e14"
            },
            {
                "employee_id": "e42",
                "name": "Jane Smith",
                "role": "Frontend Engineer",
                "timezone": "Europe/Istanbul",
                "capacity_hours_per_week": 40,
                "current_load_hours": 20,
                "skills": [
                    {"name": "react", "level": 5},
                    {"name": "typescript", "level": 4},
                    {"name": "css", "level": 5}
                ],
                "languages": ["tr", "en"],
                "email": "jane.smith@codelllama.ai",
                "jira_account_id": "5f9c-e42"
            },
            {
                "employee_id": "e44",
                "name": "Bob Johnson",
                "role": "Full Stack Engineer",
                "timezone": "Europe/Istanbul",
                "capacity_hours_per_week": 40,
                "current_load_hours": 15,
                "skills": [
                    {"name": "python", "level": 4},
                    {"name": "react", "level": 4},
                    {"name": "docker", "level": 5}
                ],
                "languages": ["tr", "en"],
                "email": "bob.j@codelllama.ai",
                "jira_account_id": "5f9c-e44"
            }
        ]
        
        employees = {}
        for emp_data in employees_data:
            employee = Employee(
                employee_id=emp_data["employee_id"],
                name=emp_data["name"],
                role=emp_data["role"],
                timezone=emp_data["timezone"],
                capacity_hours_per_week=emp_data["capacity_hours_per_week"],
                current_load_hours=emp_data["current_load_hours"],
                skills=emp_data["skills"],
                languages=emp_data["languages"],
                email=emp_data["email"],
                jira_account_id=emp_data["jira_account_id"]
            )
            db.session.add(employee)
            employees[emp_data["employee_id"]] = employee
            print(f"   ✓ {employee.name}")
        
        db.session.flush()
        
        print("\n📁 Creating project...")
        
        project = Project(
            project_title="PlanLLaMA - AI Project Manager",
            index=1,
            estimated_time="P7D",
            description="Hackathon projesi - AI destekli proje yönetim aracı",
            company="CodeLLaMA",
            department="AI Software Research & Development",
            year=2025,
            languages=["tr", "en"],
            project_description="Llama kullanarak akıllı task oluşturma ve atama yapan proje yönetim sistemi",
            possible_solution="LLM tabanlı task generation, skill matching ve Jira entegrasyonu"
        )
        
        db.session.add(project)
        db.session.flush()
        print(f"   ✓ {project.project_title}")
        
        print("\n👥 Adding team members...")
        
        for emp_id, emp in employees.items():
            member = ProjectTeamMember(
                project_id=project.id,
                employee_id=emp.id,
                role_in_project=emp.role
            )
            db.session.add(member)
            print(f"   ✓ {emp.name} - {emp.role}")
        
        db.session.flush()
        
        print("\n📋 Creating tasks...")
        
        tasks_data = [
            {
                "task_id": 1,
                "title": "Backend API Development",
                "description": "Flask REST API ile database operasyonları",
                "epic_name": "Backend Development",
                "labels": ["backend", "api"],
                "priority": "high",
                "status_name": "in_progress",
                "required_skills": ["python", "fastapi"],
                "assignee_id": "e14",
                "estimated_time": "2d"
            },
            {
                "task_id": 2,
                "title": "PostgreSQL Schema Design",
                "description": "Database modellerini ve ilişkileri tasarla",
                "epic_name": "Backend Development",
                "labels": ["backend", "database"],
                "priority": "high",
                "status_name": "completed",
                "required_skills": ["python", "postgresql"],
                "assignee_id": "e14",
                "estimated_time": "1d"
            },
            {
                "task_id": 3,
                "title": "Jira Integration Service",
                "description": "Jira API entegrasyonu ve sync fonksiyonları",
                "epic_name": "Integrations",
                "labels": ["backend", "integration"],
                "priority": "high",
                "status_name": "assigned",
                "required_skills": ["python", "rest-api"],
                "assignee_id": "e14",
                "estimated_time": "3d"
            },
            {
                "task_id": 4,
                "title": "Frontend Dashboard UI",
                "description": "React ile proje dashboard ekranı",
                "epic_name": "Frontend Development",
                "labels": ["frontend", "ui"],
                "priority": "high",
                "status_name": "in_progress",
                "required_skills": ["react", "typescript"],
                "assignee_id": "e42",
                "estimated_time": "2d"
            },
            {
                "task_id": 5,
                "title": "Task Assignment Algorithm",
                "description": "Skill matching ve workload balancing",
                "epic_name": "AI Features",
                "labels": ["ai", "algorithm"],
                "priority": "high",
                "status_name": "proposed",
                "required_skills": ["python", "ai"],
                "assignee_id": "e44",
                "estimated_time": "2d"
            },
            {
                "task_id": 6,
                "title": "LLM Task Generation",
                "description": "Llama ile akıllı task oluşturma",
                "epic_name": "AI Features",
                "labels": ["ai", "llm"],
                "priority": "medium",
                "status_name": "proposed",
                "required_skills": ["python", "llm"],
                "dependencies": [{"task_id": 5}],
                "assignee_id": "e44",
                "estimated_time": "3d"
            }
        ]
        
        for task_data in tasks_data:
            assignee_emp_id = task_data.pop("assignee_id", None)
            assignee = employees.get(assignee_emp_id) if assignee_emp_id else None
            
            task = Task(
                project_id=project.id,
                **task_data
            )
            
            if assignee:
                task.assignee_id = assignee.id
                task.decided_by = "manual"
                task.decided_at = datetime.utcnow()
                task.rationale = "Initial assignment"
            
            db.session.add(task)
            print(f"   ✓ Task #{task.task_id}: {task.title}")
        
        db.session.commit()
        
        print("\n✅ Database seeded successfully!")
        print(f"\n📊 Summary:")
        print(f"   • Employees: {len(employees)}")
        print(f"   • Projects: 1")
        print(f"   • Tasks: {len(tasks_data)}")
        print("\n🚀 Ready to use! Start the Flask app:")
        print("   python app.py")
        print("=" * 60)

if __name__ == "__main__":
    seed_database()