#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script to diagnose PostgreSQL encoding issues"""

import sys
import os

# Force UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

from services.database_connectors import PostgreSQLConnector, ensure_valid_utf8
import urllib.parse

def test_postgres():
    """Test PostgreSQL connection with various encodings"""
    
    print("\n=== PostgreSQL Connection Test ===\n")
    
    # Test parameters
    host = "localhost"
    port = 5432
    user = "postgres"
    password = "hind2003hind"
    database = "test_db"
    
    print(f"Test parameters:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  User: {user}")
    print(f"  Password: {password}")
    print(f"  Database: {database}")
    
    # Build URL manually
    print("\n1. Building URL with urllib.parse.quote()...")
    user_encoded = urllib.parse.quote(user, safe='')
    password_encoded = urllib.parse.quote(password, safe='')
    database_encoded = urllib.parse.quote(database, safe='')
    
    url = f"postgresql+psycopg2://{user_encoded}:{password_encoded}@{host}:{port}/{database_encoded}"
    print(f"  Generated URL: {url}")
    print(f"  URL bytes: {url.encode('utf-8')}")
    
    # Test parsing
    print("\n2. Parsing URL...")
    try:
        connector = PostgreSQLConnector()
        params = connector.parse_url(url)
        print(f"  Parsed successfully:")
        for key, value in params.items():
            print(f"    {key}: {value} (type: {type(value).__name__})")
    except Exception as e:
        print(f"  ERROR: {e}")
        return
    
    # Test ensure_valid_utf8
    print("\n3. Testing ensure_valid_utf8()...")
    for name, value in params.items():
        try:
            if value:
                validated = ensure_valid_utf8(value)
                print(f"  {name}: OK - {validated}")
        except Exception as e:
            print(f"  {name}: ERROR - {e}")
    
    # Try to connect
    print("\n4. Attempting connection...")
    try:
        result = connector.test_connection(url)
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_postgres()
