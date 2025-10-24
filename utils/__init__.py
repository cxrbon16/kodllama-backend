from datetime import datetime, timedelta
import re
from typing import Optional

def parse_iso_duration(duration: str) -> Optional[timedelta]:
    """
    ISO 8601 duration string'ini timedelta'ya çevir
    
    Örnek:
        P2D -> 2 gün
        P1W -> 1 hafta
        PT4H -> 4 saat
        P1DT2H -> 1 gün 2 saat
    
    Args:
        duration: ISO 8601 duration string (örn: "P2D", "PT4H")
    
    Returns:
        timedelta object veya None
    """
    if not duration:
        return None
    
    # Regex pattern for ISO 8601 duration
    pattern = r'^P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?'
    match = re.match(pattern, duration)
    
    if not match:
        return None
    
    weeks, days, hours, minutes, seconds = match.groups()
    
    delta = timedelta(
        weeks=int(weeks) if weeks else 0,
        days=int(days) if days else 0,
        hours=int(hours) if hours else 0,
        minutes=int(minutes) if minutes else 0,
        seconds=int(seconds) if seconds else 0
    )
    
    return delta

def duration_to_hours(duration: str) -> Optional[float]:
    """
    Duration string'ini saat cinsine çevir
    
    Örnek:
        P2D -> 48.0
        PT4H -> 4.0
        P1DT2H -> 26.0
    """
    delta = parse_iso_duration(duration)
    if delta:
        return delta.total_seconds() / 3600
    return None

def hours_to_duration(hours: float) -> str:
    """
    Saat değerini ISO 8601 duration'a çevir
    
    Örnek:
        48.0 -> P2D
        4.0 -> PT4H
        26.0 -> P1DT2H
    """
    days = int(hours // 24)
    remaining_hours = int(hours % 24)
    
    if days > 0 and remaining_hours > 0:
        return f"P{days}DT{remaining_hours}H"
    elif days > 0:
        return f"P{days}D"
    else:
        return f"PT{remaining_hours}H"

def calculate_skill_match_score(required_skills: list, employee_skills: list) -> float:
    """
    Gerekli skill'ler ile çalışan skill'leri arasında eşleşme skoru hesapla
    
    Args:
        required_skills: Gerekli skill'ler (string listesi)
        employee_skills: Çalışan skill'leri (dict listesi: [{"name": "python", "level": 5}])
    
    Returns:
        0.0 - 1.0 arası skor
    """
    if not required_skills:
        return 1.0
    
    if not employee_skills:
        return 0.0
    
    # Employee skill'lerini dict'e çevir
    emp_skill_dict = {skill['name'].lower(): skill['level'] for skill in employee_skills}
    
    matched_count = 0
    total_level = 0
    
    for req_skill in required_skills:
        skill_name = req_skill.lower()
        if skill_name in emp_skill_dict:
            matched_count += 1
            total_level += emp_skill_dict[skill_name]
    
    if matched_count == 0:
        return 0.0
    
    # Eşleşme yüzdesi + ortalama skill level
    match_ratio = matched_count / len(required_skills)
    avg_level = total_level / matched_count / 5.0  # Normalize to 0-1
    
    # Weighted score: %70 match ratio, %30 skill level
    score = (match_ratio * 0.7) + (avg_level * 0.3)
    
    return round(score, 2)

def calculate_workload_score(current_load: int, capacity: int) -> float:
    """
    Workload score hesapla (düşük workload = yüksek skor)
    
    Args:
        current_load: Mevcut iş yükü (saat)
        capacity: Haftalık kapasite (saat)
    
    Returns:
        0.0 - 1.0 arası skor
    """
    if capacity == 0:
        return 0.0
    
    load_ratio = current_load / capacity
    
    # Inverse score: az yük = yüksek skor
    if load_ratio >= 1.0:
        return 0.0
    else:
        return round(1.0 - load_ratio, 2)

def calculate_assignment_score(
    required_skills: list,
    employee_skills: list,
    current_load: int,
    capacity: int,
    skill_weight: float = 0.7,
    workload_weight: float = 0.3
) -> dict:
    """
    Task atama için toplam skor hesapla
    
    Args:
        required_skills: Gerekli skill'ler
        employee_skills: Çalışan skill'leri
        current_load: Mevcut yük
        capacity: Kapasite
        skill_weight: Skill skorunun ağırlığı (0-1)
        workload_weight: Workload skorunun ağırlığı (0-1)
    
    Returns:
        {
            "total_score": 0.85,
            "skill_score": 0.9,
            "workload_score": 0.7,
            "breakdown": {...}
        }
    """
    skill_score = calculate_skill_match_score(required_skills, employee_skills)
    workload_score = calculate_workload_score(current_load, capacity)
    
    total_score = (skill_score * skill_weight) + (workload_score * workload_weight)
    
    return {
        "total_score": round(total_score, 2),
        "skill_score": skill_score,
        "workload_score": workload_score,
        "breakdown": {
            "skill_weight": skill_weight,
            "workload_weight": workload_weight,
            "current_load_ratio": round(current_load / capacity, 2) if capacity > 0 else 1.0
        }
    }

def format_jira_description(description: str) -> dict:
    """
    Plain text description'ı Jira ADF formatına çevir
    
    Args:
        description: Plain text açıklama
    
    Returns:
        Jira ADF format dictionary
    """
    if not description:
        return {
            "type": "doc",
            "version": 1,
            "content": []
        }
    
    # Paragrafları ayır
    paragraphs = description.split('\n\n')
    
    content = []
    for para in paragraphs:
        if para.strip():
            content.append({
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": para.strip()
                }]
            })
    
    return {
        "type": "doc",
        "version": 1,
        "content": content
    }

def validate_employee_data(data: dict) -> tuple[bool, str]:
    """
    Employee data validasyonu
    
    Returns:
        (is_valid, error_message)
    """
    required_fields = ['employee_id', 'name']
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Employee ID formatı kontrol
    if not re.match(r'^e\d+', data['employee_id']):
        return False, "Invalid employee_id format. Expected: e14, e42, etc."
    
    return True, ""

def validate_task_data(data: dict) -> tuple[bool, str]:
    """
    Task data validasyonu
    
    Returns:
        (is_valid, error_message)
    """
    required_fields = ['task_id', 'project_id', 'title']
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Priority validation
    valid_priorities = ['high', 'medium', 'low']
    if 'priority' in data and data['priority'].lower() not in valid_priorities:
        return False, f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
    
    return True, ""