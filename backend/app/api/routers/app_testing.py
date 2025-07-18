"""API Router for unified App Testing (iOS and Android)"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import os
import tempfile
import shutil
from datetime import datetime
import hashlib

from app.core.dependencies import get_agent
from app.agents.app_testing_agent import AppTestingAgent
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/app-test", tags=["app-testing"])


def calculate_file_hash(content: bytes) -> str:
    """Calculate SHA256 hash of file content"""
    return hashlib.sha256(content).hexdigest()


def find_existing_app(platform: str, file_hash: str) -> Optional[str]:
    """Find existing app with same hash"""
    upload_dir = os.path.join("storage", "app_uploads", platform.lower())
    if not os.path.exists(upload_dir):
        return None
    
    # Check for hash file
    hash_file = os.path.join(upload_dir, f"{file_hash}.path")
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            return f.read().strip()
    return None


class AppTestRequest(BaseModel):
    """Request model for app testing"""
    platform: str = Field(..., description="Platform: 'android' or 'ios'")
    device_id: Optional[str] = Field(None, description="Optional device/simulator ID")
    test_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional test configuration"
    )


class AppTestResponse(BaseModel):
    """Response model for app test"""
    test_id: str
    platform: str
    status: str
    message: str


class PlatformComparisonRequest(BaseModel):
    """Request model for platform comparison testing"""
    test_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional test configuration for both platforms"
    )


@router.post("/upload-app", response_model=Dict[str, Any])
async def upload_app_for_testing(
    platform: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload an app file for testing
    
    - **platform**: 'android' or 'ios'
    - **file**: APK file for Android or .app bundle (zipped), .ipa for iOS
    """
    if platform.lower() not in ['android', 'ios']:
        raise HTTPException(status_code=400, detail="Platform must be 'android' or 'ios'")
    
    # Validate file extension
    if platform.lower() == 'android' and not file.filename.endswith('.apk'):
        raise HTTPException(status_code=400, detail="Android apps must be .apk files")
    elif platform.lower() == 'ios' and not file.filename.endswith(('.app', '.zip', '.tar.gz', '.tgz', '.ipa')):
        raise HTTPException(status_code=400, detail="iOS apps must be .app bundles, .ipa, .zip, .tar.gz, or .tgz files")
    
    try:
        # Read file content
        content = await file.read()
        file_hash = calculate_file_hash(content)
        
        # Check if file already exists
        existing_path = find_existing_app(platform.lower(), file_hash)
        if existing_path and os.path.exists(existing_path):
            logger.info(f"Reusing existing app: {existing_path}")
            return {
                "message": f"{platform} app already exists, reusing",
                "file_path": existing_path,
                "platform": platform.lower(),
                "reused": True
            }
        
        # Create upload directory
        upload_dir = os.path.join("storage", "app_uploads", platform.lower())
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # For iOS compressed files and .ipa files, extract the .app bundle
        if platform.lower() == 'ios' and (file_path.endswith('.zip') or file_path.endswith('.tar.gz') or file_path.endswith('.tgz') or file_path.endswith('.ipa')):
            logger.info(f"Extracting iOS archive: {file_path}")
            # Determine extract directory name based on file type
            if file_path.endswith('.tar.gz'):
                extract_dir = file_path.replace('.tar.gz', '_extracted')
            elif file_path.endswith('.tgz'):
                extract_dir = file_path.replace('.tgz', '_extracted')
            elif file_path.endswith('.ipa'):
                extract_dir = file_path.replace('.ipa', '_extracted')
            else:
                extract_dir = file_path.replace('.zip', '_extracted')
            
            # Extract the archive
            try:
                if file_path.endswith('.ipa'):
                    # IPA files are ZIP archives, extract as zip
                    shutil.unpack_archive(file_path, extract_dir, format='zip')
                else:
                    shutil.unpack_archive(file_path, extract_dir)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to extract archive: {str(e)}")
            
            # Find .app bundle in extracted files
            app_path = None
            for root, dirs, files in os.walk(extract_dir):
                for dir_name in dirs:
                    if dir_name.endswith('.app'):
                        app_path = os.path.join(root, dir_name)
                        logger.info(f"Found .app bundle at: {app_path}")
                        break
                if app_path:
                    break
                    
            if app_path:
                file_path = app_path
            else:
                # Log directory structure for debugging
                logger.error(f"No .app bundle found in {extract_dir}")
                for root, dirs, files in os.walk(extract_dir):
                    logger.error(f"Directory: {root}")
                    logger.error(f"  Subdirs: {dirs}")
                    logger.error(f"  Files: {files[:5]}...")  # First 5 files
                raise HTTPException(status_code=400, detail="No .app bundle found in archive")
        
        # Save hash mapping for future reuse
        hash_file = os.path.join(upload_dir, f"{file_hash}.path")
        with open(hash_file, 'w') as f:
            f.write(file_path)
        
        logger.info(f"Returning file path: {file_path}")
        return {
            "message": f"{platform} app uploaded successfully",
            "file_path": file_path,
            "platform": platform.lower(),
            "reused": False
        }
        
    except Exception as e:
        logger.error(f"Error uploading app: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload app: {str(e)}")


