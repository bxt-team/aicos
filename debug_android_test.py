#!/usr/bin/env python3
"""Debug script to test Android UI element detection and clicking."""

import asyncio
import re
import subprocess
import xml.etree.ElementTree as ET


async def run_adb_command(command):
    """Run ADB command and return output."""
    full_command = ["adb"] + command
    print(f"Running: {' '.join(full_command)}")
    
    process = await asyncio.create_subprocess_exec(
        *full_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if stderr:
        print(f"Error: {stderr.decode()}")
    
    return stdout.decode(), stderr.decode()


async def get_ui_dump():
    """Get UI hierarchy dump and parse it."""
    print("\n1. Getting UI dump...")
    
    device_path = "/sdcard/ui_dump.xml"
    await run_adb_command(["shell", "uiautomator", "dump", device_path])
    
    stdout, _ = await run_adb_command(["shell", "cat", device_path])
    await run_adb_command(["shell", "rm", device_path])
    
    print(f"UI dump size: {len(stdout)} bytes")
    return stdout


def parse_clickable_elements(ui_dump):
    """Parse clickable elements from UI dump with better detection."""
    print("\n2. Parsing clickable elements...")
    
    # Method 1: Using regex (current implementation)
    regex_pattern = r'<node[^>]*clickable="true"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*/>'
    regex_matches = re.findall(regex_pattern, ui_dump)
    print(f"Regex method found: {len(regex_matches)} elements")
    
    # Method 2: Using XML parsing for more robust detection
    try:
        root = ET.fromstring(ui_dump)
        xml_clickable = []
        
        # Find all nodes with clickable="true"
        for node in root.iter('node'):
            if node.get('clickable') == 'true':
                bounds = node.get('bounds')
                if bounds:
                    # Parse bounds string: "[x1,y1][x2,y2]"
                    match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                    if match:
                        x1, y1, x2, y2 = map(int, match.groups())
                        
                        # Get additional info
                        element_info = {
                            'bounds': (x1, y1, x2, y2),
                            'class': node.get('class', '').split('.')[-1],
                            'resource_id': node.get('resource-id', '').split('/')[-1] if node.get('resource-id') else '',
                            'text': node.get('text', ''),
                            'content_desc': node.get('content-desc', ''),
                            'enabled': node.get('enabled') == 'true',
                            'focusable': node.get('focusable') == 'true',
                            'focused': node.get('focused') == 'true',
                            'scrollable': node.get('scrollable') == 'true',
                            'long_clickable': node.get('long-clickable') == 'true',
                            'checkable': node.get('checkable') == 'true',
                            'checked': node.get('checked') == 'true'
                        }
                        xml_clickable.append(element_info)
        
        print(f"XML method found: {len(xml_clickable)} elements")
        
        # Show details of first 10 clickable elements
        print("\nFirst 10 clickable elements:")
        for i, elem in enumerate(xml_clickable[:10]):
            x1, y1, x2, y2 = elem['bounds']
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            width = x2 - x1
            height = y2 - y1
            
            print(f"\n{i+1}. {elem['class']}")
            print(f"   ID: {elem['resource_id'] or 'None'}")
            print(f"   Text: {elem['text'] or 'None'}")
            print(f"   Content: {elem['content_desc'] or 'None'}")
            print(f"   Bounds: [{x1},{y1}][{x2},{y2}] (center: {center_x},{center_y})")
            print(f"   Size: {width}x{height}px")
            print(f"   Enabled: {elem['enabled']}")
            print(f"   Focusable: {elem['focusable']}")
        
        return xml_clickable
        
    except ET.ParseError as e:
        print(f"XML parsing error: {e}")
        print("Falling back to regex method")
        
        # Fallback: return regex results
        return [(int(x1), int(y1), int(x2), int(y2)) for x1, y1, x2, y2 in regex_matches]


async def test_element_detection():
    """Test UI element detection."""
    print("Android UI Element Detection Debug Script")
    print("=" * 50)
    
    # Check if device is connected
    stdout, _ = await run_adb_command(["devices"])
    print("Connected devices:")
    print(stdout)
    
    if "device" not in stdout:
        print("No device connected! Please connect a device or start an emulator.")
        return
    
    # Get current activity
    stdout, _ = await run_adb_command(["shell", "dumpsys", "window", "windows", "|", "grep", "-E", "mCurrentFocus"])
    print(f"\nCurrent focus: {stdout.strip()}")
    
    # Get UI dump
    ui_dump = await get_ui_dump()
    
    # Save UI dump for inspection
    with open("ui_dump_debug.xml", "w") as f:
        f.write(ui_dump)
    print("\nUI dump saved to ui_dump_debug.xml for inspection")
    
    # Parse clickable elements
    clickable_elements = parse_clickable_elements(ui_dump)
    
    # Check if we're missing elements due to regex pattern
    print("\n3. Checking for pattern issues...")
    
    # Look for variations in the XML structure
    print("\nChecking for different node patterns:")
    
    # Pattern 1: Self-closing tags
    pattern1 = len(re.findall(r'<node[^>]*clickable="true"[^>]*/>', ui_dump))
    print(f"Self-closing clickable nodes: {pattern1}")
    
    # Pattern 2: Non-self-closing tags
    pattern2 = len(re.findall(r'<node[^>]*clickable="true"[^>]*>[^<]*</node>', ui_dump))
    print(f"Non-self-closing clickable nodes: {pattern2}")
    
    # Pattern 3: Any clickable="true"
    pattern3 = len(re.findall(r'clickable="true"', ui_dump))
    print(f"Total clickable=\"true\" occurrences: {pattern3}")
    
    # Check hierarchy depth
    print("\n4. Checking UI hierarchy depth...")
    max_depth = ui_dump.count('<node')
    print(f"Total nodes in hierarchy: {max_depth}")
    
    # Suggest improvements
    print("\n5. Recommendations:")
    if len(clickable_elements) == 0:
        print("- No clickable elements found!")
        print("- Check if the app is fully loaded")
        print("- Try waiting longer after app launch")
        print("- Verify the app has interactive elements on the current screen")
    elif len(clickable_elements) < 5:
        print("- Very few clickable elements found")
        print("- The app might not be fully loaded")
        print("- Some elements might be using touch handlers instead of clickable attribute")
        print("- Consider also checking for focusable=\"true\" elements")
    else:
        print("- Element detection seems to be working")
        print("- Found sufficient clickable elements to test")


async def main():
    """Main function."""
    await test_element_detection()


if __name__ == "__main__":
    asyncio.run(main())