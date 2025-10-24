# ============================================
# routes/projects.py - Proje Endpoint'leri
# ============================================
from flask import Blueprint, request, jsonify
from database import db
from models import Project, Employee, ProjectTeamMember, Task
from datetime import datetime

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/', methods=['GET'])
def get_projects():
    """Tüm projeleri listele"""
    try:
        projects = Project.query.all()
        return jsonify({
            "success": True,
            "count": len(projects),
            "projects": [p.to_dict() for p in projects]
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@projects_bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Tek bir projeyi getir"""
    try:
        project = Project.query.get_or_404(project_id)
        return jsonify({
            "success": True,
            "project": project.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 404

@projects_bp.route('/', methods=['POST'])
def create_project():
    """
    Yeni proje oluştur
    
    Request Body:
    {
        "project_title": "PlanLLaMA",
        "index": 1,
        "estimated_time": "P2D",
        "metadata": {
            "description": "...",
            "company": "CodeLLaMA",
            "department": "...",
            "year": 2025,
            "languages": ["tr", "en"]
        },
        "project_description": "...",
        "possible_solution": "...",
        "team": [
            {
                "employee_id": "e14",
                "name": "John Doe",
                "skills": ["python", "fastapi"],
                "department": "Backend"
            }
        ],
        "tasks": []  # Opsiyonel
    }
    """
    try:
        data = request.get_json()
        
        # Proje oluştur
        project = Project(
            project_title=data['project_title'],
            index=data['index'],
            estimated_time=data.get('estimated_time'),
            description=data.get('metadata', {}).get('description'),
            company=data.get('metadata', {}).get('company'),
            department=data.get('metadata', {}).get('department'),
            year=data.get('metadata', {}).get('year'),
            languages=data.get('metadata', {}).get('languages', []),
            project_description=data.get('project_description'),
            possible_solution=data.get('possible_solution')
        )
        
        db.session.add(project)
        db.session.flush()  # ID'yi al
        
        # Team member'ları ekle
        if 'team' in data:
            for member_data in data['team']:
                # Employee'yi bul veya oluştur
                employee = Employee.query.filter_by(
                    employee_id=member_data['employee_id']
                ).first()
                
                if not employee:
                    # Yeni employee oluştur
                    skills_data = member_data.get('skills', [])
                    # String'den dict'e çevir
                    if isinstance(skills_data, list) and skills_data and isinstance(skills_data[0], str):
                        skills_data = [{"name": skill, "level": 3} for skill in skills_data]
                    
                    employee = Employee(
                        employee_id=member_data['employee_id'],
                        name=member_data['name'],
                        role=member_data.get('department'),
                        skills=skills_data
                    )
                    db.session.add(employee)
                    db.session.flush()
                
                # Proje-Employee ilişkisi ekle
                team_member = ProjectTeamMember(
                    project_id=project.id,
                    employee_id=employee.id,
                    role_in_project=member_data.get('department')
                )
                db.session.add(team_member)
        
        # Task'ları ekle (varsa)
        if 'tasks' in data and data['tasks']:
            for task_data in data['tasks']:
                task = Task(
                    task_id=task_data['task_id'],
                    project_id=project.id,
                    title=task_data['title'],
                    description=task_data.get('description'),
                    labels=task_data.get('labels', []),
                    priority=task_data.get('priority'),
                    status_name=task_data.get('status_name', 'proposed'),
                    required_skills=task_data.get('required_skills', []),
                    dependencies=task_data.get('dependencies', [])
                )
                
                # Assignee varsa ekle
                if 'assignee' in task_data:
                    assignee_data = task_data['assignee']
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
            "message": "Project created successfully",
            "project": project.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@projects_bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Projeyi güncelle"""
    try:
        project = Project.query.get_or_404(project_id)
        data = request.get_json()
        
        # Güncellenebilir alanlar
        if 'project_title' in data:
            project.project_title = data['project_title']
        if 'estimated_time' in data:
            project.estimated_time = data['estimated_time']
        if 'project_description' in data:
            project.project_description = data['project_description']
        if 'possible_solution' in data:
            project.possible_solution = data['possible_solution']
        
        # Metadata güncelleme
        if 'metadata' in data:
            metadata = data['metadata']
            project.description = metadata.get('description')
            project.company = metadata.get('company')
            project.department = metadata.get('department')
            project.year = metadata.get('year')
            project.languages = metadata.get('languages')
        
        project.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Project updated successfully",
            "project": project.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@projects_bp.route('/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Projeyi sil (cascade ile task'lar da silinir)"""
    try:
        project = Project.query.get_or_404(project_id)
        project_title = project.project_title
        
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Project '{project_title}' deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
