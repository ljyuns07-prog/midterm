"""
screen_result.py - 경기 종료 결과 화면
"""
import pygame
from assets.constants import (
    SCREEN_W, SCREEN_H, DARK, PANEL, WHITE, LIGHT, GRAY, GOLD,
    RED, GREEN, ACCENT, YELLOW,
)
from .ui_utils import Button, draw_text, draw_panel


class ResultScreen:
    def __init__(self, app, result, gold_reward: int):
        self.app = app
        self.result = result
        self.gold_reward = gold_reward

        self.main_btn = Button((SCREEN_W//2 - 210, SCREEN_H - 120, 180, 56),
                               "메인 메뉴", lambda: app.goto("main"),
                               color=ACCENT, font_size=22)
        self.again_btn = Button((SCREEN_W//2 + 30, SCREEN_H - 120, 180, 56),
                                "다시 경기 →", lambda: app.goto("match"),
                                color=GREEN, font_size=22)

    def handle(self, events):
        screen = self.app.screen
        screen.fill(DARK)

        for ev in events:
            self.main_btn.handle(ev)
            self.again_btn.handle(ev)

        r = self.result
        win = r.player_wins
        result_word = "승리!" if win else ("무승부" if r.tied else "패배")
        result_color = GREEN if win else (YELLOW if r.tied else RED)

        draw_text(screen, result_word,
                  (SCREEN_W//2, 90),
                  size=72, color=result_color, bold=True, center=True)

        # 최종 스코어
        score_str = f"{r.player_score}  :  {r.cpu_score}"
        draw_text(screen, score_str, (SCREEN_W//2, 180),
                  size=56, color=WHITE, bold=True, center=True)

        draw_text(screen, f"{r.player_team}        {r.cpu_team}",
                  (SCREEN_W//2, 240),
                  size=20, color=LIGHT, center=True)

        # 박스스코어
        self._draw_boxscore(screen)

        # 보상
        reward_y = SCREEN_H - 220
        draw_panel(screen, pygame.Rect(SCREEN_W//2 - 260, reward_y, 520, 80),
                   color=(60, 60, 40), border=2, border_color=GOLD)
        draw_text(screen, f"획득 골드: +{self.gold_reward} G",
                  (SCREEN_W//2, reward_y + 20),
                  size=26, color=GOLD, bold=True, center=True)
        draw_text(screen,
                  f"현재 보유 {self.app.roster.gold} G",
                  (SCREEN_W//2, reward_y + 52),
                  size=18, color=LIGHT, center=True)

        self.main_btn.draw(screen)
        self.again_btn.draw(screen)

    def _draw_boxscore(self, screen):
        r = self.result
        x0, y0 = 120, 290
        innings = max(9, r.innings_played)
        cell_w = 44
        cell_h = 38

        width = 180 + innings * cell_w + 90
        # 헤더
        h = pygame.Rect(x0, y0, width, cell_h)
        draw_panel(screen, h, color=(50, 54, 70))
        draw_text(screen, "팀", (x0 + 20, y0 + 8), size=16,
                  color=WHITE, bold=True)
        for i in range(innings):
            draw_text(screen, str(i+1),
                      (x0 + 180 + i*cell_w + cell_w//2, y0 + 8),
                      size=16, color=WHITE, bold=True, center=True)
        draw_text(screen, "R", (x0 + 180 + innings*cell_w + 25, y0 + 8),
                  size=16, color=WHITE, bold=True, center=True)
        draw_text(screen, "H", (x0 + 180 + innings*cell_w + 65, y0 + 8),
                  size=16, color=WHITE, bold=True, center=True)

        # 플레이어 행
        pr = pygame.Rect(x0, y0 + cell_h + 2, width, cell_h)
        draw_panel(screen, pr, color=PANEL)
        draw_text(screen, r.player_team[:12],
                  (x0 + 20, pr.y + 8), size=16, color=WHITE)
        for i in range(innings):
            v = r.player_runs_by_inn[i] if i < len(r.player_runs_by_inn) else "-"
            draw_text(screen, str(v),
                      (x0 + 180 + i*cell_w + cell_w//2, pr.y + 8),
                      size=16, color=LIGHT, center=True)
        draw_text(screen, str(r.player_score),
                  (x0 + 180 + innings*cell_w + 25, pr.y + 8),
                  size=16, color=YELLOW, bold=True, center=True)
        draw_text(screen, str(r.player_hits),
                  (x0 + 180 + innings*cell_w + 65, pr.y + 8),
                  size=16, color=LIGHT, center=True)

        # CPU 행
        cr = pygame.Rect(x0, y0 + 2*(cell_h + 2), width, cell_h)
        draw_panel(screen, cr, color=PANEL)
        draw_text(screen, r.cpu_team[:12],
                  (x0 + 20, cr.y + 8), size=16, color=WHITE)
        for i in range(innings):
            v = r.cpu_runs_by_inn[i] if i < len(r.cpu_runs_by_inn) else "-"
            draw_text(screen, str(v),
                      (x0 + 180 + i*cell_w + cell_w//2, cr.y + 8),
                      size=16, color=LIGHT, center=True)
        draw_text(screen, str(r.cpu_score),
                  (x0 + 180 + innings*cell_w + 25, cr.y + 8),
                  size=16, color=YELLOW, bold=True, center=True)
        draw_text(screen, str(r.cpu_hits),
                  (x0 + 180 + innings*cell_w + 65, cr.y + 8),
                  size=16, color=LIGHT, center=True)
