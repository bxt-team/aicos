"""iOS Testing Tools for App Testing Agent"""

import os
import subprocess
import json
import time
import re
import plistlib
import tempfile
from typing import Dict, List, Optional, Tuple, Any
from langchain.tools import Tool
from pydantic import BaseModel, Field
from datetime import datetime
import xml.etree.ElementTree as ET
import base64

class IOSTestingTools:
    """Tools for iOS app testing using xcrun simctl and instruments"""
    
    def __init__(self):
        self.xcrun_path = self._find_xcrun()
        self.active_simulator = None
        print(f"iOS Testing Tools initialized with xcrun at: {self.xcrun_path}")
        
    def _find_xcrun(self) -> str:
        """Find xcrun command path"""
        import platform
        
        # Check if we're on macOS
        if platform.system() != 'Darwin':
            print("iOS testing is only available on macOS")
            return 'xcrun'
            
        try:
            # Try to find xcrun
            result = subprocess.run(['which', 'xcrun'], capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip()
                print(f"Found xcrun at: {path}")
                return path
            
            # Try common locations
            common_paths = [
                '/usr/bin/xcrun',
                '/Applications/Xcode.app/Contents/Developer/usr/bin/xcrun'
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    print(f"Found xcrun at common location: {path}")
                    return path
            
            print("xcrun not found, using PATH fallback")
            return 'xcrun'  # Fallback to PATH
        except Exception as e:
            print(f"Error finding xcrun: {str(e)}")
            return 'xcrun'
    
    def _run_command(self, cmd: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        """Execute a command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def list_simulators(self) -> List[Dict[str, str]]:
        """List available iOS simulators"""
        import platform
        
        # Check if we're on macOS
        if platform.system() != 'Darwin':
            return [{
                'udid': 'no-simulator',
                'name': 'iOS testing only available on macOS',
                'state': 'Not Available',
                'runtime': 'N/A',
                'isAvailable': False
            }]
            
        cmd = [self.xcrun_path, 'simctl', 'list', 'devices', '--json']
        success, stdout, stderr = self._run_command(cmd)
        
        if not success:
            print(f"Failed to list iOS simulators: {stderr}")
            # Check if it's because Xcode is not installed
            if 'xcrun: error' in stderr or 'not found' in stderr:
                return [{
                    'udid': 'no-simulator',
                    'name': 'Xcode not installed - Install from App Store',
                    'state': 'Not Available',
                    'runtime': 'N/A',
                    'isAvailable': False
                }]
            return []
        
        try:
            data = json.loads(stdout)
            simulators = []
            
            # Debug: print available runtimes
            print(f"Available runtimes: {list(data.get('devices', {}).keys())}")
            
            for runtime, devices in data.get('devices', {}).items():
                # More flexible runtime matching
                if 'iOS' in runtime or 'com.apple.CoreSimulator.SimRuntime.iOS' in runtime:
                    for device in devices:
                        # Include all devices, not just available ones
                        # Users might need to download simulators
                        simulators.append({
                            'udid': device.get('udid'),
                            'name': device.get('name'),
                            'state': device.get('state', 'Unknown'),
                            'runtime': runtime,
                            'isAvailable': device.get('isAvailable', False)
                        })
            
            # If no iOS simulators found, add a placeholder
            if not simulators:
                simulators.append({
                    'udid': 'no-simulator',
                    'name': 'No iOS Simulators Found - Please install Xcode',
                    'state': 'Not Available',
                    'runtime': 'N/A',
                    'isAvailable': False
                })
            
            print(f"Found {len(simulators)} iOS simulators")
            return simulators
        except Exception as e:
            print(f"Error parsing simulator list: {str(e)}")
            return [{
                'udid': 'error',
                'name': 'Error loading simulators',
                'state': 'Error',
                'runtime': 'N/A',
                'isAvailable': False
            }]
    
    def boot_simulator(self, udid: str) -> bool:
        """Boot an iOS simulator"""
        cmd = [self.xcrun_path, 'simctl', 'boot', udid]
        success, _, _ = self._run_command(cmd)
        
        if success:
            self.active_simulator = udid
            time.sleep(10)  # Wait for boot
            
        return success
    
    def shutdown_simulator(self, udid: str) -> bool:
        """Shutdown an iOS simulator"""
        cmd = [self.xcrun_path, 'simctl', 'shutdown', udid]
        success, _, _ = self._run_command(cmd)
        return success
    
    def install_app(self, udid: str, app_path: str) -> bool:
        """Install an iOS app on simulator"""
        cmd = [self.xcrun_path, 'simctl', 'install', udid, app_path]
        success, _, stderr = self._run_command(cmd, timeout=60)
        return success
    
    def uninstall_app(self, udid: str, bundle_id: str) -> bool:
        """Uninstall an iOS app from simulator"""
        cmd = [self.xcrun_path, 'simctl', 'uninstall', udid, bundle_id]
        success, _, _ = self._run_command(cmd)
        return success
    
    def launch_app(self, udid: str, bundle_id: str) -> bool:
        """Launch an iOS app on simulator"""
        cmd = [self.xcrun_path, 'simctl', 'launch', udid, bundle_id]
        success, stdout, _ = self._run_command(cmd)
        return success
    
    def terminate_app(self, udid: str, bundle_id: str) -> bool:
        """Terminate an iOS app on simulator"""
        cmd = [self.xcrun_path, 'simctl', 'terminate', udid, bundle_id]
        success, _, _ = self._run_command(cmd)
        return success
    
    def get_app_info(self, app_path: str) -> Optional[Dict[str, Any]]:
        """Extract app information from .app bundle"""
        try:
            plist_path = os.path.join(app_path, 'Info.plist')
            if not os.path.exists(plist_path):
                return None
                
            with open(plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
                
            return {
                'bundle_id': plist_data.get('CFBundleIdentifier'),
                'name': plist_data.get('CFBundleName'),
                'version': plist_data.get('CFBundleShortVersionString'),
                'build': plist_data.get('CFBundleVersion'),
                'minimum_os': plist_data.get('MinimumOSVersion')
            }
        except:
            return None
    
    def capture_screenshot(self, udid: str, output_path: str) -> bool:
        """Capture screenshot from iOS simulator"""
        cmd = [self.xcrun_path, 'simctl', 'io', udid, 'screenshot', output_path]
        success, _, _ = self._run_command(cmd)
        return success
    
    def get_accessibility_info(self, udid: str) -> Optional[Dict[str, Any]]:
        """Get accessibility information from current screen"""
        # Create temporary file for accessibility dump
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Use accessibility inspector to dump UI hierarchy
            cmd = [self.xcrun_path, 'simctl', 'spawn', udid, 'log', 'stream', 
                   '--predicate', 'subsystem == "com.apple.Accessibility"', 
                   '--style', 'json']
            
            # This is a simplified version - in practice, you'd use XCTest
            # or Appium for proper accessibility testing
            return {
                'accessible_elements': 0,
                'missing_labels': [],
                'small_touch_targets': [],
                'contrast_issues': []
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def get_performance_data(self, udid: str, bundle_id: str) -> Dict[str, Any]:
        """Get performance metrics for running app"""
        metrics = {
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'network_usage': 0,
            'fps': 0
        }
        
        # Get process info
        cmd = [self.xcrun_path, 'simctl', 'spawn', udid, 'ps', 'aux']
        success, stdout, _ = self._run_command(cmd)
        
        if success:
            for line in stdout.split('\n'):
                if bundle_id in line:
                    parts = line.split()
                    if len(parts) > 3:
                        metrics['cpu_usage'] = float(parts[2])
                        metrics['memory_usage'] = float(parts[3])
        
        return metrics
    
    def get_console_logs(self, udid: str, bundle_id: str, 
                        last_n_lines: int = 100) -> List[str]:
        """Get console logs for app"""
        cmd = [self.xcrun_path, 'simctl', 'spawn', udid, 'log', 'show',
               '--predicate', f'processImagePath CONTAINS "{bundle_id}"',
               '--last', str(last_n_lines)]
        
        success, stdout, _ = self._run_command(cmd, timeout=10)
        
        if success:
            return stdout.split('\n')
        return []
    
    def simulate_touch(self, udid: str, x: int, y: int) -> bool:
        """Simulate touch at coordinates"""
        # Note: This requires additional tools like Appium or XCTest
        # This is a placeholder for the actual implementation
        return True
    
    def simulate_swipe(self, udid: str, start_x: int, start_y: int, 
                      end_x: int, end_y: int, duration: float = 0.5) -> bool:
        """Simulate swipe gesture"""
        # Note: This requires additional tools like Appium or XCTest
        # This is a placeholder for the actual implementation
        return True
    
    def enter_text(self, udid: str, text: str) -> bool:
        """Enter text in focused field"""
        # Simulate text input
        for char in text:
            cmd = [self.xcrun_path, 'simctl', 'io', udid, 'keyboard', char]
            self._run_command(cmd)
        return True
    
    def press_button(self, udid: str, button: str) -> bool:
        """Press hardware button (home, lock, volume)"""
        valid_buttons = ['home', 'lock', 'volume up', 'volume down']
        if button.lower() not in valid_buttons:
            return False
            
        cmd = [self.xcrun_path, 'simctl', 'io', udid, 'press', button]
        success, _, _ = self._run_command(cmd)
        return success
    
    def record_video(self, udid: str, output_path: str, duration: int = 30) -> bool:
        """Record video from simulator"""
        cmd = [self.xcrun_path, 'simctl', 'io', udid, 'recordVideo', 
               '--time-limit', str(duration), output_path]
        success, _, _ = self._run_command(cmd, timeout=duration + 10)
        return success


def create_ios_testing_tools() -> List[Tool]:
    """Create iOS testing tools for CrewAI"""
    ios_tools = IOSTestingTools()
    
    tools = [
        Tool(
            name="list_ios_simulators",
            func=lambda _: ios_tools.list_simulators(),
            description="List available iOS simulators"
        ),
        Tool(
            name="boot_ios_simulator",
            func=lambda udid: ios_tools.boot_simulator(udid),
            description="Boot an iOS simulator by UDID"
        ),
        Tool(
            name="install_ios_app",
            func=lambda params: ios_tools.install_app(
                params.split(',')[0], params.split(',')[1]
            ),
            description="Install iOS app. Format: 'udid,app_path'"
        ),
        Tool(
            name="launch_ios_app",
            func=lambda params: ios_tools.launch_app(
                params.split(',')[0], params.split(',')[1]
            ),
            description="Launch iOS app. Format: 'udid,bundle_id'"
        ),
        Tool(
            name="capture_ios_screenshot",
            func=lambda params: ios_tools.capture_screenshot(
                params.split(',')[0], params.split(',')[1]
            ),
            description="Capture iOS screenshot. Format: 'udid,output_path'"
        ),
        Tool(
            name="get_ios_performance",
            func=lambda params: ios_tools.get_performance_data(
                params.split(',')[0], params.split(',')[1]
            ),
            description="Get iOS app performance data. Format: 'udid,bundle_id'"
        ),
        Tool(
            name="get_ios_logs",
            func=lambda params: ios_tools.get_console_logs(
                params.split(',')[0], params.split(',')[1]
            ),
            description="Get iOS app console logs. Format: 'udid,bundle_id'"
        ),
        Tool(
            name="ios_touch",
            func=lambda params: ios_tools.simulate_touch(
                params.split(',')[0], 
                int(params.split(',')[1]), 
                int(params.split(',')[2])
            ),
            description="Simulate touch. Format: 'udid,x,y'"
        ),
        Tool(
            name="ios_swipe",
            func=lambda params: ios_tools.simulate_swipe(
                params.split(',')[0],
                int(params.split(',')[1]),
                int(params.split(',')[2]),
                int(params.split(',')[3]),
                int(params.split(',')[4])
            ),
            description="Simulate swipe. Format: 'udid,start_x,start_y,end_x,end_y'"
        ),
        Tool(
            name="ios_enter_text",
            func=lambda params: ios_tools.enter_text(
                params.split(',')[0], ','.join(params.split(',')[1:])
            ),
            description="Enter text in focused field. Format: 'udid,text'"
        )
    ]
    
    return tools