"""
screen_newgame.py - 새 게임 시작 시 구단명 입력
"""
import pygame
from assets.constants import (
    SCREEN_W, SCREEN_H, DARK, PANEL, WHITE, LIGHT, GRAY,
    ACCENT, GREEN, RED, YELLOW,
)
from .ui_utils import Button, draw_text, draw_panel
from data.data_manager import new_game


class NewGameScreen:
    MAX_NAME_LEN = 16   # 구단명 최대 글자 수

    def __init__(self, app):
        self.app = app
        self.team_name = ""     # 현재 입력 중인 구단명
        self.error_msg = ""     # 유효성 검사 메시지

        cx = SCREEN_W // 2

        self.confirm_btn = Button(
            (cx - 130, 440, 120, 52),
            "시작", self._confirm, color=GREEN, font_size=22,
        )
        self.cancel_btn = Button(
            (cx + 10, 440, 120, 52),
            "취소", lambda: self.app.goto("main"),
            color=(120, 120, 130), font_size=22,
        )

    def _confirm(self):
        name = self.team_name.strip()
        if not name:
            self.error_msg = "구단명을 입력해주세요."
            return
        # 새 게임 생성 후 팀명 설정
        roster = new_game()
        roster.team_name = name
        self.app.roster = roster
        self.app.game_count = 0
        self.app.goto("main")

    def handle(self, events):
        screen = self.app.screen
        screen.fill(DARK)

        # 키보드 입력 처리
        for ev in events:
            self.confirm_btn.handle(ev)
            self.cancel_btn.handle(ev)

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    self._confirm()
                elif ev.key == pygame.K_ESCAPE:
                    self.app.goto("main")
                elif ev.key == pygame.K_BACKSPACE:
                    self.team_name = self.team_name[:-1]
                    self.error_msg = ""
                else:
                    # 글자 추가 (최대 길이 제한)
                    if len(self.team_name) < self.MAX_NAME_LEN:
                        self.team_name += ev.unicode
                    self.error_msg = ""

        # ── 그리기 ──────────────────────────────
        draw_text(screen, "새 게임",
                  (SCREEN_W // 2, 160), size=48, color=WHITE,
                  bold=True, center=True)
        draw_text(screen, "구단명을 입력하세요",
                  (SCREEN_W // 2, 240), size=22, color=LIGHT, center=True)

        # 입력 박스
        box = pygame.Rect(SCREEN_W // 2 - 220, 290, 440, 60)
        draw_panel(screen, box, color=(70, 74, 92), border=2,
                   border_color=ACCENT)
        display_name = self.team_name + "|"   # 커서 표시
        draw_text(screen, display_name,
                  (box.x + 20, box.y + 14), size=26, color=WHITE)

        # 글자 수 표시
        draw_text(screen, f"{len(self.team_name)} / {self.MAX_NAME_LEN}",
                  (box.right - 10, box.y + 20), size=14,
                  color=GRAY, right=True)

        # 에러 메시지
        if self.error_msg:
            draw_text(screen, self.error_msg,
                      (SCREEN_W // 2, 380), size=18,
                      color=RED, center=True)

        # 안내
        draw_text(screen, "Enter로 시작  /  ESC로 취소",
                  (SCREEN_W // 2, 510), size=15, color=GRAY, center=True)

        self.confirm_btn.draw(screen)
        self.cancel_btn.draw(screen)
