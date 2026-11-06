#!/usr/bin/env python3 -u
# -*- coding: utf-8 -*-

"""
=============================================================================
[프랜차이즈 대시보드 실시간 폴더 감시자 (auto_watcher.py)]
- 역할: Dashboard 폴더를 1초마다 자동으로 실시간 감시합니다.
        새로운 브랜드 분석 HTML 리포트가 복사되거나 기존 파일이 수정되면,
        0.5초 이내에 build_dashboard.py를 호출하여 대시보드 데이터를 최신화합니다.
- 실행법: 터미널에서 python3 auto_watcher.py
          (또는 '대시보드_자동업데이트_실행.command' 더블클릭)
=============================================================================
"""

import os
import time
import subprocess
import sys

# 1. 감시할 폴더 및 빌더 스크립트 경로 설정
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_SCRIPT = os.path.join(CURRENT_DIR, "build_dashboard.py")

def get_html_files_snapshot(folder_path):
    """
    폴더 내의 모든 분석 리포트 HTML 파일의 {파일명: 최종수정시각} 스냅샷을 반환하는 함수
    (단, 메인 대시보드인 index.html은 제외합니다)
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
    build_dashboard.py 스크립트를 실행하여 dashboard_data.js를 재생성하는 함수
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
            print(f"[{current_time}] ⚡ [자동 빌드 완료] 대시보드 데이터가 최신으로 갱신되었습니다!", flush=True)
        else:
            print(f"❌ 빌드 실패:\n{result.stderr}", flush=True)
    except Exception as e:
        print(f"❌ 빌드 실행 에러: {e}", flush=True)

def main():
    print("=" * 65, flush=True)
    print("🤖 [프랜차이즈 대시보드 실시간 자동 감시자 가동 시작]", flush=True)
    print(f"📁 실시간 감시 대상 폴더: {CURRENT_DIR}", flush=True)
    print("ℹ️  새로운 분석 리포트(.html)를 이 폴더에 넣기만 하면 즉시 반영됩니다.", flush=True)
    print("ℹ️  종료하려면 창을 닫거나 터미널에서 Ctrl + C 를 누르세요.", flush=True)
    print("=" * 65, flush=True)

    # 최초 1회 즉시 빌드 수행하여 현재 상태 보장
    run_build()

    # 현재 파일 상태 스냅샷 저장
    last_snapshot = get_html_files_snapshot(CURRENT_DIR)
    print(f"👀 현재 감시 중인 리포트 수: {len(last_snapshot)}개", flush=True)
    print("-----------------------------------------------------------------", flush=True)

    # 1초 주기로 폴더 변경 사항 감시
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
                
                if added_files:
                    for f in added_files:
                        print(f"  ➕ 신규 리포트 투입 감지: {f}", flush=True)
                if modified_files:
                    for f in modified_files:
                        print(f"  ✏️ 기존 리포트 수정 감지: {f}", flush=True)
                if removed_files:
                    for f in removed_files:
                        print(f"  🗑️ 리포트 삭제 감지: {f}", flush=True)

                # 파일 쓰기가 완료될 때까지 잠시 대기
                time.sleep(0.4)

                # 대시보드 데이터 자동 재빌드
                run_build()

                # 최신 스냅샷 갱신
                last_snapshot = get_html_files_snapshot(CURRENT_DIR)

    except KeyboardInterrupt:
        print("\n\n🛑 [실시간 감시자가 안전하게 종료되었습니다]", flush=True)

if __name__ == "__main__":
    main()
