"""LLM tabanlı yardımcı endpoint'ler."""
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
import os
from datetime import datetime
import requests
from database import db
from models import Project, Task
from services.llm_service import analyze_project, auto_assign_tasks, update_task_status

llm_bp = Blueprint("llm", __name__)


@llm_bp.route("/analyze-project", methods=["POST"])
def analyze_project_endpoint():
    """Bir projeyi analiz ederek özet bilgiler döndür."""
    data = request.get_json(silent=True) or {}
    project_id = data.get("project_id")

    if not project_id:
        return jsonify({"success": False, "error": "project_id alanı zorunludur."}), 400

    try:
        project = Project.query.get_or_404(project_id)
        analysis = analyze_project(project)
        return jsonify({"success": True, "analysis": analysis}), 200
    except SQLAlchemyError as exc:  # pragma: no cover - koruyucu önlem
        return jsonify({"success": False, "error": str(exc)}), 500


@llm_bp.route("/update-status", methods=["POST"])
def update_status_endpoint():
    """Task durumunu LLM çıktısına göre güncelle."""
    data = request.get_json(silent=True) or {}
    task_identifier = data.get("id") or data.get("task_id")
    status_name = data.get("status_name")

    if not task_identifier or not status_name:
        return jsonify({
            "success": False,
            "error": "id/task_id ve status_name alanları zorunludur."
        }), 400

    rationale = data.get("rationale")
    decided_by = data.get("decided_by", "llm")

    try:
        task = Task.query.get(task_identifier)
        if not task:
            task = Task.query.filter_by(task_id=task_identifier).first()
        if not task:
            return jsonify({"success": False, "error": "Task bulunamadı."}), 404

        update_task_status(task, status_name=status_name, rationale=rationale, decided_by=decided_by)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Task status updated",
            "task": task.to_dict()
        }), 200
    except SQLAlchemyError as exc:  # pragma: no cover - koruyucu önlem
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500


@llm_bp.route("/auto-assign", methods=["POST"])
def auto_assign_endpoint():
    """Belirtilen projedeki task'ları otomatik olarak LLM'e atatır."""
    data = request.get_json(silent=True) or {}
    project_id = data.get("project_id")
    limit = data.get("limit")

    if not project_id:
        return jsonify({"success": False, "error": "project_id alanı zorunludur."}), 400

    try:
        # Veritabanından proje ve ekibini çek
        project = Project.query.get_or_404(project_id)

        # LLM'e gönderilecek payload'u oluştur
        payload = {
            "json_input": {
            "project_title": getattr(project, "title", None) or getattr(project, "project_name", None) or "Bilinmeyen Proje",
            "index": project.id,
            "estimated_time": getattr(project, "estimated_time", "P2D"),
            "metadata": {
                "description": getattr(project, "description", ""),
                "company": getattr(project, "company", "Unknown"),
                "department": getattr(project, "department", "Unknown"),
                "year": datetime.now().year,
                "languages": getattr(project, "languages", []),
            },
            "project_description": getattr(project, "full_description", "") or getattr(project, "description", ""),
            "possible_solution": getattr(project, "possible_solution", ""),
            "team": [
                {
                    "employee_id": getattr(m, "id", None) or getattr(m, "employee_id", None),
                    "name": getattr(m, "name", None) or getattr(m, "full_name", None) or getattr(m, "employee_name", None) or getattr(m, "member_name", None) or "Bilinmeyen Üye",
                    "skills": getattr(m, "skills", []),
                    "department": getattr(m, "department", "Unknown")
                }
                for m in getattr(project, "team_members", [])
            ],
            "tasks": [
                {
                    "task_id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "required_skills": getattr(t, "required_skills", [])
                }
                for t in project.tasks
            ],
        },
        "project_key": getattr(project, "key", "GENERIC")
    }


        # LLM servisine istek gönder
        llm_url = os.getenv("LLM_ASSIGN_URL", "https://1b2370c02283.ngrok-free.app/api/generate")
        response = requests.post(llm_url, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        assignments = result.get("jira_json", {}).get("assignments") or []

        # Görevleri veritabanında güncelle
        updated_tasks = []
        for assignment in assignments:
            task_id = assignment.get("task_id")
            assignee_name = assignment.get("assignee")
            if not task_id or not assignee_name:
                continue

            task = Task.query.get(task_id)
            if not task:
                continue

            assignee = next(
                (m for m in project.team_members if m.name == assignee_name),
                None
            )
            if assignee:
                task.assignee_id = assignee.id
                updated_tasks.append({
                    "task_id": task.id,
                    "assignee": assignee.name
                })

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "LLM tabanlı otomatik atama tamamlandı.",
            "assignments": updated_tasks,
            "summary": {
                "assigned_count": len(updated_tasks),
                "remaining_unassigned": sum(1 for t in project.tasks if not t.assignee_id)
            }
        }), 200

    except requests.exceptions.RequestException as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"LLM isteği hatası: {str(e)}"}), 500

    except SQLAlchemyError as exc:  # pragma: no cover
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500