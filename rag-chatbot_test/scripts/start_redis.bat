@echo off
REM Redis 서버 실행 스크립트 (Windows)
REM Docker를 사용하여 Redis를 실행합니다

echo Redis 서버를 시작합니다...
echo.

REM Docker가 설치되어 있는지 확인
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Docker가 설치되어 있지 않습니다.
    echo.
    echo Redis를 실행하는 방법:
    echo 1. Docker Desktop 설치: https://www.docker.com/products/docker-desktop
    echo 2. 또는 Windows용 Redis 설치: https://github.com/microsoftarchive/redis/releases
    echo.
    pause
    exit /b 1
)

REM 기존 Redis 컨테이너가 실행 중인지 확인
docker ps | findstr "redis" >nul 2>&1
if %errorlevel% equ 0 (
    echo [정보] Redis 컨테이너가 이미 실행 중입니다.
    pause
    exit /b 0
)

REM Redis 컨테이너 시작 (없으면 생성)
echo Redis 컨테이너를 시작합니다...
docker run -d -p 6379:6379 --name gaji-redis redis:latest

if %errorlevel% equ 0 (
    echo [성공] Redis 서버가 시작되었습니다.
    echo 포트: 6379
    echo.
    echo 컨테이너 중지: docker stop gaji-redis
    echo 컨테이너 삭제: docker rm gaji-redis
) else (
    echo [오류] Redis 서버 시작 실패
)

pause

