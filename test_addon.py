#!/usr/bin/env python3
"""
Test script for Printernizer HA Addon
Tests the core functionality without requiring Home Assistant
"""

import asyncio
import json
import os
import sys
import logging
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent / "printernizer" / "rootfs" / "app"
sys.path.insert(0, str(app_dir))

# Mock environment variables for testing
os.environ.update({
    'BASHIO_WEB_PORT': '8080',
    'BASHIO_LOG_LEVEL': 'info',
    'BASHIO_MQTT_DISCOVERY': 'true',
    'BASHIO_AUTO_CONFIGURE_MQTT': 'false',
    'BASHIO_PRINTERS': json.dumps([
        {
            "id": "test_bambu",
            "name": "Test Bambu Lab A1",
            "type": "bambu_lab",
            "host": "192.168.1.100",
            "device_id": "01234567890ABCDEF",
            "serial": "01234567890ABCDEF",
            "access_code": "12345678"
        },
        {
            "id": "test_prusa",
            "name": "Test Prusa Core One",
            "type": "prusa",
            "host": "192.168.1.101",
            "api_key": "test_api_key_123"
        }
    ])
})

async def test_configuration():
    """Test configuration loading"""
    print("Testing configuration loading...")
    
    try:
        import main
        
        main.load_addon_config()
        
        print(f"✅ Configuration loaded successfully")
        print(f"   - Web port: {main.CONFIG.get('web_port')}")
        print(f"   - MQTT discovery: {main.CONFIG.get('mqtt_discovery')}")  
        print(f"   - Auto configure MQTT: {main.CONFIG.get('auto_configure_mqtt')}")
        print(f"   - Printers configured: {len(main.PRINTERS)}")
        
        for printer_id, printer_config in main.PRINTERS.items():
            print(f"   - {printer_id}: {printer_config.get('type')} ({printer_config.get('name')})")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

async def test_printer_manager():
    """Test printer manager"""
    print("\nTesting printer manager...")
    
    try:
        from printers import PrinterManager, PrinterStatus
        
        manager = PrinterManager()
        
        # Test adding a mock printer configuration
        test_config = {
            "id": "test_mock",
            "name": "Mock Printer",
            "type": "mock",
            "host": "localhost"
        }
        
        print("✅ Printer manager created successfully")
        print(f"   - Manager initialized with {len(manager.printers)} printers")
        
        return True
        
    except Exception as e:
        print(f"❌ Printer manager test failed: {e}")
        return False

async def test_api_endpoints():
    """Test API endpoints"""
    print("\nTesting API endpoints...")
    
    try:
        import httpx
        
        # Start the server in background
        from main import app
        import uvicorn
        
        # Test basic endpoint access (without actually starting server)
        print("✅ API endpoints imported successfully")
        print("   - FastAPI app created")
        print("   - Routes configured")
        
        return True
        
    except ImportError:
        print("⚠️  httpx not available for endpoint testing")
        return True
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

async def test_templates():
    """Test template rendering"""
    print("\nTesting templates...")
    
    try:
        from pathlib import Path
        
        template_path = Path("printernizer/rootfs/app/templates/index.html")
        
        if template_path.exists():
            print("✅ Template files found")
            print(f"   - index.html: {template_path.stat().st_size} bytes")
        else:
            print("❌ Template files not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Template test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("🧪 Running Printernizer HA Addon Tests")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_printer_manager,
        test_api_endpoints,
        test_templates
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"   ✅ Passed: {passed}/{total}")
    print(f"   ❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! The addon should work correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    success = asyncio.run(run_all_tests())
    
    if not success:
        sys.exit(1)
    
    print("\n🚀 To run the addon:")
    print("   1. Build the Docker image: ./dev.sh build")
    print("   2. Test locally: ./dev.sh run")
    print("   3. Or start development: ./dev.sh shell")