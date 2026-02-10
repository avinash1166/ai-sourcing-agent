#!/usr/bin/env python3
"""
AI Sourcing Agent - Main Module
OEM/ODM Discovery with Multi-Layer Validation
No Hallucinations - Fact-Based Only
"""

import os
import json
import time
import sqlite3
from datetime import datetime
from typing import TypedDict, List, Dict, Any
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph, END

from config import *
from validators import MultiLayerValidator, ValidationResult

# ==================== STATE DEFINITION ====================
class AgentState(TypedDict):
    task: str  # Current task
    search_query: str  # Current search keywords
    raw_html: str  # Scraped webpage content
    extracted_data: Dict[str, Any]  # Extracted vendor info
    validation_results: List[tuple]  # Validation layer results
    validated_data: Dict[str, Any]  # Final validated output
    historical_vendors: List[Dict[str, Any]]  # Past vendors for consistency check
    retry_count: int  # Retry counter
    error_log: str  # Error messages
    status: str  # Current status

# ==================== DATABASE SETUP ====================
def setup_database():
    """Create SQLite database for vendor tracking"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    conn = sqlite3.connect(VENDORS_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_name TEXT NOT NULL,
            url TEXT,
            platform TEXT,
            moq INTEGER,
            price_per_unit REAL,
            customizable BOOLEAN,
            os TEXT,
            screen_size TEXT,
            touchscreen BOOLEAN,
            camera_front BOOLEAN,
            wall_mount BOOLEAN,
            has_battery BOOLEAN,
            product_type TEXT,
            score INTEGER,
            status TEXT,
            raw_data TEXT,
            contacted BOOLEAN DEFAULT 0,
            contact_date TEXT,
            reply_received BOOLEAN DEFAULT 0,
            reply_date TEXT,
            reply_content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            -- New fields for learning and conversation features
            discovered_date TEXT,
            contact_email TEXT,
            product_description TEXT,
            keywords_used TEXT,
            validation_status TEXT,
            rejection_reason TEXT,
            email_sent_count INTEGER DEFAULT 0,
            last_email_date TEXT,
            email_response TEXT,
            price_quoted REAL,
            moq_quoted INTEGER,
            customization_confirmed TEXT,
            response_time_hours REAL,
            last_response_date TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS validation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            validation_passed BOOLEAN,
            layer_results TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized")

# ==================== OLLAMA LLM SETUP ====================
print(f"Initializing Ollama with model: {OLLAMA_MODEL}")
llm = OllamaLLM(
    model=OLLAMA_MODEL,
    temperature=OLLAMA_TEMPERATURE,
    top_p=OLLAMA_TOP_P
)

# ==================== VALIDATOR INSTANCE ====================
validator = MultiLayerValidator()

# ==================== SCHEMA DEFINITIONS ====================
VENDOR_SCHEMA = {
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
    "wall_mount": (bool, type(None)),  # NEW: wall mounted or portable
    "has_battery": (bool, type(None)),  # NEW: critical - must be False
    "product_type": (str, type(None)),  # NEW: identify if tablet vs display
    "description": str,
}

# ==================== NODE 1: EXTRACTION ====================
def extract_vendor_info(state: AgentState) -> AgentState:
    """
    Extract vendor information from raw HTML/text
    Using LLM with strict prompting to minimize hallucinations
    """
    print("\n>>> NODE 1: Extracting vendor information...")
    
    raw_text = state['raw_html'][:5000]  # Limit to 5000 chars to save RAM
    
    if not raw_text or len(raw_text) < 50:
        return {
            **state,
            "extracted_data": {},
            "error_log": "No content to extract from",
            "status": "extraction_failed"
        }
    
    extraction_prompt = f"""Extract product information from this text. Return ONLY valid JSON.

CRITICAL RULES:
1. If info is missing, use null (not "Unknown")
2. Do NOT use quotes inside string values
3. Keep descriptions simple and short
4. Return ONLY the JSON object - no markdown, no backticks, no explanations
5. Product must be wall-mounted display (not portable tablet)

Text to analyze:
{raw_text[:3000]}

Return this exact JSON structure (replace values with extracted data):
{{"vendor_name":"Company Name","url":null,"platform":"made-in-china","moq":100,"price_per_unit":125.5,"customizable":true,"os":"Android","screen_size":"15.6 inch","touchscreen":true,"camera_front":false,"wall_mount":true,"has_battery":false,"product_type":"smart screen","description":"Simple description no quotes"}}

