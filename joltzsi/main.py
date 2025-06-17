import pygame
import sys
import random
import csv
from datetime import datetime
import os

pygame.init()

time_limits = {
    1: 30000, 2: 28000, 3: 26000, 4: 24000, 5: 22000, 6: 20000, 7: 18000,
    8: 16000, 9: 14000, 10: 12000, 11: 10000, 12: 9000, 13: 8000, 14: 7000,
    15: 6000, 16: 5000, 17: 4500, 18: 4000, 19: 3500, 20: 3000, 21: 2800,
    22: 2600, 23: 2400, 24: 2200, 25: 2000, 26: 1800, 27: 1600, 28: 1400,
}

default_time_limit = 1200  # Level 29 and up

# Constants
pieces_placed = 0
lines_cleared = 0
level = 1
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700
GRID_SIZE = 5
TILE_SIZE = 100
MARGIN = 5
NEXT_PIECE_AREA = 100
FPS = 60

# Colors
COLORS = {
    0: (30, 30, 30),       # Black
    1: (173, 216, 230),    # White-Blue
    2: (255, 0, 0),        # Red
    3: (0, 255, 255),      # Cyan
    4: (0, 255, 0)         # Green
}

HIGHLIGHT_COLOR = (255, 255, 0)

# Tetromino shapes
TETROMINOS = [
    [(0, 0), (1, 0), (0, 1), (1, 1)],  # O
    [(0, 0), (1, 0), (2, 0), (3, 0)],  # I
    [(0, 0), (0, 1), (1, 1), (2, 1)],  # J
    [(2, 0), (0, 1), (1, 1), (2, 1)],  # L
    [(1, 0), (2, 0), (0, 1), (1, 1)],  # S
    [(0, 0), (1, 0), (1, 1), (2, 1)],  # Z
    [(1, 0), (0, 1), (1, 1), (2, 1)]   # T
]

# Setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Joltzsi")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 40)

grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
score = 0

def save_score(score):
    filename = 'scores.csv'
    new_entry = [score, datetime.now().strftime('%Y-%m-%d %H:%M:%S')]

    # Load existing scores
    scores = []
    if os.path.exists(filename):
        with open(filename, 'r', newline='') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                scores.append([int(row[1]), row[2]])

    # Add new score
    scores.append(new_entry)

    # Sort by score descending
    scores.sort(key=lambda x: x[0], reverse=True)

    # Write back with ranks
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Rank', 'Score', 'Date'])
        for i, (s, d) in enumerate(scores, start=1):
            writer.writerow([i, s, d])

def random_piece():
    return [block[:] for block in random.choice(TETROMINOS)]

current_piece = random_piece()
next_piece = random_piece()

# Start in center
piece_x, piece_y = 2, 2

def draw_piece():
    for dx, dy in current_piece:
        x = piece_x + dx
        y = piece_y + dy
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            rect = pygame.Rect(
                x * (TILE_SIZE + MARGIN) + MARGIN,
                y * (TILE_SIZE + MARGIN) + MARGIN,
                TILE_SIZE, TILE_SIZE
            )
            # Use color based on hypothetical tile value 1 (or any you prefer)
            pygame.draw.rect(screen, (255, 255, 0), rect)  # Yellow fill
            pygame.draw.rect(screen, (0, 0, 0), rect, 2)   # Black border

def flash_screen():
    for _ in range(2):  # Flash twice
        screen.fill((255, 255, 255))
        pygame.display.update()
        pygame.time.delay(100)
        draw_grid()
        draw_piece()
        draw_next_piece()
        draw_score()
        pygame.display.update()
        pygame.time.delay(100)

def draw_grid():
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            value = grid[y][x]
            color = COLORS.get(value, (255, 255, 255))  # If value > 4, show white
            rect = pygame.Rect(x * (TILE_SIZE + MARGIN) + MARGIN,
                               y * (TILE_SIZE + MARGIN) + MARGIN,
                               TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, color, rect)
            if 1 <= value <= 4:
                text = font.render(str(value), True, (0, 0, 0))
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)

