"""LLM destekli yardımcı servis fonksiyonları."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

from database import db
from models import Employee, Project, Task


def _normalize_skill_names(skills: Optional[Iterable]) -> List[str]:
    """Normalize skill listesi (str/dict karışık olabilir)."""
    if not skills:
        return []

    normalized: List[str] = []
    for item in skills:
        if isinstance(item, dict):
            name = item.get("name")
            if name:
                normalized.append(str(name).lower())
        elif isinstance(item, str):
            normalized.append(item.lower())
    return normalized


def analyze_project(project: Project) -> Dict[str, object]:
    """Projeyi analiz ederek özet ve öneriler döndür."""
    tasks = project.tasks
    status_counter: Counter = Counter(task.status_name or "unknown" for task in tasks)
    priority_counter: Counter = Counter(task.priority or "unspecified" for task in tasks)

    team_skills = set()
    for member in project.team_members:
        team_skills.update(_normalize_skill_names(member.employee.skills))

    required_skills = set()
    missing_skills = set()
    risk_tasks: List[Dict[str, object]] = []

    for task in tasks:
        task_skills = set(_normalize_skill_names(task.required_skills))
        required_skills.update(task_skills)
        uncovered = task_skills - team_skills
        if uncovered:
            missing_skills.update(uncovered)
            risk_tasks.append({
                "task_id": task.id,
                "title": task.title,
                "missing_skills": sorted(uncovered)
            })

    coverage_ratio = 1.0
    if required_skills:
        coverage_ratio = (len(required_skills) - len(missing_skills)) / len(required_skills)

    return {
        "project": {
            "id": project.id,
            "project_title": project.project_title,
            "total_tasks": len(tasks)
        },
        "summary": {
            "status_breakdown": dict(status_counter),
            "priority_breakdown": dict(priority_counter),
            "assigned_tasks": sum(1 for task in tasks if task.assignee_id),
            "unassigned_tasks": sum(1 for task in tasks if not task.assignee_id)
        },
        "skill_coverage": {
            "team_skills": sorted(team_skills),
            "required_skills": sorted(required_skills),
            "missing_skills": sorted(missing_skills),
            "coverage_ratio": round(coverage_ratio, 2)
        },
        "risks": risk_tasks,
        "recommendations": _build_recommendations(tasks, missing_skills)
    }


def _build_recommendations(tasks: Iterable[Task], missing_skills: Iterable[str]) -> List[str]:
    recommendations: List[str] = []

    unassigned = [task for task in tasks if not task.assignee_id]
    if unassigned:
        recommendations.append(
            f"{len(unassigned)} task henüz atanmamış. Otomatik atamayı veya manuel değerlendirmeyi düşünün."
        )

    if missing_skills:
        recommendations.append(
            "Takımda eksik olan beceriler: " + ", ".join(sorted(missing_skills))
        )

    high_priority_unassigned = [
        task for task in unassigned if (task.priority or "").lower() in {"high", "critical"}
    ]
    if high_priority_unassigned:
        recommendations.append(
            f"{len(high_priority_unassigned)} yüksek öncelikli task için acil atama önerilir."
        )

    if not recommendations:
        recommendations.append("Projede önemli bir risk tespit edilmedi.")

    return recommendations


def update_task_status(task: Task, status_name: str, rationale: Optional[str] = None,
                        decided_by: str = "llm") -> Task:
    """Task durumunu güncelle ve açıklama ekle."""
    task.status_name = status_name
    task.updated_at = datetime.utcnow()
    task.decided_by = decided_by
    task.decided_at = datetime.utcnow()
    if rationale:
        task.rationale = rationale

    db.session.add(task)
    return task


def auto_assign_tasks(project: Project, limit: Optional[int] = None) -> List[Dict[str, object]]:
    """Projeye bağlı task'ları beceri eşleşmesine göre otomatik ata."""
    candidates = _gather_assignment_candidates(project)
    assignments: List[Dict[str, object]] = []

    for task in project.tasks:
        if task.assignee_id:
            continue
        if limit is not None and len(assignments) >= limit:
            break

        best_employee, score, matched_skills = _select_best_candidate(task, candidates)
        if not best_employee:
            continue

        task.assignee_id = best_employee.id
        task.assignee_score = score
        task.decided_by = "llm_auto"
        task.decided_at = datetime.utcnow()
        task.rationale = (
            "Beceri eşleşmesi (" + ", ".join(matched_skills) + ") ve mevcut kapasiteye göre otomatik atandı."
            if matched_skills else
            "Mevcut kapasiteye göre otomatik atandı."
        )
        task.status_name = task.status_name or "assigned"
        task.updated_at = datetime.utcnow()

        db.session.add(task)
        assignments.append({
            "task_id": task.id,
            "task_title": task.title,
            "assignee": {
                "employee_id": best_employee.employee_id,
                "name": best_employee.name
            },
            "score": score,
            "matched_skills": matched_skills
        })

    return assignments


def _gather_assignment_candidates(project: Project) -> List[Employee]:
    team_members = [member.employee for member in project.team_members if member.employee]
    if team_members:
        return team_members
    return Employee.query.all()


def _select_best_candidate(task: Task, employees: Iterable[Employee]) -> Tuple[Optional[Employee], float, List[str]]:
    required = set(_normalize_skill_names(task.required_skills))
    best_employee: Optional[Employee] = None
    best_score: float = 0.0
    best_match: List[str] = []

    for employee in employees:
        emp_skills = set(_normalize_skill_names(employee.skills))
        matched = sorted(required & emp_skills)
        coverage = len(matched) / len(required) if required else 0.5

        capacity = float(employee.capacity_hours_per_week or 40)
        load = float(employee.current_load_hours or 0)
        remaining_capacity_ratio = max(0.0, min(1.0, (capacity - load) / capacity))

        score = round(0.7 * coverage + 0.3 * remaining_capacity_ratio, 3)

        if score > best_score:
            best_employee = employee
            best_score = score
            best_match = matched

    return best_employee, best_score, best_match
