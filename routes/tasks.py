# ============================================
# routes/tasks.py - Task Endpoint'leri
# ============================================
from flask import Blueprint, request, jsonify
from database import db
from models import Task, Project, Employee
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/', methods=['GET'])
def get_tasks():
    """Tüm task'ları listele (opsiyonel filtreleme)"""
    try:
        # Query parametreleri
        project_id = request.args.get('project_id', type=int)
        status = request.args.get('status')
        assignee_id = request.args.get('assignee_id')
        
        query = Task.query
        
        if project_id:
            query = query.filter_by(project_id=project_id)
        if status:
            query = query.filter_by(status_name=status)
        if assignee_id:
            employee = Employee.query.filter_by(employee_id=assignee_id).first()
            if employee:
                query = query.filter_by(assignee_id=employee.id)
        
        tasks = query.all()
        
        return jsonify({
            "success": True,
            "count": len(tasks),
            "tasks": [t.to_dict() for t in tasks]
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@tasks_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Tek bir task'ı getir"""
    try:
        task = Task.query.get_or_404(task_id)
        return jsonify({
            "success": True,
            "task": task.to_dict(include_project=True)
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 404

@tasks_bp.route('/', methods=['POST'])
def create_task():
    """
    Yeni task oluştur
    
    Request Body:
    {
        "task_id": 1,
        "project_id": 1,
        "title": "API rate limit middleware",
        "description": "NFR: 100rps; 429 strategy; metrics",
        "labels": ["backend", "infra"],
        "priority": "high",
        "status_name": "proposed",
        "required_skills": ["python", "fastapi", "redis"],
        "dependencies": [{"task_id": 2}],
        "assignee": {
            "employee_id": "e14",
            "score": 0.91,
            "decided_by": "auto",
            "decided_at": "2025-10-24T16:00:00Z",
            "rationale": "Skill match + low workload"
        },
        "estimated_time": "2d",
        "epic_name": "Authentication"
    }
    """
    try:
        data = request.get_json()
        
        # Project kontrolü
        project = Project.query.get_or_404(data['project_id'])
        
        task = Task(
            task_id=data['task_id'],
            project_id=data['project_id'],
            title=data['title'],
            description=data.get('description'),
            epic_name=data.get('epic_name'),
            labels=data.get('labels', []),
            priority=data.get('priority', 'medium'),
            status_name=data.get('status_name', 'proposed'),
            required_skills=data.get('required_skills', []),
            dependencies=data.get('dependencies', []),
            assignee_candidates=data.get('assignee_candidates'),
            estimated_time=data.get('estimated_time')
        )
        
        # Assignee varsa ekle
        if 'assignee' in data:
            assignee_data = data['assignee']
            employee = Employee.query.filter_by(
                employee_id=assignee_data['employee_id']
            ).first()
            
            if employee:
                task.assignee_id = employee.id
                task.assignee_score = assignee_data.get('score')
                task.decided_by = assignee_data.get('decided_by', 'auto')
                task.decided_at = datetime.fromisoformat(
                    assignee_data['decided_at']
                ) if 'decided_at' in assignee_data else datetime.utcnow()
                task.rationale = assignee_data.get('rationale')
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Task created successfully",
            "task": task.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@tasks_bp.route('/<int:task_id>/assign', methods=['POST'])
def assign_task(task_id):
    """
    Task'ı bir çalışana ata
    
    Request Body:
    {
        "employee_id": "e14",
        "decided_by": "manual",
        "rationale": "Best fit for this task"
    }
    """
    try:
        task = Task.query.get_or_404(task_id)
        data = request.get_json()
        
        employee = Employee.query.filter_by(
            employee_id=data['employee_id']
        ).first_or_404()
        
        task.assignee_id = employee.id
        task.decided_by = data.get('decided_by', 'manual')
        task.decided_at = datetime.utcnow()
        task.rationale = data.get('rationale')
        task.status_name = 'assigned'
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Task assigned to {employee.name}",
            "task": task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@tasks_bp.route('/<int:task_id>/status', methods=['PUT'])
def update_task_status(task_id):
    """
    Task durumunu güncelle
    
    Request Body:
    {
        "status_name": "in_progress"
    }
    """
    try:
        task = Task.query.get_or_404(task_id)
        data = request.get_json()
        
        task.status_name = data['status_name']
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Task status updated to {data['status_name']}",
            "task": task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Task'ı güncelle"""
    try:
        task = Task.query.get_or_404(task_id)
        data = request.get_json()
        
        # Güncellenebilir alanlar
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'labels' in data:
            task.labels = data['labels']
        if 'priority' in data:
            task.priority = data['priority']
        if 'status_name' in data:
            task.status_name = data['status_name']
        if 'required_skills' in data:
            task.required_skills = data['required_skills']
        if 'dependencies' in data:
            task.dependencies = data['dependencies']
        if 'estimated_time' in data:
            task.estimated_time = data['estimated_time']
        if 'epic_name' in data:
            task.epic_name = data['epic_name']
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Task updated successfully",
            "task": task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Task'ı sil"""
    try:
        task = Task.query.get_or_404(task_id)
        title = task.title
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Task '{title}' deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500