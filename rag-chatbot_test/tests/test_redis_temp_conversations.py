"""
Redis 임시 대화 저장 테스트

임시 대화가 Redis에 올바르게 저장/조회/삭제되는지 테스트합니다.
"""

import pytest
import json
import uuid
from datetime import datetime
from app.config.redis_client import (
    save_temp_conversation,
    get_temp_conversation,
    delete_temp_conversation,
    exists_temp_conversation
)


def test_save_and_get_temp_conversation():
    """임시 대화 저장 및 조회 테스트"""
    conversation_id = str(uuid.uuid4())
    
    # 테스트 데이터
    test_data = {
        "scenario_id": "test-scenario-123",
        "messages": [
            {
                "role": "user",
                "content": "안녕하세요",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "turn": 1
            },
            {
                "role": "assistant",
                "content": "안녕하세요! 무엇을 도와드릴까요?",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "turn": 1
            }
        ],
        "turn_count": 1,
        "is_creator": True,
        "conversation_partner_type": "stranger",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    # 저장
    result = save_temp_conversation(conversation_id, test_data, ttl=60)
    assert result is True, "임시 대화 저장 실패"
    
    # 존재 확인
    exists = exists_temp_conversation(conversation_id)
    assert exists is True, "임시 대화가 존재하지 않음"
    
    # 조회
    retrieved_data = get_temp_conversation(conversation_id)
    assert retrieved_data is not None, "임시 대화 조회 실패"
    assert retrieved_data["scenario_id"] == test_data["scenario_id"], "시나리오 ID 불일치"
    assert retrieved_data["turn_count"] == test_data["turn_count"], "턴 수 불일치"
    assert len(retrieved_data["messages"]) == len(test_data["messages"]), "메시지 수 불일치"
    
    # 정리
    delete_temp_conversation(conversation_id)


def test_delete_temp_conversation():
    """임시 대화 삭제 테스트"""
    conversation_id = str(uuid.uuid4())
    
    # 저장
    test_data = {
        "scenario_id": "test-scenario-456",
        "messages": [],
        "turn_count": 0,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    save_temp_conversation(conversation_id, test_data, ttl=60)
    
    # 존재 확인
    assert exists_temp_conversation(conversation_id) is True, "저장 후 존재하지 않음"
    
    # 삭제
    result = delete_temp_conversation(conversation_id)
    assert result is True, "임시 대화 삭제 실패"
    
    # 존재 확인 (삭제 후)
    exists = exists_temp_conversation(conversation_id)
    assert exists is False, "삭제 후에도 존재함"
    
    # 조회 (삭제 후)
    retrieved_data = get_temp_conversation(conversation_id)
    assert retrieved_data is None, "삭제 후에도 조회됨"


def test_nonexistent_conversation():
    """존재하지 않는 임시 대화 조회 테스트"""
    conversation_id = str(uuid.uuid4())
    
    # 존재 확인
    exists = exists_temp_conversation(conversation_id)
    assert exists is False, "존재하지 않는 대화가 존재함"
    
    # 조회
    retrieved_data = get_temp_conversation(conversation_id)
    assert retrieved_data is None, "존재하지 않는 대화가 조회됨"


def test_ttl_expiration():
    """TTL 만료 테스트 (1초 TTL)"""
    conversation_id = str(uuid.uuid4())
    
    # 1초 TTL로 저장
    test_data = {
        "scenario_id": "test-scenario-ttl",
        "messages": [],
        "turn_count": 0,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    save_temp_conversation(conversation_id, test_data, ttl=1)
    
    # 즉시 조회 (존재해야 함)
    assert exists_temp_conversation(conversation_id) is True, "저장 직후 존재하지 않음"
    
    # 2초 대기
    import time
    time.sleep(2)
    
    # 만료 후 조회 (존재하지 않아야 함)
    exists = exists_temp_conversation(conversation_id)
    assert exists is False, "TTL 만료 후에도 존재함"
    
    retrieved_data = get_temp_conversation(conversation_id)
    assert retrieved_data is None, "TTL 만료 후에도 조회됨"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

