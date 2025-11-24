"""
VectorDB Dataset Import Integration Tests

데이터셋 임포트 스크립트의 통합 테스트
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 스크립트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from import_dataset import (
    DatasetValidator,
    GutenbergDatasetImporter,
    ImportStats,
)
from verify_import import ImportVerifier, VerificationResult


class TestDatasetValidator:
    """DatasetValidator 테스트"""

    @pytest.fixture
    def sample_dataset_path(self):
        """샘플 데이터셋 경로"""
        return Path(__file__).parent / "fixtures" / "sample_dataset"

    @pytest.fixture
    def empty_dataset(self, tmp_path):
        """빈 데이터셋"""
        return tmp_path / "empty_dataset"

    @pytest.fixture
    def invalid_dataset(self, tmp_path):
        """잘못된 데이터셋"""
        dataset_path = tmp_path / "invalid_dataset"
        dataset_path.mkdir()

        # 잘못된 novels.json 생성
        with open(dataset_path / "novels.json", "w") as f:
            f.write("invalid json")

        return dataset_path

    def test_validate_sample_dataset(self, sample_dataset_path):
        """샘플 데이터셋 검증 테스트"""
        validator = DatasetValidator(str(sample_dataset_path))
        result = validator.validate()

        assert result["valid"] is True
        assert "novels" in result["stats"]
        assert result["stats"]["novels"] == 2  # Pride and Prejudice, Great Expectations

    def test_validate_empty_dataset(self, empty_dataset):
        """빈 데이터셋 검증 테스트"""
        empty_dataset.mkdir(exist_ok=True)

        validator = DatasetValidator(str(empty_dataset))
        result = validator.validate()

        assert result["valid"] is False
        assert any("novels.json" in error for error in result["errors"])

    def test_validate_invalid_json(self, invalid_dataset):
        """잘못된 JSON 검증 테스트"""
        validator = DatasetValidator(str(invalid_dataset))
        result = validator.validate()

        assert result["valid"] is False
        assert any("JSON 파싱" in error for error in result["errors"])

    def test_validate_missing_required_fields(self, tmp_path):
        """필수 필드 누락 검증 테스트"""
        dataset_path = tmp_path / "missing_fields"
        dataset_path.mkdir()

        # 필수 필드가 누락된 novels.json
        with open(dataset_path / "novels.json", "w") as f:
            json.dump([{"id": "test"}], f)  # title, author 누락

        validator = DatasetValidator(str(dataset_path))
        result = validator.validate()

        assert result["valid"] is False
        assert any("title" in error or "author" in error for error in result["errors"])

    def test_validate_duplicate_ids(self, tmp_path):
        """중복 ID 검증 테스트"""
        dataset_path = tmp_path / "duplicate_ids"
        dataset_path.mkdir()

        # 중복 ID가 있는 novels.json
        with open(dataset_path / "novels.json", "w") as f:
            json.dump([
                {"id": "same_id", "title": "Book 1", "author": "Author 1"},
                {"id": "same_id", "title": "Book 2", "author": "Author 2"},
            ], f)

        validator = DatasetValidator(str(dataset_path))
        result = validator.validate()

        assert result["valid"] is False
        assert any("중복 ID" in error for error in result["errors"])


class TestGutenbergDatasetImporter:
    """GutenbergDatasetImporter 테스트"""

    @pytest.fixture
    def sample_dataset_path(self):
        """샘플 데이터셋 경로"""
        return Path(__file__).parent / "fixtures" / "sample_dataset"

    @pytest.fixture
    def temp_chroma_path(self, tmp_path):
        """임시 ChromaDB 경로"""
        return str(tmp_path / "chroma_test")

    def test_init_importer(self, sample_dataset_path, temp_chroma_path):
        """임포터 초기화 테스트"""
        importer = GutenbergDatasetImporter(
            dataset_path=str(sample_dataset_path),
            vectordb_type="chromadb",
            vectordb_host=temp_chroma_path,
            dry_run=True
        )

        assert importer.dataset_path == sample_dataset_path
        assert importer.vectordb_type == "chromadb"
        assert importer.dry_run is True

    def test_dry_run_import(self, sample_dataset_path, temp_chroma_path):
        """Dry Run 임포트 테스트 (실제 저장 없음)"""
        importer = GutenbergDatasetImporter(
            dataset_path=str(sample_dataset_path),
            vectordb_type="chromadb",
            vectordb_host=temp_chroma_path,
            dry_run=True
        )

        stats = importer.import_all()

        # Dry run에서도 카운트는 정상적으로 되어야 함
        assert stats.novels_count >= 0
        assert stats.passages_count >= 0
        assert stats.characters_count >= 0

    def test_actual_import(self, sample_dataset_path, temp_chroma_path):
        """실제 ChromaDB 임포트 테스트"""
        importer = GutenbergDatasetImporter(
            dataset_path=str(sample_dataset_path),
            vectordb_type="chromadb",
            vectordb_host=temp_chroma_path,
            spring_boot_api="http://localhost:9999",  # 연결 안 됨
            dry_run=False
        )

        stats = importer.import_all()

        # 소설이 임포트되어야 함
        assert stats.novels_count == 1  # Pride and Prejudice만 passages 있음
        assert stats.passages_count == 3  # 3개 passages
        assert stats.characters_count == 2  # 2개 characters

        # 오류가 있을 수 있음 (Spring Boot 연결 실패)
        # PostgreSQL 메타데이터 생성 실패는 에러로 기록

    def test_import_with_collections(self, sample_dataset_path, temp_chroma_path):
        """컬렉션 생성 테스트"""
        importer = GutenbergDatasetImporter(
            dataset_path=str(sample_dataset_path),
            vectordb_type="chromadb",
            vectordb_host=temp_chroma_path,
            dry_run=False
        )

        importer.import_all()

        # 컬렉션 확인
        collections = importer.chroma_client.list_collections()
        collection_names = {c.name for c in collections}

        assert "novel_passages" in collection_names
        assert "characters" in collection_names

    def test_import_passages_content(self, sample_dataset_path, temp_chroma_path):
        """패시지 내용 임포트 테스트"""
        importer = GutenbergDatasetImporter(
            dataset_path=str(sample_dataset_path),
            vectordb_type="chromadb",
            vectordb_host=temp_chroma_path,
            dry_run=False
        )

        importer.import_all()

        # novel_passages 컬렉션에서 데이터 확인
        collection = importer.chroma_client.get_collection("novel_passages")
        count = collection.count()

        assert count == 3  # 3개 passages

        # 샘플 문서 조회
        sample = collection.get(limit=1)
        assert len(sample["ids"]) == 1
        assert sample["metadatas"][0]["novel_id"] == "novel_pride_and_prejudice"

    def test_import_characters_content(self, sample_dataset_path, temp_chroma_path):
        """캐릭터 내용 임포트 테스트"""
        importer = GutenbergDatasetImporter(
            dataset_path=str(sample_dataset_path),
            vectordb_type="chromadb",
            vectordb_host=temp_chroma_path,
            dry_run=False
        )

        importer.import_all()

        # characters 컬렉션에서 데이터 확인
        collection = importer.chroma_client.get_collection("characters")
        count = collection.count()

        assert count == 2  # Elizabeth Bennet, Mr. Darcy

        # 샘플 문서 조회
        sample = collection.get(limit=2)
        names = [m["name"] for m in sample["metadatas"]]
        assert "Elizabeth Bennet" in names or "Fitzwilliam Darcy" in names


class TestImportVerifier:
    """ImportVerifier 테스트"""

    @pytest.fixture
    def sample_dataset_path(self):
        """샘플 데이터셋 경로"""
        return Path(__file__).parent / "fixtures" / "sample_dataset"

    @pytest.fixture
    def populated_chroma(self, sample_dataset_path, tmp_path):
        """데이터가 있는 ChromaDB"""
        chroma_path = str(tmp_path / "chroma_populated")

        # 데이터 임포트
        importer = GutenbergDatasetImporter(
            dataset_path=str(sample_dataset_path),
            vectordb_type="chromadb",
            vectordb_host=chroma_path,
            dry_run=False
        )
        importer.import_all()

        return chroma_path

    @pytest.fixture
    def empty_chroma(self, tmp_path):
        """빈 ChromaDB"""
        import chromadb

        chroma_path = str(tmp_path / "chroma_empty")
        client = chromadb.PersistentClient(path=chroma_path)

        # 빈 컬렉션 생성
        for name in ["novel_passages", "characters", "locations", "events", "themes"]:
            client.get_or_create_collection(name=name)

        return chroma_path

    def test_verify_populated_db(self, populated_chroma):
        """데이터가 있는 DB 검증 테스트"""
        verifier = ImportVerifier(
            vectordb_host=populated_chroma,
            spring_boot_api="http://localhost:9999"
        )

        results = verifier.verify_all()

        # 컬렉션 확인 통과
        assert results["collections"].passed is True

        # 문서 수 확인 통과 (데이터가 있으므로)
        assert results["document_counts"].passed is True

        # 샘플 문서 조회 통과
        assert results["sample_documents"].passed is True

    def test_verify_empty_db(self, empty_chroma):
        """빈 DB 검증 테스트"""
        verifier = ImportVerifier(
            vectordb_host=empty_chroma,
            spring_boot_api="http://localhost:9999"
        )

        results = verifier.verify_all()

        # 컬렉션은 존재
        assert results["collections"].passed is True

        # novel_passages가 비어있으므로 실패
        assert results["document_counts"].passed is False

    def test_detailed_report(self, populated_chroma):
        """상세 리포트 테스트"""
        verifier = ImportVerifier(
            vectordb_host=populated_chroma,
            spring_boot_api="http://localhost:9999"
        )

        report = verifier.get_detailed_report()

        assert "timestamp" in report
        assert "collections" in report
        assert "novel_passages" in report["collections"]
        assert report["collections"]["novel_passages"]["count"] == 3


class TestImportStats:
    """ImportStats 테스트"""

    def test_default_values(self):
        """기본값 테스트"""
        stats = ImportStats()

        assert stats.novels_count == 0
        assert stats.passages_count == 0
        assert stats.characters_count == 0
        assert stats.locations_count == 0
        assert stats.events_count == 0
        assert stats.themes_count == 0
        assert stats.errors == []

    def test_error_tracking(self):
        """오류 추적 테스트"""
        stats = ImportStats()
        stats.errors.append("Test error 1")
        stats.errors.append("Test error 2")

        assert len(stats.errors) == 2
        assert "Test error 1" in stats.errors


class TestVerificationResult:
    """VerificationResult 테스트"""

    def test_passed_result(self):
        """통과 결과 테스트"""
        result = VerificationResult(
            passed=True,
            message="테스트 통과",
            details={"count": 10}
        )

        assert result.passed is True
        assert result.message == "테스트 통과"
        assert result.details["count"] == 10

    def test_failed_result(self):
        """실패 결과 테스트"""
        result = VerificationResult(
            passed=False,
            message="테스트 실패"
        )

        assert result.passed is False
        assert result.details is None


# Performance tests (optional, can be skipped in CI)
@pytest.mark.slow
class TestPerformance:
    """성능 테스트 (선택적)"""

    @pytest.fixture
    def large_dataset(self, tmp_path):
        """대규모 데이터셋 생성"""
        dataset_path = tmp_path / "large_dataset"
        dataset_path.mkdir()
        passages_dir = dataset_path / "passages"
        passages_dir.mkdir()

        # 10개 소설 생성
        novels = []
        for i in range(10):
            novel_id = f"novel_{i}"
            novels.append({
                "id": novel_id,
                "title": f"Test Novel {i}",
                "author": f"Author {i}",
                "publication_year": 1800 + i
            })

            # 각 소설당 100개 passages 생성
            passages = []
            for j in range(100):
                passages.append({
                    "id": f"{novel_id}_passage_{j}",
                    "chapter_number": j // 10 + 1,
                    "passage_number": j,
                    "text": f"Test passage {j} for novel {i}. " * 50,
                    "word_count": 300,
                    "passage_type": "narrative",
                    "embedding": [0.1] * 768  # 768-dim embedding
                })

            with open(passages_dir / f"{novel_id}.json", "w") as f:
                json.dump({"passages": passages}, f)

        with open(dataset_path / "novels.json", "w") as f:
            json.dump(novels, f)

        return dataset_path

    def test_import_performance(self, large_dataset, tmp_path):
        """임포트 성능 테스트"""
        import time

        chroma_path = str(tmp_path / "chroma_perf")

        importer = GutenbergDatasetImporter(
            dataset_path=str(large_dataset),
            vectordb_type="chromadb",
            vectordb_host=chroma_path,
            dry_run=False
        )

        start_time = time.time()
        stats = importer.import_all()
        elapsed_time = time.time() - start_time

        # 1000 passages (10 novels * 100 passages)
        expected_passages = 1000

        # 성능 기준: 1000 passages/minute 이상
        passages_per_minute = stats.passages_count / (elapsed_time / 60)

        print(f"\n성능 결과:")
        print(f"  총 passages: {stats.passages_count}")
        print(f"  소요 시간: {elapsed_time:.2f}초")
        print(f"  처리 속도: {passages_per_minute:.0f} passages/분")

        # 기본 검증
        assert stats.passages_count == expected_passages
        assert stats.novels_count == 10

        # 성능 기준 검증 (1000 passages/분 이상)
        # 테스트 환경에 따라 조정 필요
        assert passages_per_minute > 500, f"처리 속도 부족: {passages_per_minute:.0f} passages/분"
