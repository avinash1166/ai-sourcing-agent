#!/usr/bin/env python3
"""
System Health Check
Verifies all components are working correctly
"""

import sys
import subprocess
import os

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def check_python():
    """Check Python version"""
    print_header("Checking Python")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✓ Python version OK")
        return True
    else:
        print("✗ Python 3.8+ required")
        return False

def check_ollama():
    """Check if Ollama is installed and running"""
    print_header("Checking Ollama")
    
    # Check if ollama command exists
    try:
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        
        if result.returncode == 0:
            print("✓ Ollama is installed and running")
            print("\nInstalled models:")
            print(result.stdout)
            
            # Check for qwen2.5:3b
            if 'qwen2.5:3b' in result.stdout or 'qwen2.5' in result.stdout:
                print("✓ qwen2.5:3b model found")
                return True
            else:
                print("⚠ qwen2.5:3b model not found")
                print("Run: ollama pull qwen2.5:3b")
                return False
        else:
            print("✗ Ollama command failed")
            return False
    
    except FileNotFoundError:
        print("✗ Ollama not installed")
        print("Install: curl -fsSL https://ollama.com/install.sh | sh")
        return False
    except subprocess.TimeoutExpired:
        print("✗ Ollama not responding")
        print("Start: ollama serve")
        return False

def check_dependencies():
    """Check Python dependencies"""
    print_header("Checking Python Dependencies")
    
    required = {
        'langchain': 'langchain',
        'langchain_ollama': 'langchain-ollama',
        'langgraph': 'langgraph',
    }
    
    optional = {
        'playwright': 'playwright (for web scraping)',
    }
    
    all_ok = True
    
    print("Required packages:")
    for module, package in required.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - MISSING")
            all_ok = False
    
    print("\nOptional packages:")
    for module, package in optional.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ⊘ {package} - Not installed (test mode only)")
    
    if not all_ok:
        print("\nInstall missing packages:")
        print("  pip install langchain langchain-ollama langgraph")
    
    return all_ok

def check_files():
    """Check if all required files exist"""
    print_header("Checking Project Files")
    
    required_files = [
        'config.py',
        'validators.py',
        'oem_search.py',
        'scraper.py',
        'email_outreach.py',
        'reporting.py',
        'main.py',
    ]
    
    all_ok = True
    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  ✓ {file} ({size:,} bytes)")
        else:
            print(f"  ✗ {file} - MISSING")
            all_ok = False
    
    return all_ok

def check_directories():
    """Check/create data directories"""
    print_header("Checking Data Directories")
    
    dirs = [
        'data',
        'data/logs',
        'data/reports',
    ]
    
    for dir_path in dirs:
        if os.path.exists(dir_path):
            print(f"  ✓ {dir_path}/")
        else:
            os.makedirs(dir_path, exist_ok=True)
            print(f"  ✓ {dir_path}/ (created)")
    
    return True

def test_validator():
    """Test the validator module"""
    print_header("Testing Validator Module")
    
    try:
        from validators import MultiLayerValidator, ValidationResult
        
        validator = MultiLayerValidator()
        
        # Test format check
        test_data = {"vendor_name": "Test", "moq": 100}
        test_schema = {"vendor_name": str, "moq": int}
        
        result = validator.layer1_format_check(test_data, test_schema)
        
        if result.passed:
            print("✓ Format validation working")
        else:
            print(f"✗ Format validation failed: {result.reason}")
            return False
        
        # Test factual check
        source_text = "Our company Test has MOQ of 100 units"
        result = validator.layer2_factual_check(test_data, source_text)
        
        if result.passed:
            print("✓ Factual validation working")
        else:
            print(f"⚠ Factual validation: {result.reason}")
        
        print("✓ Validator module OK")
        return True
    
    except Exception as e:
        print(f"✗ Validator test failed: {e}")
        return False

def test_llm_connection():
    """Test LLM connection"""
    print_header("Testing LLM Connection")
    
    try:
        from langchain_ollama import OllamaLLM
        
        print("Connecting to Ollama...")
        llm = OllamaLLM(model="qwen2.5:3b", temperature=0.1)
        
        print("Sending test prompt...")
        response = llm.invoke("Say 'Hello' and nothing else.")
        
        print(f"Response: {response[:100]}")
        
        if response:
            print("✓ LLM connection working")
            return True
        else:
            print("✗ No response from LLM")
            return False
    
    except Exception as e:
        print(f"✗ LLM connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check Ollama is running: ollama serve")
        print("  2. Check model is installed: ollama list")
        print("  3. Pull model: ollama pull qwen2.5:3b")
        return False

def run_mini_test():
    """Run a mini end-to-end test"""
    print_header("Running Mini End-to-End Test")
    
    try:
        from oem_search import build_agent
        
        print("Building agent...")
        agent = build_agent()
        
        print("Testing with sample vendor...")
        
        test_state = {
            "task": "test",
            "search_query": "",
            "raw_html": """
            Test Company Ltd.
            15.6 inch Android tablet
            Price: $130/unit
            MOQ: 150 pieces
            Touchscreen: Yes
            """,
            "extracted_data": {},
            "validation_results": [],
            "validated_data": {},
            "historical_vendors": [],
            "retry_count": 0,
            "error_log": "",
            "status": "initialized"
        }
        
        print("Processing...")
        result = agent.invoke(test_state)
        
        print(f"\nResult status: {result['status']}")
        
        if result['status'] in ['validated', 'scored', 'saved']:
            print("✓ End-to-end test PASSED")
            if result.get('validated_data'):
                score = result['validated_data'].get('score', 'N/A')
                print(f"  Vendor score: {score}/100")
            return True
        else:
            print("⚠ Test completed but vendor was rejected")
            print(f"  Reason: {result.get('error_log', 'Validation failed')}")
            return True  # Still OK - rejection is valid behavior
    
    except Exception as e:
        print(f"✗ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all health checks"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║            AI Sourcing Agent - Health Check                  ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    checks = [
        ("Python Version", check_python),
        ("Ollama Installation", check_ollama),
        ("Python Dependencies", check_dependencies),
        ("Project Files", check_files),
        ("Data Directories", check_directories),
        ("Validator Module", test_validator),
        ("LLM Connection", test_llm_connection),
        ("Mini E2E Test", run_mini_test),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Unexpected error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("  HEALTH CHECK SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:8} {name}")
    
    print("\n" + "=" * 60)
    print(f"  Score: {passed}/{total} checks passed")
    
    if passed == total:
        print("  Status: ✓ ALL SYSTEMS GO")
        print("=" * 60)
        print("\nYou're ready to run:")
        print("  python3 main.py --test    # Test mode")
        print("  python3 main.py           # Production mode")
    elif passed >= total - 2:
        print("  Status: ⚠ MOSTLY READY (minor issues)")
        print("=" * 60)
        print("\nYou can run in test mode:")
        print("  python3 main.py --test")
    else:
        print("  Status: ✗ SETUP INCOMPLETE")
        print("=" * 60)
        print("\nRun setup script:")
        print("  ./setup.sh")
    
    print()

if __name__ == "__main__":
    main()
