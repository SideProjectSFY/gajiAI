"""
캐릭터 페르소나 자동 생성 스크립트

File Search를 사용하여 origin_txt의 원본 텍스트를 분석하고,
char_graph의 인물 관계도를 분석하여 id 1, 2인 캐릭터의
페르소나와 speaking_style을 생성합니다.
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from google import genai
from google.genai.types import Tool, FileSearch

# 프로젝트 루트를 Python 경로에 추가
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from app.services.api_key_manager import get_api_key_manager


class CharacterPersonaGenerator:
    """캐릭터 페르소나 생성기"""
    
    def __init__(self):
        """초기화"""
        self.api_key_manager = get_api_key_manager()
        self.api_key = self.api_key_manager.get_current_key()
        self.client = genai.Client(api_key=self.api_key)
        
        # 프로젝트 루트 경로
        self.project_root = project_root
        
        # 데이터 디렉토리 경로
        self.data_dir = self.project_root / "data"
        self.origin_txt_dir = self.data_dir / "origin_txt"
        self.char_graph_dir = self.data_dir / "char_graph"
        self.characters_dir = self.data_dir / "characters"
        
        # characters 디렉토리 생성
        self.characters_dir.mkdir(parents=True, exist_ok=True)
        
        # File Search Store 정보 로드
        self._load_store_info()
    
    def _load_store_info(self):
        """File Search Store 정보 로드"""
        # 현재 API 키 인덱스에 맞는 Store 정보 파일 찾기
        current_key_index = self.api_key_manager.current_key_index
        store_info_path = self.data_dir / f"file_search_store_info_key{current_key_index + 1}.json"
        
        if not store_info_path.exists():
            store_info_path = self.data_dir / "file_search_store_info.json"
        
        try:
            with open(store_info_path, 'r', encoding='utf-8') as f:
                store_info = json.load(f)
                self.store_name = store_info.get('store_name')
        except FileNotFoundError:
            self.store_name = None
            print(f"⚠️ File Search Store 정보를 찾을 수 없습니다: {store_info_path}")
            print("   'py scripts/setup_file_search.py'를 실행하여 Store를 설정하세요.")
    
    def _call_llm_with_file_search(self, prompt: str, system_instruction: str = None) -> str:
        """
        File Search를 사용하여 LLM 호출
        
        Args:
            prompt: 프롬프트
            system_instruction: 시스템 지시사항 (None이면 기본값 사용)
        
        Returns:
            LLM 응답 텍스트
        """
        max_retries = len(self.api_key_manager.api_keys)
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # 현재 API 키로 클라이언트 생성
                current_key = self.api_key_manager.get_current_key()
                
                # API 키가 변경되었으면 클라이언트 재생성 및 Store 정보 다시 로드
                if current_key != self.api_key:
                    self.api_key = current_key
                    self.client = genai.Client(api_key=self.api_key)
                    self._load_store_info()
                
                if not self.store_name:
                    raise ValueError("File Search Store가 설정되지 않았습니다.")
                
                # 기본 시스템 지시사항
                if system_instruction is None:
                    system_instruction = """You are a literary character analyst specializing in creating detailed character personas and speaking styles based on original text sources.
