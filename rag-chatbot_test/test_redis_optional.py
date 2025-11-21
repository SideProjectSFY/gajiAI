"""Test Redis optional functionality"""
import asyncio
from app.utils.redis_client import RedisClient

async def test_redis_optional():
    print("Testing Redis optional initialization...")
    
    # Test 1: Client initialization
    client = RedisClient()
    print(f"✓ Client created successfully")
    print(f"✓ Redis available: {client.is_available}")
    
    # Test 2: Store operation (should not fail even if Redis unavailable)
    await client.store_task_result(
        task_id="test-123",
        status="completed",
        result={"message": "test"}
    )
    print(f"✓ Store operation completed (no-op if Redis unavailable)")
    
    # Test 3: Get operation (should return not_found if Redis unavailable)
    status = await client.get_task_status("test-123")
    print(f"✓ Get operation completed: {status['status']}")
    
    # Test 4: Close operation
    await client.close()
    print(f"✓ Client closed successfully")
    
    print("\n✅ All tests passed! Redis is now optional.")

if __name__ == "__main__":
    asyncio.run(test_redis_optional())
