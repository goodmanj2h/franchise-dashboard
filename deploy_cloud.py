#!/usr/bin/env python3 -u
# -*- coding: utf-8 -*-

"""
=============================================================================
[프랜차이즈 대시보드 24시간 모바일 클라우드 배포 도구 (deploy_cloud.py)]
- 역할: 내 컴퓨터가 꺼져 있어도 스마트폰으로 24시간 접속할 수 있도록
        무료 글로벌 클라우드에 대시보드를 배포하고 스마트폰 접속 주소를 발급합니다.
=============================================================================
"""

import os
import sys
import subprocess
import webbrowser
import socket

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_local_ip():
    """현재 컴퓨터의 로컬 와이파이 IP 주소 확인"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def print_banner():
    print("=" * 65)
    print("📱 [프랜차이즈 대시보드 24시간 모바일 클라우드 배포 센터]")
    print("   '내 컴퓨터가 꺼져 있어도 스마트폰에서 언제든 접속 가능!'")
    print("=" * 65)

def run_pre_build():
    """배포 전 최신 데이터로 build_dashboard.py 실행"""
    print("\n📦 [1단계] 최신 데이터 동기화 확인 중...")
    build_script = os.path.join(CURRENT_DIR, "build_dashboard.py")
    res = subprocess.run([sys.executable, build_script], cwd=CURRENT_DIR, capture_output=True, text=True)
    if res.returncode == 0:
        print("  ✅ 최신 리포트 데이터셋 동기화 완료!")
    else:
        print(f"  ⚠️ 빌드 경고:\n{res.stderr}")

def deploy_option_web_drop():
    """
    옵션 A: 별도 코딩이나 계정 설정 없이 웹 브라우저에 폴더만 끌어다 놓는 초간단 방식 (3초 컷)
    """
    print("\n" + "=" * 65)
    print("🚀 [방식 1: 3초 웹 드래그 배포 (가장 쉽고 추천!)]")
    print("=" * 65)
    print("1. 잠시 후 무료 웹 호스팅(Netlify Drop) 사이트와 현재 폴더가 열립니다.")
    print("2. 열린 웹 브라우저 화면의 점선 네모 박스 안으로")
    print("   지금 열린 [Dashboard] 폴더를 마우스로 '쓱' 끌어다 놓으세요.")
    print("3. 단 3초 만에 24시간 컴퓨터가 꺼져도 열리는 전용 모바일 주소가 생성됩니다!")
    print("-----------------------------------------------------------------")
    input("👉 준비되셨으면 [엔터(Enter)]를 누르세요...")

    # Netlify Drop 페이지 열기
    webbrowser.open("https://app.netlify.com/drop")
    # 맥북 Finder로 현재 Dashboard 폴더 열기
    subprocess.run(["open", CURRENT_DIR])

    print("\n🎉 브라우저와 폴더가 열렸습니다! 웹 창으로 폴더를 끌어다 놓으시면 배포가 끝납니다.")

def deploy_option_github():
    """
    옵션 B: GitHub Pages를 이용한 영구 무료 자동 배포
    """
    print("\n" + "=" * 65)
    print("🐙 [방식 2: GitHub Pages 영구 무료 호스팅 배포]")
    print("=" * 65)
    print("GitHub 계정에 저장소를 연결하여 영구적인 전용 주소를 만듭니다.")
    print("주소 형태: https://<내아이디>.github.io/<저장소명>/")
    print("-----------------------------------------------------------------")
    
    username = input("1. GitHub 아이디(Username)를 입력하세요 (예: myid): ").strip()
    if not username:
        print("❌ 아이디가 입력되지 않아 취소되었습니다.")
        return

    repo_name = input("2. 생성할 GitHub 저장소(Repository) 이름을 입력하세요 [기본값: franchise-dashboard]: ").strip()
    if not repo_name:
        repo_name = "franchise-dashboard"

    print(f"\n⚙️ 깃허브 배포를 준비합니다 -> https://github.com/{username}/{repo_name}")
    print("💡 만약 깃허브 웹사이트에 아직 해당 저장소가 없다면,")
    print(f"   브라우저에서 https://github.com/new 로 접속해 [{repo_name}] Public 저장소를 먼저 생성해 주세요.")
    
    confirm = input("👉 계속 진행하시겠습니까? (y/n): ").strip().lower()
    if confirm != 'y':
        print("취소되었습니다.")
        return

    try:
        # git init 및 커밋
        subprocess.run(["git", "init"], cwd=CURRENT_DIR, check=True)
        subprocess.run(["git", "add", "."], cwd=CURRENT_DIR, check=True)
        subprocess.run(["git", "commit", "-m", "Deploy Franchise Dashboard"], cwd=CURRENT_DIR)
        subprocess.run(["git", "branch", "-M", "main"], cwd=CURRENT_DIR, check=True)
        
        remote_url = f"https://github.com/{username}/{repo_name}.git"
        subprocess.run(["git", "remote", "remove", "origin"], cwd=CURRENT_DIR, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=CURRENT_DIR, check=True)

        print(f"\n🚀 GitHub로 파일들을 전송합니다 (git push)...")
        push_res = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=CURRENT_DIR)

        if push_res.returncode == 0:
            site_url = f"https://{username}.github.io/{repo_name}/"
            print("\n" + "=" * 65)
            print("🎉 [축하합니다! 깃허브 배포가 완료되었습니다]")
            print(f"📱 스마트폰 24시간 전용 접속 주소:\n   👉 {site_url}")
            print("\n💡 [마지막 1단계 설정]:")
            print(f"1. https://github.com/{username}/{repo_name}/settings/pages 에 접속합니다.")
            print("2. Build and deployment의 Source를 [Deploy from a branch]로 선택하고,")
            print("   Branch를 [main] / [/ (root)]로 선택 후 [Save]를 누르면 끝납니다!")
            print("=" * 65)
        else:
            print("\n⚠️ 깃허브 푸시 중 로그인 인증이 필요할 수 있습니다.")
            print("깃허브 개인 액세스 토큰(PAT)을 확인하시거나, [방식 1(웹 드래그)]을 이용해 보세요.")
    except Exception as e:
        print(f"❌ 깃허브 배포 중 오류 발생: {e}")

def run_local_wifi_test():
    """
    옵션 C: 컴퓨터가 켜져 있는 동안 같은 와이파이에서 즉시 폰으로 테스트
    """
    local_ip = get_local_ip()
    port = 8080
    test_url = f"http://{local_ip}:{port}/index.html"

    print("\n" + "=" * 65)
    print("📶 [방식 3: 지금 즉시 스마트폰으로 로컬 와이파이 테스트]")
    print("=" * 65)
    print(f"스마트폰이 컴퓨터와 같은 Wi-Fi에 연결되어 있다면 지금 바로 열 수 있습니다!")
    print(f"\n📱 스마트폰 사파리나 크롬 주소창에 아래 주소를 입력하세요:")
    print(f"   👉 {test_url}")
    print("\n(테스트를 종료하시려면 Ctrl + C 를 누르세요)")
    print("-----------------------------------------------------------------")

    try:
        from http.server import SimpleHTTPRequestHandler
        import socketserver
        
        os.chdir(CURRENT_DIR)
        handler = SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"⚡ 로컬 테스트 서버가 가동 중입니다 (포트 {port})...")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 로컬 테스트 서버가 종료되었습니다.")
    except Exception as e:
        print(f"⚠️ 서버 실행 오류: {e}")

def main():
    print_banner()
    run_pre_build()

    print("\n어떤 방식으로 스마트폰 접속을 설정하시겠습니까?")
    print(" [1] 💡 3초 만에 끝나는 초간단 웹 드래그 배포 (가장 쉽고 추천, 계정/코딩 불필요)")
    print(" [2] 🐙 GitHub Pages 영구 무료 배포 (깃허브 계정 보유 시)")
    print(" [3] 📶 지금 당장 같은 Wi-Fi로 스마트폰 접속 테스트 (임시 확인용)")
    print(" [q] 종료")
    
    choice = input("\n👉 번호를 선택하세요 (1/2/3): ").strip()
    
    if choice == '1':
        deploy_option_web_drop()
    elif choice == '2':
        deploy_option_github()
    elif choice == '3':
        run_local_wifi_test()
    else:
        print("종료합니다.")

if __name__ == "__main__":
    main()

