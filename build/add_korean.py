#!/usr/bin/env python3
"""
add_korean.py  (API-free 버전)
jamdict(JMdict) 로 영어 뜻을 가져온 뒤
영어→한국어 변환 테이블로 한국어 뜻을 생성하고
tangoya/data/korean_dict.json 에 저장한다.
"""

import os, json, re
from jamdict import Jamdict

# ── 경로 설정 ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, "data")
OUT_FILE  = os.path.join(DATA_DIR, "korean_dict.json")

jmd = Jamdict()

# ══════════════════════════════════════════════════════════
# 영어 글로스 → 한국어 직접 매핑 테이블 (자주 등장하는 표현 우선)
# ══════════════════════════════════════════════════════════
EN_KO: dict[str, str] = {
    # ── 동사 (to + 원형) ──────────────────────────────────
    "to meet": "만나다", "to encounter": "만나다", "to see": "보다",
    "to eat": "먹다", "to drink": "마시다", "to run": "달리다",
    "to walk": "걷다", "to go": "가다", "to come": "오다",
    "to return": "돌아오다", "to come back": "돌아오다",
    "to write": "쓰다", "to read": "읽다", "to speak": "말하다",
    "to say": "말하다", "to tell": "말하다", "to talk": "이야기하다",
    "to listen": "듣다", "to hear": "듣다",
    "to see (a movie, show, etc.)": "보다",
    "to look": "보다", "to watch": "보다",
    "to think": "생각하다", "to know": "알다", "to understand": "이해하다",
    "to learn": "배우다", "to study": "공부하다", "to teach": "가르치다",
    "to work": "일하다", "to do": "하다", "to make": "만들다",
    "to create": "만들다", "to build": "만들다",
    "to buy": "사다", "to sell": "팔다", "to use": "사용하다",
    "to open": "열다", "to close": "닫다", "to shut": "닫다",
    "to enter": "들어가다", "to exit": "나가다", "to leave": "떠나다",
    "to arrive": "도착하다", "to start": "시작하다", "to begin": "시작하다",
    "to finish": "끝내다", "to end": "끝나다", "to stop": "멈추다",
    "to wait": "기다리다", "to rest": "쉬다", "to sleep": "자다",
    "to wake up": "일어나다", "to get up": "일어나다",
    "to sit": "앉다", "to stand": "서다", "to stand up": "일어서다",
    "to lie down": "눕다", "to fall": "떨어지다", "to fall down": "쓰러지다",
    "to rise": "오르다", "to go up": "올라가다", "to go down": "내려가다",
    "to put": "놓다", "to place": "놓다", "to set": "놓다",
    "to take": "가져가다", "to bring": "가져오다", "to carry": "나르다",
    "to hold": "잡다", "to grab": "잡다", "to catch": "잡다",
    "to throw": "던지다", "to push": "밀다", "to pull": "당기다",
    "to cut": "자르다", "to break": "부수다", "to fix": "고치다",
    "to repair": "고치다", "to clean": "청소하다", "to wash": "씻다",
    "to cook": "요리하다", "to prepare": "준비하다",
    "to send": "보내다", "to receive": "받다", "to give": "주다",
    "to lend": "빌려주다", "to borrow": "빌리다",
    "to pay": "지불하다", "to pay for": "내다",
    "to call": "전화하다", "to telephone": "전화하다",
    "to visit": "방문하다", "to travel": "여행하다",
    "to live": "살다", "to exist": "있다", "to be": "이다",
    "to have": "있다", "to possess": "가지다", "to own": "소유하다",
    "to need": "필요하다", "to want": "원하다", "to wish": "바라다",
    "to hope": "바라다", "to like": "좋아하다", "to love": "사랑하다",
    "to hate": "싫어하다", "to dislike": "싫어하다",
    "to feel": "느끼다", "to think about": "생각하다",
    "to remember": "기억하다", "to forget": "잊다",
    "to find": "찾다", "to look for": "찾다", "to search": "찾다",
    "to lose": "잃다", "to drop": "떨어뜨리다",
    "to win": "이기다", "to lose (a game)": "지다",
    "to play": "놀다", "to sing": "노래하다", "to dance": "춤추다",
    "to draw": "그리다", "to paint": "그리다",
    "to show": "보여주다", "to display": "보여주다",
    "to ask": "묻다", "to question": "질문하다", "to answer": "대답하다",
    "to reply": "대답하다", "to respond": "응답하다",
    "to help": "돕다", "to assist": "돕다",
    "to change": "바꾸다", "to exchange": "교환하다",
    "to move": "움직이다", "to transfer": "옮기다",
    "to happen": "일어나다", "to occur": "일어나다",
    "to become": "되다", "to turn into": "되다",
    "to increase": "늘다", "to decrease": "줄다",
    "to grow": "자라다", "to develop": "발전하다",
    "to gather": "모이다", "to collect": "모으다",
    "to separate": "나누다", "to divide": "나누다",
    "to connect": "연결하다", "to join": "합류하다",
    "to continue": "계속하다", "to repeat": "반복하다",
    "to try": "시도하다", "to attempt": "시도하다",
    "to succeed": "성공하다", "to fail": "실패하다",
    "to decide": "결정하다", "to choose": "선택하다",
    "to solve": "해결하다", "to resolve": "해결하다",
    "to accept": "받아들이다", "to refuse": "거절하다",
    "to agree": "동의하다", "to disagree": "동의하지 않다",
    "to apologize": "사과하다", "to forgive": "용서하다",
    "to protect": "보호하다", "to save": "구하다",
    "to escape": "도망치다", "to hide": "숨다",
    "to appear": "나타나다", "to disappear": "사라지다",
    "to produce": "생산하다", "to manufacture": "제조하다",
    "to sell": "팔다", "to purchase": "구입하다",
    "to consider": "고려하다", "to examine": "검토하다",
    "to check": "확인하다", "to confirm": "확인하다",
    "to prove": "증명하다", "to test": "테스트하다",
    "to measure": "측정하다", "to calculate": "계산하다",
    "to count": "세다", "to number": "번호를 매기다",
    "to record": "기록하다", "to note": "메모하다",
    "to report": "보고하다", "to announce": "발표하다",
    "to explain": "설명하다", "to describe": "설명하다",
    "to express": "표현하다", "to represent": "나타내다",
    "to achieve": "달성하다", "to accomplish": "이루다",
    "to manage": "관리하다", "to control": "통제하다",
    "to lead": "이끌다", "to guide": "안내하다",
    "to follow": "따르다", "to obey": "따르다",
    "to fight": "싸우다", "to argue": "다투다",
    "to discuss": "논의하다", "to debate": "토론하다",
    "to worry": "걱정하다", "to fear": "두려워하다",
    "to laugh": "웃다", "to smile": "미소 짓다", "to cry": "울다",
    "to be surprised": "놀라다", "to be shocked": "충격받다",
    "to be pleased": "기뻐하다", "to be glad": "기뻐하다",
    "to be sad": "슬퍼하다", "to be angry": "화내다",
    "to be tired": "피곤하다", "to be sick": "아프다",
    "to be born": "태어나다", "to die": "죽다",
    "to marry": "결혼하다", "to divorce": "이혼하다",
    "to graduate": "졸업하다", "to enter (school)": "입학하다",
    "to resign": "사임하다", "to retire": "은퇴하다",
    "to hire": "고용하다", "to fire": "해고하다",
    "to plant": "심다", "to harvest": "수확하다",
    "to fly": "날다", "to swim": "수영하다",
    "to drive": "운전하다", "to ride": "타다",
    "to park": "주차하다", "to sail": "항해하다",
    "to jump": "뛰어오르다", "to climb": "오르다",
    "to dig": "파다", "to mine": "채굴하다",
    "to melt": "녹다", "to freeze": "얼다", "to burn": "타다",
    "to shine": "빛나다", "to light": "켜다", "to turn off": "끄다",
    "to press": "누르다", "to touch": "만지다",
    "to smell": "냄새 맡다", "to taste": "맛보다",
    "to mix": "섞다", "to stir": "젓다",
    "to fold": "접다", "to wrap": "싸다",
    "to tie": "묶다", "to untie": "풀다",
    "to lock": "잠그다", "to unlock": "열다",
    "to load": "싣다", "to unload": "내리다",
    "to fill": "채우다", "to empty": "비우다",
    "to stretch": "늘리다", "to shrink": "줄이다",
    "to copy": "복사하다", "to print": "인쇄하다",
    "to type": "타이핑하다", "to input": "입력하다",
    "to download": "다운로드하다", "to upload": "업로드하다",
    "to share": "공유하다", "to distribute": "배포하다",
    "to reserve": "예약하다", "to book": "예약하다",
    "to cancel": "취소하다", "to postpone": "연기하다",
    "to plan": "계획하다", "to prepare": "준비하다",
    "to practice": "연습하다", "to train": "훈련하다",
    "to perform": "공연하다", "to act": "행동하다",
    "to compete": "경쟁하다", "to race": "경주하다",
    "to compare": "비교하다", "to contrast": "대조하다",
    "to combine": "결합하다", "to merge": "합치다",
    "to split": "분리하다", "to break apart": "분리하다",
    "to improve": "개선하다", "to upgrade": "향상시키다",
    "to reduce": "줄이다", "to eliminate": "없애다",
    "to add": "추가하다", "to remove": "제거하다",
    "to include": "포함하다", "to exclude": "제외하다",
    "to apply": "적용하다", "to use": "사용하다",
    "to adopt": "채택하다", "to introduce": "소개하다",
    "to establish": "설립하다", "to found": "설립하다",
    "to abolish": "폐지하다", "to destroy": "파괴하다",
    "to damage": "손상시키다", "to harm": "해치다",
    "to heal": "치유하다", "to cure": "치료하다",
    "to treat": "치료하다", "to examine": "진찰하다",
    "to consult": "상담하다", "to advise": "조언하다",
    "to warn": "경고하다", "to threaten": "위협하다",
    "to promise": "약속하다", "to swear": "맹세하다",
    "to trust": "신뢰하다", "to believe": "믿다",
    "to doubt": "의심하다", "to suspect": "의심하다",
    "to recognize": "인식하다", "to identify": "확인하다",
    "to distinguish": "구분하다", "to classify": "분류하다",
    "to organize": "정리하다", "to arrange": "정렬하다",
    "to order": "주문하다", "to command": "명령하다",
    "to request": "요청하다", "to demand": "요구하다",
    "to offer": "제공하다", "to suggest": "제안하다",
    "to propose": "제안하다", "to recommend": "추천하다",
    "to approve": "승인하다", "to reject": "거부하다",
    "to complain": "불평하다", "to protest": "항의하다",
    "to celebrate": "축하하다", "to congratulate": "축하하다",
    "to invite": "초대하다", "to welcome": "환영하다",
    "to greet": "인사하다", "to farewell": "작별 인사하다",
    "to thank": "감사하다", "to praise": "칭찬하다",
    "to criticize": "비판하다", "to blame": "비난하다",
    "to support": "지지하다", "to oppose": "반대하다",
    "to vote": "투표하다", "to elect": "선출하다",
    "to participate": "참가하다", "to join": "참여하다",
    "to contribute": "기여하다", "to donate": "기부하다",
    "to invest": "투자하다", "to save (money)": "저축하다",
    "to spend": "쓰다", "to waste": "낭비하다",
    "to earn": "벌다", "to gain": "얻다",
    "to obtain": "얻다", "to acquire": "획득하다",
    "to lose (weight)": "빠지다", "to gain (weight)": "늘다",
    "to grow up": "자라다", "to mature": "성숙하다",
    "to age": "나이 들다", "to expire": "만료되다",
    "to last": "지속하다", "to endure": "견디다",
    "to suffer": "고통받다", "to struggle": "고생하다",
    "to enjoy": "즐기다", "to appreciate": "감상하다",
    "to admire": "감탄하다", "to respect": "존경하다",
    "to envy": "부러워하다", "to imitate": "모방하다",
    "to pretend": "가장하다", "to deceive": "속이다",
    "to lie": "거짓말하다", "to cheat": "속이다",
    "to steal": "훔치다", "to rob": "빼앗다",
    "to attack": "공격하다", "to defend": "방어하다",
    "to escape": "도망치다", "to surrender": "항복하다",
    "to negotiate": "협상하다", "to compromise": "타협하다",
    "to cooperate": "협력하다", "to collaborate": "협력하다",
    "to compete": "경쟁하다", "to challenge": "도전하다",
    "to overcome": "극복하다", "to conquer": "정복하다",
    "to explore": "탐험하다", "to discover": "발견하다",
    "to invent": "발명하다", "to innovate": "혁신하다",
    "to design": "설계하다", "to develop": "개발하다",
    "to research": "연구하다", "to investigate": "조사하다",
    "to analyze": "분석하다", "to evaluate": "평가하다",
    "to review": "검토하다", "to revise": "수정하다",
    "to edit": "편집하다", "to translate": "번역하다",
    "to interpret": "해석하다", "to explain": "설명하다",
    "to summarize": "요약하다", "to conclude": "결론짓다",
    "to assume": "가정하다", "to suppose": "가정하다",
    "to imagine": "상상하다", "to dream": "꿈꾸다",
    "to concentrate": "집중하다", "to focus": "집중하다",
    "to relax": "쉬다", "to calm down": "진정하다",
    "to hurry": "서두르다", "to rush": "서두르다",
    "to delay": "지연하다", "to hesitate": "망설이다",
    "to give up": "포기하다", "to quit": "그만두다",
    "to recover": "회복하다", "to restore": "회복하다",
    "to maintain": "유지하다", "to preserve": "보존하다",
    "to protect": "보호하다", "to guard": "지키다",
    "to watch over": "지켜보다", "to care for": "돌보다",
    "to raise": "키우다", "to bring up": "키우다",
    "to educate": "교육하다", "to train": "훈련하다",
    "to test": "시험하다", "to examine": "시험하다",
    "to pass": "합격하다", "to fail (an exam)": "불합격하다",
    "to graduate from": "졸업하다", "to enroll": "입학하다",
    "to register": "등록하다", "to sign up": "신청하다",
    "to apply for": "신청하다", "to submit": "제출하다",
    "to hand in": "제출하다", "to deliver": "전달하다",
    "to pick up": "집어들다", "to drop off": "내려주다",
    "to switch": "전환하다", "to turn": "돌리다",
    "to bend": "구부리다", "to twist": "비틀다",
    "to shake": "흔들다", "to wave": "흔들다",
    "to nod": "끄덕이다", "to bow": "절하다",
    "to point": "가리키다", "to indicate": "가리키다",
    "to signal": "신호하다", "to communicate": "소통하다",
    "to contact": "연락하다", "to reach": "연락하다",
    "to connect": "접속하다", "to log in": "로그인하다",
    "to access": "접근하다", "to enter": "입력하다",

    # ── 형용사 ────────────────────────────────────────────
    "blue": "파란", "azure": "하늘색", "navy": "남색",
    "red": "빨간", "green": "초록색", "yellow": "노란",
    "white": "흰", "black": "검은", "gray": "회색",
    "brown": "갈색", "orange": "주황색", "purple": "보라색",
    "pink": "분홍색", "gold": "금색", "silver": "은색",
    "big": "큰", "large": "큰", "huge": "거대한",
    "small": "작은", "little": "작은", "tiny": "아주 작은",
    "long": "긴", "short": "짧은", "tall": "키 큰", "low": "낮은",
    "wide": "넓은", "narrow": "좁은", "broad": "넓은",
    "thick": "두꺼운", "thin": "얇은", "deep": "깊은", "shallow": "얕은",
    "heavy": "무거운", "light": "가벼운",
    "hard": "딱딱한", "soft": "부드러운",
    "hot": "뜨거운", "warm": "따뜻한", "cool": "시원한", "cold": "차가운",
    "fast": "빠른", "quick": "빠른", "slow": "느린",
    "strong": "강한", "weak": "약한", "powerful": "강력한",
    "new": "새로운", "old": "오래된", "ancient": "고대의",
    "young": "젊은", "old (person)": "늙은",
    "good": "좋은", "bad": "나쁜", "excellent": "훌륭한",
    "great": "훌륭한", "wonderful": "멋진", "amazing": "놀라운",
    "beautiful": "아름다운", "pretty": "예쁜", "lovely": "사랑스러운",
    "ugly": "못생긴", "dirty": "더러운", "clean": "깨끗한",
    "neat": "깔끔한", "tidy": "단정한", "messy": "지저분한",
    "bright": "밝은", "dark": "어두운", "shiny": "빛나는",
    "clear": "맑은", "cloudy": "흐린", "foggy": "안개 낀",
    "dry": "건조한", "wet": "젖은", "humid": "습한",
    "sweet": "달콤한", "sour": "신", "bitter": "쓴", "spicy": "매운",
    "salty": "짠", "delicious": "맛있는", "tasty": "맛있는",
    "rich": "풍부한", "poor": "가난한", "cheap": "저렴한", "expensive": "비싼",
    "free": "무료의", "valuable": "가치 있는", "worthless": "가치 없는",
    "safe": "안전한", "dangerous": "위험한", "risky": "위험한",
    "easy": "쉬운", "simple": "간단한", "difficult": "어려운", "hard": "어려운",
    "complex": "복잡한", "complicated": "복잡한",
    "busy": "바쁜", "free (available)": "한가한", "idle": "한가한",
    "happy": "행복한", "glad": "기쁜", "joyful": "즐거운",
    "sad": "슬픈", "unhappy": "불행한", "miserable": "비참한",
    "angry": "화난", "furious": "격노한", "upset": "속상한",
    "calm": "차분한", "peaceful": "평화로운", "quiet": "조용한",
    "loud": "시끄러운", "noisy": "시끄러운",
    "tired": "피곤한", "exhausted": "지친", "energetic": "활기찬",
    "healthy": "건강한", "sick": "아픈", "ill": "아픈",
    "alive": "살아있는", "dead": "죽은",
    "true": "사실인", "false": "거짓인", "real": "진짜의", "fake": "가짜의",
    "correct": "올바른", "wrong": "틀린", "accurate": "정확한",
    "sure": "확실한", "uncertain": "불확실한",
    "possible": "가능한", "impossible": "불가능한",
    "necessary": "필요한", "unnecessary": "불필요한",
    "important": "중요한", "unimportant": "중요하지 않은",
    "interesting": "흥미로운", "boring": "지루한",
    "funny": "재미있는", "serious": "진지한",
    "kind": "친절한", "unkind": "불친절한", "gentle": "온화한",
    "cruel": "잔인한", "harsh": "가혹한",
    "honest": "정직한", "dishonest": "부정직한",
    "brave": "용감한", "cowardly": "겁쟁이",
    "smart": "똑똑한", "clever": "영리한", "intelligent": "지적인",
    "stupid": "멍청한", "foolish": "어리석은",
    "careful": "조심스러운", "careless": "부주의한",
    "polite": "예의 바른", "rude": "무례한",
    "patient": "인내심 있는", "impatient": "참을성 없는",
    "strict": "엄격한", "lenient": "너그러운",
    "famous": "유명한", "unknown": "무명의",
    "popular": "인기 있는", "unpopular": "인기 없는",
    "special": "특별한", "ordinary": "평범한", "normal": "보통의",
    "strange": "이상한", "weird": "이상한", "unusual": "특이한",
    "natural": "자연스러운", "artificial": "인공적인",
    "original": "독창적인", "unique": "유일한",
    "similar": "비슷한", "different": "다른", "same": "같은",
    "various": "다양한", "diverse": "다양한",
    "complete": "완전한", "incomplete": "불완전한",
    "perfect": "완벽한", "imperfect": "불완전한",
    "whole": "전체의", "partial": "부분적인",
    "alone": "혼자인", "lonely": "외로운",
    "together": "함께", "separate": "분리된",
    "public": "공공의", "private": "개인의",
    "open": "열려있는", "closed": "닫혀있는",
    "full": "가득 찬", "empty": "빈",
    "fresh": "신선한", "stale": "오래된",
    "raw": "날것의", "cooked": "익힌",
    "sharp": "날카로운", "dull": "무딘",
    "smooth": "매끄러운", "rough": "거친",
    "flat": "평평한", "curved": "굽은",
    "round": "둥근", "square": "네모난",
    "straight": "곧은", "crooked": "구부러진",
    "right": "오른쪽의", "left": "왼쪽의",
    "upper": "위의", "lower": "아래의",
    "front": "앞의", "back": "뒤의",
    "inner": "내부의", "outer": "외부의",
    "main": "주된", "minor": "부수적인",
    "major": "주요한", "secondary": "이차적인",
    "general": "일반적인", "specific": "특정한",
    "global": "세계적인", "local": "지역적인",
    "national": "국가적인", "international": "국제적인",
    "traditional": "전통적인", "modern": "현대적인",
    "formal": "공식적인", "informal": "비공식적인",
    "official": "공식적인", "unofficial": "비공식적인",
    "legal": "합법적인", "illegal": "불법적인",
    "fair": "공평한", "unfair": "불공평한",
    "equal": "동등한", "unequal": "불평등한",
    "mutual": "상호적인", "one-sided": "일방적인",
    "voluntary": "자발적인", "compulsory": "의무적인",
    "temporary": "임시적인", "permanent": "영구적인",
    "flexible": "유연한", "rigid": "딱딱한",
    "active": "활발한", "passive": "수동적인",
    "positive": "긍정적인", "negative": "부정적인",
    "optimistic": "낙관적인", "pessimistic": "비관적인",
    "reasonable": "합리적인", "unreasonable": "비합리적인",
    "logical": "논리적인", "illogical": "비논리적인",
    "practical": "실용적인", "theoretical": "이론적인",

    # ── 명사 ──────────────────────────────────────────────
    "student": "학생", "teacher": "교사", "professor": "교수",
    "doctor": "의사", "nurse": "간호사", "hospital": "병원",
    "school": "학교", "university": "대학교", "college": "대학",
    "company": "회사", "office": "사무실", "factory": "공장",
    "shop": "가게", "store": "가게", "market": "시장",
    "restaurant": "식당", "hotel": "호텔", "bank": "은행",
    "library": "도서관", "museum": "박물관", "park": "공원",
    "station": "역", "airport": "공항", "port": "항구",
    "house": "집", "home": "집", "apartment": "아파트",
    "room": "방", "kitchen": "부엌", "bathroom": "욕실",
    "window": "창문", "door": "문", "floor": "바닥",
    "wall": "벽", "ceiling": "천장", "roof": "지붕",
    "street": "길", "road": "도로", "bridge": "다리",
    "country": "나라", "city": "도시", "town": "마을",
    "village": "마을", "island": "섬", "mountain": "산",
    "river": "강", "lake": "호수", "sea": "바다", "ocean": "바다",
    "forest": "숲", "field": "들판", "farm": "농장",
    "person": "사람", "man": "남자", "woman": "여자",
    "child": "아이", "baby": "아기", "adult": "어른",
    "family": "가족", "parent": "부모", "mother": "어머니",
    "father": "아버지", "son": "아들", "daughter": "딸",
    "brother": "형제", "sister": "자매", "husband": "남편",
    "wife": "아내", "friend": "친구", "neighbor": "이웃",
    "colleague": "동료", "boss": "상사", "employee": "직원",
    "customer": "고객", "visitor": "방문객", "guest": "손님",
    "face": "얼굴", "eye": "눈", "nose": "코", "mouth": "입",
    "ear": "귀", "hand": "손", "foot": "발", "leg": "다리",
    "arm": "팔", "head": "머리", "heart": "심장", "body": "몸",
    "hair": "머리카락", "skin": "피부", "blood": "피",
    "food": "음식", "meal": "식사", "breakfast": "아침식사",
    "lunch": "점심", "dinner": "저녁", "rice": "밥",
    "bread": "빵", "meat": "고기", "fish": "생선",
    "vegetable": "채소", "fruit": "과일", "water": "물",
    "tea": "차", "coffee": "커피", "juice": "주스",
    "sugar": "설탕", "salt": "소금", "oil": "기름",
    "book": "책", "newspaper": "신문", "magazine": "잡지",
    "letter": "편지", "document": "서류", "paper": "종이",
    "pen": "펜", "pencil": "연필", "notebook": "노트",
    "bag": "가방", "wallet": "지갑", "key": "열쇠",
    "phone": "전화", "computer": "컴퓨터", "camera": "카메라",
    "television": "텔레비전", "radio": "라디오", "clock": "시계",
    "watch": "시계", "glasses": "안경",
    "car": "자동차", "bus": "버스", "train": "기차",
    "bicycle": "자전거", "ship": "배", "airplane": "비행기",
    "money": "돈", "price": "가격", "cost": "비용",
    "work": "일", "job": "직업", "career": "직업",
    "business": "사업", "trade": "무역", "economy": "경제",
    "politics": "정치", "society": "사회", "culture": "문화",
    "history": "역사", "science": "과학", "technology": "기술",
    "art": "예술", "music": "음악", "sports": "스포츠",
    "game": "게임", "sport": "스포츠", "match": "경기",
    "team": "팀", "player": "선수", "coach": "감독",
    "language": "언어", "word": "단어", "sentence": "문장",
    "story": "이야기", "news": "뉴스", "information": "정보",
    "question": "질문", "answer": "답", "problem": "문제",
    "idea": "아이디어", "opinion": "의견", "fact": "사실",
    "reason": "이유", "result": "결과", "effect": "효과",
    "method": "방법", "way": "방법", "means": "수단",
    "plan": "계획", "project": "프로젝트", "goal": "목표",
    "rule": "규칙", "law": "법", "order": "명령",
    "right": "권리", "duty": "의무", "responsibility": "책임",
    "power": "힘", "energy": "에너지", "force": "힘",
    "light": "빛", "sound": "소리", "voice": "목소리",
    "color": "색", "shape": "모양", "size": "크기",
    "number": "숫자", "amount": "양", "quantity": "수량",
    "time": "시간", "hour": "시간", "minute": "분",
    "second": "초", "day": "날", "week": "주",
    "month": "달", "year": "년", "century": "세기",
    "morning": "아침", "afternoon": "오후", "evening": "저녁",
    "night": "밤", "midnight": "자정", "noon": "정오",
    "spring": "봄", "summer": "여름", "autumn": "가을", "fall": "가을",
    "winter": "겨울", "season": "계절", "weather": "날씨",
    "rain": "비", "snow": "눈", "wind": "바람", "cloud": "구름",
    "sun": "태양", "moon": "달", "star": "별",
    "sky": "하늘", "earth": "지구", "ground": "땅",
    "fire": "불", "water (element)": "물", "air": "공기",
    "nature": "자연", "environment": "환경", "space": "우주",
    "animal": "동물", "plant": "식물", "tree": "나무",
    "flower": "꽃", "grass": "풀", "leaf": "잎",
    "dog": "개", "cat": "고양이", "bird": "새",
    "fish (animal)": "물고기", "horse": "말", "cow": "소",
    "pig": "돼지", "chicken": "닭", "rabbit": "토끼",
    "color": "색깔", "pattern": "무늬", "design": "디자인",
    "material": "재료", "wood": "나무", "metal": "금속",
    "stone": "돌", "glass": "유리", "plastic": "플라스틱",
    "cloth": "천", "thread": "실", "needle": "바늘",
    "cup": "컵", "glass (cup)": "컵", "plate": "접시",
    "bowl": "그릇", "pot": "냄비", "pan": "프라이팬",
    "knife": "칼", "fork": "포크", "spoon": "숟가락",
    "chair": "의자", "table": "탁자", "desk": "책상",
    "bed": "침대", "sofa": "소파", "shelf": "선반",
    "box": "상자", "bottle": "병", "jar": "항아리",
    "medicine": "약", "pill": "알약", "treatment": "치료",
    "disease": "병", "illness": "병", "pain": "통증",
    "accident": "사고", "incident": "사건", "disaster": "재해",
    "war": "전쟁", "peace": "평화", "conflict": "갈등",
    "agreement": "합의", "contract": "계약", "treaty": "조약",
    "meeting": "회의", "conference": "회의", "event": "행사",
    "party": "파티", "ceremony": "행사", "festival": "축제",
    "wedding": "결혼식", "funeral": "장례식", "birthday": "생일",
    "holiday": "휴일", "vacation": "방학", "trip": "여행",
    "tour": "관광", "tourism": "관광", "sightseeing": "관광",
    "photo": "사진", "picture": "그림", "image": "이미지",
    "film": "영화", "movie": "영화", "drama": "드라마",
    "song": "노래", "melody": "멜로디", "rhythm": "리듬",
    "dance": "춤", "performance": "공연", "show": "공연",
    "education": "교육", "knowledge": "지식", "experience": "경험",
    "skill": "기술", "ability": "능력", "talent": "재능",
    "memory": "기억", "dream": "꿈", "imagination": "상상",
    "feeling": "감정", "emotion": "감정", "mood": "기분",
    "love": "사랑", "hate": "증오", "fear": "두려움",
    "hope": "희망", "joy": "기쁨", "sadness": "슬픔",
    "anger": "분노", "surprise": "놀라움", "disgust": "혐오",
    "pride": "자부심", "shame": "부끄러움", "guilt": "죄책감",
    "trust": "신뢰", "doubt": "의심", "belief": "믿음",
    "health": "건강", "life": "생명", "death": "죽음",
    "birth": "탄생", "age": "나이", "growth": "성장",
    "change": "변화", "development": "발전", "progress": "발전",
    "success": "성공", "failure": "실패", "mistake": "실수",
    "effort": "노력", "practice": "연습", "habit": "습관",
    "character": "성격", "personality": "개성", "attitude": "태도",
    "behavior": "행동", "action": "행동", "activity": "활동",
    "relationship": "관계", "connection": "연결", "link": "연결",
    "communication": "소통", "conversation": "대화", "talk": "이야기",
    "speech": "연설", "lecture": "강의", "lesson": "수업",
    "class": "수업", "course": "과정", "subject": "과목",
    "exam": "시험", "test": "시험", "grade": "성적",
    "score": "점수", "rank": "순위", "level": "수준",
    "quality": "품질", "standard": "기준", "value": "가치",
    "price": "가격", "rate": "비율", "percent": "퍼센트",
    "total": "합계", "sum": "합계", "average": "평균",
    "maximum": "최대", "minimum": "최소", "limit": "한계",
    "beginning": "시작", "start": "시작", "end": "끝",
    "middle": "중간", "center": "중심", "edge": "가장자리",
    "surface": "표면", "inside": "내부", "outside": "외부",
    "side": "측면", "part": "부분", "whole": "전체",
    "group": "그룹", "team": "팀", "organization": "조직",
    "club": "클럽", "association": "협회", "union": "연합",
    "government": "정부", "state": "국가", "nation": "국가",
    "society": "사회", "community": "공동체", "public": "공공",
    "people": "사람들", "population": "인구", "citizen": "시민",
    "leader": "지도자", "member": "회원", "participant": "참가자",
    "expert": "전문가", "specialist": "전문가", "professional": "전문가",
    "beginner": "초보자", "amateur": "아마추어",
    "winner": "우승자", "champion": "챔피언", "prize": "상",
    "award": "상", "trophy": "트로피", "medal": "메달",
    "information": "정보", "data": "데이터", "statistics": "통계",
    "research": "연구", "study": "연구", "survey": "조사",
    "report": "보고서", "article": "기사", "essay": "에세이",
    "novel": "소설", "poem": "시", "script": "대본",
    "signal": "신호", "message": "메시지", "notice": "공지",
    "advertisement": "광고", "announcement": "발표",
    "title": "제목", "name": "이름", "label": "라벨",
    "address": "주소", "location": "위치", "place": "장소",
    "area": "지역", "region": "지역", "zone": "구역",
    "distance": "거리", "direction": "방향", "position": "위치",
    "north": "북쪽", "south": "남쪽", "east": "동쪽", "west": "서쪽",
    "top": "위", "bottom": "아래", "left": "왼쪽", "right": "오른쪽",
    "situation": "상황", "condition": "상태", "state": "상태",
    "case": "경우", "example": "예", "instance": "예",
    "type": "유형", "kind": "종류", "sort": "종류",
    "category": "범주", "class": "종류", "species": "종",
    "model": "모델", "pattern": "패턴", "style": "스타일",
    "version": "버전", "edition": "판", "copy": "복사본",
    "original": "원본", "draft": "초안", "final": "최종",
    "beginning": "처음", "introduction": "소개", "conclusion": "결론",
    "summary": "요약", "outline": "개요", "detail": "세부사항",
    "point": "포인트", "argument": "주장", "evidence": "증거",
    "cause": "원인", "effect": "결과", "consequence": "결과",
    "solution": "해결책", "answer": "답", "response": "반응",

    # ── 부사/접속사/감탄사 ────────────────────────────────
    "slowly": "천천히", "quickly": "빠르게", "carefully": "조심스럽게",
    "suddenly": "갑자기", "gradually": "점차", "finally": "마침내",
    "already": "이미", "still": "아직", "yet": "아직",
    "again": "다시", "always": "항상", "never": "절대로",
    "often": "자주", "sometimes": "때때로", "rarely": "드물게",
    "soon": "곧", "immediately": "즉시", "recently": "최근에",
    "now": "지금", "then": "그때", "later": "나중에",
    "before": "이전에", "after": "이후에", "during": "동안",
    "together": "함께", "separately": "따로", "alone": "혼자",
    "here": "여기", "there": "저기", "everywhere": "어디서나",
    "very": "매우", "extremely": "매우", "quite": "꽤",
    "just": "바로", "only": "오직", "also": "또한",
    "too": "또한", "furthermore": "더욱이", "moreover": "게다가",
    "however": "그러나", "but": "그러나", "although": "비록",
    "if": "만약", "because": "왜냐하면", "since": "이후로",
    "while": "~하는 동안", "when": "~할 때", "where": "~하는 곳",
    "whether": "~인지", "that": "~라는 것", "so": "그래서",
    "therefore": "따라서", "thus": "따라서", "hence": "그러므로",
    "yes": "예", "no": "아니요", "maybe": "아마",
    "perhaps": "아마도", "certainly": "확실히", "probably": "아마도",
    "especially": "특히", "particularly": "특히", "mainly": "주로",
    "generally": "일반적으로", "usually": "보통", "normally": "보통",
    "actually": "실제로", "really": "정말로", "truly": "진정으로",
    "almost": "거의", "nearly": "거의", "about": "약",
    "approximately": "약", "exactly": "정확히", "precisely": "정확히",

    # ── 접두어/접미어 포함 표현 ──────────────────────────
    "without haste": "여유롭게", "unhurriedly": "천천히",
    "in order": "순서대로", "at once": "즉시",
    "at first": "처음에", "at last": "마침내",
    "in fact": "사실", "in particular": "특히",
    "on purpose": "일부러", "by chance": "우연히",
    "for example": "예를 들어", "such as": "예를 들어",
    "instead of": "대신에", "in addition": "게다가",
    "in spite of": "에도 불구하고", "according to": "에 따르면",
    "as well": "또한", "as a result": "결과적으로",
    "at the same time": "동시에", "from now on": "앞으로",
    "so far": "지금까지", "after all": "결국",
}

