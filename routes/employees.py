# ============================================
# routes/employees.py - Çalışan Endpoint'leri
# ============================================
from flask import Blueprint, request, jsonify
from database import db
from models import Employee
import datetime

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/', methods=['GET'])
def get_employees():
    """Tüm çalışanları listele"""
    try:
        employees = Employee.query.all()
        return jsonify({
            "success": True,
            "count": len(employees),
            "employees": [e.to_dict() for e in employees]
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@employees_bp.route('/<string:employee_id>', methods=['GET'])
def get_employee(employee_id):
    """Tek bir çalışanı getir"""
    try:
        employee = Employee.query.filter_by(employee_id=employee_id).first_or_404()
        return jsonify({
            "success": True,
            "employee": employee.to_dict(include_tasks=True)
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 404

@employees_bp.route('/', methods=['POST'])
def create_employee():
    """
    Yeni çalışan oluştur
    
    Request Body:
    {
        "employee_id": "e14",
        "name": "Yavuz K.",
        "role": "Backend Engineer",
        "timezone": "Europe/Istanbul",
        "capacity_hours_per_week": 40,
        "current_load_hours": 18,
        "skills": [
            {"name": "python", "level": 5},
            {"name": "fastapi", "level": 5}
        ],
        "languages": ["tr", "en"],
        "integrations": {
            "email": "yavuz.k@codelllama.ai",
            "slack_user_id": "U03E14",
            "jira_account_id": "5f9c-e14"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Employee ID kontrolü
        existing = Employee.query.filter_by(employee_id=data['employee_id']).first()
        if existing:
            return jsonify({
                "success": False,
                "error": f"Employee with ID {data['employee_id']} already exists"
            }), 409
        
        integrations = data.get('integrations', {})
        
        employee = Employee(
            employee_id=data['employee_id'],
            name=data['name'],
            role=data.get('role'),
            timezone=data.get('timezone'),
            capacity_hours_per_week=data.get('capacity_hours_per_week', 40),
            current_load_hours=data.get('current_load_hours', 0),
            skills=data.get('skills', []),
            languages=data.get('languages', []),
            email=integrations.get('email'),
            slack_user_id=integrations.get('slack_user_id'),
            jira_account_id=integrations.get('jira_account_id')
        )
        
        db.session.add(employee)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Employee created successfully",
            "employee": employee.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@employees_bp.route('/<string:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """Çalışanı güncelle"""
    try:
        employee = Employee.query.filter_by(employee_id=employee_id).first_or_404()
        data = request.get_json()
        
        # Güncellenebilir alanlar
        if 'name' in data:
            employee.name = data['name']
        if 'role' in data:
            employee.role = data['role']
        if 'timezone' in data:
            employee.timezone = data['timezone']
        if 'capacity_hours_per_week' in data:
            employee.capacity_hours_per_week = data['capacity_hours_per_week']
        if 'current_load_hours' in data:
            employee.current_load_hours = data['current_load_hours']
        if 'skills' in data:
            employee.skills = data['skills']
        if 'languages' in data:
            employee.languages = data['languages']
        
        # Integrations güncelleme
        if 'integrations' in data:
            integrations = data['integrations']
            employee.email = integrations.get('email')
            employee.slack_user_id = integrations.get('slack_user_id')
            employee.jira_account_id = integrations.get('jira_account_id')
        
        employee.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Employee updated successfully",
            "employee": employee.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@employees_bp.route('/<string:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """Çalışanı sil"""
    try:
        employee = Employee.query.filter_by(employee_id=employee_id).first_or_404()
        name = employee.name
        
        db.session.delete(employee)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Employee '{name}' deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
