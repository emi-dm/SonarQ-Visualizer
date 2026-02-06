#!/usr/bin/env python3
"""Direct test with requests to compare."""

import requests
import json

token = '86d94f6df17bbf7f79ec048dbe378f3f84ddc235'

# Exact same call as the test script that worked
url = "https://sonarcloud.io/api/measures/component"
params = {
    "component": "emi-dm_SpecKit-Example",
    "metricKeys": "bugs,vulnerabilities,code_smells,coverage"  # Simpler metrics
}
headers = {"Authorization": f"Bearer {token}"}

print("🔍 Probando con requests directo (sin branch)...")
response = requests.get(url, params=params, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("✅ Funciona!\n")
    print(json.dumps(data, indent=2))
else:
    print(f"❌ Error: {response.text}")

print("\n\n🔍 Probando con branch 001-paper-repository...")
params["branch"] = "001-paper-repository"
response = requests.get(url, params=params, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("✅ Funciona con branch!\n")
    print(json.dumps(data, indent=2))
else:
    print(f"❌ Error con branch: {response.text}")

print("\n\n🔍 Probando con Basic Auth (token como usuario)...")
params.pop("branch", None)
response = requests.get(url, params=params, auth=(token, ''))
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("✅ Funciona con Basic Auth!\n")
    print(json.dumps(data, indent=2))
else:
    print(f"❌ Error con Basic Auth: {response.text}")
