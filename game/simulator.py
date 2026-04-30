"""
simulator.py - 야구 게임 시뮬레이션 (9이닝)

내부 스탯 매핑:
  타자: power(파워) / accuracy(정확) / discipline(선구) / speed(주루) / defense(수비)
  투수: power(변화) / accuracy(구위) / discipline(제구) / speed(체력) / defense(수비)
"""
import random
from dataclasses import dataclass, field
from typing import List, Optional

from assets.constants import (
    INNINGS, EXTRA_INNINGS_MAX,
    BASE_K_RATE, BASE_BB_RATE, BASE_HIT_RATE,
)
from .player import Player, Roster, CPUTeam


# ── 결과 데이터 ─────────────────────────────────────────
@dataclass
class PlayEvent:
    inning: int
    top: bool          # True = 플레이어 팀 공격
    batter: str
    pitcher: str
    result: str        # K / BB / 1B / 2B / 3B / HR / OUT
    text: str
    runs: int = 0
    outs_after: int = 0

    def to_dict(self):
        return self.__dict__


@dataclass
class GameResult:
    player_team: str
    cpu_team: str
    innings_played: int = 0
    player_runs_by_inn: List[int] = field(default_factory=list)
    cpu_runs_by_inn:    List[int] = field(default_factory=list)
    player_hits: int = 0
    cpu_hits: int = 0
    events: List[PlayEvent] = field(default_factory=list)

    @property
    def player_score(self): return sum(self.player_runs_by_inn)
    @property
    def cpu_score(self):    return sum(self.cpu_runs_by_inn)
    @property
    def player_wins(self):  return self.player_score > self.cpu_score
    @property
    def tied(self):         return self.player_score == self.cpu_score


# 헬퍼 함수 
def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


# 타석 별 결과 계산 
def _simulate_pa(batter: Player, pitcher: Player, defense: float) -> str:
    # 삼진 확률
    k_rate = _clamp(
        BASE_K_RATE + (pitcher.power + pitcher.accuracy - batter.discipline - batter.accuracy) * 0.0016,
        0.06, 0.42
    )
    # 볼넷 확률
    bb_rate = _clamp(
        BASE_BB_RATE + (batter.discipline - pitcher.discipline) * 0.0028,
        0.02, 0.22
    )
    # 안타 확률 (수비력도 영향)
    hit_rate = _clamp(
        BASE_HIT_RATE + (batter.accuracy - pitcher.accuracy) * 0.003 - (defense - 60) * 0.0015,
        0.10, 0.50
    )

    r = random.random()
    if r < k_rate:
        return "K"
    r -= k_rate
    if r < bb_rate:
        return "BB"
    r -= bb_rate
    if r < hit_rate:
        # 장타 분배: 타자 파워(power) vs 투수 구위(accuracy)
        gap = batter.power - pitcher.accuracy
        hr_share     = _clamp(0.09 + gap * 0.0035, 0.02, 0.28)
        triple_share = 0.03 + _clamp(batter.speed - 60, 0, 30) * 0.0015
        double_share = _clamp(0.20 + gap * 0.0015, 0.12, 0.30)
        h = random.random()
        if h < hr_share:                          return "HR"
        if h < hr_share + triple_share:           return "3B"
        if h < hr_share + triple_share + double_share: return "2B"
        return "1B"
    return "OUT"


def _advance(bases, batter, result):
    """주자 진루 처리. bases = [1루, 2루, 3루]"""
    b1, b2, b3 = bases
    runs = 0

    if result == "HR":
        runs = sum(1 for b in bases if b) + 1
        return [None, None, None], runs
    if result == "3B":
        runs = sum(1 for b in bases if b)
        return [None, None, batter], runs
    if result == "2B":
        if b3: runs += 1
        if b2: runs += 1
        return [None, batter, b1], runs
    if result == "1B":
        if b3: runs += 1
        if b2: runs += 1
        return [batter, b1, None], runs
    if result == "BB":
        nb = [None, None, None]
        nb[0] = batter
        if b1 is None:
            nb[1], nb[2] = b2, b3
        else:
            nb[1] = b1
            if b2 is None:
                nb[2] = b3
            else:
                nb[2] = b2
                if b3:
                    runs += 1
        return nb, runs
    return bases, 0


