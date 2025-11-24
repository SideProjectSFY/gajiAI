#!/usr/bin/env python
"""
VectorDB Dataset Import Script

Pre-processed Project Gutenberg 데이터셋을 ChromaDB/Pinecone에 임포트합니다.
5개의 컬렉션(novel_passages, characters, locations, events, themes)을 생성하고
PostgreSQL 메타데이터를 Spring Boot API를 통해 생성합니다.

사용법:
    python scripts/import_dataset.py \
        --dataset-path /path/to/gutenberg_dataset \
        --vectordb chromadb \
        --vectordb-host localhost:8001 \
        --spring-boot-api http://localhost:8080
"""

import argparse
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pandas as pd
except ImportError:
    print("❌ pandas 라이브러리가 설치되지 않았습니다.")
    print("설치: pip install pandas")
    sys.exit(1)

try:
    import chromadb
except ImportError:
    print("❌ chromadb 라이브러리가 설치되지 않았습니다.")
    print("설치: pip install chromadb")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("❌ httpx 라이브러리가 설치되지 않았습니다.")
    print("설치: pip install httpx")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    # tqdm이 없으면 간단한 대체 구현 사용
    def tqdm(iterable, desc="", total=None):
        """Simple tqdm fallback"""
        for i, item in enumerate(iterable):
            if total:
                print(f"\r{desc}: {i+1}/{total}", end="", flush=True)
            yield item
        print()


