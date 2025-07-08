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
from langchain.vectorstores import FAISS
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
        
        self.logger.info(f"Initializing AndroidTestingAgent with ADB path: {adb_path}")
        
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
    
    async def _run_adb_command(self, command: List[str]) -> Tuple[str, str]:
        """Run ADB command asynchronously."""
        full_command = [self.adb_path] + command
        self.logger.debug(f"Running ADB command: {' '.join(full_command)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stderr:
                self.logger.warning(f"ADB command stderr: {stderr.decode()[:200]}")
            
            return stdout.decode(), stderr.decode()
        except Exception as e:
            self.logger.error(f"Error running ADB command: {e}")
            raise
    
    def _run_adb_command_sync(self, command: List[str]) -> Tuple[str, str]:
        """Run ADB command synchronously."""
        full_command = [self.adb_path] + command
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr
    
    async def _check_emulator_running(self) -> bool:
        """Check if an Android emulator is running."""
        self.logger.info("Checking if Android emulator is running...")
        stdout, _ = await self._run_adb_command(["devices"])
        lines = stdout.strip().split('\n')
        
        self.logger.debug(f"ADB devices output: {stdout}")
        
        for line in lines[1:]:  # Skip header
            if line and "emulator" in line:
                self.logger.info(f"Found running emulator: {line}")
                return True
        
        self.logger.warning("No emulator found running")
        return False
    
    async def _start_emulator(self, avd_name: Optional[str] = None) -> bool:
        """Start Android emulator if not running."""
        self.logger.info("Attempting to start Android emulator...")
        
        if await self._check_emulator_running():
            self.logger.info("Emulator already running, skipping startup")
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
                self.logger.error("No AVDs found. Please create an AVD first.")
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
    
    async def _install_apk(self, apk_path: str) -> bool:
        """Install APK on emulator."""
        self.logger.info(f"Installing APK: {apk_path}")
        stdout, stderr = await self._run_adb_command(["install", "-r", apk_path])
        
        if "Success" in stdout:
            self.logger.info("APK installation successful")
            return True
        else:
            self.logger.error(f"APK installation failed. Output: {stdout[:200]}")
            return False
    
    async def _get_package_name(self, apk_path: str) -> Optional[str]:
        """Extract package name from APK."""
        self.logger.info(f"Extracting package name from APK: {apk_path}")
        
        try:
            # Use aapt to get package info
            result = subprocess.run(
                ["aapt", "dump", "badging", apk_path],
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
        self.logger.info(f"Launching app: {package_name}")
        
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
            self.logger.info("App launched successfully")
            return True
        else:
            self.logger.error(f"Failed to launch app. Output: {stdout[:200]}")
            return False
    
    async def _capture_screenshot(self, test_id: str, name: str) -> str:
        """Capture screenshot from device."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_id}_{name}_{timestamp}.png"
        filepath = os.path.join(self.screenshot_dir, filename)
        
        self.logger.debug(f"Capturing screenshot: {name}")
        
        try:
            # Capture on device
            device_path = f"/sdcard/{filename}"
            await self._run_adb_command(["shell", "screencap", "-p", device_path])
            
            # Pull to local
            await self._run_adb_command(["pull", device_path, filepath])
            
            # Clean up device
            await self._run_adb_command(["shell", "rm", device_path])
            
            self.logger.debug(f"Screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return ""
    
    async def _get_ui_dump(self) -> str:
        """Get UI hierarchy dump."""
        self.logger.debug("Getting UI hierarchy dump...")
        
        try:
            device_path = "/sdcard/ui_dump.xml"
            await self._run_adb_command(["shell", "uiautomator", "dump", device_path])
            
            stdout, _ = await self._run_adb_command(["shell", "cat", device_path])
            
            await self._run_adb_command(["shell", "rm", device_path])
            
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
        
        # Check for content descriptions
        if 'content-desc=""' in ui_dump:
            count = ui_dump.count('content-desc=""')
            issues.append({
                "type": "missing_content_description",
                "severity": "medium",
                "count": count,
                "description": f"{count} UI elements missing content descriptions"
            })
        
        # Check for clickable elements without text or content description
        clickable_pattern = r'clickable="true"[^>]*(?:text=""|content-desc="")'
        if re.search(clickable_pattern, ui_dump):
            issues.append({
                "type": "unlabeled_clickable",
                "severity": "high",
                "description": "Clickable elements without labels found"
            })
        
        # Check text contrast (would need screenshot analysis)
        # Check touch target sizes
        small_targets = re.findall(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', ui_dump)
        for bounds in small_targets:
            x1, y1, x2, y2 = map(int, bounds)
            width = x2 - x1
            height = y2 - y1
            if width < 48 or height < 48:  # Material Design minimum
                issues.append({
                    "type": "small_touch_target",
                    "severity": "medium",
                    "description": f"Touch target too small: {width}x{height}px"
                })
                break  # Only report once
        
        return {
            "accessible": len(issues) == 0,
            "issues": issues,
            "score": max(0, 100 - len(issues) * 10)
        }
    
    async def _perform_ui_actions(self, package_name: str, test_id: str) -> List[Dict[str, Any]]:
        """Perform automated UI actions and record results."""
        self.logger.info("Starting UI action testing...")
        actions_log = []
        
        # Get initial UI state
        ui_dump = await self._get_ui_dump()
        
        # Parse clickable elements
        clickable_elements = re.findall(
            r'<node[^>]*clickable="true"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*/>',
            ui_dump
        )
        
        self.logger.info(f"Found {len(clickable_elements)} clickable elements")
        
        # Test tapping various elements
        for i, bounds in enumerate(clickable_elements[:10]):  # Limit to 10 elements
            x1, y1, x2, y2 = map(int, bounds)
            x = (x1 + x2) // 2
            y = (y1 + y2) // 2
            
            self.logger.debug(f"Testing tap {i+1}/10 at coordinates ({x}, {y})")
            
            # Take before screenshot
            before_screenshot = await self._capture_screenshot(test_id, f"before_tap_{i}")
            
            # Perform tap
            await self._run_adb_command(["shell", "input", "tap", str(x), str(y)])
            await asyncio.sleep(1)
            
            # Take after screenshot
            after_screenshot = await self._capture_screenshot(test_id, f"after_tap_{i}")
            
            # Check if app crashed
            stdout, _ = await self._run_adb_command([
                "shell", "pidof", package_name
            ])
            
            app_crashed = len(stdout.strip()) == 0
            
            if app_crashed:
                self.logger.warning(f"App crashed after tap at ({x}, {y})")
            
            actions_log.append({
                "action": "tap",
                "coordinates": {"x": x, "y": y},
                "before_screenshot": before_screenshot,
                "after_screenshot": after_screenshot,
                "app_crashed": app_crashed
            })
            
            if app_crashed:
                # App crashed, try to restart
                self.logger.info("Attempting to restart crashed app...")
                await self._launch_app(package_name)
                await asyncio.sleep(2)
        
        # Test scrolling
        self.logger.debug("Testing scroll action...")
        await self._run_adb_command([
            "shell", "input", "swipe", "500", "1000", "500", "300", "300"
        ])
        actions_log.append({
            "action": "scroll",
            "direction": "up"
        })
        
        self.logger.info(f"Completed {len(actions_log)} UI actions")
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
            apk_path: Path to the APK file
            test_actions: List of test actions to perform
            target_api_level: Target API level for emulator
            avd_name: Specific AVD to use
            
        Returns:
            Test results with errors, performance metrics, UX recommendations, and accessibility findings
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Android app testing...")
        self.logger.info(f"APK Path: {apk_path}")
        self.logger.info(f"AVD Name: {avd_name or 'Default'}")
        self.logger.info("=" * 60)
        
        try:
            # Validate APK exists
            self.logger.info("Step 1: Validating APK file...")
            if not os.path.exists(apk_path):
                self.logger.error(f"APK file not found: {apk_path}")
                return {
                    "success": False,
                    "error": f"APK file not found: {apk_path}"
                }
            
            # Generate test ID
            test_id = self._generate_test_id(apk_path)
            self.logger.info(f"Generated test ID: {test_id}")
            
            # Start emulator if needed
            self.logger.info("\nStep 2: Checking/Starting emulator...")
            if not await self._check_emulator_running():
                if not await self._start_emulator(avd_name):
                    self.logger.error("Failed to start Android emulator")
                    return {
                        "success": False,
                        "error": "Failed to start Android emulator"
                    }
            
            # Get package name
            self.logger.info("\nStep 3: Extracting package information...")
            package_name = await self._get_package_name(apk_path)
            if not package_name:
                self.logger.error("Failed to extract package name from APK")
                return {
                    "success": False,
                    "error": "Failed to extract package name from APK"
                }
            
            # Install APK
            self.logger.info("\nStep 4: Installing APK on emulator...")
            if not await self._install_apk(apk_path):
                self.logger.error("Failed to install APK on emulator")
                return {
                    "success": False,
                    "error": "Failed to install APK on emulator"
                }
            
            # Launch app
            self.logger.info("\nStep 5: Launching the app...")
            launch_start = time.time()
            if not await self._launch_app(package_name):
                self.logger.error("Failed to launch app")
                return {
                    "success": False,
                    "error": "Failed to launch app"
                }
            launch_time = (time.time() - launch_start) * 1000
            self.logger.info(f"App launched in {launch_time:.0f}ms")
            
            # Wait for app to stabilize
            self.logger.info("Waiting 3 seconds for app to stabilize...")
            await asyncio.sleep(3)
            
            # Capture initial screenshot
            self.logger.info("\nStep 6: Capturing initial state...")
            initial_screenshot = await self._capture_screenshot(test_id, "initial")
            
            # Get initial UI dump for accessibility check
            self.logger.info("Getting UI hierarchy for analysis...")
            ui_dump = await self._get_ui_dump()
            
            # Check accessibility
            self.logger.info("\nStep 7: Checking accessibility...")
            accessibility_results = await self._check_accessibility(ui_dump)
            self.logger.info(f"Accessibility score: {accessibility_results.get('score', 'N/A')}/100")
            
            # Perform UI actions and test navigation
            self.logger.info("\nStep 8: Performing UI interaction tests...")
            actions_log = await self._perform_ui_actions(package_name, test_id)
            
            # Analyze performance
            self.logger.info("\nStep 9: Analyzing performance metrics...")
            performance_metrics = await self._analyze_performance(package_name)
            performance_metrics["startup_time_ms"] = launch_time
            
            # Analyze crashes and errors from logcat
            self.logger.info("\nStep 10: Analyzing logcat for errors...")
            stdout, _ = await self._run_adb_command([
                "logcat", "-d", "-s", f"{package_name}:E", "AndroidRuntime:E"
            ])
            
            errors = []
            for line in stdout.split('\n'):
                if "FATAL EXCEPTION" in line or "ERROR" in line:
                    errors.append(line.strip())
            
            if errors:
                self.logger.warning(f"Found {len(errors)} errors in logcat")
            else:
                self.logger.info("No errors found in logcat")
            
            # Generate UX recommendations based on findings
            self.logger.info("\nStep 11: Generating UX recommendations...")
            ux_recommendations = self._generate_ux_recommendations(
                actions_log, performance_metrics, accessibility_results
            )
            self.logger.info(f"Generated {len(ux_recommendations)} recommendations")
            
            # Compile results
            self.logger.info("\nStep 12: Compiling test results...")
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
                    "screens_accessed": len(set(a.get("after_screenshot", "") for a in actions_log))
                },
                "accessibility": accessibility_results,
                "ux_recommendations": ux_recommendations,
                "screenshots": {
                    "initial": initial_screenshot,
                    "action_count": len([a for a in actions_log if "screenshot" in a])
                }
            }
            
            # Save results
            self.logger.info("Saving test results...")
            self.storage[test_id] = results
            self._save_storage()
            
            # Uninstall app to clean up
            self.logger.info("\nStep 13: Cleaning up - uninstalling app...")
            await self._run_adb_command(["uninstall", package_name])
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("Android app testing completed successfully!")
            self.logger.info(f"Test ID: {test_id}")
            self.logger.info(f"Crashes detected: {results['navigation']['crashes_detected']}")
            self.logger.info(f"Performance issues: {len(results['performance']['issues'])}")
            self.logger.info(f"Accessibility issues: {len(accessibility_results.get('issues', []))}")
            self.logger.info("=" * 60 + "\n")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Test execution failed with exception: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Test execution failed: {str(e)}"
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
                "description": "App takes too long to start"
            })
        
        if metrics.get("memory_usage_mb", 0) > self.performance_thresholds["memory_usage_mb"]:
            issues.append({
                "type": "high_memory_usage",
                "severity": "medium",
                "value": metrics["memory_usage_mb"],
                "threshold": self.performance_thresholds["memory_usage_mb"],
                "description": "App uses excessive memory"
            })
        
        if metrics.get("cpu_usage_percent", 0) > self.performance_thresholds["cpu_usage_percent"]:
            issues.append({
                "type": "high_cpu_usage",
                "severity": "medium",
                "value": metrics["cpu_usage_percent"],
                "threshold": self.performance_thresholds["cpu_usage_percent"],
                "description": "App uses too much CPU"
            })
        
        if metrics.get("janky_frames", 0) > 10:
            issues.append({
                "type": "ui_jank",
                "severity": "medium",
                "value": metrics["janky_frames"],
                "description": "UI has janky animations"
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
                "title": "Optimize App Startup",
                "description": "Consider implementing a splash screen or lazy loading to improve perceived performance"
            })
        
        # Crash-based recommendations
        crash_count = sum(1 for a in actions_log if a.get("app_crashed", False))
        if crash_count > 0:
            recommendations.append({
                "category": "stability",
                "priority": "critical",
                "title": "Fix App Crashes",
                "description": f"App crashed {crash_count} times during testing. Investigate crash logs and implement proper error handling"
            })
        
        # Accessibility recommendations
        if not accessibility_results["accessible"]:
            for issue in accessibility_results["issues"][:3]:  # Top 3 issues
                if issue["type"] == "missing_content_description":
                    recommendations.append({
                        "category": "accessibility",
                        "priority": "medium",
                        "title": "Add Content Descriptions",
                        "description": "Add content descriptions to UI elements for screen reader support"
                    })
                elif issue["type"] == "small_touch_target":
                    recommendations.append({
                        "category": "accessibility",
                        "priority": "medium",
                        "title": "Increase Touch Target Sizes",
                        "description": "Increase touch target sizes to at least 48x48dp for better usability"
                    })
        
        # General UX recommendations
        recommendations.append({
            "category": "ux",
            "priority": "low",
            "title": "Implement User Onboarding",
            "description": "Consider adding a tutorial or onboarding flow for first-time users"
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
                    "crash_count": data.get("navigation", {}).get("crashes_detected", 0)
                }
                for test_id, data in sorted_tests
            ]
        }