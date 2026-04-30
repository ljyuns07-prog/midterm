"""
screen_game.py - 경기 진행 (play-by-play)

simulate_game() 이 반환한 이벤트 로그를 시간 순으로 플레이백한다.
"""
import pygame
from assets.constants import (
    SCREEN_W, SCREEN_H, DARK, PANEL, WHITE, LIGHT, GRAY,
    RED, GREEN, ACCENT, YELLOW,
)
from .ui_utils import Button, draw_text, draw_panel


class GameScreen:
    PLAY_MS_PER_EVENT = 400   # 이벤트 간 간격

    def __init__(self, app, result):
        self.app = app
        self.result = result

        self.event_idx = 0
        self.time_accum = 0.0
        self.last_ticks = pygame.time.get_ticks()
        self.speed = 1.0      # 배속
        self.paused = False

        self.skip_btn = Button((SCREEN_W - 160, SCREEN_H - 60, 130, 46),
                               "끝까지 ▶▶", self._skip_to_end, color=RED)
        self.speed_btn = Button((SCREEN_W - 320, SCREEN_H - 60, 140, 46),
                                f"속도 x{self.speed}", self._cycle_speed,
                                color=(80, 140, 220))
        self.pause_btn = Button((SCREEN_W - 480, SCREEN_H - 60, 140, 46),
                                "일시정지", self._toggle_pause,
                                color=(130, 130, 150))
        self.next_btn = Button((30, SCREEN_H - 60, 160, 46),
                               "결과 보기 ▶",
                               lambda: self.app.goto_result(self.result),
                               color=GREEN, disabled=True)

        # 현재 스코어보드(누적)
        self.cur_player_runs_by_inn = []
        self.cur_cpu_runs_by_inn    = []
        self.cur_inning = 0          # 진행 중 inning
        self.cur_top    = True
        self.cur_outs   = 0
        self.cur_bases  = [False, False, False]   # 간이
        self.log_lines  = []          # 최근 이벤트 텍스트

        # 현재 투수 이름
        self.cur_player_pitcher = ""   # 우리 팀 투수 (CPU 공격 시 등판)
        self.cur_cpu_pitcher    = ""   # 상대 투수 (우리 팀 공격 시 등판)

    # ── 컨트롤 ────────────────────────────────────
    def _cycle_speed(self):
        order = [0.5, 1.0, 2.0, 4.0, 8.0]
        try:
            i = order.index(self.speed)
            self.speed = order[(i + 1) % len(order)]
        except ValueError:
            self.speed = 1.0
        self.speed_btn.label = f"속도 x{self.speed}"

    def _toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.label = "▶ 재생" if self.paused else "일시정지"

    def _skip_to_end(self):
        # 남은 이벤트 전부 적용
        while self.event_idx < len(self.result.events):
            self._apply_event(self.result.events[self.event_idx])
            self.event_idx += 1
        self._finish()

    def _finish(self):
        self.next_btn.disabled = False

    # ── 이벤트 반영 ───────────────────────────────
    def _apply_event(self, ev):
        # 이닝 경계 감지
        if ev.inning != self.cur_inning or ev.top != self.cur_top:
            # 이전 half 종료 시 스코어 배열에 채움
            if self.cur_inning != 0:
                if self.cur_top:
                    # 방금 막 끝낸게 top
                    self._ensure_inning_slot(self.cur_player_runs_by_inn,
                                             self.cur_inning)
                else:
                    self._ensure_inning_slot(self.cur_cpu_runs_by_inn,
                                             self.cur_inning)
            self.cur_inning = ev.inning
            self.cur_top    = ev.top
            self.cur_outs   = 0
            self.cur_bases  = [False, False, False]

        # 현재 투수 갱신
        if ev.top:
            self.cur_cpu_pitcher = ev.pitcher      # 우리 팀 공격 → CPU 투수
        else:
            self.cur_player_pitcher = ev.pitcher   # CPU 공격 → 우리 팀 투수

        # 텍스트 로그
        prefix = f"{ev.inning}회 {'초' if ev.top else '말'}"
        self.log_lines.append(f"{prefix} | {ev.text}")
        if len(self.log_lines) > 14:
            self.log_lines = self.log_lines[-14:]

        # 스코어 누적
        if ev.top:
            self._add_run(self.cur_player_runs_by_inn, ev.inning, ev.runs)
        else:
            self._add_run(self.cur_cpu_runs_by_inn, ev.inning, ev.runs)

        # 아웃/베이스 (간이 추적)
        r = ev.result
        if r in ("K", "OUT"):
            self.cur_outs = ev.outs_after
        elif r == "HR":
            self.cur_bases = [False, False, False]
            self.cur_outs = ev.outs_after
        elif r == "3B":
            self.cur_bases = [False, False, True]
        elif r == "2B":
            # 2루타: 새 2루 + 1루 비움. 실제 시뮬과 다를 수 있음 (간이)
            self.cur_bases = [False, True, self.cur_bases[0]]
        elif r == "1B":
            self.cur_bases = [True, self.cur_bases[0], self.cur_bases[1] or self.cur_bases[2]]
        elif r == "BB":
            if all(self.cur_bases):
                pass  # 밀어내기 - 베이스는 그대로
            else:
                if not self.cur_bases[0]:
                    self.cur_bases[0] = True
                else:
                    if not self.cur_bases[1]:
                        self.cur_bases[1] = True
                    else:
                        self.cur_bases[2] = True

    def _add_run(self, lst, inning, runs):
        while len(lst) < inning:
            lst.append(0)
        lst[inning - 1] += runs

    def _ensure_inning_slot(self, lst, inning):
        while len(lst) < inning:
            lst.append(0)

    # ── 메인 루프 ─────────────────────────────────
    def handle(self, events):
        screen = self.app.screen
        screen.fill(DARK)

        for ev in events:
            self.skip_btn.handle(ev)
            self.speed_btn.handle(ev)
            self.pause_btn.handle(ev)
            self.next_btn.handle(ev)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE:
                    self._toggle_pause()
                elif ev.key == pygame.K_s:
                    self._skip_to_end()

        # 시간 흐름
        now = pygame.time.get_ticks()
        dt = now - self.last_ticks
        self.last_ticks = now
        if not self.paused and self.event_idx < len(self.result.events):
            self.time_accum += dt * self.speed
            step = self.PLAY_MS_PER_EVENT
            while self.time_accum >= step and self.event_idx < len(self.result.events):
                self._apply_event(self.result.events[self.event_idx])
                self.event_idx += 1
                self.time_accum -= step
            if self.event_idx >= len(self.result.events):
                self._finish()

        # 그리기
        self._draw_header(screen)
        self._draw_scoreboard(screen)
        self._draw_diamond(screen)
        self._draw_log(screen)

        self.pause_btn.draw(screen)
        self.speed_btn.draw(screen)
        self.skip_btn.draw(screen)
        self.next_btn.draw(screen)

    def _draw_header(self, screen):
        draw_text(screen, f"{self.result.player_team}  VS  {self.result.cpu_team}",
                  (SCREEN_W // 2, 40),
                  size=28, color=WHITE, bold=True, center=True)
        total_ev = len(self.result.events)
        progress = self.event_idx / max(total_ev, 1)
        bar_rect = pygame.Rect(SCREEN_W//2 - 300, 85, 600, 8)
        pygame.draw.rect(screen, (60, 64, 80), bar_rect, border_radius=4)
        pygame.draw.rect(screen, ACCENT,
                         pygame.Rect(bar_rect.x, bar_rect.y,
                                     int(bar_rect.w * progress), bar_rect.h),
                         border_radius=4)

    def _draw_scoreboard(self, screen):
        # 박스스코어 스타일
        x0, y0 = 40, 130
        cols = max(9, self.cur_inning)
        cell_w = 48
        cell_h = 44
        # 헤더
        header = pygame.Rect(x0, y0, 160 + cols * cell_w + 90, cell_h)
        draw_panel(screen, header, color=(50, 54, 70))
        draw_text(screen, "팀", (x0 + 20, y0 + 12), size=18,
                  color=WHITE, bold=True)
        for i in range(cols):
            draw_text(screen, str(i + 1),
                      (x0 + 160 + i * cell_w + cell_w // 2, y0 + 12),
                      size=18, color=WHITE, center=True, bold=True)
        # R H
        draw_text(screen, "R", (x0 + 160 + cols * cell_w + 25, y0 + 12),
                  size=18, color=WHITE, bold=True, center=True)
        draw_text(screen, "H", (x0 + 160 + cols * cell_w + 65, y0 + 12),
                  size=18, color=WHITE, bold=True, center=True)

        # 플레이어 행
        pr = pygame.Rect(x0, y0 + cell_h + 2, header.w, cell_h)
        draw_panel(screen, pr, color=PANEL)
        draw_text(screen, self.result.player_team[:10],
                  (x0 + 20, pr.y + 12), size=18, color=WHITE)
        for i in range(cols):
            v = self.cur_player_runs_by_inn[i] if i < len(self.cur_player_runs_by_inn) else ""
            draw_text(screen, str(v),
                      (x0 + 160 + i * cell_w + cell_w // 2, pr.y + 12),
                      size=18, color=LIGHT, center=True)
        draw_text(screen, str(sum(self.cur_player_runs_by_inn)),
                  (x0 + 160 + cols * cell_w + 25, pr.y + 12),
                  size=18, color=YELLOW, bold=True, center=True)
        draw_text(screen, str(self._count_hits(top=True)),
                  (x0 + 160 + cols * cell_w + 65, pr.y + 12),
                  size=18, color=LIGHT, center=True)

        # CPU 행
        cr = pygame.Rect(x0, y0 + 2 * (cell_h + 2), header.w, cell_h)
        draw_panel(screen, cr, color=PANEL)
        draw_text(screen, self.result.cpu_team[:10],
                  (x0 + 20, cr.y + 12), size=18, color=WHITE)
        for i in range(cols):
            v = self.cur_cpu_runs_by_inn[i] if i < len(self.cur_cpu_runs_by_inn) else ""
            draw_text(screen, str(v),
                      (x0 + 160 + i * cell_w + cell_w // 2, cr.y + 12),
                      size=18, color=LIGHT, center=True)
        draw_text(screen, str(sum(self.cur_cpu_runs_by_inn)),
                  (x0 + 160 + cols * cell_w + 25, cr.y + 12),
                  size=18, color=YELLOW, bold=True, center=True)
        draw_text(screen, str(self._count_hits(top=False)),
                  (x0 + 160 + cols * cell_w + 65, cr.y + 12),
                  size=18, color=LIGHT, center=True)

    def _count_hits(self, top: bool) -> int:
        # 현재까지 재생된 이벤트 기준
        cnt = 0
        for i, ev in enumerate(self.result.events[:self.event_idx]):
            if ev.top == top and ev.result in ("1B", "2B", "3B", "HR"):
                cnt += 1
        return cnt

    def _draw_diamond(self, screen):
        # 우측 정보 패널 (이닝 / 주자 / 아웃 / 투수)
        px = SCREEN_W - 265   # 패널 좌측 x
        pw = 250              # 패널 너비
        cx = px + pw // 2     # 패널 중앙 x

        draw_panel(screen, pygame.Rect(px, 130, pw, SCREEN_H - 130 - 90), color=PANEL)

        # 이닝 표시
        inn_label = f"{self.cur_inning}회 {'초' if self.cur_top else '말'}" if self.cur_inning else "대기"
        draw_text(screen, inn_label, (cx, 152), size=22, color=WHITE, bold=True, center=True)

        # 다이아몬드 (상단: 2루 / 우측: 1루 / 하단: 홈 / 좌측: 3루)
        bx  = px + 30    # 다이아몬드 좌측
        by  = 185        # 다이아몬드 상단
        sz  = 95         # 크기

        home   = (bx + sz//2, by + sz)
        first  = (bx + sz,    by + sz//2)
        second = (bx + sz//2, by)
        third  = (bx,         by + sz//2)

        def draw_base(pt, occupied):
            color = YELLOW if occupied else (80, 80, 100)
            r = 13
            pygame.draw.rect(screen, color, pygame.Rect(pt[0]-r, pt[1]-r, r*2, r*2))
            pygame.draw.rect(screen, WHITE, pygame.Rect(pt[0]-r, pt[1]-r, r*2, r*2), width=2)

        draw_base(home, False)
        draw_base(first,  self.cur_bases[0])
        draw_base(second, self.cur_bases[1])
        draw_base(third,  self.cur_bases[2])
        pygame.draw.polygon(screen, (80, 80, 100), [home, first, second, third], width=2)

        # 아웃 카운트
        draw_text(screen, f"아웃  {self.cur_outs}",
                  (cx, by + sz + 24),
                  size=18, color=YELLOW if self.cur_outs else LIGHT,
                  center=True, bold=True)

        # 투수 정보
        ty = by + sz + 58
        draw_text(screen, "[ 투수 ]", (cx, ty), size=15, color=GRAY, center=True)
        draw_text(screen, f"상대:  {self.cur_cpu_pitcher or '-'}",
                  (px + 15, ty + 24), size=15, color=ACCENT)
        draw_text(screen, f"우리:  {self.cur_player_pitcher or '-'}",
                  (px + 15, ty + 46), size=15, color=GREEN)

    def _draw_log(self, screen):
        # 로그 패널 너비를 우측 정보 패널과 겹치지 않게 설정
        panel = pygame.Rect(40, 310, SCREEN_W - 310, SCREEN_H - 310 - 90)
        draw_panel(screen, panel, color=PANEL)
        draw_text(screen, "플레이 로그", (panel.x + 20, panel.y + 12),
                  size=20, color=WHITE, bold=True)
        for i, line in enumerate(self.log_lines):
            draw_text(screen, line,
                      (panel.x + 20, panel.y + 50 + i * 22),
                      size=16, color=LIGHT)
