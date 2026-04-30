"""
ui_utils.py - UI 공용 유틸 (버튼, 폰트, 도형)
"""
from __future__ import annotations
import os
import platform
import pygame
from typing import Callable, Optional, Tuple

from assets.constants import (
    WHITE, BLACK, GRAY, LIGHT, DARK, PANEL, ACCENT, GREEN, RED, YELLOW,
)


# ────────────────────────────────────────────────
# 폰트 (한글 지원)
# ────────────────────────────────────────────────
_FONT_CACHE: dict = {}

def _find_korean_font() -> Optional[str]:
    """OS별로 설치된 한글 폰트를 찾음. 없으면 None."""
    candidates = []
    sys_name = platform.system()
    if sys_name == "Windows":
        candidates = [
            "C:/Windows/Fonts/malgun.ttf",
            "C:/Windows/Fonts/malgunbd.ttf",
            "C:/Windows/Fonts/NanumGothic.ttf",
            "C:/Windows/Fonts/gulim.ttc",
        ]
    elif sys_name == "Darwin":
        candidates = [
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/Library/Fonts/AppleGothic.ttf",
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
            "/Library/Fonts/NanumGothic.ttf",
        ]
    else:  # Linux
        candidates = [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


_KOREAN_FONT_PATH: Optional[str] = None
_FONT_RESOLVED = False

def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    global _KOREAN_FONT_PATH, _FONT_RESOLVED
    if not _FONT_RESOLVED:
        _KOREAN_FONT_PATH = _find_korean_font()
        _FONT_RESOLVED = True
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    if _KOREAN_FONT_PATH:
        f = pygame.font.Font(_KOREAN_FONT_PATH, size)
        f.set_bold(bold)
    else:
        try:
            fname = pygame.font.match_font(
                "malgungothic,applegothic,nanumgothic,notosanscjk,dejavusans"
            )
            f = pygame.font.Font(fname, size) if fname else pygame.font.SysFont(None, size)
            f.set_bold(bold)
        except Exception:
            f = pygame.font.SysFont(None, size)
    _FONT_CACHE[key] = f
    return f


# ────────────────────────────────────────────────
# 텍스트 렌더 도우미
# ────────────────────────────────────────────────
def draw_text(surface: pygame.Surface, text: str, pos: Tuple[int, int],
              size: int = 20, color=WHITE, bold: bool = False,
              center: bool = False, right: bool = False):
    font = get_font(size, bold=bold)
    surf = font.render(str(text), True, color)
    rect = surf.get_rect()
    if center:
        rect.center = pos
    elif right:
        rect.topright = pos
    else:
        rect.topleft = pos
    surface.blit(surf, rect)
    return rect


def draw_panel(surface, rect, color=PANEL, radius=8, border=None, border_color=ACCENT):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surface, border_color, rect, width=border, border_radius=radius)


# ────────────────────────────────────────────────
# Button
# ────────────────────────────────────────────────
class Button:
    def __init__(self, rect, label: str, on_click: Callable[[], None],
                 color=ACCENT, hover_color=None, text_color=WHITE,
                 font_size: int = 20, disabled: bool = False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.color = color
        self.hover_color = hover_color or tuple(min(255, c + 25) for c in color)
        self.text_color = text_color
        self.font_size = font_size
        self.disabled = disabled
        self._hovered = False

    def handle(self, event):
        if self.disabled:
            return
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()

    def draw(self, surface):
        if self.disabled:
            c = GRAY
        else:
            c = self.hover_color if self._hovered else self.color
        pygame.draw.rect(surface, c, self.rect, border_radius=6)
        draw_text(surface, self.label, self.rect.center,
                  size=self.font_size, color=self.text_color,
                  bold=True, center=True)