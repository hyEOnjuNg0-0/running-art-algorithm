#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git 커밋 스크립트
손상된 git 저장소에서 변경사항을 커밋하고 푸시
"""
import os
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    """명령 실행"""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def main():
    repo_path = Path(__file__).parent
    
    print("=== Git 상태 확인 ===")
    code, stdout, stderr = run_command("git status --short", cwd=repo_path)
    print(stdout)
    
    print("\n=== 변경사항 추가 ===")
    code, stdout, stderr = run_command("git add -A", cwd=repo_path)
    if code != 0:
        print(f"Error: {stderr}")
        return False
    print("스테이징 완료")
    
    print("\n=== 커밋 생성 ===")
    message = """Phase 2, 3 implementation complete

Phase 2: Data Layer (OSM)
- Node, Edge, RoadGraph entities
- GraphRepository interface and OSMGraphRepository implementation
- Graph caching service with pickle and JSON support

Phase 3: Shape Processing
- Shape templates (Circle, Heart, Star, Digits 0-9)
- Shape transformer (rotation, scaling, coordinate conversion)
- Shape processor (user input handling, simplification, smoothing)

Total tests passed: 78"""
    
    cmd = f'git commit -m "{message}"'
    code, stdout, stderr = run_command(cmd, cwd=repo_path)
    
    if code == 0:
        print("커밋 성공!")
        print(stdout)
        
        print("\n=== 푸시 ===")
        code, stdout, stderr = run_command("git push origin main", cwd=repo_path)
        if code == 0:
            print("푸시 성공!")
            print(stdout)
            return True
        else:
            print(f"푸시 실패: {stderr}")
            return False
    else:
        print(f"커밋 실패: {stderr}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
