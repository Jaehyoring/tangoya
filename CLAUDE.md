# CLAUDE.md — tangoya (単語屋) 개발 가이드

> Claude Code가 이 프로젝트를 작업할 때 반드시 숙지해야 할 모든 규칙, 구조, 코딩 컨벤션 정보.

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 앱 이름 | tangoya (単語屋) |
| 목적 | 일본어 텍스트 입력 → 형태소별 JLPT 레벨 판정 + 한국어 뜻 표시 + 한국어 번역 |
| 배포 방식 | 단일 HTML 파일 (`dist/tangoya.html`), 로컬 HTTP 서버 필요 |
| CDN 의존성 | Kuromoji.js v0.1.2 (형태소 분석), Google Fonts (로컬 캐시), Google Translate 비공식 API |
| UI 언어 | 한국어 |
| 입력 언어 | 일본어 |
| 최종 배포 파일 크기 | ~824 KB |

---

## 2. 파일 구조 & 역할

```
tangoya/
├── CLAUDE.md                      ← 이 파일 (개발 규칙)
├── README.md                      ← 사용자용 안내
├── PRD_tangoya.md                 ← 제품 요구사항 문서 (v2.1)
├── data/
│   ├── N1_words_naver.txt         (2,723줄) ← 읽기,한자,N1 형식
│   ├── N2_words_naver.txt         (2,263줄)
│   ├── N3_words_naver.txt         (1,309줄)
│   ├── N4_words_naver.txt         (878줄)
│   ├── N5_words_naver.txt         (512줄)
│   └── korean_dict.json           (7,518개) ← {"漢字": "한국어뜻"}
├── build/
│   ├── add_korean.py              (jamdict 기반 한국어 뜻 자동 생성)
│   ├── build_dict.py              (jlpt_dict.json 생성 — 중간 산출물)
│   ├── build_html.py              (HTML 빌드 자동화)
│   └── jlpt_dict.json             (13,680개 항목 — 참고/디버그용)
└── dist/
    ├── tangoya_template.html      ← ✏️ UI 수정 대상 파일 (플레이스홀더 포함, ~154 KB)
    └── tangoya.html               ← ✅ 최종 배포 파일 (JLPT_DICT 내장, ~824 KB)
```

### ⚠️ 핵심 규칙: 어떤 파일을 수정하는가

| 작업 | 수정 파일 | 이후 작업 |
|------|----------|-----------|
| UI / JS / CSS 수정 | `dist/tangoya.html` 직접 편집 | `tangoya_template.html` 동기화 필수 |
| 데이터 변경 후 빌드 | `tangoya_template.html` 편집 | `python3 build/build_html.py` 실행 |
| 단어 데이터 추가 | `data/N*_words_naver.txt` | `add_korean.py` → `build_html.py` |

> **❌ 절대 금지**: `build_html.py`로 `tangoya.html`을 덮어쓰면 UI 변경 사항이 소실됨.
> 반드시 `tangoya_template.html`에 먼저 반영하거나, UI 수정 후 template을 동기화할 것.

**template 동기화 명령어** (tangoya.html 수정 후 실행):

```bash
cd <프로젝트 루트>
python3 - << 'EOF'
import re
with open('dist/tangoya.html','r',encoding='utf-8') as f: c=f.read()
n=re.sub(r'  const JLPT_DICT = \{.*?\};','  // __JLPT_DICT_PLACEHOLDER__',c,count=1,flags=re.DOTALL)
with open('dist/tangoya_template.html','w',encoding='utf-8') as f: f.write(n)
print("Template synced.")
EOF
```

---

## 3. HTML 파일 전체 구조

`tangoya_template.html` (~154 KB)의 구조:

| 구간 | 내용 | 비율 |
|------|------|------|
| Lines 1–15 | `<!DOCTYPE html>`, `<head>`, CDN 로드 | ~1% |
| Lines 16–1220 | `<style>` CSS 전체 | ~47% |
| Lines 1222–1355 | HTML Body (toolbar, modals, header, input, result area) | ~5% |
| Lines 1356–끝 | `<script>` JavaScript 전체 | ~47% |
| Line ~1360 | `// __JLPT_DICT_PLACEHOLDER__` → 빌드 시 JLPT_DICT 삽입 지점 | — |

### HTML 주요 요소

