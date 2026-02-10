# Configuration for AI Sourcing Agent
# All settings for the OEM/ODM Discovery System

# ==================== PRODUCT SPECIFICATIONS ====================
# CRITICAL: We need SMART SCREENS / DIGITAL SIGNAGE, not tablets!
PRODUCT_SPECS = {
    "product_type": "Smart Screen / Digital Signage / Wall Mount Display",  # NOT TABLET!
    "display": "15.6 inch IPS touchscreen",
    "resolution": "1920x1080 (1080p)",
    "os": "Android (AOSP preferred, Android 8.1/9/11)",
    "battery": "NO BATTERY - Wall powered only (12V DC adapter)",  # CRITICAL
    "camera": "Front camera (2MP minimum, optional)",
    "audio": "Speakers with basic audio, microphones (optional)",
    "connectivity": "WiFi required, 4G LTE optional, RJ45 ethernet",
    "app_support": "Must run cloud-hosted interactive video app",
    "customization": "Removable/modifiable casing, custom firmware",
    "mounting": "Wall mount (VESA mount preferred)",
    "moq_pilot": 100,
    "moq_max_acceptable": 500,
    "target_cogs_min": 70,  # USD - targeting below market
    "target_cogs_max": 90,  # USD - Need cheaper than $95-160 range
    "target_cogs_inr_min": 6000,
    "target_cogs_inr_max": 8000,
    "reference_vendor": "HYY Technology (we-signage.en.made-in-china.com)",
    "reference_price": "95-160 USD (TOO HIGH, need 15-30% discount)",
    "reference_product": "15.6 Inch Wall Mount Android Touch Screen Smart Home Display",
}

# ==================== SEARCH KEYWORDS ====================
# CRITICAL: We need SMART SCREENS / DIGITAL SIGNAGE, NOT tablets!
SEARCH_KEYWORDS = [
    "15.6 inch wall mount Android touch screen smart display",
    "Android digital signage 15.6 inch wall mount",
    "smart home display 15.6 Android touchscreen",
    "wall mounted Android panel 15 inch touch screen",
    "Android advertising display 15.6 touch screen",
    "interactive wall mount LCD display Android",
    "smart screen 15.6 inch Android IPS panel",
    "digital menu board 15.6 Android touch",
    "wall mount smart display Android 1080p",
    "Android signage display 15.6 capacitive touch"
]

# ==================== SEARCH PLATFORMS ====================
SEARCH_PLATFORMS = [
    "https://www.alibaba.com",
    "https://www.made-in-china.com",
    "https://www.globalsources.com"
]

# ==================== RED FLAGS (Auto-reject) ====================
# These indicate the vendor is NOT what we want
RED_FLAGS = [
    "loop video player only",  # Video players, not smart displays
    "no customization",
    "MOQ > 1000",
    "battery required",  # CRITICAL: We need wall-powered displays
    "Windows only",
    "no Android support",
    "tablet pc",  # We want displays, not tablets!
    "portable tablet",  # Not portable - wall mounted!
    "gaming tablet",
    "education tablet",
    "battery operated",
    "rechargeable battery",
    "built-in battery"
]

# ==================== SCORING CRITERIA ====================
# Weighted scoring for SMART SCREENS / DIGITAL SIGNAGE
SCORING_WEIGHTS = {
    "android_os": 25,           # CRITICAL - must be Android
    "wall_mount": 20,           # CRITICAL - wall mounted, not portable
    "no_battery": 15,           # CRITICAL - powered by adapter, not battery
    "correct_size": 15,         # 15.6 inch is ideal
    "touchscreen": 10,          # Nice to have
    "price_in_range": 20,       # Very important (under $90)
    "moq_acceptable": 10,       # MOQ <= 500
    "customizable": 10,         # Can modify casing/firmware
    "ips_panel": 5,             # Better viewing angles
}

# ==================== EMAIL TEMPLATE ====================
EMAIL_TEMPLATE = """Subject: Inquiry for 15.6" Wall Mount Android Smart Display - Pilot Order

Hi,

We are a startup building a smart AI frame product. We're looking for a **15.6" wall-mounted Android smart display / digital signage** with the following specifications:

**Required Specifications:**
- **Product Type:** Wall-mounted smart screen / digital signage (NOT portable tablet)
- **Display:** 15.6" IPS touchscreen panel, 1920x1080 resolution
- **OS:** Android (Android 8.1/9/11 preferred)
- **Power:** DC adapter powered (12V) - **NO battery** (critical)
- **Touchscreen:** Capacitive touch (10-point preferred)
- **Connectivity:** WiFi required, RJ45 ethernet preferred, 4G/LTE optional
- **Mounting:** Wall mount with VESA bracket
- **Camera:** 2MP front camera (optional)
- **Audio:** Basic speakers and microphones (optional)

**Key Requirements:**
✓ Must be wall-powered (no battery)
✓ Can run cloud-hosted Android applications
✓ Customization capability (casing modification, custom firmware)
✓ Long-term reliability (24/7 operation capable)

**Order Details:**
- Pilot order: 100-300 units
- Target price: $70-90/unit FOB (we've seen $95-160 in market)
- Future volume: 1000+ units if pilot successful

Could you please provide:
1. Complete product specifications
2. Unit price for 100, 200, 300 units
3. MOQ (Minimum Order Quantity)
4. Customization options (casing, firmware, branding)
5. Lead time and shipping options
6. Product photos/catalog

We're ready to move quickly for the right partner.

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