You MUST use File Search to find information from the original text before answering.
Be thorough, accurate, and base your analysis on concrete evidence from the source material."""
                
                # API 호출
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[{"role": "user", "parts": [{"text": prompt}]}],
                    config={
                        "system_instruction": system_instruction,
                        "tools": [
                            Tool(
                                file_search=FileSearch(
                                    file_search_store_names=[self.store_name]
                                )
                            )
                        ],
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "max_output_tokens": 4096
                    }
                )
                
                # 응답 추출
                response_text = ""
                if hasattr(response, 'text') and response.text:
                    response_text = response.text
                elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    response_text += part.text
                
                if not response_text or not response_text.strip():
                    raise ValueError("LLM 응답이 비어있습니다.")
                
                return response_text.strip()
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # 할당량 에러 처리
                if self.api_key_manager._is_quota_error(e):
                    if attempt < max_retries - 1:
                        if self.api_key_manager.switch_to_next_key():
                            print(f"  ⚠️ API 키 할당량 초과. 다음 키로 전환...")
                            time.sleep(2)
                            continue
                
                # Store 접근 권한 에러
                if 'PERMISSION_DENIED' in error_str or 'file search store' in error_str.lower():
                    raise ValueError(f"Store 접근 권한이 없습니다: {str(e)}")
                
                # 마지막 시도면 에러 전파
                if attempt >= max_retries - 1:
                    raise Exception(f"LLM 호출 실패: {str(e)}") from last_error
                
                time.sleep(1)
        
        raise Exception(f"모든 API 키에서 실패했습니다: {str(last_error)}")
    
    def load_books_info(self) -> List[Dict]:
        """saved_books_info.json에서 책 목록 로드"""
        books_info_path = self.origin_txt_dir / "saved_books_info.json"
        
        try:
            with open(books_info_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('books', [])
        except FileNotFoundError:
            print(f"❌ 책 정보 파일을 찾을 수 없습니다: {books_info_path}")
            return []
    
    def load_char_graph(self, book_title: str) -> Optional[Dict]:
        """char_graph JSON 파일 로드"""
        # 책 제목으로 파일명 생성 (gutenberg_id는 saved_books_info에서 가져와야 함)
        # 일단 모든 JSON 파일을 검색
        json_files = list(self.char_graph_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 파일명에서 책 제목 추출하여 매칭 (대략적)
                    # 정확한 매칭을 위해 saved_books_info의 gutenberg_id 사용
                    return data
            except Exception as e:
                continue
        
        return None
    
    def find_char_graph_file(self, gutenberg_id: int) -> Optional[Path]:
        """gutenberg_id로 char_graph 파일 찾기"""
        # 파일명 패턴: {gutenberg_id}_{book_title}.json
        pattern = f"{gutenberg_id}_*.json"
        matches = list(self.char_graph_dir.glob(pattern))
        
        if matches:
            return matches[0]
        return None
    
    def extract_characters_by_id(self, char_graph_data: Dict, target_ids: List[int] = [1, 2]) -> List[Dict]:
        """char_graph에서 id가 target_ids에 해당하는 캐릭터 추출"""
        characters = []
        
        for char in char_graph_data.get('characters', []):
            if char.get('id') in target_ids:
                characters.append(char)
        
        # id 순서로 정렬
        characters.sort(key=lambda x: x.get('id', 0))
        
        return characters
    
    def generate_persona(self, character: Dict, book_title: str, author: str, language: str = "en") -> str:
        """페르소나 생성
        
        Args:
            character: 캐릭터 정보
            book_title: 책 제목
            author: 저자
            language: 생성 언어 ("en" 또는 "ko")
        """
        character_name = character.get('common_name', '')
        description = character.get('description', '')
        names = character.get('names', [])
        
        if language == "ko":
            prompt = f"""당신은 문학 작품의 캐릭터 분석 전문가입니다.

다음 정보를 바탕으로 {character_name}의 상세한 페르소나를 한국어로 작성하세요:

【중요】반드시 File Search를 사용하여 원본 텍스트에서 정보를 찾아야 합니다.

【File Search를 사용하여 찾을 정보】
1. {character_name}의 주요 대사 샘플 (10-20개)
2. {character_name}이 등장하는 주요 사건/장면 요약
3. {character_name}의 행동 패턴 및 결정
4. 서술자/다른 인물의 {character_name}에 대한 평가

【인물 관계도 분석】
- 캐릭터 설명: {description}
- 캐릭터 이름 변형: {', '.join(names[:10])}

【책 정보】
- 책 제목: {book_title}
- 저자: {author}

【요구사항】
1. File Search를 먼저 사용하여 원본 텍스트에서 구체적 증거를 찾으세요
2. 캐릭터의 성격, 가치관, 동기, 배경을 종합적으로 분석
3. 원본 텍스트의 구체적 증거를 바탕으로 작성
4. 인물 관계도에서 파악한 관계를 반영
5. 2인칭 "당신은..." 형식으로 한국어로 작성
6. 200-300단어로 작성
7. 한국어로 자연스럽고 정확하게 작성

페르소나를 한국어로 작성하세요:"""
        else:  # English
            prompt = f"""You are a literary character analyst specializing in creating detailed character personas.

Write a detailed persona for {character_name} in English based on the following information:

【IMPORTANT】You MUST use File Search to find information from the original text.

【Information to find using File Search】
1. Key dialogue samples from {character_name} (10-20 examples)
2. Summary of major events/scenes where {character_name} appears
3. {character_name}'s behavioral patterns and decisions
4. Narrator/other characters' evaluations of {character_name}

【Character Graph Analysis】
- Character description: {description}
- Character name variations: {', '.join(names[:10])}

【Book Information】
- Book title: {book_title}
- Author: {author}

【Requirements】
1. First use File Search to find concrete evidence from the original text
2. Comprehensively analyze the character's personality, values, motivations, and background
3. Write based on concrete evidence from the original text
4. Reflect relationships identified in the character graph
5. Write in second person "You are..." format
6. Write 200-300 words
7. Write in clear, natural English

Write the persona in English:"""
        
        try:
            system_instruction = f"""You are a literary character analyst specializing in creating detailed character personas based on original text sources.
