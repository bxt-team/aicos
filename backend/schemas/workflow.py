from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class WorkflowCreateRequest(BaseModel):
    period: str
    workflow_type: Optional[str] = "full"
    options: Optional[Dict[str, Any]] = None

class AndroidTestRequest(BaseModel):
    apk_path: str
    test_actions: Optional[List[str]] = None
    target_api_level: Optional[int] = None
    avd_name: Optional[str] = None

class AndroidTestResultRequest(BaseModel):
    test_id: str