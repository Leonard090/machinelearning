import pygame
import random
import sys
import csv
import os
from datetime import datetime

# Initialize Pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 600
BLOCK_SIZE = 30
COLUMNS = 10
ROWS = SCREEN_HEIGHT // BLOCK_SIZE

NES_SPEEDS = {
    0: 800, 1: 720, 2: 630, 3: 550, 4: 470,
    5: 380, 6: 300, 7: 220, 8: 130, 9: 100,
    10: 80, 11: 80, 12: 80, 13: 70, 14: 70, 15: 70,
    16: 50, 17: 50, 18: 50, 19: 30, 20: 30, 21: 30,
    22: 20, 23: 20, 24: 20, 25: 20, 26: 20, 27: 20, 28: 20, 29: 20
}


# Colors
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
COLORS = [
    (0, 255, 255),  # Cyan
    (0, 0, 255),    # Blue
    (255, 165, 0),  # Orange
    (255, 255, 0),  # Yellow
    (0, 255, 0),    # Green
    (160, 32, 240), # Purple
    (255, 0, 0)     # Red
]

# Tetromino shapes
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[2, 0, 0], [2, 2, 2]],  # J
    [[0, 0, 3], [3, 3, 3]],  # L
    [[4, 4], [4, 4]],  # O
    [[0, 5, 5], [5, 5, 0]],  # S
    [[0, 6, 0], [6, 6, 6]],  # T
    [[7, 7, 0], [0, 7, 7]]   # Z
]

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tetris")

clock = pygame.time.Clock()
base_fall_speed = 1000  # milliseconds

font = pygame.font.SysFont("Arial", 24)

class Tetromino:
    def __init__(self, shape, type_id):
        self.shape = shape
        self.type_id = type_id
        self.color = COLORS[type_id]  # Direct color assignment by type
        self.x = COLUMNS // 2 - len(shape[0]) // 2
        self.y = 0

    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

    def collision(self, grid, dx=0, dy=0):
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = self.x + x + dx
                    new_y = self.y + y + dy
                    if new_x < 0 or new_x >= COLUMNS or new_y >= ROWS:
                        return True
                    if new_y >= 0 and grid[new_y][new_x]:
                        return True
        return False

    def lock(self, grid):
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    grid[self.y + y][self.x + x] = cell

