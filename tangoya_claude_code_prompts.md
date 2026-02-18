# tangoya (単語屋) — Claude Code 단계별 프롬프트

> **사용법:** 아래 프롬프트를 단계 순서대로 Claude Code에 붙여넣어 실행한다.
> 각 단계가 완료되고 결과물을 확인한 뒤 다음 단계로 진행한다.
> 프로젝트 루트에 `N1_words_naver.txt` ~ `N5_words_naver.txt` 파일이 있는 상태에서 시작한다.

---

## STEP 1 — 프로젝트 구조 생성 및 데이터 확인

```
아래 지시에 따라 tangoya 프로젝트의 기본 구조를 만들어줘.

【작업 내용】
1. 현재 디렉토리에 다음 폴더 구조를 생성해:
   tangoya/
   ├── data/          (원본 단어 파일을 이동할 폴더)
   ├── build/         (빌드 스크립트를 위한 폴더)
   └── dist/          (최종 배포 파일 tangoya.html이 생성될 폴더)

2. 현재 디렉토리의 N1_words_naver.txt ~ N5_words_naver.txt 파일을
   tangoya/data/ 폴더로 복사해.

3. 각 파일을 읽어 아래 항목을 터미널에 출력해:
   - 파일명
   - 총 라인 수
   - 첫 3줄 (데이터 형식 샘플)
   - 형식이 "히라가나,한자표기,레벨" 3컬럼인지 확인

【기대 결과】
- 5개 파일 모두 확인되고, 형식이 "あう,会う,N5" 패턴임이 확인된다.
- N5: 511줄, N4: 877줄, N3: 1,308줄, N2: 2,262줄, N1: 2,722줄 (합계 7,680줄)

【완료 확인】
위 구조가 정상 생성되었으면 "STEP 1 완료"를 출력해줘.
```

---

## STEP 2 — 한국어 뜻 일괄 번역 및 사전 생성

```
이 단계는 원본 단어 파일의 7,680개 단어에 한국어 뜻을 붙여
tangoya/data/korean_dict.json 을 생성하는 것이 목표다.

【배경】
원본 파일(N1~N5_words_naver.txt)에는 한국어 뜻이 없다.
Claude API를 사용해 일본어 단어에 한국어 뜻을 일괄 번역하여 별도 JSON으로 저장한다.
이 파일은 이후 STEP 3에서 JLPT 레벨 정보와 합쳐진다.

【작업: tangoya/build/add_korean.py 작성 및 실행】

스크립트 동작:
  1. tangoya/data/ 의 N5→N4→N3→N2→N1 순서로 전체 단어 목록을 수집
     각 단어에서: reading(히라가나), kanji(한자표기), level(N1~N5) 추출
     중복 kanji 제거 (kanji 기준, 먼저 등장한 레벨 우선)

  2. 기존 tangoya/data/korean_dict.json 이 있으면 로드
     → 이미 번역된 단어는 건너뛰어 재시작 시 중복 API 호출 방지

  3. 미번역 단어를 100개씩 배치로 묶어 Claude API 호출
     API 엔드포인트: https://api.anthropic.com/v1/messages
     모델: claude-haiku-4-5-20251001
     max_tokens: 2000

     요청 프롬프트 (system):
       "You are a Japanese-Korean dictionary assistant.
        Return ONLY a JSON object. No explanation, no markdown, no code blocks.
        Format: {\"kanji\": \"한국어뜻\", ...}
        Rules:
        - Provide the most common Korean meaning (1~3 words, concise)
        - For verbs add ~하다/~이다 form when natural
        - For adjectives use ~한/~인 form
        - For nouns use plain form
        - If a word has multiple meanings, pick the most common one"

     요청 메시지 (user):
       "Translate these Japanese words to Korean:\n{kanji1}\n{kanji2}\n..."
       (배치 내 한자표기를 줄바꿈으로 나열)

  4. 응답 파싱:
     - JSON 파싱 성공 시: 결과를 korean_dict에 병합
     - 파싱 실패 시: 해당 배치를 건너뛰고 경고 출력 (중단하지 않음)

  5. 배치마다 tangoya/data/korean_dict.json 에 중간 저장 (중단 시 복구 가능)

  6. 전체 완료 후 통계 출력:
     - 번역 완료: N개
     - 번역 실패/건너뜀: N개
     - 저장 경로: tangoya/data/korean_dict.json

【korean_dict.json 최종 스키마】
{
  "会う":    "만나다",
  "青い":    "파랗다",
  "学生":    "학생",
  "食べる":  "먹다",
  "愛想":    "붙임성",
  ...
}
키: 한자표기 (원본 파일의 2번째 컬럼)
값: 한국어 뜻 문자열

【주의사항】
- API 키는 환경변수 ANTHROPIC_API_KEY 에서 읽는다:
    import os
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
- API 호출 실패(네트워크 오류, rate limit 등) 시 3초 대기 후 1회 재시도
- 재시도도 실패하면 해당 배치는 건너뛰고 계속 진행
- 진행 상황을 배치마다 출력:
    [12/77] N2 배치 처리 중... (1200/7680 완료)

【완료 확인】
스크립트를 실행해서 tangoya/data/korean_dict.json 이 생성되고
7,000개 이상이 번역 완료되면 "STEP 2 완료"를 출력해줘.
(일부 실패 허용, 이후 단계에서 누락분은 "-"로 표시)
```

