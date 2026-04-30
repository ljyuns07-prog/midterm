"""
screen_main.py - 메인 메뉴
"""
import pygame
from assets.constants import (
    SCREEN_W, SCREEN_H, DARK, ACCENT, GREEN, RED, YELLOW, WHITE, GOLD,
    PANEL, LIGHT, GRAY,
)
from .ui_utils import Button, draw_text, draw_panel


class MainMenuScreen:
    def __init__(self, app):
        self.app = app

        # 버튼 레이아웃
        bw, bh = 280, 60
        cx = SCREEN_W // 2
        start_y = 300
        gap = 80

        self.buttons = [
            Button((cx - bw//2, start_y + 0*gap, bw, bh),
                   "경기 시작", lambda: app.goto("match"),
                   color=GREEN),
            Button((cx - bw//2, start_y + 1*gap, bw, bh),
                   "엔트리 관리", lambda: app.goto("roster")),
            Button((cx - bw//2, start_y + 2*gap, bw, bh),
                   "상점 (선수 뽑기)", lambda: app.goto("shop"),
                   color=YELLOW, text_color=(40, 40, 40)),
            Button((cx - bw//2, start_y + 3*gap, bw, bh),
                   "저장하기", lambda: app.goto("save"),
                   color=(100, 180, 220)),
            Button((cx - bw//2, start_y + 4*gap, bw, bh),
                   "새 게임", lambda: app.goto("new_game"),
                   color=RED),
        ]

        self.quit_btn = Button(
            (20, 20, 100, 38), "나가기", lambda: app.quit(),
            color=(70, 70, 80), font_size=16,
        )

    def handle(self, events):
        screen = self.app.screen
        screen.fill(DARK)

        # 타이틀
        draw_text(screen, "SNU Baseball Manager",
                  (SCREEN_W//2, 110), size=52, color=WHITE,
                  bold=True, center=True)
        draw_text(screen, "야구 시뮬레이션 게임",
                  (SCREEN_W//2, 165), size=20, color=LIGHT, center=True)

        # 팀 정보 패널
        r = self.app.roster
        panel_rect = pygame.Rect(SCREEN_W//2 - 280, 200, 560, 70)
        draw_panel(screen, panel_rect, color=PANEL, border=2)
        draw_text(screen, f"팀명 : {r.team_name}",
                  (panel_rect.x + 20, panel_rect.y + 10),
                  size=22, color=WHITE, bold=True)
        draw_text(screen, f"경기 수 : {self.app.game_count}경기",
                  (panel_rect.x + 20, panel_rect.y + 40),
                  size=18, color=LIGHT)
        draw_text(screen, f"{r.gold} G",
                  (panel_rect.right - 20, panel_rect.y + 20),
                  size=28, color=GOLD, bold=True, right=True)

        for ev in events:
            for b in self.buttons:
                b.handle(ev)
            self.quit_btn.handle(ev)

        for b in self.buttons:
            b.draw(screen)
        self.quit_btn.draw(screen)

        # 하단 안내
        draw_text(screen,
                  "Excel 편집 → players.xlsx / cpu_teams.xlsx (data 폴더)",
                  (SCREEN_W//2, SCREEN_H - 40),
                  size=15, color=GRAY, center=True)