# 투수 교체 조건 판단
def _is_tired(pitcher: Player, bf: int, runs: int, inning: int) -> bool:
    if pitcher is None:
        return False
    if pitcher.position == "SP":
        limit = 22 + (pitcher.speed - 60) // 4   # 체력(speed)에 따라 22~30 타자
        return bf >= limit or (runs >= 4 and inning >= 5) or inning >= 7
    if pitcher.position == "RP":
        limit = max(3, 5 + (pitcher.speed - 60) // 10)
        return bf >= limit or runs >= 2
    if pitcher.position == "CP":
        return bf >= 5 or runs >= 2
    return False


# 다음 투수 결정
def _next_pitcher(sp, rp, cp, game_count, inning, leading) -> Optional[Player]:
    if inning >= 9 and leading and cp:
        return cp[0]
    if rp:
        return rp[(game_count + inning) % len(rp)]
    pool = cp + sp
    return pool[0] if pool else None


def _fill_lineup(roster: Roster) -> List[Player]:
    lu = [p for p in roster.lineup if p]
    for p in roster.bench:
        if len(lu) >= 9:
            break
        lu.append(p)
    if not lu:
        lu = [Player(name=f"선수{i+1}", position="DH",
                     power=40, accuracy=40, discipline=40, speed=40, defense=40, tier="C")
              for i in range(9)]
    return lu


def _team_defense(lineup: List[Player]) -> float:
    return sum(p.defense for p in lineup) / len(lineup) if lineup else 60.0


# 시뮬레이션 함수
def simulate_game(roster: Roster, cpu: CPUTeam,
                  game_count: int = 0,
                  seed: Optional[int] = None) -> GameResult:
    if seed is not None:
        random.seed(seed)
    if cpu.roster is None:
        raise ValueError(f"CPU 팀 '{cpu.name}' 로스터가 없습니다.")

    result = GameResult(player_team=roster.team_name, cpu_team=cpu.name)

    # 타순 구성
    p_lineup = _fill_lineup(roster)
    c_lineup = _fill_lineup(cpu.roster)

    # 투수 풀
    p_sp, p_rp, p_cp = list(roster.sp), list(roster.rp), list(roster.cp)
    c_sp, c_rp, c_cp = list(cpu.roster.sp), list(cpu.roster.rp), list(cpu.roster.cp)

    # 선발 투수 결정 (game_count로 로테이션)
    def starting(sp, rp, cp):
        if sp: return sp[game_count % len(sp)]
        if rp: return rp[0]
        if cp: return cp[0]
        return None

    p_pitcher = starting(p_sp, p_rp, p_cp)   # 우리 팀 투수
    c_pitcher = starting(c_sp, c_rp, c_cp)   # CPU 팀 투수
    if not p_pitcher or not c_pitcher:
        raise ValueError("투수가 최소 1명 필요합니다.")

    # 팀 평균 수비력
    p_def = _team_defense(p_lineup)
    c_def = _team_defense(c_lineup)

    # 타순 인덱스
    p_bat = 0
    c_bat = 0

    # 투수 피로도 추적용 변수
    p_bf, p_ra = 0, 0   # 우리 팀 투수: 상대한 타자 수, 실점
    c_bf, c_ra = 0, 0   # CPU 투수: 상대한 타자 수, 실점

    HIT_TEXT = {"1B": "1루타", "2B": "2루타", "3B": "3루타", "HR": "홈런", "BB": "볼넷"}

    for inning in range(1, EXTRA_INNINGS_MAX + 1):

        # 초 공격 (플레이어 팀 공격)
        outs = 0
        bases = [None, None, None]
        inn_runs = 0

        while outs < 3:
            batter = p_lineup[p_bat]
            p_bat = (p_bat + 1) % 9

            pa = _simulate_pa(batter, c_pitcher, c_def)
            run_delta = 0

            if pa in ("K", "OUT"):
                outs += 1
                # 희생플라이: 3루 주자 있고 2아웃 전이면 25% 확률로 득점
                if pa == "OUT" and bases[2] and outs <= 2 and random.random() < 0.25:
                    run_delta = 1
                    bases[2] = None
                    text = f"{batter.name} 희생플라이 (1득점)"
                else:
                    text = f"{batter.name} {'삼진' if pa == 'K' else '범타 아웃'}"
            elif pa == "BB":
                bases, run_delta = _advance(bases, batter, pa)
                text = f"{batter.name} 볼넷"
            else:
                bases, run_delta = _advance(bases, batter, pa)
                text = f"{batter.name} {HIT_TEXT[pa]}"
                if run_delta:
                    text += f" ({run_delta}득점)"
                result.player_hits += 1

            inn_runs += run_delta
            c_bf += 1
            c_ra += run_delta

            result.events.append(PlayEvent(
                inning=inning, top=True,
                batter=batter.name, pitcher=c_pitcher.name,
                result=pa, text=text,
                runs=run_delta, outs_after=min(outs, 3),
            ))

            # CPU 투수 교체 
            if _is_tired(c_pitcher, c_bf, c_ra, inning):
                leading = result.cpu_score > (result.player_score + inn_runs)
                new_p = _next_pitcher(c_sp, c_rp, c_cp, game_count, inning + 1, leading)
                if new_p and new_p.pid != c_pitcher.pid:
                    c_pitcher = new_p
                    c_bf, c_ra = 0, 0

        result.player_runs_by_inn.append(inn_runs)

        # 9회 이후 CPU가 리드 중이면 종료 (CPU가 말이므로)
        if inning >= INNINGS and result.cpu_score > result.player_score:
            result.cpu_runs_by_inn.append(0)
            result.innings_played = inning
            break

        # 말 공격 (CPU 공격)
        outs = 0
        bases = [None, None, None]
        inn_runs = 0

        while outs < 3:
            batter = c_lineup[c_bat]
            c_bat = (c_bat + 1) % 9

            pa = _simulate_pa(batter, p_pitcher, p_def)
            run_delta = 0

            if pa in ("K", "OUT"):
                outs += 1
                if pa == "OUT" and bases[2] and outs <= 2 and random.random() < 0.25:
                    run_delta = 1
                    bases[2] = None
                    text = f"{batter.name} 희생플라이 (1득점)"
                else:
                    text = f"{batter.name} {'삼진' if pa == 'K' else '범타 아웃'}"
            elif pa == "BB":
                bases, run_delta = _advance(bases, batter, pa)
                text = f"{batter.name} 볼넷"
            else:
                bases, run_delta = _advance(bases, batter, pa)
                text = f"{batter.name} {HIT_TEXT[pa]}"
                if run_delta:
                    text += f" ({run_delta}득점)"
                result.cpu_hits += 1

            inn_runs += run_delta
            p_bf += 1
            p_ra += run_delta

            result.events.append(PlayEvent(
                inning=inning, top=False,
                batter=batter.name, pitcher=p_pitcher.name,
                result=pa, text=text,
                runs=run_delta, outs_after=min(outs, 3),
            ))

            # 우리 팀 투수 교체
            if _is_tired(p_pitcher, p_bf, p_ra, inning):
                leading = result.player_score > (result.cpu_score + inn_runs)
                new_p = _next_pitcher(p_sp, p_rp, p_cp, game_count, inning + 1, leading)
                if new_p and new_p.pid != p_pitcher.pid:
                    p_pitcher = new_p
                    p_bf, p_ra = 0, 0

        result.cpu_runs_by_inn.append(inn_runs)
        result.innings_played = inning

        if inning >= INNINGS and result.player_score != result.cpu_score:
            break

    return result