---

## STEP 3 — JLPT 사전 빌드 스크립트 작성

```
tangoya/build/build_dict.py 스크립트를 작성해줘.

【스크립트 역할】
N1~N5 단어 파일 5개 + korean_dict.json 을 합쳐서
tangoya.html에 내장할 최종 JSON 사전(jlpt_dict.json)을 생성한다.

【상세 요구사항】

(1) 입력 파일
  - tangoya/data/N1~N5_words_naver.txt: 히라가나,한자표기,JLPT레벨 형식
  - tangoya/data/korean_dict.json: {"한자표기": "한국어뜻"} 형식
  - korean_dict.json 이 없으면 경고만 출력하고 한국어 뜻 없이 진행

(2) 처리 규칙
  파일 처리 순서: N5 → N4 → N3 → N2 → N1

  각 줄 파싱 후 아래 두 가지 키를 모두 등록:

    한자표기 키:
      "会う" → {"r": "あう", "l": "N5", "k": "만나다"}

    히라가나 키:
      "あう" → {"r": "あう", "l": "N5", "k": "만나다"}

  필드 설명:
    r : reading (히라가나)
    l : level (N1~N5)
    k : korean (한국어 뜻, korean_dict에 없으면 "-")

  키 충돌 시: 먼저 등록된 항목 유지 (N5 우선)

(3) 출력
  - 저장 경로: tangoya/build/jlpt_dict.json
  - JSON 형식: 공백 없음 (separators=(',', ':'))
  - 인코딩: UTF-8 (ensure_ascii=False)

(4) 완료 후 통계 출력
  - 레벨별 항목 수 (N5/N4/N3/N2/N1)
  - 한국어 뜻 포함 항목 수 / 누락("-") 항목 수
  - 전체 항목 수 및 파일 크기 (KB)
  - 샘플 5개 출력:
      会う → r:あう, l:N5, k:만나다

【완료 확인】
스크립트를 실행해서 tangoya/build/jlpt_dict.json이 생성되고
한국어 뜻이 포함된 샘플이 출력되면 "STEP 3 완료"를 출력해줘.
```

---

## STEP 4 — HTML 뼈대 및 CSS 작성

