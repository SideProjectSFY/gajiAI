"""
마이그레이션 검증 스크립트
V48, V49 파일에 모든 소설이 포함되어 있는지 확인
"""

import sys
from pathlib import Path

# 확인할 소설 목록 (origin_txt 기반, 108 제외)
novels_from_origin = [
    "Alice's Adventures in Wonderland",
    "The Count of Monte Cristo, Illustrated",
    "Treasure Island",
    "The Three Musketeers",
    "Jane Eyre: An Autobiography",
    "Pride and Prejudice",
    "Great Expectations",
    "Moby Dick; Or, The Whale",
    "Romeo and Juliet",
    "The Moonstone",
    "Emma",
    "Sense and Sensibility",
    "Twenty Thousand Leagues under the Sea",
    "The Adventures of Sherlock Holmes",
    "The Hound of the Baskervilles",
    "Dracula",
    "The Time Machine",
    "The War of the Worlds",
    "The Strange Case of Dr. Jekyll and Mr. Hyde",
    "The Life and Adventures of Robinson Crusoe",
    "The Great Gatsby",
    "The Adventures of Tom Sawyer, Complete",
    "Wuthering Heights",
    "Frankenstein; Or, The Modern Prometheus",
    "A Tale of Two Cities",
]

# 마이그레이션 디렉토리
migration_dir = Path(__file__).parent.parent.parent.parent / "gajiBE" / "src" / "main" / "resources" / "db" / "migration"

v48_file = migration_dir / "V48__update_character_personas.sql"
v49_file = migration_dir / "V49__update_character_relationships.sql"

# 파일 읽기
with open(v48_file, 'r', encoding='utf-8') as f:
    v48_content = f.read()

with open(v49_file, 'r', encoding='utf-8') as f:
    v49_content = f.read()

print('='*70)
print('마이그레이션 검증 결과 (108_The Return of Sherlock Holmes 제외)')
print('='*70)
print(f'\n총 확인할 소설: {len(novels_from_origin)}개\n')
print('범례: ✅ V48 (캐릭터 페르소나) | ✅ V49 (캐릭터 관계)\n')

missing_in_v48 = []
missing_in_v49 = []

for novel in sorted(novels_from_origin):
    # WHERE n.title = 'novel_title' 패턴 찾기
    search_pattern = f"WHERE n.title = '{novel}'"
    in_v48 = search_pattern in v48_content
    in_v49 = search_pattern in v49_content
    
    status_48 = '✅' if in_v48 else '❌'
    status_49 = '✅' if in_v49 else '❌'
    
    print(f'{status_48} {status_49}  {novel}')
    
    if not in_v48:
        missing_in_v48.append(novel)
    if not in_v49:
        missing_in_v49.append(novel)

print('\n' + '='*70)
print('요약')
print('='*70)
print(f'V48 (캐릭터 페르소나): {len(novels_from_origin) - len(missing_in_v48)}/{len(novels_from_origin)} 포함')
print(f'V49 (캐릭터 관계): {len(novels_from_origin) - len(missing_in_v49)}/{len(novels_from_origin)} 포함')

if missing_in_v48:
    print(f'\n❌ V48에 누락된 소설 ({len(missing_in_v48)}개):')
    for novel in missing_in_v48:
        print(f'   - {novel}')

if missing_in_v49:
    print(f'\n❌ V49에 누락된 소설 ({len(missing_in_v49)}개):')
    for novel in missing_in_v49:
        print(f'   - {novel}')

if not missing_in_v48 and not missing_in_v49:
    print('\n✅ 모든 소설이 정상적으로 마이그레이션되었습니다!')
else:
    print('\n⚠️  일부 소설이 누락되었습니다. 위 목록을 확인하세요.')
    sys.exit(1)




