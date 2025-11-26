"""
Scenario Quality Evaluator - Story 2.4
Uses Gemini 2.5 Flash as AI judge for meta-evaluation of prompt quality
"""

import json
import os
import time
from typing import Dict, List, Optional
from datetime import datetime

from google import generativeai as genai

from app.models.scenario_test import ScenarioTest, TestResult
from app.services.prompt_adapter import PromptAdapter


class ScenarioQualityEvaluator:
    """
    AI Quality Judge using Gemini 2.5 Flash
    
    Evaluates AI conversation quality through meta-prompting:
    - Coherence: Logical consistency with scenario
    - Consistency: Character traits preservation
    - Creativity: Engaging and imaginative responses
    """
    
    def __init__(self):
        """Initialize Gemini 2.5 Flash judge"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.judge_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.prompt_adapter = PromptAdapter()
        
        # Judge configuration for consistent evaluation
        self.judge_config = genai.types.GenerationConfig(
            temperature=0.2,  # Low temperature for consistency
            max_output_tokens=1500,
            response_mime_type="application/json"
        )
    
    async def evaluate_scenario_test(self, test: ScenarioTest) -> TestResult:
        """
        Execute a scenario test and evaluate with Gemini judge
        
        Args:
            test: ScenarioTest to execute
            
        Returns:
            TestResult with scores and evaluation
        """
        start_time = time.time()
        
        # Step 1: Generate AI responses for test messages
        conversation = await self._execute_test_scenario(test)
        
        # Step 2: Evaluate with Gemini judge
        evaluation = await self._judge_conversation(test, conversation)
        
        # Step 3: Calculate results
        execution_time = time.time() - start_time
        
        avg_score = (
            evaluation["coherence_score"] +
            evaluation["consistency_score"] +
            evaluation["creativity_score"]
        ) / 3
        
        passed = (
            avg_score >= test.min_coherence_score and
            evaluation["passes_criteria"]
        )
        
        return TestResult(
            test_id=test.test_id,
            passed=passed,
            scores={
                "coherence_score": evaluation["coherence_score"],
                "consistency_score": evaluation["consistency_score"],
                "creativity_score": evaluation["creativity_score"]
            },
            average_score=round(avg_score, 2),
            conversation=conversation,
            strengths=evaluation["strengths"],
            weaknesses=evaluation["weaknesses"],
            execution_time=round(execution_time, 2),
            timestamp=datetime.now()
        )
    
    async def _execute_test_scenario(self, test: ScenarioTest) -> List[str]:
        """
        Execute test scenario and collect AI responses
        
        Args:
            test: ScenarioTest to execute
            
        Returns:
            List of AI responses
        """
        # Build system prompt using PromptAdapter
        # Use adapt_prompt() with scenario data
        base_prompt = "You are role-playing in an alternate scenario."
        
        try:
            prompt_result = await self.prompt_adapter.adapt_prompt(
                scenario_id=f"test-{test.test_id}",
                base_prompt=base_prompt,
                scenario_data=test.scenario
            )
            system_instruction = prompt_result["system_instruction"]
        except Exception:
            # Fallback: use simple system instruction if adapt_prompt fails
            system_instruction = self._build_simple_system_instruction(test.scenario)
        
        # Simulate conversation with Gemini
        responses = []
        conversation_history = []
        
        for user_message in test.test_messages:
            # Build conversation context
            conversation_context = self._build_conversation_context(
                system_instruction,
                conversation_history,
                user_message
            )
            
            # Generate AI response
            response = await self._generate_ai_response(conversation_context)
            
            # Store in history
            conversation_history.append({
                "role": "user",
                "content": user_message
            })
            conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            responses.append(response)
        
        return responses
    
    def _build_simple_system_instruction(self, scenario: Dict) -> str:
        """
        Build a simple system instruction when PromptAdapter fails
        
        Args:
            scenario: Scenario dictionary
            
        Returns:
            Simple system instruction string
        """
        base_story = scenario.get("base_story", "a story")
        scenario_type = scenario.get("type", scenario.get("scenario_type", "UNKNOWN"))
        parameters = scenario.get("parameters", {})
        
        if scenario_type == "CHARACTER_CHANGE":
            character = parameters.get("character", "the character")
            original = parameters.get("original_property", "")
            new_prop = parameters.get("new_property", "")
            
            return f"""You are role-playing as {character} from {base_story}.
            
