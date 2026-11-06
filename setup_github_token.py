#!/usr/bin/env python3 -u
# -*- coding: utf-8 -*-

"""
=============================================================================
[GitHub 스마트폰 자동 배포를 위한 1회성 토큰 설정 도구]
- 역할: 맥북이 깃허브로 백그라운드 무인 자동 전송(Push)을 할 수 있도록
        1회성 개인 액세스 토큰(PAT)을 안전하게 연동합니다.
=============================================================================
"""

import os
import sys
import subprocess
import webbrowser

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
GITHUB_USER = "goodmanj2h"
REPO_NAME = "franchise-dashboard"

def main():
    print("=" * 65)
    print("🔑 [GitHub 스마트폰 자동 배포 1회성 권한 설정]")
    print("=" * 65)
    print("스마트폰(GitHub Pages)으로 리포트가 자동으로 업로드되려면,")
    print("맥북에 '자동 전송 권한 토큰'을 딱 1번만 등록해 주시면 됩니다.")
    print("-----------------------------------------------------------------")
    print("💡 [토큰 발급 30초 안내]:")
    print("1. 잠시 후 깃허브 토큰 생성 페이지가 브라우저로 열립니다.")
    print("2. [Note]에 'franchise' 입력")
    print("3. [Expiration]에서 'No expiration'(기한 없음) 선택")
    print("4. [Select scopes]에서 맨 위에 있는 ✅ [repo] 체크박스 1개만 체크!")
    print("5. 맨 아래 초록색 [Generate token] 버튼을 누르면 'ghp_...' 로 시작하는")
    print("   초록색 토큰 번호가 나옵니다. (우측 복사 아이콘 클릭)")
    print("-----------------------------------------------------------------")

    input("👉 준비되셨으면 [엔터(Enter)]를 누르세요. 깃허브 페이지를 엽니다...")
    webbrowser.open("https://github.com/settings/tokens/new?description=franchise-auto-deploy&scopes=repo")

    print("\n복사하신 토큰(ghp_로 시작하는 문자열)을 아래에 붙여넣어 주세요:")
    token = input("👉 토큰 붙여넣기: ").strip()

    if not token or not token.startswith("ghp_") and not token.startswith("github_pat_"):
        print("\n⚠️ 올바른 깃허브 토큰 형식이 아닙니다 (ghp_... 로 시작해야 합니다).")
        confirm = input("그래도 이 값으로 등록을 시도할까요? (y/n): ").strip().lower()
        if confirm != 'y':
            print("취소되었습니다.")
            return

    # 원격 URL을 토큰이 포함된 형태로 설정
    auth_remote_url = f"https://{GITHUB_USER}:{token}@github.com/{GITHUB_USER}/{REPO_NAME}.git"
    
    try:
        subprocess.run(["git", "remote", "set-url", "origin", auth_remote_url], cwd=CURRENT_DIR, check=True)
        print("\n⚙️ 저장소 원격 주소에 토큰이 안전하게 연동되었습니다.")
        print("🚀 지금 바로 최신 데이터(4. 반궁 포함)를 깃허브로 자동 배포 테스트합니다...")

        # 커밋 & 푸시 테스트
        subprocess.run(["git", "add", "-A"], cwd=CURRENT_DIR, check=True)
        subprocess.run(["git", "commit", "-m", "자동 배포 토큰 연동 및 최신 리포트 동기화"], cwd=CURRENT_DIR)
        
        push_res = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=CURRENT_DIR, capture_output=True, text=True)

        if push_res.returncode == 0:
            print("\n" + "=" * 65)
            print("🎉🎉 [축하합니다! 무인 자동 배포 연동이 완벽하게 완료되었습니다!]")
            print(f"📱 스마트폰 주소: https://{GITHUB_USER}.github.io/{REPO_NAME}/")
            print("-----------------------------------------------------------------")
            print("이제 앞으로는 [대시보드_자동업데이트_실행.command]만 켜두시면,")
            print("폴더에 리포트 파일을 넣는 즉시 컴퓨터 대시보드와 스마트폰 주소까지")
            print("완전 자동으로 실시간 동시 업데이트됩니다!")
            print("=" * 65)
        else:
            print(f"\n❌ 전송 실패:\n{push_res.stderr}")
            print("토큰 값을 다시 확인해 주세요.")

    except Exception as e:
        print(f"❌ 설정 중 오류 발생: {e}")

if __name__ == "__main__":
    main()

