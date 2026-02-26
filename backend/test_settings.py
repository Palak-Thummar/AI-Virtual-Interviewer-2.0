#!/usr/bin/env python
import os
import sys

# Test if OPENROUTER_MODEL_NAME loads from .env
print(f"Current directory: {os.getcwd()}")
print(f".env exists: {os.path.exists('.env')}")

# Show .env content for OPENROUTER_MODEL_NAME
print("\nContent of .env for OPENROUTER_MODEL_NAME:")
with open('.env' if os.path.exists('.env') else '') as f:
    for line in f:
        if 'OPENROUTER_MODEL_NAME' in line or line.startswith('OPENROUTER_'):
            print(f"  {line.strip()}")

# Now test loading settings
from app.core.config import Settings
settings = Settings()

print(f"\nSettings loaded:")
print(f"  OPENROUTER_API_KEY set: {bool(settings.OPENROUTER_API_KEY)}")
print(f"  OPENROUTER_MODEL_NAME: {settings.OPENROUTER_MODEL_NAME}")

