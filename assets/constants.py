# 게임 전역 상수

import sys
from pathlib import Path

# ── 기본 ─────────────────────────────────────────────
TITLE      = "SNU Baseball Manager"
SCREEN_W   = 1280
SCREEN_H   = 760
FPS        = 60

# ── 경로 ─────────────────────────────────────────────
# 번들(.app/.exe)로 실행될 때와 일반 실행 모두 대응
if getattr(sys, 'frozen', False):
    # PyInstaller 6.x: 데이터 파일은 _internal/ 폴더 안에 있음
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

# 세이브는 번들 밖 사용자 문서 폴더에 저장 (앱 내부는 읽기 전용일 수 있음)
_SAVE_ROOT = Path.home() / 'Documents' / 'SNU Baseball Manager'

DATA_DIR   = BASE_DIR / "data"
SAVE_DIR   = _SAVE_ROOT / "saves"
SAVE_FILE  = SAVE_DIR / "savegame.json"

# Excel 파일 경로는 data_manager.py 에서 재선언 (순환참조 방지용 동일 상수)
PLAYER_XL_PATH = DATA_DIR / "players.xlsx"
CPU_XL_PATH    = DATA_DIR / "cpu_teams.xlsx"

# ── 색상 ─────────────────────────────────────────────
WHITE   = (245, 245, 245)
BLACK   = (20, 20, 20)
GRAY    = (120, 120, 120)
LIGHT   = (220, 220, 220)
DARK    = (45, 48, 60)
PANEL   = (58, 62, 78)
ACCENT  = (90, 160, 240)
GREEN   = (90, 190, 110)
RED     = (220, 90, 90)
YELLOW  = (240, 200, 80)
GOLD    = (250, 200, 60)
DIAMOND = (140, 110, 220)

# ── 포지션 ───────────────────────────────────────────
POS_BATTERS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]
POS_PITCHERS = ["SP", "RP", "CP"]
POS_ALL = POS_BATTERS + POS_PITCHERS

# 엔트리 구성 (총 26명)
ROSTER_STARTERS_BAT = 9   # 주전 타자
ROSTER_BENCH_BAT    = 5   # 후보 타자
ROSTER_SP           = 5   # 선발투수
ROSTER_RP           = 6   # 중간계투
ROSTER_CP           = 1   # 마무리
ROSTER_SIZE         = (ROSTER_STARTERS_BAT + ROSTER_BENCH_BAT
                       + ROSTER_SP + ROSTER_RP + ROSTER_CP)  # 26


# ── 경제 ─────────────────────────────────────────────
WIN_GOLD_BASE  = 30   # 승리 시 기본 골드
LOSS_GOLD_BASE = 8    # 패배 시 참가비 보상

PACK_CHEAP_PRICE  = 80
PACK_PREMIUM_PRICE = 250
PACK_CHEAP_TIER_WEIGHTS  = {"C": 55, "B": 35, "A": 9,  "S": 1}
PACK_PREMIUM_TIER_WEIGHTS = {"C": 10, "B": 35, "A": 40, "S": 15}


# ── 시뮬 밸런스 ──────────────────────────────────────
INNINGS = 9                # 정규 이닝
EXTRA_INNINGS_MAX = 12     # 무승부 시 최대 연장

# 스탯 → 확률 변환 계수
BASE_K_RATE   = 0.22
BASE_BB_RATE  = 0.085
BASE_HIT_RATE = 0.30
