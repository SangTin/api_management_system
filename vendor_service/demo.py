#!/usr/bin/env python
"""
Demo script for API Management System with multiple vendor types
"""
import requests
import json
import time
import uuid

BASE_URL = "http://localhost:8000/api"  # API Gateway URL
USER_TOKEN = None  # Will be populated after login

def login():
    """Login to get JWT token"""
    response = requests.post(
        f"{BASE_URL}/auth/login/",
        json={
            "username": "suzueyume",
            "password": "sangpro1100"
        }
    )
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        exit(1)
        
    data = response.json()
    global USER_TOKEN
    USER_TOKEN = data['access']
    print(f"Logged in successfully. User: {data['user']['username']}")
    return data['user']

def get_headers():
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {USER_TOKEN}",
        "Content-Type": "application/json"
    }

def create_vendor(name, code, description=""):
    """Create a vendor if not exists"""
    # Check if vendor exists
    response = requests.get(
        f"{BASE_URL}/vendors/?name={name}",
        headers=get_headers()
    )
    
    print(f"Checking for existing vendor: {name}")
    vendors = response.json()['results']
    if vendors:
        for vendor in vendors:
            if vendor['name'] == name:
                print(f"Using existing vendor: {vendor['name']}")
                return vendor
    
    # Create new vendor
    response = requests.post(
        f"{BASE_URL}/vendors/",
        headers=get_headers(),
        json={
            "name": name,
            "code": code,
            "description": description,
            "contact_info": {
                "email": f"{code.lower()}@example.com",
                "phone": "123456789"
            },
            "status": "active"
        }
    )
    
    if response.status_code != 201:
        print(f"Create vendor failed: {response.status_code}")
        print(response.text)
        exit(1)
        
    vendor = response.json()
    print(f"Created vendor: {vendor['name']}")
    return vendor

def create_api_config(vendor_id, name, base_url, auth_type, auth_config):
    """Create API configuration if not exists"""
    # Check if API config exists
    response = requests.get(
        f"{BASE_URL}/api-configs/?vendor_id={vendor_id}",
        headers=get_headers()
    )
    
    configs = response.json()['results']
    for config in configs:
        if config['name'] == name:
            print(f"Using existing API config: {config['name']}")
            return config
    
    # Create new API config
    response = requests.post(
        f"{BASE_URL}/api-configs/",
        headers=get_headers(),
        json={
            "name": name,
            "version": "1.0",
            "description": f"API for {name}",
            "base_url": base_url,
            "auth_type": auth_type,
            "auth_config": auth_config,
            "vendor_id": vendor_id
        }
    )
    
    if response.status_code != 201:
        print(f"Create API config failed: {response.status_code}")
        print(response.text)
        exit(1)
        
    api_config = response.json()
    print(f"Created API config: {api_config['name']}")
    return api_config

def create_smart_traffic_templates(api_config_id):
    """Create command templates for Smart Traffic Solutions"""
    # Check if command templates exist
    response = requests.get(
        f"{BASE_URL}/command-templates/?api_config={api_config_id}",
        headers=get_headers()
    )
    
    templates = response.json()['results']
    if templates:
        print(f"Using existing command templates for Smart Traffic ({len(templates)})")
        return templates
    
    # Create get status command
    status_response = requests.post(
        f"{BASE_URL}/command-templates/",
        headers=get_headers(),
        json={
            "api_config_id": api_config_id,
            "name": "Get Traffic Light Status",
            "command_type": "get_status",
            "description": "Get the status of a traffic light",
            "method": "GET",
            "url_template": "devices/{device_id}",
            "body_template": {},
            "required_params": ["device_id"]
        }
    )
    
    if status_response.status_code != 201:
        print(f"Create status command failed: {status_response.status_code}")
        print(status_response.text)
    else:
        print("Created get_status command template")
    
    # Create turn on command
    turn_on_response = requests.post(
        f"{BASE_URL}/command-templates/",
        headers=get_headers(),
        json={
            "api_config_id": api_config_id,
            "name": "Turn On Green Light",
            "command_type": "turn_on_green",
            "description": "Turn on the green traffic light",
            "method": "POST",
            "url_template": "devices/{device_id}/control",
            "body_template": {
                "command": "turn_on",
                "intensity": 100
            },
            "required_params": ["device_id"]
        }
    )
    
    if turn_on_response.status_code != 201:
        print(f"Create turn on command failed: {turn_on_response.status_code}")
        print(turn_on_response.text)
    else:
        print("Created turn_on_green command template")
    
    # Create turn off command
    turn_off_response = requests.post(
        f"{BASE_URL}/command-templates/",
        headers=get_headers(),
        json={
            "api_config_id": api_config_id,
            "name": "Turn On Red Light",
            "command_type": "turn_on_red",
            "description": "Turn on the red traffic light (turn off green)",
            "method": "POST",
            "url_template": "devices/{device_id}/control",
            "body_template": {
                "command": "turn_off",
                "intensity": 0
            },
            "required_params": ["device_id"]
        }
    )
    
    if turn_off_response.status_code != 201:
        print(f"Create turn off command failed: {turn_off_response.status_code}")
        print(turn_off_response.text)
    else:
        print("Created turn_on_red command template")
    
    # Create set yellow command
    yellow_response = requests.post(
        f"{BASE_URL}/command-templates/",
        headers=get_headers(),
        json={
            "api_config_id": api_config_id,
            "name": "Set Yellow Light",
            "command_type": "set_yellow",
            "description": "Set the traffic light to yellow",
            "method": "POST",
            "url_template": "devices/{device_id}/control",
            "body_template": {
                "command": "set_yellow",
                "intensity": 90
            },
            "required_params": ["device_id"]
        }
    )
    
    if yellow_response.status_code != 201:
        print(f"Create yellow command failed: {yellow_response.status_code}")
        print(yellow_response.text)
    else:
        print("Created set_yellow command template")
    
    # Get all command templates
    response = requests.get(
        f"{BASE_URL}/command-templates/?api_config={api_config_id}",
        headers=get_headers()
    )
    
    return response.json()['results']

