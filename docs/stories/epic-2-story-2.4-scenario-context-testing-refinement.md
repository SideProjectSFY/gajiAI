# Story 2.4: Scenario Context Testing & Refinement

**Epic**: Epic 2 - AI Adaptation Layer  
**Priority**: P2 - Medium  
**Status**: Not Started  
**Estimated Effort**: 10 hours

## Description

Build comprehensive testing framework to validate AI prompt quality, scenario coherence, and character consistency across diverse scenarios with automated quality metrics.

## Dependencies

**Blocks**:

- None (testing/quality assurance story)

**Requires**:

- Story 2.1: Scenario-to-Prompt Engine
- Story 2.2: Context Window Manager
- Story 2.3: Multi-Timeline Character Consistency

## Acceptance Criteria

- [ ] `ScenarioContextTester` automated test suite with 30+ test scenarios
- [ ] Test categories: Character consistency (10 tests), Event coherence (10 tests), Setting adaptation (10 tests)
- [ ] Each test includes: scenario definition, expected AI behavior, evaluation criteria
- [ ] Automated quality metrics: Coherence score (1-10), Character consistency score (1-10), Creativity score (1-10)
- [ ] **Gemini 2.5 Flash as judge**: Meta-prompting to evaluate AI responses for quality
- [ ] Test report generation: JSON output with pass/fail status, scores, example responses
- [ ] Regression testing: Compare new prompt versions against baseline quality
- [ ] `/api/ai/test-scenario` admin endpoint to run individual scenario tests
- [ ] CI/CD integration: Run test suite on prompt template changes
- [ ] Quality threshold: Average score ≥ 7.0 required to pass

## Technical Notes

**Test Scenario Structure**:

```python
@dataclass
class ScenarioTest:
    test_id: str
    name: str
    category: str  # "character_consistency", "event_coherence", "setting_adaptation"
    scenario: dict  # Scenario parameters
    test_messages: list[str]  # User messages to test with
    evaluation_criteria: dict
    expected_behaviors: list[str]
    min_coherence_score: float = 7.0
```

**Example Test Cases**:

```python
SCENARIO_TESTS = [
    ScenarioTest(
        test_id="CC-001",
        name="Hermione Slytherin Personality Preservation",
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
        test_messages=[
            "How do you feel about your housemates?",
            "What's your approach to studying?",
            "How do you handle conflicts?"
        ],
        evaluation_criteria={
            "intelligence_preserved": "Hermione should still be highly intelligent",
            "ambition_added": "Slytherin traits like ambition should appear",
            "loyalty_adapted": "Loyalty to Draco/Pansy instead of Harry/Ron"
        },
        expected_behaviors=[
            "References studying and books",
            "Mentions Slytherin housemates",
            "Maintains intelligent personality"
        ],
        min_coherence_score=8.0
    ),

    ScenarioTest(
        test_id="EC-001",
        name="Ned Stark Survival Event Coherence",
        category="event_coherence",
        scenario={
            "base_story": "Game of Thrones",
            "scenario_type": "EVENT_ALTERATION",
            "parameters": {
                "event_name": "Ned Stark's Execution",
                "original_outcome": "Ned Stark was executed in King's Landing",
                "altered_outcome": "Ned Stark escaped and returned to Winterfell"
            }
        },
        test_messages=[
            "What happened after you escaped King's Landing?",
            "How does your family react to your return?",
            "What are your plans now?"
        ],
        evaluation_criteria={
            "event_acknowledged": "AI acknowledges escape instead of execution",
            "logical_consequences": "Discusses impact on War of Five Kings",
            "character_preservation": "Ned remains honorable and just"
        },
        expected_behaviors=[
            "Mentions escape from King's Landing",
            "Discusses reunion with family",
            "Maintains honorable character"
        ],
        min_coherence_score=7.5
    ),

    ScenarioTest(
        test_id="SA-001",
        name="Harry Potter Modern Day Setting",
        category="setting_adaptation",
        scenario={
            "base_story": "Harry Potter",
            "scenario_type": "SETTING_MODIFICATION",
            "parameters": {
                "setting_aspect": "time_period",
                "original_setting": "1990s",
                "new_setting": "2024"
            }
        },
        test_messages=[
            "How do you communicate with your friends?",
            "What technology do you use at school?",
            "How has magic adapted to modern times?"
        ],
        evaluation_criteria={
            "modern_tech_integrated": "References smartphones, internet, social media",
            "magic_adapted": "Discusses magic-tech integration",
            "core_story_preserved": "Still about wizard school and Voldemort threat"
        },
        expected_behaviors=[
            "Mentions modern technology",
            "Discusses social media or phones",
            "Maintains magical world elements"
        ],
        min_coherence_score=7.0
    )
]
```