# ── 품사 → 한국어 접미사 규칙 ──────────────────────────────
def apply_pos_suffix(base_ko: str, pos_tags: list[str]) -> str:
    """품사 태그에 따라 한국어 표현 조정"""
    pos_str = " ".join(pos_tags).lower()

    # 동사: "to + 원형" 패턴이면 이미 ~하다 포함
    if any(p in pos_str for p in ["verb", "intransitive", "transitive", "godan", "ichidan"]):
        # 이미 "하다"로 끝나면 그대로
        if base_ko.endswith(("하다", "이다", "되다", "나다", "받다", "치다",
                              "지다", "오다", "가다", "다", "다")):
            return base_ko
        # "~하다" 붙이기
        if not base_ko.endswith("다"):
            return base_ko + "하다"
    return base_ko


# ── 영어 글로스를 한국어로 변환 ───────────────────────────
def gloss_to_korean(gloss_list, pos_tags):
    for gloss in gloss_list:
        g = gloss.strip().lower()
        # 정확한 매핑
        if g in EN_KO:
            return EN_KO[g]
        # "to + ..." 형식
        if g.startswith("to "):
            key = g  # 전체 "to move" 등
            if key in EN_KO:
                return EN_KO[key]
    return None


# ── JLPT 특화 수동 사전 (jamdict에서 잘 안 잡히거나 뜻이 불명확한 단어) ──
MANUAL: dict[str, str] = {
    "か月·箇月": "개월",
    "さっさと": "빨리빨리",
    "しいんと": "쥐 죽은 듯이",
    "ずっと": "쭉",
    "やっぱり": "역시",
    "やはり": "역시",
    "なかなか": "좀처럼",
    "せっかく": "모처럼",
    "だんだん": "점점",
    "どんどん": "점점",
    "ちゃんと": "제대로",
    "きちんと": "바르게",
    "はっきり": "확실히",
    "もちろん": "물론",
    "たとえば": "예를 들어",
    "ところで": "그런데",
    "それほど": "그다지",
    "かなり": "꽤",
    "まず": "우선",
    "しかも": "게다가",
    "さらに": "더욱이",
    "したがって": "따라서",
    "すなわち": "즉",
    "つまり": "즉",
    "ただし": "단",
    "ところが": "그런데",
    "そのため": "그래서",
    "そこで": "그래서",
    "それでも": "그래도",
    "それなのに": "그런데도",
    "ところに": "그런데",
    "いわゆる": "소위",
    "むしろ": "오히려",
    "かえって": "오히려",
    "わざと": "일부러",
    "わざわざ": "일부러",
    "まさか": "설마",
    "もしかして": "혹시",
    "もしかしたら": "혹시",
    "たぶん": "아마",
    "おそらく": "아마도",
    "きっと": "틀림없이",
    "ぜひ": "꼭",
    "なんと": "무려",
    "いったい": "도대체",
    "けっして": "절대로",
    "必ずしも": "반드시",
    "めったに": "좀처럼",
    "しばしば": "자주",
    "たびたび": "자주",
    "いつも": "항상",
    "つねに": "항상",
    "常に": "항상",
    "あまり": "그다지",
    "ほとんど": "거의",
    "まったく": "전혀",
    "すこしも": "조금도",
    "ちっとも": "조금도",
    "ずいぶん": "꽤",
    "非常に": "매우",
    "たいへん": "매우",
    "ひどく": "심하게",
    "すごく": "엄청",
    "とても": "매우",
    "本当に": "정말로",
    "確かに": "확실히",
    "はたして": "과연",
    "やがて": "이윽고",
    "ついに": "마침내",
    "とうとう": "드디어",
    "いよいよ": "드디어",
    "そのうち": "머지않아",
    "まもなく": "곧",
    "すぐに": "즉시",
    "急に": "갑자기",
    "突然": "갑자기",
    "初めて": "처음으로",
    "あらかじめ": "미리",
    "あらためて": "다시",
    "ふたたび": "다시",
    "引き続き": "계속해서",
    "ますます": "점점 더",
    "次第に": "점차",
    "徐々に": "서서히",
    "少しずつ": "조금씩",
    "一気に": "단숨에",
    "一度に": "한꺼번에",
    "一緒に": "함께",
    "互いに": "서로",
    "お互いに": "서로",
    "自ら": "스스로",
    "自分で": "스스로",
}