```html
<!-- 툴바 (fixed, top-right) -->
<div id="toolbar">
  <button id="themeBtn" onclick="toggleTheme()">🌙</button>
  <button id="addWordBtn" onclick="openAddWordModal()">+</button>
  <button id="adminBtn" onclick="openAdminModal()">🔒</button>
  <button id="criteriaUploadBtn" title="레벨 분류 기준 CSV 업로드">📋</button>
  <button id="syncBtn" onclick="openSyncModal()">☁</button>
  <!-- 관리자 모드에서만 표시 -->
  <button id="dictDownloadBtn" onclick="openDictDlModal()" style="display:none">📖</button>
  <button id="dictEditBtn" onclick="openDictEditModal()" style="display:none">✏</button>
</div>

<!-- 관리자 패스워드 모달 -->
<div id="adminModal" role="dialog" aria-modal="true">
  <input type="password" id="adminPwInput" onkeydown="Enter→confirmAdmin(), Esc→closeAdminModal()">
  <div id="adminPwError"></div>
</div>

<!-- 사전 수정 모달 (관리자 전용) -->
<div id="dictEditModal" role="dialog" aria-modal="true" aria-labelledby="dictEditTitle">
  <div class="dict-edit-box">
    <!-- 탭: 전체 / 수정된 / 커스텀 단어 -->
    <div class="dict-edit-tabs">
      <button class="dict-edit-tab active" data-tab="all">전체</button>
      <button class="dict-edit-tab" data-tab="edited">수정된</button>
      <button class="dict-edit-tab" data-tab="custom">커스텀</button>
    </div>
    <!-- 검색 + 레벨 필터 -->
    <input id="dictEditSearch" type="text" placeholder="검색…" oninput="refreshDictEditList()">
    <select id="dictEditLevelFilter" onchange="refreshDictEditList()">…</select>
    <!-- 결과 목록 -->
    <div id="dictEditList">…</div>
    <div id="dictEditInfo">…</div>
  </div>
</div>

<!-- 사전 CSV 다운로드 진행 모달 (관리자 전용) -->
<div id="dictDlModal" role="dialog" aria-modal="true" aria-labelledby="dictDlTitle">
  <div class="dict-dl-box">
    <div id="dictDlStatus">준비 중…</div>
    <div class="dict-dl-progress-wrap"><div class="dict-dl-bar" id="dictDlBar"></div></div>
    <div id="dictDlDetail"></div>
    <button onclick="closeDictDlModal()">취소</button>
  </div>
</div>

<!-- 헤더 -->
<header class="header">
  <div class="badge">TANGOYA · 単語屋</div>
  <h1 class="header-title">일본어 어휘 레벨 판정기</h1>
  <div id="adminBadge">ADMIN MODE</div>   <!-- admin-mode 클래스 시 표시 -->
</header>

<!-- 레벨 범례 -->
<nav class="legend" aria-label="JLPT 레벨 범례"> ... </nav>

<!-- 입력 카드 -->
<section class="card" aria-label="입력 영역">
  <textarea id="inputText" maxlength="1000"></textarea>
  <button id="analyzeBtn" onclick="analyze()">분석하기</button>
  <button id="resetBtn" onclick="resetAll()">↺ 초기화</button>
</section>

<!-- 에러 / 로딩 -->
<div id="errorMsg" role="alert" aria-live="polite"></div>
<div id="loading" aria-live="polite">...</div>

<!-- 결과 영역 -->
<section id="resultArea" aria-label="분석 결과">
  <div id="resultContent"></div>   <!-- showResult()가 innerHTML 주입 -->
  <!-- 한국어 번역 (analyze() 후 자동 표시) -->
  <div id="translationSection" aria-live="polite" aria-label="한국어 번역">
    <div class="translation-header">
      <span class="translation-label">한국어 번역</span>
      <span class="translation-badge">via Google 번역</span>
    </div>
    <div id="translationText" class="translation-text"></div>
  </div>
  <div class="download-section">
    <button onclick="downloadJSON()">⬇ JSON</button>
    <button onclick="downloadCSV()">⬇ CSV</button>
    <button onclick="downloadTXT()">⬇ TXT</button>
    <button onclick="resetKrEdits()">↺ 수정 초기화</button>
  </div>
</section>

<!-- 언어 감지 경고 모달 -->
<div id="langModal" role="dialog" aria-modal="true" aria-labelledby="langModalTitle">
  <div class="lang-modal-backdrop" onclick="closeLangModal()"></div>
  <button class="lang-modal-btn" onclick="closeLangModal()">확인</button>
</div>
```

---

## 4. 데이터 형식

### 4-1. 단어 파일 (N1~N5_words_naver.txt)

```
읽기(히라가나),한자표기,레벨
あいそう,愛想,N1
あいじょう,愛情,N2
あう,会う,N5
```
- 3컬럼 미만 줄은 빌드 시 자동 스킵
- 레벨은 파일명에서 확정 (3번째 컬럼은 참고용)

### 4-2. korean_dict.json

```json
{ "会う": "만나다", "青い": "파란" }
```
- 키: 한자표기 또는 히라가나
- 값: 한국어 뜻 문자열 (7,518개)

### 4-3. JLPT_DICT (빌드 결과 — JS에 인라인 삽입)

```json
{
  "会う":  {"r": "あう",  "l": "N5", "k": "만나다"},
  "あう":  {"r": "あう",  "l": "N5", "k": "만나다"}
}
```
- 키: 한자형 + 히라가나형 **이중 등록** (총 13,680개 항목, 고유 단어 6,823개)
- `r`: reading(읽기), `l`: level(레벨), `k`: korean(한국어 뜻)
- **N5 우선 원칙**: 같은 단어가 복수 레벨에 존재하면 낮은 급수(N5 > N4 > … > N1)로 등록
- 빌드 시 N5 → N4 → N3 → N2 → N1 순 처리, "먼저 등록된 항목 유지" 정책 적용

### 4-4. 사전 CSV 내보내기 중복 제거 규칙

JLPT_DICT에는 한자형·히라가나형 이중 등록이 있으므로 CSV 다운로드 시 중복 제거가 필요하다.
- **스킵 조건**: `key === entry.r` (표층형이 읽기와 동일 = 순수 히라가나 키) → 한자형 키만 남김
- 결과: 13,680개 항목 → **6,823개** 고유 단어

---

## 5. JLPT_DICT 플레이스홀더 시스템

```
tangoya_template.html 안의 한 줄(~line 1360):
  // __JLPT_DICT_PLACEHOLDER__

→ build_html.py 실행 시 아래로 교체:
  const JLPT_DICT = { ... 13,680개 항목 ... };
```

- 교체는 `str.replace(PLACEHOLDER, replacement, 1)` 1회만 수행
- 결과물 `tangoya.html` 크기: ~824 KB

---

## 6. JavaScript 아키텍처

### 6-1. 전역 상태 변수

```javascript
let tokenizer      = null;     // Kuromoji 인스턴스 (최초 1회 초기화)
let initFailed     = false;    // Kuromoji 초기화 실패 여부
let lastResult     = null;     // 최신 분석 결과 { input, rawTokens, tokens, analyzedAt }
let isAdminMode    = false;    // 관리자 모드 활성화 여부
let _dictDlCancelled = false;  // 사전 CSV 다운로드 취소 플래그
let _dictEditTab   = 'all';    // 사전 수정 모달 현재 탭 ('all'|'edited'|'custom')
let _dictEditTimer = null;     // 사전 수정 목록 debounce 타이머 ID
```

### 6-2. 핵심 상수

```javascript
const LEVEL_RANK = { N5:1, N4:2, N3:3, N2:4, N1:5, '外':6, '文法':7 };

const LEVEL_COLOR = {           // updateLevelColors()에서 테마별로 동적 갱신
  N1:'#ff4d6d', N2:'#ff8800', N3:'#ffd600',
  N4:'#00e676', N5:'#40c4ff',
  '外':'#6060a0', '文法':'#444466'
};

const GRAMMAR_POS = ['助詞','助動詞','記号','接続詞'];  // 항상 '文法'으로 판정

const ADMIN_PW        = '4649';
const THEME_KEY       = 'tangoya_theme';
const KR_EDITS_KEY    = 'tangoya_kr_edits';
const MERGE_RULES_KEY = 'tangoya_merge_rules';
const ADMIN_EDITS_KEY = 'tangoya_admin_edits';
```

### 6-3. localStorage 키