```
tangoya/dist/tangoya.html 파일을 새로 만들어줘.
이번 단계에서는 JavaScript 로직 없이 HTML 구조와 CSS만 완성한다.

【HTML 구조 요구사항】

<head> 에 포함할 것:
  - charset UTF-8, viewport meta
  - title: "tangoya | 単語屋"
  - Google Fonts: Noto Serif JP (400, 700), Noto Sans KR (300, 400, 500, 700), DM Mono
  - Kuromoji.js CDN: https://cdn.jsdelivr.net/npm/kuromoji@0.1.2/build/kuromoji.js
  - 모든 CSS는 <style> 태그 안에 인라인으로 작성

<body> 구성 (아래 순서로):
  ① 헤더 영역
     - 배지: "● TANGOYA · 単語屋" (작은 뱃지 스타일)
     - 타이틀: "日本語レベル判定" (대형)
     - 서브타이틀: "일본어 텍스트를 입력하면 형태소 분석 후 JLPT 레벨을 판정합니다"

  ② 레벨 범례 (가로 나열)
     - N1 최고급 / N2 고급 / N3 중급 / N4 초중급 / N5 초급 / 外 미등재
     - 각 항목은 컬러 점 + 텍스트

  ③ 입력 카드
     - 레이블: "일본어 입력"
     - textarea (id="inputText", maxlength=1000)
       placeholder: "예) 会う　　또는　　私は学生です"
     - 분석하기 버튼 (id="analyzeBtn", onclick="analyze()")

  ④ 에러 메시지 영역 (id="errorMsg", 초기 hidden)

  ⑤ 로딩 표시 (id="loading", 초기 hidden)
     - 스피너 + "형태소 분석 중..." 텍스트

  ⑥ 결과 영역 (id="resultArea", 초기 hidden)
     - 내부 콘텐츠 컨테이너 (id="resultContent")
     - 다운로드 섹션
       버튼 3개: "⬇ JSON", "⬇ CSV", "⬇ TXT"
       각각 onclick="downloadJSON()", downloadCSV(), downloadTXT()

【CSS 요구사항】

CSS 변수:
  --bg: #0f0f13        --surface: #18181f    --surface2: #222230
  --border: #2e2e40    --text: #e8e8f0       --muted: #7070a0
  --N1: #ff4d6d        --N2: #ff8800         --N3: #ffd600
  --N4: #00e676        --N5: #40c4ff         --EX: #6060a0

필수 스타일:
  - body: 다크 배경(--bg), 중앙 정렬 flex column
  - 최대 너비 860px, 좌우 패딩 24px
  - 토큰 카드 클래스 (.lv-N1 ~ .lv-N5, .lv-EX) 미리 정의
    각 클래스: 배경색(반투명), 테두리색, 글자색 레벨별로 구분
  - 단어 1개 결과 카드(.single-word-card): 중앙 정렬, 대형 글씨
  - 반응형: 480px 이하에서 입력행 세로 배치, 버튼 full-width

【완료 확인】
브라우저에서 tangoya.html을 열었을 때 레이아웃 골격이 보이면 "STEP 4 완료"를 출력해줘.
```

---

## STEP 5 — Kuromoji 초기화 및 사전 데이터 내장

```
tangoya/dist/tangoya.html의 <script> 섹션에 아래를 추가해줘.

【작업 1: JLPT_DICT 데이터 내장】
tangoya/build/jlpt_dict.json 파일을 읽어서
HTML <script> 내부 맨 위에 다음 형식으로 삽입:

  const JLPT_DICT = {전체 JSON 내용};

JSON은 파일에서 읽어 그대로 붙여넣는다.

【작업 2: Kuromoji 초기화】
  - kuromoji.builder({ dicPath: 'https://cdn.jsdelivr.net/npm/kuromoji@0.1.2/dict' })
  - Promise 래핑, 비동기 처리
  - 성공: 전역 tokenizer 에 저장
  - 실패: initFailed = true, 버튼 비활성화, 에러 표시
  - 페이지 로드 시 자동 실행
  - 성공 시 콘솔 출력:
      console.log('tangoya 준비 완료:', Object.keys(JLPT_DICT).length, '개 단어');

【작업 3: 보조 함수】

  toKatakana(str):
    히라가나(U+3041~U+3096) → 카타카나 변환 (+0x60)

  lookupWord(surface, baseForm, reading):
    JLPT_DICT에서 항목 검색. 반환값: {r, l, k} 또는 null
    검색 순서:
      1. baseForm 직접 조회
      2. surface 조회
      3. reading 조회
      4. 각 키에 '·' '・' 포함 시 분리 후 각 부분 조회
      5. 카타카나 변환 후 재조회
    첫 번째 매칭 반환

  showError(msg) / hideError()
  showLoading(bool)

【완료 확인】
브라우저 콘솔에 "tangoya 준비 완료: NNNNN 개 단어" 가 출력되면 "STEP 5 완료"를 출력해줘.
```

