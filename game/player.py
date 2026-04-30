# 로스터 조작 파일
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import List, Optional
import uuid

from assets.constants import (
    POS_BATTERS, POS_PITCHERS, POS_ALL,
    ROSTER_BENCH_BAT,
    ROSTER_SP, ROSTER_RP, ROSTER_CP,
)


def new_id() -> str:
    return uuid.uuid4().hex[:8]


@dataclass
class Player:
    name: str
    position: str         # C/1B/.../CP
    power: int = 60       # 파워
    accuracy: int = 60    # 정확
    discipline: int = 60  # 선구
    speed: int = 60       # 주루
    defense: int = 60     # 수비
    tier: str = "B"       # C/B/A/S
    pid: str = field(default_factory=new_id)

    # ─── 유틸 ───
    @property
    def is_pitcher(self) -> bool:
        return self.position in POS_PITCHERS

    @property
    def overall(self) -> int:
        if self.is_pitcher:
            # 투수: 변화(power)*1.1 + 구위(accuracy)*1.2 + 제구(discipline)*0.9 + 체력(speed)*0.4 + 수비*0.4
            return round((self.power*1.1 + self.accuracy*1.2
                          + self.discipline*0.9 + self.speed*0.4
                          + self.defense*0.4) / 4)
        return round((self.power + self.accuracy + self.discipline
                      + self.speed + self.defense) / 5)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Player":
        allowed = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**allowed)


@dataclass
class Roster:
    team_name: str = "My Team"
    gold: int = 500

    # 주전 타순 9명 (position-locked: idx는 타순 1~9)
    lineup: List[Optional[Player]] = field(default_factory=lambda: [None]*9)
    # 후보 타자 최대 5명
    bench: List[Player] = field(default_factory=list)
    # 선발 5명
    sp: List[Player] = field(default_factory=list)
    # 중간계투 6명
    rp: List[Player] = field(default_factory=list)
    # 마무리 1명
    cp: List[Player] = field(default_factory=list)
    # 획득했지만 엔트리에 미배정된 선수 (창고)
    storage: List[Player] = field(default_factory=list)

    # ── 파생 ──────────────────────────────────────
    def all_players(self) -> List[Player]:
        out: List[Player] = []
        out += [p for p in self.lineup if p]
        out += self.bench + self.sp + self.rp + self.cp + self.storage
        return out

    def active_roster(self) -> List[Player]:
        """26인 엔트리"""
        return [p for p in self.lineup if p] + self.bench + self.sp + self.rp + self.cp

    # ── 검증 ──────────────────────────────────────
    def roster_status(self) -> dict:
        """각 포지션/역할 슬롯 채움 현황"""
        lineup_positions = [p.position for p in self.lineup if p]
        return {
            "lineup_filled": sum(1 for p in self.lineup if p),
            "lineup_need":   9,
            "lineup_positions": lineup_positions,
            "dup_positions": [pos for pos in POS_BATTERS
                              if lineup_positions.count(pos) > 1],
            "missing_positions": [pos for pos in POS_BATTERS
                                  if pos not in lineup_positions],
            "bench": len(self.bench), "bench_max": ROSTER_BENCH_BAT,
            "sp": len(self.sp), "sp_max": ROSTER_SP,
            "rp": len(self.rp), "rp_max": ROSTER_RP,
            "cp": len(self.cp), "cp_max": ROSTER_CP,
        }

    def is_valid(self) -> bool:
        s = self.roster_status()
        return (s["lineup_filled"] == 9
                and not s["dup_positions"]
                and s["sp"] >= 1 and s["cp"] >= 1)

    # ── 엔트리 조작 ───────────────────────────────
    def remove_player(self, pid: str) -> Optional[Player]:
        """pid 로 선수 찾아 모든 위치에서 제거 후 반환"""
        for i, pl in enumerate(self.lineup):
            if pl and pl.pid == pid:
                self.lineup[i] = None
                return pl
        for lst in (self.bench, self.sp, self.rp, self.cp, self.storage):
            for i, pl in enumerate(lst):
                if pl.pid == pid:
                    return lst.pop(i)
        return None

    def find(self, pid: str) -> Optional[Player]:
        for p in self.all_players():
            if p.pid == pid:
                return p
        return None

    def location_of(self, pid: str) -> Optional[str]:
        for i, p in enumerate(self.lineup):
            if p and p.pid == pid:
                return f"lineup:{i}"
        for name, lst in (("bench", self.bench), ("sp", self.sp),
                          ("rp", self.rp), ("cp", self.cp),
                          ("storage", self.storage)):
            for i, p in enumerate(lst):
                if p.pid == pid:
                    return f"{name}:{i}"
        return None

    def swap_lineup(self, i: int, j: int):
        self.lineup[i], self.lineup[j] = self.lineup[j], self.lineup[i]

    # ── 직렬화 ────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "team_name": self.team_name,
            "gold": self.gold,
            "lineup":  [p.to_dict() if p else None for p in self.lineup],
            "bench":   [p.to_dict() for p in self.bench],
            "sp":      [p.to_dict() for p in self.sp],
            "rp":      [p.to_dict() for p in self.rp],
            "cp":      [p.to_dict() for p in self.cp],
            "storage": [p.to_dict() for p in self.storage],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Roster":
        r = cls(team_name=d.get("team_name", "My Team"),
                gold=d.get("gold", 0))
        r.lineup  = [Player.from_dict(p) if p else None
                     for p in d.get("lineup", [None]*9)]
        while len(r.lineup) < 9:
            r.lineup.append(None)
        r.bench   = [Player.from_dict(p) for p in d.get("bench", [])]
        r.sp      = [Player.from_dict(p) for p in d.get("sp", [])]
        r.rp      = [Player.from_dict(p) for p in d.get("rp", [])]
        r.cp      = [Player.from_dict(p) for p in d.get("cp", [])]
        r.storage = [Player.from_dict(p) for p in d.get("storage", [])]
        return r


@dataclass
class CPUTeam:
    name: str
    difficulty: int = 1                  # 1(쉬움) ~ 5(매우 어려움)
    color: tuple = (200, 80, 80)
    roster: Optional[Roster] = None      # 26인 엔트리

    def to_dict(self) -> dict:
        d = {"name": self.name,
             "difficulty": self.difficulty,
             "color": self.color}
        if self.roster is not None:
            d["roster"] = self.roster.to_dict()
        return d


# ────────────────────────────────────────────────
# 포지션별 능력치 라벨
# 내부 필드는 power/accuracy/discipline/speed/defense 로 통일,
# UI 표시만 포지션에 따라 다르게.
# ────────────────────────────────────────────────
BATTER_STAT_LABELS  = ("파워", "정확", "선구", "주루", "수비")
PITCHER_STAT_LABELS = ("변화", "구위", "제구", "체력", "수비")

def stat_labels(player: "Player"):
    return PITCHER_STAT_LABELS if player.is_pitcher else BATTER_STAT_LABELS

def stat_values(player: "Player"):
    return (player.power, player.accuracy, player.discipline,
            player.speed, player.defense)

def stat_short(player: "Player") -> str:
    """예) '파70 정65 선60 주58 수62' (타자) / '변70 구68 제62 체60 수55' (투수)"""
    labels = stat_labels(player)
    values = stat_values(player)
    return " ".join(f"{l[0]}{v}" for l, v in zip(labels, values))
