#!/usr/bin/env python
import urllib.request
import json

try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/test-openrouter')
    data = json.loads(response.read().decode())
    print(f"test_call_success: {data.get('test_call_success')}")
    print(f"debug_model_name: {data.get('debug_model_name')}")
    print(f"error: {data.get('error', 'None')[:100]}")
except Exception as e:
    print(f"Error: {e}")
