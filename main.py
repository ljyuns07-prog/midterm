# pygame과 openpyxl 모듈 필요
# mac이면 pip3 install pygame 으로 설치 (Windows면 pip install 사용)
# conda 환경이면 conda install 사용

# 프로그램의 핵심이 되는 main.py

import sys
import os
sys.path.insert(0, os.getcwd())

import pygame
from assets.constants import *
from data.data_manager import (
    load_cpu_teams, save_game, load_game, new_game,
    PLAYER_XL, CPU_XL
)
from game.simulator import simulate_game
from ui import (MainMenuScreen, RosterScreen, ShopScreen,
                MatchScreen, GameScreen, ResultScreen, NewGameScreen)


class App:

    # 시작 화면
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen  = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock   = pygame.time.Clock()
        self.running = True

        # 게임 데이터
        self.roster    = None
        self.cpu_teams = []
        self.game_count= 0

        # 현재 화면
        self.current_screen = None

        # 초기화
        self._ensure_templates()
        self._load_cpu_teams()
        self._try_load_save()
        self.goto("main")

    # 초기화
    def _ensure_templates(self):
        if not PLAYER_XL.exists():
            raise FileNotFoundError(
                f"players.xlsx 가 없습니다: {PLAYER_XL}\n"
                f"직접 선수풀 엑셀을 만들어 넣어주세요."
            )
        if not CPU_XL.exists():
            print("[App] cpu_teams.xlsx 없음 → 샘플 템플릿 생성")

    def _load_cpu_teams(self):
        self.cpu_teams = load_cpu_teams()
        print(f"[App] CPU팀 {len(self.cpu_teams)}개 로드")

    def _try_load_save(self):
        result = load_game()
        if result:
            self.roster, self.game_count = result
            print(f"[App] 세이브 로드: {self.roster.team_name} "
                  f"(경기수 {self.game_count})")
        else:
            print("[App] 세이브 없음 → 새 게임 시작")
            self.roster = new_game()

    # 화면 전환
    def goto(self, name: str):
        if name == "main":
            self.current_screen = MainMenuScreen(self)
        elif name == "roster":
            self.current_screen = RosterScreen(self)
        elif name == "shop":
            self.current_screen = ShopScreen(self)
        elif name == "match":
            self.current_screen = MatchScreen(self)
        elif name == "new_game":
            self.current_screen = NewGameScreen(self)
        elif name == "save":
            save_game(self.roster, self.game_count)
            self.current_screen = MainMenuScreen(self)

    def quit(self):
        self.running = False

    def start_game(self, cpu_team):
        result = simulate_game(self.roster, cpu_team, self.game_count)
        self.game_count += 1
        # 골드 보상
        if result.player_wins:
            gold_reward = WIN_GOLD_BASE + cpu_team.difficulty * 3
        else:
            gold_reward = LOSS_GOLD_BASE
        self.roster.gold += gold_reward
        self._pending_result = result
        self._pending_gold   = gold_reward
        self.current_screen  = GameScreen(self, result)

    def goto_result(self, result):
        self.current_screen = ResultScreen(self, result, self._pending_gold)

    # 메인 루프
    def run(self):
        while self.running:
            events = pygame.event.get()
            for ev in events:
                if ev.type == pygame.QUIT:
                    self.running = False

            if self.current_screen:
                self.current_screen.handle(events)

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = App()
    app.run()