# Configuration for AI Sourcing Agent
# All settings for the OEM/ODM Discovery System

# ==================== PRODUCT SPECIFICATIONS ====================
PRODUCT_SPECS = {
    "display": "15.6 inch IPS touchscreen",
    "resolution": "1920x1080 (1080p)",
    "os": "Android (AOSP preferred)",
    "battery": "No battery required",
    "camera": "Front camera (2MP minimum)",
    "audio": "Speakers with basic noise filtering, microphones",
    "connectivity": "eSIM support, 4G LTE, WiFi",
    "app_support": "Must run cloud-hosted interactive video app",
    "customization": "Removable/modifiable casing",
    "moq_pilot": 100,
    "moq_max_acceptable": 500,
    "target_cogs_min": 120,  # USD
    "target_cogs_max": 150,  # USD
    "target_cogs_inr_min": 11000,
    "target_cogs_inr_max": 15000,
}

# ==================== SEARCH KEYWORDS ====================
SEARCH_KEYWORDS = [
    "15.6 inch Android tablet",
    "Android digital signage 15 inch touch",
    "ODM Android touch panel with camera",
    "15.6 Android touchscreen display",
    "Android tablet OEM customization",
    "Android kiosk tablet 15.6",
    "industrial Android tablet 15 inch"
]

# ==================== SEARCH PLATFORMS ====================
SEARCH_PLATFORMS = [
    "https://www.alibaba.com",
    "https://www.made-in-china.com",
    "https://www.globalsources.com"
]

# ==================== RED FLAGS (Auto-reject) ====================
RED_FLAGS = [
    "loop video player only",
    "no customization",
    "MOQ > 1000",
    "battery required",
    "Windows only",
    "no Android support"
]

# ==================== SCORING CRITERIA ====================
SCORING_WEIGHTS = {
    "android_os": 20,
    "touchscreen": 15,
    "correct_size": 15,
    "front_camera": 10,
    "esim_lte": 15,
    "moq_acceptable": 15,
    "price_in_range": 20,
    "customizable": 10
}

# ==================== EMAIL TEMPLATE ====================
EMAIL_TEMPLATE = """Subject: Inquiry for 15.6" Android Touchscreen Device - Pilot Order

Hi,

We are a startup building a smart AI frame product based on Android. We're looking for a 15.6″ touchscreen device with the following specifications:

- Android OS (AOSP preferred)
- 15.6" IPS touchscreen (1080p)
- Front camera (2MP or better)
- WiFi and 4G LTE with eSIM support
- Speakers and microphones
- No battery required (wall-powered)
- Ability to run cloud-hosted applications

We are particularly interested in whether slight customization is possible, such as:
- Removing back camera (if present)
- Modifying or removing casing
- Custom firmware/app pre-installation

Could you please share:
1. Complete product specifications
2. MOQ (Minimum Order Quantity)
3. Unit price for 100-300 units
4. Customization capabilities
5. Lead time and shipping options

We are evaluating suppliers for a pilot run of 100-300 units with potential for scaling.

Looking forward to your response.

Best regards,
Avinash
Frame AI Team
"""

# ==================== OLLAMA SETTINGS ====================
OLLAMA_MODEL = "qwen2.5-coder:3b"  # Lightweight model for 8GB RAM (using coder variant)
OLLAMA_TEMPERATURE = 0.1  # Low temperature for factual outputs
OLLAMA_TOP_P = 0.9

# ==================== FILE PATHS ====================
import os
# Use script directory instead of current working directory for portability
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
VENDORS_DB = os.path.join(DATA_DIR, "vendors.db")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")

# ==================== VALIDATION LAYERS ====================
VALIDATION_LAYERS = {
    "layer1_format_check": True,  # Check if output matches expected format
    "layer2_factual_check": True,  # Verify extracted data against source
    "layer3_constraint_check": True,  # Check against product requirements
    "layer4_consistency_check": True,  # Cross-validate with previous data
    "layer5_human_review": False  # Flag for human review (for critical decisions)
}

# ==================== RATE LIMITS ====================
RATE_LIMITS = {
    "search_delay_seconds": 5,  # Delay between searches to avoid blocking
    "email_daily_limit": 50,  # Max emails per day
    "max_vendors_per_day": 30  # Max new vendors to scrape per day
}
