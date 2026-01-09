#!/usr/bin/env python3
"""
Quick test for MCP server functionality.
This verifies that the server can be initialized and has the expected structure.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set minimal environment for testing
os.environ.setdefault('MEMU_PROVIDER', 'ollama')
os.environ.setdefault('OLLAMA_BASE_URL', 'http://localhost:11434/v1')
os.environ.setdefault('OLLAMA_MODEL', 'llama3')
os.environ.setdefault('OLLAMA_API_KEY', 'ollama')

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import Resource, TextContent, Tool
        print("✓ MCP SDK imports successful")
    except ImportError as e:
        print(f"✗ MCP SDK import failed: {e}")
        return False
    
    try:
        from memu.app import MemoryService
        print("✓ MemU MemoryService import successful")
    except ImportError as e:
        print(f"✗ MemoryService import failed: {e}")
        return False
    
    try:
        import memu.mcp_server
        print("✓ MCP server module import successful")
    except ImportError as e:
        print(f"✗ MCP server module import failed: {e}")
        return False
    
    return True

def test_server_initialization():
    """Test that the MCP server can be initialized."""
    print("\nTesting server initialization...")
    try:
        from memu.mcp_server import MemUMCPServer
        
        # Create server instance
        server = MemUMCPServer()
        print("✓ Server instance created")
        
        # Check that it has the expected attributes
        assert hasattr(server, 'config'), "Server missing config attribute"
        assert hasattr(server, 'server'), "Server missing server attribute"
        print("✓ Server has expected attributes")
        
        # Check config
        assert 'provider' in server.config, "Config missing provider"
        assert 'llm_profiles' in server.config, "Config missing llm_profiles"
        print(f"✓ Server configured with provider: {server.config['provider']}")
        
        return True
    except Exception as e:
        print(f"✗ Server initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loading():
    """Test configuration loading from environment."""
    print("\nTesting config loading...")
    try:
        from memu.mcp_server import MemUMCPServer
        
        # Test with explicit provider
        os.environ['MEMU_PROVIDER'] = 'openai'
        os.environ['OPENAI_API_KEY'] = 'test-key'
        
        server = MemUMCPServer()
        assert server.config['provider'] == 'openai', f"Expected openai, got {server.config['provider']}"
        print("✓ Config loaded from environment variables")
        
        # Check OpenAI profile
        assert 'default' in server.config['llm_profiles'], "Missing default profile"
        profile = server.config['llm_profiles']['default']
        assert 'base_url' in profile, "Profile missing base_url"
        assert 'api_key' in profile, "Profile missing api_key"
        print(f"✓ OpenAI profile configured: {profile['base_url']}")
        
        return True
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("MemU MCP Server - Quick Test")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Server Initialization", test_server_initialization),
        ("Config Loading", test_config_loading),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("All tests passed! ✓")
        return 0
    else:
        print("Some tests failed. ✗")
        return 1

if __name__ == "__main__":
    sys.exit(main())
