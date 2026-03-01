import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 500, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Eye + Hand Controlled Racing Game")

# Load assets
road = pygame.image.load("assets/Road.png")
road = pygame.transform.scale(road, (WIDTH, HEIGHT))

player_car = pygame.image.load("assets/car.png")
player_car = pygame.transform.scale(player_car, (60, 120))

enemy_car = pygame.image.load("assets/enemy_car.png")
enemy_car = pygame.transform.scale(enemy_car, (60, 120))

WHITE = (255, 255, 255)
FPS = 60
clock = pygame.time.Clock()

# Road boundaries - define the playable road area (where the white boundary lines are in the road image)
ROAD_LEFT = 50      # Left boundary where white line is in road image
ROAD_RIGHT = 450    # Right boundary where white line is in road image (500 - 50)
CAR_WIDTH = 60

def draw_game(player_x, player_y, enemies, score, action=None):
    """Draw all game elements and optional action overlay"""
    # Scrolling background: road_y set by caller (global 'road_y' assumed)
    try:
        y = int(draw_game.road_y)
    except Exception:
        y = 0
    screen.blit(road, (0, y))
    screen.blit(road, (0, y - HEIGHT))
    
    # Draw road boundaries (white lines matching the white lines in the road image)
    try:
        pygame.draw.line(screen, (255, 255, 255), (ROAD_LEFT, 0), (ROAD_LEFT, HEIGHT), 2)
        pygame.draw.line(screen, (255, 255, 255), (ROAD_RIGHT, 0), (ROAD_RIGHT, HEIGHT), 2)
    except Exception:
        pass
    
    screen.blit(player_car, (player_x, player_y))
    # draw all enemies
    for e in enemies:
        screen.blit(enemy_car, (e['x'], e['y']))

    # Debug: draw collision rectangles to visualize detection areas (requires significant overlap)
    try:
        player_rect_debug = pygame.Rect(player_x + 15, player_y + 25, 30, 70)
        pygame.draw.rect(screen, (0, 255, 255), player_rect_debug, 2)
        for e in enemies:
            enemy_rect_debug = pygame.Rect(e['x'] + 15, e['y'] + 25, 30, 70)
            pygame.draw.rect(screen, (255, 0, 255), enemy_rect_debug, 2)
    except Exception:
        pass

    # (Outlines removed - debug rectangles disabled)

    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # Action overlay
    if action:
        action_font = pygame.font.Font(None, 30)
        a_text = action_font.render(f"Action: {action}", True, (0, 255, 0))
        screen.blit(a_text, (10, 50))

    pygame.display.update()