def save_score(score):
    filename = 'tetris_scores.csv'
    file_exists = os.path.isfile(filename)

    scores = []
    # Read existing scores to calculate rank
    if file_exists:
        with open(filename, 'r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                scores.append(int(row['Score']))

    # Determine rank (higher scores are better)
    rank = 1
    for s in scores:
        if s > score:
            rank += 1

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(filename, 'a', newline='') as file:
        fieldnames = ['Rank', 'Score', 'Date']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({'Rank': rank, 'Score': score, 'Date': current_time})

def get_nes_speed(level):
    return NES_SPEEDS.get(level, 20)

def create_grid():
    return [[0 for _ in range(COLUMNS)] for _ in range(ROWS)]

def draw_grid(surface, grid):
    surface.fill(BLACK)
    for y in range(ROWS):
        for x in range(COLUMNS):
            if grid[y][x]:
                color = COLORS[grid[y][x] - 1]
                pygame.draw.rect(surface, color, (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
    for x in range(COLUMNS):
        pygame.draw.line(surface, GRAY, (x * BLOCK_SIZE, 0), (x * BLOCK_SIZE, SCREEN_HEIGHT))
    for y in range(ROWS):
        pygame.draw.line(surface, GRAY, (0, y * BLOCK_SIZE), (COLUMNS * BLOCK_SIZE, y * BLOCK_SIZE))

def draw_tetromino(surface, tetromino):
    for y, row in enumerate(tetromino.shape):
        for x, cell in enumerate(row):
            if cell:
                pygame.draw.rect(
                    surface, tetromino.color,
                    ((tetromino.x + x) * BLOCK_SIZE, (tetromino.y + y) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                )

def clear_lines(grid):
    new_grid = []
    cleared_lines = []

    # Go from bottom to top and keep rows that are not full
    for y in range(ROWS):
        if all(cell != 0 for cell in grid[y]):
            cleared_lines.append(y)  # Store the cleared line indices
        else:
            new_grid.append(grid[y])  # Keep non-full rows

    # Add empty rows at the top to maintain grid size
    while len(new_grid) < ROWS:
        new_grid.insert(0, [0 for _ in range(COLUMNS)])

    return new_grid, len(cleared_lines), cleared_lines

def draw_sidebar(surface, score, lines, level, next_piece):
    sidebar = pygame.Surface((200, SCREEN_HEIGHT))
    sidebar.fill(BLACK)

    score_text = font.render(f"Score: {score}", True, WHITE)
    lines_text = font.render(f"Lines: {lines}", True, WHITE)
    level_text = font.render(f"Level: {level}", True, WHITE)
    next_text = font.render("Next:", True, WHITE)

    sidebar.blit(score_text, (10, 30))
    sidebar.blit(lines_text, (10, 60))
    sidebar.blit(level_text, (10, 90))
    sidebar.blit(next_text, (10, 120))

    for y, row in enumerate(next_piece.shape):
        for x, cell in enumerate(row):
            if cell:
                pygame.draw.rect(
                    sidebar, next_piece.color,
                    (10 + x * BLOCK_SIZE, 150 + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                )

    surface.blit(sidebar, (COLUMNS * BLOCK_SIZE, 0))

def draw_ghost_piece(surface, grid, tetromino):
    # Create ghost with the same type_id and shape
    ghost = Tetromino(tetromino.shape, tetromino.type_id)
    ghost.x = tetromino.x
    ghost.y = tetromino.y
    ghost.color = (200, 200, 200)  # Light gray ghost color for ghost piece

    # Drop the ghost as far as possible
    while not ghost.collision(grid, dy=1):
        ghost.y += 1

    # Draw the ghost as an outline
    for y, row in enumerate(ghost.shape):
        for x, cell in enumerate(row):
            if cell:
                pygame.draw.rect(
                    surface, ghost.color,
                    ((ghost.x + x) * BLOCK_SIZE, (ghost.y + y) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE),
                    1  # Outline only for ghost
                )


def spawn_piece():
    index = random.randint(0, len(SHAPES) - 1)
    return Tetromino([row[:] for row in SHAPES[index]], index)

def find_cleared_lines(grid):
    return [y for y, row in enumerate(grid) if all(row)]

def flash_lines(screen, grid, lines_to_clear):
    flash_time = 200  # milliseconds per flash
    flash_cycles = 3  # number of flash cycles

    for _ in range(flash_cycles):
        # Draw white lines
        for y in lines_to_clear:
            for x in range(COLUMNS):
                pygame.draw.rect(screen, WHITE, (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
        pygame.display.update()
        pygame.time.wait(flash_time // 2)

        # Redraw original grid
        draw_grid(screen, grid)
        pygame.display.update()
        pygame.time.wait(flash_time // 2)

def animate_line_clear(surface, grid, cleared_lines):
    if not cleared_lines:
        return

    flash_border = len(cleared_lines) == 4  # Tetris = 4 lines
    mid = COLUMNS // 2
    steps = mid + 1
    delay = 50  # ms per step

    # Animate disappearing blocks from middle outwards
    for step in range(steps):
        temp_grid = [row[:] for row in grid]  # Copy grid for safe drawing

        for line in cleared_lines:
            left_idx = mid - step
            right_idx = mid + step
            if 0 <= left_idx < COLUMNS:
                temp_grid[line][left_idx] = 0
            if 0 <= right_idx < COLUMNS and right_idx != left_idx:
                temp_grid[line][right_idx] = 0

        draw_grid(surface, temp_grid)
        pygame.display.update()
        pygame.time.delay(delay)

    # Flash border if Tetris
    if flash_border:
        for _ in range(2):
            pygame.draw.rect(surface, WHITE, (0, 0, COLUMNS * BLOCK_SIZE, ROWS * BLOCK_SIZE), 5)
            pygame.display.update()
            pygame.time.delay(150)
            draw_grid(surface, grid)
            pygame.display.update()
            pygame.time.delay(150)

def main():
    is_saved = False
    grid = create_grid()
    current_piece = spawn_piece()
    next_piece = spawn_piece()
    fall_time = 0
    game_over = False
    score = 0
    lines_cleared = 0
    level = 1

    move_left = False
    move_right = False
    move_down = False

    move_delay = 100  # Delay between auto moves when holding (ms)
    move_timer = 0
    down_move_timer = 0

    while True:
        if game_over:
            pygame.display.set_caption(f"Tetris - Game Over! Final Score: {score}")
            save_score(score)
            pygame.time.wait(5000)  # pause 5 seconds so user can see final screen
            return

        if level >= 256:
            level = 1

        dt = clock.tick(60)
        fall_time += dt
        move_timer += dt
        down_move_timer += dt

        fall_speed = get_nes_speed(level)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if not current_piece.collision(grid, dx=-1):
                        current_piece.x -= 1
                    move_left = True
                    move_timer = 0  # Reset hold timer

                if event.key == pygame.K_RIGHT:
                    if not current_piece.collision(grid, dx=1):
                        current_piece.x += 1
                    move_right = True
                    move_timer = 0  # Reset hold timer

                if event.key == pygame.K_DOWN:
                    if not current_piece.collision(grid, dy=1):
                        current_piece.y += 1
                        score += 1
                    move_down = True
                    down_move_timer = 0

                if event.key == pygame.K_UP:
                    original_shape = current_piece.shape
                    current_piece.rotate()
                    if current_piece.collision(grid):
                        current_piece.shape = original_shape

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    move_left = False
                if event.key == pygame.K_RIGHT:
                    move_right = False
                if event.key == pygame.K_DOWN:
                    move_down = False

        # Handle held key movement
        if move_left and move_timer > move_delay:
            if not current_piece.collision(grid, dx=-1):
                current_piece.x -= 1
            move_timer = 0

        if move_right and move_timer > move_delay:
            if not current_piece.collision(grid, dx=1):
                current_piece.x += 1
            move_timer = 0

        if move_down and down_move_timer > move_delay:
            if not current_piece.collision(grid, dy=1):
                current_piece.y += 1
                score += 1
            down_move_timer = 0

        # Handle automatic falling
        if fall_time > fall_speed:
            fall_time = 0
            if not current_piece.collision(grid, dy=1):
                current_piece.y += 1
            else:
                current_piece.lock(grid)

                # Clear lines with animation
                grid, cleared, cleared_lines = clear_lines(grid)
                if cleared > 0:
                    animate_line_clear(screen, grid, cleared_lines)

                lines_cleared += cleared

                if cleared == 1:
                    score += 40 * level
                elif cleared == 2:
                    score += 100 * level
                elif cleared == 3:
                    score += 300 * level
                elif cleared == 4:
                    score += 1200 * level

                if cleared:
                    level = lines_cleared // 10 + 1

                current_piece = next_piece
                next_piece = spawn_piece()

                if current_piece.collision(grid):
                    game_over = True

        # Drawing
        draw_grid(screen, grid)
        draw_ghost_piece(screen, grid, current_piece)
        draw_tetromino(screen, current_piece)
        draw_sidebar(screen, score, lines_cleared, level, next_piece)
        pygame.display.update()


if __name__ == "__main__":
    main()