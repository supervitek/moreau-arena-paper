"""8x8 grid and movement logic.

Standalone version for the companion repository.
"""

from __future__ import annotations

import dataclasses

from simulator.animals import Creature, Position, Size
from simulator.seed import seeded_random


class Grid:
    def __init__(self, width: int = 8, height: int = 8) -> None:
        self.width = width
        self.height = height
        self._cells: dict[Position, Creature] = {}

    def is_valid_position(self, position: Position, size: Size) -> bool:
        if position.row < 0 or position.col < 0:
            return False
        if position.row + size.rows > self.height:
            return False
        if position.col + size.cols > self.width:
            return False
        return True

    def get_occupied_cells(self, position: Position, size: Size) -> list[Position]:
        cells = []
        for dr in range(size.rows):
            for dc in range(size.cols):
                cells.append(Position(position.row + dr, position.col + dc))
        return cells

    def place_creature(self, creature: Creature) -> None:
        if not self.is_valid_position(creature.position, creature.size):
            raise ValueError(
                f"Position {creature.position} invalid for size {creature.size}"
            )
        cells = self.get_occupied_cells(creature.position, creature.size)
        for cell in cells:
            if cell in self._cells and self._cells[cell] is not creature:
                raise ValueError(f"Cell {cell} already occupied")
        for cell in cells:
            self._cells[cell] = creature

    def remove_creature(self, creature: Creature) -> None:
        cells = self.get_occupied_cells(creature.position, creature.size)
        for cell in cells:
            if cell in self._cells and self._cells[cell] is creature:
                del self._cells[cell]

    def get_creature_at(self, position: Position) -> Creature | None:
        return self._cells.get(position)

    def move_creature(self, creature: Creature, target: Position) -> Creature:
        dist = self.get_distance(creature.position, target)
        if dist > creature.movement_range:
            raise ValueError(
                f"Target {target} out of movement range "
                f"({dist} > {creature.movement_range})"
            )
        if not self.is_valid_position(target, creature.size):
            raise ValueError(f"Target {target} invalid for size {creature.size}")
        target_cells = self.get_occupied_cells(target, creature.size)
        for cell in target_cells:
            occupant = self._cells.get(cell)
            if occupant is not None and occupant is not creature:
                raise ValueError(f"Target cell {cell} occupied by another creature")
        self.remove_creature(creature)
        moved = dataclasses.replace(creature, position=target)
        self.place_creature(moved)
        return moved

    @staticmethod
    def get_distance(a: Position, b: Position) -> int:
        return max(abs(a.row - b.row), abs(a.col - b.col))

    def get_adjacent_cells(self, position: Position, size: Size) -> list[Position]:
        occupied = set(self.get_occupied_cells(position, size))
        adjacent: set[Position] = set()
        for cell in occupied:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    neighbor = Position(cell.row + dr, cell.col + dc)
                    if (
                        0 <= neighbor.row < self.height
                        and 0 <= neighbor.col < self.width
                        and neighbor not in occupied
                    ):
                        adjacent.add(neighbor)
        return list(adjacent)

    def _is_position_free(
        self, pos: Position, size: Size, exclude: Creature | None = None
    ) -> bool:
        if not self.is_valid_position(pos, size):
            return False
        for cell in self.get_occupied_cells(pos, size):
            occupant = self._cells.get(cell)
            if occupant is not None and occupant is not exclude:
                return False
        return True

    def find_path_toward(self, creature: Creature, target: Position) -> Position:
        best_pos = creature.position
        best_dist = self.get_distance(creature.position, target)
        for dr in range(-creature.movement_range, creature.movement_range + 1):
            for dc in range(-creature.movement_range, creature.movement_range + 1):
                if dr == 0 and dc == 0:
                    continue
                candidate = Position(
                    creature.position.row + dr, creature.position.col + dc
                )
                move_dist = self.get_distance(creature.position, candidate)
                if move_dist > creature.movement_range:
                    continue
                if not self._is_position_free(
                    candidate, creature.size, exclude=creature
                ):
                    continue
                dist_to_target = self.get_distance(candidate, target)
                if dist_to_target < best_dist:
                    best_dist = dist_to_target
                    best_pos = candidate
                elif dist_to_target == best_dist and candidate < best_pos:
                    best_pos = candidate
        return best_pos

    def find_path_away(self, creature: Creature, enemy_pos: Position) -> Position:
        best_pos = creature.position
        best_dist = self.get_distance(creature.position, enemy_pos)
        for dr in range(-creature.movement_range, creature.movement_range + 1):
            for dc in range(-creature.movement_range, creature.movement_range + 1):
                if dr == 0 and dc == 0:
                    continue
                candidate = Position(
                    creature.position.row + dr, creature.position.col + dc
                )
                move_dist = self.get_distance(creature.position, candidate)
                if move_dist > creature.movement_range:
                    continue
                if not self._is_position_free(
                    candidate, creature.size, exclude=creature
                ):
                    continue
                dist_to_enemy = self.get_distance(candidate, enemy_pos)
                if dist_to_enemy > best_dist:
                    best_dist = dist_to_enemy
                    best_pos = candidate
                elif dist_to_enemy == best_dist and candidate < best_pos:
                    best_pos = candidate
        return best_pos

    def generate_starting_position(self, side: str, size: Size, seed: int) -> Position:
        max_col = self.width - size.cols
        col_f = seeded_random(seed, 0.0, max_col + 0.999)
        col = int(col_f)
        col = max(0, min(col, max_col))
        if side == "a":
            max_row = min(1, self.height - size.rows)
            row = 0 if size.rows >= 2 else max_row
        else:
            min_start = self.height - size.rows - 1
            row = max(min_start, self.height - size.rows)
        return Position(row=row, col=col)