| 상수명 | 키 문자열 | 저장 형식 |
|--------|-----------|-----------|
| `THEME_KEY` | `'tangoya_theme'` | `'dark'` 또는 `'light'` |
| `KR_EDITS_KEY` | `'tangoya_kr_edits'` | `{ "baseForm": "한국어뜻" }` |
| `MERGE_RULES_KEY` | `'tangoya_merge_rules'` | `{ "inputText": [[0,1],[3,4]] }` |
| `ADMIN_EDITS_KEY` | `'tangoya_admin_edits'` | `{ "origIdx@@inputText": {reading,level,pos,surface,baseForm} }` |

- 직접 `localStorage.setItem/getItem` 호출 금지 → 반드시 전용 load/save 함수 사용
- 각 키마다 load/save 쌍 함수 존재: `loadKrEdits()`/`saveKrEdits()`, `loadMergeRules()`/`saveMergeRules()`, `loadAdminEdits()`/`saveAdminEdit()`

### 6-4. 토큰 객체 구조

```javascript
{
  surface:   "会う",      // 표층형 (원문 그대로)
  baseForm:  "会う",      // 사전형 (기본형)
  reading:   "あう",      // 읽기 (히라가나로 변환)
  pos:       "動詞",      // 품사
  posDetail: "自立",      // 품사 세부 (optional)
  level:     "N5",        // JLPT 레벨
  korean:    "만나다",    // 한국어 뜻 ('-'이면 미등재)
  _origIdx:  0,           // 원본 인덱스 (병합/편집 추적용)
  _isMerged: false        // 병합된 토큰 여부
}
```

### 6-5. 데이터 흐름

```
analyze() 호출
  ↓
① 유효성 검사: containsJapanese() + hasForeignNonJapanese()
    비일본어 감지 → langModal 표시 후 종료
  ↓
② Kuromoji tokenize(text)
  ↓
③ 각 토큰 처리:
    - pos ∈ GRAMMAR_POS → level='文法', korean='-'
    - else → lookupWord(surface, baseForm, readingHira)
    - 미등재 → level='外', korean='-'
  ↓
④ applyMergeGroups(rawTokens, groups) — localStorage 병합 규칙 적용
  ↓
⑤ applyAdminEdits(tokens, inputText) — localStorage 관리자 편집 적용
  ↓
⑥ lastResult = { input, rawTokens, tokens, analyzedAt } 저장
  ↓
⑦ showResult(tokens, inputText) — Case A / Case B 렌더링
  ↓
⑧ translateText(text) — Google Translate API로 전문 한국어 번역
    (비동기; 결과는 #translationSection에 순차 표시)
```

### 6-6. lookupWord 동작 원칙

```javascript
function lookupWord(surface, baseForm, reading) {
  const candidates = [baseForm, surface, reading].filter(Boolean);
  let best = null;

  function keepLowest(entry) {
    if (!entry) return;
    if (!best || LEVEL_RANK[entry.l] < LEVEL_RANK[best.l]) best = entry;
  }

  for (const key of candidates) {
    keepLowest(JLPT_DICT[key]);
    // 점(·, ・) 포함 단어는 분리해서 각각 검색
    if (key.includes('·') || key.includes('・')) {
      for (const part of key.split(/[·・]/)) keepLowest(JLPT_DICT[part.trim()]);
    }
    // 히라가나 ↔ 가타카나 변환 후 재시도
    const kata = toKatakana(key);
    if (kata !== key) keepLowest(JLPT_DICT[kata]);
  }
  return best;
}
```

- **반드시** `keepLowest()` 패턴 유지 — 첫 번째 히트에서 즉시 return 금지
- GRAMMAR_POS 해당 시 JLPT_DICT 조회 없이 `level = '文法'`

### 6-7. Google Translate 비공식 API

```javascript
// 엔드포인트 (API 키 불필요)
const url = 'https://translate.googleapis.com/translate_a/single'
  + '?client=gtx&sl=ja&tl=ko&dt=t&q=' + encodeURIComponent(text);

// 응답 파싱
const data = await (await fetch(url)).json();
const translated = data[0].map(chunk => chunk[0]).join('');
```

- **배치 번역**: 30개 단어를 `\n`으로 연결하여 1회 요청; 응답 `\n` 분리로 복원
- **오류 처리**: fetch 실패 시 `showTranslation('번역 불러오기 실패…', 'error')` 표시
- **취소 플래그**: `_dictDlCancelled = true` 시 루프 중단

---

## 7. 함수 목록

### 분석 엔진

| 함수 | 역할 |
|------|------|
| `analyze()` | 메인 분석 진입점. 유효성 검사 → Kuromoji → 후처리 → 렌더링 → 번역 |
| `initKuromoji()` | Kuromoji 초기화 (Promise 반환, 최초 1회, IIFE로 자동 실행) |
| `lookupWord(surface, baseForm, reading)` | JLPT_DICT 조회, keepLowest 패턴으로 최저 레벨 반환 |
| `toKatakana(str)` | 히라가나 → 가타카나 (코드포인트 +0x60) |
| `toHiragana(str)` | 가타카나 → 히라가나 (코드포인트 -0x60) |
| `containsJapanese(str)` | 일본어 문자(히라가나/가타카나/한자) 포함 여부 |
| `hasForeignNonJapanese(str)` | 허용 범위(ASCII + 일본어 범위) 외 문자 감지 |

### 렌더링

| 함수 | 역할 |
|------|------|
| `showResult(tokens, inputText)` | tokens.length === 1 → Case A, 2+ → Case B |
| `escHtml(str)` | &, <, >, " → HTML 엔티티 변환 (XSS 방지) |
| `showLoading(bool)` | #loading 요소 visible 토글 |
| `showError(msg)` / `hideError()` | #errorMsg 표시/숨김 |
| `showLangModal()` / `closeLangModal()` | 언어 경고 모달 열기/닫기 |

### 번역

| 함수 | 역할 |
|------|------|
| `showTranslation(text, state)` | `#translationSection` 표시/갱신. state: `'loading'`\|`'done'`\|`'error'`\|`'hide'` |
| `translateText(text)` | Google Translate 비공식 API로 일본어 전문을 한국어로 번역 (async) |

### 한국어 뜻 편집

| 함수 | 역할 |
|------|------|
| `loadKrEdits()` / `saveKrEdits(edits)` | localStorage 입출력 |
| `updateKrEdit(baseForm, newKorean)` | JLPT_DICT + localStorage 동시 업데이트 |
| `isEdited(baseForm)` | 편집 여부 확인 |
| `applyStoredEdits()` | 페이지 로드 시 저장된 뜻을 JLPT_DICT에 반영 |
| `startKrEdit(el)` | span 클릭 → input으로 교체하여 인라인 편집 시작 |
| `startKrEditFromBtn(btn)` | +뜻 버튼 → input 생성하여 인라인 편집 시작 |
| `commitKrEdit(input)` | 편집 저장: updateKrEdit + lastResult 갱신 + span 복원 |
| `cancelKrEdit(input)` | 편집 취소: 원본 span 복원 |
| `resetKrEdits()` | 전체 초기화 (confirm → removeItem → reload) |

