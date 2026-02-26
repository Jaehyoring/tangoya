# tangoya (単語屋)

일본어 JLPT 레벨 판정 앱 — 한국어 뜻 포함

---

## 웹에서 바로 실행

**https://jaehyoring.github.io/tangoya/dist/tangoya.html**

설치 없이 브라우저에서 즉시 사용 가능합니다.

---

## 빠른 시작 (로컬 실행)

| 플랫폼 | 실행 방법 |
|--------|----------|
| **macOS** | `tangoya.app` 더블클릭 |
| **Windows** | `tangoya.vbs` 더블클릭 |
| **터미널** | `python3 dist/start_server.py` |

더블클릭하면 터미널 창 없이 바로 브라우저가 열립니다.

**처음 실행 시** 필요한 에셋(Kuromoji 사전 ~17.8 MB, 폰트 파일)을 자동으로
다운로드한 뒤 브라우저가 열립니다. 두 번째 실행부터는 바로 시작됩니다.

> **요구사항**
> - Python 3.6+
> - 인터넷 연결 (최초 1회만 필요)

> **macOS 최초 실행 시** Gatekeeper 보안 경고가 뜰 수 있습니다.
> `tangoya.app`을 **우클릭 → 열기**로 실행하면 허용됩니다.

> **왜 서버가 필요한가?**
> Kuromoji 형태소 분석기가 사전 파일을 XHR로 로드하므로, `file://` 프로토콜로는
> 브라우저 보안 정책(CORS)에 의해 차단됩니다. 반드시 서버를 통해 열어야 합니다.

---

## 기능

- 일본어 단어/문장 입력 → 형태소별 JLPT 레벨 판정 (N1~N5)
- 각 단어에 한국어 뜻 표시
- 다크/라이트 모드 전환
- 관리자 모드: 읽기/레벨/품사/한자표기/뜻 수정 (비밀번호: 4649)
- 형태소 병합 기능 (예: `お` + `田` → `お田`)
- 수정 내역 자동 저장 (localStorage)
- 결과 내보내기 (JSON / CSV / TXT)

---

## 파일 구조

```
tangoya/
├── tangoya.app/            ← macOS 앱 (더블클릭, 터미널 없이 실행)
├── tangoya.vbs             ← Windows 실행 파일 (더블클릭, 창 없이 실행)
├── data/
│   ├── N1~N5_words_naver.txt   JLPT 단어 데이터 (총 7,685개)
│   └── korean_dict.json        한국어 뜻 사전 (7,518개)
├── build/
│   ├── download_offline_assets.py  ← 오프라인 에셋 다운로드 (최초 1회)
│   ├── build_html.py               ← HTML 재빌드
│   ├── build_dict.py               중간 사전 생성
│   └── add_korean.py               한국어 뜻 자동 생성 (jamdict 필요)
└── dist/
    ├── tangoya.html            ← 앱 본체 (~824 KB, JLPT_DICT 내장)
    ├── tangoya_template.html   빌드용 템플릿
    ├── start_server.py         ← 로컬 서버 실행기
    ├── kuromoji.js             Kuromoji JS (download 후 생성, ~301 KB)
    ├── dict/                   Kuromoji 사전 파일 (download 후 생성, ~17.8 MB)
    └── fonts/                  폰트 파일 (download 후 생성)
        ├── fonts.css
        └── *.woff2
```

> `dist/kuromoji.js`, `dist/dict/`, `dist/fonts/*.woff2`는 `.gitignore`에 포함된 대용량 파일입니다.
> 저장소 클론 후 `python3 dist/start_server.py`를 실행하면 자동으로 다운로드됩니다.

---

## 개발자용: 데이터 업데이트

```bash
# 단어 파일 수정 후 재빌드
python3 build/build_html.py

# 한국어 뜻도 재생성할 경우 (jamdict 필요)
python3 build/add_korean.py
python3 build/build_html.py
```

---

## 기술 스택

- **형태소 분석**: Kuromoji.js v0.1.2 (IPAdic 사전)
- **JLPT 데이터**: N1~N5 총 13,680개 항목 + 한국어 뜻 내장
- **배포**: 단일 HTML 파일 + 로컬 에셋 폴더 구조
- **요구사항**: Python 3.6+
