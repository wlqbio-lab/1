#!/usr/bin/env python3
"""A simple terminal version of the classic "Down 100 Floors" arcade game.

Use the left and right arrow keys (or A/D) to steer the hero toward the gaps in
approaching floors. Survive a hundred floors to win the game.
"""
from __future__ import annotations

import curses
import random
import time
from dataclasses import dataclass


@dataclass
class Floor:
    """Represents a single moving floor segment."""

    y: int
    hole_start: int
    hole_end: int
    passed: bool = False


WIDTH = 40
HEIGHT = 24
PLAYER_Y = HEIGHT - 4
HOLE_WIDTH = 6
FLOOR_GAP = 4
FRAME_DELAY = 0.08
SPEEDUP_INTERVAL = 15
MIN_FRAME_DELAY = 0.04


def create_floor(y: int) -> Floor:
    hole_center = random.randint(4, WIDTH - 5)
    hole_start = max(1, hole_center - HOLE_WIDTH // 2)
    hole_end = min(WIDTH - 2, hole_start + HOLE_WIDTH)
    return Floor(y=y, hole_start=hole_start, hole_end=hole_end)


def init_floors() -> list[Floor]:
    floors: list[Floor] = []
    for i in range(HEIGHT // FLOOR_GAP + 3):
        floors.append(create_floor(HEIGHT + i * FLOOR_GAP))
    return floors


def draw_border(stdscr: "curses._CursesWindow") -> None:
    for x in range(WIDTH):
        stdscr.addch(0, x, "#")
        stdscr.addch(HEIGHT - 1, x, "#")
    for y in range(HEIGHT):
        stdscr.addch(y, 0, "#")
        stdscr.addch(y, WIDTH - 1, "#")


def draw_floor(stdscr: "curses._CursesWindow", floor: Floor) -> None:
    if not (0 < floor.y < HEIGHT - 1):
        return
    for x in range(1, WIDTH - 1):
        ch = " " if floor.hole_start <= x < floor.hole_end else "="
        stdscr.addch(floor.y, x, ch)


def draw_player(stdscr: "curses._CursesWindow", x: int) -> None:
    stdscr.addch(PLAYER_Y, x, "@")
    stdscr.addch(PLAYER_Y + 1, x, "|")


def render(stdscr: "curses._CursesWindow", floors: list[Floor], player_x: int, cleared: int, best: int) -> None:
    stdscr.erase()
    draw_border(stdscr)
    for floor in floors:
        draw_floor(stdscr, floor)
    draw_player(stdscr, player_x)
    stdscr.addstr(1, 2, f"Cleared: {cleared:3d}/100")
    stdscr.addstr(2, 2, f"Best:    {best:3d}")
    stdscr.addstr(3, 2, "Move with ←/→ or A/D. Survive 100 floors!")
    stdscr.refresh()


def update_floors(floors: list[Floor]) -> None:
    for floor in floors:
        floor.y -= 1


def recycle_floors(floors: list[Floor]) -> None:
    floors[:] = [f for f in floors if f.y > 0]
    while len(floors) < HEIGHT // FLOOR_GAP + 3:
        last_y = max((f.y for f in floors), default=0)
        floors.append(create_floor(last_y + FLOOR_GAP))


def check_collision(floors: list[Floor], player_x: int, cleared: int) -> tuple[bool, int]:
    for floor in floors:
        if floor.passed:
            continue
        if floor.y <= PLAYER_Y:
            floor.passed = True
            if floor.hole_start <= player_x < floor.hole_end:
                cleared += 1
            else:
                return True, cleared
    return False, cleared


def handle_input(stdscr: "curses._CursesWindow", player_x: int) -> int:
    try:
        key = stdscr.getch()
    except curses.error:
        return player_x
    if key in (curses.KEY_LEFT, ord("a"), ord("A")):
        player_x = max(1, player_x - 1)
    elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
        player_x = min(WIDTH - 2, player_x + 1)
    return player_x


def game_loop(stdscr: "curses._CursesWindow") -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    floors = init_floors()
    player_x = WIDTH // 2
    cleared = 0
    best = 0
    frame_delay = FRAME_DELAY
    speed_stage = 0

    while True:
        render(stdscr, floors, player_x, cleared, best)
        start = time.time()

        player_x = handle_input(stdscr, player_x)
        update_floors(floors)
        collision, cleared = check_collision(floors, player_x, cleared)
        if cleared > best:
            best = cleared
        if collision:
            message = "Game over! Press R to retry or Q to quit."
            stdscr.addstr(HEIGHT // 2, max(2, WIDTH // 2 - len(message) // 2), message)
            stdscr.refresh()
            stdscr.nodelay(False)
            while True:
                ch = stdscr.getch()
                if ch in (ord("q"), ord("Q")):
                    return
                if ch in (ord("r"), ord("R")):
                    floors = init_floors()
                    player_x = WIDTH // 2
                    cleared = 0
                    frame_delay = FRAME_DELAY
                    speed_stage = 0
                    stdscr.nodelay(True)
                    break
            continue

        if cleared >= 100:
            message = "You cleared 100 floors! Press Q to quit or R to play again."
            stdscr.addstr(HEIGHT // 2, max(2, WIDTH // 2 - len(message) // 2), message)
            stdscr.refresh()
            stdscr.nodelay(False)
            while True:
                ch = stdscr.getch()
                if ch in (ord("q"), ord("Q")):
                    return
                if ch in (ord("r"), ord("R")):
                    floors = init_floors()
                    player_x = WIDTH // 2
                    cleared = 0
                    frame_delay = FRAME_DELAY
                    speed_stage = 0
                    stdscr.nodelay(True)
                    break
            continue

        recycle_floors(floors)
        target_stage = cleared // SPEEDUP_INTERVAL
        if target_stage > speed_stage:
            frame_delay = max(MIN_FRAME_DELAY, frame_delay * 0.95)
            speed_stage = target_stage

        elapsed = time.time() - start
        time.sleep(max(0, frame_delay - elapsed))


def main() -> None:
    curses.wrapper(game_loop)


if __name__ == "__main__":
    main()
