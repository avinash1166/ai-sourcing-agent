#!/usr/bin/env python3
"""Quick test of the validation system"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validators import MultiLayerValidator

print("="*60)
print("TESTING VALIDATION SYSTEM")
print("="*60)

validator = MultiLayerValidator()

# Test data
test_vendor = {
    "vendor_name": "Shenzhen TechDisplay Co., Ltd.",
    "url": "Unknown",
    "platform": "Unknown",
    "moq": "100",
    "price_per_unit": "$135",
    "customizable": "Yes",
    "os": "Android 11",
    "screen_size": "15.6 inch",
    "touchscreen": "capacitive touchscreen",
    "camera_front": "2MP front camera",
    "esim_support": "eSIM",
    "description": "15.6 inch Android Tablet Display with IPS LCD 1920x1080 touchscreen"
}

source_text = """
Company: Shenzhen TechDisplay Co., Ltd.
Product: 15.6 inch Android Tablet Display
Display: 15.6" IPS LCD, 1920x1080
OS: Android 11 (customizable)
Touch: 10-point capacitive touchscreen
Camera: 2MP front camera
Connectivity: WiFi, 4G LTE with eSIM
Price: $135 per unit
MOQ: 100 pieces
Customization: Yes, ODM services available
"""

schema = {
    "vendor_name": str,
    "url": str,
    "platform": str,
    "moq": (int, str, type(None)),
    "price_per_unit": (float, str, type(None)),
    "customizable": (bool, type(None)),
    "os": (str, type(None)),
    "screen_size": (str, type(None)),
    "touchscreen": (bool, type(None)),
    "camera_front": (bool, type(None)),
    "esim_support": (bool, type(None)),
    "description": str,
}

requirements = {
    'moq_max_acceptable': 500,
    'target_cogs_max': 150,
    'red_flags': ["loop video player only", "no customization"]
}

print("\nRunning 5-layer validation...")
print("-"*60)

passed, results = validator.validate_all(
    data=test_vendor,
    source_text=source_text,
    expected_schema=schema,
    requirements=requirements,
    historical_data=[]
)

for layer_name, result in results:
    status = "✓ PASS" if result.passed else "✗ FAIL"
    print(f"{status} | {layer_name}")
    print(f"       Reason: {result.reason}")
    print(f"       Confidence: {result.confidence:.2f}")
    print()

print("="*60)
if passed:
    print("RESULT: ✓ ALL VALIDATIONS PASSED")
    print("This vendor data is FACT-BASED and RELIABLE")
else:
    print("RESULT: ✗ VALIDATION FAILED")
    print("This vendor data was REJECTED")
print("="*60)
