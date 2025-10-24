# ============================================
# 4. models.py - SQLAlchemy Modelleri
# ============================================
from database import db
from datetime import datetime
from sqlalchemy import JSON, Text, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List

class Project(db.Model):
    """Proje tablosu"""
    __tablename__ = 'projects'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_title: Mapped[str] = mapped_column(String(200), nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_time: Mapped[Optional[str]] = mapped_column(String(50))  # ISO 8601 duration
    
    # Metadata JSON olarak
    description: Mapped[Optional[str]] = mapped_column(Text)
    company: Mapped[Optional[str]] = mapped_column(String(200))
    department: Mapped[Optional[str]] = mapped_column(String(200))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    languages: Mapped[Optional[dict]] = mapped_column(JSON)  # ["tr", "en"]
    
    project_description: Mapped[Optional[str]] = mapped_column(Text)
    possible_solution: Mapped[Optional[str]] = mapped_column(Text)
    
    # Jira entegrasyonu
    jira_project_key: Mapped[Optional[str]] = mapped_column(String(50))
    jira_synced: Mapped[bool] = mapped_column(Boolean, default=False)
    jira_sync_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # İlişkiler
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    team_members: Mapped[List["ProjectTeamMember"]] = relationship("ProjectTeamMember", back_populates="project", cascade="all, delete-orphan")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, include_tasks=True, include_team=True):
        """Project'i JSON formatına çevir"""
        data = {
            "id": self.id,
            "project_title": self.project_title,
            "index": self.index,
            "estimated_time": self.estimated_time,
            "metadata": {
                "description": self.description,
                "company": self.company,
                "department": self.department,
                "year": self.year,
                "languages": self.languages or []
            },
            "project_description": self.project_description,
            "possible_solution": self.possible_solution,
            "jira_project_key": self.jira_project_key,
            "jira_synced": self.jira_synced,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_tasks:
            data["tasks"] = [task.to_dict(include_project=False) for task in self.tasks]
        
        if include_team:
            data["team"] = [member.to_dict() for member in self.team_members]
        
        return data


class Employee(db.Model):
    """Çalışan tablosu"""
    __tablename__ = 'employees'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # e14, e42
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(200))
    timezone: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Kapasite
    capacity_hours_per_week: Mapped[Optional[int]] = mapped_column(Integer, default=40)
    current_load_hours: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    
    # Skills JSON olarak
    skills: Mapped[Optional[dict]] = mapped_column(JSON)  # [{"name": "python", "level": 5}]
    languages: Mapped[Optional[dict]] = mapped_column(JSON)  # ["tr", "en"]
    
    # Entegrasyonlar
    email: Mapped[Optional[str]] = mapped_column(String(200))
    slack_user_id: Mapped[Optional[str]] = mapped_column(String(100))
    jira_account_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # İlişkiler
    assigned_tasks: Mapped[List["Task"]] = relationship("Task", back_populates="assignee")
    project_memberships: Mapped[List["ProjectTeamMember"]] = relationship("ProjectTeamMember", back_populates="employee")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, include_tasks=False):
        """Employee'yi JSON formatına çevir"""
        data = {
            "id": self.id,
            "employee_id": self.employee_id,
            "name": self.name,
            "role": self.role,
            "timezone": self.timezone,
            "capacity_hours_per_week": self.capacity_hours_per_week,
            "current_load_hours": self.current_load_hours,
            "skills": self.skills or [],
            "languages": self.languages or [],
            "integrations": {
                "email": self.email,
                "slack_user_id": self.slack_user_id,
                "jira_account_id": self.jira_account_id
            }
        }
        
        if include_tasks:
            data["assigned_tasks"] = [task.to_dict(include_project=False) for task in self.assigned_tasks]
        
        return data


