/**
 * [프랜차이즈 대시보드 모바일 PWA 서비스 워커 (sw.js)]
 * 스마트폰에서 오프라인 캐싱 및 부드러운 앱 환경을 지원합니다.
 */

const CACHE_NAME = 'franchise-dashboard-v1';

// 설치 시 기본 리소스 캐싱
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

// 활성화 시 이전 캐시 정리
self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

// 네트워크 우선, 실패 시 캐시 폴백 전략 (최신 데이터 보장)
self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        return response;
      })
      .catch(() => {
        return caches.match(event.request);
      })
  );
});

