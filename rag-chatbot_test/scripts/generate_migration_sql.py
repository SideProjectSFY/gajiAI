"""
캐릭터 데이터 → PostgreSQL 마이그레이션 SQL 생성 스크립트

사용법:
    python scripts/generate_migration_sql.py
"""

import json
from pathlib import Path
from typing import Dict, Any, List


def escape_sql_string(text: str) -> str:
    """SQL 문자열 이스케이프 처리"""
    if not text:
        return ""
    # $ 기호를 사용한 dollar-quoted string으로 처리
    return text.replace("$", "$$")


def generate_character_personas_migration(
    characters_dir: Path,
    output_file: Path
) -> None:
    """캐릭터 페르소나 마이그레이션 SQL 생성"""
    
    sql_lines = [
        "-- V48: Update character personas from AI chatbot JSON files",
        "-- Adds/updates persona and speaking style data for 26 novels",
        "",
    ]
    
    # novels 테이블의 title과 JSON 파일 매핑
    novel_title_mapping = {
        "The_Adventures_of_Sherlock_Holmes.json": "The Adventures of Sherlock Holmes",
        "Pride_and_Prejudice.json": "Pride and Prejudice",
        "The_Great_Gatsby.json": "The Great Gatsby",
        "Romeo_and_Juliet.json": "Romeo and Juliet",
        "The_Adventures_of_Tom_Sawyer_Complete.json": "The Adventures of Tom Sawyer, Complete",
        "Frankenstein_Or_The_Modern_Prometheus.json": "Frankenstein; Or, The Modern Prometheus",
        "The_Return_of_Sherlock_Holmes.json": "The Return of Sherlock Holmes",
        "Great_Expectations.json": "Great Expectations",
        "The_Time_Machine.json": "The Time Machine",
        "Twenty_Thousand_Leagues_under_the_Sea.json": "Twenty Thousand Leagues under the Sea",
        "The_War_of_the_Worlds.json": "The War of the Worlds",
        "The_Hound_of_the_Baskervilles.json": "The Hound of the Baskervilles",
        "The_Moonstone.json": "The Moonstone",
        "Sense_and_Sensibility.json": "Sense and Sensibility",
        "Wuthering_Heights.json": "Wuthering Heights",
        "Jane_Eyre_An_Autobiography.json": "Jane Eyre: An Autobiography",
        "Treasure_Island.json": "Treasure Island",
        "The_Three_Musketeers.json": "The Three Musketeers",
        "The_Life_and_Adventures_of_Robinson_Crusoe.json": "The Life and Adventures of Robinson Crusoe",
        "Dracula.json": "Dracula",
        "A_Tale_of_Two_Cities.json": "A Tale of Two Cities",
        "The_Count_of_Monte_Cristo_Illustrated.json": "The Count of Monte Cristo, Illustrated",
        "Emma.json": "Emma",
        "Moby-Dick_or_The_Whale.json": "Moby Dick; Or, The Whale",
        "Alice_s_Adventures_in_Wonderland.json": "Alice's Adventures in Wonderland",
        "The_Strange_Case_of_Dr_Jekyll_and_Mr_Hyde.json": "The Strange Case of Dr. Jekyll and Mr. Hyde",
    }
    
    character_files = sorted(characters_dir.glob("*.json"))
    
    for char_file in character_files:
        if char_file.name not in novel_title_mapping:
            print(f"⚠️  매핑 정보 없음: {char_file.name}")
            continue
        
        novel_title = novel_title_mapping[char_file.name]
        
        with open(char_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        book_title = data.get("book_title", "")
        author = data.get("author", "")
        characters = data.get("characters", [])
        
        if not characters:
            continue
        
        sql_lines.append(f"-- ============================================")
        sql_lines.append(f"-- {book_title}")
        sql_lines.append(f"-- Author: {author}")
        sql_lines.append(f"-- ============================================")
        
        for idx, char in enumerate(characters, 1):
            char_name = char.get("character_name", "")
            persona = escape_sql_string(char.get("persona", ""))
            persona_en = escape_sql_string(char.get("persona_en", ""))
            persona_ko = escape_sql_string(char.get("persona_ko", ""))
            speaking_style = escape_sql_string(char.get("speaking_style", ""))
            speaking_style_en = escape_sql_string(char.get("speaking_style_en", ""))
            speaking_style_ko = escape_sql_string(char.get("speaking_style_ko", ""))
            
            # vectordb_character_id 생성 (소문자 + 밑줄)
            vectordb_id = char_name.lower().replace(" ", "_").replace(".", "")
            vectordb_id = f"{vectordb_id}_{book_title[:20].lower().replace(' ', '_')}"
            
            sql_lines.append(f"")
            sql_lines.append(f"INSERT INTO characters (")
            sql_lines.append(f"    novel_id, common_name, is_main_character,")
            sql_lines.append(f"    persona, persona_en, persona_ko,")
            sql_lines.append(f"    speaking_style, speaking_style_en, speaking_style_ko,")
            sql_lines.append(f"    vectordb_character_id")
            sql_lines.append(f")")
            sql_lines.append(f"SELECT")
            sql_lines.append(f"    n.id,")
            sql_lines.append(f"    '{char_name}',")
            sql_lines.append(f"    {str(idx == 1).lower()},")  # 첫 번째 캐릭터를 주인공으로 설정
            sql_lines.append(f"    $persona${persona}$persona$,")
            sql_lines.append(f"    $persona_en${persona_en}$persona_en$,")
            sql_lines.append(f"    $persona_ko${persona_ko}$persona_ko$,")
            sql_lines.append(f"    $style${speaking_style}$style$,")
            sql_lines.append(f"    $style_en${speaking_style_en}$style_en$,")
            sql_lines.append(f"    $style_ko${speaking_style_ko}$style_ko$,")
            sql_lines.append(f"    '{vectordb_id}'")
            sql_lines.append(f"FROM novels n")
            sql_lines.append(f"WHERE n.title = '{novel_title}'")
            sql_lines.append(f"ON CONFLICT (novel_id, common_name) DO UPDATE SET")
            sql_lines.append(f"    persona = EXCLUDED.persona,")
            sql_lines.append(f"    persona_en = EXCLUDED.persona_en,")
            sql_lines.append(f"    persona_ko = EXCLUDED.persona_ko,")
            sql_lines.append(f"    speaking_style = EXCLUDED.speaking_style,")
            sql_lines.append(f"    speaking_style_en = EXCLUDED.speaking_style_en,")
            sql_lines.append(f"    speaking_style_ko = EXCLUDED.speaking_style_ko,")
            sql_lines.append(f"    updated_at = CURRENT_TIMESTAMP;")
        
        sql_lines.append("")
    
    # 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
    
    print(f"✅ 생성 완료: {output_file}")
    print(f"   처리된 작품: {len(character_files)}개")


def generate_character_relationships_migration(
    char_graph_dir: Path,
    output_file: Path
) -> None:
    """캐릭터 관계 마이그레이션 SQL 생성"""
    
    sql_lines = [
        "-- V49: Add character relationships from char_graph JSON files",
        "-- Populates character_relationships table with graph data",
        "",
    ]
    
    # 모든 JSON 파일을 자동으로 매핑 (파일명에서 숫자_ 제거)
    def get_novel_title_from_filename(filename: str) -> str:
        """파일명에서 소설 제목 추출"""
        # 숫자_를 제거하고 확장자 제거
        name = filename.split('_', 1)[-1].replace('.json', '')
        
        # 특수 문자 변환
        title_mapping = {
            "The Adventures of Sherlock Holmes": "The Adventures of Sherlock Holmes",
            "Pride and Prejudice": "Pride and Prejudice",
            "The Great Gatsby": "The Great Gatsby",
            "Romeo and Juliet": "Romeo and Juliet",
            "The Adventures of Tom Sawyer_ Complete": "The Adventures of Tom Sawyer, Complete",
            "Frankenstein_ Or_ The Modern Prometheus": "Frankenstein; Or, The Modern Prometheus",
            "The Return of Sherlock Holmes": "The Return of Sherlock Holmes",
            "Great Expectations": "Great Expectations",
            "The Time Machine": "The Time Machine",
            "Twenty Thousand Leagues under the Sea": "Twenty Thousand Leagues under the Sea",
            "The War of the Worlds": "The War of the Worlds",
            "The Hound of the Baskervilles": "The Hound of the Baskervilles",
            "The Moonstone": "The Moonstone",
            "Sense and Sensibility": "Sense and Sensibility",
            "Wuthering Heights": "Wuthering Heights",
            "Jane Eyre_ An Autobiography": "Jane Eyre: An Autobiography",
            "Treasure Island": "Treasure Island",
            "The Three Musketeers": "The Three Musketeers",
            "The Life and Adventures of Robinson Crusoe": "The Life and Adventures of Robinson Crusoe",
            "Dracula": "Dracula",
            "A Tale of Two Cities": "A Tale of Two Cities",
            "The Count of Monte Cristo_ Illustrated": "The Count of Monte Cristo, Illustrated",
            "Emma": "Emma",
            "Moby-Dick_ or_ The Whale": "Moby Dick; Or, The Whale",
            "Alice_s Adventures in Wonderland": "Alice's Adventures in Wonderland",
            "The Strange Case of Dr_ Jekyll and Mr_ Hyde": "The Strange Case of Dr. Jekyll and Mr. Hyde",
        }
        
        return title_mapping.get(name, name)
    
    char_graph_files = sorted(char_graph_dir.glob("*.json"))
    
    for graph_file in char_graph_files:
        novel_title = get_novel_title_from_filename(graph_file.name)
        
        with open(graph_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        characters = data.get("characters", [])
        relations = data.get("relations", [])
        
        if not relations:
            continue
        
        sql_lines.append(f"-- ============================================")
        sql_lines.append(f"-- {novel_title}")
        sql_lines.append(f"-- Characters: {len(characters)}, Relationships: {len(relations)}")
        sql_lines.append(f"-- ============================================")
        sql_lines.append(f"")
        
        # 캐릭터 ID 매핑 (char_graph_id -> common_name)
        char_id_to_name = {char["id"]: char["common_name"] for char in characters}
        
        for edge in relations:
            id1 = edge.get("id1")
            id2 = edge.get("id2")
            weight = edge.get("weight", 1.0)
            
            # relation 배열을 설명으로 변환
            relation_list = edge.get("relation", [])
            if isinstance(relation_list, list):
                description = ", ".join(relation_list)
            else:
                description = str(relation_list)
            description = escape_sql_string(description)
            
            if id1 not in char_id_to_name or id2 not in char_id_to_name:
                continue
            
            name1 = char_id_to_name[id1]
            name2 = char_id_to_name[id2]
            
            sql_lines.append(f"INSERT INTO character_relationships (")
            sql_lines.append(f"    novel_id, source_character_id, target_character_id,")
            sql_lines.append(f"    weight, description")
            sql_lines.append(f")")
            sql_lines.append(f"SELECT")
            sql_lines.append(f"    n.id,")
            sql_lines.append(f"    c1.id,")
            sql_lines.append(f"    c2.id,")
            sql_lines.append(f"    {weight},")
            sql_lines.append(f"    $desc${description}$desc$")
            sql_lines.append(f"FROM novels n")
            sql_lines.append(f"JOIN characters c1 ON c1.novel_id = n.id AND c1.common_name = '{name1}'")
            sql_lines.append(f"JOIN characters c2 ON c2.novel_id = n.id AND c2.common_name = '{name2}'")
            sql_lines.append(f"WHERE n.title = '{novel_title}'")
            sql_lines.append(f"ON CONFLICT (source_character_id, target_character_id) DO UPDATE SET")
            sql_lines.append(f"    weight = EXCLUDED.weight,")
            sql_lines.append(f"    description = EXCLUDED.description,")
            sql_lines.append(f"    updated_at = CURRENT_TIMESTAMP;")
            sql_lines.append(f"")
        
        sql_lines.append("")
    
    # 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
    
    print(f"✅ 생성 완료: {output_file}")
    print(f"   처리된 작품: {len(char_graph_files)}개")


def main():
    project_root = Path(__file__).parent.parent
    
    # 경로 설정
    characters_dir = project_root / "data" / "characters"
    char_graph_dir = project_root / "data" / "char_graph"
    migration_dir = project_root.parent.parent / "gajiBE" / "src" / "main" / "resources" / "db" / "migration"
    
    # 디렉토리 존재 확인
    if not characters_dir.exists():
        print(f"❌ characters 디렉토리가 없습니다: {characters_dir}")
        return
    
    if not char_graph_dir.exists():
        print(f"❌ char_graph 디렉토리가 없습니다: {char_graph_dir}")
        return
    
    if not migration_dir.exists():
        print(f"❌ migration 디렉토리가 없습니다: {migration_dir}")
        return
    
    print("="*60)
    print("캐릭터 데이터 마이그레이션 SQL 생성")
    print("="*60)
    
    # V48: 캐릭터 페르소나 마이그레이션
    print("\n[1/2] 캐릭터 페르소나 마이그레이션 생성 중...")
    generate_character_personas_migration(
        characters_dir=characters_dir,
        output_file=migration_dir / "V48__update_character_personas.sql"
    )
    
    # V49: 캐릭터 관계 마이그레이션
    print("\n[2/2] 캐릭터 관계 마이그레이션 생성 중...")
    generate_character_relationships_migration(
        char_graph_dir=char_graph_dir,
        output_file=migration_dir / "V49__update_character_relationships.sql"
    )
    
    print("\n" + "="*60)
    print("✅ 마이그레이션 파일 생성 완료")
    print("="*60)
    print(f"\n생성된 파일:")
    print(f"  - {migration_dir / 'V48__update_character_personas.sql'}")
    print(f"  - {migration_dir / 'V49__update_character_relationships.sql'}")
    print(f"\n다음 단계:")
    print(f"  1. 생성된 SQL 파일 확인")
    print(f"  2. Spring Boot 애플리케이션 재시작 (Flyway가 자동 실행)")


if __name__ == "__main__":
    main()