class Task(db.Model):
    """Task tablosu"""
    __tablename__ = 'tasks'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Frontend'den gelen ID
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id'), nullable=False)
    
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    epic_name: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Labels ve priority
    labels: Mapped[Optional[dict]] = mapped_column(JSON)  # ["backend", "infra"]
    priority: Mapped[Optional[str]] = mapped_column(String(50))  # high, medium, low
    status_name: Mapped[Optional[str]] = mapped_column(String(50))  # assigned, proposed, in_progress
    
    # Skills ve dependencies
    required_skills: Mapped[Optional[dict]] = mapped_column(JSON)  # ["python", "fastapi"]
    dependencies: Mapped[Optional[dict]] = mapped_column(JSON)  # [{"task_id": 2}]
    
    # Atama bilgileri
    assignee_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('employees.id'))
    assignee_score: Mapped[Optional[float]] = mapped_column(Float)
    decided_by: Mapped[Optional[str]] = mapped_column(String(50))  # auto, manual
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    rationale: Mapped[Optional[str]] = mapped_column(Text)
    
    # Aday atamalar (JSON)
    assignee_candidates: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Jira entegrasyonu
    jira_issue_key: Mapped[Optional[str]] = mapped_column(String(50))  # KN-123
    jira_issue_id: Mapped[Optional[str]] = mapped_column(String(50))
    jira_synced: Mapped[bool] = mapped_column(Boolean, default=False)
    jira_sync_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Zaman takibi
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    estimated_time: Mapped[Optional[str]] = mapped_column(String(50))  # 2d, 4h
    
    # İlişkiler
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    assignee: Mapped[Optional["Employee"]] = relationship("Employee", back_populates="assigned_tasks")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, include_project=False, include_assignee=True):
        """Task'ı JSON formatına çevir"""
        data = {
            "id": self.id,
            "task_id": self.task_id,
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description,
            "epic_name": self.epic_name,
            "labels": self.labels or [],
            "priority": self.priority,
            "status_name": self.status_name,
            "required_skills": self.required_skills or [],
            "dependencies": self.dependencies or [],
            "assignee_candidates": self.assignee_candidates,
            "jira_issue_key": self.jira_issue_key,
            "jira_synced": self.jira_synced,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "estimated_time": self.estimated_time,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        if include_assignee and self.assignee:
            data["assignee"] = {
                "employee_id": self.assignee.employee_id,
                "name": self.assignee.name,
                "score": self.assignee_score,
                "decided_by": self.decided_by,
                "decided_at": self.decided_at.isoformat() if self.decided_at else None,
                "rationale": self.rationale
            }
        
        if include_project and self.project:
            data["project"] = {
                "id": self.project.id,
                "project_title": self.project.project_title
            }
        
        return data


class ProjectTeamMember(db.Model):
    """Proje-Çalışan ilişki tablosu"""
    __tablename__ = 'project_team_members'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id'), nullable=False)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey('employees.id'), nullable=False)
    
    # Ekstra bilgiler
    role_in_project: Mapped[Optional[str]] = mapped_column(String(200))  # "Backend Lead", "Frontend Dev"
    
    # İlişkiler
    project: Mapped["Project"] = relationship("Project", back_populates="team_members")
    employee: Mapped["Employee"] = relationship("Employee", back_populates="project_memberships")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Team member'ı JSON formatına çevir"""
        return {
            "employee_id": self.employee.employee_id,
            "name": self.employee.name,
            "role_in_project": self.role_in_project,
            "skills": self.employee.skills or [],
            "department": self.employee.role
        }


class JiraSyncLog(db.Model):
    """Jira senkronizasyon log'ları"""
    __tablename__ = 'jira_sync_logs'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sync_type: Mapped[str] = mapped_column(String(50))  # project, task, full
    sync_direction: Mapped[str] = mapped_column(String(50))  # to_jira, from_jira
    status: Mapped[str] = mapped_column(String(50))  # success, error, partial
    
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('projects.id'))
    task_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('tasks.id'))
    
    details: Mapped[Optional[dict]] = mapped_column(JSON)  # Detaylı log bilgisi
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "sync_type": self.sync_type,
            "sync_direction": self.sync_direction,
            "status": self.status,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "details": self.details,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat()
        }