def create_led_display_templates(api_config_id):
    """Create command templates for LED Display Systems"""
    # Check if command templates exist
    response = requests.get(
        f"{BASE_URL}/command-templates/?api_config={api_config_id}",
        headers=get_headers()
    )
    
    templates = response.json()['results']
    if templates:
        print(f"Using existing command templates for LED Display ({len(templates)})")
        return templates
    
    # Create get status command
    status_response = requests.post(
        f"{BASE_URL}/command-templates/",
        headers=get_headers(),
        json={
            "api_config_id": api_config_id,
            "name": "Get Display Status",
            "command_type": "get_status",
            "description": "Get the status of an LED display",
            "method": "GET",
            "url_template": "control/{device_id}",
            "body_template": {},
            "required_params": ["device_id"]
        }
    )
    
    if status_response.status_code != 201:
        print(f"Create status command failed: {status_response.status_code}")
        print(status_response.text)
    else:
        print("Created get_status command template")
    
    # Create update message command
    message_response = requests.post(
        f"{BASE_URL}/command-templates/",
        headers=get_headers(),
        json={
            "api_config_id": api_config_id,
            "name": "Update Display Message",
            "command_type": "update_message",
            "description": "Update the message on an LED display",
            "method": "POST",
            "url_template": "control/{device_id}",
            "body_template": {
                "action": "update_message",
                "message": "{message}"
            },
            "required_params": ["device_id", "message"]
        }
    )
    
    if message_response.status_code != 201:
        print(f"Create message command failed: {message_response.status_code}")
        print(message_response.text)
    else:
        print("Created update_message command template")
    
    # Create turn on command
    turn_on_response = requests.post(
        f"{BASE_URL}/command-templates/",
        headers=get_headers(),
        json={
            "api_config_id": api_config_id,
            "name": "Turn On Display",
            "command_type": "turn_on",
            "description": "Turn on an LED display",
            "method": "POST",
            "url_template": "control/{device_id}",
            "body_template": {
                "action": "turn_on"
            },
            "required_params": ["device_id"]
        }
    )
    
    if turn_on_response.status_code != 201:
        print(f"Create turn on command failed: {turn_on_response.status_code}")
        print(turn_on_response.text)
    else:
        print("Created turn_on command template")
    
    # Create turn off command
    turn_off_response = requests.post(
        f"{BASE_URL}/command-templates/",
        headers=get_headers(),
        json={
            "api_config_id": api_config_id,
            "name": "Turn Off Display",
            "command_type": "turn_off",
            "description": "Turn off an LED display",
            "method": "POST",
            "url_template": "control/{device_id}",
            "body_template": {
                "action": "turn_off"
            },
            "required_params": ["device_id"]
        }
    )
    
    if turn_off_response.status_code != 201:
        print(f"Create turn off command failed: {turn_off_response.status_code}")
        print(turn_off_response.text)
    else:
        print("Created turn_off command template")
    
    # Get all command templates
    response = requests.get(
        f"{BASE_URL}/command-templates/?api_config={api_config_id}",
        headers=get_headers()
    )
    
    return response.json()['results']

