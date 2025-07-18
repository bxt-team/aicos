"""Unified App Testing Agent for iOS and Android"""

import os
import subprocess
import json
import time
import uuid
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import tempfile
import shutil
import xml.etree.ElementTree as ET

from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew
from crewai.agent import Agent as CrewAgent

from app.agents.crews.base_crew import BaseCrew
from app.agents.tools.android_testing_tools import AndroidTestingTools
from app.agents.tools.ios_testing_tools import IOSTestingTools
from app.core.storage import StorageFactory
from app.agents.tools.image_analysis_tool import ImageAnalysisTool
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class AppTestingAgent(BaseCrew):
    """Unified testing agent for iOS and Android apps"""
    
    def __init__(self):
        super().__init__()
        self.android_tools = AndroidTestingTools()
        self.ios_tools = IOSTestingTools()
        self.image_analysis = ImageAnalysisTool()
        
        # Initialize storage adapter
        self.storage = StorageFactory.get_adapter()
        self.collection = "app_test_results"
        
        # Load existing test results from storage
        self.test_results = {}
        self._load_test_results()
        
        # Initialize the crew
        self.crew = self._setup_crew()
        
    def _setup_crew(self) -> Crew:
        """Setup the testing crew with platform-specific tools"""
        from crewai.tools import BaseTool
        
        # For now, create a simple crew without tools to avoid validation issues
        # The tools will be used directly in the test methods instead
        
        # Create testing agent
        testing_agent = Agent(
            role=self.agents_config['app_testing_agent']['role'],
            goal=self.agents_config['app_testing_agent']['goal'],
            backstory=self.agents_config['app_testing_agent']['backstory'],
            tools=[],  # Empty tools list for now
            llm=ChatOpenAI(
                model="gpt-4o",
                temperature=0.1,
                api_key=settings.OPENAI_API_KEY
            ),
            verbose=True,
            allow_delegation=False
        )
        
        return Crew(
            agents=[testing_agent],
            tasks=[],
            verbose=True
        )
    
    def _load_test_results(self):
        """Load test results from storage"""
        try:
            # Run async operation in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.storage.list(self.collection))
            
            # Convert list to dictionary with test_id as key
            for result in results:
                if 'test_id' in result:
                    self.test_results[result['test_id']] = result
            
            logger.info(f"Loaded {len(self.test_results)} test results from storage")
        except Exception as e:
            logger.error(f"Error loading test results: {e}")
            self.test_results = {}
    
    async def _save_test_result(self, test_id: str):
        """Save a test result to storage"""
        try:
            if test_id in self.test_results:
                result = self.test_results[test_id].copy()
                # Ensure test_id is in the data
                result['test_id'] = test_id
                await self.storage.save(self.collection, test_id, result)
                logger.info(f"Saved test result {test_id} to storage")
        except Exception as e:
            logger.error(f"Error saving test result {test_id}: {e}")
    
    def _parse_crew_result(self, result) -> Dict[str, Any]:
        """Parse CrewAI result which might be JSON or markdown-wrapped JSON"""
        try:
            # Try to extract JSON from markdown code blocks if present
            result_str = str(result)
            if '```json' in result_str and '```' in result_str:
                # Extract JSON from markdown code block
                start = result_str.find('```json') + 7
                end = result_str.rfind('```')
                json_str = result_str[start:end].strip()
            else:
                json_str = result_str
            
            parsed_result = json.loads(json_str)
            logger.info(f"Successfully parsed test result")
            return parsed_result
        except Exception as e:
            logger.error(f"Failed to parse test result as JSON: {e}")
            logger.info(f"Raw test result: {result}")
            # Return a properly structured dict instead of wrapping in raw_result
            return {
                'test_summary': 'Test completed but results could not be parsed',
                'raw_result': str(result),
                'parse_error': str(e)
            }
    
    async def test_app(
        self,
        platform: str,
        app_path: str,
        device_id: Optional[str] = None,
        test_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Test a mobile app on specified platform
        
        Args:
            platform: 'android' or 'ios'
            app_path: Path to APK (Android) or .app bundle (iOS)
            device_id: Optional device/simulator ID
            test_config: Optional test configuration
            
        Returns:
            Test results dictionary
        """
        if platform.lower() not in ['android', 'ios']:
            raise ValueError("Platform must be 'android' or 'ios'")
            
        test_id = str(uuid.uuid4())
        self.test_results[test_id] = {
            'id': test_id,
            'test_id': test_id,  # Include for storage
            'platform': platform.lower(),
            'app_path': app_path,
            'device_id': device_id,
            'status': 'running',
            'started_at': datetime.now().isoformat(),
            'results': {}
        }
        
        # Save initial test record to storage
        await self._save_test_result(test_id)
        
        try:
            if platform.lower() == 'android':
                results = await self._test_android_app(app_path, device_id, test_config)
            else:
                results = await self._test_ios_app(app_path, device_id, test_config)
                
            self.test_results[test_id]['results'] = results
            self.test_results[test_id]['status'] = 'completed'
            self.test_results[test_id]['completed_at'] = datetime.now().isoformat()
            logger.info(f"Test {test_id} completed successfully with results: {json.dumps(results, indent=2) if isinstance(results, dict) else results}")
            
            # Save to storage
            await self._save_test_result(test_id)
            
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            self.test_results[test_id]['status'] = 'failed'
            self.test_results[test_id]['error'] = str(e)
            
            # Save failed result to storage
            await self._save_test_result(test_id)
            
        return self.test_results[test_id]
    
    async def _test_android_app(
        self,
        apk_path: str,
        device_id: Optional[str] = None,
        test_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Test Android app using existing Android testing logic"""
        config = test_config or {}
        
        # Use first available AVD if not specified
        if not device_id:
            avds = self.android_tools.list_avds()
            if not avds:
                raise ValueError("No Android emulators available")
            device_id = avds[0]['name']
        
        # Create testing task
        test_task = Task(
            description=f"""
            Führe einen umfassenden Test der Android-App durch:
            
            1. Installiere die APK: {apk_path} auf Emulator: {device_id}
            2. Starte die App und warte auf Stabilität
            3. Navigiere durch die wichtigsten Screens:
               - Mache Screenshots von jedem Screen
               - Analysiere die UI-Hierarchie
               - Teste Buttons und interaktive Elemente
            4. Sammle Performance-Metriken:
               - CPU und Memory Usage
               - Startup Time
               - Frame Rate und Jank
            5. Prüfe Barrierefreiheit:
               - Content Descriptions
               - Touch Target Größen
               - Kontraste und Lesbarkeit
            6. Erkenne Fehler und Crashes:
               - Überwache Logcat
               - Dokumentiere alle Fehler mit Screenshots
            
            Erstelle einen strukturierten Bericht mit:
            - Übersicht der getesteten Features
            - Gefundene Fehler (kritisch bis niedrig)
            - Performance-Analyse
            - UX/UI Empfehlungen
            - Barrierefreiheits-Bewertung
            """,
            expected_output="""
            Ein umfassender Testbericht im JSON-Format mit:
            - test_summary: Zusammenfassung der Tests
            - screenshots: Liste der erstellten Screenshots mit Beschreibungen
            - errors: Gefundene Fehler nach Priorität
            - performance: Performance-Metriken
            - accessibility: Barrierefreiheits-Bewertung
            - recommendations: Priorisierte Verbesserungsvorschläge
            """,
            agent=self.crew.agents[0]
        )
        
        # Add task to crew and execute
        self.crew.tasks = [test_task]
        result = self.crew.kickoff()
        
        return self._parse_crew_result(result)
    
    async def _test_ios_app(
        self,
        app_path: str,
        device_id: Optional[str] = None,
        test_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Test iOS app using iOS testing tools"""
        config = test_config or {}
        
        # Use first available simulator if not specified
        if not device_id:
            simulators = self.ios_tools.list_simulators()
            
            # Check if we have actual simulators (not error placeholders)
            real_simulators = [s for s in simulators if s.get('udid') not in ['no-simulator', 'error']]
            
            if not real_simulators:
                raise ValueError(
                    "No iOS simulators found. Please ensure Xcode is installed and "
                    "iOS simulators are downloaded. You can download simulators from "
                    "Xcode > Preferences > Components."
                )
            
            # Use any available simulator
            available = real_simulators
                
            device_id = available[0]['udid']
            
            # Only boot if simulator is shutdown
            if available[0].get('state') == 'Shutdown':
                if not self.ios_tools.boot_simulator(device_id):
                    raise ValueError("Failed to boot iOS simulator")
        
        # Extract app info
        app_info = self.ios_tools.get_app_info(app_path)
        if not app_info:
            raise ValueError("Invalid iOS app bundle")
            
        bundle_id = app_info['bundle_id']
        
        # Create testing task
        test_task = Task(
            description=f"""
            Führe einen umfassenden Test der iOS-App durch:
            
            1. Installiere die App: {app_path} auf Simulator: {device_id}
            2. Starte die App mit Bundle ID: {bundle_id}
            3. Navigiere durch die wichtigsten Screens:
               - Mache Screenshots von jedem Screen
               - Teste Touch-Gesten und Interaktionen
               - Prüfe UI-Elemente und Navigation
            4. Sammle Performance-Metriken:
               - CPU und Memory Usage
               - App Launch Time
               - Frame Rate
            5. Prüfe Barrierefreiheit:
               - VoiceOver Kompatibilität
               - Touch Target Größen
               - Kontraste und Lesbarkeit
            6. Erkenne Fehler und Crashes:
               - Überwache Console Logs
               - Dokumentiere alle Fehler mit Screenshots
            
            Erstelle einen strukturierten Bericht mit:
            - Übersicht der getesteten Features
            - Gefundene Fehler (kritisch bis niedrig)
            - Performance-Analyse
            - UX/UI Empfehlungen
            - Barrierefreiheits-Bewertung
            - iOS-spezifische Empfehlungen
            """,
            expected_output="""
            Ein umfassender Testbericht im JSON-Format mit:
            - test_summary: Zusammenfassung der Tests
            - app_info: App-Informationen (Name, Version, Bundle ID)
            - screenshots: Liste der erstellten Screenshots mit Beschreibungen
            - errors: Gefundene Fehler nach Priorität
            - performance: Performance-Metriken
            - accessibility: Barrierefreiheits-Bewertung
            - recommendations: Priorisierte Verbesserungsvorschläge
            - ios_specific: iOS-spezifische Findings
            """,
            agent=self.crew.agents[0]
        )
        
        # Add task to crew and execute
        self.crew.tasks = [test_task]
        result = self.crew.kickoff()
        
        # Shutdown simulator if we started it
        if config.get('shutdown_after_test', True):
            self.ios_tools.shutdown_simulator(device_id)
        
        return self._parse_crew_result(result)
    
    def get_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get results for a specific test"""
        return self.test_results.get(test_id)
    
    def list_tests(self) -> List[Dict[str, Any]]:
        """List all test runs"""
        return list(self.test_results.values())
    
    def get_available_devices(self, platform: str) -> List[Dict[str, Any]]:
        """Get available devices/simulators for testing"""
        if platform.lower() == 'android':
            return self.android_tools.list_avds()
        elif platform.lower() == 'ios':
            return self.ios_tools.list_simulators()
        else:
            return []
    
    def cleanup_test(self, test_id: str) -> bool:
        """Clean up test artifacts"""
        test = self.test_results.get(test_id)
        if not test:
            return False
            
        # Remove screenshots if they exist
        if 'results' in test and 'screenshots' in test['results']:
            for screenshot in test['results']['screenshots']:
                if 'path' in screenshot and os.path.exists(screenshot['path']):
                    try:
                        os.remove(screenshot['path'])
                    except:
                        pass
                        
        # Remove test from results
        del self.test_results[test_id]
        
        # Remove from storage
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.storage.delete(self.collection, test_id))
            logger.info(f"Deleted test {test_id} from storage")
        except Exception as e:
            logger.error(f"Error deleting test {test_id} from storage: {e}")
        
        return True
    
    async def compare_platforms(
        self,
        android_apk: str,
        ios_app: str,
        test_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run comparative testing between Android and iOS versions"""
        comparison_id = str(uuid.uuid4())
        
        # Run tests on both platforms
        android_result = await self.test_app('android', android_apk, test_config=test_config)
        ios_result = await self.test_app('ios', ios_app, test_config=test_config)
        
        # Create comparison report
        comparison = {
            'id': comparison_id,
            'android_test': android_result,
            'ios_test': ios_result,
            'comparison': self._generate_comparison(android_result, ios_result),
            'created_at': datetime.now().isoformat()
        }
        
        return comparison
    
    def _generate_comparison(
        self,
        android_result: Dict[str, Any],
        ios_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate platform comparison insights"""
        comparison = {
            'feature_parity': [],
            'performance_comparison': {},
            'ui_differences': [],
            'platform_specific_issues': {
                'android': [],
                'ios': []
            },
            'recommendations': []
        }
        
        # Compare performance metrics if available
        if 'results' in android_result and 'results' in ios_result:
            android_perf = android_result['results'].get('performance', {})
            ios_perf = ios_result['results'].get('performance', {})
            
            for metric in ['startup_time', 'memory_usage', 'cpu_usage']:
                if metric in android_perf and metric in ios_perf:
                    comparison['performance_comparison'][metric] = {
                        'android': android_perf[metric],
                        'ios': ios_perf[metric],
                        'difference': abs(android_perf[metric] - ios_perf[metric])
                    }
        
        return comparison
    
    def health_check(self) -> Dict[str, Any]:
        """Check if testing tools are available"""
        health = {
            'status': 'healthy',
            'platforms': {
                'android': {
                    'adb_available': False,
                    'emulators': 0,
                    'status': 'unknown'
                },
                'ios': {
                    'xcrun_available': False,
                    'simulators': 0,
                    'status': 'unknown',
                    'xcode_installed': False
                }
            }
        }
        
        # Check Android
        try:
            avds = self.android_tools.list_avds()
            health['platforms']['android']['adb_available'] = True
            health['platforms']['android']['emulators'] = len(avds)
            health['platforms']['android']['status'] = 'ready' if len(avds) > 0 else 'no_devices'
        except Exception as e:
            health['platforms']['android']['status'] = 'error'
            health['platforms']['android']['error'] = str(e)
            health['status'] = 'degraded'
            
        # Check iOS
        try:
            # Check if xcrun exists
            import subprocess
            xcrun_check = subprocess.run(['which', 'xcrun'], capture_output=True)
            health['platforms']['ios']['xcrun_available'] = xcrun_check.returncode == 0
            
            if health['platforms']['ios']['xcrun_available']:
                sims = self.ios_tools.list_simulators()
                # Filter out placeholder entries
                real_sims = [s for s in sims if s.get('udid') not in ['no-simulator', 'error']]
                health['platforms']['ios']['simulators'] = len(real_sims)
                health['platforms']['ios']['xcode_installed'] = len(real_sims) > 0
                
                if len(real_sims) > 0:
                    health['platforms']['ios']['status'] = 'ready'
                elif any(s.get('udid') == 'no-simulator' for s in sims):
                    health['platforms']['ios']['status'] = 'no_simulators'
                    health['platforms']['ios']['message'] = 'Xcode installed but no iOS simulators found'
                else:
                    health['platforms']['ios']['status'] = 'error'
            else:
                health['platforms']['ios']['status'] = 'xcode_not_found'
                health['platforms']['ios']['message'] = 'Xcode command line tools not installed'
                
        except Exception as e:
            health['platforms']['ios']['status'] = 'error'
            health['platforms']['ios']['error'] = str(e)
            health['status'] = 'degraded'
            
        # Update overall status
        android_ok = health['platforms']['android']['status'] == 'ready'
        ios_ok = health['platforms']['ios']['status'] == 'ready'
        
        if android_ok and ios_ok:
            health['status'] = 'healthy'
        elif android_ok or ios_ok:
            health['status'] = 'partial'
        else:
            health['status'] = 'unhealthy'
            
        return health