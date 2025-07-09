import os
import json
import hashlib
import subprocess
import asyncio
import tempfile
import shutil
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
import time
from pathlib import Path
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from src.crews.base_crew import BaseCrew
from crewai.llm import LLM


class AndroidTestingAgent(BaseCrew):
    """Agent for automated Android app testing and quality assurance."""
    
    def __init__(self, openai_api_key: str, adb_path: str = "adb"):
        super().__init__()
        self.openai_api_key = openai_api_key
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        self.adb_path = adb_path
        self.device_serial = None  # Will be set when a device is selected
        
        # Set up logging
        self.logger = logging.getLogger('AndroidTestingAgent')
        self.logger.setLevel(logging.DEBUG)
        
        # Create console handler with formatting
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        self.logger.info(f"Initialisiere AndroidTestingAgent mit ADB-Pfad: {adb_path}")
        
        # Storage for test results
        self.storage_file = os.path.join(
            os.path.dirname(__file__), 
            "../../static/android_test_results.json"
        )
        self.storage = self._load_storage()
        
        # Screenshot directory
        self.screenshot_dir = os.path.join(
            os.path.dirname(__file__), 
            "../../static/android_screenshots"
        )
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # Create the testing agent
        self.agent = self.create_agent("android_testing_agent", llm=self.llm)
        
        # Test configuration defaults
        self.default_test_actions = [
            "tap_all_buttons",
            "scroll_all_views", 
            "input_text_fields",
            "navigate_back",
            "check_permissions"
        ]
        
        # Performance thresholds
        self.performance_thresholds = {
            "startup_time_ms": 3000,
            "frame_rate_fps": 30,
            "memory_usage_mb": 200,
            "cpu_usage_percent": 80,
            "battery_drain_percent_per_hour": 10
        }
        
    def _load_storage(self) -> Dict[str, Any]:
        """Load test results from storage."""
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_storage(self):
        """Save test results to storage."""
        with open(self.storage_file, 'w') as f:
            json.dump(self.storage, f, indent=2)
    
    def _generate_test_id(self, apk_path: str) -> str:
        """Generate unique test ID based on APK."""
        with open(apk_path, 'rb') as f:
            apk_hash = hashlib.md5(f.read()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"test_{apk_hash}_{timestamp}"
    
    async def _get_devices(self) -> List[Dict[str, str]]:
        """Get list of connected devices/emulators."""
        stdout, _ = await self._run_adb_command(["devices", "-l"], use_device=False)
        devices = []
        
        for line in stdout.strip().split('\n')[1:]:  # Skip header
            if line.strip():
                parts = line.split()
                if len(parts) >= 2 and parts[1] == 'device':
                    device_info = {
                        'serial': parts[0],
                        'status': parts[1],
                        'type': 'emulator' if 'emulator' in parts[0] else 'device'
                    }
                    # Parse additional info
                    for part in parts[2:]:
                        if ':' in part:
                            key, value = part.split(':', 1)
                            device_info[key] = value
                    devices.append(device_info)
        
        return devices
    
    async def _select_device(self) -> Optional[str]:
        """Select a device to use for testing."""
        devices = await self._get_devices()
        
        if not devices:
            self.logger.error("No devices found")
            return None
        
        # Prefer emulators over physical devices
        emulators = [d for d in devices if d['type'] == 'emulator']
        if emulators:
            self.device_serial = emulators[0]['serial']
            self.logger.info(f"Emulator ausgewählt: {self.device_serial}")
        else:
            self.device_serial = devices[0]['serial']
            self.logger.info(f"Gerät ausgewählt: {self.device_serial}")
        
        return self.device_serial
    
    async def _run_adb_command(self, command: List[str], use_device: bool = True) -> Tuple[str, str]:
        """Run ADB command asynchronously."""
        if use_device and self.device_serial:
            full_command = [self.adb_path, "-s", self.device_serial] + command
        else:
            full_command = [self.adb_path] + command
            
        self.logger.debug(f"Running ADB command: {' '.join(full_command)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stderr and "more than one device" in stderr.decode():
                # If multiple devices error, try to select one
                if not self.device_serial:
                    await self._select_device()
                    if self.device_serial:
                        # Retry with selected device
                        return await self._run_adb_command(command, use_device)
            
            if stderr:
                self.logger.warning(f"ADB command stderr: {stderr.decode()[:200]}")
            
            return stdout.decode(), stderr.decode()
        except Exception as e:
            self.logger.error(f"Error running ADB command: {e}")
            raise
    
    def _run_adb_command_sync(self, command: List[str], use_device: bool = True) -> Tuple[str, str]:
        """Run ADB command synchronously."""
        if use_device and self.device_serial:
            full_command = [self.adb_path, "-s", self.device_serial] + command
        else:
            full_command = [self.adb_path] + command
            
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr
    
    async def _check_emulator_running(self) -> bool:
        """Check if an Android emulator is running."""
        self.logger.info("Prüfe ob Android-Emulator läuft...")
        devices = await self._get_devices()
        
        emulators = [d for d in devices if d['type'] == 'emulator']
        if emulators:
            self.logger.info(f"Gefunden: {len(emulators)} laufende(r) Emulator(en)")
            return True
        
        self.logger.warning("Kein laufender Emulator gefunden")
        return False
    
    async def _start_emulator(self, avd_name: Optional[str] = None) -> bool:
        """Start Android emulator if not running."""
        self.logger.info("Attempting to start Android emulator...")
        
        if await self._check_emulator_running():
            self.logger.info("Emulator läuft bereits, überspringe Start")
            return True
            
        # Try to start emulator with given AVD name or default
        if not avd_name:
            self.logger.info("No AVD specified, listing available AVDs...")
            # List available AVDs
            result = subprocess.run(
                ["emulator", "-list-avds"],
                capture_output=True,
                text=True
            )
            avds = result.stdout.strip().split('\n')
            self.logger.debug(f"Available AVDs: {avds}")
            
            if not avds or not avds[0]:
                self.logger.error("Keine AVDs gefunden. Bitte erstellen Sie zuerst ein AVD.")
                return False
            avd_name = avds[0]
            self.logger.info(f"Selected AVD: {avd_name}")
        
        # Start emulator in background
        self.logger.info(f"Starting emulator with AVD: {avd_name}")
        subprocess.Popen(
            ["emulator", "-avd", avd_name, "-no-snapshot"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Wait for emulator to be ready
        max_wait = 60
        start_time = time.time()
        self.logger.info(f"Waiting up to {max_wait} seconds for emulator to start...")
        
        while time.time() - start_time < max_wait:
            elapsed = int(time.time() - start_time)
            self.logger.debug(f"Waiting for emulator... ({elapsed}s elapsed)")
            
            if await self._check_emulator_running():
                self.logger.info("Emulator detected, waiting 5 more seconds for full boot...")
                await asyncio.sleep(5)  # Extra time for full boot
                self.logger.info("Emulator startup complete")
                return True
            await asyncio.sleep(2)
        
        self.logger.error(f"Emulator failed to start within {max_wait} seconds")
        return False
    
    async def _install_apk(self, app_path: str) -> bool:
        """Install APK on emulator."""
        file_ext = os.path.splitext(app_path)[1].lower()
        
        if file_ext == '.apk':
            return await self._install_apk_file(app_path)
        else:
            self.logger.error(f"Unsupported file type for installation: {file_ext}. Only .apk files are supported.")
            return False
    
    async def _install_apk_file(self, apk_path: str) -> bool:
        """Install APK file on emulator."""
        self.logger.info(f"Installiere APK: {apk_path}")
        stdout, stderr = await self._run_adb_command(["install", "-r", apk_path])
        
        if "Success" in stdout:
            self.logger.info("APK-Installation erfolgreich")
            return True
        else:
            self.logger.error(f"APK-Installation fehlgeschlagen. Ausgabe: {stdout[:200]}")
            return False
    
    
    
    async def _get_package_name(self, app_path: str) -> Optional[str]:
        """Extract package name from APK file."""
        self.logger.info(f"Extracting package name from: {app_path}")
        
        # Determine file type
        file_ext = os.path.splitext(app_path)[1].lower()
        
        if file_ext == '.apk':
            return await self._get_package_name_from_apk(app_path)
        else:
            self.logger.error(f"Unsupported file type: {file_ext}. Only .apk files are supported.")
            return None
    
    async def _get_package_name_from_apk(self, apk_path: str) -> Optional[str]:
        """Extract package name from APK using aapt."""
        self.logger.info(f"Extracting package name from APK: {apk_path}")
        
        try:
            # Use aapt to get package info
            # Try to find aapt in common locations
            aapt_path = "aapt"
            android_home = os.environ.get("ANDROID_HOME")
            if android_home:
                # Check build-tools directories
                build_tools_dir = os.path.join(android_home, "build-tools")
                if os.path.exists(build_tools_dir):
                    # Get the latest build-tools version
                    versions = sorted([d for d in os.listdir(build_tools_dir) if os.path.isdir(os.path.join(build_tools_dir, d))], reverse=True)
                    for version in versions:
                        possible_aapt = os.path.join(build_tools_dir, version, "aapt")
                        if os.path.exists(possible_aapt):
                            aapt_path = possible_aapt
                            break
            
            result = subprocess.run(
                [aapt_path, "dump", "badging", apk_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                match = re.search(r"package: name='([^']+)'", result.stdout)
                if match:
                    package_name = match.group(1)
                    self.logger.info(f"Found package name: {package_name}")
                    return package_name
                else:
                    self.logger.error("Could not parse package name from aapt output")
            else:
                self.logger.error(f"aapt command failed with return code: {result.returncode}")
                self.logger.error(f"Error output: {result.stderr[:200]}")
        except FileNotFoundError:
            self.logger.error("aapt command not found. Make sure Android SDK build-tools are installed.")
        except Exception as e:
            self.logger.error(f"Error extracting package name: {e}")
        
        return None
    
    
    
    async def _launch_app(self, package_name: str) -> bool:
        """Launch the app by package name."""
        self.logger.info(f"Starte App: {package_name}")
        
        # Get main activity
        self.logger.debug("Attempting to find main activity...")
        stdout, _ = await self._run_adb_command([
            "shell", "pm", "dump", package_name, "|", "grep", "-A", "1", "MAIN"
        ])
        
        # Try monkey as fallback to launch
        self.logger.info("Using monkey to launch app...")
        stdout, stderr = await self._run_adb_command([
            "shell", "monkey", "-p", package_name, "-c", 
            "android.intent.category.LAUNCHER", "1"
        ])
        
        if "Events injected: 1" in stdout:
            self.logger.info("App erfolgreich gestartet")
            return True
        else:
            self.logger.error(f"App-Start fehlgeschlagen. Ausgabe: {stdout[:200]}")
            return False
    
    async def _capture_screenshot(self, test_id: str, name: str, action_description: str = "") -> Dict[str, Any]:
        """Capture screenshot from device with AI description."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_id}_{name}_{timestamp}.png"
        filepath = os.path.join(self.screenshot_dir, filename)
        
        self.logger.debug(f"Erfasse Screenshot: {name}")
        
        screenshot_data = {
            "filename": filename,
            "filepath": filepath,
            "name": name,
            "timestamp": timestamp,
            "action": action_description,
            "description": "",
            "ui_elements_found": []
        }
        
        try:
            # Capture on device
            device_path = f"/sdcard/{filename}"
            await self._run_adb_command(["shell", "screencap", "-p", device_path])
            
            # Pull to local
            await self._run_adb_command(["pull", device_path, filepath])
            
            # Clean up device
            await self._run_adb_command(["shell", "rm", device_path])
            
            self.logger.debug(f"Screenshot gespeichert: {filepath}")
            
            # Get AI description of the screenshot
            try:
                ui_dump = await self._get_ui_dump()
                if ui_dump:
                    description = await self._analyze_screenshot_content(ui_dump, filepath, action_description)
                    screenshot_data["description"] = description["screen_description"]
                    screenshot_data["ui_elements_found"] = description["elements_found"]
            except Exception as e:
                self.logger.warning(f"Could not analyze screenshot: {e}")
            
            # Store screenshot metadata
            if test_id not in self.storage:
                self.storage[test_id] = {"screenshots": {}}
            if "screenshots" not in self.storage[test_id]:
                self.storage[test_id]["screenshots"] = {}
            
            self.storage[test_id]["screenshots"][name] = screenshot_data
            self._save_storage()
            
            return screenshot_data
        except Exception as e:
            self.logger.error(f"Screenshot konnte nicht erfasst werden: {e}")
            return screenshot_data
    
    async def _analyze_screenshot_content(self, ui_dump: str, screenshot_path: str, action_performed: str) -> Dict[str, Any]:
        """Analyze screenshot content using AI to describe what's visible."""
        try:
            # Parse UI dump to get key elements
            elements = self._parse_clickable_elements_improved(ui_dump)
            self.logger.info(f"Parsed {len(elements)} elements from UI dump")
            
            input_fields = []
            buttons = []
            
            # Categorize elements
            for elem in elements:
                class_name = elem.get('class', '').lower()
                text = elem.get('text', '')
                
                if 'edittext' in class_name:
                    input_fields.append({
                        'type': 'input',
                        'text': text,
                        'hint': elem.get('content_desc', ''),
                        'filled': bool(text and text.strip())
                    })
                elif 'button' in class_name or elem.get('clickable'):
                    buttons.append({
                        'type': 'button',
                        'text': text or elem.get('content_desc', 'Unnamed button')
                    })
            
            self.logger.info(f"Found {len(input_fields)} input fields and {len(buttons)} buttons")
            
            # If no elements found, just return basic info
            if len(elements) == 0:
                return {
                    "screen_description": f"Screen after {action_performed or 'initial load'}. No interactive elements detected.",
                    "elements_found": {
                        "input_fields": [],
                        "buttons": [],
                        "total_elements": 0
                    }
                }
            
            # Try simpler description without AI if CrewAI fails
            try:
                # Create AI task to analyze the screen
                analyze_task = Task(
                    description=f"""
                    Analyze this Android app screen based on the UI hierarchy.
                    
                    Action just performed: {action_performed if action_performed else "Initial screen load"}
                    
                    Found elements:
                    - Input fields: {len(input_fields)} (Filled: {sum(1 for f in input_fields if f['filled'])})
                    - Buttons: {len(buttons)}
                    
                    Input field details: {input_fields[:5]}  # First 5 fields
                    Button details: {buttons[:5]}  # First 5 buttons
                    
                    Provide a brief description of:
                    1. What screen/activity is this (login, home, settings, etc.)?
                    2. What input fields are visible and their state (filled/empty)?
                    3. What actions are available (buttons, navigation)?
                    4. Any issues noticed (missing labels, unclear UI, etc.)?
                    
                    Be concise but informative.
                    """,
                    expected_output="A brief description of the screen content and available actions",
                    agent=self.agent
                )
                
                crew = Crew(
                    agents=[self.agent],
                    tasks=[analyze_task],
                    verbose=False
                )
                
                result = crew.kickoff()
                ai_description = str(result)
                
            except Exception as crew_error:
                self.logger.warning(f"CrewAI analysis failed: {crew_error}, using fallback description")
                # Fallback description without AI
                ai_description = self._generate_fallback_description(action_performed, input_fields, buttons)
            
            return {
                "screen_description": ai_description,
                "elements_found": {
                    "input_fields": input_fields,
                    "buttons": buttons,
                    "total_elements": len(elements)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing screenshot: {e}", exc_info=True)
            # Return basic info even on error
            return {
                "screen_description": f"Screen analysis failed. Action performed: {action_performed or 'initial load'}",
                "elements_found": {
                    "input_fields": [],
                    "buttons": [],
                    "total_elements": 0
                }
            }
    
    def _generate_fallback_description(self, action_performed: str, input_fields: List[Dict], buttons: List[Dict]) -> str:
        """Generate a basic description without AI when CrewAI fails."""
        description = f"Screen after {action_performed or 'initial load'}. "
        
        if input_fields:
            filled = sum(1 for f in input_fields if f['filled'])
            description += f"Found {len(input_fields)} input field(s) ({filled} filled). "
        
        if buttons:
            button_texts = [b['text'] for b in buttons[:3] if b['text']]
            if button_texts:
                description += f"Buttons: {', '.join(button_texts)}. "
        
        return description
    
    async def _get_ui_dump(self) -> str:
        """Get UI hierarchy dump with improved error handling."""
        self.logger.debug("Getting UI hierarchy dump...")
        
        try:
            device_path = "/sdcard/ui_dump.xml"
            
            # Clear any existing dump first
            await self._run_adb_command(["shell", "rm", "-f", device_path])
            
            # Dump UI hierarchy
            stdout, stderr = await self._run_adb_command(["shell", "uiautomator", "dump", device_path])
            
            # Check if dump was successful
            if "UI hierchary dumped to" in stdout or "dumped to" in stdout:
                self.logger.debug("UI dump command successful")
            else:
                self.logger.warning(f"Unexpected dump output: {stdout}")
            
            # Wait a bit for file to be written
            await asyncio.sleep(0.5)
            
            # Read the dump file
            stdout, _ = await self._run_adb_command(["shell", "cat", device_path])
            
            if not stdout or len(stdout) < 100:
                self.logger.error(f"UI dump appears empty or too small: {len(stdout)} bytes")
                # Try alternative method
                stdout, _ = await self._run_adb_command(["shell", "uiautomator", "dump", "/dev/stdout"])
            
            # Clean up
            await self._run_adb_command(["shell", "rm", "-f", device_path])
            
            self.logger.debug(f"UI dump retrieved, size: {len(stdout)} bytes")
            return stdout
        except Exception as e:
            self.logger.error(f"Failed to get UI dump: {e}")
            return ""
    
    async def _analyze_performance(self, package_name: str) -> Dict[str, Any]:
        """Analyze app performance metrics."""
        self.logger.info("Analyzing app performance metrics...")
        metrics = {}
        
        # CPU usage
        self.logger.debug("Checking CPU usage...")
        stdout, _ = await self._run_adb_command([
            "shell", "top", "-n", "1", "|", "grep", package_name
        ])
        if stdout:
            cpu_match = re.search(r'(\d+)%', stdout)
            if cpu_match:
                metrics["cpu_usage_percent"] = int(cpu_match.group(1))
                self.logger.info(f"CPU usage: {metrics['cpu_usage_percent']}%")
        else:
            self.logger.warning("Could not get CPU usage data")
        
        # Memory usage
        self.logger.debug("Checking memory usage...")
        stdout, _ = await self._run_adb_command([
            "shell", "dumpsys", "meminfo", package_name, "|", "grep", "TOTAL"
        ])
        if stdout:
            mem_match = re.search(r'TOTAL\s+(\d+)', stdout)
            if mem_match:
                metrics["memory_usage_mb"] = int(mem_match.group(1)) / 1024
                self.logger.info(f"Memory usage: {metrics['memory_usage_mb']:.1f} MB")
        else:
            self.logger.warning("Could not get memory usage data")
        
        # Frame rate (if available)
        self.logger.debug("Checking frame statistics...")
        stdout, _ = await self._run_adb_command([
            "shell", "dumpsys", "gfxinfo", package_name, "framestats"
        ])
        if "Total frames rendered" in stdout:
            # Parse frame statistics
            lines = stdout.split('\n')
            for line in lines:
                if "Janky frames" in line:
                    janky_match = re.search(r'(\d+)', line)
                    if janky_match:
                        metrics["janky_frames"] = int(janky_match.group(1))
                        self.logger.info(f"Janky frames: {metrics['janky_frames']}")
        else:
            self.logger.warning("Could not get frame statistics")
        
        self.logger.info(f"Performance analysis complete. Metrics: {metrics}")
        return metrics
    
    async def _check_accessibility(self, ui_dump: str) -> Dict[str, Any]:
        """Check accessibility issues in UI."""
        issues = []
        
        # Check for content descriptions with detailed element info
        missing_content_desc_elements = []
        # Parse all nodes with missing content descriptions
        node_pattern = r'<node[^>]*content-desc=""[^>]*>'
        for match in re.finditer(node_pattern, ui_dump):
            node = match.group(0)
            
            # Extract element details
            element_info = {}
            
            # Get class
            class_match = re.search(r'class="([^"]+)"', node)
            if class_match:
                element_info['class'] = class_match.group(1).split('.')[-1]  # Get just class name
            
            # Get resource ID
            id_match = re.search(r'resource-id="([^"]+)"', node)
            if id_match:
                element_info['id'] = id_match.group(1).split('/')[-1]  # Get just ID part
            
            # Get text if available
            text_match = re.search(r'text="([^"]+)"', node)
            if text_match:
                element_info['text'] = text_match.group(1)
            
            # Get bounds
            bounds_match = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
            if bounds_match:
                element_info['bounds'] = bounds_match.group(0).replace('bounds=', '').strip('"')
            
            # Check if element is clickable
            clickable_match = re.search(r'clickable="true"', node)
            is_clickable = clickable_match is not None
            
            # Only add if it's a meaningful element that needs content description:
            # - Must be clickable OR be an image/icon element
            # - Must NOT be a layout container
            # - Must NOT already have text (text elements don't need content-desc)
            element_class = element_info.get('class', '').lower()
            has_text = bool(element_info.get('text'))
            is_layout = element_class in ['viewgroup', 'linearlayout', 'relativelayout', 'framelayout', 'constraintlayout']
            is_image = 'image' in element_class or 'icon' in element_class
            
            if not is_layout and (is_clickable or is_image) and not has_text:
                missing_content_desc_elements.append(element_info)
        
        if missing_content_desc_elements:
            issues.append({
                "type": "missing_content_description",
                "severity": "medium",
                "count": len(missing_content_desc_elements),
                "description": f"{len(missing_content_desc_elements)} clickable or image elements missing content descriptions (text elements excluded)",
                "elements": missing_content_desc_elements[:20]  # Limit to first 20 elements
            })
        
        # Check for clickable elements without text or content description
        clickable_elements = []
        clickable_pattern = r'<node[^>]*clickable="true"[^>]*(?:text=""|content-desc="")[^>]*>'
        for match in re.finditer(clickable_pattern, ui_dump):
            node = match.group(0)
            element_info = {}
            
            # Get class
            class_match = re.search(r'class="([^"]+)"', node)
            if class_match:
                element_info['class'] = class_match.group(1).split('.')[-1]
            
            # Get resource ID
            id_match = re.search(r'resource-id="([^"]+)"', node)
            if id_match:
                element_info['id'] = id_match.group(1).split('/')[-1]
                
            # Get bounds
            bounds_match = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
            if bounds_match:
                element_info['bounds'] = bounds_match.group(0).replace('bounds=', '').strip('"')
            
            clickable_elements.append(element_info)
        
        if clickable_elements:
            issues.append({
                "type": "unlabeled_clickable",
                "severity": "high",
                "count": len(clickable_elements),
                "description": f"{len(clickable_elements)} clickable elements without labels found",
                "elements": clickable_elements[:10]  # Limit to first 10 elements
            })
        
        # Check touch target sizes with details
        small_touch_targets = []
        all_nodes_pattern = r'<node[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*>'
        for match in re.finditer(all_nodes_pattern, ui_dump):
            node = match.group(0)
            bounds_match = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
            if bounds_match:
                x1, y1, x2, y2 = map(int, bounds_match.groups())
                width = x2 - x1
                height = y2 - y1
                
                # Check if clickable or focusable
                is_interactive = 'clickable="true"' in node or 'focusable="true"' in node
                
                if is_interactive and (width < 48 or height < 48):  # Material Design minimum
                    element_info = {
                        'size': f"{width}x{height}px",
                        'bounds': bounds_match.group(0).replace('bounds=', '').strip('"')
                    }
                    
                    # Get class
                    class_match = re.search(r'class="([^"]+)"', node)
                    if class_match:
                        element_info['class'] = class_match.group(1).split('.')[-1]
                    
                    # Get resource ID
                    id_match = re.search(r'resource-id="([^"]+)"', node)
                    if id_match:
                        element_info['id'] = id_match.group(1).split('/')[-1]
                    
                    small_touch_targets.append(element_info)
        
        if small_touch_targets:
            issues.append({
                "type": "small_touch_target",
                "severity": "medium",
                "count": len(small_touch_targets),
                "description": f"{len(small_touch_targets)} touch targets too small",
                "elements": small_touch_targets[:10]  # Limit to first 10 elements
            })
        
        return {
            "accessible": len(issues) == 0,
            "issues": issues,
            "score": max(0, 100 - len(issues) * 10)
        }
    
    async def _perform_ui_actions(self, package_name: str, test_id: str) -> List[Dict[str, Any]]:
        """Perform automated UI actions and record results."""
        self.logger.info("Starting improved UI action testing...")
        actions_log = []
        visited_screens = set()
        screen_count = 0
        
        # Get initial UI state
        ui_dump = await self._get_ui_dump()
        if not ui_dump:
            self.logger.error("Failed to get UI dump")
            return actions_log
        
        # Parse clickable elements using improved method
        clickable_elements = self._parse_clickable_elements_improved(ui_dump)
        
        if not clickable_elements:
            self.logger.warning("No clickable elements found with improved parser, trying regex fallback")
            # Fallback to regex method but with better pattern
            clickable_pattern = r'<node[^>]*clickable="true"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*/?>'
            matches = re.findall(clickable_pattern, ui_dump)
            clickable_elements = []
            for match in matches:
                x1, y1, x2, y2 = map(int, match)
                clickable_elements.append({
                    'bounds': (x1, y1, x2, y2),
                    'center': ((x1 + x2) // 2, (y1 + y2) // 2),
                    'class': 'Unknown',
                    'text': '',
                    'content_desc': ''
                })
        
        self.logger.info(f"Found {len(clickable_elements)} clickable elements")
        
        # Skip initial screenshot here as it's already taken in the main test flow
        # Just mark the initial screen as visited
        visited_screens.add(self._get_screen_signature(ui_dump))
        screen_count = 1  # Start from 1 since initial screenshot is taken in main flow
        
        # Find and fill text input fields first
        await self._fill_text_fields(ui_dump, test_id, screen_count)
        
        # Log details of first few elements for debugging
        for i, elem in enumerate(clickable_elements[:5]):
            self.logger.debug(
                f"Element {i+1}: {elem.get('class', 'Unknown')} at {elem.get('center', 'Unknown')}, "
                f"text='{elem.get('text', '')}', desc='{elem.get('content_desc', '')}'"
            )
        
        # Test tapping various elements
        max_actions = min(len(clickable_elements), 15)  # Test up to 15 elements
        for i, element in enumerate(clickable_elements[:max_actions]):
            x, y = element['center']
            
            element_desc = f"{element.get('class', 'Unknown')} (text: '{element.get('text', '')[:20]}', desc: '{element.get('content_desc', '')[:20]}')"
            self.logger.debug(f"Testing tap {i+1}/{max_actions} on {element_desc} at coordinates ({x}, {y})")
            
            # Get screen signature before tap
            before_screen_sig = self._get_screen_signature(ui_dump)
            
            # Perform tap
            await self._run_adb_command(["shell", "input", "tap", str(x), str(y)])
            await asyncio.sleep(2)  # Give more time for screen transitions
            
            # Get new UI state
            new_ui_dump = await self._get_ui_dump()
            after_screen_sig = self._get_screen_signature(new_ui_dump)
            
            # Initialize screenshot variable
            screenshot_data = None
            
            # Check if we navigated to a new screen
            if after_screen_sig != before_screen_sig and after_screen_sig not in visited_screens:
                self.logger.info(f"Navigated to new screen after tapping {element_desc}")
                visited_screens.add(after_screen_sig)
                
                # Take screenshot of new screen
                screenshot_data = await self._capture_screenshot(test_id, f"screen_{screen_count}", f"After tapping: {elem.get('text', elem.get('content_desc', 'Unknown element'))}")
                screen_count += 1
                
                # Fill any text fields on the new screen
                await self._fill_text_fields(new_ui_dump, test_id, screen_count)
                
                # Update UI dump after filling fields
                ui_dump = await self._get_ui_dump()
            else:
                # Skip screenshot for actions that don't change the screen
                screenshot_data = None
                self.logger.debug(f"Skipping screenshot - no screen change after tapping: {elem.get('text', elem.get('content_desc', 'Unknown element'))}")
            
            # Check if app crashed
            stdout, _ = await self._run_adb_command([
                "shell", "pidof", package_name
            ])
            
            app_crashed = len(stdout.strip()) == 0
            
            if app_crashed:
                self.logger.warning(f"App crashed after tap at ({x}, {y})")
            
            action_result = {
                "action": "tap",
                "element": element_desc,
                "coordinates": {"x": x, "y": y},
                "screen_changed": after_screen_sig != before_screen_sig,
                "new_screen": after_screen_sig not in visited_screens if after_screen_sig != before_screen_sig else False,
                "app_crashed": app_crashed,
                "screenshot": screenshot_data.get('filepath', '') if screenshot_data else '',
                "screenshot_description": screenshot_data.get('description', '') if screenshot_data else '',
                "ui_elements_found": screenshot_data.get('ui_elements_found', {}) if screenshot_data else {},
                "element_details": {
                    "class": element.get('class', 'Unknown'),
                    "text": element.get('text', ''),
                    "content_desc": element.get('content_desc', ''),
                    "resource_id": element.get('resource_id', '')
                }
            }
                
            actions_log.append(action_result)
            
            if app_crashed:
                # App crashed, try to restart
                self.logger.info("Attempting to restart crashed app...")
                await self._launch_app(package_name)
                await asyncio.sleep(3)
                # Reset UI dump after restart
                ui_dump = await self._get_ui_dump()
        
        # Test scrolling and check for new content
        self.logger.debug("Testing scroll action...")
        before_scroll_sig = self._get_screen_signature(ui_dump)
        
        await self._run_adb_command([
            "shell", "input", "swipe", "500", "1000", "500", "300", "300"
        ])
        await asyncio.sleep(1)
        
        # Check if scroll revealed new content
        ui_dump_after_scroll = await self._get_ui_dump()
        after_scroll_sig = self._get_screen_signature(ui_dump_after_scroll)
        
        if after_scroll_sig != before_scroll_sig:
            self.logger.info("Scroll revealed new content")
            scroll_screenshot = await self._capture_screenshot(test_id, f"screen_{screen_count}_scrolled", "After scrolling down to reveal more content")
            screen_count += 1
            
            # Fill any newly revealed text fields
            await self._fill_text_fields(ui_dump_after_scroll, test_id, screen_count)
        
        actions_log.append({
            "action": "scroll",
            "direction": "down",
            "revealed_new_content": after_scroll_sig != before_scroll_sig
        })
        
        self.logger.info(f"Completed {len(actions_log)} UI actions")
        self.logger.info(f"Captured {screen_count} unique screens")
        return actions_log
    
    async def test_android_app(
        self,
        apk_path: str,
        test_actions: Optional[List[str]] = None,
        target_api_level: Optional[int] = None,
        avd_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main method to test an Android app.
        
        Args:
            apk_path: Path to the APK file (only .apk files are supported)
            test_actions: List of test actions to perform
            target_api_level: Target API level for emulator
            avd_name: Specific AVD to use
            
        Returns:
            Test results with errors, performance metrics, UX recommendations, and accessibility findings
        """
        self.logger.info("=" * 60)
        self.logger.info("Starte Android-App-Test...")
        self.logger.info(f"APK-Pfad: {apk_path}")
        self.logger.info(f"AVD-Name: {avd_name or 'Standard'}")
        self.logger.info("=" * 60)
        
        try:
            # Validate APK exists
            self.logger.info("Schritt 1: Validiere APK-Datei...")
            if not os.path.exists(apk_path):
                self.logger.error(f"APK-Datei nicht gefunden: {apk_path}")
                return {
                    "success": False,
                    "error": f"APK-Datei nicht gefunden: {apk_path}"
                }
            
            # Validate file extension
            file_ext = os.path.splitext(apk_path)[1].lower()
            if file_ext != '.apk':
                self.logger.error(f"Ungültiger Dateityp: {file_ext}. Nur .apk-Dateien werden unterstützt.")
                return {
                    "success": False,
                    "error": f"Ungültiger Dateityp: {file_ext}. Nur .apk-Dateien werden unterstützt."
                }
            
            # Generate test ID
            test_id = self._generate_test_id(apk_path)
            self.logger.info(f"Generated test ID: {test_id}")
            
            # Select device if multiple are connected
            self.logger.info("\nSchritt 1.5: Wähle Gerät für Test...")
            await self._select_device()
            
            # Start emulator if needed
            self.logger.info("\nSchritt 2: Prüfe/Starte Emulator...")
            if not await self._check_emulator_running():
                if not await self._start_emulator(avd_name):
                    self.logger.error("Android-Emulator konnte nicht gestartet werden")
                    return {
                        "success": False,
                        "error": "Android-Emulator konnte nicht gestartet werden"
                    }
            
            # Get package name
            self.logger.info("\nSchritt 3: Extrahiere Paketinformationen...")
            package_name = await self._get_package_name(apk_path)
            if not package_name:
                self.logger.error("Paketname konnte nicht aus APK extrahiert werden")
                return {
                    "success": False,
                    "error": "Paketname konnte nicht aus APK extrahiert werden"
                }
            
            # Install app
            self.logger.info("\nSchritt 4: Installiere App auf Emulator...")
            if not await self._install_apk(apk_path):
                self.logger.error("APK konnte nicht auf Emulator installiert werden")
                return {
                    "success": False,
                    "error": "APK konnte nicht auf Emulator installiert werden"
                }
            
            # Launch app
            self.logger.info("\nSchritt 5: Starte die App...")
            launch_start = time.time()
            if not await self._launch_app(package_name):
                self.logger.error("App konnte nicht gestartet werden")
                return {
                    "success": False,
                    "error": "App konnte nicht gestartet werden"
                }
            launch_time = (time.time() - launch_start) * 1000
            self.logger.info(f"App gestartet in {launch_time:.0f}ms ({launch_time/1000:.2f} Sekunden)")
            
            # Wait for app to stabilize
            self.logger.info("Warte 3 Sekunden bis App stabil ist...")
            await asyncio.sleep(3)
            
            # Capture initial screenshot
            self.logger.info("\nSchritt 6: Erfasse Anfangszustand...")
            initial_screenshot = await self._capture_screenshot(test_id, "screen_0_initial", "App launched - initial state")
            
            # Get initial UI dump for accessibility check
            self.logger.info("Erfasse UI-Hierarchie für Analyse...")
            ui_dump = await self._get_ui_dump()
            
            # Check accessibility
            self.logger.info("\nSchritt 7: Prüfe Barrierefreiheit...")
            accessibility_results = await self._check_accessibility(ui_dump)
            self.logger.info(f"Barrierefreiheits-Score: {accessibility_results.get('score', 'N/A')}/100")
            
            # Perform UI actions and test navigation
            self.logger.info("\nSchritt 8: Führe UI-Interaktionstests durch...")
            actions_log = await self._perform_ui_actions(package_name, test_id)
            
            # Analyze performance
            self.logger.info("\nSchritt 9: Analysiere Performance-Metriken...")
            performance_metrics = await self._analyze_performance(package_name)
            performance_metrics["startup_time_ms"] = launch_time
            
            # Analyze crashes and errors from logcat
            self.logger.info("\nSchritt 10: Analysiere Logcat nach Fehlern...")
            stdout, _ = await self._run_adb_command([
                "logcat", "-d", "-s", f"{package_name}:E", "AndroidRuntime:E"
            ])
            
            errors = []
            for line in stdout.split('\n'):
                if "FATAL EXCEPTION" in line or "ERROR" in line:
                    errors.append(line.strip())
            
            if errors:
                self.logger.warning(f"Gefunden: {len(errors)} Fehler in Logcat")
            else:
                self.logger.info("Keine Fehler in Logcat gefunden")
            
            # Generate UX recommendations based on findings
            self.logger.info("\nSchritt 11: Generiere UX-Empfehlungen...")
            ux_recommendations = self._generate_ux_recommendations(
                actions_log, performance_metrics, accessibility_results
            )
            self.logger.info(f"Generiert: {len(ux_recommendations)} Empfehlungen")
            
            # Compile results
            self.logger.info("\nSchritt 12: Stelle Testergebnisse zusammen...")
            results = {
                "success": True,
                "test_id": test_id,
                "package_name": package_name,
                "timestamp": datetime.now().isoformat(),
                "app_launches": launch_time < self.performance_thresholds["startup_time_ms"],
                "errors": errors[:10],  # Limit to 10 errors
                "performance": {
                    "metrics": performance_metrics,
                    "issues": self._identify_performance_issues(performance_metrics)
                },
                "navigation": {
                    "actions_performed": len(actions_log),
                    "crashes_detected": sum(1 for a in actions_log if a.get("app_crashed", False)),
                    "screens_accessed": max(1, len([f for f in os.listdir(self.screenshot_dir) if f.startswith(f"{test_id}_screen_") and f.endswith(".png")]))
                },
                "accessibility": accessibility_results,
                "ux_recommendations": ux_recommendations,
                "screenshots": {
                    "initial": initial_screenshot,
                    "action_count": len([a for a in actions_log if "screenshot" in a])
                }
            }
            
            # Save results
            self.logger.info("Speichere Testergebnisse...")
            self.storage[test_id] = results
            self._save_storage()
            
            # Uninstall app to clean up
            self.logger.info("\nSchritt 13: Aufräumen - deinstalliere App...")
            await self._run_adb_command(["uninstall", package_name])
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("Android-App-Test erfolgreich abgeschlossen!")
            self.logger.info(f"Test-ID: {test_id}")
            self.logger.info(f"Abstürze erkannt: {results['navigation']['crashes_detected']}")
            self.logger.info(f"Performance-Probleme: {len(results['performance']['issues'])}")
            self.logger.info(f"Barrierefreiheits-Probleme: {len(accessibility_results.get('issues', []))}")
            self.logger.info("=" * 60 + "\n")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Testausführung fehlgeschlagen mit Ausnahme: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Testausführung fehlgeschlagen: {str(e)}"
            }
    
    def _identify_performance_issues(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance issues based on metrics."""
        issues = []
        
        if metrics.get("startup_time_ms", 0) > self.performance_thresholds["startup_time_ms"]:
            issues.append({
                "type": "slow_startup",
                "severity": "high",
                "value": metrics["startup_time_ms"],
                "threshold": self.performance_thresholds["startup_time_ms"],
                "description": "App benötigt zu lange zum Starten"
            })
        
        if metrics.get("memory_usage_mb", 0) > self.performance_thresholds["memory_usage_mb"]:
            issues.append({
                "type": "high_memory_usage",
                "severity": "medium",
                "value": metrics["memory_usage_mb"],
                "threshold": self.performance_thresholds["memory_usage_mb"],
                "description": "App nutzt übermäßig viel Speicher"
            })
        
        if metrics.get("cpu_usage_percent", 0) > self.performance_thresholds["cpu_usage_percent"]:
            issues.append({
                "type": "high_cpu_usage",
                "severity": "medium",
                "value": metrics["cpu_usage_percent"],
                "threshold": self.performance_thresholds["cpu_usage_percent"],
                "description": "App nutzt zu viel CPU"
            })
        
        if metrics.get("janky_frames", 0) > 10:
            issues.append({
                "type": "ui_jank",
                "severity": "medium",
                "value": metrics["janky_frames"],
                "description": "UI hat ruckelige Animationen"
            })
        
        return issues
    
    def _generate_ux_recommendations(
        self,
        actions_log: List[Dict[str, Any]],
        performance_metrics: Dict[str, Any],
        accessibility_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate UX improvement recommendations."""
        recommendations = []
        
        # Performance-based recommendations
        if performance_metrics.get("startup_time_ms", 0) > 2000:
            recommendations.append({
                "category": "performance",
                "priority": "high",
                "title": "App-Start optimieren",
                "description": "Erwägen Sie die Implementierung eines Splash-Screens oder Lazy Loading für bessere wahrgenommene Performance"
            })
        
        # Crash-based recommendations
        crash_count = sum(1 for a in actions_log if a.get("app_crashed", False))
        if crash_count > 0:
            recommendations.append({
                "category": "stability",
                "priority": "critical",
                "title": "App-Abstürze beheben",
                "description": f"App stürzte {crash_count} Mal während des Tests ab. Untersuchen Sie Crash-Logs und implementieren Sie ordnungsgemäße Fehlerbehandlung"
            })
        
        # Accessibility recommendations
        if not accessibility_results["accessible"]:
            for issue in accessibility_results["issues"][:3]:  # Top 3 issues
                if issue["type"] == "missing_content_description":
                    recommendations.append({
                        "category": "accessibility",
                        "priority": "medium",
                        "title": "Inhaltsbeschreibungen hinzufügen",
                        "description": "Fügen Sie UI-Elementen Inhaltsbeschreibungen für Screenreader-Unterstützung hinzu"
                    })
                elif issue["type"] == "small_touch_target":
                    recommendations.append({
                        "category": "accessibility",
                        "priority": "medium",
                        "title": "Touch-Ziele vergrößern",
                        "description": "Vergrößern Sie Touch-Ziele auf mindestens 48x48dp für bessere Bedienbarkeit"
                    })
        
        # General UX recommendations
        recommendations.append({
            "category": "ux",
            "priority": "low",
            "title": "Benutzer-Onboarding implementieren",
            "description": "Erwägen Sie ein Tutorial oder einen Onboarding-Ablauf für Erstbenutzer"
        })
        
        return recommendations
    
    def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Retrieve test results by ID."""
        if test_id in self.storage:
            return {
                "success": True,
                "data": self.storage[test_id]
            }
        return {
            "success": False,
            "error": f"Test results not found for ID: {test_id}"
        }
    
    def list_recent_tests(self, limit: int = 10) -> Dict[str, Any]:
        """List recent test results."""
        # Sort by timestamp
        sorted_tests = sorted(
            self.storage.items(),
            key=lambda x: x[1].get("timestamp", ""),
            reverse=True
        )[:limit]
        
        return {
            "success": True,
            "data": [
                {
                    "test_id": test_id,
                    "package_name": data.get("package_name"),
                    "timestamp": data.get("timestamp"),
                    "success": data.get("app_launches", False),
                    "crash_count": data.get("navigation", {}).get("crashes_detected", 0),
                    "startup_time_seconds": round(data.get("performance", {}).get("startup_time_ms", 0) / 1000.0, 2)
                }
                for test_id, data in sorted_tests
            ]
        }
    
    def delete_test_run(self, test_id: str) -> Dict[str, Any]:
        """Delete a test run and its associated data."""
        if test_id not in self.storage:
            return {
                "success": False,
                "error": f"Test-ID nicht gefunden: {test_id}"
            }
        
        # Get test data before deletion
        test_data = self.storage[test_id]
        
        # Delete screenshots associated with this test
        deleted_screenshots = []
        try:
            import glob
            screenshot_pattern = os.path.join(self.screenshot_dir, f"{test_id}_*.png")
            screenshots = glob.glob(screenshot_pattern)
            
            for screenshot in screenshots:
                try:
                    os.remove(screenshot)
                    deleted_screenshots.append(os.path.basename(screenshot))
                    self.logger.info(f"Gelöschter Screenshot: {screenshot}")
                except Exception as e:
                    self.logger.error(f"Fehler beim Löschen des Screenshots {screenshot}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Suchen von Screenshots: {e}")
        
        # Delete test data from storage
        del self.storage[test_id]
        self._save_storage()
        
        return {
            "success": True,
            "message": f"Test {test_id} erfolgreich gelöscht",
            "deleted_screenshots": deleted_screenshots,
            "deleted_test": {
                "test_id": test_id,
                "package_name": test_data.get("package_name"),
                "timestamp": test_data.get("timestamp")
            }
        }
    
    def _parse_clickable_elements_improved(self, ui_dump: str) -> List[Dict[str, Any]]:
        """Parse clickable elements using XML parsing for better accuracy."""
        import xml.etree.ElementTree as ET
        
        clickable_elements = []
        
        try:
            # Clean up the XML if needed
            ui_dump = ui_dump.strip()
            if not ui_dump.startswith('<?xml'):
                # Try to find the start of XML
                xml_start = ui_dump.find('<?xml')
                if xml_start > 0:
                    ui_dump = ui_dump[xml_start:]
            
            root = ET.fromstring(ui_dump)
            
            # Find all nodes with clickable="true" or that might be interactive
            for node in root.iter('node'):
                # Check if element is interactive
                is_clickable = node.get('clickable') == 'true'
                is_checkable = node.get('checkable') == 'true'
                is_long_clickable = node.get('long-clickable') == 'true'
                has_click_handler = is_clickable or is_checkable or is_long_clickable
                
                # Also check for common button/clickable classes
                class_name = node.get('class', '')
                is_button_class = any(btn in class_name.lower() for btn in [
                    'button', 'imagebutton', 'checkbox', 'radiobutton', 
                    'switch', 'togglebutton', 'chip', 'cardview', 'textview'
                ])
                
                # Check if it's enabled and has bounds
                is_enabled = node.get('enabled') != 'false'
                bounds = node.get('bounds', '')
                
                if (has_click_handler or is_button_class) and is_enabled and bounds:
                    # Parse bounds
                    match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                    if match:
                        x1, y1, x2, y2 = map(int, match.groups())
                        
                        # Skip if element has no area
                        if x2 <= x1 or y2 <= y1:
                            continue
                        
                        # Skip if element is too small (likely hidden)
                        width = x2 - x1
                        height = y2 - y1
                        if width < 10 or height < 10:
                            continue
                        
                        element_info = {
                            'bounds': (x1, y1, x2, y2),
                            'center': ((x1 + x2) // 2, (y1 + y2) // 2),
                            'size': (width, height),
                            'class': class_name.split('.')[-1] if '.' in class_name else class_name,
                            'resource_id': node.get('resource-id', ''),
                            'text': node.get('text', ''),
                            'content_desc': node.get('content-desc', ''),
                            'clickable': is_clickable,
                            'checkable': is_checkable,
                            'long_clickable': is_long_clickable,
                            'enabled': is_enabled,
                            'focusable': node.get('focusable') == 'true',
                            'scrollable': node.get('scrollable') == 'true',
                            'index': node.get('index', '0')
                        }
                        
                        clickable_elements.append(element_info)
            
            # Sort by position (top to bottom, left to right)
            clickable_elements.sort(key=lambda e: (e['center'][1], e['center'][0]))
            
            self.logger.info(f"XML parser found {len(clickable_elements)} interactive elements")
            return clickable_elements
            
        except ET.ParseError as e:
            self.logger.error(f"XML parsing error: {e}")
            self.logger.debug(f"First 500 chars of dump: {ui_dump[:500]}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing clickable elements: {e}")
            return []
    
    def _get_screen_signature(self, ui_dump: str) -> str:
        """Generate a signature for the current screen state."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(ui_dump)
            
            # Get structural elements for better screen identification
            structure_elements = []
            texts = []
            
            for node in root.iter('node'):
                # Get class names for structural identification
                class_name = node.get('class', '')
                if class_name:
                    simple_class = class_name.split('.')[-1]
                    # Count important UI elements
                    if any(elem in simple_class for elem in ['Button', 'TextView', 'EditText', 'ImageView']):
                        structure_elements.append(simple_class)
                
                # Get text content
                text = node.get('text', '').strip()
                if text and len(text) > 2:  # Skip very short texts
                    texts.append(text)
                
                # Get content descriptions
                desc = node.get('content-desc', '').strip()
                if desc and len(desc) > 2:
                    texts.append(desc)
                
                # Get resource IDs for key elements
                resource_id = node.get('resource-id', '')
                if resource_id and ':id/' in resource_id:
                    id_part = resource_id.split(':id/')[-1]
                    if id_part:
                        structure_elements.append(f"id:{id_part}")
            
            # Create signature combining structure and content
            texts.sort()
            structure_elements.sort()
            
            # Use top elements to create signature
            signature_parts = [
                '|'.join(structure_elements[:10]),  # Top 10 structural elements
                '|'.join(texts[:15]),  # Top 15 text elements
                f"buttons:{ui_dump.count('Button')}",
                f"edittexts:{ui_dump.count('EditText')}",
                "clickable:" + str(ui_dump.count('clickable="true"'))
            ]
            
            signature = '||'.join(signature_parts)
            return signature
            
        except Exception as e:
            self.logger.debug(f"Error creating screen signature: {e}")
            # Fallback to simple hash
            return str(hash(ui_dump))
    
    async def _fill_text_fields(self, ui_dump: str, test_id: str, screen_num: int) -> int:
        """Find and fill all text input fields on the current screen."""
        self.logger.info("Looking for text input fields to fill...")
        filled_count = 0
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(ui_dump)
            
            # Sample data for different field types
            sample_data = {
                'email': 'test@example.com',
                'phone': '+1234567890',
                'name': 'Test User',
                'firstname': 'Test',
                'lastname': 'User',
                'username': 'testuser123',
                'password': 'Test123!@#',
                'address': '123 Test Street',
                'city': 'Test City',
                'zip': '12345',
                'search': 'test search',
                'message': 'This is a test message',
                'comment': 'Test comment',
                'description': 'Test description',
                'default': 'Test Input'
            }
            
            # Find all EditText elements
            for node in root.iter('node'):
                class_name = node.get('class', '')
                
                # Check if it's an EditText or similar input field
                if 'EditText' in class_name or 'TextInputEditText' in class_name:
                    # Skip if already has text
                    existing_text = node.get('text', '')
                    if existing_text and existing_text.strip():
                        continue
                    
                    # Skip if not enabled
                    if node.get('enabled') == 'false':
                        continue
                    
                    # Get field info
                    resource_id = node.get('resource-id', '')
                    content_desc = node.get('content-desc', '').lower()
                    hint = node.get('hint', '').lower() if 'hint' in node.attrib else ''
                    
                    # Determine what type of data to input
                    field_identifiers = (resource_id + ' ' + content_desc + ' ' + hint).lower()
                    
                    input_text = sample_data['default']
                    for field_type, sample_value in sample_data.items():
                        if field_type in field_identifiers:
                            input_text = sample_value
                            break
                    
                    # Get bounds for clicking
                    bounds = node.get('bounds', '')
                    match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                    if match:
                        x1, y1, x2, y2 = map(int, match.groups())
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        
                        self.logger.info(f"Filling text field at ({center_x}, {center_y}) with '{input_text}'")
                        self.logger.debug(f"Field details - resource_id: {resource_id}, content_desc: {content_desc}, hint: {hint}")
                        
                        # Click on the field
                        await self._run_adb_command(["shell", "input", "tap", str(center_x), str(center_y)])
                        await asyncio.sleep(0.5)
                        
                        # Clear any existing text
                        await self._run_adb_command(["shell", "input", "keyevent", "KEYCODE_MOVE_END"])
                        await self._run_adb_command(["shell", "input", "keyevent", "--longpress", "KEYCODE_DEL"])
                        
                        # Type the text
                        # Use a different approach for text input to handle spaces properly
                        # Method 1: Try using quotes around the entire text
                        try:
                            await self._run_adb_command(["shell", "input", "text", f'"{input_text}"'])
                        except Exception as e:
                            self.logger.warning(f"Failed to input text with quotes: {e}")
                            # Method 2: Try character by character for special cases
                            try:
                                for char in input_text:
                                    if char == ' ':
                                        await self._run_adb_command(["shell", "input", "keyevent", "62"])  # KEYCODE_SPACE
                                    else:
                                        await self._run_adb_command(["shell", "input", "text", char])
                                    await asyncio.sleep(0.05)
                            except Exception as e2:
                                self.logger.error(f"Failed to input text character by character: {e2}")
                        
                        await asyncio.sleep(0.5)
                        
                        # Hide keyboard
                        await self._run_adb_command(["shell", "input", "keyevent", "KEYCODE_BACK"])
                        
                        filled_count += 1
            
            if filled_count > 0:
                self.logger.info(f"Filled {filled_count} text fields")
                # Take screenshot after filling fields
                await self._capture_screenshot(test_id, f"screen_{screen_num}_filled_fields", f"After filling {filled_count} text input fields")
            else:
                self.logger.info("No empty text fields found to fill")
                
        except Exception as e:
            self.logger.error(f"Error filling text fields: {e}")
        
        return filled_count