@dataclass
class ImportStats:
    """임포트 통계"""
    novels_count: int = 0
    passages_count: int = 0
    characters_count: int = 0
    locations_count: int = 0
    events_count: int = 0
    themes_count: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class DatasetValidator:
    """데이터셋 구조 및 무결성 검증"""

    REQUIRED_FILES = ["novels.json"]
    OPTIONAL_DIRS = ["passages", "characters", "locations", "events", "themes"]
    EMBEDDING_DIM = 768  # Gemini Embedding API 차원

    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)

    def validate(self) -> Dict[str, Any]:
        """
        데이터셋 검증 수행

        Returns:
            검증 결과 dict
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }

        # 1. 필수 파일 확인
        for required_file in self.REQUIRED_FILES:
            file_path = self.dataset_path / required_file
            if not file_path.exists():
                result["valid"] = False
                result["errors"].append(f"필수 파일 없음: {required_file}")

        # 2. 선택 디렉토리 확인
        for optional_dir in self.OPTIONAL_DIRS:
            dir_path = self.dataset_path / optional_dir
            if dir_path.exists():
                result["stats"][optional_dir] = self._count_files(dir_path)
            else:
                result["warnings"].append(f"선택 디렉토리 없음: {optional_dir}")

        # 3. novels.json 내용 검증
        novels_path = self.dataset_path / "novels.json"
        if novels_path.exists():
            novels_result = self._validate_novels(novels_path)
            result["stats"]["novels"] = novels_result["count"]
            result["errors"].extend(novels_result["errors"])
            if novels_result["errors"]:
                result["valid"] = False

        # 4. 임베딩 차원 검증 (샘플)
        passages_dir = self.dataset_path / "passages"
        if passages_dir.exists():
            embedding_result = self._validate_embeddings(passages_dir)
            result["errors"].extend(embedding_result["errors"])
            if embedding_result["errors"]:
                result["valid"] = False

        return result

    def _count_files(self, dir_path: Path) -> int:
        """디렉토리 내 파일 수 카운트"""
        return len(list(dir_path.glob("*.json"))) + len(list(dir_path.glob("*.parquet")))

    def _validate_novels(self, novels_path: Path) -> Dict:
        """novels.json 검증"""
        result = {"count": 0, "errors": []}

        try:
            with open(novels_path, "r", encoding="utf-8") as f:
                novels = json.load(f)

            if not isinstance(novels, list):
                result["errors"].append("novels.json은 배열이어야 합니다")
                return result

            result["count"] = len(novels)

            # 필수 필드 검증
            required_fields = ["id", "title", "author"]
            for i, novel in enumerate(novels):
                for field in required_fields:
                    if field not in novel:
                        result["errors"].append(
                            f"novels[{i}]: 필수 필드 '{field}' 없음"
                        )

            # 중복 ID 검사
            novel_ids = [n.get("id") for n in novels if n.get("id")]
            if len(novel_ids) != len(set(novel_ids)):
                result["errors"].append("novels.json에 중복 ID가 있습니다")

        except json.JSONDecodeError as e:
            result["errors"].append(f"novels.json JSON 파싱 오류: {e}")
        except Exception as e:
            result["errors"].append(f"novels.json 읽기 오류: {e}")

        return result

    def _validate_embeddings(self, passages_dir: Path) -> Dict:
        """임베딩 차원 검증 (첫 번째 파일 샘플)"""
        result = {"errors": []}

        # JSON 또는 Parquet 파일 찾기
        json_files = list(passages_dir.glob("*.json"))
        parquet_files = list(passages_dir.glob("*.parquet"))

        if json_files:
            try:
                with open(json_files[0], "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list) and len(data) > 0:
                    sample = data[0]
                elif isinstance(data, dict) and "passages" in data:
                    sample = data["passages"][0] if data["passages"] else None
                else:
                    sample = None

                if sample and "embedding" in sample:
                    dim = len(sample["embedding"])
                    if dim != self.EMBEDDING_DIM:
                        result["errors"].append(
                            f"임베딩 차원 불일치: {dim} (expected: {self.EMBEDDING_DIM})"
                        )
            except Exception as e:
                result["errors"].append(f"임베딩 검증 오류: {e}")

        elif parquet_files:
            try:
                df = pd.read_parquet(parquet_files[0])
                if "embedding" in df.columns and len(df) > 0:
                    embedding = df.iloc[0]["embedding"]
                    if hasattr(embedding, "__len__"):
                        dim = len(embedding)
                        if dim != self.EMBEDDING_DIM:
                            result["errors"].append(
                                f"임베딩 차원 불일치: {dim} (expected: {self.EMBEDDING_DIM})"
                            )
            except Exception as e:
                result["errors"].append(f"Parquet 임베딩 검증 오류: {e}")

        return result


class GutenbergDatasetImporter:
    """
    Project Gutenberg 데이터셋 임포터

    ChromaDB/Pinecone에 전처리된 데이터를 임포트하고
    Spring Boot API를 통해 PostgreSQL 메타데이터를 생성합니다.
    """

    # 컬렉션 이름
    COLLECTIONS = [
        "novel_passages",
        "characters",
        "locations",
        "events",
        "themes"
    ]

    BATCH_SIZE = 1000
    MAX_RETRIES = 3

    def __init__(
        self,
        dataset_path: str,
        vectordb_type: str = "chromadb",
        vectordb_host: str = "localhost:8001",
        spring_boot_api: str = "http://localhost:8080",
        dry_run: bool = False
    ):
        """
        Args:
            dataset_path: 데이터셋 경로
            vectordb_type: VectorDB 타입 (chromadb, pinecone)
            vectordb_host: VectorDB 호스트
            spring_boot_api: Spring Boot API URL
            dry_run: True면 실제 저장 없이 검증만 수행
        """
        self.dataset_path = Path(dataset_path)
        self.vectordb_type = vectordb_type
        self.vectordb_host = vectordb_host
        self.spring_boot_api = spring_boot_api.rstrip("/")
        self.dry_run = dry_run

        self.stats = ImportStats()
        self._init_vectordb_client()

    def _init_vectordb_client(self):
        """VectorDB 클라이언트 초기화"""
        if self.vectordb_type == "chromadb":
            # Docker 환경에서는 HTTP 클라이언트, 로컬에서는 Persistent 클라이언트
            if ":" in self.vectordb_host:
                host, port = self.vectordb_host.split(":")
                self.chroma_client = chromadb.HttpClient(
                    host=host,
                    port=int(port)
                )
            else:
                # 로컬 persistent 모드
                self.chroma_client = chromadb.PersistentClient(
                    path=self.vectordb_host
                )
        elif self.vectordb_type == "pinecone":
            # Pinecone은 별도 초기화 필요
            raise NotImplementedError("Pinecone 지원은 추후 구현 예정")
        else:
            raise ValueError(f"지원하지 않는 vectordb_type: {self.vectordb_type}")

    def import_all(self) -> ImportStats:
        """
        전체 데이터셋 임포트 수행

        Returns:
            임포트 통계
        """
        start_time = time.time()

        print("🚀 데이터셋 임포트 시작...")
        print(f"   데이터셋 경로: {self.dataset_path}")
        print(f"   VectorDB: {self.vectordb_type} ({self.vectordb_host})")
        print(f"   Spring Boot API: {self.spring_boot_api}")
        print(f"   Dry Run: {self.dry_run}")
        print()

        # 1. 데이터셋 검증
        print("📋 Step 1/6: 데이터셋 검증 중...")
        validator = DatasetValidator(str(self.dataset_path))
        validation_result = validator.validate()

        if not validation_result["valid"]:
            print("❌ 데이터셋 검증 실패:")
            for error in validation_result["errors"]:
                print(f"   - {error}")
            self.stats.errors.extend(validation_result["errors"])
            return self.stats

        print(f"✅ 데이터셋 검증 완료: {validation_result['stats']}")

        if validation_result["warnings"]:
            for warning in validation_result["warnings"]:
                print(f"⚠️  {warning}")
        print()

        # 2. 컬렉션 생성
        print("📋 Step 2/6: ChromaDB 컬렉션 생성 중...")
        self._create_collections()
        print()

        # 3. 소설 로드
        print("📋 Step 3/6: novels.json 로드 중...")
        novels = self._load_novels()
        print(f"✅ {len(novels)}개 소설 로드 완료")
        print()

        # 4. 각 소설별 데이터 임포트
        print("📋 Step 4/6: 소설 데이터 임포트 중...")
        for novel in tqdm(novels, desc="소설 임포트", total=len(novels)):
            try:
                self._import_novel(novel)
                self.stats.novels_count += 1
            except Exception as e:
                error_msg = f"소설 '{novel.get('title', 'Unknown')}' 임포트 실패: {e}"
                print(f"\n❌ {error_msg}")
                self.stats.errors.append(error_msg)
        print()

        # 5. PostgreSQL 메타데이터 생성
        print("📋 Step 5/6: PostgreSQL 메타데이터 생성 중...")
        for novel in novels:
            try:
                self._create_novel_metadata(novel)
            except Exception as e:
                error_msg = f"메타데이터 생성 실패 ('{novel.get('title')}'): {e}"
                print(f"\n⚠️  {error_msg}")
                self.stats.errors.append(error_msg)
        print()

        # 6. 검증
        print("📋 Step 6/6: 임포트 검증 중...")
        self._verify_import()

        elapsed_time = time.time() - start_time

        print()
        print("=" * 60)
        print("✅ 데이터셋 임포트 완료!")
        print("=" * 60)
        print(f"   소설 수: {self.stats.novels_count}")
        print(f"   패시지 수: {self.stats.passages_count}")
        print(f"   캐릭터 수: {self.stats.characters_count}")
        print(f"   장소 수: {self.stats.locations_count}")
        print(f"   이벤트 수: {self.stats.events_count}")
        print(f"   테마 수: {self.stats.themes_count}")
        print(f"   소요 시간: {elapsed_time:.2f}초")
        print(f"   오류 수: {len(self.stats.errors)}")

        if self.stats.errors:
            print("\n❌ 오류 목록:")
            for error in self.stats.errors[:10]:  # 최대 10개만 표시
                print(f"   - {error}")
            if len(self.stats.errors) > 10:
                print(f"   ... 외 {len(self.stats.errors) - 10}개")

        return self.stats

    def _create_collections(self):
        """ChromaDB 컬렉션 생성"""
        for collection_name in self.COLLECTIONS:
            try:
                if self.dry_run:
                    print(f"   [DRY RUN] 컬렉션 생성 건너뜀: {collection_name}")
                    continue

                self.chroma_client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}  # HNSW 인덱스, 코사인 유사도
                )
                print(f"   ✅ 컬렉션 생성/확인: {collection_name}")
            except Exception as e:
                print(f"   ⚠️  컬렉션 {collection_name} 생성 중 오류: {e}")

    def _load_novels(self) -> List[Dict]:
        """novels.json 로드"""
        novels_path = self.dataset_path / "novels.json"
        with open(novels_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _import_novel(self, novel: Dict):
        """단일 소설 데이터 임포트"""
        novel_id = novel["id"]

        # 패시지 임포트
        self._import_passages(novel_id)

        # 캐릭터 임포트
        self._import_characters(novel_id)

        # 장소 임포트 (선택)
        self._import_locations(novel_id)

        # 이벤트 임포트 (선택)
        self._import_events(novel_id)

        # 테마 임포트 (선택)
        self._import_themes(novel_id)

    def _import_passages(self, novel_id: str):
        """패시지 데이터 임포트"""
        # JSON 또는 Parquet 파일 찾기
        passages_dir = self.dataset_path / "passages"

        # 파일 형식 결정
        json_path = passages_dir / f"{novel_id}.json"
        parquet_path = passages_dir / f"{novel_id}.parquet"

        passages = []

        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
            passages = df.to_dict("records")
        elif json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    passages = data
                elif isinstance(data, dict) and "passages" in data:
                    passages = data["passages"]
                elif isinstance(data, dict) and "chunks" in data:
                    # 기존 포맷 지원
                    passages = data["chunks"]
        else:
            return  # 파일 없으면 건너뜀

        if not passages:
            return

        if self.dry_run:
            self.stats.passages_count += len(passages)
            return

        collection = self.chroma_client.get_collection("novel_passages")

        # 배치 처리
        for i in range(0, len(passages), self.BATCH_SIZE):
            batch = passages[i:i + self.BATCH_SIZE]

            ids = []
            embeddings = []
            documents = []
            metadatas = []

            for p in batch:
                # ID 생성
                passage_id = p.get("id") or f"{novel_id}_passage_{p.get('chunk_index', uuid.uuid4().hex[:8])}"
                ids.append(passage_id)

                # 임베딩
                embedding = p.get("embedding")
                if embedding:
                    embeddings.append(embedding)

                # 문서 텍스트
                documents.append(p.get("text", ""))

                # 메타데이터
                metadatas.append({
                    "novel_id": novel_id,
                    "chapter_number": p.get("chapter_number", 0),
                    "passage_number": p.get("passage_number", p.get("chunk_index", 0)),
                    "word_count": p.get("word_count", 0),
                    "passage_type": p.get("passage_type", "narrative")
                })

            # ChromaDB에 추가
            if embeddings:
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )

            self.stats.passages_count += len(batch)

    def _import_characters(self, novel_id: str):
        """캐릭터 데이터 임포트"""
        chars_path = self.dataset_path / "characters" / f"{novel_id}.json"

        if not chars_path.exists():
            return

        with open(chars_path, "r", encoding="utf-8") as f:
            characters = json.load(f)

        if not characters:
            return

        if self.dry_run:
            self.stats.characters_count += len(characters)
            return

        collection = self.chroma_client.get_collection("characters")

        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for char in characters:
            char_id = char.get("id") or f"{novel_id}_char_{char.get('name', 'unknown')}"
            ids.append(char_id)

            # 임베딩
            if char.get("embedding"):
                embeddings.append(char["embedding"])

            # 문서 (캐릭터 설명)
            documents.append(char.get("description", ""))

            # personality_traits를 JSON 문자열로 변환
            personality_traits = char.get("personality_traits", [])
            if isinstance(personality_traits, list):
                personality_traits_str = json.dumps(personality_traits)
            else:
                personality_traits_str = str(personality_traits)

            metadatas.append({
                "novel_id": novel_id,
                "name": char.get("name", ""),
                "role": char.get("role", "supporting"),
                "personality_traits": personality_traits_str,
                "first_appearance_chapter": char.get("first_appearance_chapter", 1)
            })

        if embeddings:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

        self.stats.characters_count += len(characters)

    def _import_locations(self, novel_id: str):
        """장소 데이터 임포트"""
        locations_path = self.dataset_path / "locations" / f"{novel_id}.json"

        if not locations_path.exists():
            return

        with open(locations_path, "r", encoding="utf-8") as f:
            locations = json.load(f)

        if not locations or self.dry_run:
            if locations:
                self.stats.locations_count += len(locations)
            return

        collection = self.chroma_client.get_collection("locations")

        ids = [loc.get("id") or f"{novel_id}_loc_{i}" for i, loc in enumerate(locations)]
        embeddings = [loc["embedding"] for loc in locations if loc.get("embedding")]
        documents = [loc.get("description", "") for loc in locations]
        metadatas = [{"novel_id": novel_id, "name": loc.get("name", "")} for loc in locations]

        if embeddings:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

        self.stats.locations_count += len(locations)

    def _import_events(self, novel_id: str):
        """이벤트 데이터 임포트"""
        events_path = self.dataset_path / "events" / f"{novel_id}.json"

        if not events_path.exists():
            return

        with open(events_path, "r", encoding="utf-8") as f:
            events = json.load(f)

        if not events or self.dry_run:
            if events:
                self.stats.events_count += len(events)
            return

        collection = self.chroma_client.get_collection("events")

        ids = [evt.get("id") or f"{novel_id}_evt_{i}" for i, evt in enumerate(events)]
        embeddings = [evt["embedding"] for evt in events if evt.get("embedding")]
        documents = [evt.get("description", "") for evt in events]
        metadatas = [{"novel_id": novel_id, "name": evt.get("name", "")} for evt in events]

        if embeddings:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

        self.stats.events_count += len(events)

    def _import_themes(self, novel_id: str):
        """테마 데이터 임포트"""
        themes_path = self.dataset_path / "themes" / f"{novel_id}.json"

        if not themes_path.exists():
            return

        with open(themes_path, "r", encoding="utf-8") as f:
            themes = json.load(f)

        if not themes or self.dry_run:
            if themes:
                self.stats.themes_count += len(themes)
            return

        collection = self.chroma_client.get_collection("themes")

        ids = [thm.get("id") or f"{novel_id}_thm_{i}" for i, thm in enumerate(themes)]
        embeddings = [thm["embedding"] for thm in themes if thm.get("embedding")]
        documents = [thm.get("description", "") for thm in themes]
        metadatas = [{"novel_id": novel_id, "name": thm.get("name", "")} for thm in themes]

        if embeddings:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

        self.stats.themes_count += len(themes)

    def _create_novel_metadata(self, novel: Dict):
        """Spring Boot API를 통해 PostgreSQL 메타데이터 생성"""
        if self.dry_run:
            print(f"   [DRY RUN] 메타데이터 생성 건너뜀: {novel.get('title')}")
            return

        # 패시지와 캐릭터 수 계산
        passages_count = 0
        characters_count = 0

        passages_dir = self.dataset_path / "passages"
        if (passages_dir / f"{novel['id']}.parquet").exists():
            df = pd.read_parquet(passages_dir / f"{novel['id']}.parquet")
            passages_count = len(df)
        elif (passages_dir / f"{novel['id']}.json").exists():
            with open(passages_dir / f"{novel['id']}.json", "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    passages_count = len(data)
                elif isinstance(data, dict):
                    passages_count = len(data.get("passages", data.get("chunks", [])))

        chars_path = self.dataset_path / "characters" / f"{novel['id']}.json"
        if chars_path.exists():
            with open(chars_path, "r") as f:
                chars = json.load(f)
                characters_count = len(chars)

        payload = {
            "title": novel.get("title", "Unknown"),
            "author": novel.get("author", "Unknown"),
            "publication_year": novel.get("publication_year"),
            "genre": novel.get("genre", ""),
            "language": novel.get("language", "en"),
            "vectordb_collection_id": novel["id"],
            "total_passages_count": passages_count,
            "total_characters_count": characters_count,
            "ingestion_status": "completed"
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(
                        f"{self.spring_boot_api}/api/internal/novels",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )

                    if response.status_code in (200, 201):
                        result = response.json()
                        print(f"   ✅ 메타데이터 생성: {novel.get('title')} (ID: {result.get('id', 'N/A')})")
                        return result
                    elif response.status_code == 409:
                        # 이미 존재하는 경우
                        print(f"   ⚠️  이미 존재: {novel.get('title')}")
                        return None
                    else:
                        print(f"   ⚠️  API 응답 오류 ({response.status_code}): {response.text[:100]}")

            except httpx.ConnectError:
                if attempt < self.MAX_RETRIES - 1:
                    print(f"   ⚠️  Spring Boot 연결 실패, 재시도 중... ({attempt + 1}/{self.MAX_RETRIES})")
                    time.sleep(2 ** attempt)  # 지수 백오프
                else:
                    print(f"   ❌ Spring Boot API 연결 실패: {self.spring_boot_api}")
                    self.stats.errors.append(f"Spring Boot 연결 실패: {novel.get('title')}")

            except Exception as e:
                self.stats.errors.append(f"메타데이터 생성 오류 ({novel.get('title')}): {e}")
                break

        return None

    def _verify_import(self):
        """임포트 검증"""
        print("\n🔍 임포트 검증 결과:")

        for collection_name in self.COLLECTIONS:
            try:
                collection = self.chroma_client.get_collection(collection_name)
                count = collection.count()
                print(f"   ✅ {collection_name}: {count}개 문서")
            except Exception as e:
                print(f"   ❌ {collection_name}: 오류 - {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Project Gutenberg 데이터셋을 VectorDB에 임포트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
    # ChromaDB (로컬)
    python scripts/import_dataset.py \\
        --dataset-path ./data/gutenberg_dataset \\
        --vectordb chromadb \\
        --vectordb-host ./chroma_data

    # ChromaDB (Docker)
    python scripts/import_dataset.py \\
        --dataset-path ./data/gutenberg_dataset \\
        --vectordb chromadb \\
        --vectordb-host localhost:8001 \\
        --spring-boot-api http://localhost:8080

    # Dry Run (검증만)
    python scripts/import_dataset.py \\
        --dataset-path ./data/gutenberg_dataset \\
        --dry-run
        """
    )

    parser.add_argument(
        "--dataset-path",
        required=True,
        help="전처리된 데이터셋 경로"
    )
    parser.add_argument(
        "--vectordb",
        choices=["chromadb", "pinecone"],
        default="chromadb",
        help="VectorDB 타입 (기본: chromadb)"
    )
    parser.add_argument(
        "--vectordb-host",
        default="localhost:8001",
        help="VectorDB 호스트 (기본: localhost:8001)"
    )
    parser.add_argument(
        "--spring-boot-api",
        default="http://localhost:8080",
        help="Spring Boot API URL (기본: http://localhost:8080)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="검증만 수행하고 실제 임포트는 건너뜀"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="데이터셋 검증만 수행"
    )

    args = parser.parse_args()

    # 검증만 수행
    if args.validate_only:
        print("📋 데이터셋 검증 중...")
        validator = DatasetValidator(args.dataset_path)
        result = validator.validate()

        if result["valid"]:
            print("✅ 데이터셋 검증 성공!")
            print(f"   통계: {result['stats']}")
        else:
            print("❌ 데이터셋 검증 실패!")
            for error in result["errors"]:
                print(f"   - {error}")

        if result["warnings"]:
            print("\n⚠️  경고:")
            for warning in result["warnings"]:
                print(f"   - {warning}")

        sys.exit(0 if result["valid"] else 1)

    # 전체 임포트 수행
    importer = GutenbergDatasetImporter(
        dataset_path=args.dataset_path,
        vectordb_type=args.vectordb,
        vectordb_host=args.vectordb_host,
        spring_boot_api=args.spring_boot_api,
        dry_run=args.dry_run
    )

    stats = importer.import_all()

    # 오류가 있으면 exit code 1
    sys.exit(1 if stats.errors else 0)


if __name__ == "__main__":
    main()