### 토큰 병합

| 함수 | 역할 |
|------|------|
| `loadMergeRules()` / `saveMergeRules(rules)` | localStorage 입출력 |
| `getMergeGroups(inputText)` | 특정 입력에 대한 병합 그룹 반환 |
| `addMerge(inputText, idxA, idxB)` | 병합 그룹 추가 (기존 그룹과 합치기 처리) |
| `removeMerge(inputText, idx)` | idx 포함 그룹 제거 |
| `applyMergeGroups(rawTokens, groups)` | 병합 규칙 적용 → 새 토큰 배열 반환 |
| `doMerge(origIdx)` | 버튼 핸들러: origIdx와 origIdx+1 병합 후 재렌더 |
| `doUnmerge(origIdx)` | 버튼 핸들러: origIdx 그룹 해제 후 재렌더 |
| `resetMergeRules()` | 전체 초기화 (confirm → removeItem → reload) |

### 관리자 모드

| 함수 | 역할 |
|------|------|
| `openAdminModal()` | 이미 admin이면 exitAdminMode(), 아니면 패스워드 모달 표시 |
| `closeAdminModal()` | 모달 숨김, 비밀번호 및 에러 초기화 |
| `confirmAdmin()` | '4649' 확인 → enterAdminMode() / 오류 시 shake 애니메이션 |
| `enterAdminMode()` | isAdminMode=true, body.admin-mode, 🔓, krEdits 재적용, 재렌더 |
| `exitAdminMode()` | isAdminMode=false, class 제거, 🔒, krEdits 재적용, 재렌더 |
| `loadAdminEdits()` / `saveAdminEdit(inputText, origIdx, field, value)` | localStorage 입출력 |
| `getAdminEdit(inputText, origIdx)` | 특정 토큰의 편집 내역 반환 |
| `applyAdminEdits(tokens, inputText)` | reading/level/pos/surface/baseForm 복원 |
| `adminSaveField(el)` | 이벤트 위임 핸들러: 필드 저장 + lastResult 갱신 + 재렌더 |
| `resetAdminEdits()` | 전체 초기화 (confirm → removeItem → reload) |

### 사전 수정 모달 (관리자 전용)

| 함수 | 역할 |
|------|------|
| `openDictEditModal()` | 모달 표시, 탭·검색 초기화, 목록 렌더 (관리자 전용) |
| `closeDictEditModal()` | 모달 숨김 |
| `_updateDictTabUI()` | 탭 버튼 active 클래스 갱신 |
| `refreshDictEditList()` | 80ms debounce 후 `_renderDictList()` 호출 |
| `_renderDictList()` | 탭·검색어·레벨 필터에 따라 목록 HTML 생성 (최대 150개 표시) |
| `startDictKrEdit(el)` | 목록 행 한국어 뜻 클릭 → input으로 교체하여 인라인 편집 시작 |
| `commitDictKrEdit(input)` | 편집 저장: updateKrEdit + lastResult 갱신 + span 복원 |
| `cancelDictKrEdit(input)` | 편집 취소: 원본 span 복원 |

### 사전 CSV 다운로드 (관리자 전용)

| 함수 | 역할 |
|------|------|
| `openDictDlModal()` | 진행 모달 표시, `runDictDownload()` 비동기 시작 (관리자 전용) |
| `closeDictDlModal()` | 취소 플래그 설정 + 모달 숨김 |
| `_dictDlSetProgress(msg, pct)` | 진행 상태 메시지 + 프로그레스 바 너비 갱신 |
| `_dictBuildRows()` | JLPT_DICT 순회 → 중복 제거(6,823개) → krEdits·커스텀 단어 반영 → 레벨순 정렬 |
| `_dictTranslateBatch(batch)` | 단어 최대 30개 `\n` 연결 → Google Translate 1회 요청 → 각 단어에 뜻 설정 |
| `runDictDownload()` | 전체 오케스트레이터: 수집 → 번역 루프 → CSV 생성 → `downloadFile()` |

### 테마 & 기타

| 함수 | 역할 |
|------|------|
| `applyTheme(theme)` | 'light'/'dark' 적용, body 클래스 토글, 버튼 이모지 갱신, localStorage 저장 |
| `toggleTheme()` | 현재 테마 감지 후 반전 |
| `updateLevelColors()` | LEVEL_COLOR 객체를 테마에 맞게 갱신 (다크: 밝은 색, 라이트: 어두운 색) |
| `resetAll()` | 입력 + 결과 + 번역 + 에러 초기화, lastResult=null |
| `downloadFile(content, filename, mimeType)` | UTF-8 BOM Blob 생성 + 앵커 다운로드 트리거 |
| `downloadJSON()` / `downloadCSV()` / `downloadTXT()` | 결과 내보내기 (snake_case JSON / 탭구분 CSV / 텍스트) |

---

## 8. showResult — Case A / Case B

### Case A (토큰 1개 = 단어 단독 입력)

```
[읽기]         ← 관리자: admin-input.reading-input (font-size:18px)
[한자표기]     ← 관리자: admin-input.surface-input.lg
[레벨 배지/select] [품사 배지/select] [사전형 배지/input.lg]
[한국어 뜻 div.word-kr  or  button.btn-add-word-kr]
[JLPT 등재 여부 텍스트]
```

### Case B (토큰 2개 이상 = 문장)

```
[레벨별 통계 뱃지들]
[헤더: "분석 결과" + N형태소]
[토큰 카드 스트림 .token-stream]
  각 카드 .token-card.lv-{LEVEL}:
    [병합버튼 .btn-merge or .btn-unmerge]
    [읽기: span.token-reading or admin-input.reading-input]
    [표층형: span.token-jp or admin-input (surface)]
    [레벨: span.token-lv or admin-select]
    [품사: span.token-pos or admin-select]
    [사전형: (숨김) or admin-input (baseForm)]
    [한국어뜻: span.token-kr or button.btn-add-kr]
[TEXT PREVIEW 섹션]
```

> **번역 섹션**: `showResult()` 완료 후 `translateText(text)`가 비동기 호출되어
> `#translationSection`에 번역 결과가 순차적으로 표시됨 (로딩 → 완료/오류).

