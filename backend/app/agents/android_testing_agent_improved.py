"""Improved UI action detection methods for AndroidTestingAgent."""

import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple
import asyncio


async def _get_ui_dump_improved(self) -> str:
    """Get UI hierarchy dump with better error handling."""
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
        stdout, stderr = await self._run_adb_command(["shell", "cat", device_path])
        
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


def _parse_clickable_elements_xml(self, ui_dump: str) -> List[Dict[str, Any]]:
    """Parse clickable elements using XML parsing for better accuracy."""
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
                'switch', 'togglebutton', 'chip', 'cardview'
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
        
        self.logger.info(f"Found {len(clickable_elements)} interactive elements using XML parsing")
        return clickable_elements
        
    except ET.ParseError as e:
        self.logger.error(f"XML parsing error: {e}")
        self.logger.debug(f"First 500 chars of dump: {ui_dump[:500]}")
        return []
    except Exception as e:
        self.logger.error(f"Error parsing clickable elements: {e}")
        return []


async def _perform_ui_actions_improved(self, package_name: str, test_id: str) -> List[Dict[str, Any]]:
    """Improved UI action testing with better element detection."""
    self.logger.info("Starting improved UI action testing...")
    actions_log = []
    visited_screens = set()
    
    # Get initial UI state
    ui_dump = await self._get_ui_dump_improved()
    if not ui_dump:
        self.logger.error("Failed to get UI dump")
        return actions_log
    
    # Save initial dump for debugging
    initial_dump_path = f"/tmp/{test_id}_initial_ui_dump.xml"
    with open(initial_dump_path, 'w') as f:
        f.write(ui_dump)
    self.logger.debug(f"Saved initial UI dump to {initial_dump_path}")
    
    # Parse clickable elements using improved method
    clickable_elements = self._parse_clickable_elements_xml(ui_dump)
    
    if not clickable_elements:
        self.logger.warning("No clickable elements found, trying fallback regex method")
        # Fallback to regex method
        regex_pattern = r'<node[^>]*clickable="true"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*'
        matches = re.findall(regex_pattern, ui_dump)
        for x1, y1, x2, y2 in matches:
            clickable_elements.append({
                'bounds': (int(x1), int(y1), int(x2), int(y2)),
                'center': ((int(x1) + int(x2)) // 2, (int(y1) + int(y2)) // 2),
                'class': 'Unknown',
                'text': '',
                'content_desc': ''
            })
    
    self.logger.info(f"Found {len(clickable_elements)} clickable elements to test")
    
    # Log details of elements found
    for i, elem in enumerate(clickable_elements[:5]):
        self.logger.debug(
            f"Element {i+1}: {elem['class']} at {elem['center']}, "
            f"text='{elem['text']}', desc='{elem['content_desc']}'"
        )
    
    # Test tapping various elements
    max_actions = min(len(clickable_elements), 20)  # Test up to 20 elements
    for i, element in enumerate(clickable_elements[:max_actions]):
        try:
            x, y = element['center']
            element_desc = (
                f"{element['class']} "
                f"(text: '{element['text'][:20]}', desc: '{element['content_desc'][:20]}')"
            )
            
            self.logger.info(f"Testing tap {i+1}/{max_actions} on {element_desc} at ({x}, {y})")
            
            # Take before screenshot
            before_screenshot = await self._capture_screenshot(test_id, f"before_tap_{i}")
            
            # Get screen signature before tap
            before_screen_sig = self._get_screen_signature(ui_dump)
            
            # Perform tap
            await self._run_adb_command(["shell", "input", "tap", str(x), str(y)])
            
            # Wait for UI to update
            await asyncio.sleep(1.5)
            
            # Take after screenshot
            after_screenshot = await self._capture_screenshot(test_id, f"after_tap_{i}")
            
            # Check if app crashed
            stdout, _ = await self._run_adb_command(["shell", "pidof", package_name])
            app_crashed = len(stdout.strip()) == 0
            
            # Get new UI state
            new_ui_dump = await self._get_ui_dump_improved()
            after_screen_sig = self._get_screen_signature(new_ui_dump)
            
            # Check if screen changed
            screen_changed = before_screen_sig != after_screen_sig
            
            action_result = {
                "action": "tap",
                "element": element_desc,
                "coordinates": {"x": x, "y": y},
                "before_screenshot": before_screenshot,
                "after_screenshot": after_screenshot,
                "app_crashed": app_crashed,
                "screen_changed": screen_changed,
                "element_details": {
                    "class": element['class'],
                    "text": element['text'],
                    "content_desc": element['content_desc'],
                    "resource_id": element.get('resource_id', '')
                }
            }
            
            if app_crashed:
                self.logger.warning(f"App crashed after tapping {element_desc}")
                action_result["crash_details"] = "App stopped responding"
                
                # Restart app
                self.logger.info("Attempting to restart crashed app...")
                await self._launch_app(package_name)
                await asyncio.sleep(3)
            
            elif screen_changed:
                self.logger.info(f"Screen changed after tapping {element_desc}")
                visited_screens.add(after_screen_sig)
                
                # If we navigated to a new screen, also test the back button
                if len(visited_screens) > 1:
                    self.logger.debug("Testing back navigation...")
                    await self._run_adb_command(["shell", "input", "keyevent", "KEYCODE_BACK"])
                    await asyncio.sleep(1)
                    actions_log.append({
                        "action": "back",
                        "purpose": "Navigate back from new screen"
                    })
            
            else:
                self.logger.debug(f"No visible change after tapping {element_desc}")
            
            actions_log.append(action_result)
            
        except Exception as e:
            self.logger.error(f"Error during tap action {i+1}: {e}")
            continue
    
    # Test scrolling in different directions
    self.logger.info("Testing scroll actions...")
    
    # Scroll down
    await self._run_adb_command([
        "shell", "input", "swipe", "500", "1200", "500", "400", "300"
    ])
    await asyncio.sleep(1)
    actions_log.append({
        "action": "scroll",
        "direction": "down",
        "description": "Scroll to see more content"
    })
    
    # Scroll up
    await self._run_adb_command([
        "shell", "input", "swipe", "500", "400", "500", "1200", "300"
    ])
    await asyncio.sleep(1)
    actions_log.append({
        "action": "scroll",
        "direction": "up",
        "description": "Scroll back to top"
    })
    
    # Test horizontal scroll if applicable
    if any(elem.get('scrollable') for elem in clickable_elements):
        self.logger.debug("Testing horizontal scroll...")
        await self._run_adb_command([
            "shell", "input", "swipe", "800", "800", "200", "800", "300"
        ])
        actions_log.append({
            "action": "scroll",
            "direction": "horizontal",
            "description": "Test horizontal scrolling"
        })
    
    self.logger.info(f"Completed {len(actions_log)} UI actions")
    self.logger.info(f"Visited {len(visited_screens)} unique screens")
    
    return actions_log


def _get_screen_signature(self, ui_dump: str) -> str:
    """Generate a signature for the current screen state."""
    # Extract key elements that define the screen
    # This helps identify when we've navigated to a new screen
    try:
        root = ET.fromstring(ui_dump)
        
        # Get all text and content descriptions
        texts = []
        for node in root.iter('node'):
            text = node.get('text', '').strip()
            if text and len(text) > 2:  # Skip very short texts
                texts.append(text)
            
            desc = node.get('content-desc', '').strip()
            if desc and len(desc) > 2:
                texts.append(desc)
        
        # Sort and join to create signature
        texts.sort()
        signature = '|'.join(texts[:20])  # Use top 20 texts
        
        # Add structure info
        clickable_count = ui_dump.count('clickable="true"')
        signature += f"|clickable:{clickable_count}"
        
        return signature
        
    except:
        # Fallback to simple hash
        return str(hash(ui_dump))


# Additional helper method for finding specific UI elements
def _find_element_by_text(self, elements: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
    """Find an element by its text or content description."""
    text_lower = text.lower()
    
    for elem in elements:
        if text_lower in elem.get('text', '').lower():
            return elem
        if text_lower in elem.get('content_desc', '').lower():
            return elem
    
    return None


# Method to wait for UI to stabilize
async def _wait_for_ui_stable(self, timeout: float = 5.0) -> bool:
    """Wait for UI to become stable (no changes)."""
    self.logger.debug("Waiting for UI to stabilize...")
    
    stable_count = 0
    last_dump = ""
    check_interval = 0.5
    
    start_time = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start_time < timeout:
        current_dump = await self._get_ui_dump_improved()
        
        if current_dump == last_dump:
            stable_count += 1
            if stable_count >= 2:  # Stable for 1 second
                self.logger.debug("UI is stable")
                return True
        else:
            stable_count = 0
            
        last_dump = current_dump
        await asyncio.sleep(check_interval)
    
    self.logger.warning("UI did not stabilize within timeout")
    return False