#!/usr/bin/env python3
"""Test metrics extraction with fixed Basic Auth."""

from backend.src.services.sonarqube_client import SonarQubeClient
import json
import os

token = os.getenv("SONAR_API_TOKEN", "")

if not token:
    raise SystemExit("Missing SONAR_API_TOKEN environment variable")

client = SonarQubeClient('https://sonarcloud.io', token)

try:
    print('🔍 Obteniendo métricas de SpecKit-Example con branch 001-paper-repository...')
    metrics = client.get_project_metrics('emi-dm_SpecKit-Example', branch='001-paper-repository')
    print('✅ Métricas obtenidas exitosamente!')
    print('\n📊 Resumen:')
    print(f'   Bugs: {metrics.get("bugs_count")}')
    print(f'   Vulnerabilities: {metrics.get("vulnerabilities_count")}')
    print(f'   Code Smells: {metrics.get("code_smells_count")}')
    print(f'   Coverage: {metrics.get("coverage_pct")}%')
    print(f'   Quality Gate: {metrics.get("quality_gate_status")}')
    print(f'   NCLOC: {metrics.get("ncloc")}')
    print('\n📋 Respuesta completa:')
    print(json.dumps(metrics, indent=2, default=str))
finally:
    client.close()