### 관리자 모드 편집 가능 필드

| 필드 | data-field | 타입 | CSS 클래스 |
|------|-----------|------|-----------|
| 읽기 | `reading` | input | `admin-input reading-input` |
| 한자표기 | `surface` | input | `admin-input surface-input lg` (Case A) / `admin-input` (Case B) |
| 레벨 | `level` | select | `admin-select` (`admin-select lg` in Case A) |
| 품사 | `pos` | select | `admin-select` (`admin-select lg` in Case A) |
| 사전형 | `baseForm` | input | `admin-input lg` (Case A) / `admin-input` (Case B) |

---

## 9. 이벤트 위임 패턴

**⚠️ 중요**: innerHTML 주입으로 생성된 요소에는 `onclick` 속성 방식 사용 금지.
동적 요소의 이벤트는 반드시 `document.addEventListener`로 위임 처리.

DOMContentLoaded 내에서 등록되는 위임 핸들러:

```javascript
// ① select 변경 → adminSaveField
document.addEventListener('change', e => {
  const el = e.target;
  if (el.classList.contains('admin-select') && el.dataset.field) adminSaveField(el);
});

// ② input Enter/Escape
document.addEventListener('keydown', e => {
  const el = e.target;
  if (el.classList.contains('admin-input') && el.dataset.field) {
    if (e.key === 'Enter') {
      adminSaveField(el);
      // 초록 테두리 700ms 피드백
      el.classList.add('saved');
      setTimeout(() => el.classList.remove('saved'), 700);
    }
    if (e.key === 'Escape') el.blur();
  }
});

// ③ input blur → adminSaveField (capture phase)
document.addEventListener('blur', e => {
  const el = e.target;
  if (el.classList.contains('admin-input') && el.dataset.field) adminSaveField(el);
}, true);

// ④ 클릭: 한국어 편집 (token-kr, word-kr, btn-add-kr, btn-add-word-kr)
document.addEventListener('click', e => {
  const el = e.target;
  if (el.classList.contains('token-kr') || el.classList.contains('word-kr')) {
    e.stopPropagation(); startKrEdit(el);
  }
  if (el.classList.contains('btn-add-kr') || el.classList.contains('btn-add-word-kr')) {
    e.stopPropagation(); startKrEditFromBtn(el);
  }
  // 사전 수정 모달: 한국어 뜻 인라인 편집
  if (el.classList.contains('dict-edit-kr')) {
    startDictKrEdit(el);
  }
  // 사전 수정 모달: 수정 삭제 버튼
  if (el.classList.contains('dict-edit-del-btn')) {
    const surface = el.dataset.deSurface;
    if (surface) { updateKrEdit(surface, ''); refreshDictEditList(); }
  }
  // 사전 수정 모달: 탭 전환
  if (el.classList.contains('dict-edit-tab')) {
    _dictEditTab = el.dataset.tab || 'all';
    _updateDictTabUI();
    refreshDictEditList();
  }
});

// ⑤ textarea Enter → analyze()
document.getElementById('inputText').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); analyze(); }
});
```

**예외 (인라인 onclick 허용)**:
- `doMerge`, `doUnmerge` — 카드 자체 클릭 이벤트와 충돌 방지를 위해 `onclick="event.stopPropagation();doMerge(...)"` 인라인 사용
- 정적 HTML 버튼들 (`analyzeBtn`, `resetBtn`, `themeBtn`, `adminBtn` 등)

---

## 10. CSS 아키텍처

### 10-1. CSS 변수 (다크모드 기본)

```css
:root {
  --bg:       #0f0f13;
  --surface:  #18181f;
  --surface2: #222230;
  --border:   #2e2e40;
  --text:     #e8e8f0;
  --muted:    #7070a0;

  /* JLPT 레벨 색상 */
  --N1: #ff4d6d;  --N2: #ff8800;  --N3: #ffd600;
  --N4: #00e676;  --N5: #40c4ff;  --EX: #6060a0;

  /* 둥근 모서리 토큰 */
  --radius-sm: 6px;  --radius-md: 12px;  --radius-lg: 18px;
}

body.light-mode {
  --bg:       #f5f5fa;
  --surface:  #ffffff;
  --surface2: #f0f0f8;
  --border:   #d8d8e8;
  --text:     #1a1a2e;
  --muted:    #6060a0;
}
```

### 10-2. 레벨 색상 클래스

```css
.lv-N1 { background: rgba(255,77,109,0.12);  border-color: rgba(255,77,109,0.35);  color: #ff4d6d; }
.lv-N2 { background: rgba(255,136,0,0.12);   border-color: rgba(255,136,0,0.35);   color: #ff8800; }
.lv-N3 { background: rgba(255,214,0,0.12);   border-color: rgba(255,214,0,0.35);   color: #ffd600; }
.lv-N4 { background: rgba(0,230,118,0.12);   border-color: rgba(0,230,118,0.35);   color: #00e676; }
.lv-N5 { background: rgba(64,196,255,0.12);  border-color: rgba(64,196,255,0.35);  color: #40c4ff; }
.lv-EX  { background: rgba(96,96,160,0.10);  border-color: rgba(96,96,160,0.30);   color: #6060a0; }
```

### 10-3. 관리자 편집 필드 CSS

```css
.admin-input,
.admin-select {
  background: rgba(255,180,0,0.07);
  border: 1.5px solid rgba(255,180,0,0.55);   /* 노란 테두리 */
  border-radius: 5px;
  color: var(--text);
  font-family: 'DM Mono', monospace;
  font-size: 10px;
  padding: 2px 5px;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
}
.admin-input:focus, .admin-select:focus {
  border-color: #ffb400;
  box-shadow: 0 0 0 2.5px rgba(255,180,0,0.25);
  background: rgba(255,180,0,0.12);
}
.admin-input.lg      { font-size: 16px; max-width: 160px; text-align: center; padding: 4px 8px; }
.admin-select.lg     { font-size: 12px; max-width: 100px; padding: 4px 6px; }
.admin-input.surface-input { font-family: 'Noto Serif JP', serif; font-weight: 700; }
.admin-input.reading-input { font-family: 'Noto Serif JP', serif; font-size: 11px; }
.admin-input.saved   { border-color: #00e676 !important;   /* 저장 완료 초록 */
                       box-shadow: 0 0 0 2px rgba(0,230,118,0.22) !important; }
```

### 10-4. 번역 섹션 CSS