@router.post("/", response_model=AppTestResponse)
async def create_app_test(
    request: AppTestRequest,
    app_path: str,
    agent: AppTestingAgent = Depends(lambda: get_agent("app_testing"))
):
    """
    Create a new app test
    
    - **platform**: 'android' or 'ios'
    - **app_path**: Path to the app file (from upload endpoint)
    - **device_id**: Optional specific device/simulator to use
    - **test_config**: Optional test configuration
    """
    try:
        # Validate app path exists
        if not os.path.exists(app_path):
            raise HTTPException(status_code=404, detail="App file not found")
        
        # Start test
        result = await agent.test_app(
            platform=request.platform,
            app_path=app_path,
            device_id=request.device_id,
            test_config=request.test_config
        )
        
        return AppTestResponse(
            test_id=result['id'],
            platform=result['platform'],
            status=result['status'],
            message=f"{request.platform.capitalize()} app test started successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating app test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create test: {str(e)}")


@router.get("/{test_id}")
async def get_test_results(
    test_id: str,
    agent: AppTestingAgent = Depends(lambda: get_agent("app_testing"))
):
    """Get test results by ID"""
    result = agent.get_test_results(test_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test not found")
    return result


@router.get("/")
async def list_tests(
    agent: AppTestingAgent = Depends(lambda: get_agent("app_testing"))
):
    """List all test runs"""
    return agent.list_tests()


@router.get("/devices/{platform}")
async def list_available_devices(
    platform: str,
    agent: AppTestingAgent = Depends(lambda: get_agent("app_testing"))
):
    """
    List available devices/simulators for a platform
    
    - **platform**: 'android' or 'ios'
    """
    if platform.lower() not in ['android', 'ios']:
        raise HTTPException(status_code=400, detail="Platform must be 'android' or 'ios'")
        
    devices = agent.get_available_devices(platform)
    return {
        "platform": platform.lower(),
        "devices": devices,
        "count": len(devices)
    }


@router.post("/compare-platforms")
async def compare_platforms(
    request: PlatformComparisonRequest,
    android_apk_path: str,
    ios_app_path: str,
    agent: AppTestingAgent = Depends(lambda: get_agent("app_testing"))
):
    """
    Run comparative testing between Android and iOS versions
    
    - **android_apk_path**: Path to Android APK
    - **ios_app_path**: Path to iOS .app bundle
    - **test_config**: Optional test configuration for both platforms
    """
    try:
        # Validate paths
        if not os.path.exists(android_apk_path):
            raise HTTPException(status_code=404, detail="Android APK not found")
        if not os.path.exists(ios_app_path):
            raise HTTPException(status_code=404, detail="iOS app not found")
        
        # Run comparison
        result = await agent.compare_platforms(
            android_apk=android_apk_path,
            ios_app=ios_app_path,
            test_config=request.test_config
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error comparing platforms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/{test_id}/screenshots")
async def get_test_screenshots(
    test_id: str,
    agent: AppTestingAgent = Depends(lambda: get_agent("app_testing"))
):
    """Get screenshots from a test run"""
    result = agent.get_test_results(test_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test not found")
        
    screenshots = []
    if 'results' in result and 'screenshots' in result['results']:
        for screenshot in result['results']['screenshots']:
            if 'path' in screenshot and os.path.exists(screenshot['path']):
                screenshots.append({
                    'description': screenshot.get('description', 'Screenshot'),
                    'path': screenshot['path'],
                    'timestamp': screenshot.get('timestamp')
                })
                
    return {
        "test_id": test_id,
        "platform": result['platform'],
        "screenshots": screenshots,
        "count": len(screenshots)
    }


@router.delete("/{test_id}")
async def delete_test(
    test_id: str,
    agent: AppTestingAgent = Depends(lambda: get_agent("app_testing"))
):
    """Delete a test and its artifacts"""
    if agent.cleanup_test(test_id):
        return {"message": "Test deleted successfully", "test_id": test_id}
    else:
        raise HTTPException(status_code=404, detail="Test not found")


@router.get("/health/check")
async def health_check(
    agent: AppTestingAgent = Depends(lambda: get_agent("app_testing"))
):
    """Check health status of app testing tools"""
    return agent.health_check()


@router.get("/uploaded-apps/{platform}")
async def list_uploaded_apps(platform: str):
    """
    List previously uploaded apps for a platform
    
    - **platform**: 'android' or 'ios'
    """
    if platform.lower() not in ['android', 'ios']:
        raise HTTPException(status_code=400, detail="Platform must be 'android' or 'ios'")
    
    upload_dir = os.path.join("storage", "app_uploads", platform.lower())
    if not os.path.exists(upload_dir):
        return {"platform": platform.lower(), "apps": []}
    
    apps = []
    for filename in os.listdir(upload_dir):
        if filename.endswith('.path'):
            continue  # Skip hash files
            
        file_path = os.path.join(upload_dir, filename)
        if os.path.isfile(file_path) or (os.path.isdir(file_path) and filename.endswith('.app')):
            # Get file info
            stat = os.stat(file_path)
            apps.append({
                "filename": filename,
                "path": file_path,
                "size": stat.st_size if os.path.isfile(file_path) else 0,
                "uploaded_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "is_directory": os.path.isdir(file_path)
            })
    
    # Sort by upload time (newest first)
    apps.sort(key=lambda x: x['uploaded_at'], reverse=True)
    
    return {
        "platform": platform.lower(),
        "apps": apps,
        "count": len(apps)
    }