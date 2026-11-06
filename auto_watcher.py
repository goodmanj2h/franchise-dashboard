#!/usr/bin/env python3 -u
# -*- coding: utf-8 -*-

"""
=============================================================================
[프랜차이즈 대시보드 실시간 폴더 감시 및 클라우드 자동 배포자 (auto_watcher.py)]
- 역할: 
  1. Dashboard 폴더를 1초마다 실시간 감시합니다.
  2. 새 리포트 HTML 파일이 추가되거나 수정되면,
     0.5초 이내에 로컬 대시보드 데이터(dashboard_data.js)를 즉시 빌드합니다.
  3. 동시에 GitHub 클라우드 저장소(goodmanj2h/franchise-dashboard)로 
     자동 git push를 실행하여 스마트폰 화면까지 실시간 동기화합니다!
=============================================================================
"""

import os
import time
import subprocess
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_SCRIPT = os.path.join(CURRENT_DIR, "build_dashboard.py")
GITHUB_SITE_URL = "https://goodmanj2h.github.io/franchise-dashboard/"

def get_html_files_snapshot(folder_path):
    """
    폴더 내의 모든 분석 리포트 HTML 파일의 {파일명: 최종수정시각} 스냅샷을 반환하는 함수
    (메인 대시보드인 index.html은 제외합니다)
    """
    snapshot = {}
    try:
        for entry in os.scandir(folder_path):
            if entry.is_file() and entry.name.lower().endswith(".html"):
                if not entry.name.lower().startswith("index"):
                    snapshot[entry.name] = entry.stat().st_mtime
    except Exception as e:
        print(f"⚠️ 폴더 스캔 중 일시적 오류 (무시 가능): {e}", flush=True)
    return snapshot

def run_build():
    """
    build_dashboard.py 스크립트를 실행하여 로컬 dashboard_data.js를 재생성하는 함수
    """
    try:
        result = subprocess.run(
            [sys.executable, BUILD_SCRIPT],
            cwd=CURRENT_DIR,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            current_time = time.strftime("%H:%M:%S")
            print(f"[{current_time}] ⚡ [1단계: 로컬 빌드 완료] 내 컴퓨터 대시보드가 최신으로 갱신되었습니다!", flush=True)
            return True
        else:
            print(f"❌ 빌드 실패:\n{result.stderr}", flush=True)
            return False
    except Exception as e:
        print(f"❌ 빌드 실행 에러: {e}", flush=True)
        return False

def run_cloud_push(event_reason="새로운 리포트 추가"):
    """
    GitHub 저장소로 자동 커밋 & 푸시하여 스마트폰(GitHub Pages)까지 배포하는 함수
    """
    try:
        current_time = time.strftime("%H:%M:%S")
        print(f"[{current_time}] ☁️  [2단계: 클라우드 자동 배포 진행 중...]", flush=True)

        # 1. 파일 전체 스테이징
        subprocess.run(["git", "add", "-A"], cwd=CURRENT_DIR, capture_output=True)

        # 2. 변경사항 자동 커밋
        commit_msg = f"Auto deploy: {event_reason} ({time.strftime('%Y-%m-%d %H:%M:%S')})"
        commit_res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=CURRENT_DIR, capture_output=True, text=True)

        # 3. 비대화형 git push 실행 (터미널 멈춤 방지)
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        push_res = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=CURRENT_DIR,
            capture_output=True,
            text=True,
            env=env
        )

        if push_res.returncode == 0:
            print(f"[{current_time}] 🎉 [클라우드 배포 성공!] 스마트폰 주소에 반영 요청되었습니다.", flush=True)
            print(f"   👉 스마트폰 확인: {GITHUB_SITE_URL}", flush=True)
            print(f"   (💡 GitHub가 사이트를 빌드하는 데 약 30초~1분 정도 소요됩니다.)", flush=True)
        else:
            # 인증 권한이 없는 경우 친절한 안내
            if "could not read Username" in push_res.stderr or "Permission to" in push_res.stderr or "Authentication failed" in push_res.stderr:
                print(f"[{current_time}] 💡 [안내] 깃허브 무인 자동 배포 권한이 아직 설정되지 않았습니다.", flush=True)
                print(f"   ➔ 폴더 안의 [설정_깃허브_자동배포_토큰등록.command]를 1회 실행하시면", flush=True)
                print(f"      스마트폰 자동 배포가 영구적으로 가동됩니다!", flush=True)
            else:
                print(f"⚠️ 클라우드 배포 스킵 또는 경고: {push_res.stderr.strip()}", flush=True)

    except Exception as e:
        print(f"❌ 클라우드 배포 실행 중 오류: {e}", flush=True)

def main():
    print("=" * 65, flush=True)
    print("🤖 [프랜차이즈 대시보드 실시간 자동 감시 & 클라우드 배포자 가동]", flush=True)
    print(f"📁 감시 폴더: {CURRENT_DIR}", flush=True)
    print(f"📱 스마트폰 주소: {GITHUB_SITE_URL}", flush=True)
    print("ℹ️  새로운 분석 리포트(.html)를 이 폴더에 넣기만 하면 즉시 반영됩니다.", flush=True)
    print("ℹ️  종료하려면 창을 닫거나 터미널에서 Ctrl + C 를 누르세요.", flush=True)
    print("=" * 65, flush=True)

    # 최초 1회 로컬 빌드 수행
    run_build()

    last_snapshot = get_html_files_snapshot(CURRENT_DIR)
    print(f"👀 현재 감시 중인 리포트 수: {len(last_snapshot)}개", flush=True)
    print("-----------------------------------------------------------------", flush=True)

    try:
        while True:
            time.sleep(1.0)
            current_snapshot = get_html_files_snapshot(CURRENT_DIR)

            added_files = set(current_snapshot.keys()) - set(last_snapshot.keys())
            removed_files = set(last_snapshot.keys()) - set(current_snapshot.keys())

            modified_files = set()
            for name, mtime in current_snapshot.items():
                if name in last_snapshot and mtime > last_snapshot[name]:
                    modified_files.add(name)

            if added_files or removed_files or modified_files:
                current_time = time.strftime("%H:%M:%S")
                print(f"\n🔔 [{current_time}] 폴더 변경 감지됨!", flush=True)
                
                reason = ""
                if added_files:
                    for f in added_files:
                        print(f"  ➕ 신규 리포트 투입 감지: {f}", flush=True)
                    reason = f"신규 리포트 추가 ({', '.join(added_files)})"
                if modified_files:
                    for f in modified_files:
                        print(f"  ✏️ 기존 리포트 수정 감지: {f}", flush=True)
                    reason = f"리포트 수정 ({', '.join(modified_files)})"
                if removed_files:
                    for f in removed_files:
                        print(f"  🗑️ 리포트 삭제 감지: {f}", flush=True)
                    reason = f"리포트 삭제 ({', '.join(removed_files)})"

                # 파일 복사 완료 대기
                time.sleep(0.4)

                # 1. 로컬 대시보드 데이터 빌드
                build_success = run_build()

                # 2. 클라우드(GitHub Pages) 자동 배포 실행
                if build_success:
                    run_cloud_push(reason)

                # 스냅샷 갱신
                last_snapshot = get_html_files_snapshot(CURRENT_DIR)

    except KeyboardInterrupt:
        print("\n\n🛑 [실시간 감시자가 안전하게 종료되었습니다]", flush=True)

if __name__ == "__main__":
    main()
