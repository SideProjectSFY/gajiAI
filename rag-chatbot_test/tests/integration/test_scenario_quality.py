"""
Integration Tests for Story 2.4 - Scenario Quality Testing
Tests the automated quality evaluation system with Gemini judge
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.models.scenario_test import ScenarioTest, TestResult, TestSuiteResult
from app.services.scenario_quality_evaluator import ScenarioQualityEvaluator
from app.services.scenario_tests import (
    ALL_SCENARIO_TESTS,
    CHARACTER_CONSISTENCY_TESTS,
    EVENT_COHERENCE_TESTS,
    SETTING_ADAPTATION_TESTS,
    get_tests_by_category,
    get_test_by_id
)


@pytest.fixture
def sample_test():
    """Sample test for unit testing"""
    return ScenarioTest(
        test_id="TEST-001",
        name="Sample Test",
        category="character_consistency",
        scenario={
            "base_story": "Harry Potter",
            "scenario_type": "CHARACTER_CHANGE",
            "parameters": {
                "character": "Hermione",
                "original_property": "Gryffindor",
                "new_property": "Slytherin"
            }
        },
        test_messages=["How do you feel about your house?"],
        evaluation_criteria={
            "intelligence_preserved": "Should remain intelligent"
        },
        expected_behaviors=["References studying"],
        min_coherence_score=7.0
    )


@pytest.fixture
def mock_gemini_judge_response():
    """Mock Gemini judge response"""
    return {
        "coherence_score": 8.5,
        "consistency_score": 8.0,
        "creativity_score": 7.5,
        "strengths": [
            "Maintains character intelligence",
            "Shows Slytherin ambition",
            "Consistent personality"
        ],
        "weaknesses": [
            "Could show more house loyalty"
        ],
        "passes_criteria": True
    }


class TestScenarioTestData:
    """Test scenario test data structure"""
    
    def test_all_tests_count(self):
        """Verify we have 30+ tests"""
        assert len(ALL_SCENARIO_TESTS) == 30
        assert len(CHARACTER_CONSISTENCY_TESTS) == 10
        assert len(EVENT_COHERENCE_TESTS) == 10
        assert len(SETTING_ADAPTATION_TESTS) == 10
    
    def test_get_tests_by_category(self):
        """Test filtering tests by category"""
        cc_tests = get_tests_by_category("character_consistency")
        assert len(cc_tests) == 10
        assert all(t.category == "character_consistency" for t in cc_tests)
        
        ec_tests = get_tests_by_category("event_coherence")
        assert len(ec_tests) == 10
        
        sa_tests = get_tests_by_category("setting_adaptation")
        assert len(sa_tests) == 10
    
    def test_get_test_by_id(self):
        """Test retrieving specific test by ID"""
        test = get_test_by_id("CC-001")
        assert test is not None
        assert test.test_id == "CC-001"
        assert test.name == "Hermione Slytherin Personality Preservation"
        assert test.category == "character_consistency"
        
        # Non-existent test
        assert get_test_by_id("INVALID-999") is None
    
    def test_test_structure_validation(self):
        """Validate all tests have required fields"""
        for test in ALL_SCENARIO_TESTS:
            assert test.test_id
            assert test.name
            assert test.category in [
                "character_consistency",
                "event_coherence",
                "setting_adaptation"
            ]
            assert test.scenario
            assert len(test.test_messages) > 0
            assert test.evaluation_criteria
            assert len(test.expected_behaviors) > 0
            assert 1.0 <= test.min_coherence_score <= 10.0


class TestScenarioQualityEvaluator:
    """Test Gemini judge evaluator"""
    
    @pytest.mark.asyncio
    @patch('app.services.scenario_quality_evaluator.genai')
    async def test_evaluate_scenario_test_success(
        self,
        mock_genai,
        sample_test,
        mock_gemini_judge_response
    ):
        """Test successful scenario evaluation"""
        import json
        
        # Mock Gemini responses
        mock_model = AsyncMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Mock AI response generation
        ai_response = AsyncMock()
        ai_response.text = "I'm Hermione, and being in Slytherin has taught me that ambition and intelligence go hand in hand. I still value knowledge above all."
        mock_model.generate_content_async.side_effect = [
            ai_response,  # First call: AI response
            AsyncMock(text=json.dumps(mock_gemini_judge_response))  # Second call: Judge evaluation (proper JSON)
        ]
        
        # Mock environment variable
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            evaluator = ScenarioQualityEvaluator()
            result = await evaluator.evaluate_scenario_test(sample_test)
        
        # Assertions
        assert isinstance(result, TestResult)
        assert result.test_id == "TEST-001"
        assert result.passed is True
        assert result.average_score >= 7.0
        assert len(result.conversation) > 0
        assert len(result.strengths) > 0
        assert result.execution_time >= 0  # Can be 0 in mocked environment
    
    @pytest.mark.asyncio
    @patch('app.services.scenario_quality_evaluator.genai')
    async def test_evaluate_scenario_test_failure(
        self,
        mock_genai,
        sample_test
    ):
        """Test scenario evaluation that fails"""
        import json
        
        # Mock low scores
        low_score_response = {
            "coherence_score": 3.0,
            "consistency_score": 4.0,
            "creativity_score": 3.5,
            "strengths": ["Attempted to answer"],
            "weaknesses": [
                "Character completely wrong",
                "Nonsensical response",
                "No house awareness"
            ],
            "passes_criteria": False
        }
        
        # Mock Gemini responses
        mock_model = AsyncMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        ai_response = AsyncMock()
        ai_response.text = "I don't know what house I'm in."
        mock_model.generate_content_async.side_effect = [
            ai_response,
            AsyncMock(text=json.dumps(low_score_response))  # Proper JSON serialization
        ]
        
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            evaluator = ScenarioQualityEvaluator()
            result = await evaluator.evaluate_scenario_test(sample_test)
        
        # Assertions
        assert result.passed is False
        assert result.average_score < 7.0
        assert len(result.weaknesses) > 0
    
    def test_judge_prompt_building(self):
        """Test evaluation prompt construction"""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            evaluator = ScenarioQualityEvaluator()
        
        test = ScenarioTest(
            test_id="TEST-001",
            name="Test",
            category="character_consistency",
            scenario={"test": "scenario"},
            test_messages=["Hello"],
            evaluation_criteria={"key": "value"},
            expected_behaviors=["behavior"],
            min_coherence_score=7.0
        )
        
        conversation = ["Response 1"]
        prompt = evaluator._build_evaluation_prompt(test, conversation)
        
        # Verify prompt contains key elements
        assert "Scenario Context:" in prompt
        assert "Evaluation Criteria:" in prompt
        assert "Conversation to Evaluate:" in prompt
        assert "coherence_score" in prompt
        assert "consistency_score" in prompt
        assert "creativity_score" in prompt
    
    def test_validation_error_handling(self):
        """Test evaluation validation"""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            evaluator = ScenarioQualityEvaluator()
        
        # Valid evaluation
        valid_eval = {
            "coherence_score": 8.0,
            "consistency_score": 7.5,
            "creativity_score": 8.5,
            "strengths": ["good"],
            "weaknesses": ["minor issue"],
            "passes_criteria": True
        }
        evaluator._validate_evaluation(valid_eval)  # Should not raise
        
        # Invalid evaluation - missing field
        with pytest.raises(ValueError, match="Missing required field"):
            evaluator._validate_evaluation({"coherence_score": 8.0})
        
        # Invalid evaluation - score out of range
        with pytest.raises(ValueError, match="Invalid score"):
            invalid_eval = valid_eval.copy()
            invalid_eval["coherence_score"] = 15.0
            evaluator._validate_evaluation(invalid_eval)


class TestTestSuiteResult:
    """Test suite result aggregation"""
    
    def test_suite_result_creation(self):
        """Test creating test suite result"""
        results = [
            TestResult(
                test_id="TEST-001",
                passed=True,
                scores={"coherence_score": 8.0, "consistency_score": 8.0, "creativity_score": 7.5},
                average_score=7.8,
                conversation=["response 1"],
                strengths=["good"],
                weaknesses=["minor"],
                execution_time=1.5,
                timestamp=datetime.now()
            ),
            TestResult(
                test_id="TEST-002",
                passed=False,
                scores={"coherence_score": 5.0, "consistency_score": 6.0, "creativity_score": 5.5},
                average_score=5.5,
                conversation=["response 2"],
                strengths=["attempted"],
                weaknesses=["poor quality"],
                execution_time=1.2,
                timestamp=datetime.now()
            )
        ]
        
        suite_result = TestSuiteResult(
            total_tests=2,
            passed=1,
            failed=1,
            pass_rate=0.5,
            average_score=6.65,
            results=results,
            status="FAIL",
            execution_time=2.7,
            timestamp=datetime.now()
        )
        
        assert suite_result.total_tests == 2
        assert suite_result.passed == 1
        assert suite_result.failed == 1
        assert abs(suite_result.pass_rate - 0.5) < 0.01  # Float comparison with tolerance
        assert suite_result.status == "FAIL"
        
        # Test serialization
        suite_dict = suite_result.to_dict()
        assert suite_dict["total_tests"] == 2
        assert suite_dict["status"] == "FAIL"
        assert len(suite_dict["results"]) == 2


class TestScenarioDataIntegrity:
    """Test data integrity of scenario tests"""
    
    def test_unique_test_ids(self):
        """Ensure all test IDs are unique"""
        test_ids = [t.test_id for t in ALL_SCENARIO_TESTS]
        assert len(test_ids) == len(set(test_ids))
    
    def test_id_naming_convention(self):
        """Verify test ID naming follows convention"""
        for test in ALL_SCENARIO_TESTS:
            prefix = test.test_id.split("-")[0]
            if test.category == "character_consistency":
                assert prefix == "CC"
            elif test.category == "event_coherence":
                assert prefix == "EC"
            elif test.category == "setting_adaptation":
                assert prefix == "SA"
    
    def test_scenario_completeness(self):
        """Verify all scenarios have required fields"""
        for test in ALL_SCENARIO_TESTS:
            scenario = test.scenario
            
            # All scenarios should have certain keys
            assert "scenario_id" in scenario or "base_story" in scenario
            
            # Check for type-specific fields
            if test.category == "character_consistency":
                assert "CHARACTER_CHANGE" in str(scenario) or "character" in str(scenario).lower()
            elif test.category == "event_coherence":
                assert "EVENT_ALTERATION" in str(scenario) or "event" in str(scenario).lower()
            elif test.category == "setting_adaptation":
                assert "SETTING_MODIFICATION" in str(scenario) or "setting" in str(scenario).lower()


@pytest.mark.integration
class TestScenarioQualityAPI:
    """Integration tests for API endpoints"""
    
    @pytest.mark.asyncio
    async def test_test_categories_endpoint(self):
        """Test getting test categories"""
        from app.api.scenario_testing import get_test_categories
        
        result = await get_test_categories()
        
        assert result["total_tests"] == 30
        assert "character_consistency" in result["categories"]
        assert "event_coherence" in result["categories"]
        assert "setting_adaptation" in result["categories"]
        assert result["categories"]["character_consistency"] == 10
    
    @pytest.mark.asyncio
    async def test_list_tests_endpoint(self):
        """Test listing all tests"""
        from app.api.scenario_testing import list_all_tests
        
        result = await list_all_tests()
        
        assert result["total"] == 30
        assert len(result["tests"]) == 30
        
        # Test filtering
        cc_result = await list_all_tests(category="character_consistency")
        assert cc_result["total"] == 10
