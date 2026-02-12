#!/usr/bin/env python3
"""Refresh metrics for all projects with available analyses."""

import requests
import sys
import os

TOKEN = os.getenv("SONAR_API_TOKEN", "")
BASE_URL = 'http://127.0.0.1:8000/api/v1'

def refresh_project_metrics(project_id, project_name, branch=None):
    """Refresh metrics for a project."""
    print(f"\n🔄 Refreshing metrics for Project {project_id}: {project_name}")
    
    try:
        payload = {"token": TOKEN}
        if branch:
            payload["branch"] = branch
            
        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/metrics/refresh",
            json=payload
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("   ✅ Metrics refreshed successfully!")
            print(f"      - Bugs: {data.get('bugs_count')}")
            print(f"      - Vulnerabilities: {data.get('vulnerabilities_count')}")
            print(f"      - Code Smells: {data.get('code_smells_count')}")
            print(f"      - Coverage: {data.get('coverage_pct')}%")
            return True
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"      {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

# Projects to refresh
projects = [
    {"id": 2, "name": "SpecKit-Example", "branch": "001-paper-repository"},
    {"id": 3, "name": "YouTube-Vault", "branch": "001-youtube-video-library"}
]

print("🚀 Refreshing metrics for all projects with analyses...")

if not TOKEN:
    print("❌ Missing SONAR_API_TOKEN environment variable")
    sys.exit(1)

success_count = 0
for project in projects:
    if refresh_project_metrics(project["id"], project["name"], project["branch"]):
        success_count += 1

print(f"\n📊 Summary: {success_count}/{len(projects)} projects refreshed successfully")