def game_loop(get_action):
    """Main game loop; get_action() should return a tuple (hand_action, eye_action) where each is
    'LEFT','RIGHT','ACCELERATE','BRAKE', or None. Both are applied (combined) each frame."""
    car_x, car_y = WIDTH // 2 - 30, HEIGHT - 150
    # Player movement per frame (smaller = slower)
    car_speed = 5
    # Vertical movement speed (medium slower than horizontal)
    vert_speed = 2
    # Spawn enemy at x not too close to player
    def spawn_enemy_x(player_x):
        min_x = 50
        max_x = WIDTH - 100
        safe_distance = 100
        attempts = 0
        while attempts < 20:
            x = random.randint(min_x, max_x)
            if abs(x - player_x) >= safe_distance:
                return x
            attempts += 1
        return random.randint(min_x, max_x)

    # Create multiple enemies (2-3); default to 3 staggered vertically
    num_enemies = 3
    enemies = []
    start_y = -150
    gap = 200
    for i in range(num_enemies):
        enemies.append({'x': spawn_enemy_x(car_x), 'y': start_y - i * gap})
    # Base enemy speed (slower start)
    enemy_speed = 3
    score = 0
    running = True

    # Debug: print initial positions for player and enemies
    print(f"Game start: player=({car_x},{car_y}) enemies={[ (e['x'], e['y']) for e in enemies ]}")

    # debounce for gestures: require N consistent frames
    debounce_frames = 1
    last_action = None
    stable_count = 0
    frame_counter = 0
    # Scrolling background state
    draw_game.road_y = 0
    road_scroll_speed = 6

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Get live actions (hand, eye)
        hand_action, eye_action = get_action()

        # Debounce horizontal (LEFT/RIGHT) and vertical (ACCELERATE/BRAKE) separately
        horiz = hand_action if hand_action in ("LEFT", "RIGHT") else eye_action if eye_action in ("LEFT","RIGHT") else None
        vert = hand_action if hand_action in ("ACCELERATE", "BRAKE") else eye_action if eye_action in ("ACCELERATE","BRAKE") else None

        # Horizontal debounce
        if horiz == last_action:
            stable_count += 1
        else:
            stable_count = 1
            last_action = horiz
        applied_horiz = horiz if (horiz is not None and stable_count >= debounce_frames) else None

        # Vertical debounce (independent)
        # use simple immediate apply for vertical (or could use separate counters)
        applied_vert = vert

        # Apply horizontal
        if applied_horiz == "LEFT":
            car_x -= car_speed
        elif applied_horiz == "RIGHT":
            car_x += car_speed

        # Apply vertical using medium speed
        if applied_vert == "ACCELERATE":
            car_y -= vert_speed
        elif applied_vert == "BRAKE":
            car_y += vert_speed

        # Adjust speeds based on score (increase every 10 points)
        speed_tier = min(score // 10, 5)  # cap the tiers to avoid runaway speed
        enemy_speed = 3 + speed_tier  # increments by 1 per tier
        road_scroll_speed = 4 + speed_tier

        # Update enemies
        for e in enemies:
            e['y'] += enemy_speed
            if e['y'] > HEIGHT:
                # respawn above screen with safe x
                e['y'] = -150 - random.randint(0, 100)
                e['x'] = spawn_enemy_x(car_x)
                score += 1

        # Keep player within road boundaries
        # Car cannot go left of ROAD_LEFT or right of ROAD_RIGHT
        car_x = max(ROAD_LEFT, min(ROAD_RIGHT - CAR_WIDTH, car_x))
        car_y = max(0, min(HEIGHT - 120, car_y))

        # Check collision - requires cars to overlap significantly in the center
        # Smaller rectangles (30x70) ensure cars must touch substantially
        player_rect = pygame.Rect(car_x + 15, car_y + 25, 30, 70)
        # Check collision against all enemies
        collision = False
        for e in enemies:
            enemy_rect = pygame.Rect(e['x'] + 15, e['y'] + 25, 30, 70)
            if player_rect.colliderect(enemy_rect):
                # Print debug info and show a Game Over overlay instead of immediate close
                print("*** GAME OVER! Collision detected ***")
                print(f"player_rect={player_rect} enemy_rect={enemy_rect}")

                # Draw Game Over overlay
                font = pygame.font.Font(None, 72)
                go_text = font.render("GAME OVER", True, (255, 0, 0))
                screen.blit(go_text, (WIDTH // 2 - go_text.get_width() // 2, HEIGHT // 2 - 36))
                pygame.display.update()

                # Pause briefly so user can see it
                pygame.time.delay(2000)
                running = False
                collision = True
                break

        # update road scroll
        draw_game.road_y = (draw_game.road_y + road_scroll_speed) % HEIGHT

        # draw with action overlay (show applied action and raw)
        overlay_text = f"hand={hand_action} eye={eye_action} horiz={applied_horiz} vert={applied_vert} score={score} spd={enemy_speed}"
        draw_game(car_x, car_y, enemies, score, action=overlay_text)

        clock.tick(FPS)
        frame_counter += 1
        if frame_counter % FPS == 0:
            # print positions of first enemy for debugging
            first_enemy = enemies[0] if enemies else {'x':0,'y':0}
            print(f"DEBUG frame: player=({car_x},{car_y}) enemy=({first_enemy['x']},{first_enemy['y']}) hand={hand_action} eye={eye_action} horiz={applied_horiz} vert={applied_vert} score={score} spd={enemy_speed}")
    # return whether collision occurred and final score so caller can decide next action
    return collision, score
