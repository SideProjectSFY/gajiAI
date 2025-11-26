"""
Scenario Test Models for Story 2.4
Automated quality testing framework for AI prompt validation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class ScenarioTest:
    """Test case for scenario quality validation"""
    
    test_id: str
    name: str
    category: str  # "character_consistency", "event_coherence", "setting_adaptation"
    scenario: Dict  # Scenario parameters for prompt adapter
    test_messages: List[str]  # User messages to test with
    evaluation_criteria: Dict  # What to check in responses
    expected_behaviors: List[str]  # Expected AI behaviors
    min_coherence_score: float = 7.0
    
    def __post_init__(self):
        valid_categories = ["character_consistency", "event_coherence", "setting_adaptation"]
        if self.category not in valid_categories:
            raise ValueError(f"Invalid category. Must be one of {valid_categories}")


@dataclass
class TestResult:
    """Result of a single scenario test execution"""
    
    test_id: str
    passed: bool
    scores: Dict  # coherence_score, consistency_score, creativity_score
    average_score: float
    conversation: List[str]  # AI responses
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    execution_time: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "test_id": self.test_id,
            "passed": self.passed,
            "scores": self.scores,
            "average_score": self.average_score,
            "conversation": self.conversation,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class TestSuiteResult:
    """Result of full test suite execution"""
    
    total_tests: int
    passed: int
    failed: int
    pass_rate: float
    average_score: float
    results: List[TestResult]
    status: str  # "PASS" or "FAIL"
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": self.pass_rate,
            "average_score": self.average_score,
            "results": [r.to_dict() for r in self.results],
            "status": self.status,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat()
        }