---

## STEP 6 — 형태소 분석 및 결과 렌더링 구현

```
tangoya/dist/tangoya.html의 <script>에
analyze() 함수와 showResult() 함수를 구현해줘.

【analyze() 함수】

트리거: 분석 버튼 클릭, textarea Enter 키 (Shift+Enter 제외)

처리 흐름:
  1. initFailed → 에러, tokenizer 없음 → "사전 로딩 중" 에러
  2. 입력값 trim() → 빈 값이면 에러 "텍스트를 입력해주세요"
  3. hideError(), showLoading(true), 결과 영역 숨김
  4. setTimeout(..., 50) 으로 비동기 처리:
     ① tokenizer.tokenize(text) 실행
     ② 각 토큰에서 추출:
          surface  : t.surface_form
          baseForm : t.basic_form !== '*' ? t.basic_form : surface
          reading  : t.reading 카타카나를 히라가나로 변환 (U+30A1~U+30F6, -0x60)
          pos      : t.pos !== '*' ? t.pos : '不明'
          posDetail: t.pos_detail_1 !== '*' ? t.pos_detail_1 : ''
     ③ lookupWord(surface, baseForm, readingHira) 호출
     ④ 결과 조합:
          info 있음  → level = info.l, korean = info.k
          info 없음 + pos ∈ ['助詞','助動詞','記号','接続詞']
                     → level = '文法', korean = '-'
          info 없음 (기타) → level = '外', korean = '-'
     ⑤ lastResult 저장:
          { input: text, tokens: [...], analyzedAt: new Date().toISOString() }
          토큰 객체: { surface, baseForm, reading, pos, posDetail, level, korean }
     ⑥ showResult(tokens, text) 호출
     ⑦ showLoading(false)
  5. try-catch: 오류 시 에러 메시지 표시

Enter 키:
  textarea keydown → Enter && !shiftKey → e.preventDefault(), analyze()

【showResult(tokens, inputText) 함수】

tokens.length === 1 → Case A, 2 이상 → Case B

━━ Case A: 단어 1개 ━━
id="resultContent" 에 렌더링:
  ┌──────────────────────────────┐
  │  あう              ← 읽기(--muted, 16px)       │
  │  会う              ← 표층형(56px, 레벨 색상)    │
  │  [N5] [動詞] [会う] ← 메타 칩 3개               │
  │  한국어 뜻: 만나다  ← 한국어 뜻(22px, 강조)     │
  │  JLPT N5 등재 단어 ← 등재 여부                  │
  └──────────────────────────────┘
  - korean === '-' 이면 한국어 뜻 행 표시 안 함
  - 미등재이면 "JLPT 미등재" 표시

━━ Case B: 문장 ━━

① 레벨 통계 칩 행(.stats-row):
   N5→N4→N3→N2→N1→外→文法 순서, 1개 이상인 레벨만 표시
   형식: "● N5 3개"

② 헤더: "분석 결과" (좌) + "{n} 형태소" (우, --muted)

③ 토큰 카드 플로우(.tokens-flow):
   각 카드 (.token-card .lv-{레벨}):
     위→아래:
       읽기 (9px)
       표층형 (18px, bold)
       레벨 (9px, DM Mono)
       한국어 뜻 (10px) ← 기존 "품사" 자리를 한국어 뜻으로 교체
                           korean === '-' 이면 품사를 대신 표시
   마우스 오버 툴팁 (.tooltip), 5개 항목:
       표층형 / 사전형 / 읽기 / 품사(posDetail 있으면 " · posDetail") / JLPT레벨

④ 텍스트 미리보기(.text-preview):
   "{surface}[{reading}, {pos}, {level}, {korean}]" 형식
   공백으로 토큰 구분

결과 영역(id="resultArea") 표시

【escHtml 함수 필수 포함】
function escHtml(str) {
  return (str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;')
                  .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

【완료 확인】
"会う" 입력 시 한국어 뜻 "만나다"가 표시되고
"私は学生です" 입력 시 각 카드에 한국어 뜻이 표시되면 "STEP 6 완료"를 출력해줘.
```