def create_camera_templates(api_config_id):
    """Create command templates for Intelligent Cameras"""
    # Check if command templates exist
    response = requests.get(
        f"{BASE_URL}/command-templates/?api_config={api_config_id}",
        headers=get_headers()
    )
    
    templates = response.json()['results']
    if templates:
        print(f"Using existing command templates for Cameras ({len(templates)})")
        return templates
    
    # Create get camera info command
    info_response = requests.post(
        f"{BASE_URL}/command-templates/",
        headers=get_headers(),
        json={
            "api_config_id": api_config_id,
            "name": "Get Camera Info",
            "command_type": "get_info",
            "description": "Get information about a camera",
            "method": "GET",
            "url_template": "api/v2/cameras/{device_id}",
            "body_template": {},
            "required_params": ["device_id"]
        }
    )
    
    if info_response.status_code != 201:
        print(f"Create info command failed: {info_response.status_code}")
        print(info_response.text)
    else:
        print("Created get_info command template")
    
    # Create start recording command
    start_rec_response = requests.post(
        f"{BASE_URL}/command-templates/",
        headers=get_headers(),
        json={
            "api_config_id": api_config_id,
            "name": "Start Recording",
            "command_type": "start_recording",
            "description": "Start recording with a camera",
            "method": "POST",
            "url_template": "api/v2/cameras/{device_id}/start_recording",
            "body_template": {},
            "required_params": ["device_id"]
        }
    )
    
    if start_rec_response.status_code != 201:
        print(f"Create start recording command failed: {start_rec_response.status_code}")
        print(start_rec_response.text)
    else:
        print("Created start_recording command template")
    
    # Create stop recording command
    stop_rec_response = requests.post(
        f"{BASE_URL}/command-templates/",
        headers=get_headers(),
        json={
            "api_config_id": api_config_id,
            "name": "Stop Recording",
            "command_type": "stop_recording",
            "description": "Stop recording with a camera",
            "method": "POST",
            "url_template": "api/v2/cameras/{device_id}/stop_recording",
            "body_template": {},
            "required_params": ["device_id"]
        }
    )
    
    if stop_rec_response.status_code != 201:
        print(f"Create stop recording command failed: {stop_rec_response.status_code}")
        print(stop_rec_response.text)
    else:
        print("Created stop_recording command template")
    
    # Create zoom command
    zoom_response = requests.post(
        f"{BASE_URL}/command-templates/",
        headers=get_headers(),
        json={
            "api_config_id": api_config_id,
            "name": "Zoom Camera",
            "command_type": "zoom",
            "description": "Zoom a PTZ camera",
            "method": "POST",
            "url_template": "api/v2/cameras/{device_id}/zoom",
            "body_template": {
                "level": "{zoom_level}"
            },
            "required_params": ["device_id", "zoom_level"]
        }
    )
    
    if zoom_response.status_code != 201:
        print(f"Create zoom command failed: {zoom_response.status_code}")
        print(zoom_response.text)
    else:
        print("Created zoom command template")
    
    # Get all command templates
    response = requests.get(
        f"{BASE_URL}/command-templates/?api_config={api_config_id}",
        headers=get_headers()
    )
    
    return response.json()['results']

def create_device(vendor_id, name, device_id, model, command_templates):
    """Create device if not exists"""
    # Check if device exists
    response = requests.get(
        f"{BASE_URL}/devices/?name={name}",
        headers=get_headers()
    )
    
    devices = response.json()['results']
    for device in devices:
        if device['name'] == name:
            print(f"Using existing device: {device['name']}")
            return device
    
    # Create new device
    response = requests.post(
        f"{BASE_URL}/devices/",
        headers=get_headers(),
        json={
            "name": name,
            "vendor_id": vendor_id,
            "model": model,
            "serial_number": device_id,
            "firmware_version": "1.0",
            "command_ids": [template['id'] for template in command_templates]
        }
    )
    
    if response.status_code != 201:
        print(f"Create device failed: {response.status_code}")
        print(response.text)
        exit(1)
        
    device = response.json()
    print(f"Created device: {device['name']}")
    return device

