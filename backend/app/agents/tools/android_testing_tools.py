"""Android Testing Tools for App Testing Agent"""

import os
import subprocess
import json
import time
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from langchain.tools import Tool
from datetime import datetime
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)


class AndroidTestingTools:
    """Tools for Android app testing using ADB"""
    
    def __init__(self, adb_path: Optional[str] = None):
        self.adb_path = adb_path or os.environ.get("ADB_PATH", "adb")
        self.device_id = None
        logger.info(f"Android Testing Tools initialized with adb at: {self.adb_path}")
        
    def _run_adb_command(self, cmd: List[str]) -> Tuple[bool, str, str]:
        """Execute an ADB command and return success, stdout, stderr"""
        try:
            full_cmd = [self.adb_path]
            if self.device_id:
                full_cmd.extend(["-s", self.device_id])
            full_cmd.extend(cmd)
            
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def list_avds(self) -> List[Dict[str, str]]:
        """List available Android Virtual Devices"""
        try:
            # Try to find emulator command
            emulator_path = os.path.join(os.path.dirname(self.adb_path), "emulator")
            if not os.path.exists(emulator_path):
                emulator_path = "emulator"
                
            result = subprocess.run(
                [emulator_path, "-list-avds"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return []
                
            avds = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    avds.append({
                        'name': line.strip(),
                        'status': 'available'
                    })
            return avds
        except:
            return []
    
    def install_apk(self, apk_path: str) -> bool:
        """Install an APK on the device"""
        success, stdout, stderr = self._run_adb_command(["install", "-r", apk_path])
        if success:
            logger.info(f"Successfully installed APK: {apk_path}")
        else:
            logger.error(f"Failed to install APK: {stderr}")
        return success
    
    def launch_app(self, package_name: str) -> bool:
        """Launch an Android app by package name"""
        # Try to find the main activity
        success, stdout, _ = self._run_adb_command([
            "shell", "cmd", "package", "resolve-activity", 
            "--brief", package_name
        ])
        
        if success and "/" in stdout:
            activity = stdout.strip().split('\n')[0]
            success, _, _ = self._run_adb_command([
                "shell", "am", "start", "-n", activity
            ])
            return success
        return False
    
    def capture_screenshot(self, output_path: str) -> bool:
        """Capture a screenshot from the device"""
        # Take screenshot on device
        device_path = "/sdcard/screenshot.png"
        success, _, _ = self._run_adb_command([
            "shell", "screencap", "-p", device_path
        ])
        
        if success:
            # Pull screenshot to local machine
            success, _, _ = self._run_adb_command([
                "pull", device_path, output_path
            ])
            
            # Clean up device screenshot
            self._run_adb_command(["shell", "rm", device_path])
            
        return success
    
    def get_ui_hierarchy(self) -> Optional[str]:
        """Get the UI hierarchy dump"""
        device_path = "/sdcard/ui_dump.xml"
        success, _, _ = self._run_adb_command([
            "shell", "uiautomator", "dump", device_path
        ])
        
        if success:
            success, stdout, _ = self._run_adb_command([
                "shell", "cat", device_path
            ])
            
            # Clean up
            self._run_adb_command(["shell", "rm", device_path])
            
            if success:
                return stdout
        return None
    
    def get_performance_metrics(self, package_name: str) -> Dict[str, Any]:
        """Get performance metrics for an app"""
        metrics = {
            'cpu_usage': 0,
            'memory_usage': 0,
            'frame_stats': {}
        }
        
        # Get memory info
        success, stdout, _ = self._run_adb_command([
            "shell", "dumpsys", "meminfo", package_name
        ])
        
        if success:
            for line in stdout.split('\n'):
                if "TOTAL" in line and "TOTAL SWAP" not in line:
                    parts = line.split()
                    if len(parts) > 1 and parts[1].isdigit():
                        metrics['memory_usage'] = int(parts[1]) * 1024  # Convert to KB
                        break
        
        # Get CPU usage
        success, stdout, _ = self._run_adb_command([
            "shell", "top", "-n", "1"
        ])
        
        if success:
            for line in stdout.split('\n'):
                if package_name in line:
                    parts = line.split()
                    if len(parts) > 8:
                        try:
                            cpu = parts[8].rstrip('%')
                            metrics['cpu_usage'] = float(cpu)
                        except:
                            pass
                    break
        
        return metrics
    
    def check_accessibility(self) -> Dict[str, Any]:
        """Check accessibility issues in current screen"""
        ui_dump = self.get_ui_hierarchy()
        if not ui_dump:
            return {'issues': [], 'score': 0}
            
        issues = []
        total_elements = 0
        accessible_elements = 0
        
        try:
            root = ET.fromstring(ui_dump)
            for node in root.iter('node'):
                total_elements += 1
                
                # Check for content description
                content_desc = node.get('content-desc', '')
                text = node.get('text', '')
                clickable = node.get('clickable', 'false') == 'true'
                
                if clickable:
                    if content_desc or text:
                        accessible_elements += 1
                    else:
                        bounds = node.get('bounds', '')
                        issues.append({
                            'type': 'missing_content_description',
                            'element': node.get('class', 'Unknown'),
                            'bounds': bounds
                        })
                        
        except:
            pass
            
        score = (accessible_elements / max(1, total_elements)) * 100
        
        return {
            'issues': issues[:10],  # Limit to 10 issues
            'score': round(score, 2),
            'total_elements': total_elements,
            'accessible_elements': accessible_elements
        }
    
    def tap_element(self, x: int, y: int) -> bool:
        """Tap at specific coordinates"""
        success, _, _ = self._run_adb_command([
            "shell", "input", "tap", str(x), str(y)
        ])
        return success
    
    def scroll(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        """Perform scroll gesture"""
        success, _, _ = self._run_adb_command([
            "shell", "input", "swipe", 
            str(start_x), str(start_y), 
            str(end_x), str(end_y), 
            "300"  # duration in ms
        ])
        return success
    
    def enter_text(self, text: str) -> bool:
        """Enter text in focused field"""
        # Escape special characters
        escaped_text = text.replace(' ', '%s').replace("'", "\\'")
        success, _, _ = self._run_adb_command([
            "shell", "input", "text", escaped_text
        ])
        return success
    
    def get_logcat(self, package_name: Optional[str] = None, lines: int = 100) -> List[str]:
        """Get logcat output"""
        cmd = ["logcat", "-d", "-t", str(lines)]
        if package_name:
            cmd.extend(["-s", f"{package_name}:*"])
            
        success, stdout, _ = self._run_adb_command(cmd)
        
        if success:
            return stdout.split('\n')
        return []
    
    # Tool creation methods for CrewAI
    def install_apk_tool(self) -> Tool:
        """Create install APK tool"""
        return Tool(
            name="install_android_apk",
            func=lambda path: self.install_apk(path),
            description="Install an Android APK file. Input: 'path/to/app.apk'"
        )
    
    def launch_app_tool(self) -> Tool:
        """Create launch app tool"""
        return Tool(
            name="launch_android_app",
            func=lambda package: self.launch_app(package),
            description="Launch Android app by package name. Input: 'com.example.app'"
        )
    
    def capture_screenshot_tool(self) -> Tool:
        """Create screenshot tool"""
        return Tool(
            name="capture_android_screenshot",
            func=lambda path: self.capture_screenshot(path),
            description="Capture Android screenshot. Input: 'path/to/save/screenshot.png'"
        )
    
    def analyze_ui_hierarchy_tool(self) -> Tool:
        """Create UI analysis tool"""
        return Tool(
            name="analyze_android_ui",
            func=lambda _: self.get_ui_hierarchy(),
            description="Get Android UI hierarchy XML dump"
        )
    
    def get_performance_metrics_tool(self) -> Tool:
        """Create performance metrics tool"""
        return Tool(
            name="get_android_performance",
            func=lambda package: self.get_performance_metrics(package),
            description="Get Android app performance metrics. Input: 'com.example.app'"
        )
    
    def check_accessibility_tool(self) -> Tool:
        """Create accessibility check tool"""
        return Tool(
            name="check_android_accessibility",
            func=lambda _: self.check_accessibility(),
            description="Check Android accessibility issues on current screen"
        )
    
    def tap_element_tool(self) -> Tool:
        """Create tap tool"""
        return Tool(
            name="tap_android_element",
            func=lambda coords: self.tap_element(
                int(coords.split(',')[0]), 
                int(coords.split(',')[1])
            ),
            description="Tap Android screen at coordinates. Input: 'x,y'"
        )
    
    def scroll_tool(self) -> Tool:
        """Create scroll tool"""
        return Tool(
            name="scroll_android_screen",
            func=lambda coords: self.scroll(
                int(coords.split(',')[0]),
                int(coords.split(',')[1]),
                int(coords.split(',')[2]),
                int(coords.split(',')[3])
            ),
            description="Scroll Android screen. Input: 'start_x,start_y,end_x,end_y'"
        )
    
    def enter_text_tool(self) -> Tool:
        """Create text input tool"""
        return Tool(
            name="enter_android_text",
            func=lambda text: self.enter_text(text),
            description="Enter text in focused Android field. Input: 'text to enter'"
        )
    
    def get_logcat_tool(self) -> Tool:
        """Create logcat tool"""
        return Tool(
            name="get_android_logs",
            func=lambda package: self.get_logcat(package if package else None),
            description="Get Android logcat output. Input: 'com.example.app' or empty for all"
        )
    
    def list_avds_tool(self) -> Tool:
        """Create AVD listing tool"""
        return Tool(
            name="list_android_avds",
            func=lambda _: self.list_avds(),
            description="List available Android Virtual Devices (AVDs)"
        )