---

## STEP 7 — 다운로드 기능 구현

```
tangoya/dist/tangoya.html의 <script>에 다운로드 함수 3개를 구현해줘.

【공통】
- lastResult 전역변수를 데이터 소스로 사용 (null이면 아무것도 안 함)
- UTF-8 with BOM:
    new Blob(['\uFEFF' + content], { type: mimeType + ';charset=utf-8;' })
- 공통 헬퍼:
    function downloadFile(content, filename, mimeType) {
      const blob = new Blob(['\uFEFF' + content], { type: mimeType+';charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = filename;
      document.body.appendChild(a); a.click();
      document.body.removeChild(a); URL.revokeObjectURL(url);
    }

【downloadJSON() — tangoya_result.json】
{
  "input": "...",
  "analyzed_at": "ISO8601",
  "tokens": [
    {
      "surface": "私",
      "reading": "わたし",
      "base_form": "私",
      "pos": "名詞",
      "level": "N5",
      "korean": "나"        ← 한국어 뜻 포함
    }, ...
  ]
}
JSON.stringify(data, null, 2) 적용

【downloadCSV() — tangoya_result.csv】
헤더: 원문,읽기,사전형,품사,JLPT레벨,한국어뜻    ← 한국어뜻 컬럼 추가
데이터 예시:
  私,わたし,私,名詞,N5,나
  は,は,は,助詞,文法,-
  学生,がくせい,学生,名詞,N5,학생
각 값 큰따옴표 래핑, 내부 " → ""

【downloadTXT() — tangoya_result.txt】
1행: 입력: {input}
2행: 분석: {surface}[{reading}, {pos}, {level}, {korean}] ...
                                              ↑ 한국어 뜻 포함
공백으로 토큰 구분

【완료 확인】
분석 완료 후 3가지 다운로드 버튼이 모두 작동하고
JSON에 "korean" 필드가, CSV에 "한국어뜻" 컬럼이,
TXT에 한국어 뜻이 포함되면 "STEP 7 완료"를 출력해줘.
```

---

## STEP 8 — 통합 테스트 및 엣지 케이스 검증