# ══════════════════════════════════════════════════════════
# 메인 변환 함수
# ══════════════════════════════════════════════════════════
def translate_word(reading, kanji):
    """jamdict + 변환 테이블로 한국어 뜻 반환. 실패 시 '-'"""

    # 1. 수동 사전 우선
    if kanji in MANUAL:
        return MANUAL[kanji]
    if reading in MANUAL:
        return MANUAL[reading]

    # 2. jamdict lookup (한자 → 읽기 순서)
    result = jmd.lookup(kanji)
    if not result.entries:
        result = jmd.lookup(reading)
    if not result.entries:
        return "-"

    entry = result.entries[0]

    # 3. 각 sense에서 한국어 매핑 시도
    for sense in entry.senses:
        pos_tags = [str(p) for p in sense.pos]
        gloss_strs = [str(g) for g in sense.gloss]

        ko = gloss_to_korean(gloss_strs, pos_tags)
        if ko:
            return ko

    # 4. 매핑 실패 시: 첫 번째 영어 글로스를 가공
    first_sense = entry.senses[0]
    first_gloss = str(first_sense.gloss[0]).strip() if first_sense.gloss else ""
    pos_tags = [str(p) for p in first_sense.pos]

    # "to ~" 패턴이면 영어 원형으로 재시도
    if first_gloss.startswith("to "):
        verb = first_gloss[3:].split("/")[0].strip()
        if verb in EN_KO:
            return EN_KO[verb]

    # 영어 단어 그대로 있으면 단순 조합 시도
    g_lower = first_gloss.lower().split("/")[0].strip()
    if g_lower in EN_KO:
        return EN_KO[g_lower]

    # 마지막: 영어 글로스 그대로 반환 (이후 수동 보완 가능)
    return first_gloss if first_gloss else "-"


