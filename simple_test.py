#!/usr/bin/env python3
import urllib.request
import json
import sys

try:
    print("Testing API health endpoint...")
    req = urllib.request.Request('http://localhost:8000/api/health')
    with urllib.request.urlopen(req, timeout=3) as response:
        data = json.loads(response.read().decode())
        print("✓ Backend is responding!")
        print("Response:", json.dumps(data, indent=2))
except Exception as e:
    print(f"✗ Error connecting: {e}")
    sys.exit(1)
