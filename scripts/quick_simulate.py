import requests
import random
import time
import os
from datetime import datetime, timedelta
import uuid

# Configuration
TELEMETRY_URL = "http://localhost:8001/telemetry"
DEVICES_URL = "http://localhost:8001/devices"
AI_SERVICE_URL = "http://localhost:8002"
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "your-auth-token-here")

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

# Device templates to create
DEVICE_TEMPLATES = [
    {
        "name": "Living Room AC",
        "type": "air_conditioner",
        "room": "living_room",
        "power_rating": 2.5,
        "model": "LG Dual Inverter",
        "manufacturer": "LG"
    },
    {
        "name": "Kitchen Refrigerator",
        "type": "refrigerator",
        "room": "kitchen",
        "power_rating": 0.15,
        "model": "Samsung Family Hub",
        "manufacturer": "Samsung"
    },
    {
        "name": "Washing Machine",
        "type": "washing_machine",
        "room": "laundry_room",
        "power_rating": 1.5,
        "model": "Whirlpool Front Load",
        "manufacturer": "Whirlpool"
    },
    {
        "name": "Living Room TV",
        "type": "television",
        "room": "living_room",
        "power_rating": 0.15,
        "model": "Samsung QLED 55\"",
        "manufacturer": "Samsung"
    },
    {
        "name": "Bedroom Lights",
        "type": "lighting",
        "room": "bedroom",
        "power_rating": 0.2,
        "model": "Philips Hue",
        "manufacturer": "Philips"
    },
    {
        "name": "Home Office Computer",
        "type": "computer",
        "room": "office",
        "power_rating": 0.3,
        "model": "Dell OptiPlex",
        "manufacturer": "Dell"
    },
    {
        "name": "Kitchen Dishwasher",
        "type": "dishwasher",
        "room": "kitchen",
        "power_rating": 1.8,
        "model": "Bosch 500 Series",
        "manufacturer": "Bosch"
    },
    {
        "name": "Master Bedroom AC",
        "type": "air_conditioner",
        "room": "bedroom",
        "power_rating": 1.5,
        "model": "Daikin Split AC",
        "manufacturer": "Daikin"
    }
]