def demo_make_primary(device_id):
    """Demo changing primary command"""
    print("\n=== COMMAND MANAGEMENT DEMO ===\n")
    
    # Step 1: Get all commands for device
    print("\n1. Getting device commands...")
    response = requests.get(
        f"{BASE_URL}/device-commands/?device={device_id}",
        headers=get_headers()
    )
    
    if response.status_code != 200:
        print(f"Failed to get device commands: {response.status_code}")
        print(response.text)
        return
    
    commands = response.json()['results']
    print(f"Found {len(commands)} commands")
    
    # Tìm command có type là get_status
    status_commands = [cmd for cmd in commands if cmd['command_type'] == 'get_status']
    if not status_commands:
        print("No status commands found")
        return
    
    # Lấy command đầu tiên
    command = status_commands[0]
    command_id = command['id']
    
    # Step 2: Make this command primary
    print(f"\n2. Making command {command_id} primary...")
    make_primary_command_id = execute_command(
        device_id, 
        "make_primary", 
        {"command_id": command_id}
    )
    
    if make_primary_command_id:
        make_primary_result = check_command_status(make_primary_command_id)
        
        # Kiểm tra kết quả
        if make_primary_result and 'execution' in make_primary_result:
            result = make_primary_result['execution']['result']
            if result.get('success', False):
                print("Successfully set command as primary")
            else:
                print(f"Failed to set command as primary: {result.get('message', 'Unknown error')}")

def execute_command(device_id, command_type, params=None):
    """Execute a command on a device"""
    if params is None:
        params = {}
    
    response = requests.post(
        f"{BASE_URL}/commands/execute/",
        headers=get_headers(),
        json={
            "device_id": device_id,
            "command_type": command_type,
            "params": params
        }
    )
    
    if response.status_code != 200:
        print(f"Execute command failed: {response.status_code}")
        print(response.text)
        return None
        
    result = response.json()
    command_id = result['command_id']
    print(f"Command {command_type} initiated with ID: {command_id}")
    return command_id

def check_command_status(command_id, max_retries=10, retry_delay=1):
    """Check command execution status"""
    retries = 0
    
    while retries < max_retries:
        response = requests.get(
            f"{BASE_URL}/commands/{command_id}/status/",
            headers=get_headers()
        )
        
        if response.status_code != 200:
            print(f"Check status failed: {response.status_code}")
            print(response.text)
            return None
            
        result = response.json()
        status = result['status']
        print(f"Command status: {status}")
        
        if status in ['completed', 'failed']:
            if 'execution' in result:
                execution_result = result['execution']['result']
                print(f"Result: {json.dumps(execution_result, indent=2)}")
            return result
        
        retries += 1
        time.sleep(retry_delay)
    
    print("Command status check timed out")
    return None

def demo_traffic_light(device_id):
    """Demo traffic light control"""
    print("\n=== TRAFFIC LIGHT DEMO ===\n")
    
    # Step 1: Get status
    print("\n1. Getting traffic light status...")
    status_command_id = execute_command(device_id, "get_status", {"device_id": "TL001"})
    status_result = check_command_status(status_command_id)
    
    # Step 2: Turn on green light
    print("\n2. Turning on green light...")
    turn_on_command_id = execute_command(device_id, "turn_on_green", {"device_id": "TL001"})
    turn_on_result = check_command_status(turn_on_command_id)
    
    # Step 3: Check status again
    print("\n3. Checking status after turning on green...")
    status_command_id2 = execute_command(device_id, "get_status", {"device_id": "TL001"})
    status_result2 = check_command_status(status_command_id2)
    
    # Step 4: Set yellow
    print("\n4. Setting yellow light...")
    yellow_command_id = execute_command(device_id, "set_yellow", {"device_id": "TL001"})
    yellow_result = check_command_status(yellow_command_id)
    
    # Step 5: Turn on red light
    print("\n5. Turning on red light...")
    red_command_id = execute_command(device_id, "turn_on_red", {"device_id": "TL001"})
    red_result = check_command_status(red_command_id)
    
    # Step 6: Final status check
    print("\n6. Final status check...")
    status_command_id3 = execute_command(device_id, "get_status", {"device_id": "TL001"})
    status_result3 = check_command_status(status_command_id3)