# ══════════════════════════════════════════════════════════
# 단어 수집
# ══════════════════════════════════════════════════════════
def load_words():
    words = []
    seen = set()
    for level in ["N5", "N4", "N3", "N2", "N1"]:
        path = os.path.join(DATA_DIR, f"{level}_words_naver.txt")
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) >= 3 and parts[1] not in seen:
                    seen.add(parts[1])
                    words.append((parts[0], parts[1], parts[2]))
    return words


# ══════════════════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════════════════
def main():
    print("단어 파일 로드 중...")
    words = load_words()
    print(f"  총 {len(words)}개 단어 (kanji 중복 제거 후)")

    # 기존 JSON 로드
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, encoding="utf-8") as f:
            korean_dict = json.load(f)
        print(f"  기존 번역 로드: {len(korean_dict)}개")
    else:
        korean_dict = {}

    untranslated = [(r, k, l) for r, k, l in words if k not in korean_dict]
    print(f"  미번역: {len(untranslated)}개\n")

    translated_count = 0
    failed_count = 0
    SAVE_INTERVAL = 500

    for i, (reading, kanji, level) in enumerate(untranslated, 1):
        ko = translate_word(reading, kanji)
        if ko and ko != "-":
            korean_dict[kanji] = ko
            translated_count += 1
        else:
            korean_dict[kanji] = "-"
            failed_count += 1

        # 진행 출력 (100개마다)
        if i % 100 == 0:
            print(f"  [{i}/{len(untranslated)}] 처리 중... ({len(korean_dict)}/{len(words)} 완료)")

        # 중간 저장 (500개마다)
        if i % SAVE_INTERVAL == 0:
            with open(OUT_FILE, "w", encoding="utf-8") as f:
                json.dump(korean_dict, f, ensure_ascii=False, indent=2)

    # 최종 저장
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(korean_dict, f, ensure_ascii=False, indent=2)

    # 통계
    total = len(words)
    final_translated = sum(1 for v in korean_dict.values() if v != "-")
    final_failed = sum(1 for v in korean_dict.values() if v == "-")

    print("\n" + "━" * 45)
    print(f"번역 완료:         {final_translated}개")
    print(f"번역 실패/건너뜀:  {final_failed}개")
    print(f"저장 경로:         {OUT_FILE}")
    print("━" * 45)

    # 샘플 출력
    sample_keys = list(korean_dict.keys())[:10]
    print("\n[샘플 결과]")
    for k in sample_keys:
        print(f"  {k:10s} → {korean_dict[k]}")

    if final_translated >= 7000:
        print("\nSTEP 2 완료")
    else:
        print(f"\n⚠ 번역 완료 수({final_translated})가 7,000개 미만. 수동 보완 필요.")


if __name__ == "__main__":
    main()