def create_devices():
    """Create devices and return their IDs"""
    print("Creating devices...")
    created_devices = []
    
    for template in DEVICE_TEMPLATES:
        try:
            response = requests.post(DEVICES_URL, json=template, headers=headers)
            if response.status_code == 201:
                device_data = response.json()
                device_id = device_data.get("data", {}).get("id") or device_data.get("id")
                created_devices.append({
                    "id": device_id,
                    "name": template["name"],
                    "type": template["type"],
                    "power_rating": template["power_rating"]
                })
                print(f"✓ Created device: {template['name']} (ID: {device_id})")
            else:
                print(f"✗ Failed to create {template['name']}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"✗ Error creating {template['name']}: {e}")
        
        time.sleep(0.1)  # Small delay between device creation
    
    return created_devices

def get_existing_devices():
    """Get existing devices from the AI service"""
    try:
        response = requests.get(f"{AI_SERVICE_URL}/ai/devices", headers=headers)
        if response.status_code == 200:
            devices_data = response.json()
            return devices_data.get("devices", [])
        else:
            print(f"Failed to fetch existing devices: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching existing devices: {e}")
        return []

def generate_device_schedules(device):
    """Generate realistic schedules for different device types"""
    device_type = device.get('type', '').lower()
    power_rating = device.get('power_rating', 1.0)
    schedules = []
    
    if device_type == 'refrigerator':
        # Refrigerator runs 24/7 with consistent power
        for day in range(7):
            schedules.append({
                "day_of_week": day,
                "start_hour": 0,
                "end_hour": 23,
                "power_consumption": power_rating
            })
    
    elif device_type == 'air_conditioner':
        # AC runs during hot hours, more on weekends
        for day in range(7):
            if day in [0, 6]:  # Weekend
                schedules.extend([
                    {"day_of_week": day, "start_hour": 10, "end_hour": 22, "power_consumption": power_rating},
                ])
            else:  # Weekday
                schedules.extend([
                    {"day_of_week": day, "start_hour": 18, "end_hour": 23, "power_consumption": power_rating},
                    {"day_of_week": day, "start_hour": 6, "end_hour": 8, "power_consumption": power_rating * 0.7},
                ])
    
    elif device_type == 'washing_machine':
        # Washing machine runs few times a week
        schedules.extend([
            {"day_of_week": 1, "start_hour": 8, "end_hour": 10, "power_consumption": power_rating},
            {"day_of_week": 3, "start_hour": 19, "end_hour": 21, "power_consumption": power_rating},
            {"day_of_week": 6, "start_hour": 10, "end_hour": 12, "power_consumption": power_rating},
        ])
    
    elif device_type == 'dishwasher':
        # Dishwasher runs daily after dinner
        for day in range(7):
            schedules.append({
                "day_of_week": day,
                "start_hour": 20,
                "end_hour": 22,
                "power_consumption": power_rating
            })
    
    elif device_type == 'television':
        # TV usage in evenings, more on weekends
        for day in range(7):
            if day in [0, 6]:  # Weekend
                schedules.extend([
                    {"day_of_week": day, "start_hour": 10, "end_hour": 12, "power_consumption": power_rating},
                    {"day_of_week": day, "start_hour": 14, "end_hour": 23, "power_consumption": power_rating},
                ])
            else:
                schedules.append(
                    {"day_of_week": day, "start_hour": 19, "end_hour": 23, "power_consumption": power_rating}
                )
    
    elif device_type == 'lighting':
        # Lights on in morning and evening
        for day in range(7):
            schedules.extend([
                {"day_of_week": day, "start_hour": 6, "end_hour": 8, "power_consumption": power_rating},
                {"day_of_week": day, "start_hour": 18, "end_hour": 23, "power_consumption": power_rating},
            ])
    
    elif device_type == 'computer':
        # Computer usage during work hours on weekdays
        for day in range(1, 6):  # Monday to Friday
            schedules.append({
                "day_of_week": day,
                "start_hour": 9,
                "end_hour": 17,
                "power_consumption": power_rating
            })
    
    else:
        # Default pattern: some usage in morning and evening
        for day in range(7):
            schedules.extend([
                {"day_of_week": day, "start_hour": 7, "end_hour": 9, "power_consumption": power_rating * 0.5},
                {"day_of_week": day, "start_hour": 18, "end_hour": 21, "power_consumption": power_rating},
            ])
    
    return schedules

def set_device_schedules(devices):
    """Set schedules for all devices"""
    print("\nSetting up device schedules...")
    
    for device in devices:
        schedules = generate_device_schedules(device)
        
        if schedules:
            try:
                response = requests.post(
                    f"{DEVICES_URL}/{device['id']}/schedule",
                    json=schedules,
                    headers=headers
                )
                if response.status_code == 200:
                    print(f"✓ Set schedule for {device['name']} ({len(schedules)} time blocks)")
                else:
                    print(f"✗ Failed to set schedule for {device['name']}: {response.status_code}")
            except Exception as e:
                print(f"✗ Error setting schedule for {device['name']}: {e}")
            
            time.sleep(0.1)

def generate_telemetry_data(devices, days=7):
    """Generate telemetry data for specified number of days"""
    print(f"\nGenerating telemetry data for {len(devices)} devices over {days} days...")
    start_date = datetime.utcnow() - timedelta(days=days)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    successful_readings = 0
    failed_readings = 0
    
    # Target daily consumption: 20-40 kWh
    target_daily_kwh = random.uniform(20, 40)
    
    # Calculate scaling factor based on number of devices
    # Targeting ~30 kWh daily total across all devices
    num_devices = len(devices)
    # Estimate average consumption per device per hour (rough baseline)
    estimated_avg_per_device_per_hour = 0.3  # kWh
    estimated_daily_total = num_devices * 24 * estimated_avg_per_device_per_hour
    scaling_factor = 30.0 / estimated_daily_total if estimated_daily_total > 30 else 1.0
    scaling_factor = max(0.1, min(1.0, scaling_factor))  # Keep between 0.1 and 1.0
    
    print(f"Devices: {num_devices}, Estimated daily total: {estimated_daily_total:.1f} kWh, Scaling factor: {scaling_factor:.3f}")
    
    # Generate data for every hour
    for hours in range(days * 24):
        timestamp = start_date + timedelta(hours=hours)
        hour = timestamp.hour
        day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
        
        # Reset daily target at midnight
        if hour == 0:
            target_daily_kwh = random.uniform(20, 40)
        
        for device in devices:
            # Generate realistic consumption based on device type and time
            device_type = device.get('type', '').lower()
            base_power = device.get('power_rating', 1.0)
            
            # UPDATED: More realistic consumption patterns in kWh per hour
            if device_type == 'refrigerator':
                # Refrigerators use about 1-2 kWh per day (0.04-0.08 per hour)
                energy_usage = random.uniform(0.04, 0.08)  # Per hour
                
            elif device_type == 'air_conditioner':
                # AC uses 1-3 kWh per hour when running (reduced from 2.5-4.5)
                if 10 <= hour <= 18:  # Daytime
                    if day_of_week in [5, 6]:  # Weekend
                        energy_usage = random.uniform(1.0, 2.5) if random.random() > 0.3 else 0
                    else:
                        energy_usage = random.uniform(0.8, 1.8) if random.random() > 0.5 else 0
                elif hour >= 18 or hour <= 6:  # Evening/Night
                    energy_usage = random.uniform(0.5, 1.5) if random.random() > 0.4 else 0
                else:
                    energy_usage = 0
                    
            elif device_type == 'washing_machine':
                # Washing machine uses 0.5-1 kWh per hour when running
                if day_of_week in [1, 3, 6] and hour in [8, 9, 19, 20]:
                    energy_usage = random.uniform(0.5, 1.0)
                else:
                    energy_usage = 0
                    
            elif device_type == 'dishwasher':
                # Dishwasher uses 0.8-1.2 kWh per hour when running
                if 20 <= hour <= 21:
                    energy_usage = random.uniform(0.8, 1.2)
                else:
                    energy_usage = 0
                    
            elif device_type == 'television':
                # TV uses 0.1-0.15 kWh per hour
                if day_of_week in [5, 6]:  # Weekend
                    if 10 <= hour <= 23:
                        energy_usage = random.uniform(0.1, 0.15) if random.random() > 0.2 else 0
                    else:
                        energy_usage = 0
                else:  # Weekday
                    if 19 <= hour <= 23:
                        energy_usage = random.uniform(0.1, 0.15)
                    else:
                        energy_usage = 0
                        
            elif device_type == 'lighting':
                # All lights combined use 0.2-0.6 kWh per hour when on (reduced from 0.5-1.5)
                if hour in [6, 7] or 18 <= hour <= 23:
                    usage_factor = random.uniform(0.6, 1.0)
                    energy_usage = random.uniform(0.2, 0.6) * usage_factor
                else:
                    energy_usage = random.uniform(0, 0.05)  # Some lights always on
                    
            elif device_type == 'computer':
                # Computer uses 0.15-0.25 kWh per hour (reduced from 0.2-0.4)
                if day_of_week < 5:  # Weekday
                    if 9 <= hour <= 17:
                        energy_usage = random.uniform(0.15, 0.25)
                    elif 18 <= hour <= 22:
                        energy_usage = random.uniform(0.08, 0.15)
                    else:
                        energy_usage = 0.01  # Standby
                else:
                    energy_usage = random.uniform(0.05, 0.15) if 10 <= hour <= 20 else 0.01
                    
            else:
                # Other appliances (microwave, coffee maker, etc.) - reduced
                if 6 <= hour <= 22:
                    energy_usage = random.uniform(0.05, 0.25)
                else:
                    energy_usage = 0
            
            # Add some realistic variation
            if energy_usage > 0:
                energy_usage *= random.uniform(0.8, 1.2)
            
            # Apply scaling factor to reduce total consumption
            energy_usage *= scaling_factor
            
            # Ensure non-negative values
            energy_usage = max(0, energy_usage)
            
            # Post telemetry
            payload = {
                "device_id": device['id'],
                "energy_usage": round(energy_usage, 3)
            }
            
            try:
                response = requests.post(TELEMETRY_URL, json=payload, headers=headers)
                if response.status_code == 201:
                    if hours % 24 == 0:  # Print once per day per device
                        print(f"✓ {timestamp.strftime('%Y-%m-%d')} - {device['name']}: generating hourly data...")
                    successful_readings += 1
                else:
                    print(f"✗ Failed: {response.status_code} - {device['name']} at {timestamp}")
                    failed_readings += 1
            except Exception as e:
                print(f"✗ Error posting telemetry for {device['name']}: {e}")
                failed_readings += 1
            
            time.sleep(0.01)  # Smaller delay for faster generation
    
    return successful_readings, failed_readings

def test_data_visualization():
    """Test data retrieval through AI service endpoints"""
    print("\n🔍 Testing data visualization endpoints...")
    
    try:
        # Test dashboard data
        response = requests.get(f"{AI_SERVICE_URL}/ai/dashboard", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Dashboard data retrieved successfully")
            print(f"  - Today's total: {data.get('today_total', 0):.2f} kWh")
            print(f"  - Active devices: {len(data.get('current_usage', []))}")
            print(f"  - Monthly cost estimate: ${data.get('estimated_monthly_cost', 0):.2f}")
        else:
            print(f"✗ Failed to get dashboard data: {response.status_code}")
            
        # Test consumption timeline
        response = requests.get(f"{AI_SERVICE_URL}/ai/consumption-timeline?view=week", headers=headers)
        if response.status_code == 200:
            data = response.json()
            timeline_data = data.get('data', [])
            print(f"✓ Consumption timeline retrieved: {len(timeline_data)} data points")
        else:
            print(f"✗ Failed to get timeline data: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error testing visualization: {e}")

def main():
    print("Smart Home Energy Monitoring - Weekly Data Simulator")
    print("=" * 50)
    
    # Check if we have an auth token
    if not AUTH_TOKEN or AUTH_TOKEN == "your-auth-token-here":
        print("❌ No auth token found!")
        print("Please set AUTH_TOKEN environment variable:")
        print("export AUTH_TOKEN='your-jwt-token-here'")
        print("\nTo get a token, run:")
        print("curl -X POST http://localhost:8000/auth/login \\")
        print("  -H \"Content-Type: application/x-www-form-urlencoded\" \\")
        print("  -d \"username=your-email@example.com&password=your-password\"")
        return
    
    # Step 1: Check for existing devices
    print("Step 1: Checking for existing devices...")
    existing_devices = get_existing_devices()
    
    if existing_devices:
        print(f"Found {len(existing_devices)} existing devices:")
        for device in existing_devices:
            print(f"  - {device['name']} ({device['type']})")
        
        use_existing = input("\nUse existing devices? (y/n): ").lower().strip()
        if use_existing == 'y':
            devices = existing_devices
        else:
            print("\nStep 2: Creating new devices...")
            devices = create_devices()
    else:
        print("No existing devices found.")
        print("\nStep 2: Creating new devices...")
        devices = create_devices()
    
    if not devices:
        print("❌ No devices available for simulation!")
        return
    
    print(f"\n✓ Ready to simulate with {len(devices)} devices")
    
    # Step 3: Set up device schedules
    set_device_schedules(devices)
    
    # Step 4: Generate telemetry data for past 15 days
    print("\nStep 4: Generating 15 days of telemetry data...")
    successful, failed = generate_telemetry_data(devices, days=15)
    
    # Summary
    print("\n" + "=" * 50)
    print("Simulation Complete!")
    print(f"✓ Successful readings: {successful}")
    print(f"✗ Failed readings: {failed}")
    print(f"📊 Total devices: {len(devices)}")
    print(f"📅 Time period: 15 days")
    print(f"⏰ Data points per device: ~360 (hourly readings)")
    print("=" * 50)
    
    # Test data visualization
    test_data_visualization()
    
    print("\n✅ Your Smart Home Energy Monitor now has realistic data!")
    print("🌐 Open http://localhost:3000 to view your dashboard")

if __name__ == "__main__":
    main()