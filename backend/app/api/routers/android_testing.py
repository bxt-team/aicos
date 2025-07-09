"""
Android testing endpoints
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional
import os
import tempfile
import shutil
from pydantic import BaseModel

from app.core.dependencies import get_agent

router = APIRouter(prefix="/api", tags=["android-testing"])

# Request models
class AndroidTestRequest(BaseModel):
    apk_path: str
    test_actions: Optional[List[str]] = None
    target_api_level: Optional[int] = None
    avd_name: Optional[str] = None

class AndroidTestResultRequest(BaseModel):
    test_id: str

# Android testing endpoints
@router.post("/android-test")
async def create_android_test(request: AndroidTestRequest):
    """Create a new Android test"""
    android_testing_agent = get_agent('android_testing_agent')
    if not android_testing_agent:
        raise HTTPException(status_code=503, detail="Android testing agent not available")
    
    result = android_testing_agent.run_test(
        request.apk_path,
        request.test_actions,
        request.target_api_level,
        request.avd_name
    )
    
    return result

@router.get("/android-test/{test_id}")
async def get_android_test(test_id: str):
    """Get Android test results"""
    android_testing_agent = get_agent('android_testing_agent')
    if not android_testing_agent:
        raise HTTPException(status_code=503, detail="Android testing agent not available")
    
    result = android_testing_agent.get_test_result(test_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return result

@router.get("/android-tests")
async def list_android_tests():
    """List all Android tests"""
    android_testing_agent = get_agent('android_testing_agent')
    if not android_testing_agent:
        raise HTTPException(status_code=503, detail="Android testing agent not available")
    
    return android_testing_agent.list_tests()

@router.get("/android-avds")
async def list_android_avds():
    """List available Android Virtual Devices"""
    android_testing_agent = get_agent('android_testing_agent')
    if not android_testing_agent:
        raise HTTPException(status_code=503, detail="Android testing agent not available")
    
    return android_testing_agent.list_avds()

@router.post("/android-test/upload-apk")
async def upload_apk(file: UploadFile = File(...)):
    """Upload an APK file for testing"""
    android_testing_agent = get_agent('android_testing_agent')
    if not android_testing_agent:
        raise HTTPException(status_code=503, detail="Android testing agent not available")
    
    # Ensure file is an APK
    if not file.filename.endswith('.apk'):
        raise HTTPException(status_code=400, detail="File must be an APK")
    
    # Save uploaded file
    temp_dir = tempfile.mkdtemp()
    try:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
        # Move to permanent location
        permanent_path = android_testing_agent.save_apk(file_path, file.filename)
        
        return {
            "success": True,
            "apk_path": permanent_path,
            "filename": file.filename
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@router.get("/android-test/{test_id}/screenshots")
async def get_android_test_screenshots(test_id: str):
    """Get screenshots from Android test"""
    android_testing_agent = get_agent('android_testing_agent')
    if not android_testing_agent:
        raise HTTPException(status_code=503, detail="Android testing agent not available")
    
    screenshots = android_testing_agent.get_test_screenshots(test_id)
    if not screenshots:
        raise HTTPException(status_code=404, detail="No screenshots found for test")
    
    return {"test_id": test_id, "screenshots": screenshots}

@router.delete("/android-test/{test_id}")
async def delete_android_test(test_id: str):
    """Delete an Android test and its artifacts"""
    android_testing_agent = get_agent('android_testing_agent')
    if not android_testing_agent:
        raise HTTPException(status_code=503, detail="Android testing agent not available")
    
    result = android_testing_agent.delete_test(test_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Test not found")
    
    return result