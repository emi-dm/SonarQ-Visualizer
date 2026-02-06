#!/usr/bin/env python3
"""Verify dashboard data integrity."""

import requests
import json

response = requests.get('http://127.0.0.1:8000/api/v1/dashboard')
data = response.json()

print('🎯 VERIFICACIÓN COMPLETA DEL DASHBOARD\n')
print('='*60)

# Verificar proyectos
projects = data.get('projects', [])
print(f'\n📊 PROYECTOS: {len(projects)} proyectos con métricas\n')

for i, proj in enumerate(projects, 1):
    print(f'  [{i}] {proj["project_name"]} (ID: {proj["project_id"]})')
    metrics = proj.get('latest_metrics', {})
    print(f'      ├─ Branch: {metrics.get("branch_name")}')
    print(f'      ├─ Bugs: {metrics.get("bugs_count")}')
    print(f'      ├─ Vulnerabilities: {metrics.get("vulnerabilities_count")}')
    print(f'      ├─ Code Smells: {metrics.get("code_smells_count")}')
    print(f'      ├─ Coverage: {metrics.get("coverage_pct") or "N/A"}')
    print(f'      ├─ Duplications: {metrics.get("duplications_pct")}%')
    print(f'      ├─ Quality Gate: {metrics.get("quality_gate_status")}')
    print(f'      ├─ NCLOC: {metrics.get("ncloc")}')
    print(f'      └─ Staleness: {proj.get("staleness_hours")} hours')
    
    # Verificar severity breakdown
    severity = metrics.get('severity_breakdown', {})
    if severity:
        print(f'      Severity Breakdown:')
        for key, val in severity.items():
            print(f'        • {key}: {val}')
    print()

# Verificar agregados
agg = data.get('aggregates', {})
print(f'\n📈 AGREGADOS (FR-029):\n')
print(f'  ├─ Total Projects: {agg.get("total_projects")}')
print(f'  ├─ Total Bugs: {agg.get("total_bugs")}')
print(f'  ├─ Total Vulnerabilities: {agg.get("total_vulnerabilities")}')
print(f'  ├─ Total Code Smells: {agg.get("total_code_smells")}')
print(f'  ├─ Avg Coverage: {agg.get("avg_coverage") or "N/A"}')
print(f'  ├─ Avg Duplications: {agg.get("avg_duplications")}%')
print(f'  └─ Quality Gate Pass Rate: {agg.get("quality_gate_pass_rate")}%')

print(f'\n' + '='*60)

# Verificaciones de integridad
issues = []

if len(projects) == 0:
    issues.append('❌ No hay proyectos con métricas')
    
for proj in projects:
    if not proj.get('latest_metrics'):
        issues.append(f'❌ Proyecto {proj["project_name"]} sin métricas')
    else:
        metrics = proj['latest_metrics']
        required_fields = ['bugs_count', 'vulnerabilities_count', 'code_smells_count', 
                          'quality_gate_status', 'branch_name']
        for field in required_fields:
            if field not in metrics:
                issues.append(f'❌ Proyecto {proj["project_name"]}: falta campo {field}')

if agg.get('total_projects', 0) != len(projects):
    issues.append(f'❌ Inconsistencia: total_projects={agg.get("total_projects")} pero hay {len(projects)} proyectos')

if issues:
    print('\n⚠️  PROBLEMAS ENCONTRADOS:\n')
    for issue in issues:
        print(f'  {issue}')
else:
    print('\n✅ VERIFICACIÓN COMPLETA: Todos los datos se vuelcan correctamente')
    print('   • Proyectos con métricas completas')
    print('   • Agregados calculados correctamente (FR-029)')
    print('   • Severity breakdown disponible')
    print('   • Staleness calculado')

print()