def draw_next_piece():
    label = font.render("Next:", True, (255, 255, 255))
    screen.blit(label, (20, SCREEN_HEIGHT - NEXT_PIECE_AREA + 20))
    for dx, dy in next_piece:
        rect = pygame.Rect(150 + dx * (TILE_SIZE // 2 + 5),
                           SCREEN_HEIGHT - NEXT_PIECE_AREA + 20 + dy * (TILE_SIZE // 2 + 5),
                           TILE_SIZE // 2, TILE_SIZE // 2)
        pygame.draw.rect(screen, (200, 200, 200), rect)

def can_place(piece, grid_x, grid_y):
    for dx, dy in piece:
        x = grid_x + dx
        y = grid_y + dy
        if x < 0 or x >= GRID_SIZE or y < 0 or y >= GRID_SIZE:
            return False
    return True

def place_piece(piece, grid_x, grid_y):
    global score, current_piece, next_piece, piece_timer, piece_time_limit

    # Calculate remaining time in milliseconds
    now = pygame.time.get_ticks()
    elapsed = now - piece_timer
    remaining_ms = max(piece_time_limit - elapsed, 0)

    # Add points = remaining time in seconds * 10
    points_to_add = int((remaining_ms/(elapsed + remaining_ms)) * 20)
    score += points_to_add

    # Place blocks on the grid
    for dx, dy in piece:
        x = grid_x + dx
        y = grid_y + dy
        grid[y][x] += 1
        if grid[y][x] > 4:
            return False  # Game over

    score += 1  # existing +1 point for placing a piece

    check_lines()

    current_piece = next_piece
    next_piece = random_piece()

    # Reset timer for next piece
    piece_timer = pygame.time.get_ticks()

    return True


def check_lines():
    global score
    global level
    rows_to_clear = set()
    cols_to_clear = set()
    rows_values = []
    cols_values = []

    # Check rows
    for y in range(GRID_SIZE):
        value = grid[y][0]
        if value in [1, 2, 3, 4] and all(grid[y][x] == value for x in range(GRID_SIZE)):
            rows_to_clear.add(y)
            rows_values.append(value)

    # Check columns
    for x in range(GRID_SIZE):
        value = grid[0][x]
        if value in [1, 2, 3, 4] and all(grid[y][x] == value for y in range(GRID_SIZE)):
            cols_to_clear.add(x)
            cols_values.append(value)

    rows_cleared = len(rows_to_clear)
    cols_cleared = len(cols_to_clear)

    if rows_cleared > 0 or cols_cleared > 0:
        # Score tables (single line clear score)
        score_table = {
            1: [10, 40, 100, 300],
            2: [40, 100, 300, 1200],
            3: [100, 300, 1200, 6400],
            4: [300, 1200, 6400, 11200]
        }

        # Helper function to get score for lines cleared and tile value
        def line_score(tile_value, lines_cleared):
            # Clamp lines_cleared to 4 max index for score_table
            lines = min(lines_cleared, 4)
            return score_table[lines][tile_value - 1]

        # Calculate total score for rows and columns separately
        rows_score = sum(line_score(val, rows_cleared) for val in rows_values)
        cols_score = sum(line_score(val, cols_cleared) for val in cols_values)

        if rows_cleared > 0 and cols_cleared > 0:
            # Apply the special formula if both rows and cols cleared in same move
            score += (rows_score * (cols_cleared+1) + cols_score * (rows_cleared+1))*level
        else:
            # Otherwise just add the sum
            score += (rows_score + cols_score)*level

        # Flash on special case
        if 4 in rows_values + cols_values and (rows_cleared + cols_cleared) >= 4:
            flash_screen()

        # Clear rows
        # Animate clearing rows from center outwards
        if rows_to_clear:
            steps = GRID_SIZE // 2 + 1
            for step in range(steps):
                for y in rows_to_clear:
                    for offset in [-step, step]:
                        x = GRID_SIZE // 2 + offset
                        if 0 <= x < GRID_SIZE:
                            grid[y][x] = 0
                screen.fill((50, 50, 50))
                draw_grid()
                draw_next_piece()
                draw_score()
                draw_highlight(current_piece, piece_x, piece_y)
                pygame.display.flip()
                pygame.time.delay(100)

        # Animate clearing columns from center outwards
        if cols_to_clear:
            steps = GRID_SIZE // 2 + 1
            for step in range(steps):
                for x in cols_to_clear:
                    for offset in [-step, step]:
                        y = GRID_SIZE // 2 + offset
                        if 0 <= y < GRID_SIZE:
                            grid[y][x] = 0
                screen.fill((50, 50, 50))
                draw_grid()
                draw_next_piece()
                draw_score()
                draw_highlight(current_piece, piece_x, piece_y)
                pygame.display.flip()
                pygame.time.delay(100)
    # Track lines cleared and level up
    cleared_now = len(rows_to_clear) + len(cols_to_clear)
    if cleared_now > 0:
        global lines_cleared, game_over
        lines_cleared += cleared_now
        if lines_cleared // 10 + 1 > level:
            level += 1
            if level >= 256:
                game_over = True


def draw_score():
    text = font.render(
        f"Score: {score}  Level: {level}  Lines: {lines_cleared}  Pieces: {pieces_placed}",
        True,
        (255, 255, 255)
    )
    screen.blit(text, (SCREEN_WIDTH - 550, SCREEN_HEIGHT - NEXT_PIECE_AREA + 20))



def draw_game_over():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    text = font.render(f"Game Over! Score: {score} Level: {level}", True, (255, 0, 0))
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(text, text_rect)


def draw_highlight(piece, grid_x, grid_y):
    if not can_place(piece, grid_x, grid_y):
        return
    for dx, dy in piece:
        x = grid_x + dx
        y = grid_y + dy
        rect = pygame.Rect(x * (TILE_SIZE + MARGIN) + MARGIN,
                           y * (TILE_SIZE + MARGIN) + MARGIN,
                           TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(screen, HIGHLIGHT_COLOR, rect, 5)

def rotate_piece(piece):
    return [(-dy, dx) for dx, dy in piece]

def draw_timer_bar():
    global piece_time_limit, piece_timer, score

    now = pygame.time.get_ticks()
    elapsed = now - piece_timer
    remaining = max(piece_time_limit - elapsed, 0)

    # Add 1 point for every 100ms passed before the timer ends
    # Calculate how many 100ms intervals have passed since last check
    intervals_passed = elapsed // 100
    if not hasattr(draw_timer_bar, "last_intervals"):
        draw_timer_bar.last_intervals = 0

    # Add points only for new intervals
    new_intervals = intervals_passed - draw_timer_bar.last_intervals
    if new_intervals > 0 and remaining > 0:
        draw_timer_bar.last_intervals = intervals_passed

    bar_width = SCREEN_WIDTH - 2 * MARGIN
    bar_height = 20
    fill_width = int(bar_width * (remaining / piece_time_limit)) if piece_time_limit > 0 else 0

    bg_rect = pygame.Rect(MARGIN, SCREEN_HEIGHT - NEXT_PIECE_AREA - 30, bar_width, bar_height)
    pygame.draw.rect(screen, (80, 80, 80), bg_rect)

    if remaining > piece_time_limit / 2:
        color = (0, 255, 0)
    elif remaining > piece_time_limit / 4:
        color = (255, 165, 0)
    else:
        color = (255, 0, 0)

    fill_rect = pygame.Rect(MARGIN, SCREEN_HEIGHT - NEXT_PIECE_AREA - 30, fill_width, bar_height)
    pygame.draw.rect(screen, color, fill_rect)

    # Show time with one decimal place in seconds, e.g. 4.5
    seconds = remaining / 1000
    time_text = f"Time: {seconds:.1f}s"
    text = font.render(time_text, True, (255, 255, 255))
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - NEXT_PIECE_AREA - 20))
    screen.blit(text, text_rect)

def main():
    global piece_x, piece_y, current_piece, piece_timer, piece_time_limit, level, pieces_placed
    running = True
    game_over = False
    is_saved = False

    piece_timer = pygame.time.get_ticks()  # Start timer for first piece

    # Initialize piece_time_limit based on starting level
    if level in time_limits:
        piece_time_limit = time_limits[level]
    else:
        piece_time_limit = default_time_limit

    while running:
        screen.fill((50, 50, 50))
        draw_grid()
        draw_next_piece()
        draw_score()
        draw_highlight(current_piece, piece_x, piece_y)
        draw_timer_bar()

        if game_over:
            draw_game_over()
            if is_saved == False:
                save_score(score)
                is_saved = True

        pygame.display.flip()
        clock.tick(FPS)

        # Update time limit based on current level
        if level in time_limits:
            piece_time_limit = time_limits[level]
        else:
            piece_time_limit = default_time_limit

        # Force place piece if time runs out
        if not game_over:
            if pygame.time.get_ticks() - piece_timer >= piece_time_limit:
                if can_place(current_piece, piece_x, piece_y):
                    if not place_piece(current_piece, piece_x, piece_y):
                        game_over = True
                    pieces_placed += 1
                    level = pieces_placed // 10 + 1
                    if level >= 256:
                        game_over = True
                    if current_piece == [(0, 0), (1, 0), (2, 0), (3, 0)]:  # Line piece
                        piece_x, piece_y = 0, 2
                    else:
                        piece_x, piece_y = 2, 2
                    piece_timer = pygame.time.get_ticks()
                else:
                    game_over = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if not game_over:
                    if event.key == pygame.K_LEFT:
                        if can_place(current_piece, piece_x - 1, piece_y):
                            piece_x -= 1
                    if event.key == pygame.K_RIGHT:
                        if can_place(current_piece, piece_x + 1, piece_y):
                            piece_x += 1
                    if event.key == pygame.K_UP:
                        if can_place(current_piece, piece_x, piece_y - 1):
                            piece_y -= 1
                    if event.key == pygame.K_DOWN:
                        if can_place(current_piece, piece_x, piece_y + 1):
                            piece_y += 1
                    if event.key == pygame.K_z:
                        rotated = rotate_piece(current_piece)
                        if can_place(rotated, piece_x, piece_y):
                            current_piece = rotated

                if event.key == pygame.K_SPACE and not game_over:
                    if can_place(current_piece, piece_x, piece_y):
                        if not place_piece(current_piece, piece_x, piece_y):
                            game_over = True
                        pieces_placed += 1
                        level = pieces_placed // 10 + 1
                        if level >= 256:
                            game_over = True
                        if current_piece == [(0, 0), (1, 0), (2, 0), (3, 0)]:  # Line piece
                            piece_x, piece_y = 0, 2
                        else:
                            piece_x, piece_y = 2, 2
                        piece_timer = pygame.time.get_ticks()  # Reset timer for new piece

if __name__ == "__main__":
    main()