**Automated Quality Evaluation**:

```python
from google import generativeai as genai

class ScenarioQualityEvaluator:

    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.judge_model = genai.GenerativeModel('gemini-2.5-flash')

    async def evaluate_scenario_test(self, test: ScenarioTest) -> TestResult:
        # Generate AI responses for test messages
        conversation_id = await create_test_conversation(test.scenario)
        responses = []

        for message in test.test_messages:
            response = await send_message_and_get_response(
                conversation_id,
                message
            )
            responses.append(response)

        # Evaluate using Gemini 2.5 Flash as judge
        evaluation_prompt = f"""
        Evaluate this AI conversation for quality.

        Scenario: {json.dumps(test.scenario)}
        Expected Behaviors: {json.dumps(test.expected_behaviors)}
        Evaluation Criteria: {json.dumps(test.evaluation_criteria)}

        Conversation:
        {self.format_conversation(test.test_messages, responses)}

        Rate the conversation on three dimensions (1-10 scale):
        1. Coherence: Does the AI maintain logical consistency with the scenario?
        2. Character Consistency: Are character traits preserved correctly?
        3. Creativity: Is the response engaging and imaginative?

        Return ONLY valid JSON:
        {{
          "coherence_score": X,
          "consistency_score": X,
          "creativity_score": X,
          "strengths": ["strength 1", "strength 2"],
          "weaknesses": ["weakness 1", "weakness 2"],
          "passes_criteria": true/false
        }}
        """

        judge_response = await self.judge_model.generate_content_async(
            evaluation_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,  # Low temp for consistent evaluation
                max_output_tokens=1000
            )
        )

        evaluation = json.loads(judge_response.text)

        # Calculate overall score
        avg_score = (
            evaluation["coherence_score"] +
            evaluation["consistency_score"] +
            evaluation["creativity_score"]
        ) / 3

        return TestResult(
            test_id=test.test_id,
            passed=avg_score >= test.min_coherence_score,
            scores=evaluation,
            average_score=avg_score,
            conversation=responses
        )
```

**Test Suite Execution**:

```python
@router.post("/ai/test-suite")
async def run_test_suite(category: str = None):
    """Run automated scenario quality tests"""
    evaluator = ScenarioQualityEvaluator()

    tests_to_run = SCENARIO_TESTS
    if category:
        tests_to_run = [t for t in SCENARIO_TESTS if t.category == category]

    results = []
    for test in tests_to_run:
        result = await evaluator.evaluate_scenario_test(test)
        results.append(result)

    # Calculate suite statistics
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed)
    avg_score = sum(r.average_score for r in results) / total_tests

    return {
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": total_tests - passed_tests,
        "pass_rate": passed_tests / total_tests,
        "average_score": avg_score,
        "results": results,
        "status": "PASS" if avg_score >= 7.0 else "FAIL"
    }
```

## QA Checklist

### Test Coverage

- [ ] 10+ character consistency tests covering different characters and scenarios
- [ ] 10+ event coherence tests covering different event types
- [ ] 10+ setting adaptation tests covering different settings
- [ ] All three scenario types covered

### Automated Evaluation

- [ ] Gemini 2.5 Flash judge provides consistent scores (±0.5 variance on re-run)
- [ ] Evaluation detects obvious failures (nonsensical responses)
- [ ] Evaluation recognizes high-quality responses
- [ ] Scores correlate with human judgment (validate with 10 manual reviews)

### Regression Testing

- [ ] Baseline quality scores recorded for current prompts
- [ ] New prompt versions compared against baseline
- [ ] Regression detected when average score drops >1.0
- [ ] Test results stored in database for historical tracking

### CI/CD Integration

- [ ] Test suite runs automatically on prompt template changes
- [ ] Test suite completes in < 10 minutes
- [ ] Failed tests block deployment
- [ ] Test report generated and stored

### Performance

- [ ] Single test execution < 30s
- [ ] Full suite (30 tests) < 10 minutes
- [ ] Parallel test execution supported (5 concurrent tests)

## Estimated Effort

10 hours