```css
#translationSection {
  display: none;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 16px 20px;
}
#translationSection.visible { display: block; }
.translation-label { font-size: 10px; font-family: 'DM Mono', monospace;
                     color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase; }
.translation-badge { font-size: 10px; font-family: 'DM Mono', monospace;
                     color: var(--muted); opacity: 0.55; margin-left: auto; }
.translation-text  { font-family: 'Noto Sans KR', sans-serif; font-size: 15px;
                     font-weight: 400; color: var(--text); line-height: 1.75; word-break: keep-all; }
.translation-text.loading { color: var(--muted); font-size: 13px;
                             animation: pulse 1.4s ease-in-out infinite; }
.translation-text.error   { color: var(--muted); font-size: 12px; }
```

### 10-5. 사전 CSV 다운로드 진행 모달 CSS

```css
#dictDlModal { display: none; position: fixed; inset: 0; z-index: 9999;
               align-items: center; justify-content: center;
               background: rgba(0,0,0,0.55); backdrop-filter: blur(2px); }
#dictDlModal.visible { display: flex; }
.dict-dl-box { background: var(--surface); border: 1px solid var(--border);
               border-radius: var(--radius-lg); padding: 28px 32px;
               width: 420px; max-width: 92vw; display: flex; flex-direction: column;
               gap: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.45);
               animation: slideUp 0.22s ease; }
.dict-dl-bar { height: 100%;
               background: linear-gradient(90deg, #40c4ff 0%, #00e676 100%);
               border-radius: 99px; width: 0%; transition: width 0.3s ease; }
```

### 10-6. 사전 수정 모달 CSS (주요)

```css
#dictEditModal { display: none; position: fixed; inset: 0; z-index: 9000;
                 align-items: center; justify-content: center;
                 background: rgba(0,0,0,0.55); backdrop-filter: blur(2px); }
#dictEditModal.visible { display: flex; }
.dict-edit-box   { background: var(--surface); border-radius: var(--radius-lg);
                   width: 600px; max-width: 95vw; max-height: 80vh;
                   display: flex; flex-direction: column; }
.dict-edit-tab   { /* monospace, 11px; .active 시 밑줄 강조 */ }
.dict-edit-row   { display: grid; grid-template-columns: 1fr 1fr auto auto auto;
                   align-items: center; gap: 8px; padding: 6px 0;
                   border-bottom: 1px solid var(--border); }
.dict-edit-kr.edited { color: #ffd600; }   /* 수정된 뜻: 노란색 */
.dict-edit-kr.empty  { color: var(--muted); font-style: italic; }  /* (없음) */
.dict-edit-kr-input  { /* admin-input 스타일 준용, font-size 11px */ }
```

### 10-7. 주요 레이아웃 클래스

```css
.container         /* max-width:860px, flex column, gap:32px */
.header            /* centered, gap:16px */
.card              /* surface 배경, border, padding:28px 32px */
.badge             /* 인라인 플렉스, monospace, 11px uppercase */
.header-title      /* Noto Serif JP, clamp(32px~52px), 700 */
.single-word-card  /* 단어 카드: 가운데 정렬, flex column */
.word-jp           /* 대형 일본어: clamp(36px~64px), serif, 700 */
.word-reading      /* 읽기: monospace, 18px, muted */
.word-kr           /* 한국어 뜻: 22px, 500 weight */
.token-stream      /* flex wrap, gap:10px */
.token-card        /* inline flex column, min-width:48px, bordered */
.token-jp          /* serif, 17px, bold */
.token-reading     /* monospace, 9px, 70% opacity */
.token-lv          /* monospace, 9px, letter-spacing */
.token-pos         /* 9px, 65% opacity */
.token-kr          /* 10px, 600 weight; .edited 시 '✎' 표시 */
.btn-merge         /* 절대위치, 18px 원형, 호버 시 파란색 표시 */
.btn-unmerge       /* 절대위치, 18px 원형, 호버 시 빨간색(#ff6b6b) */
.token-card.merged /* 점선 테두리, 0.5 opacity */
```

### 10-8. 애니메이션

```css
@keyframes pulse    { 0%/100%: opacity:1; 50%: opacity:0.35 }  /* 2.4s — 배지 점, 번역 로딩 */
@keyframes spin     { to: rotate(360deg) }                       /* 0.8s — 로딩 스피너 */
@keyframes slideUp  { from: translateY(20px) scale(0.96) }       /* 0.22s — 모달 진입 */
@keyframes fadeIn   { from: opacity:0 }                          /* 모달 배경 */
@keyframes shake    { 0/100%:0; 25%:-6px; 75%:+6px }            /* 패스워드 오류 */
```

### 10-9. 반응형

- **모바일 브레이크포인트**: `@media (max-width: 480px)`
  - body padding 감소, 카드 padding 축소
  - 입력행 → `flex-direction: column`
  - 버튼 스택, 전폭 적용
  - 다운로드 버튼 `flex-direction: column`

---

## 11. 관리자 모드 동작 규칙

1. 🔒 클릭 → `openAdminModal()` → 이미 관리자면 `exitAdminMode()`, 아니면 패스워드 모달 표시
2. `'4649'` 입력 후 확인 → `enterAdminMode()`:
   - `isAdminMode = true`
   - `document.body.classList.add('admin-mode')`
   - adminBtn: `'🔓'` + `admin-active` 클래스
   - `dictDownloadBtn`, `dictEditBtn` 표시
   - **krEdits 재적용**: `lastResult.tokens`에 `loadKrEdits()`를 다시 적용한 뒤 재렌더
     → ⚠️ 이 단계 없이 바로 `showResult()`를 호출하면 저장된 한국어 뜻이 초기화됨
3. 🔓 클릭 → `exitAdminMode()`:
   - `isAdminMode = false`
   - `document.body.classList.remove('admin-mode')`
   - adminBtn: `'🔒'`, `dictDownloadBtn`/`dictEditBtn` 숨김
   - **krEdits 재적용** 후 `showResult()` 재렌더 (동일 원칙)
4. 오류 패스워드: 입력 필드 `shake` 애니메이션, 에러 메시지 1.2초 표시 후 자동 초기화
5. **관리자 모드에서만 활성화**:
   - 토큰 필드 편집 (reading / surface / baseForm / level / pos)
   - 한국어 뜻 인라인 편집 (`.token-kr`, `.word-kr` 클릭)
   - `+ 뜻 추가` 버튼 (`.btn-add-kr`, `.btn-add-word-kr`)
   - 병합(+) / 병합 취소(✕) 버튼
   - ✏ 사전 수정 모달 (`openDictEditModal()`)
   - 📖 사전 CSV 다운로드 (`openDictDlModal()`)