Output ONLY the JSON. Start with {{ end with }}. No other text.

JSON:"""

    try:
        response = llm.invoke(extraction_prompt)
        
        # AGGRESSIVE JSON CLEANING
        response = response.strip()
        
        # Remove markdown code blocks
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        # Remove any text before first { and after last }
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        if start_idx != -1 and end_idx != -1:
            response = response[start_idx:end_idx+1]
        
        # Fix common JSON issues
        # Replace "Unknown" with null
        import re
        response = re.sub(r':\s*"Unknown"', ': null', response)
        response = re.sub(r':\s*"unknown"', ': null', response)
        
        # Remove trailing commas before } or ]
        response = re.sub(r',(\s*[}\]])', r'\1', response)
        
        # Parse JSON
        extracted = json.loads(response)
        
        # TYPE COERCION: Fix common LLM mistakes
        # Fix 1: Convert int prices to float
        if 'price_per_unit' in extracted and isinstance(extracted['price_per_unit'], int):
            extracted['price_per_unit'] = float(extracted['price_per_unit'])
        
        # Fix 2: Convert list OS to string (join with commas)
        if 'os' in extracted and isinstance(extracted['os'], list):
            extracted['os'] = ', '.join(str(x) for x in extracted['os'])
        
        # Fix 3: Convert float MOQ to int
        if 'moq' in extracted and isinstance(extracted['moq'], float):
            extracted['moq'] = int(extracted['moq'])
        
        # Fix 4: Ensure platform is lowercase
        if 'platform' in extracted and extracted['platform']:
            extracted['platform'] = str(extracted['platform']).lower()
        
        # Replace None values (keep them as None, don't convert to "Unknown")
        # This is already handled by the prompt now
        
        print(f"✓ Extracted data for: {extracted.get('vendor_name', 'Unknown')}")
        
        return {
            **state,
            "extracted_data": extracted,
            "status": "extracted"
        }
    
    except json.JSONDecodeError as e:
        print(f"✗ JSON parsing error: {e}")
        print(f"  Raw response (first 300 chars): {response[:300] if 'response' in locals() else 'N/A'}")
        
        # FALLBACK: Use rule-based extraction from raw text
        print("  → Using fallback rule-based extraction...")
        try:
            import re
            
            # Extract basic info from raw text using regex
            simple_data = {
                "vendor_name": "Unknown Vendor",
                "url": None,
                "platform": "made-in-china",
                "moq": None,
                "price_per_unit": None,
                "customizable": None,
                "os": None,
                "screen_size": None,
                "touchscreen": None,
                "camera_front": None,
                "wall_mount": None,
                "has_battery": None,
                "product_type": None,
                "description": raw_text[:200].replace('\n', ' ').replace('"', '').replace("'", '')
            }
            
            # Extract vendor name from raw text (first line or company pattern)
            lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
            if lines:
                # Try first non-empty line
                first_line = lines[0]
                if len(first_line) > 5 and len(first_line) < 150:
                    simple_data['vendor_name'] = first_line[:100]
            
            # Look for company name patterns
            name_match = re.search(r'([\w\s]+(?:Co\.|Ltd\.|Inc\.|Technology|Electronics|Display|Screen)[\w\s,\.]*)', raw_text[:500])
            if name_match:
                potential_name = name_match.group(1).strip()
                if len(potential_name) > 5 and len(potential_name) < 100:
                    simple_data['vendor_name'] = potential_name
            
            # Extract price (various formats)
            price_patterns = [
                r'US?\$\s*(\d+(?:\.\d{1,2})?)',  # $125 or US$125.50
                r'(\d+(?:\.\d{1,2})?)\s*USD',     # 125 USD
                r'Price[:\s]+(\d+(?:\.\d{1,2})?)', # Price: 125
            ]
            for pattern in price_patterns:
                price_match = re.search(pattern, raw_text, re.IGNORECASE)
                if price_match:
                    simple_data['price_per_unit'] = float(price_match.group(1))
                    break
            
            # Extract MOQ
            moq_patterns = [
                r'MOQ[:\s]*(\d+)',
                r'Minimum[:\s]+(\d+)',
                r'(\d+)\s+[Pp]ieces?\s+\(MOQ\)',
            ]
            for pattern in moq_patterns:
                moq_match = re.search(pattern, raw_text, re.IGNORECASE)
                if moq_match:
                    simple_data['moq'] = int(moq_match.group(1))
                    break
            
            # Detect Android
            if 'android' in raw_text.lower():
                simple_data['os'] = 'Android'
                # Try to extract version
                android_ver = re.search(r'Android\s+(\d+(?:\.\d+)?)', raw_text, re.IGNORECASE)
                if android_ver:
                    simple_data['os'] = f"Android {android_ver.group(1)}"
            
            # Detect screen size
            size_match = re.search(r'(\d+\.?\d*)\s*(?:inch|"|′)', raw_text, re.IGNORECASE)
            if size_match:
                simple_data['screen_size'] = f"{size_match.group(1)} inch"
            
            # Detect touchscreen
            if any(word in raw_text.lower() for word in ['touch screen', 'touchscreen', 'touch panel', 'capacitive']):
                simple_data['touchscreen'] = True
            
            # Detect wall mount (CRITICAL)
            if any(word in raw_text.lower() for word in ['wall mount', 'wall-mount', 'vesa', 'bracket']):
                simple_data['wall_mount'] = True
            elif any(word in raw_text.lower() for word in ['portable', 'handheld', 'tablet pc']):
                simple_data['wall_mount'] = False
            
            # Detect battery (CRITICAL - we DON'T want battery)
            if any(word in raw_text.lower() for word in ['battery', 'rechargeable', 'built-in battery']):
                simple_data['has_battery'] = True
            elif any(word in raw_text.lower() for word in ['dc adapter', '12v', 'wall powered', 'ac adapter']):
                simple_data['has_battery'] = False
            
            # Detect product type
            if any(word in raw_text.lower() for word in ['digital signage', 'smart display', 'advertising display', 'menu board']):
                simple_data['product_type'] = 'smart screen'
            elif 'tablet pc' in raw_text.lower() or 'portable tablet' in raw_text.lower():
                simple_data['product_type'] = 'tablet'
            
            # Detect customizable
            if any(word in raw_text.lower() for word in ['customizable', 'oem', 'odm', 'custom']):
                simple_data['customizable'] = True
            
            print(f"  ✓ Fallback extraction successful: {simple_data['vendor_name']}")
            
            return {
                **state,
                "extracted_data": simple_data,
                "status": "extracted"
            }
            
        except Exception as fallback_error:
            print(f"  ✗ Fallback extraction also failed: {fallback_error}")
            return {
                **state,
                "extracted_data": {},
                "error_log": f"Both JSON and fallback extraction failed: {str(e)}",
                "status": "extraction_failed",
                "retry_count": state['retry_count'] + 1
            }
    
    except Exception as e:
        print(f"✗ Extraction error: {e}")
        return {
            **state,
            "extracted_data": {},
            "error_log": f"Extraction error: {str(e)}",
            "status": "extraction_failed",
            "retry_count": state['retry_count'] + 1
        }

# ==================== NODE 2: VALIDATION ====================
def validate_extracted_data(state: AgentState) -> AgentState:
    """
    Run all 5 validation layers
    Only pass data that meets ALL criteria
    """
    print("\n>>> NODE 2: Validating extracted data...")
    
    extracted = state['extracted_data']
    
    if not extracted:
        return {
            **state,
            "validation_results": [],
            "validated_data": {},
            "status": "validation_skipped"
        }
    
    # Run all validation layers (use original schema with tuples)
    passed, results = validator.validate_all(
        data=extracted,
        source_text=state['raw_html'],
        expected_schema=VENDOR_SCHEMA,
        requirements={
            'moq_max_acceptable': PRODUCT_SPECS['moq_max_acceptable'],
            'target_cogs_max': PRODUCT_SPECS['target_cogs_max'],
            'red_flags': RED_FLAGS
        },
        historical_data=state.get('historical_vendors', [])
    )
    
    # Print results
    print("\n=== VALIDATION RESULTS ===")
    for layer_name, result in results:
        status_icon = "✓" if result.passed else "✗"
        print(f"{status_icon} {layer_name}: {result.reason} (confidence: {result.confidence:.2f})")
    
    if passed:
        print("\n✓ ALL VALIDATION LAYERS PASSED - Data is factual and reliable")
        return {
            **state,
            "validation_results": results,
            "validated_data": extracted,
            "status": "validated"
        }
    else:
        print("\n✗ VALIDATION FAILED - Data rejected (potential hallucination or constraint violation)")
        return {
            **state,
            "validation_results": results,
            "validated_data": {},
            "status": "validation_failed"
        }

# ==================== NODE 3: SCORING ====================
def score_vendor(state: AgentState) -> AgentState:
    """
    Calculate vendor score based on validated data
    UPDATED: Focus on smart screens, not tablets
    """
    print("\n>>> NODE 3: Scoring vendor...")
    
    validated = state['validated_data']
    
    if not validated:
        return {
            **state,
            "status": "scoring_skipped"
        }
    
    score = 0
    max_score = sum(SCORING_WEIGHTS.values())
    
    # Android OS - CRITICAL
    if validated.get('os') and 'android' in str(validated['os']).lower():
        score += SCORING_WEIGHTS['android_os']
    
    # Wall mount - CRITICAL (not portable tablet)
    if validated.get('wall_mount') is True:
        score += SCORING_WEIGHTS['wall_mount']
    
    # No battery - CRITICAL (wall-powered only)
    if validated.get('has_battery') is False:
        score += SCORING_WEIGHTS['no_battery']
    # Penalty if it HAS a battery (portable device)
    elif validated.get('has_battery') is True:
        score -= 20  # Major penalty for battery-powered devices
    
    # Correct size (15.6 inch)
    screen_size = str(validated.get('screen_size', ''))
    if '15.6' in screen_size or '15' in screen_size:
        score += SCORING_WEIGHTS['correct_size']
    
    # Touchscreen
    if validated.get('touchscreen') is True:
        score += SCORING_WEIGHTS['touchscreen']
    
    # Price in range ($70-90)
    price = validated.get('price_per_unit')
    if price:
        try:
            price_num = float(str(price).replace('$', '').replace(',', ''))
            if PRODUCT_SPECS['target_cogs_min'] <= price_num <= PRODUCT_SPECS['target_cogs_max']:
                score += SCORING_WEIGHTS['price_in_range']
            elif price_num <= PRODUCT_SPECS['target_cogs_max'] * 2:  # Within 2x range
                score += SCORING_WEIGHTS['price_in_range'] // 2  # Half points
        except:
            pass
    
    # MOQ acceptable
    moq = validated.get('moq')
    if moq:
        try:
            moq_num = int(str(moq).replace(',', ''))
            if moq_num <= PRODUCT_SPECS['moq_max_acceptable']:
                score += SCORING_WEIGHTS['moq_acceptable']
        except:
            pass
    
    # Customizable
    if validated.get('customizable') is True:
        score += SCORING_WEIGHTS['customizable']
    
    # IPS Panel (bonus if mentioned)
    desc = str(validated.get('description', '')).lower()
    if 'ips' in desc:
        score += SCORING_WEIGHTS.get('ips_panel', 0)
    
    # REJECT if clearly a portable tablet
    product_type = str(validated.get('product_type', '')).lower()
    if 'tablet' in product_type and 'wall' not in desc and 'mount' not in desc:
        score -= 30  # Major penalty for tablets
    
    # Ensure score is not negative
    score = max(0, score)
    
    # Calculate percentage
    score_percentage = int((score / max_score) * 100)
    
    print(f"✓ Vendor score: {score_percentage}/100 ({score}/{max_score} points)")
    
    # Add score to validated data
    validated['score'] = score_percentage
    
    return {
        **state,
        "validated_data": validated,
        "status": "scored"
    }

# ==================== NODE 4: SAVE TO DATABASE ====================
def save_to_database(state: AgentState) -> AgentState:
    """
    Save validated vendor to database
    """
    print("\n>>> NODE 4: Saving to database...")
    
    validated = state['validated_data']
    
    # LOWERED: Accept vendors with score >= 30 (was 50)
    # Rationale: Let email negotiation filter, not strict thresholds
    if not validated or validated.get('score', 0) < 30:
        print("✗ Skipping save - no validated data or score too low")
        return {
            **state,
            "status": "save_skipped"
        }
    
    try:
        conn = sqlite3.connect(VENDORS_DB)
        cursor = conn.cursor()
        
        # Get current date for discovered_date
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT INTO vendors (
                vendor_name, url, platform, moq, price_per_unit,
                customizable, os, screen_size, touchscreen,
                camera_front, wall_mount, has_battery, product_type,
                score, status, raw_data,
                discovered_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            validated.get('vendor_name'),
            validated.get('url'),
            validated.get('platform'),
            validated.get('moq'),
            validated.get('price_per_unit'),
            validated.get('customizable'),
            validated.get('os'),
            validated.get('screen_size'),
            validated.get('touchscreen'),
            validated.get('camera_front'),
            validated.get('wall_mount'),
            validated.get('has_battery'),
            validated.get('product_type'),
            validated.get('score'),
            'new',
            json.dumps(validated),
            today  # ADDED: Set discovered_date to today
        ))
        
        vendor_id = cursor.lastrowid
        
        # Save validation log
        cursor.execute('''
            INSERT INTO validation_logs (vendor_id, validation_passed, layer_results)
            VALUES (?, ?, ?)
        ''', (
            vendor_id,
            True,
            json.dumps([(name, {"passed": r.passed, "reason": r.reason, "confidence": r.confidence}) 
                       for name, r in state['validation_results']])
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Vendor saved to database (ID: {vendor_id})")
        
        return {
            **state,
            "status": "saved"
        }
    
    except Exception as e:
        print(f"✗ Database error: {e}")
        return {
            **state,
            "error_log": f"Database error: {str(e)}",
            "status": "save_failed"
        }

# ==================== ROUTING LOGIC ====================
def should_retry(state: AgentState) -> str:
    """Decide if we should retry extraction"""
    if state['status'] == 'extraction_failed' and state['retry_count'] < 2:
        print("→ Retrying extraction...")
        return "extract"
    elif state['status'] in ['validated', 'scored', 'saved']:
        return "end"
    else:
        if state['status'] == 'extraction_failed':
            print("→ Extraction failed after retries, skipping vendor")
        else:
            print("→ Moving to end (no retry)")
        return "end"

# ==================== BUILD THE GRAPH ====================
def build_agent():
    """Build the LangGraph agent with validation layers"""
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("extract", extract_vendor_info)
    workflow.add_node("validate", validate_extracted_data)
    workflow.add_node("score", score_vendor)
    workflow.add_node("save", save_to_database)
    
    # Set entry point
    workflow.set_entry_point("extract")
    
    # Add edges
    workflow.add_conditional_edges(
        "extract",
        should_retry,
        {
            "extract": "extract",
            "end": "validate"
        }
    )
    workflow.add_edge("validate", "score")
    workflow.add_edge("score", "save")
    workflow.add_edge("save", END)
    
    return workflow.compile()

# ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    print("=" * 60)
    print("AI SOURCING AGENT - OEM/ODM Discovery System")
    print("Multi-Layer Validation - No Hallucinations")
    print("=" * 60)
    
    # Setup
    setup_database()
    
    # Build agent
    agent = build_agent()
    
    # Test with sample vendor data
    sample_vendor_text = """
    Company: Shenzhen TechDisplay Co., Ltd.
    Product: 15.6 inch Android Tablet Display
    
    Specifications:
    - Display: 15.6" IPS LCD, 1920x1080 resolution
    - OS: Android 11 (customizable)
    - Touch: 10-point capacitive touchscreen
    - Camera: 2MP front camera
    - Connectivity: WiFi, 4G LTE with eSIM support
    - Audio: Dual speakers, dual microphones
    - Power: DC 12V (no battery)
    
    Price: $135 per unit (FOB Shenzhen)
    MOQ: 100 pieces
    Customization: Yes, we support ODM services including casing modification
    Lead time: 25-30 days
    
    Contact: sales@techdisplay.com
    """
    
    print("\n" + "=" * 60)
    print("TESTING WITH SAMPLE VENDOR")
    print("=" * 60)
    
    initial_state = {
        "task": "extract_and_validate_vendor",
        "search_query": "15.6 inch Android tablet",
        "raw_html": sample_vendor_text,
        "extracted_data": {},
        "validation_results": [],
        "validated_data": {},
        "historical_vendors": [],
        "retry_count": 0,
        "error_log": "",
        "status": "initialized"
    }
    
    # Run agent
    final_state = agent.invoke(initial_state)
    
    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Status: {final_state['status']}")
    if final_state['validated_data']:
        print(f"\n✓ VALIDATED VENDOR:")
        print(json.dumps(final_state['validated_data'], indent=2))
    else:
        print("\n✗ No validated data produced")
        if final_state['error_log']:
            print(f"Error: {final_state['error_log']}")
    
    # Print validation report
    print("\n" + validator.get_validation_report())