You MUST use File Search to find information from the original text before answering.
Be thorough, accurate, and base your analysis on concrete evidence from the source material.
Write in {language.upper()}."""
            
            persona = self._call_llm_with_file_search(prompt, system_instruction)
            return persona
        except Exception as e:
            print(f"    ❌ 페르소나 생성 실패 ({language}): {str(e)}")
            return ""
    
    def generate_speaking_style(self, character: Dict, book_title: str, author: str, language: str = "en") -> str:
        """Speaking Style 생성
        
        Args:
            character: 캐릭터 정보
            book_title: 책 제목
            author: 저자
            language: 생성 언어 ("en" 또는 "ko")
        """
        character_name = character.get('common_name', '')
        description = character.get('description', '')
        names = character.get('names', [])
        
        if language == "ko":
            prompt = f"""다음 정보를 바탕으로 {character_name}의 말투(speaking style)를 한국어로 작성하세요:

【중요】반드시 File Search를 사용하여 원본 텍스트에서 {character_name}의 실제 대사를 찾아야 합니다.

【File Search를 사용하여 찾을 정보】
1. {character_name}의 실제 대사 샘플 (최소 10개 이상)
2. 대사의 문장 구조 분석
3. 사용하는 어휘의 특징
4. 반복되는 표현/구문

【캐릭터 정보】
- 캐릭터 설명: {description}
- 캐릭터 이름 변형: {', '.join(names[:10])}
- 책 제목: {book_title}
- 저자: {author}

【요구사항】
1. File Search를 먼저 사용하여 원본 텍스트에서 실제 대사를 찾으세요
2. 실제 대사 패턴을 반영하여 한국어로 말할 때의 말투를 구체적으로 설명
3. 시대적/사회적 배경을 고려
4. 캐릭터의 성격과 일치하는 말투로 작성
5. 한국어 특유의 표현, 어미, 존댓말/반말 수준, 문장 길이 등을 구체적으로 명시
6. 150-200단어로 작성
7. 한국어로 자연스럽고 정확하게 작성

Speaking Style을 한국어로 작성하세요:"""
        else:  # English
            prompt = f"""Write the speaking style for {character_name} in English based on the following information:

【IMPORTANT】You MUST use File Search to find {character_name}'s actual dialogue from the original text.

【Information to find using File Search】
1. Actual dialogue samples from {character_name} (at least 10 examples)
2. Analysis of sentence structure in dialogue
3. Characteristics of vocabulary used
4. Recurring expressions/phrases

【Character Information】
- Character description: {description}
- Character name variations: {', '.join(names[:10])}
- Book title: {book_title}
- Author: {author}

【Requirements】
1. First use File Search to find actual dialogue from the original text
2. Reflect actual dialogue patterns
3. Consider historical/social background
4. Match the character's personality
5. Write 150-200 words
6. Write in clear, natural English

Write the speaking style in English:"""
        
        try:
            system_instruction = f"""You are a literary character analyst specializing in analyzing speaking styles based on original text sources.