---

## 12. 인라인 한국어 편집 라이프사이클

```
span.token-kr 클릭 (admin mode)
  ↓ startKrEdit(el)
span을 input으로 교체, focus + selectAll
Enter 또는 blur (+120ms delay)
  ↓ commitKrEdit(input)
updateKrEdit(baseForm, newKorean)  →  JLPT_DICT + localStorage 업데이트
lastResult.tokens 인메모리 업데이트
span 복원 (edited 클래스 + '✎' 마커)
```

- `cancelKrEdit(input)`: Escape 시 원본 span 복원 (저장 없음)
- `startKrEditFromBtn(btn)`: `+ 뜻 추가` 버튼에서 시작하는 경우 (dataset.fromBtn='true')
- `commitKrEdit`/`cancelKrEdit`에서 `onclick` 직접 할당 금지 (이벤트 위임으로 처리)

### 사전 수정 모달 내 편집

```
dict-edit-kr span 클릭
  ↓ startDictKrEdit(el)
span → dict-edit-kr-input으로 교체
Enter/blur → commitDictKrEdit(input)
  updateKrEdit(surface, newKorean)  →  JLPT_DICT + localStorage
  lastResult.tokens 인메모리 업데이트
  span 복원 (edited 클래스)
Escape → cancelDictKrEdit(input)
```

---

## 13. 토큰 병합 동작 규칙

- **병합 키**: `inputText` 문자열 단위로 저장 (입력이 달라지면 별개의 규칙)
- **`_origIdx`**: rawTokens 기준 원본 인덱스 (병합 후에도 불변)
- **`_mergedIndices`**: 병합 그룹 내 모든 origIdx 배열
- **병합 후 레벨**: 병합된 surface/reading으로 `lookupWord()` 재시도
- **그룹 합치기**: A-B가 병합되고 B-C가 병합되면 A-B-C 하나의 그룹으로 통합

---

## 14. 빌드 절차

### 단순 UI 수정 후 배포

```bash
# 1. tangoya.html 직접 편집
# 2. template 동기화
cd <프로젝트 루트>
python3 - << 'EOF'
import re
with open('dist/tangoya.html','r',encoding='utf-8') as f: c=f.read()
n=re.sub(r'  const JLPT_DICT = \{.*?\};','  // __JLPT_DICT_PLACEHOLDER__',c,count=1,flags=re.DOTALL)
with open('dist/tangoya_template.html','w',encoding='utf-8') as f: f.write(n)
print("Template synced.")
EOF
```

### 데이터 변경 후 전체 빌드

```bash
cd <프로젝트 루트>

# (선택) 한국어 뜻 재생성 (jamdict 필요)
python3 build/add_korean.py

# HTML 재빌드 (template → tangoya.html)
python3 build/build_html.py
```

**build_html.py 처리 순서**: N5 → N4 → N3 → N2 → N1 (N5 우선 원칙)

---

## 15. 코딩 컨벤션

### JavaScript

- **들여쓰기**: 스페이스 2칸
- **함수 선언**: `function` 키워드 사용 (화살표 함수는 콜백/IIFE에만)
- **const/let**: 전역 상수 → `const`, 변경 가능 변수 → `let`
- **HTML 생성**: 템플릿 리터럴(`` ` ` ``) 사용, 항상 `escHtml()` 적용
- **이벤트**: innerHTML 주입 요소는 반드시 이벤트 위임 방식
- **에러 처리**: `try/catch` + `showError()` 표시
- **localStorage**: 직접 접근 금지, 전용 load/save 함수 사용
- **섹션 구분**: `// ══════════════════════════` 구분선 주석 사용

### CSS

- **변수**: `var(--변수명)` 사용, 하드코딩 색상 지양
- **인라인 style**: 동적 색상(`LEVEL_COLOR`)만 허용, 그 외는 클래스로
- **새 클래스**: 관련 CSS 섹션 근처에 추가, 기존 패턴 유지
- **!important**: `.saved` 피드백 오버라이드 등 불가피한 경우에만 사용

### Python (빌드 스크립트)

- **인코딩**: 항상 `encoding='utf-8'`
- **경로**: `os.path.join()` 사용, 하드코딩 경로 금지
- **JSON 출력**: `ensure_ascii=False, separators=(',', ':')` (minified)

---

## 16. 주요 주의사항

### ❌ 하지 말 것

1. `build_html.py`로 `tangoya.html` 직접 덮어쓰기 → UI 변경 사항 소실
2. `onclick="func()"` 인라인 핸들러를 `innerHTML` 주입 요소에 사용 → 이벤트 위임 사용
3. `lookupWord()`에서 첫 번째 히트에서 즉시 return → `keepLowest()` 패턴 유지
4. `JLPT_DICT`에 높은 레벨(N1)을 낮은 레벨(N5)보다 먼저 등록 → N5 우선 원칙
5. `surface`/`baseForm` 변경 시 재렌더 트리거 누락 → `adminSaveField()`에서 재렌더
6. `commitKrEdit`/`cancelKrEdit`에서 span에 `onclick` 직접 할당 → 이벤트 위임이 처리
7. 새 편집 필드 추가 시 `applyAdminEdits()` 업데이트 누락
8. `enterAdminMode()`/`exitAdminMode()`에서 krEdits 재적용 없이 바로 `showResult()` 호출 → 저장된 한국어 뜻 소실
9. 사전 CSV 다운로드 중 `_dictDlCancelled` 플래그 체크 누락 → 취소 후에도 계속 실행됨

### ✅ 해야 할 것

1. UI 수정 후 반드시 `tangoya_template.html` 동기화 (섹션 14 명령어 사용)
2. 새 localStorage 키 추가 시: 상수 선언 → load/save 함수 쌍 → reset 함수
3. 새 편집 필드 추가 시: `applyAdminEdits()`에 복원 코드, `adminSaveField()`에 재렌더 트리거
4. 모든 사용자 입력 기반 HTML 출력에 `escHtml()` 적용
5. `lastResult` — 분석 결과 저장 후 재렌더 시 재사용 (`showResult(lastResult.tokens, lastResult.input)`)
6. `enterAdminMode()`/`exitAdminMode()` 재렌더 전에 `lastResult.tokens`에 krEdits 재적용
7. 사전 CSV 다운로드 배치 루프에 `_dictDlCancelled` 체크 포함

