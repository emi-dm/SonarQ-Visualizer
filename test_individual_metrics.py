#!/usr/bin/env python3
"""Test each metric to find which ones cause 404."""

import requests

token = '86d94f6df17bbf7f79ec048dbe378f3f84ddc235'
url = "https://sonarcloud.io/api/measures/component"
project = "emi-dm_SpecKit-Example"

all_metrics = [
    "bugs",
    "vulnerabilities",
    "code_smells",
    "coverage",
    "duplicated_lines_density",
    "ncloc",
    "alert_status",
    "quality_gate_status",
    "quality_gate_details",
    "blocker_violations",
    "critical_violations",
    "major_violations",
    "minor_violations",
    "info_violations"
]

print("🔍 Probando cada métrica individualmente...\n")

working_metrics = []
failing_metrics = []

for metric in all_metrics:
    response = requests.get(
        url, 
        params={"component": project, "metricKeys": metric},
        auth=(token, '')
    )
    if response.status_code == 200:
        data = response.json()
        measures = data.get("component", {}).get("measures", [])
        if measures:
            value = measures[0].get("value", "N/A")
            working_metrics.append(metric)
            print(f"✅ {metric:30} = {value}")
        else:
            print(f"⚠️  {metric:30} (sin datos)")
            working_metrics.append(metric)  # Available but no value
    else:
        failing_metrics.append(metric)
        print(f"❌ {metric:30} (404)")

print(f"\n\n📊 Resumen:")
print(f"   Métricas disponibles: {len(working_metrics)}/{len(all_metrics)}")
print(f"   Lista de métricas que funcionan:")
print(f"   {', '.join(working_metrics)}")

if failing_metrics:
    print(f"\n   ⚠️  Métricas que causan 404:")
    print(f"   {', '.join(failing_metrics)}")

print(f"\n\n🔧 Probando con TODAS las métricas disponibles juntas...")
working_keys = ",".join(working_metrics)
response = requests.get(
    url,
    params={"component": project, "metricKeys": working_keys},
    auth=(token, '')
)

if response.status_code == 200:
    print("✅ Funciona con todas las métricas disponibles")
else:
    print(f"❌ Falla con todas juntas: {response.status_code}")