```
tangoya/dist/tangoya.html을 완성된 상태로 열고
아래 테스트를 순서대로 실행해서 결과를 확인해줘.

【테스트 1: 단어 단독 (Case A) — 한국어 뜻 포함 확인】
입력: 会う
기대: 읽기 "あう", 레벨 N5, 품사 動詞, 한국어 뜻 "만나다"

입력: 食べる
기대: 레벨 N5, 한국어 뜻 "먹다"

입력: 美しい
기대: 레벨 N2, 한국어 뜻 표시 (예: "아름답다")

【테스트 2: 문장 (Case B) — 카드별 한국어 뜻 확인】
입력: 私は学生です
기대:
  私  → N5, 한국어 "나"
  は  → 文法, 한국어 "-" (품사 표시)
  学生 → N5, 한국어 "학생"
  です → N5 또는 文法

입력: 東京は大きい都市です
기대: 각 카드에 레벨 + 한국어 뜻 표시

【테스트 3: 엣지 케이스】
입력: (공백) → 에러 "텍스트를 입력해주세요"
입력: xyz    → 레벨 外, 한국어 "-"
입력: 123    → 레벨 外, 한국어 "-"

【테스트 4: 다운로드 파일 내용 확인】
"私は学生です" 분석 후:
  JSON → "korean": "나", "학생" 등 값 확인
  CSV → 헤더에 "한국어뜻" 컬럼 존재, 각 행에 값 포함
  TXT → "[わたし, 名詞, N5, 나]" 형식으로 한국어 뜻 포함

【테스트 5: UX 동작】
  - Enter 키로 분석 실행
  - Shift+Enter 줄바꿈
  - 토큰 카드 마우스 오버 시 툴팁 5개 항목 표시
  - 툴팁에는 품사 정보가 포함되어 있어야 함

【결과 보고 형식】
  ✅ 테스트 1-1 (会う): PASS — N5, 만나다 표시
  ❌ 테스트 X-X: FAIL — 이유

실패 항목은 즉시 수정 후 재테스트.
모든 PASS 시 "STEP 8 완료"를 출력해줘.
```

---

## STEP 9 — 빌드 자동화 및 최종 배포

```
아래 작업을 순서대로 진행해줘.

【작업 1: 빌드 자동화 스크립트 — tangoya/build/build_html.py】

이 스크립트 하나를 실행하면 STEP 3~5의 과정이 자동화되어
tangoya/dist/tangoya.html 이 완성된 상태로 재생성된다.

처리 흐름:
  1. tangoya/data/ 의 N1~N5 파일 읽기
  2. tangoya/data/korean_dict.json 로드 (없으면 경고 후 빈 dict 사용)
  3. JLPT_DICT 생성 (STEP 3 로직과 동일, r+l+k 포함)
  4. tangoya/dist/tangoya_template.html 읽기
  5. 플레이스홀더 교체:
     // __JLPT_DICT_PLACEHOLDER__
     → const JLPT_DICT = {json};
  6. tangoya/dist/tangoya.html 로 저장
  7. 완료 통계 출력:
       단어 데이터: N개 항목 내장 (한국어 뜻 포함: N개)
       출력 파일: tangoya/dist/tangoya.html (NNN KB)
       빌드 완료: YYYY-MM-DD HH:MM:SS

실행:
  cd tangoya && python3 build/build_html.py

【작업 2: 템플릿과 최종본 분리】
  tangoya/dist/tangoya_template.html:
    현재 tangoya.html에서 JLPT_DICT JSON 데이터 부분을 제거하고
    // __JLPT_DICT_PLACEHOLDER__ 로 표시한 버전

  tangoya/dist/tangoya.html:
    build_html.py 실행 결과물 (데이터 내장 완성본)

【작업 3: README.md 작성 — tangoya/ 루트】

내용:
  # tangoya (単語屋)
  일본어 JLPT 레벨 판정 앱 — 한국어 뜻 포함

  ## 사용 방법
  tangoya/dist/tangoya.html 을 더블클릭해서 브라우저로 열면 바로 사용 가능.
  인터넷 연결 필요 (Kuromoji 형태소 분석 사전 자동 로딩).

  ## 기능
  - 일본어 단어/문장 입력 → 형태소별 JLPT 레벨 판정
  - 각 단어에 한국어 뜻 표시
  - 결과 다운로드 (JSON / CSV / TXT)

  ## 개발자용: 데이터 업데이트
  1. 단어 파일 수정: data/*.txt
  2. 한국어 뜻 재생성: python3 build/add_korean.py
  3. HTML 재빌드: python3 build/build_html.py

  ## 파일 구조
  (실제 생성된 구조 그대로 반영)

  ## 기술 스택
  - 형태소 분석: Kuromoji.js v0.1.2 (IPAdic 사전)
  - JLPT 데이터: N1~N5 총 13,680개 항목 + 한국어 뜻 내장
  - 배포: 단일 HTML 파일 (서버 불필요)

【최종 체크리스트】
  □ tangoya/dist/tangoya.html — 브라우저에서 정상 동작, 한국어 뜻 표시
  □ tangoya/dist/tangoya_template.html — 존재
  □ tangoya/build/build_html.py — 실행 시 tangoya.html 재생성
  □ tangoya/build/add_korean.py — 존재
  □ tangoya/data/korean_dict.json — 존재, 7,000개 이상
  □ tangoya/README.md — 존재
  □ 최종 파일 크기 출력

모두 확인되면 "STEP 9 완료 — tangoya 빌드 완료"를 출력해줘.
```

