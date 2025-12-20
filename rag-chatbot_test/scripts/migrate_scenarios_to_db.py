"""
시나리오 파일 → PostgreSQL 마이그레이션 스크립트

사용법:
    python scripts/migrate_scenarios_to_db.py --token YOUR_JWT_TOKEN
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# 프로젝트 루트를 Python Path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.spring_boot_client import spring_boot_client


async def load_scenarios_from_files(scenarios_dir: Path) -> list[Dict[str, Any]]:
    """파일 시스템에서 시나리오 로드"""
    scenarios = []
    
    # public 시나리오
    public_dir = scenarios_dir / "public"
    if public_dir.exists():
        for file_path in public_dir.glob("*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                scenario = json.load(f)
                scenario['_source_file'] = str(file_path)
                scenarios.append(scenario)
    
    # private 시나리오
    private_dir = scenarios_dir / "private"
    if private_dir.exists():
        for user_dir in private_dir.iterdir():
            if user_dir.is_dir():
                for file_path in user_dir.glob("*.json"):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        scenario = json.load(f)
                        scenario['_source_file'] = str(file_path)
                        scenarios.append(scenario)
    
    # forked 시나리오
    forked_dir = scenarios_dir / "forked"
    if forked_dir.exists():
        for user_dir in forked_dir.iterdir():
            if user_dir.is_dir():
                for file_path in user_dir.glob("*.json"):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        scenario = json.load(f)
                        scenario['_source_file'] = str(file_path)
                        scenarios.append(scenario)
    
    return scenarios


def convert_to_spring_boot_format(old_scenario: Dict[str, Any]) -> Dict[str, Any]:
    """FastAPI 형식 → Spring Boot 형식 변환"""
    
    # Spring Boot CreateScenarioRequest 형식으로 변환
    spring_scenario = {
        "novelId": "123e4567-e89b-12d3-a456-426614174001",  # TODO: 실제 Novel ID 매핑 필요
        "baseScenarioId": old_scenario.get("base_scenario_id"),
        "scenarioTitle": old_scenario.get("scenario_name", "Migrated Scenario"),
        "whatIfQuestion": old_scenario.get("what_if_question", ""),
        "isPrivate": not old_scenario.get("is_public", False)
    }
    
    # Character changes
    char_changes = old_scenario.get("character_property_changes", {})
    if char_changes.get("enabled"):
        spring_scenario["characterChanges"] = char_changes.get("description", "")
    
    # Event alterations
    event_changes = old_scenario.get("event_alterations", {})
    if event_changes.get("enabled"):
        spring_scenario["eventAlterations"] = event_changes.get("description", "")
    
    # Setting modifications
    setting_changes = old_scenario.get("setting_modifications", {})
    if setting_changes.get("enabled"):
        spring_scenario["settingModifications"] = setting_changes.get("description", "")
    
    return spring_scenario


async def migrate_scenario(
    scenario: Dict[str, Any],
    jwt_token: str,
    dry_run: bool = True
) -> Dict[str, Any]:
    """단일 시나리오 마이그레이션"""
    
    # 변환
    spring_format = convert_to_spring_boot_format(scenario)
    
    if dry_run:
        print(f"\n[DRY RUN] 마이그레이션 예정:")
        print(f"  Source: {scenario.get('_source_file', 'unknown')}")
        print(f"  Title: {spring_format['scenarioTitle']}")
        print(f"  Private: {spring_format['isPrivate']}")
        return {"status": "dry_run", "data": spring_format}
    
    try:
        # Spring Boot로 생성
        result = await spring_boot_client.create_scenario(
            scenario_data=spring_format,
            jwt_token=jwt_token
        )
        
        print(f"✅ 마이그레이션 성공:")
        print(f"  Source: {scenario.get('_source_file', 'unknown')}")
        print(f"  New ID: {result.get('scenarioId', 'unknown')}")
        
        return {"status": "success", "data": result}
    
    except Exception as e:
        print(f"❌ 마이그레이션 실패:")
        print(f"  Source: {scenario.get('_source_file', 'unknown')}")
        print(f"  Error: {str(e)}")
        
        return {"status": "error", "error": str(e)}


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="시나리오 마이그레이션")
    parser.add_argument("--token", required=True, help="JWT Access Token (관리자)")
    parser.add_argument("--dry-run", action="store_true", help="실제 실행하지 않고 미리보기만")
    parser.add_argument("--scenarios-dir", default="data/scenarios", help="시나리오 디렉토리 경로")
    
    args = parser.parse_args()
    
    # 시나리오 로드
    scenarios_dir = Path(args.scenarios_dir)
    if not scenarios_dir.exists():
        print(f"❌ 시나리오 디렉토리가 없습니다: {scenarios_dir}")
        return
    
    scenarios = await load_scenarios_from_files(scenarios_dir)
    print(f"\n📂 발견된 시나리오: {len(scenarios)}개")
    
    if len(scenarios) == 0:
        print("ℹ️  마이그레이션할 시나리오가 없습니다.")
        return
    
    # 마이그레이션 실행
    results = []
    for scenario in scenarios:
        result = await migrate_scenario(
            scenario=scenario,
            jwt_token=args.token,
            dry_run=args.dry_run
        )
        results.append(result)
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 마이그레이션 결과 요약")
    print("="*60)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")
    dry_run_count = sum(1 for r in results if r["status"] == "dry_run")
    
    if args.dry_run:
        print(f"  DRY RUN: {dry_run_count}개")
        print("\n실제 마이그레이션을 실행하려면 --dry-run 플래그 없이 실행하세요.")
    else:
        print(f"  ✅ 성공: {success_count}개")
        print(f"  ❌ 실패: {error_count}개")
        print(f"  📊 총합: {len(scenarios)}개")


if __name__ == "__main__":
    asyncio.run(main())

