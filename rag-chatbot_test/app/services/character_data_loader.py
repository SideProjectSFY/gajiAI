"""
캐릭터 데이터 로더

캐릭터 정보 로드 및 조회 기능을 제공하는 유틸리티 클래스
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class CharacterDataLoader:
    """캐릭터 데이터 로드 전용 유틸리티"""
    
    @staticmethod
    def load_characters(path: str = None) -> List[Dict]:
        """캐릭터 정보 로드
        
        우선순위:
        1. data/characters/ 폴더의 책별 JSON 파일들 (새 구조)
        2. data/characters.json (레거시, 호환성 유지)
        """
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        characters_dir = project_root / "data" / "characters"
        legacy_file = project_root / "data" / "characters.json"
        
        all_characters = []
        
        # 1. 새 구조: data/characters/ 폴더의 모든 JSON 파일 로드
        if characters_dir.exists() and characters_dir.is_dir():
            json_files = list(characters_dir.glob("*.json"))
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        book_data = json.load(f)
                        book_title = book_data.get('book_title', '')
                        author = book_data.get('author', '')
                        
                        # 각 캐릭터에 book_title과 author 추가
                        for char in book_data.get('characters', []):
                            char['book_title'] = book_title
                            char['author'] = author
                            all_characters.append(char)
                except Exception:
                    # 파일 읽기 실패 시 건너뛰기
                    continue
        
        # 2. 레거시 구조: data/characters.json 파일 로드 (호환성)
        if not all_characters and legacy_file.exists():
            try:
                with open(legacy_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_characters = data.get('characters', [])
            except Exception:
                pass
        
        return all_characters
    
    @staticmethod
    def get_character_info(characters: List[Dict], character_name: str, book_title: Optional[str] = None) -> Optional[Dict]:
        """특정 캐릭터 정보 가져오기
        
        Args:
            characters: 캐릭터 목록
            character_name: 캐릭터 이름
            book_title: 책 제목 (선택, 제공되면 같은 책의 캐릭터만 검색)
        
        Returns:
            캐릭터 정보 딕셔너리 또는 None
        """
        for char in characters:
            if char['character_name'].lower() == character_name.lower():
                # book_title이 제공되면 일치하는지 확인
                if book_title is None or char['book_title'].lower() == book_title.lower():
                    return char
        return None
    
    @staticmethod
    def get_available_characters(characters: List[Dict]) -> List[Dict]:
        """사용 가능한 캐릭터 목록 반환"""
        return [
            {
                'character_name': c['character_name'],
                'book_title': c['book_title'],
                'author': c['author']
            }
            for c in characters
        ]
    
    @staticmethod
    def get_other_main_character(
        characters: List[Dict], 
        current_character_name: str, 
        book_title: str
    ) -> Optional[Dict]:
        """같은 책의 다른 주인공 찾기
        
        Args:
            characters: 캐릭터 목록
            current_character_name: 현재 선택된 캐릭터 이름
            book_title: 책 제목
        
        Returns:
            다른 주인공 정보 딕셔너리 또는 None (없으면)
        """
        # 같은 책의 다른 캐릭터 찾기
        # (각 책마다 보통 2명의 주인공이 있으므로)
        other_characters = [
            char for char in characters
            if (char.get('book_title', '').lower() == book_title.lower() and
                char.get('character_name', '').lower() != current_character_name.lower())
        ]
        
        # 첫 번째 다른 캐릭터 반환 (보통 2명이므로)
        return other_characters[0] if other_characters else None