---

## 부록 A — 오류 발생 시 디버깅 프롬프트

```
아래 문제가 발생하면 이 프롬프트를 사용해줘.

【문제 1: Kuromoji 로딩 실패】
브라우저 콘솔에서 Kuromoji 관련 에러 발생.
확인:
  1. 인터넷 연결 확인
  2. CDN URL 확인:
     https://cdn.jsdelivr.net/npm/kuromoji@0.1.2/build/kuromoji.js
  3. 콘솔 에러 메시지 전문을 알려줘

【문제 2: 한국어 뜻이 모두 "-" 로 표시됨】
korean_dict.json이 제대로 생성됐는지 확인:
  python3 -c "
  import json
  d = json.load(open('tangoya/data/korean_dict.json'))
  print(len(d), '개')
  print(list(d.items())[:5])
  "
결과가 0개이거나 파일이 없으면 add_korean.py 를 다시 실행해줘.

【문제 3: add_korean.py API 오류】
ANTHROPIC_API_KEY 환경변수 설정 확인:
  export ANTHROPIC_API_KEY="your-key-here"
Rate limit 오류 시: 스크립트 내 대기 시간을 3초→10초로 늘려줘.

【문제 4: 특정 단어 레벨이 "外"로 표시됨】
해당 단어가 사전에 있는지 확인:
  python3 -c "
  import json
  d = json.load(open('tangoya/build/jlpt_dict.json'))
  print(d.get('단어'))
  print(d.get('단어의히라가나'))
  "
없으면 build_dict.py 의 키 등록 로직을 점검해줘.

【문제 5: CSV 파일 글자 깨짐】
Blob 생성 시 '\uFEFF' BOM이 포함됐는지 확인.
없으면 downloadCSV() 함수를 수정:
  new Blob(['\uFEFF' + content], ...)
```

---

## 부록 B — 기능 확장 프롬프트 (선택)

```
【확장 1: 분석 이력】
최근 분석한 입력 5개를 sessionStorage에 저장하고
입력창 아래에 클릭 가능한 태그로 표시해줘.
클릭 시 자동 입력 후 분석 실행.

【확장 2: 레벨 필터】
결과 카드 위에 필터 버튼 [전체] [N1] [N2] [N3] [N4] [N5] [外]를 추가.
선택된 레벨 카드만 표시, 나머지는 opacity 0.2.

【확장 3: 복사 버튼】
텍스트 미리보기 영역 오른쪽에 [📋 복사] 버튼 추가.
클릭 시 클립보드 복사 + 버튼 "✓ 복사됨" 1초 후 원래대로.

【확장 4: 한국어 뜻 수동 편집】
한국어 뜻이 "-" 인 카드에 [+뜻 추가] 버튼 표시.
클릭 시 인라인 입력창 열림 → 입력 후 Enter로 저장
→ sessionStorage에 임시 저장해서 해당 세션 내 재사용.
```

---

*tangoya (単語屋) — Claude Code 단계별 프롬프트 v2.0*
*PRD v2.1 기준 | 한국어 뜻 추가 반영 | 2026-02-18*