---

## 17. 접근성(ARIA) 마크업

| 요소 | 속성 |
|------|------|
| `#langModal` | `role="dialog"`, `aria-modal="true"`, `aria-labelledby="langModalTitle"` |
| `#adminModal` | `role="dialog"`, `aria-modal="true"` |
| `#dictEditModal` | `role="dialog"`, `aria-modal="true"`, `aria-labelledby="dictEditTitle"` |
| `#dictDlModal` | `role="dialog"`, `aria-modal="true"`, `aria-labelledby="dictDlTitle"` |
| `#errorMsg` | `role="alert"`, `aria-live="polite"` |
| `#loading` | `aria-live="polite"`, `aria-label="분석 중"` |
| `#translationSection` | `aria-live="polite"`, `aria-label="한국어 번역"` |
| `<section>` (입력/결과) | `aria-label` 각각 지정 |
| `<nav>` (범례) | `aria-label="JLPT 레벨 범례"` |

---

## 18. 디버깅 팁

```javascript
// JLPT_DICT 직접 조회
JLPT_DICT["会う"]            // {r:"あう", l:"N5", k:"만나다"}

// localStorage 확인
localStorage.getItem('tangoya_admin_edits')
localStorage.getItem('tangoya_kr_edits')
localStorage.getItem('tangoya_merge_rules')

// 최신 분석 결과 확인
lastResult.tokens            // 현재 화면의 토큰 배열
lastResult.input             // 원본 입력 텍스트

// 관리자 편집 저장 키 형식
// "origIdx@@inputText"  예: "0@@会う"

// 병합 규칙 형식
// {"会う": [[0,1]]}      → '会'(idx:0)와 'う'(idx:1)가 병합됨

// 사전 CSV 다운로드 중 취소
_dictDlCancelled = true

// 사전 수정 모달 목록 강제 갱신
_renderDictList()
```

**빌드 통계** (build_html.py 실행 시 출력):
- 레벨별 항목 수, 한국어 뜻 커버리지
- 중간 사전: `build/jlpt_dict.json` (13,680개 항목, 고유 단어 6,823개)

---

## 19. 오프라인 배포

tangoya는 인터넷 없이도 완전히 동작한다. 모든 외부 의존성이 `dist/` 폴더에 로컬로 포함되어 있다.
단, **한국어 번역** 기능과 **사전 CSV 다운로드의 번역 보완** 기능은 Google Translate API를 사용하므로 인터넷 연결이 필요하다.

### 19-1. 오프라인 파일 구조

```
dist/
├── tangoya.html           ← 메인 앱 (로컬 경로 참조)
├── tangoya_template.html  ← 빌드용 템플릿
├── kuromoji.js            ← Kuromoji v0.1.2 브라우저 빌드 (300 KB)
├── start_server.py        ← 로컬 서버 실행 스크립트
├── dict/                  ← Kuromoji 사전 파일 (총 ~17.8 MB)
│   ├── base.dat.gz        (3.8 MB)
│   ├── cc.dat.gz          (1.6 MB)
│   ├── check.dat.gz       (3.0 MB)
│   ├── tid.dat.gz         (1.5 MB)
│   ├── tid_map.dat.gz     (1.4 MB)
│   ├── tid_pos.dat.gz     (5.6 MB)
│   ├── unk.dat.gz / unk_*.dat.gz  (소형 파일 6개)
│   └── ... (총 12개)
└── fonts/                 ← Google Fonts 로컬 캐시
    ├── fonts.css          ← @font-face 정의
    └── *.woff2            ← Noto Serif JP / Noto Sans KR / DM Mono
```

### 19-2. 왜 HTTP 서버가 필요한가

Kuromoji 사전 로더(`BrowserDictionaryLoader`)는 **XMLHttpRequest**로 `dict/*.dat.gz` 파일을 로드한다.
`file://` 프로토콜에서는 브라우저 보안 정책(CORS)으로 XHR이 차단되므로
반드시 로컬 HTTP 서버를 통해 접근해야 한다.

### 19-3. 실행 방법

```bash
# dist/ 폴더에서 로컬 서버 실행 (포트 8000, 브라우저 자동 열림)
python3 dist/start_server.py

# 또는 npx serve 사용 (Claude Code 개발 환경에서 권장)
npx serve -l 8000 /path/to/tangoya/dist
```

→ `http://localhost:8000/tangoya.html` 자동 실행

### 19-4. 에셋 재다운로드 (초기 설치 또는 업데이트 시)

```bash
cd <프로젝트 루트>
python3 build/download_offline_assets.py
```

이미 존재하는 파일은 자동 스킵된다. 이 명령은 **인터넷 연결이 필요**하다.

### 19-5. CDN 참조 현황

| 항목 | 이전 (온라인) | 현재 (오프라인/하이브리드) |
|------|--------------|--------------------------|
| Google Fonts CSS | `https://fonts.googleapis.com/css2?...` | `fonts/fonts.css` |
| Kuromoji JS | `https://cdn.jsdelivr.net/npm/kuromoji@0.1.2/build/kuromoji.js` | `kuromoji.js` |
| Kuromoji 사전 | `https://cdn.jsdelivr.net/npm/kuromoji@0.1.2/dict` | `dict` |
| Google Translate | N/A | `https://translate.googleapis.com/translate_a/single` (온라인 필요) |

### 19-6. 에셋 업데이트 주의사항

- `build/download_offline_assets.py`를 재실행하면 기존 파일을 덮어쓰지 않는다 (skip)
- 강제 재다운로드 시: 해당 파일을 삭제한 후 스크립트 재실행
- `tangoya.html`이나 `tangoya_template.html`을 수정해도 로컬 에셋 경로는 변경되지 않음
- `build_html.py`로 재빌드해도 로컬 경로(`fonts/fonts.css`, `kuromoji.js`, `dict`)는 유지됨
  → `tangoya_template.html`에 이미 로컬 경로로 기록되어 있기 때문

### 19-7. Claude Code 개발 환경 서버 설정

`.claude/launch.json`에 `npx serve`를 사용하는 서버 구성이 등록되어 있다.
Python `http.server`는 Claude Code 샌드박스에서 `os.getcwd()` 호출로 인해 차단될 수 있으므로
`npx serve`를 사용하는 것을 권장한다.

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "tangoya",
      "runtimeExecutable": "npx",
      "runtimeArgs": ["serve", "-l", "8000", "/path/to/tangoya/dist"],
      "port": 8000
    }
  ]
}
```
