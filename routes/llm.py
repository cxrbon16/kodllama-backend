"""LLM tabanlı yardımcı endpoint'ler."""
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

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
    """Belirtilen projedeki task'ları otomatik olarak ekibe ata."""
    data = request.get_json(silent=True) or {}
    project_id = data.get("project_id")
    limit = data.get("limit")

    if not project_id:
        return jsonify({"success": False, "error": "project_id alanı zorunludur."}), 400

    try:
        project = Project.query.get_or_404(project_id)
        assignments = auto_assign_tasks(project, limit=limit)
        db.session.commit()

        return jsonify({
            "success": True,
            "assignments": assignments,
            "summary": {
                "assigned_count": len(assignments),
                "remaining_unassigned": sum(1 for task in project.tasks if not task.assignee_id)
            }
        }), 200
    except SQLAlchemyError as exc:  # pragma: no cover - koruyucu önlem
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500
