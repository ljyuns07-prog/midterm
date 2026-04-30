"""
screen_match.py - CPU팀 선택
"""
import pygame
from assets.constants import (
    SCREEN_W, SCREEN_H, DARK, PANEL, WHITE, LIGHT, GRAY, GOLD,
    RED, GREEN, ACCENT, YELLOW,
    WIN_GOLD_BASE, LOSS_GOLD_BASE,
)
from .ui_utils import Button, draw_text, draw_panel


class MatchScreen:
    def __init__(self, app):
        self.app = app
        self.selected_idx = 0
        self.message = ""
        self.message_timer = 0

        self.back_btn = Button((30, SCREEN_H - 60, 140, 46),
                               "◀ 메인", lambda: self.app.goto("main"),
                               color=(120, 120, 130))
        self.start_btn = Button((SCREEN_W - 260, SCREEN_H - 60, 230, 46),
                                "경기 시작 ▶", self._start, color=GREEN)

    def _start(self):
        if not self.app.cpu_teams:
            self._notify("CPU 팀이 없습니다.")
            return
        if not self.app.roster.is_valid():
            self._notify("엔트리가 유효하지 않습니다 (타순 9명/CP 1명 필요)")
            return
        cpu = self.app.cpu_teams[self.selected_idx]
        self.app.start_game(cpu)

    def _notify(self, msg):
        self.message = msg
        self.message_timer = 180

    def handle(self, events):
        screen = self.app.screen
        screen.fill(DARK)

        # 이벤트
        for ev in events:
            self.back_btn.handle(ev)
            self.start_btn.handle(ev)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    self.selected_idx = max(0, self.selected_idx - 1)
                elif ev.key == pygame.K_DOWN:
                    self.selected_idx = min(len(self.app.cpu_teams) - 1,
                                            self.selected_idx + 1)
                elif ev.key == pygame.K_RETURN:
                    self._start()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self._check_team_click(ev.pos)

        # 헤더
        draw_text(screen, "상대 팀 선택",
                  (SCREEN_W//2, 50), size=36, color=WHITE,
                  bold=True, center=True)
        draw_text(screen, f"{self.app.roster.gold} G",
                  (SCREEN_W - 30, 40), size=26, color=GOLD,
                  bold=True, right=True)

        # 팀 카드
        self._team_rects = []
        teams = self.app.cpu_teams
        if not teams:
            draw_text(screen,
                      "CPU 팀이 없습니다. data/cpu_teams.xlsx 를 확인하세요.",
                      (SCREEN_W//2, SCREEN_H//2), size=20,
                      color=RED, center=True)
        else:
            per_row = 4
            card_w, card_h = 260, 180
            total_w = per_row * card_w + (per_row - 1) * 20
            start_x = (SCREEN_W - total_w) // 2
            start_y = 120
            for i, t in enumerate(teams):
                col = i % per_row
                row = i // per_row
                x = start_x + col * (card_w + 20)
                y = start_y + row * (card_h + 20)
                rect = pygame.Rect(x, y, card_w, card_h)
                self._team_rects.append(rect)
                is_sel = i == self.selected_idx
                bg = t.color if is_sel else tuple(c//2 + 40 for c in t.color)
                pygame.draw.rect(screen, bg, rect, border_radius=8)
                if is_sel:
                    pygame.draw.rect(screen, YELLOW, rect, width=3,
                                     border_radius=8)
                draw_text(screen, t.name, (rect.centerx, rect.y + 20),
                          size=22, color=WHITE, bold=True, center=True)
                diff_stars = "★" * t.difficulty + "☆" * (5 - t.difficulty)
                draw_text(screen, diff_stars, (rect.centerx, rect.y + 60),
                          size=22, color=YELLOW, center=True)
                # 오버롤 계산
                if t.roster:
                    players = t.roster.active_roster()
                    ovr = round(sum(p.overall for p in players) / len(players)) if players else 0
                    n_players = len(players)
                else:
                    ovr, n_players = 0, 0
                draw_text(screen, f"OVR  {ovr}",
                          (rect.centerx, rect.y + 95),
                          size=20, color=WHITE, bold=True, center=True)
                draw_text(screen, f"엔트리 {n_players}명",
                          (rect.centerx, rect.y + 122),
                          size=14, color=LIGHT, center=True)
                reward = WIN_GOLD_BASE + t.difficulty * 3
                draw_text(screen, f"승리 보상  {reward}G",
                          (rect.centerx, rect.y + 150),
                          size=15, color=GOLD, bold=True, center=True)

        # 안내
        draw_text(screen,
                  "키보드: ↑/↓ 선택  Enter 시작   |   마우스: 클릭 후 '경기 시작'",
                  (SCREEN_W//2, SCREEN_H - 100), size=15, color=GRAY,
                  center=True)

        self.back_btn.draw(screen)
        self.start_btn.draw(screen)

        # 메시지
        if self.message_timer > 0:
            self.message_timer -= 1
            draw_text(screen, self.message,
                      (SCREEN_W//2, SCREEN_H - 130),
                      size=18, color=RED, bold=True, center=True)

    def _check_team_click(self, pos):
        for i, r in enumerate(getattr(self, "_team_rects", [])):
            if r.collidepoint(pos):
                self.selected_idx = i
                return
