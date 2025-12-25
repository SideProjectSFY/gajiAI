"""
마이그레이션 중복 확인
V46/V47 (기존) vs V48/V49 (새로 생성)
"""

import re
from pathlib import Path

migration_dir = Path(__file__).parent.parent.parent.parent / "gajiBE" / "src" / "main" / "resources" / "db" / "migration"

# 파일 읽기
with open(migration_dir / "V46__add_character_data.sql", 'r', encoding='utf-8') as f:
    v46 = f.read()

with open(migration_dir / "V47__add_character_relationships.sql", 'r', encoding='utf-8') as f:
    v47 = f.read()

with open(migration_dir / "V48__update_character_personas.sql", 'r', encoding='utf-8') as f:
    v48 = f.read()

with open(migration_dir / "V49__update_character_relationships.sql", 'r', encoding='utf-8') as f:
    v49 = f.read()

# 소설 제목 추출
v46_novels = set(re.findall(r"WHERE n\.title = '(.+?)'", v46))
v47_novels = set(re.findall(r"WHERE n\.title = '(.+?)'", v47))
v48_novels = set(re.findall(r"WHERE n\.title = '(.+?)'", v48))
v49_novels = set(re.findall(r"WHERE n\.title = '(.+?)'", v49))

print('='*70)
print('Migration Files Overlap Analysis')
print('='*70)

print('\nV46__add_character_data.sql (OLD)')
print('-'*70)
print(f'Novels: {len(v46_novels)}')
for novel in sorted(v46_novels):
    print(f'  - {novel}')

print('\nV47__add_character_relationships.sql (OLD)')
print('-'*70)
print(f'Novels: {len(v47_novels)}')
for novel in sorted(v47_novels):
    print(f'  - {novel}')

print('\nV48__update_character_personas.sql (NEW)')
print('-'*70)
print(f'Novels: {len(v48_novels)}')

print('\nV49__update_character_relationships.sql (NEW)')
print('-'*70)
print(f'Novels: {len(v49_novels)}')

# 중복 확인
overlap_46_48 = v46_novels & v48_novels
overlap_47_49 = v47_novels & v49_novels

print('\n' + '='*70)
print('Overlap Analysis')
print('='*70)

print(f'\nV46 and V48 overlap: {len(overlap_46_48)} novels')
if overlap_46_48:
    for novel in sorted(overlap_46_48):
        print(f'  - {novel}')
    print('\nWARNING: These novels exist in both V46 and V48!')
    print('V48 uses "ON CONFLICT ... DO UPDATE", so it will overwrite V46 data.')

print(f'\nV47 and V49 overlap: {len(overlap_47_49)} novels')
if overlap_47_49:
    for novel in sorted(overlap_47_49):
        print(f'  - {novel}')
    print('\nWARNING: These novels exist in both V47 and V49!')
    print('V49 uses "ON CONFLICT ... DO UPDATE", so it will overwrite V47 data.')

# V48/V49에만 있는 소설 (새로 추가된 것)
only_in_v48 = v48_novels - v46_novels
only_in_v49 = v49_novels - v47_novels

print(f'\nOnly in V48 (new characters): {len(only_in_v48)} novels')
if only_in_v48:
    for novel in sorted(only_in_v48):
        print(f'  - {novel}')

print(f'\nOnly in V49 (new relationships): {len(only_in_v49)} novels')
if only_in_v49:
    for novel in sorted(only_in_v49):
        print(f'  - {novel}')

print('\n' + '='*70)
print('Summary')
print('='*70)
print(f'V46 (old) novels: {len(v46_novels)}')
print(f'V48 (new) novels: {len(v48_novels)}')
print(f'Overlap: {len(overlap_46_48)}')
print(f'New in V48: {len(only_in_v48)}')
print()
print(f'V47 (old) novels: {len(v47_novels)}')
print(f'V49 (new) novels: {len(v49_novels)}')
print(f'Overlap: {len(overlap_47_49)}')
print(f'New in V49: {len(only_in_v49)}')




