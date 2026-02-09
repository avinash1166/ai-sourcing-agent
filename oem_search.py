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
            esim_support BOOLEAN,
            score INTEGER,
            status TEXT,
            raw_data TEXT,
            contacted BOOLEAN DEFAULT 0,
            contact_date TEXT,
            reply_received BOOLEAN DEFAULT 0,
            reply_date TEXT,
            reply_content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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
    "esim_support": (bool, type(None)),
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
    
    extraction_prompt = f"""You are a data extraction bot. Extract ONLY factual information from the text below.

RULES:
1. If information is NOT in the text, return "Unknown" or null
2. DO NOT guess or infer
3. DO NOT make up information
4. Extract exact numbers and text as they appear
5. Return valid JSON only

Text to analyze:
{raw_text}

Extract these fields in JSON format:
{{
    "vendor_name": "exact company name from text or Unknown",
    "url": "product URL if mentioned or Unknown",
    "platform": "alibaba or made-in-china or globalsources or other",
    "moq": "minimum order quantity as number or Unknown",
    "price_per_unit": "price per unit in USD or Unknown",
    "customizable": true/false/null,
    "os": "operating system mentioned or Unknown",
    "screen_size": "screen size mentioned or Unknown",
    "touchscreen": true/false/null,
    "camera_front": true/false/null,
    "esim_support": true/false/null,
    "description": "brief product description from text"
}}

JSON output:"""

    try:
        response = llm.invoke(extraction_prompt)
        
        # Clean response - remove markdown formatting if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        # Parse JSON
        extracted = json.loads(response)
        
        # Replace "Unknown" strings with None for consistency
        for key, value in extracted.items():
            if value == "Unknown" or value == "unknown":
                extracted[key] = None
        
        print(f"✓ Extracted data for: {extracted.get('vendor_name', 'Unknown')}")
        
        return {
            **state,
            "extracted_data": extracted,
            "status": "extracted"
        }
    
    except json.JSONDecodeError as e:
        print(f"✗ JSON parsing error: {e}")
        return {
            **state,
            "extracted_data": {},
            "error_log": f"JSON parsing failed: {str(e)}",
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
    Only uses VALIDATED facts, no assumptions
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
    
    # Android OS
    if validated.get('os') and 'android' in str(validated['os']).lower():
        score += SCORING_WEIGHTS['android_os']
    
    # Touchscreen
    if validated.get('touchscreen') is True:
        score += SCORING_WEIGHTS['touchscreen']
    
    # Correct size
    screen_size = str(validated.get('screen_size', ''))
    if '15.6' in screen_size or '15' in screen_size:
        score += SCORING_WEIGHTS['correct_size']
    
    # Front camera
    if validated.get('camera_front') is True:
        score += SCORING_WEIGHTS['front_camera']
    
    # eSIM/LTE
    if validated.get('esim_support') is True:
        score += SCORING_WEIGHTS['esim_lte']
    
    # MOQ acceptable
    moq = validated.get('moq')
    if moq:
        try:
            moq_num = int(str(moq).replace(',', ''))
            if moq_num <= PRODUCT_SPECS['moq_max_acceptable']:
                score += SCORING_WEIGHTS['moq_acceptable']
        except:
            pass
    
    # Price in range
    price = validated.get('price_per_unit')
    if price:
        try:
            price_num = float(str(price).replace('$', '').replace(',', ''))
            if PRODUCT_SPECS['target_cogs_min'] <= price_num <= PRODUCT_SPECS['target_cogs_max']:
                score += SCORING_WEIGHTS['price_in_range']
        except:
            pass
    
    # Customizable
    if validated.get('customizable') is True:
        score += SCORING_WEIGHTS['customizable']
    
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
    
    if not validated or validated.get('score', 0) < 50:
        print("✗ Skipping save - no validated data or score too low")
        return {
            **state,
            "status": "save_skipped"
        }
    
    try:
        conn = sqlite3.connect(VENDORS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vendors (
                vendor_name, url, platform, moq, price_per_unit,
                customizable, os, screen_size, touchscreen,
                camera_front, esim_support, score, status, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            validated.get('esim_support'),
            validated.get('score'),
            'new',
            json.dumps(validated)
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
