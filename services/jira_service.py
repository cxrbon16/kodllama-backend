# ============================================
# services/jira_service.py - Jira API İşlemleri
# ============================================
import requests
import json
from requests.auth import HTTPBasicAuth
from typing import Optional, Dict, List

class JiraService:
    """Jira API v3 yönetim servisi"""
    
    def __init__(self, domain: str, email: str, api_token: str, project_key: str):
        self.domain = domain.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.project_key = project_key
        
        self.auth = HTTPBasicAuth(email, api_token)
        self.base_url = f"{self.domain}/rest/api/3"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Cache
        self._issue_types = None
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """HTTP isteği gönder"""
        url = f"{self.base_url}{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            auth=self.auth,
            timeout=15,
            **kwargs
        )
        response.raise_for_status()
        return response
    
    def get_issue_types(self) -> List[Dict]:
        """Proje issue type'larını al"""
        if self._issue_types:
            return self._issue_types
        
        try:
            response = self._request(
                "GET",
                f"/issue/createmeta/{self.project_key}/issuetypes"
            )
            self._issue_types = response.json().get('issueTypes', [])
            return self._issue_types
        except:
            return []
    
    def get_issue_type_id(self, issue_type_name: str) -> Optional[str]:
        """Issue type adından ID bul"""
        types = self.get_issue_types()
        for it in types:
            if it['name'].lower() == issue_type_name.lower():
                return it['id']
        return None
    
    def create_task(
        self,
        summary: str,
        issue_type: str = "Task",
        description: Optional[str] = None,
        assignee_id: Optional[str] = None,
        parent_key: Optional[str] = None,
        labels: Optional[List[str]] = None,
        priority: Optional[str] = None
    ) -> Optional[str]:
        """Jira task oluştur"""
        
        issue_type_id = self.get_issue_type_id(issue_type)
        if not issue_type_id:
            raise ValueError(f"Issue type '{issue_type}' not found")
        
        fields = {
            "project": {"key": self.project_key},
            "summary": summary,
            "issuetype": {"id": issue_type_id}
        }
        
        if description:
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}]
                }]
            }
        
        if assignee_id:
            fields["assignee"] = {"accountId": assignee_id}
        
        if parent_key:
            fields["parent"] = {"key": parent_key}
        
        if labels:
            fields["labels"] = labels
        
        # Priority mapping
        if priority:
            priority_map = {
                "high": "High",
                "medium": "Medium",
                "low": "Low"
            }
            priority_name = priority_map.get(priority.lower(), "Medium")
            # Priority eklemek için field kontrolü gerekebilir
            # fields["priority"] = {"name": priority_name}
        
        payload = {"fields": fields}
        
        try:
            response = self._request(
                "POST",
                "/issue",
                data=json.dumps(payload)
            )
            result = response.json()
            return result['key']
        except Exception as e:
            print(f"Jira create error: {e}")
            return None
    
    def get_task(self, issue_key: str) -> Optional[Dict]:
        """Jira task bilgilerini al"""
        try:
            response = self._request("GET", f"/issue/{issue_key}")
            return response.json()
        except:
            return None
    
    def update_task_status(self, issue_key: str, transition_id: str) -> bool:
        """Task durumunu değiştir"""
        try:
            payload = {"transition": {"id": transition_id}}
            self._request(
                "POST",
                f"/issue/{issue_key}/transitions",
                data=json.dumps(payload)
            )
            return True
        except:
            return False
