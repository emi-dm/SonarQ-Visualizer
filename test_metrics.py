#!/usr/bin/env python3
"""Test metrics extraction with fixed Basic Auth."""

from backend.src.services.sonarqube_client import SonarQubeClient
import json

token = '86d94f6df17bbf7f79ec048dbe378f3f84ddc235'
client = SonarQubeClient('https://sonarcloud.io', token)

try:
    print('🔍 Obteniendo métricas de SpecKit-Example con branch 001-paper-repository...')
    metrics = client.get_project_metrics('emi-dm_SpecKit-Example', branch='001-paper-repository')
    print('✅ Métricas obtenidas exitosamente!')
    print(f'\n📊 Resumen:')
    print(f'   Bugs: {metrics.get("bugs_count")}')
    print(f'   Vulnerabilities: {metrics.get("vulnerabilities_count")}')
    print(f'   Code Smells: {metrics.get("code_smells_count")}')
    print(f'   Coverage: {metrics.get("coverage_pct")}%')
    print(f'   Quality Gate: {metrics.get("quality_gate_status")}')
    print(f'   NCLOC: {metrics.get("ncloc")}')
    print(f'\n📋 Respuesta completa:')
    print(json.dumps(metrics, indent=2, default=str))
finally:
    client.close()
