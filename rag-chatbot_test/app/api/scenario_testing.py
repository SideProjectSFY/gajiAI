"""
API Endpoints for Scenario Testing - Story 2.4
Admin endpoints for running automated quality tests
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from app.models.scenario_test import TestSuiteResult
from app.services.scenario_tests import (
    ALL_SCENARIO_TESTS,
    get_tests_by_category,
    get_test_by_id
)
from app.services.scenario_quality_evaluator import ScenarioQualityEvaluator


router = APIRouter(prefix="/ai", tags=["Scenario Testing"])


@router.post("/test-suite", response_model=dict)
async def run_test_suite(
    category: Optional[str] = None
) -> dict:
    """
    Run automated scenario quality test suite
    
    Args:
        category: Optional filter by category (character_consistency, event_coherence, setting_adaptation)
        
    Returns:
        Test suite results with statistics
    """
    # Select tests to run
    if category:
        valid_categories = ["character_consistency", "event_coherence", "setting_adaptation"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {valid_categories}"
            )
        tests_to_run = get_tests_by_category(category)
        if not tests_to_run:
            raise HTTPException(
                status_code=404,
                detail=f"No tests found for category: {category}"
            )
    else:
        tests_to_run = ALL_SCENARIO_TESTS
    
    # Initialize evaluator
    try:
        evaluator = ScenarioQualityEvaluator()
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize evaluator: {str(e)}"
        )
    
    # Run tests
    start_time = datetime.now()
    results = await evaluator.evaluate_multiple_tests(tests_to_run)
    execution_time = (datetime.now() - start_time).total_seconds()
    
    # Calculate suite statistics
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed)
    failed_tests = total_tests - passed_tests
    pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
    average_score = sum(r.average_score for r in results) / total_tests if total_tests > 0 else 0.0
    
    # Determine suite status
    status = "PASS" if average_score >= 7.0 and pass_rate >= 0.8 else "FAIL"
    
    # Build test suite result
    suite_result = TestSuiteResult(
        total_tests=total_tests,
        passed=passed_tests,
        failed=failed_tests,
        pass_rate=round(pass_rate, 3),
        average_score=round(average_score, 2),
        results=results,
        status=status,
        execution_time=round(execution_time, 2),
        timestamp=datetime.now()
    )
    
    return suite_result.to_dict()


@router.post("/test-scenario/{test_id}", response_model=dict)
async def run_single_test(test_id: str) -> dict:
    """
    Run a single scenario test by ID
    
    Args:
        test_id: Test ID (e.g., "CC-001", "EC-005", "SA-010")
        
    Returns:
        Individual test result
    """
    # Find test
    test = get_test_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=404,
            detail=f"Test not found: {test_id}"
        )
    
    # Initialize evaluator
    try:
        evaluator = ScenarioQualityEvaluator()
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize evaluator: {str(e)}"
        )
    
    # Run test
    result = await evaluator.evaluate_scenario_test(test)
    
    return result.to_dict()


@router.get("/test-categories", response_model=dict)
async def get_test_categories() -> dict:
    """
    Get available test categories and counts
    
    Returns:
        Test categories with counts
    """
    categories = {}
    
    for test in ALL_SCENARIO_TESTS:
        if test.category not in categories:
            categories[test.category] = 0
        categories[test.category] += 1
    
    return {
        "total_tests": len(ALL_SCENARIO_TESTS),
        "categories": categories,
        "available_categories": list(categories.keys())
    }


@router.get("/test-list", response_model=dict)
async def list_all_tests(category: Optional[str] = None) -> dict:
    """
    List all available tests
    
    Args:
        category: Optional filter by category
        
    Returns:
        List of tests with metadata
    """
    if category:
        tests = get_tests_by_category(category)
    else:
        tests = ALL_SCENARIO_TESTS
    
    test_list = [
        {
            "test_id": t.test_id,
            "name": t.name,
            "category": t.category,
            "min_coherence_score": t.min_coherence_score,
            "message_count": len(t.test_messages)
        }
        for t in tests
    ]
    
    return {
        "total": len(test_list),
        "tests": test_list
    }