In this alternate scenario, instead of {original}, you are {new_prop}.
Maintain the character's core personality while adapting to this change.
Be creative and stay in character throughout the conversation."""
        
        elif scenario_type == "EVENT_ALTERATION":
            event = parameters.get("event_name", "a key event")
            new_outcome = parameters.get("new_outcome", parameters.get("altered_outcome", ""))
            
            return f"""You are role-playing in an alternate version of {base_story}.
            
In this scenario, {event} happened differently: {new_outcome}
Respond as if this alternate outcome is the true history.
Maintain consistency with this alternate timeline."""
        
        elif scenario_type == "SETTING_MODIFICATION":
            setting_aspect = parameters.get("setting_aspect", "setting")
            new_setting = parameters.get("new_setting", "a different setting")
            
            return f"""You are role-playing in an alternate version of {base_story}.
            
In this scenario, the {setting_aspect} is different: {new_setting}
Adapt the story to this new setting while maintaining core themes and characters.
Be creative in how the setting affects the narrative."""
        
        else:
            return f"""You are role-playing in an alternate scenario based on {base_story}.
Respond creatively and maintain consistency with the alternate scenario parameters."""
    
    def _build_conversation_context(
        self,
        system_prompt: str,
        history: List[Dict],
        user_message: str
    ) -> str:
        """Build full conversation context for AI generation"""
        context_parts = [
            f"System Instructions:\n{system_prompt}\n",
            "\nPrevious Conversation:"
        ]
        
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            context_parts.append(f"\n{role}: {msg['content']}")
        
        context_parts.append(f"\n\nUser: {user_message}")
        context_parts.append("\nAssistant:")
        
        return "\n".join(context_parts)
    
    async def _generate_ai_response(self, conversation_context: str) -> str:
        """Generate AI response using Gemini"""
        try:
            # Use higher temperature for creative responses
            response = await self.judge_model.generate_content_async(
                conversation_context,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=500
                )
            )
            return response.text.strip()
        except Exception as e:
            return f"[AI Response Error: {str(e)}]"
    
    async def _judge_conversation(
        self,
        test: ScenarioTest,
        conversation: List[str]
    ) -> Dict:
        """
        Use Gemini 2.5 Flash as judge to evaluate conversation quality
        
        Args:
            test: Original test specification
            conversation: List of AI responses
            
        Returns:
            Evaluation dict with scores and analysis
        """
        evaluation_prompt = self._build_evaluation_prompt(test, conversation)
        
        try:
            judge_response = await self.judge_model.generate_content_async(
                evaluation_prompt,
                generation_config=self.judge_config
            )
            
            # Parse JSON response
            evaluation = json.loads(judge_response.text)
            
            # Validate evaluation structure
            self._validate_evaluation(evaluation)
            
            return evaluation
            
        except json.JSONDecodeError as e:
            # Fallback evaluation on parse error
            return {
                "coherence_score": 5.0,
                "consistency_score": 5.0,
                "creativity_score": 5.0,
                "strengths": ["Unable to evaluate - JSON parse error"],
                "weaknesses": [f"Judge response parsing failed: {str(e)}"],
                "passes_criteria": False
            }
        except Exception as e:
            # Fallback on other errors
            return {
                "coherence_score": 5.0,
                "consistency_score": 5.0,
                "creativity_score": 5.0,
                "strengths": ["Unable to evaluate - judge error"],
                "weaknesses": [f"Judge evaluation failed: {str(e)}"],
                "passes_criteria": False
            }
    
    def _build_evaluation_prompt(
        self,
        test: ScenarioTest,
        conversation: List[str]
    ) -> str:
        """
        Build meta-prompt for Gemini judge evaluation
        
        This is the core of the quality evaluation system.
        The judge evaluates AI responses for coherence, consistency, and creativity.
        """
        formatted_conversation = self._format_conversation_for_judge(
            test.test_messages,
            conversation
        )
        
        return f"""You are an expert AI quality evaluator. Evaluate this AI conversation for quality.

