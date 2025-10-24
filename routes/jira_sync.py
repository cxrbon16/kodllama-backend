# ============================================
# routes/jira_sync.py - Jira Senkronizasyon
# ============================================
from flask import Blueprint, request, jsonify
from database import db
from models import Project, Task, Employee, JiraSyncLog
from services.jira_service import JiraService
from datetime import datetime
import os

jira_sync_bp = Blueprint('jira_sync', __name__)

# Jira Service'i başlat
jira_service = JiraService(
    domain=os.getenv('JIRA_DOMAIN'),
    email=os.getenv('JIRA_EMAIL'),
    api_token=os.getenv('JIRA_API_TOKEN'),
    project_key=os.getenv('JIRA_PROJECT_KEY')
)

@jira_sync_bp.route('/sync/project/<int:project_id>', methods=['POST'])
def sync_project_to_jira(project_id):
    """
    Projeyi ve task'larını Jira'ya aktar
    
    Bu endpoint:
    1. Projeye ait tüm task'ları alır
    2. Her task için Jira'da issue oluşturur
    3. Parent-child ilişkilerini kurar
    4. Assignee'leri atar
    """
    try:
        project = Project.query.get_or_404(project_id)
        
        # Log başlat
        sync_log = JiraSyncLog(
            sync_type='project',
            sync_direction='to_jira',
            project_id=project.id,
            status='in_progress'
        )
        db.session.add(sync_log)
        db.session.commit()
        
        results = {
            "project_id": project.id,
            "project_title": project.project_title,
            "tasks_synced": [],
            "errors": []
        }
        
        # Task'ları grupla: Epic'ler ve normal task'lar
        tasks = Task.query.filter_by(project_id=project.id).all()
        epic_tasks = [t for t in tasks if t.epic_name]
        regular_tasks = [t for t in tasks if not t.epic_name]
        
        # Epic'leri oluştur (parent task olarak)
        epic_map = {}
        for epic_name in set(t.epic_name for t in epic_tasks):
            try:
                # Epic için parent task oluştur
                jira_key = jira_service.create_task(
                    summary=f"[Epic] {epic_name}",
                    description=f"Epic for {epic_name} related tasks",
                    issue_type="Task"
                )
                
                if jira_key:
                    epic_map[epic_name] = jira_key
                    results["tasks_synced"].append({
                        "type": "epic",
                        "name": epic_name,
                        "jira_key": jira_key
                    })
            except Exception as e:
                results["errors"].append({
                    "epic": epic_name,
                    "error": str(e)
                })
        
        # Task'ları oluştur
        for task in tasks:
            try:
                # Assignee bilgisi
                assignee_jira_id = None
                if task.assignee and task.assignee.jira_account_id:
                    assignee_jira_id = task.assignee.jira_account_id
                
                # Parent key (epic varsa)
                parent_key = None
                if task.epic_name and task.epic_name in epic_map:
                    parent_key = epic_map[task.epic_name]
                
                # Jira'da task oluştur
                issue_type = "Sub-task" if parent_key else "Task"
                
                jira_key = jira_service.create_task(
                    summary=task.title,
                    description=task.description,
                    issue_type=issue_type,
                    assignee_id=assignee_jira_id,
                    parent_key=parent_key,
                    labels=task.labels or [],
                    priority=task.priority
                )
                
                if jira_key:
                    # Database'i güncelle
                    task.jira_issue_key = jira_key
                    task.jira_synced = True
                    task.jira_sync_date = datetime.utcnow()
                    
                    results["tasks_synced"].append({
                        "task_id": task.task_id,
                        "title": task.title,
                        "jira_key": jira_key,
                        "parent": parent_key
                    })
                
            except Exception as e:
                results["errors"].append({
                    "task_id": task.task_id,
                    "title": task.title,
                    "error": str(e)
                })
        
        # Proje sync durumunu güncelle
        project.jira_synced = True
        project.jira_sync_date = datetime.utcnow()
        
        # Log'u güncelle
        sync_log.status = 'success' if not results["errors"] else 'partial'
        sync_log.details = results
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Synced {len(results['tasks_synced'])} items to Jira",
            "results": results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        
        # Log'a hatayı kaydet
        if 'sync_log' in locals():
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            db.session.commit()
        
        return jsonify({"success": False, "error": str(e)}), 500

@jira_sync_bp.route('/sync/task/<int:task_id>', methods=['POST'])
def sync_task_to_jira(task_id):
    """Tek bir task'ı Jira'ya aktar"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # Assignee bilgisi
        assignee_jira_id = None
        if task.assignee and task.assignee.jira_account_id:
            assignee_jira_id = task.assignee.jira_account_id
        
        # Jira'da task oluştur
        jira_key = jira_service.create_task(
            summary=task.title,
            description=task.description,
            issue_type="Task",
            assignee_id=assignee_jira_id,
            labels=task.labels or [],
            priority=task.priority
        )
        
        if jira_key:
            # Database'i güncelle
            task.jira_issue_key = jira_key
            task.jira_synced = True
            task.jira_sync_date = datetime.utcnow()
            
            # Log oluştur
            sync_log = JiraSyncLog(
                sync_type='task',
                sync_direction='to_jira',
                task_id=task.id,
                status='success',
                details={"jira_key": jira_key}
            )
            db.session.add(sync_log)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": f"Task synced to Jira: {jira_key}",
                "task": task.to_dict()
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Failed to create Jira issue"
            }), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@jira_sync_bp.route('/sync/status/<int:task_id>', methods=['POST'])
def sync_task_status_from_jira(task_id):
    """Jira'dan task durumunu çek ve güncelle"""
    try:
        task = Task.query.get_or_404(task_id)
        
        if not task.jira_issue_key:
            return jsonify({
                "success": False,
                "error": "Task not synced with Jira"
            }), 400
        
        # Jira'dan görev bilgilerini al
        jira_task = jira_service.get_task(task.jira_issue_key)
        
        if jira_task:
            # Status'u güncelle
            jira_status = jira_task['fields']['status']['name']
            task.status_name = jira_status.lower().replace(' ', '_')
            task.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": f"Status updated from Jira: {jira_status}",
                "task": task.to_dict()
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch Jira task"
            }), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@jira_sync_bp.route('/logs', methods=['GET'])
def get_sync_logs():
    """Senkronizasyon loglarını listele"""
    try:
        limit = request.args.get('limit', 50, type=int)
        logs = JiraSyncLog.query.order_by(
            JiraSyncLog.created_at.desc()
        ).limit(limit).all()
        
        return jsonify({
            "success": True,
            "count": len(logs),
            "logs": [log.to_dict() for log in logs]
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
