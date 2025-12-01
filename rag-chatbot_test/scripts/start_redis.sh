#!/bin/bash
# Redis 서버 실행 스크립트 (Linux/Mac)
# Docker를 사용하여 Redis를 실행합니다

echo "Redis 서버를 시작합니다..."
echo ""

# Docker가 설치되어 있는지 확인
if ! command -v docker &> /dev/null; then
    echo "[오류] Docker가 설치되어 있지 않습니다."
    echo ""
    echo "Redis를 실행하는 방법:"
    echo "1. Docker 설치: https://www.docker.com/products/docker-desktop"
    echo "2. 또는 로컬에 Redis 설치: sudo apt-get install redis-server (Ubuntu)"
    echo ""
    exit 1
fi

# 기존 Redis 컨테이너가 실행 중인지 확인
if docker ps | grep -q "redis"; then
    echo "[정보] Redis 컨테이너가 이미 실행 중입니다."
    exit 0
fi

# Redis 컨테이너 시작 (없으면 생성)
echo "Redis 컨테이너를 시작합니다..."
docker run -d -p 6379:6379 --name gaji-redis redis:latest

if [ $? -eq 0 ]; then
    echo "[성공] Redis 서버가 시작되었습니다."
    echo "포트: 6379"
    echo ""
    echo "컨테이너 중지: docker stop gaji-redis"
    echo "컨테이너 삭제: docker rm gaji-redis"
else
    echo "[오류] Redis 서버 시작 실패"
    exit 1
fi