**Scenario Context:**
{json.dumps(test.scenario, indent=2)}

**Test Information:**
- Test ID: {test.test_id}
- Test Name: {test.name}
- Category: {test.category}
- Minimum Score Required: {test.min_coherence_score}

**Expected Behaviors:**
{json.dumps(test.expected_behaviors, indent=2)}

**Evaluation Criteria:**
{json.dumps(test.evaluation_criteria, indent=2)}

**Conversation to Evaluate:**
{formatted_conversation}

**Your Task:**
Rate this conversation on three dimensions using a 1-10 scale:

1. **Coherence Score (1-10)**: Does the AI maintain logical consistency with the scenario? Are responses coherent with the alternate scenario's rules and constraints?

2. **Consistency Score (1-10)**: Are character traits, personality, and behaviors preserved correctly according to the scenario modifications? Does the character feel authentic?

3. **Creativity Score (1-10)**: Is the response engaging, imaginative, and well-written? Does it show depth and nuance?

**Scoring Guidelines:**
- 9-10: Exceptional quality, exceeds expectations
- 7-8: Good quality, meets expectations
- 5-6: Acceptable quality, minor issues
- 3-4: Poor quality, significant issues
- 1-2: Unacceptable quality, major failures

**Output Requirements:**
Return ONLY valid JSON with this exact structure:
{{
  "coherence_score": <float 1-10>,
  "consistency_score": <float 1-10>,
  "creativity_score": <float 1-10>,
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "passes_criteria": <boolean>
}}

The "passes_criteria" field should be true if the conversation meets all evaluation criteria, false otherwise.

Be objective, thorough, and constructive in your evaluation."""
    
    def _format_conversation_for_judge(
        self,
        messages: List[str],
        responses: List[str]
    ) -> str:
        """Format conversation in readable format for judge"""
        formatted = []
        for i, (msg, resp) in enumerate(zip(messages, responses), 1):
            formatted.append(f"Turn {i}:")
            formatted.append(f"  User: {msg}")
            formatted.append(f"  AI: {resp}")
            formatted.append("")
        return "\n".join(formatted)
    
    def _validate_evaluation(self, evaluation: Dict) -> None:
        """Validate judge evaluation has required fields"""
        required_fields = [
            "coherence_score",
            "consistency_score",
            "creativity_score",
            "strengths",
            "weaknesses",
            "passes_criteria"
        ]
        
        for field in required_fields:
            if field not in evaluation:
                raise ValueError(f"Missing required field in evaluation: {field}")
        
        # Validate score ranges
        for score_field in ["coherence_score", "consistency_score", "creativity_score"]:
            score = evaluation[score_field]
            if not isinstance(score, (int, float)) or not (1 <= score <= 10):
                raise ValueError(f"Invalid score for {score_field}: {score}")
        
        # Validate lists
        if not isinstance(evaluation["strengths"], list):
            raise ValueError("strengths must be a list")
        if not isinstance(evaluation["weaknesses"], list):
            raise ValueError("weaknesses must be a list")
        
        # Validate boolean
        if not isinstance(evaluation["passes_criteria"], bool):
            raise ValueError("passes_criteria must be a boolean")
    
    async def evaluate_multiple_tests(
        self,
        tests: List[ScenarioTest]
    ) -> List[TestResult]:
        """
        Evaluate multiple tests sequentially
        
        Args:
            tests: List of ScenarioTest to evaluate
            
        Returns:
            List of TestResult
        """
        results = []
        for test in tests:
            result = await self.evaluate_scenario_test(test)
            results.append(result)
        
        return results
