# ============================================
# routes/__init__.py
# ============================================
from flask import Blueprint

# Blueprint'leri import et
from routes.projects import projects_bp
from routes.employees import employees_bp
from routes.tasks import tasks_bp
from routes.jira_sync import jira_sync_bp

__all__ = ['projects_bp', 'employees_bp', 'tasks_bp', 'jira_sync_bp']
