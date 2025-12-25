"""
마이그레이션 파일 통계 출력
"""

import re
from pathlib import Path

# 마이그레이션 디렉토리
migration_dir = Path(__file__).parent.parent.parent.parent / "gajiBE" / "src" / "main" / "resources" / "db" / "migration"

v48_file = migration_dir / "V48__update_character_personas.sql"
v49_file = migration_dir / "V49__update_character_relationships.sql"

# V48 통계
with open(v48_file, 'r', encoding='utf-8') as f:
    v48 = f.read()

# V49 통계
with open(v49_file, 'r', encoding='utf-8') as f:
    v49 = f.read()

# V48: INSERT 문 카운트
v48_inserts = len(re.findall(r'INSERT INTO characters', v48))

# V49: INSERT 문 카운트
v49_inserts = len(re.findall(r'INSERT INTO character_relationships', v49))

# V48: 소설별 캐릭터 수
v48_novels = re.findall(r'-- ============================================\n-- (.+?)\n-- Author:', v48)

# V49: 소설별 관계 수
v49_novels_info = re.findall(r'-- ============================================\n-- (.+?)\n-- Characters: (\d+), Relationships: (\d+)', v49)

print('='*70)
print('Migration Files - Detailed Statistics')
print('='*70)

print('\nV48__update_character_personas.sql')
print('-'*70)
print(f'Total INSERT statements: {v48_inserts}')
print(f'Total novels: {len(v48_novels)}')
print(f'Average characters per novel: {v48_inserts / len(v48_novels):.1f}')

print('\nV49__update_character_relationships.sql')
print('-'*70)
print(f'Total INSERT statements: {v49_inserts}')
print(f'Total novels: {len(v49_novels_info)}')
if v49_novels_info:
    total_chars = sum(int(info[1]) for info in v49_novels_info)
    total_rels = sum(int(info[2]) for info in v49_novels_info)
    print(f'Total characters: {total_chars}')
    print(f'Total relationships: {total_rels}')
    print(f'Average relationships per novel: {total_rels / len(v49_novels_info):.1f}')

print('\nTop 10 Novels by Relationship Count')
print('-'*70)
sorted_novels = sorted(v49_novels_info, key=lambda x: int(x[2]), reverse=True)[:10]
for idx, (novel, chars, rels) in enumerate(sorted_novels, 1):
    print(f'{idx:2}. {novel:45s} {chars:>3} chars  {rels:>4} rels')

print('\nBottom 5 Novels by Relationship Count')
print('-'*70)
sorted_novels_asc = sorted(v49_novels_info, key=lambda x: int(x[2]))[:5]
for idx, (novel, chars, rels) in enumerate(sorted_novels_asc, 1):
    print(f'{idx:2}. {novel:45s} {chars:>3} chars  {rels:>4} rels')

# 파일 크기
v48_size = v48_file.stat().st_size / 1024
v49_size = v49_file.stat().st_size / 1024

print('\nFile Sizes')
print('-'*70)
print(f'V48: {v48_size:.2f} KB ({v48_file.stat().st_size:,} bytes)')
print(f'V49: {v49_size:.2f} KB ({v49_file.stat().st_size:,} bytes)')
print(f'Total: {v48_size + v49_size:.2f} KB')




