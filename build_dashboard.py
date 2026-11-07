#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
=============================================================================
[프랜차이즈 분석 리포트 통합 대시보드 자동 빌더 스크립트]
- 기능: Dashboard 폴더 내의 모든 프랜차이즈 분석 HTML 리포트에서 데이터를 수집하여
        비교 우위 지표(4대 성향별 스코어, 3대 과락 여부, 4사분면 매트릭스 좌표)를
        자동 계산하고, 대시보드 데이터(dashboard_data.js)를 생성합니다.
- 실행법: 터미널에서 python3 build_dashboard.py 실행
=============================================================================
"""

import os
import glob
import re
import json
import time
import unicodedata

# 1. 경로 설정 (현재 스크립트가 위치한 폴더 기준)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_JS_PATH = os.path.join(CURRENT_DIR, "dashboard_data.js")

def parse_money(s):
    """
    한글 금액 표기(예: '1억 1,415만', '1,697만 원')를 정수(만원 단위)로 변환하는 함수
    """
    if not s or "정보" in s or "미제공" in s or "없음" in s:
        return 0
    clean = str(s).replace(",", "").replace(" ", "").replace("원", "")
    eok = 0.0
    man = 0.0
    m_eok = re.search(r"(\d+(?:\.\d+)?)억", clean)
    if m_eok:
        eok = float(m_eok.group(1))
    m_man = re.search(r"(\d+(?:\.\d+)?)만", clean)
    if m_man:
        man = float(m_man.group(1))
    if not m_eok and not m_man:
        m_num = re.search(r"(\d+(?:\.\d+)?)", clean)
        if m_num:
            return float(m_num.group(1))
    return int(round(eok * 10000 + man))

def parse_number(s):
    """문자열에서 소수점/정수 첫 번째 숫자를 추출 (예: '16.3%' -> 16.3, '98개점' -> 98)"""
    if not s or "정보" in s or "없음" in s:
        return 0.0
    m = re.search(r"(\d+(?:\.\d+)?)", str(s))
    return float(m.group(1)) if m else 0.0

def parse_js_object(js_code):
    """
    자바스크립트 객체 리터럴 문자열을 파이썬 딕셔너리로 안전하게 변환하는 파서
    """
    buf = []
    i = 0
    n = len(js_code)
    in_str = False
    str_char = ""
    escaped = False

    while i < n:
        c = js_code[i]
        if in_str:
            buf.append(c)
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == str_char:
                in_str = False
            i += 1
        else:
            if c in ('"', "'"):
                in_str = True
                str_char = c
                buf.append(c)
                i += 1
            elif c == "/" and i + 1 < n and js_code[i+1] == "/":
                while i < n and js_code[i] != "\n":
                    i += 1
            else:
                buf.append(c)
                i += 1

    cleaned = "".join(buf)

    # 문자열 리터럴을 임시 마스킹 처리
    strings = []
    def save_str(match):
        strings.append(match.group(0))
        return f"__STR_{len(strings)-1}__"

    pattern = r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')'
    masked = re.sub(pattern, save_str, cleaned)

    # 객체 키를 따옴표로 감싸기: key: -> "key":
    masked = re.sub(r'([{,]\s*)([a-zA-Z0-9_$]+)\s*:', r'\1"\2":', masked)

    # 쉼표 뒤 닫는 괄호(trailing comma) 제거
    masked = re.sub(r',\s*([}\]])', r'\1', masked)

    # 마스킹된 문자열을 표준 JSON 문자열로 복원
    for idx, s in enumerate(strings):
        if s.startswith("'"):
            inner = s[1:-1]
            inner = inner.replace('\\\'', "'").replace('"', '\\"')
            json_s = '"' + inner + '"'
        else:
            json_s = s
        masked = masked.replace(f"__STR_{idx}__", json_s)

    return json.loads(masked)

def extract_report_data(html_path, index_num):
    """
    개별 리포트 HTML 파일에서 TEMPLATE_DATA를 추출하고 대시보드용 지표를 계산
    """
    # 맥OS 환경(자모 분리 NFD)에서도 웹 호환을 위해 완성형(NFC)으로 유니코드 정규화
    file_name = unicodedata.normalize("NFC", os.path.basename(html_path))
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # TEMPLATE_DATA 자바스크립트 객체 탐색
    m = re.search(r"const\s+TEMPLATE_DATA\s*=\s*(\{[\s\S]*?\n\s*\});", content)
    if not m:
        return None

    raw_data = parse_js_object(m.group(1))

    # 기본 정보
    name = raw_data.get("name", file_name.replace(".html", "")).strip()
    corp = raw_data.get("corp", "법인명 미제공")
    category = raw_data.get("category", "일반외식")
    scale_tag = raw_data.get("scaleTag", "권장 평수 정보 없음")
    subtitle = raw_data.get("subtitle", "")
    verdict = raw_data.get("verdict", "")
    tags = raw_data.get("tags", [])
    scores = raw_data.get("scores", [0]*10)

    # KPI 1~5 세부 지표
    kpi1 = raw_data.get("kpi1", {})
    kpi2 = raw_data.get("kpi2", {})
    kpi3 = raw_data.get("kpi3", {})
    kpi4 = raw_data.get("kpi4", {})
    kpi5 = raw_data.get("kpi5", {})

    # 수치형 정량 데이터 정규화
    capex_man = parse_money(kpi4.get("totalCost", "0"))
    pyeong_sales_man = parse_money(kpi3.get("pyeongSales", "0"))
    annual_sales_man = parse_money(kpi3.get("annualSales", "0"))
    store_count = int(parse_number(kpi2.get("storeCount", "0")))
    churn_rate = parse_number(kpi2.get("realChurn", "0"))
    debt_ratio = parse_number(kpi1.get("debtRatio", "0"))

    # =========================================================================
    # [비교 우위 핵심 판단 로직]
    # =========================================================================

    # 1. 3대 치명적 과락(One-Strike) 판정
    strike_capital = (scores[0] == 0) or ("자본잠식" in verdict) or ("자본잠식" in str(tags))
    strike_churn = (scores[3] == 0) or (churn_rate >= 15.0) or ("이탈률" in verdict and "과락" in verdict)
    strike_data = (scores[2] == 0 and scores[5] == 0) or ("검증 데이터 부재" in verdict)
    is_disqualified = strike_capital or strike_churn or strike_data

    strike_reasons = []
    if strike_capital:
        strike_reasons.append("본사 자본잠식 (부도 위험)")
    if strike_churn:
        strike_reasons.append(f"실질 이탈률 과다 ({churn_rate}%로 15% 초과)")
    if strike_data:
        strike_reasons.append("가맹/직영 영업데이터 전무")

    # 2. 종합 스코어 (100점 만점)
    raw_total_score = sum(scores)

    # 3. 4대 투자자 맞춤형(페르소나) 비교 우위 인덱스 계산 (각 100점 만점 환산)
    stability_score = round(
        (scores[0] * 2.5) + (scores[1] * 1.5) + (scores[2] * 2.0) + (scores[3] * 2.0) + (scores[9] * 2.0),
        1
    )

    roi_score = round(
        (scores[5] * 3.5) + (scores[6] * 3.5) + (scores[4] * 1.5) + (scores[1] * 1.5),
        1
    )

    partner_score = round(
        (scores[7] * 4.0) + (scores[8] * 3.0) + (scores[9] * 2.0) + (scores[2] * 1.0),
        1
    )

    if capex_man <= 10000:
        capex_light_score = 10
    elif capex_man <= 15000:
        capex_light_score = 7
    elif capex_man <= 20000:
        capex_light_score = 4
    else:
        capex_light_score = 2
    light_capital_score = round(
        (capex_light_score * 4.0) + (scores[5] * 3.0) + (scores[6] * 3.0),
        1
    )

    # 4. 4사분면 포지셔닝 분류
    is_low_capex = capex_man <= 14000
    is_high_pyeong = pyeong_sales_man >= 1750

    if is_low_capex and is_high_pyeong:
        quadrant = "Q1_SUPER_ALZZA"
        quadrant_label = "💡 슈퍼 알짜형 (적은 창업비 + 높은 평당매출)"
        quadrant_color = "#10b981"
    elif not is_low_capex and is_high_pyeong:
        quadrant = "Q2_HIGH_END"
        quadrant_label = "🏢 하이엔드형 (높은 투자비 + 높은 평당매출)"
        quadrant_color = "#0071e3"
    elif is_low_capex and not is_high_pyeong:
        quadrant = "Q3_SMALL_STABLE"
        quadrant_label = "☕ 생계 소형형 (적은 투자비 + 안정형 매출)"
        quadrant_color = "#f59e0b"
    else:
        quadrant = "Q4_HIGH_RISK"
        quadrant_label = "⚠️ 고위험 함정형 (높은 투자비 + 낮은 평당매출)"
        quadrant_color = "#ef4444"

    brand_id = f"brand_{index_num}_{re.sub(r'[^a-zA-Z0-9]', '', name)}"
    if len(brand_id) <= 8:
        brand_id = f"brand_{index_num}"

    return {
        "id": brand_id,
        "name": name,
        "corp": corp,
        "category": category,
        "scaleTag": scale_tag,
        "fileName": file_name,
        "subtitle": subtitle,
        "verdict": verdict,
        "tags": tags,
        # 점수 정보
        "scores": scores,
        "totalScore": raw_total_score,
        "personaScores": {
            "stability": stability_score,
            "roi": roi_score,
            "partner": partner_score,
            "lightCapital": light_capital_score
        },
        # 과락 정보
        "isDisqualified": is_disqualified,
        "strikeReasons": strike_reasons,
        # 정량 지표
        "metrics": {
            "capexMan": capex_man,
            "capexText": kpi4.get("totalCost", "미제공"),
            "pyeongSalesMan": pyeong_sales_man,
            "pyeongSalesText": kpi3.get("pyeongSales", "미제공"),
            "annualSalesMan": annual_sales_man,
            "annualSalesText": kpi3.get("annualSales", "미제공"),
            "storeCount": store_count,
            "storeCountText": kpi2.get("storeCount", "0개점"),
            "directCountText": kpi2.get("directCount", "0개"),
            "churnRate": churn_rate,
            "churnRateText": kpi2.get("realChurn", "0%"),
            "paybackEst": kpi4.get("paybackEst", "계산 불가"),
            "debtRatioText": kpi1.get("debtRatio", "미제공"),
            "opProfitText": kpi1.get("opProfit", "미제공"),
            "royaltyText": kpi5.get("royalty", "미제공"),
            "logisticsMarginText": kpi5.get("logisticsMargin", "미제공"),
            "svRatioText": kpi5.get("svRatio", "미제공")
        },
        # 사분면 좌표 및 구분
        "quadrant": {
            "type": quadrant,
            "label": quadrant_label,
            "color": quadrant_color,
            "x": capex_man,
            "y": pyeong_sales_man,
            "r": max(8, min(24, int(store_count * 0.2) + 8)) if store_count > 0 else 8
        },
        # 시뮬레이션 기본 파라미터
        "simDefaults": raw_data.get("simDefaults", {
            "annualSales": annual_sales_man if annual_sales_man > 0 else 50000,
            "area": 25,
            "cogs": 35.0,
            "rent": 300,
            "labor": 1200,
            "royalty": 3.0,
            "other": 5.0,
            "capex": capex_man if capex_man > 0 else 12000
        })
    }

def main():
    start_ts = int(time.time() * 1000)

    # Dashboard 폴더 내의 모든 html 파일 탐색 (index.html은 제외)
    html_files = sorted(glob.glob(os.path.join(CURRENT_DIR, "*.html")))
    report_files = [f for f in html_files if not os.path.basename(f).lower().startswith("index")]

    brands_data = []
    for idx, file_path in enumerate(report_files, start=1):
        try:
            brand_info = extract_report_data(file_path, idx)
            if brand_info:
                brands_data.append(brand_info)
        except Exception as e:
            print(f"  ❌ 에러 발생 ({os.path.basename(file_path)}): {e}")

    # 기본 정렬: 총점 내림차순
    brands_data.sort(key=lambda x: x["totalScore"], reverse=True)

    # JS 파일로 저장 (window.FRANCHISE_DATA 전역 객체 + buildTime 타임스탬프)
    json_text = json.dumps(brands_data, ensure_ascii=False, indent=2)
    js_content = f"""/**
 * 프랜차이즈 분석 리포트 통합 데이터셋
 * 자동 생성 타임스탬프: {start_ts}
 * 총 브랜드 수: {len(brands_data)}개
 */
window.FRANCHISE_BUILD_TIME = {start_ts};
window.FRANCHISE_DATA = {json_text};
"""

    with open(OUTPUT_JS_PATH, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"📊 [빌드 완료] 총 {len(brands_data)}개 브랜드 데이터 동기화 완료 (타임스탬프: {start_ts})")

if __name__ == "__main__":
    main()
