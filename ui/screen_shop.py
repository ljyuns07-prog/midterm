# 상점
import pygame
from typing import List, Optional

from assets.constants import (
    SCREEN_W, SCREEN_H, DARK, PANEL, ACCENT, GREEN, RED, YELLOW, WHITE,
    LIGHT, GRAY, GOLD, DIAMOND,
    PACK_CHEAP_PRICE, PACK_PREMIUM_PRICE,
)
from .ui_utils import Button, draw_text, draw_panel
from data.data_manager import load_player_pool, draw_from_pack
from game.player import Player


TIER_COLOR = {
    "S": (240, 200, 60),
    "A": (180, 100, 220),
    "B": (90, 160, 240),
    "C": (150, 150, 150),
}


class ShopScreen:
    def __init__(self, app):
        self.app = app
        self.roster = app.roster

        # 선수풀 캐시
        try:
            self.pool: List[Player] = load_player_pool()
        except Exception as e:
            self.pool = []
            self.load_error = f"선수풀 로드 실패: {e}"
        else:
            self.load_error = ""

        # 최근 뽑은 선수
        self.last_draws: List[Player] = []
        self.message = ""
        self.message_timer = 0

        self._build_buttons()

    def _build_buttons(self):
        self.back_btn = Button((30, SCREEN_H - 60, 140, 46),
                               "◀ 메인", lambda: self.app.goto("main"),
                               color=(120, 120, 130))

        cx = SCREEN_W // 2

        # 저렴한 팩
        self.cheap_btn = Button(
            (cx - 320, 280, 260, 90),
            f"저렴한 팩 1회 ({PACK_CHEAP_PRICE}G)",
            lambda: self._buy("cheap", 1),
            color=(80, 140, 220), font_size=20,
        )
        self.cheap_10_btn = Button(
            (cx - 320, 380, 260, 60),
            f"저렴한 팩 10회 ({PACK_CHEAP_PRICE*10*0.99}G)",
            lambda: self._buy("cheap", 10),
            color=(60, 120, 200), font_size=16,
        )

        # 프리미엄 팩
        self.prem_btn = Button(
            (cx + 60, 280, 260, 90),
            f"프리미엄 팩 1회 ({PACK_PREMIUM_PRICE}G)",
            lambda: self._buy("premium", 1),
            color=(220, 160, 60), font_size=20, text_color=(40, 40, 40),
        )
        self.prem_10_btn = Button(
            (cx + 60, 380, 260, 60),
            f"프리미엄 팩 10회 ({PACK_PREMIUM_PRICE*10*0.99}G)",
            lambda: self._buy("premium", 10),
            color=(200, 140, 50), font_size=16, text_color=(40, 40, 40),
        )

    def notify(self, msg: str, frames: int = 180):
        self.message = msg
        self.message_timer = frames

    def _buy(self, kind: str, count: int):
        if self.load_error:
            self.notify(self.load_error); return
        if not self.pool:
            self.notify("선수풀이 비어있습니다 (Excel 확인)"); return
        price = (PACK_CHEAP_PRICE if kind == "cheap"
                 else PACK_PREMIUM_PRICE) * count
        if self.roster.gold < price:
            self.notify(f"골드 부족! ({self.roster.gold} / {price})"); return
        # 창고 용량 제한은 없음
        self.roster.gold -= price
        self.last_draws = []
        for _ in range(count):
            p = draw_from_pack(self.pool, kind)
            self.roster.storage.append(p)
            self.last_draws.append(p)
        self.notify(f"{count}명 획득! (창고 확인)", frames=160)

    def handle(self, events):
        screen = self.app.screen
        screen.fill(DARK)

        for ev in events:
            self.back_btn.handle(ev)
            self.cheap_btn.handle(ev)
            self.cheap_10_btn.handle(ev)
            self.prem_btn.handle(ev)
            self.prem_10_btn.handle(ev)

        # 헤더
        draw_text(screen, "상점 (선수 뽑기)",
                  (SCREEN_W//2, 50), size=36, color=WHITE,
                  bold=True, center=True)
        draw_text(screen, f"{self.roster.gold} G",
                  (SCREEN_W - 30, 40), size=28, color=GOLD,
                  bold=True, right=True)
        draw_text(screen,
                  f"보유 창고 {len(self.roster.storage)}명",
                  (SCREEN_W - 30, 75), size=16, color=LIGHT, right=True)

        # 팩 설명
        cx = SCREEN_W // 2
        # 저렴한 팩 패널
        lpanel = pygame.Rect(cx - 340, 140, 320, 330)
        draw_panel(screen, lpanel, color=(60, 70, 100), border=2)
        draw_text(screen, "저렴한 팩", (lpanel.centerx, lpanel.y + 30),
                  size=26, color=WHITE, bold=True, center=True)
        draw_text(screen, "C 55% / B 35% / A 9% / S 1%",
                  (lpanel.centerx, lpanel.y + 68),
                  size=15, color=LIGHT, center=True)
        draw_text(screen, "실속형", (lpanel.centerx, lpanel.y + 95),
                  size=14, color=GRAY, center=True)

        # 프리미엄 팩 패널
        rpanel = pygame.Rect(cx + 20, 140, 320, 330)
        draw_panel(screen, rpanel, color=(120, 90, 40), border=2)
        draw_text(screen, "프리미엄 팩", (rpanel.centerx, rpanel.y + 30),
                  size=26, color=WHITE, bold=True, center=True)
        draw_text(screen, "C 10% / B 35% / A 40% / S 15%",
                  (rpanel.centerx, rpanel.y + 68),
                  size=15, color=LIGHT, center=True)
        draw_text(screen, "고급 선수 기대!", (rpanel.centerx, rpanel.y + 95),
                  size=14, color=YELLOW, center=True)

        self.cheap_btn.draw(screen)
        self.cheap_10_btn.draw(screen)
        self.prem_btn.draw(screen)
        self.prem_10_btn.draw(screen)
        self.back_btn.draw(screen)

        # 최근 뽑기 결과
        if self.last_draws:
            result_rect = pygame.Rect(60, 490, SCREEN_W - 120, 200)
            draw_panel(screen, result_rect, color=PANEL)
            draw_text(screen, "최근 획득",
                      (result_rect.x + 20, result_rect.y + 10),
                      size=20, color=WHITE, bold=True)
            # 최대 10명 표시
            per_row = 5
            cell_w = (result_rect.w - 40) // per_row
            cell_h = 80
            for i, p in enumerate(self.last_draws[-10:]):
                rx = result_rect.x + 20 + (i % per_row) * cell_w
                ry = result_rect.y + 40 + (i // per_row) * cell_h
                cr = pygame.Rect(rx + 4, ry, cell_w - 8, cell_h - 4)
                pygame.draw.rect(screen, (70, 74, 92), cr, border_radius=5)
                tc = TIER_COLOR.get(p.tier, WHITE)
                draw_text(screen, f"[{p.tier}] {p.position}",
                          (cr.x + 10, cr.y + 6),
                          size=16, color=tc, bold=True)
                draw_text(screen, p.name, (cr.x + 10, cr.y + 28),
                          size=16, color=WHITE)
                draw_text(screen, f"OVR {p.overall}",
                          (cr.x + 10, cr.y + 50),
                          size=14, color=LIGHT)

        # 메시지
        if self.message_timer > 0:
            self.message_timer -= 1
            draw_text(screen, self.message,
                      (SCREEN_W // 2, 460),
                      size=20, color=YELLOW, center=True, bold=True)