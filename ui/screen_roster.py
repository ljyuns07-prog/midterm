"""
screen_roster.py - 엔트리 관리 (타순/벤치/투수/창고)
"""
import pygame
from typing import List, Optional

from assets.constants import (
    SCREEN_W, SCREEN_H, DARK, PANEL, ACCENT, GREEN, RED, YELLOW, WHITE,
    LIGHT, GRAY, GOLD, POS_BATTERS, POS_PITCHERS, DIAMOND,
    ROSTER_BENCH_BAT, ROSTER_SP, ROSTER_RP, ROSTER_CP,
)
from .ui_utils import Button, draw_text, draw_panel
from game.player import Player, Roster, stat_short


TIER_COLOR = {
    "S": (240, 200, 60),
    "A": (180, 100, 220),
    "B": (90, 160, 240),
    "C": (150, 150, 150),
}


def _player_line(p: Player) -> str:
    return f"[{p.tier}] {p.name:<10} {stat_short(p)}  OVR {p.overall:>2}"


class RosterScreen:
    TABS = [("타순", "lineup"), ("벤치", "bench"),
            ("투수", "pitch"), ("창고", "storage")]

    def __init__(self, app):
        self.app = app
        self.roster: Roster = app.roster

        # 현재 탭
        self.tab = "lineup"

        # 선택된 선수 (pid)
        self.selected_pid: Optional[str] = None
        # 교체 모달 (후보 리스트 팝업)
        self.swap_candidates: Optional[List[Player]] = None
        self.swap_source_loc: Optional[str] = None

        # 메시지
        self.message = ""
        self.message_timer = 0

        self._build_static_buttons()

    # ── 정적 버튼 (탭, 뒤로) ────────────────────────
    def _build_static_buttons(self):
        self.back_btn = Button((30, SCREEN_H - 60, 140, 46),
                               "◀ 메인", lambda: self.app.goto("main"),
                               color=(120, 120, 130))

        # 탭 버튼 (상단)
        tab_w, tab_h = 120, 44
        start_x = 30
        y = 20
        self.tab_buttons = []
        for i, (label, key) in enumerate(self.TABS):
            def make_cb(k=key):
                def cb():
                    self.tab = k
                    self.selected_pid = None
                return cb
            btn = Button((start_x + i*(tab_w + 10), y, tab_w, tab_h),
                         label, make_cb())
            self.tab_buttons.append((btn, key))

    # ── 메시지 ────────────────────────────────────
    def notify(self, msg: str, frames: int = 150):
        self.message = msg
        self.message_timer = frames

    # ── 이벤트 & 그리기 ───────────────────────────
    def handle(self, events):
        screen = self.app.screen
        screen.fill(DARK)

        # 모달이 떠 있으면 모달 이벤트만
        if self.swap_candidates is not None:
            self._draw_swap_modal(screen, events)
            pygame.display.flip = pygame.display.flip  # no-op
            return

        # 이벤트 → 버튼 전파
        for ev in events:
            self.back_btn.handle(ev)
            for btn, _ in self.tab_buttons:
                btn.handle(ev)
            self._handle_action_buttons(ev)
            # 리스트 슬롯 클릭
            self._handle_list_click(ev)

        # 그리기
        self._draw_header(screen)
        for btn, key in self.tab_buttons:
            # 현재 탭은 하이라이트
            original = btn.color
            if key == self.tab:
                btn.color = GREEN
                btn.hover_color = tuple(min(255, c + 20) for c in GREEN)
            else:
                btn.color = (80, 85, 105)
                btn.hover_color = (100, 110, 130)
            btn.draw(screen)
            btn.color = original

        self.back_btn.draw(screen)

        # 탭 컨텐츠
        content_rect = pygame.Rect(30, 80, SCREEN_W - 60, SCREEN_H - 200)
        draw_panel(screen, content_rect, color=PANEL)
        if self.tab == "lineup":
            self._draw_lineup(screen, content_rect)
        elif self.tab == "bench":
            self._draw_bench(screen, content_rect)
        elif self.tab == "pitch":
            self._draw_pitchers(screen, content_rect)
        elif self.tab == "storage":
            self._draw_storage(screen, content_rect)

        # 하단 액션 버튼
        self._draw_action_buttons(screen)

        # 메시지
        if self.message_timer > 0:
            self.message_timer -= 1
            draw_text(screen, self.message,
                      (SCREEN_W // 2, SCREEN_H - 80),
                      size=18, color=YELLOW, center=True, bold=True)

    # ── 헤더 ──────────────────────────────────────
    def _draw_header(self, screen):
        r = self.roster
        s = r.roster_status()

        # 팀 오버롤 계산
        players = r.active_roster()
        team_ovr = round(sum(p.overall for p in players) / len(players)) if players else 0

        info = (f"{r.team_name}   "
                f"타순 {s['lineup_filled']}/9   "
                f"벤치 {s['bench']}/{s['bench_max']}   "
                f"SP {s['sp']}/{s['sp_max']}   "
                f"RP {s['rp']}/{s['rp_max']}   "
                f"CP {s['cp']}/{s['cp_max']}   "
                f"창고 {len(r.storage)}")
        draw_text(screen, info, (SCREEN_W - 30, 35),
                  size=16, color=LIGHT, right=True)
        draw_text(screen, f"OVR {team_ovr}   {r.gold} G",
                  (SCREEN_W - 30, 55),
                  size=22, color=GOLD, bold=True, right=True)

        if s["dup_positions"]:
            draw_text(screen,
                      f"⚠ 포지션 중복: {', '.join(s['dup_positions'])}",
                      (30, SCREEN_H - 90), size=16, color=RED)
        if s["missing_positions"]:
            draw_text(screen,
                      f"⚠ 빈 포지션: {', '.join(s['missing_positions'])}",
                      (30, SCREEN_H - 110), size=16, color=RED)

    # ── 슬롯 레이아웃 정보 저장 (클릭 판정용) ─────
    def _reset_slots(self):
        self._slot_rects = []   # (rect, loc_key)

    def _register_slot(self, rect, loc_key):
        self._slot_rects.append((rect, loc_key))

    # ── 타순 탭 ───────────────────────────────────
    def _draw_lineup(self, screen, rect):
        self._reset_slots()
        draw_text(screen, "주전 타순 (순서대로 1번 ~ 9번)",
                  (rect.x + 20, rect.y + 15),
                  size=22, color=WHITE, bold=True)

        row_h = 48
        top_y = rect.y + 55
        for i in range(9):
            p = self.roster.lineup[i]
            row_rect = pygame.Rect(rect.x + 20, top_y + i*row_h,
                                   rect.w - 40, row_h - 6)
            is_sel = p is not None and p.pid == self.selected_pid
            color = ACCENT if is_sel else (70, 74, 92)
            pygame.draw.rect(screen, color, row_rect, border_radius=5)

            draw_text(screen, f"{i+1}번",
                      (row_rect.x + 15, row_rect.y + 12),
                      size=22, color=WHITE, bold=True)
            if p:
                tc = TIER_COLOR.get(p.tier, WHITE)
                draw_text(screen, f"[{p.position}]",
                          (row_rect.x + 75, row_rect.y + 14),
                          size=20, color=DIAMOND, bold=True)
                draw_text(screen, f"{p.name}",
                          (row_rect.x + 140, row_rect.y + 14),
                          size=20, color=WHITE)
                draw_text(screen,
                          f"{stat_short(p)}  OVR {p.overall}",
                          (row_rect.x + 280, row_rect.y + 14),
                          size=18, color=LIGHT)
                draw_text(screen, p.tier,
                          (row_rect.right - 30, row_rect.y + 14),
                          size=22, color=tc, bold=True, right=True)
                self._register_slot(row_rect, f"lineup:{i}")
            else:
                draw_text(screen, "(비어있음)",
                          (row_rect.x + 140, row_rect.y + 14),
                          size=18, color=GRAY)

    # ── 벤치 탭 ───────────────────────────────────
    def _draw_bench(self, screen, rect):
        self._reset_slots()
        draw_text(screen, f"후보 타자 ({len(self.roster.bench)}/{ROSTER_BENCH_BAT})",
                  (rect.x + 20, rect.y + 15),
                  size=22, color=WHITE, bold=True)
        self._draw_player_list(screen, rect, self.roster.bench, "bench", 55)

    # ── 투수 탭 ───────────────────────────────────
    def _draw_pitchers(self, screen, rect):
        self._reset_slots()
        section_h = (rect.h - 60) // 3
        y = rect.y + 10

        # SP
        draw_text(screen, f"선발투수 SP ({len(self.roster.sp)}/{ROSTER_SP})",
                  (rect.x + 20, y + 8), size=20, color=WHITE, bold=True)
        self._draw_pitcher_row(screen, rect, self.roster.sp, "sp",
                               y_start=y + 35, max_slots=ROSTER_SP)
        y += section_h

        # RP
        draw_text(screen, f"중간계투 RP ({len(self.roster.rp)}/{ROSTER_RP})",
                  (rect.x + 20, y + 8), size=20, color=WHITE, bold=True)
        self._draw_pitcher_row(screen, rect, self.roster.rp, "rp",
                               y_start=y + 35, max_slots=ROSTER_RP)
        y += section_h

        # CP
        draw_text(screen, f"마무리 CP ({len(self.roster.cp)}/{ROSTER_CP})",
                  (rect.x + 20, y + 8), size=20, color=WHITE, bold=True)
        self._draw_pitcher_row(screen, rect, self.roster.cp, "cp",
                               y_start=y + 35, max_slots=ROSTER_CP)

    def _draw_pitcher_row(self, screen, rect, lst, key, y_start, max_slots):
        cell_w = (rect.w - 40) // max(max_slots, 1)
        cell_h = 80
        for i in range(max_slots):
            cx = rect.x + 20 + i * cell_w
            cr = pygame.Rect(cx + 4, y_start, cell_w - 8, cell_h)
            p = lst[i] if i < len(lst) else None
            is_sel = p is not None and p.pid == self.selected_pid
            c = ACCENT if is_sel else (70, 74, 92)
            pygame.draw.rect(screen, c, cr, border_radius=5)
            if p:
                tc = TIER_COLOR.get(p.tier, WHITE)
                draw_text(screen, f"[{p.tier}] {p.name}",
                          (cr.x + 10, cr.y + 8),
                          size=16, color=tc, bold=True)
                # 투수 라벨: 변/구/제/체/수
                draw_text(screen,
                          f"변{p.power} 구{p.accuracy} 제{p.discipline}",
                          (cr.x + 10, cr.y + 30),
                          size=14, color=LIGHT)
                draw_text(screen,
                          f"체{p.speed} 수{p.defense}  OVR {p.overall}",
                          (cr.x + 10, cr.y + 50),
                          size=14, color=LIGHT)
                self._register_slot(cr, f"{key}:{i}")
            else:
                draw_text(screen, "(빈 슬롯)",
                          (cr.center[0], cr.center[1]),
                          size=14, color=GRAY, center=True)

    # ── 창고 탭 ───────────────────────────────────
    def _draw_storage(self, screen, rect):
        self._reset_slots()
        draw_text(screen, f"창고 (미배정 선수) : {len(self.roster.storage)}명",
                  (rect.x + 20, rect.y + 15),
                  size=22, color=WHITE, bold=True)
        self._draw_player_list(screen, rect, self.roster.storage, "storage", 55)

    def _draw_player_list(self, screen, rect, lst, key, top_offset):
        row_h = 40
        max_rows = (rect.h - top_offset - 10) // row_h
        for i, p in enumerate(lst[:max_rows]):
            row_rect = pygame.Rect(rect.x + 20, rect.y + top_offset + i*row_h,
                                   rect.w - 40, row_h - 4)
            is_sel = p.pid == self.selected_pid
            c = ACCENT if is_sel else (70, 74, 92)
            pygame.draw.rect(screen, c, row_rect, border_radius=5)
            tc = TIER_COLOR.get(p.tier, WHITE)
            draw_text(screen, f"[{p.position}]",
                      (row_rect.x + 15, row_rect.y + 10),
                      size=18, color=DIAMOND, bold=True)
            draw_text(screen, p.name,
                      (row_rect.x + 85, row_rect.y + 10),
                      size=18, color=WHITE)
            draw_text(screen,
                      f"{stat_short(p)}  OVR {p.overall}",
                      (row_rect.x + 230, row_rect.y + 10),
                      size=16, color=LIGHT)
            draw_text(screen, p.tier,
                      (row_rect.right - 20, row_rect.y + 10),
                      size=18, color=tc, bold=True, right=True)
            self._register_slot(row_rect, f"{key}:{i}")

    # ── 클릭 → 선수 선택 ─────────────────────────
    def _handle_list_click(self, ev):
        if ev.type != pygame.MOUSEBUTTONDOWN or ev.button != 1:
            return
        for rect, loc in getattr(self, "_slot_rects", []):
            if rect.collidepoint(ev.pos):
                # pid 추출
                p = self._player_at_loc(loc)
                if p is not None:
                    self.selected_pid = p.pid if self.selected_pid != p.pid else None
                return

    def _player_at_loc(self, loc: str) -> Optional[Player]:
        kind, idx = loc.split(":")
        idx = int(idx)
        if kind == "lineup":
            return self.roster.lineup[idx]
        return getattr(self.roster, kind)[idx] if idx < len(getattr(self.roster, kind)) else None

    # ── 하단 액션 버튼 ────────────────────────────
    def _draw_action_buttons(self, screen):
        y = SCREEN_H - 60
        # 선택된 선수에 따라 버튼 구성
        self._action_buttons = []
        sel = self.roster.find(self.selected_pid) if self.selected_pid else None
        if sel is None:
            draw_text(screen,
                      "선수를 클릭해 선택하면 이동/교체 버튼이 나타납니다.",
                      (SCREEN_W // 2, y + 22),
                      size=16, color=GRAY, center=True)
            return

        loc = self.roster.location_of(self.selected_pid)
        bw, bh = 150, 46
        x = 200
        gap = 12

        def add_btn(label, fn, color=ACCENT):
            nonlocal x
            b = Button((x, y, bw, bh), label, fn, color=color, font_size=16)
            self._action_buttons.append(b)
            b.draw(screen)
            x += bw + gap

        if loc and loc.startswith("lineup:"):
            idx = int(loc.split(":")[1])
            add_btn("↑ 위로", lambda: self._move_lineup(idx, -1),
                    color=(80, 140, 220))
            add_btn("↓ 아래로", lambda: self._move_lineup(idx, +1),
                    color=(80, 140, 220))
            add_btn("벤치와 교체", lambda: self._open_swap_with("bench", sel),
                    color=(230, 170, 80))
            add_btn("창고로", lambda: self._to_storage(sel), color=RED)
        elif loc and loc.startswith("bench:"):
            add_btn("주전과 교체", lambda: self._open_swap_with("lineup", sel),
                    color=GREEN)
            add_btn("창고로", lambda: self._to_storage(sel), color=RED)
        elif loc and (loc.startswith("sp:") or loc.startswith("rp:")
                      or loc.startswith("cp:")):
            add_btn("창고로", lambda: self._to_storage(sel), color=RED)
        elif loc and loc.startswith("storage:"):
            add_btn("엔트리에 추가", lambda: self._from_storage(sel), color=GREEN)
            add_btn("제외(삭제)", lambda: self._remove_storage(sel), color=(130, 60, 60))

    def _handle_action_buttons(self, ev):
        for b in getattr(self, "_action_buttons", []):
            b.handle(ev)

    # ── 액션 구현 ────────────────────────────────
    def _move_lineup(self, idx: int, delta: int):
        new = idx + delta
        if 0 <= new < 9:
            self.roster.swap_lineup(idx, new)
            self.notify(f"{idx+1}번 ↔ {new+1}번 타순 변경")

    def _open_swap_with(self, target_list: str, sel: Player):
        if target_list == "bench":
            # lineup → bench 같은 포지션 후보
            cands = [p for p in self.roster.bench if p.position == sel.position]
            if not cands:
                self.notify(f"벤치에 {sel.position} 교체 후보가 없습니다.")
                return
        else:
            # bench → lineup 같은 포지션 슬롯
            cands = [p for p in self.roster.lineup
                     if p and p.position == sel.position]
            if not cands:
                self.notify(f"주전에 {sel.position} 선수가 없습니다.")
                return
        self.swap_candidates = cands
        self.swap_source_loc = self.roster.location_of(sel.pid)

    def _do_swap(self, partner: Player):
        sel_loc     = self.swap_source_loc
        partner_loc = self.roster.location_of(partner.pid)
        sel = self.roster.find(self.selected_pid)
        if sel is None or partner is None or sel_loc is None or partner_loc is None:
            self.swap_candidates = None
            return
        # 두 슬롯 교환
        self._set_at_loc(sel_loc, partner)
        self._set_at_loc(partner_loc, sel)
        self.notify(f"{sel.name} ↔ {partner.name} 교체 완료")
        self.swap_candidates = None
        self.swap_source_loc = None

    def _set_at_loc(self, loc: str, player: Optional[Player]):
        kind, idx = loc.split(":")
        idx = int(idx)
        if kind == "lineup":
            self.roster.lineup[idx] = player
        else:
            lst = getattr(self.roster, kind)
            if idx < len(lst):
                if player is None:
                    lst.pop(idx)
                else:
                    lst[idx] = player
            elif player is not None:
                lst.append(player)

    def _to_storage(self, sel: Player):
        loc = self.roster.location_of(sel.pid)
        if not loc:
            return
        p = self.roster.remove_player(sel.pid)
        if p:
            self.roster.storage.append(p)
            self.notify(f"{p.name} → 창고")
            self.selected_pid = None

    def _from_storage(self, sel: Player):
        """창고에서 엔트리로 자동 배치"""
        if sel.position in POS_BATTERS:
            # 같은 포지션 주전이 비었나?
            pos_idx = next((i for i, p in enumerate(self.roster.lineup)
                            if p is None), None)
            lineup_pos = [p.position for p in self.roster.lineup if p]
            if sel.position not in lineup_pos and pos_idx is not None:
                # 주전 비어있는 슬롯에 투입 (처음 빈 슬롯)
                self.roster.storage.remove(sel)
                self.roster.lineup[pos_idx] = sel
                self.notify(f"{sel.name} → 주전({pos_idx+1}번)")
                return
            # 벤치 여유
            if len(self.roster.bench) < ROSTER_BENCH_BAT:
                self.roster.storage.remove(sel)
                self.roster.bench.append(sel)
                self.notify(f"{sel.name} → 벤치")
                return
            self.notify("타자 엔트리에 빈 자리가 없습니다.")
            return
        # 투수
        if sel.position == "SP":
            if len(self.roster.sp) < ROSTER_SP:
                self.roster.storage.remove(sel); self.roster.sp.append(sel)
                self.notify(f"{sel.name} → SP"); return
            self.notify("SP 자리가 가득 찼습니다.")
        elif sel.position == "RP":
            if len(self.roster.rp) < ROSTER_RP:
                self.roster.storage.remove(sel); self.roster.rp.append(sel)
                self.notify(f"{sel.name} → RP"); return
            self.notify("RP 자리가 가득 찼습니다.")
        elif sel.position == "CP":
            if len(self.roster.cp) < ROSTER_CP:
                self.roster.storage.remove(sel); self.roster.cp.append(sel)
                self.notify(f"{sel.name} → CP"); return
            self.notify("CP 자리가 가득 찼습니다.")

    def _remove_storage(self, sel: Player):
        if sel in self.roster.storage:
            self.roster.storage.remove(sel)
            self.notify(f"{sel.name} 제외")
            self.selected_pid = None

    # ── 교체 모달 ────────────────────────────────
    def _draw_swap_modal(self, screen, events):
        # 배경 딤
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # 모달
        mw, mh = 600, 440
        mx, my = (SCREEN_W - mw)//2, (SCREEN_H - mh)//2
        modal = pygame.Rect(mx, my, mw, mh)
        draw_panel(screen, modal, color=PANEL, border=2)
        draw_text(screen, "교체할 선수 선택",
                  (mx + mw//2, my + 25), size=26,
                  color=WHITE, bold=True, center=True)

        # 후보 목록
        row_h = 44
        buttons = []
        for i, p in enumerate(self.swap_candidates):
            rr = pygame.Rect(mx + 20, my + 60 + i*row_h, mw - 40, row_h - 6)
            def make_cb(px=p): return lambda: self._do_swap(px)
            btn = Button(rr, _player_line(p), make_cb(),
                         color=(90, 110, 150), font_size=15)
            buttons.append(btn)

        cancel_btn = Button((mx + mw - 130, my + mh - 60, 110, 44),
                            "취소", self._close_modal, color=(140, 60, 60))

        for ev in events:
            for b in buttons:
                b.handle(ev)
            cancel_btn.handle(ev)
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self._close_modal()

        for b in buttons:
            b.draw(screen)
        cancel_btn.draw(screen)

    def _close_modal(self):
        self.swap_candidates = None
        self.swap_source_loc = None