You MUST use File Search to find actual dialogue from the original text before answering.
Be thorough, accurate, and base your analysis on concrete evidence from the source material.
Write in {language.upper()}."""
            
            speaking_style = self._call_llm_with_file_search(prompt, system_instruction)
            return speaking_style
        except Exception as e:
            print(f"    ❌ Speaking Style 생성 실패 ({language}): {str(e)}")
            return ""
    
    def process_book(self, book_info: Dict) -> Optional[Dict]:
        """한 책 처리"""
        book_title = book_info.get('title', '')
        author = book_info.get('author', '')
        gutenberg_id = book_info.get('gutenberg_id')
        
        print(f"\n📖 처리 중: {book_title}")
        print(f"   저자: {author}")
        
        # char_graph 파일 찾기
        char_graph_file = self.find_char_graph_file(gutenberg_id)
        if not char_graph_file:
            print(f"   ⚠️ char_graph 파일을 찾을 수 없습니다 (gutenberg_id: {gutenberg_id})")
            return None
        
        # char_graph 데이터 로드
        try:
            with open(char_graph_file, 'r', encoding='utf-8') as f:
                char_graph_data = json.load(f)
        except Exception as e:
            print(f"   ❌ char_graph 파일 로드 실패: {str(e)}")
            return None
        
        # id 1, 2인 캐릭터 추출
        characters = self.extract_characters_by_id(char_graph_data, [1, 2])
        
        if not characters:
            print(f"   ⚠️ id 1, 2인 캐릭터를 찾을 수 없습니다")
            return None
        
        print(f"   발견된 캐릭터: {len(characters)}명")
        for char in characters:
            print(f"      - {char.get('common_name')} (id: {char.get('id')})")
        
        # 각 캐릭터에 대해 페르소나와 speaking_style 생성 (영어/한국어)
        result_characters = []
        
        for char in characters:
            character_name = char.get('common_name', '')
            print(f"\n   🎭 {character_name} 처리 중...")
            
            # 영어 페르소나 생성
            print(f"      영어 페르소나 생성 중...")
            persona_en = self.generate_persona(char, book_title, author, "en")
            time.sleep(1)  # API 호출 간격
            
            # 한국어 페르소나 생성
            print(f"      한국어 페르소나 생성 중...")
            persona_ko = self.generate_persona(char, book_title, author, "ko")
            time.sleep(1)  # API 호출 간격
            
            # 영어 Speaking Style 생성
            print(f"      영어 Speaking Style 생성 중...")
            speaking_style_en = self.generate_speaking_style(char, book_title, author, "en")
            time.sleep(1)  # API 호출 간격
            
            # 한국어 Speaking Style 생성
            print(f"      한국어 Speaking Style 생성 중...")
            speaking_style_ko = self.generate_speaking_style(char, book_title, author, "ko")
            time.sleep(1)  # API 호출 간격
            
            if persona_en and persona_ko and speaking_style_en and speaking_style_ko:
                result_characters.append({
                    "character_name": character_name,
                    "persona": persona_en,  # 기존 호환성을 위해 영어를 기본값으로
                    "persona_en": persona_en,
                    "persona_ko": persona_ko,
                    "speaking_style": speaking_style_en,  # 기존 호환성을 위해 영어를 기본값으로
                    "speaking_style_en": speaking_style_en,
                    "speaking_style_ko": speaking_style_ko
                })
                print(f"      ✅ 완료 (영어/한국어)")
            else:
                print(f"      ⚠️ 일부 정보가 누락되었습니다")
                # 부분 성공도 저장
                if persona_en or persona_ko or speaking_style_en or speaking_style_ko:
                    result_characters.append({
                        "character_name": character_name,
                        "persona": persona_en or "",
                        "persona_en": persona_en or "",
                        "persona_ko": persona_ko or "",
                        "speaking_style": speaking_style_en or "",
                        "speaking_style_en": speaking_style_en or "",
                        "speaking_style_ko": speaking_style_ko or ""
                    })
        
        if not result_characters:
            print(f"   ❌ 생성된 캐릭터가 없습니다")
            return None
        
        # 결과 구성
        result = {
            "book_title": book_title,
            "author": author,
            "characters": result_characters
        }
        
        return result
    
    def save_character_file(self, book_title: str, data: Dict):
        """캐릭터 파일 저장"""
        # 파일명 생성 (특수문자 제거)
        safe_filename = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_filename = safe_filename.replace(' ', '_')
        filepath = self.characters_dir / f"{safe_filename}.json"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"   💾 저장 완료: {filepath}")
        except Exception as e:
            print(f"   ❌ 저장 실패: {str(e)}")
    
    def process_all_books(self):
        """모든 책 처리"""
        print("=" * 60)
        print("캐릭터 페르소나 자동 생성 시작")
        print("=" * 60)
        
        # File Search Store 확인
        if not self.store_name:
            print("\n❌ File Search Store가 설정되지 않았습니다.")
            print("   'py scripts/setup_file_search.py'를 실행하여 Store를 설정하세요.")
            return
        
        print(f"\n✅ File Search Store: {self.store_name}")
        
        # 책 목록 로드
        books = self.load_books_info()
        
        if not books:
            print("\n❌ 책 정보를 찾을 수 없습니다.")
            return
        
        print(f"\n📚 총 {len(books)}권의 책을 처리합니다.\n")
        
        # 각 책 처리
        success_count = 0
        fail_count = 0
        
        for i, book in enumerate(books, 1):
            print(f"\n[{i}/{len(books)}]")
            
            try:
                result = self.process_book(book)
                
                if result:
                    self.save_character_file(book.get('title'), result)
                    success_count += 1
                else:
                    fail_count += 1
                    
            except Exception as e:
                print(f"   ❌ 처리 중 오류 발생: {str(e)}")
                fail_count += 1
            
            # 책 간 간격
            if i < len(books):
                print("\n" + "-" * 60)
                time.sleep(2)
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("처리 완료!")
        print(f"  ✅ 성공: {success_count}권")
        print(f"  ❌ 실패: {fail_count}권")
        print(f"  📁 저장 위치: {self.characters_dir}")
        print("=" * 60)


def main():
    """메인 함수"""
    try:
        generator = CharacterPersonaGenerator()
        generator.process_all_books()
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

