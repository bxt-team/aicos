"""File handling utility functions"""
import os
import json
import shutil
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

def save_json_file(data: Dict[str, Any], directory: str, filename: Optional[str] = None) -> str:
    """Save data as JSON file and return the filepath"""
    os.makedirs(directory, exist_ok=True)
    
    if not filename:
        filename = f"{str(uuid.uuid4())}.json"
    
    filepath = os.path.join(directory, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filepath

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load JSON file and return data"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def ensure_directory(path: str) -> str:
    """Ensure directory exists and return the path"""
    os.makedirs(path, exist_ok=True)
    return path

def cleanup_old_files(directory: str, days: int = 30):
    """Remove files older than specified days"""
    if not os.path.exists(directory):
        return
    
    cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            if os.path.getmtime(filepath) < cutoff_time:
                os.remove(filepath)

def copy_file_with_metadata(source: str, destination: str, metadata: Dict[str, Any]):
    """Copy file and save associated metadata"""
    # Copy the file
    shutil.copy2(source, destination)
    
    # Save metadata
    metadata_path = destination.replace(os.path.splitext(destination)[1], '_metadata.json')
    save_json_file(metadata, os.path.dirname(metadata_path), os.path.basename(metadata_path))
    
    return destination, metadata_path