def demo_led_display(device_id):
    """Demo LED display control"""
    print("\n=== LED DISPLAY DEMO ===\n")
    
    # Step 1: Get status
    print("\n1. Getting LED display status...")
    status_command_id = execute_command(device_id, "get_status", {"device_id": "LED001"})
    status_result = check_command_status(status_command_id)
    
    # Step 2: Update message
    print("\n2. Updating display message...")
    message = "SLOW DOWN - WORK ZONE"
    message_command_id = execute_command(
        device_id, 
        "update_message", 
        {"device_id": "LED001", "message": message}
    )
    message_result = check_command_status(message_command_id)
    
    # Step 3: Check status after update
    print("\n3. Checking status after message update...")
    status_command_id2 = execute_command(device_id, "get_status", {"device_id": "LED001"})
    status_result2 = check_command_status(status_command_id2)
    
    # Step 4: Turn off display
    print("\n4. Turning off display...")
    off_command_id = execute_command(device_id, "turn_off", {"device_id": "LED001"})
    off_result = check_command_status(off_command_id)
    
    # Step 5: Turn on display
    print("\n5. Turning on display...")
    on_command_id = execute_command(device_id, "turn_on", {"device_id": "LED001"})
    on_result = check_command_status(on_command_id)
    
    # Step 6: Final status check
    print("\n6. Final status check...")
    status_command_id3 = execute_command(device_id, "get_status", {"device_id": "LED001"})
    status_result3 = check_command_status(status_command_id3)

def demo_camera(device_id):
    """Demo camera control"""
    print("\n=== INTELLIGENT CAMERA DEMO ===\n")
    
    # Step 1: Get camera info
    print("\n1. Getting camera info...")
    info_command_id = execute_command(device_id, "get_info", {"device_id": "CAM001"})
    info_result = check_command_status(info_command_id)
    
    # Step 2: Start recording
    print("\n2. Starting recording...")
    start_command_id = execute_command(device_id, "start_recording", {"device_id": "CAM001"})
    start_result = check_command_status(start_command_id)
    
    # Step 3: Zoom camera
    print("\n3. Zooming camera...")
    zoom_command_id = execute_command(
        device_id, 
        "zoom", 
        {"device_id": "CAM001", "zoom_level": 2.5}
    )
    zoom_result = check_command_status(zoom_command_id)
    
    # Step 4: Get updated info
    print("\n4. Getting updated camera info...")
    info_command_id2 = execute_command(device_id, "get_info", {"device_id": "CAM001"})
    info_result2 = check_command_status(info_command_id2)
    
    # Step 5: Stop recording
    print("\n5. Stopping recording...")
    stop_command_id = execute_command(device_id, "stop_recording", {"device_id": "CAM001"})
    stop_result = check_command_status(stop_command_id)
    
    # Step 6: Final info check
    print("\n6. Final info check...")
    info_command_id3 = execute_command(device_id, "get_info", {"device_id": "CAM001"})
    info_result3 = check_command_status(info_command_id3)

def main():
    """Main demo flow"""
    print("=== API MANAGEMENT SYSTEM DEMO ===\n")
    
    # Step 1: Login
    user = login()
    
    # Step 2: Create vendors
    traffic_vendor = create_vendor("Smart Traffic Solutions", "STS", "Vendor for traffic light control")
    led_vendor = create_vendor("Digital LED Systems", "DLS", "Vendor for LED display control")
    camera_vendor = create_vendor("Intelligent Security Systems", "ISS", "Vendor for intelligent camera control")
    
    # Step 3: Create API configurations
    traffic_api = create_api_config(
        traffic_vendor['id'],
        "Traffic Light API",
        "http://mock-vendors:9000/smart_traffic",
        "api_key",
        {"key_name": "X-API-Key", "api_key": "traffic-api-key-123"}
    )
    
    led_api = create_api_config(
        led_vendor['id'],
        "LED Display API",
        "http://mock-vendors:9000/led_display",
        "api_key",
        {"key_name": "X-API-Key", "api_key": "led-api-key-456"}
    )
    
    camera_api = create_api_config(
        camera_vendor['id'],
        "Camera API",
        "http://mock-vendors:9000/intelligent_camera",
        "bearer",
        {"token": "camera-token-789"}
    )
    
    # Step 4: Create command templates
    traffic_templates = create_smart_traffic_templates(traffic_api['id'])
    led_templates = create_led_display_templates(led_api['id'])
    camera_templates = create_camera_templates(camera_api['id'])
    
    # Step 5: Create devices
    traffic_device = create_device(
        traffic_vendor['id'], 
        "Traffic Light #1", 
        "TL001", 
        "TL-2000", 
        traffic_templates
    )
    
    led_device = create_device(
        led_vendor['id'], 
        "Highway LED Display #1", 
        "LED001", 
        "LED-5000", 
        led_templates
    )
    
    camera_device = create_device(
        camera_vendor['id'], 
        "PTZ Camera #1", 
        "CAM001", 
        "CAM-8000", 
        camera_templates
    )
    
    # Step 6: Demo each device type
    demo_traffic_light(traffic_device['id'])
    # demo_led_display(led_device['id'])
    # demo_camera(camera_device['id'])
    
    print("\n=== DEMO COMPLETED ===\n")

if __name__ == "__main__":
    main()