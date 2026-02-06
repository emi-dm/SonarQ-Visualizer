#!/usr/bin/env python3
"""Script para verificar acceso a SonarCloud y listar proyectos disponibles."""

import requests
import sys
import json

def test_sonarcloud_access(token: str, organization: str):
    """Verifica acceso a SonarCloud y lista proyectos."""
    
    print(f"\n🔍 Verificando acceso a SonarCloud...")
    print(f"   Organización: {organization}\n")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Verificar autenticación
    print("1️⃣  Verificando autenticación...")
    auth_response = requests.get(
        "https://sonarcloud.io/api/authentication/validate",
        headers=headers
    )
    
    if auth_response.status_code == 200:
        auth_data = auth_response.json()
        print(f"   ✅ Token válido - Usuario: {auth_data.get('login', 'N/A')}")
    else:
        print(f"   ❌ Token inválido - Status: {auth_response.status_code}")
        return
    
    # 2. Listar proyectos de la organización
    print(f"\n2️⃣  Listando proyectos en organización '{organization}'...")
    projects_response = requests.get(
        "https://sonarcloud.io/api/projects/search",
        params={"organization": organization, "ps": 100},
        headers=headers
    )
    
    if projects_response.status_code != 200:
        print(f"   ❌ Error al listar proyectos - Status: {projects_response.status_code}")
        print(f"   Respuesta: {projects_response.text}")
        return
    
    projects_data = projects_response.json()
    components = projects_data.get("components", [])
    
    if not components:
        print("   ⚠️  No se encontraron proyectos en esta organización")
        print("   💡 Posibles causas:")
        print("      - No hay proyectos creados aún")
        print("      - El token no tiene permisos para ver proyectos")
        return
    
    print(f"   ✅ Encontrados {len(components)} proyecto(s):\n")
    
    # 3. Verificar estado de cada proyecto
    for idx, project in enumerate(components, 1):
        key = project.get("key")
        name = project.get("name")
        last_analysis = project.get("lastAnalysisDate", "❌ Nunca analizado")
        
        print(f"   [{idx}] {name}")
        print(f"       Key: {key}")
        print(f"       Último análisis: {last_analysis}")
        
        # Intentar obtener métricas
        metrics_response = requests.get(
            "https://sonarcloud.io/api/measures/component",
            params={
                "component": key,
                "metricKeys": "bugs,vulnerabilities,code_smells,coverage"
            },
            headers=headers
        )
        
        if metrics_response.status_code == 200:
            measures = metrics_response.json().get("component", {}).get("measures", [])
            if measures:
                print(f"       ✅ Métricas disponibles ({len(measures)} métricas)")
                for measure in measures[:3]:  # Mostrar primeras 3
                    print(f"          - {measure.get('metric')}: {measure.get('value', 'N/A')}")
            else:
                print(f"       ⚠️  Sin métricas (proyecto no analizado)")
        else:
            print(f"       ⚠️  No se pueden obtener métricas - Status: {metrics_response.status_code}")
        
        # Verificar branches
        branches_response = requests.get(
            "https://sonarcloud.io/api/project_branches/list",
            params={"project": key},
            headers=headers
        )
        
        if branches_response.status_code == 200:
            branches = branches_response.json().get("branches", [])
            if branches:
                default_branch = next((b for b in branches if b.get("isMain")), branches[0])
                print(f"       📋 Branch por defecto: {default_branch.get('name')}")
            else:
                print(f"       ⚠️  Sin branches configurados")
        
        print()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python test_sonarcloud_access.py <TOKEN> <ORGANIZATION>")
        print("\nEjemplo:")
        print("  python test_sonarcloud_access.py squ_abc123... phd-sdd")
        sys.exit(1)
    
    token = sys.argv[1]
    organization = sys.argv[2]
    
    test_sonarcloud_access(token, organization)
