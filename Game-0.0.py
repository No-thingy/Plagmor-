import pygame
import random
import sys
import json
import os
import math

pygame.init()

settings = {
    'volume': 60,
    'difficulty': 1,
    'resolution': (800, 600),
    'fullscreen': False
}


def load_settings():
    global settings
    try:
        with open('settings.json', 'r') as f:
            loaded_settings = json.load(f)
            if 'resolution' not in loaded_settings:
                loaded_settings['resolution'] = settings['resolution']
            if 'fullscreen' not in loaded_settings:
                loaded_settings['fullscreen'] = settings['fullscreen']
            settings.update(loaded_settings)
            settings['resolution'] = tuple(settings['resolution'])
    except FileNotFoundError:
        save_settings()


def save_settings():
    with open('settings.json', 'w') as f:
        json.dump(settings, f)


def set_resolution(width, height, fullscreen=False):
    global WIDTH, HEIGHT, screen
    WIDTH, HEIGHT = width, height
    if fullscreen:
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
    settings['resolution'] = (WIDTH, HEIGHT)
    settings['fullscreen'] = fullscreen
    save_settings()


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
DARK_GRAY = (40, 40, 40)

font = pygame.font.Font(None, 36)

pygame.mixer.init()
attack_sound = pygame.mixer.Sound("attack.wav") if os.path.exists("attack.wav") else None
artifact_sound = pygame.mixer.Sound("artifact.wav") if os.path.exists("artifact.wav") else None
background_music = pygame.mixer.Sound("background.mp3") if os.path.exists("background.mp3") else None

background_image = pygame.image.load("background.jpg") if os.path.exists("background.jpg") else None


class Decor(pygame.sprite.Sprite):
    def __init__(self, decor_type="rock"):
        super().__init__()
        self.type = decor_type
        self.animation_frame = 0
        if decor_type == "rock":
            self.image = pygame.Surface((25, 25), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (100, 100, 100), (12, 12), 10)
            pygame.draw.circle(self.image, (80, 80, 80), (15, 10), 5)
        elif decor_type == "grass":
            self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, (50, 200, 50), [(10, 20), (5, 10), (15, 5), (10, 0)])
        elif decor_type == "particle":
            self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (200, 200, 50), (4, 4), 3)
            self.speed = random.uniform(0.5, 2.0)
        self.rect = self.image.get_rect(center=(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        self.angle = 0

    def update(self):
        if self.type == "particle":
            self.angle += self.speed
            self.rect.x += math.cos(self.angle) * 0.5
            self.rect.y += math.sin(self.angle) * 0.5
            alpha = 100 + int(math.sin(self.angle * 2) * 50)
            self.image.set_alpha(abs(alpha))
        if self.rect.left > WIDTH: self.rect.right = 0
        if self.rect.right < 0: self.rect.left = WIDTH
        if self.rect.top > HEIGHT: self.rect.bottom = 0
        if self.rect.bottom < 0: self.rect.top = HEIGHT


class Player(pygame.sprite.Sprite):
    def __init__(self, image_path="player.png"):
        super().__init__()
        if os.path.exists(image_path):
            self.image = pygame.image.load(image_path)
        else:
            self.image = pygame.Surface((30, 30))
            self.image.fill(GREEN)
        self.image = pygame.transform.scale(self.image, (30, 30))
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.health = 100
        self.max_health = 100
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 100
        self.damage = 10
        self.sword_level = 1
        self.attack_cooldown = 0
        self.max_cooldown = 30

    def update(self, keys):
        if keys[pygame.K_LEFT]: self.rect.x -= 5
        if keys[pygame.K_RIGHT]: self.rect.x += 5
        if keys[pygame.K_UP]: self.rect.y -= 5
        if keys[pygame.K_DOWN]: self.rect.y += 5
        if self.rect.left > WIDTH: self.rect.right = 0
        if self.rect.right < 0: self.rect.left = WIDTH
        if self.rect.top > HEIGHT: self.rect.bottom = 0
        if self.rect.bottom < 0: self.rect.top = HEIGHT
        if self.attack_cooldown > 0: self.attack_cooldown -= 1

    def attack(self, enemies):
        if self.attack_cooldown <= 0:
            self.attack_cooldown = self.max_cooldown
            if attack_sound: attack_sound.play()
            for enemy in enemies:
                if self.rect.colliderect(enemy.rect):
                    enemy.health -= self.damage
                    if enemy.health <= 0:
                        enemy.kill()
                        self.gain_experience(10)

    def gain_experience(self, amount):
        self.experience += amount
        if self.experience >= self.experience_to_next_level:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.experience = 0
        self.experience_to_next_level = int(self.experience_to_next_level * 1.5)
        self.max_health += 20
        self.health = self.max_health
        self.damage += 5
        show_dialog(f"Вы достигли уровня {self.level}!")

    def upgrade_sword(self):
        self.sword_level += 1
        self.damage += 5


class Enemy(pygame.sprite.Sprite):
    def __init__(self, difficulty):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        self.health = 20 * difficulty
        self.damage = 5 * difficulty
        self.animation_frame = 0

    def update(self):
        self.rect.x += random.randint(-2, 2)
        self.rect.y += random.randint(-2, 2)
        self.animation_frame += 1
        if self.animation_frame % 10 == 0:
            self.image.fill(ORANGE if self.image.get_at((0, 0)) == RED else RED)
        if self.rect.left > WIDTH: self.rect.right = 0
        if self.rect.right < 0: self.rect.left = WIDTH
        if self.rect.top > HEIGHT: self.rect.bottom = 0
        if self.rect.bottom < 0: self.rect.top = HEIGHT


class Artifact(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(center=(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        self.angle = 0

    def update(self):
        self.angle += 5
        if self.angle >= 360: self.angle = 0
        self.image = pygame.transform.rotate(pygame.Surface((20, 20)), self.angle)
        self.image.fill(BLUE)
        if self.rect.left > WIDTH: self.rect.right = 0
        if self.rect.right < 0: self.rect.left = WIDTH
        if self.rect.top > HEIGHT: self.rect.bottom = 0
        if self.rect.bottom < 0: self.rect.top = HEIGHT


class ShopItem:
    def __init__(self, name, cost, effect):
        self.name = name
        self.cost = cost
        self.effect = effect

    def apply(self, player):
        if player.level >= self.cost:
            player.level -= self.cost
            self.effect(player)
            return True
        return False


class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.x + WIDTH // 2
        y = -target.rect.y + HEIGHT // 2
        self.camera = pygame.Rect(x, y, self.width, self.height)


def show_shop(player):
    shop_items = [
        ShopItem("Улучшение меча (+5 урона)", 5, lambda p: p.upgrade_sword()),
        ShopItem("Увеличение здоровья (+20 HP)", 3, lambda p: setattr(p, 'health', min(p.health + 20, p.max_health))),
        ShopItem("Увеличение уровня (+1)", 10, lambda p: setattr(p, 'level', p.level + 1))
    ]
    selected_option = 0
    while True:
        screen.fill(BLACK)
        for i, item in enumerate(shop_items):
            color = WHITE if i == selected_option else RED
            text_surface = font.render(f"{item.name} - {item.cost} уровней", True, color)
            screen.blit(text_surface, (WIDTH // 2 - 200, HEIGHT // 2 + i * 50 - 100))
        text_surface = font.render(f"Ваши уровни: {player.level}", True, WHITE)
        screen.blit(text_surface, (WIDTH // 2 - 100, HEIGHT // 2 + len(shop_items) * 50 - 50))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(shop_items)
                if event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(shop_items)
                if event.key == pygame.K_RETURN:
                    if shop_items[selected_option].apply(player):
                        show_dialog("Покупка совершена!")
                    else:
                        show_dialog("Недостаточно уровней!")
                    return
                if event.key == pygame.K_ESCAPE:
                    return


def show_dialog(text):
    dialog_box = pygame.Surface((600, 100))
    dialog_box.fill(WHITE)
    text_surface = font.render(text, True, BLACK)
    dialog_box.blit(text_surface, (50, 30))
    screen.blit(dialog_box, (100, HEIGHT - 150))
    pygame.display.flip()
    pygame.time.wait(2000)


def draw_health_bar(player):
    health_width = 200
    health_height = 20
    filled_width = (player.health / player.max_health) * health_width
    pygame.draw.rect(screen, RED, (10, 10, health_width, health_height))
    pygame.draw.rect(screen, GREEN, (10, 10, filled_width, health_height))


def draw_level_indicator(player):
    level_text = font.render(f"Уровень: {player.level}", True, WHITE)
    screen.blit(level_text, (10, 40))


def draw_experience_bar(player):
    experience_width = 200
    experience_height = 10
    filled_width = (player.experience / player.experience_to_next_level) * experience_width
    pygame.draw.rect(screen, BLUE, (10, 70, experience_width, experience_height))
    pygame.draw.rect(screen, YELLOW, (10, 70, filled_width, experience_height))


def show_pause_menu():
    pause_options = ["Продолжить", "Выйти в меню", "Выйти из игры"]
    selected_option = 0
    while True:
        screen.fill(BLACK)
        for i, option in enumerate(pause_options):
            color = WHITE if i == selected_option else RED
            text_surface = font.render(option, True, color)
            screen.blit(text_surface, (WIDTH // 2 - 100, HEIGHT // 2 + i * 50 - 50))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(pause_options)
                if event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(pause_options)
                if event.key == pygame.K_RETURN:
                    return selected_option


def save_progress(player):
    progress = {
        'level': player.level,
        'health': player.health,
        'damage': player.damage,
        'sword_level': player.sword_level,
        'experience': player.experience,
        'experience_to_next_level': player.experience_to_next_level
    }
    with open('progress.json', 'w') as f:
        json.dump(progress, f)


def load_progress(player):
    try:
        with open('progress.json', 'r') as f:
            progress = json.load(f)
            player.level = progress['level']
            player.health = progress['health']
            player.damage = progress['damage']
            player.sword_level = progress['sword_level']
            player.experience = progress['experience']
            player.experience_to_next_level = progress['experience_to_next_level']
    except FileNotFoundError:
        pass


def show_menu():
    menu_options = ["Начать игру", "Настройки", "Магазин", "Выход"]
    selected_option = 0
    while True:
        screen.fill(BLACK)
        for i, option in enumerate(menu_options):
            color = WHITE if i == selected_option else RED
            text_surface = font.render(option, True, color)
            screen.blit(text_surface, (WIDTH // 2 - 100, HEIGHT // 2 + i * 50 - 50))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(menu_options)
                if event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(menu_options)
                if event.key == pygame.K_RETURN:
                    return selected_option


def show_settings():
    settings_options = [
        "Громкость: " + str(settings['volume']),
        "Сложность: " + str(settings['difficulty']),
        "Разрешение: " + str(settings['resolution'][0]) + "x" + str(settings['resolution'][1]),
        "Полный экран: " + ("Вкл" if settings['fullscreen'] else "Выкл"),
        "Назад"
    ]
    selected_option = 0
    while True:
        screen.fill(BLACK)
        for i, option in enumerate(settings_options):
            color = WHITE if i == selected_option else RED
            text_surface = font.render(option, True, color)
            screen.blit(text_surface, (WIDTH // 2 - 150, HEIGHT // 2 + i * 50 - 100))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(settings_options)
                if event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(settings_options)
                if event.key == pygame.K_RETURN:
                    if selected_option == 0:
                        settings['volume'] = (settings['volume'] + 10) % 110
                        settings_options[0] = "Громкость: " + str(settings['volume'])
                    elif selected_option == 1:
                        settings['difficulty'] = 3 - settings['difficulty']
                        settings_options[1] = "Сложность: " + str(settings['difficulty'])
                    elif selected_option == 2:
                        resolutions = [
                            (800, 600),
                            (1024, 768),
                            (1280, 720),
                            (1366, 768),
                            (1600, 900),
                            (1920, 1080)
                        ]
                        current_index = resolutions.index(settings['resolution'])
                        new_index = (current_index + 1) % len(resolutions)
                        set_resolution(*resolutions[new_index], settings['fullscreen'])
                        settings_options[2] = "Разрешение: " + str(settings['resolution'][0]) + "x" + str(
                            settings['resolution'][1])
                    elif selected_option == 3:
                        settings['fullscreen'] = not settings['fullscreen']
                        set_resolution(*settings['resolution'], settings['fullscreen'])
                        settings_options[3] = "Полный экран: " + ("Вкл" if settings['fullscreen'] else "Выкл")
                    elif selected_option == 4:
                        save_settings()
                        return


def show_game_over():
    game_over_options = ["Играть снова", "Выйти в меню", "Выйти из игры"]
    selected_option = 0
    while True:
        screen.fill(BLACK)
        text_surface = font.render("Вы проиграли!", True, RED)
        screen.blit(text_surface, (WIDTH // 2 - 100, HEIGHT // 2 - 50))
        for i, option in enumerate(game_over_options):
            color = WHITE if i == selected_option else RED
            text_surface = font.render(option, True, color)
            screen.blit(text_surface, (WIDTH // 2 - 100, HEIGHT // 2 + i * 50))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(game_over_options)
                if event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(game_over_options)
                if event.key == pygame.K_RETURN:
                    return selected_option


def draw_cooldown_bar(player):
    if player.attack_cooldown > 0:
        cooldown_width = 200
        cooldown_height = 20
        filled_width = (player.max_cooldown - player.attack_cooldown) / player.max_cooldown * cooldown_width
        pygame.draw.rect(screen, RED, (WIDTH // 2 - cooldown_width // 2, HEIGHT - 50, cooldown_width, cooldown_height))
        pygame.draw.rect(screen, GREEN, (WIDTH // 2 - cooldown_width // 2, HEIGHT - 50, filled_width, cooldown_height))


def main():
    clock = pygame.time.Clock()
    player = Player()
    load_progress(player)
    difficulty = settings['difficulty']
    enemies = pygame.sprite.Group()
    artifacts = pygame.sprite.Group()
    decor = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)

    for _ in range(15):
        rock = Decor("rock")
        decor.add(rock)
        all_sprites.add(rock)

    for _ in range(10):
        grass = Decor("grass")
        decor.add(grass)
        all_sprites.add(grass)

    for _ in range(30):
        particle = Decor("particle")
        decor.add(particle)
        all_sprites.add(particle)

    for _ in range(5):
        enemy = Enemy(difficulty)
        enemies.add(enemy)
        all_sprites.add(enemy)

    for _ in range(3):
        artifact = Artifact()
        artifacts.add(artifact)
        all_sprites.add(artifact)

    camera = Camera(WIDTH, HEIGHT)

    running = True
    wave = 1
    artifact_respawn_time = 0

    if background_music:
        background_music.play(-1)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_progress(player)
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.attack(enemies)
                if event.key == pygame.K_ESCAPE:
                    selected_option = show_pause_menu()
                    if selected_option == 1:
                        return
                    elif selected_option == 2:
                        pygame.quit()
                        sys.exit()

        keys = pygame.key.get_pressed()
        player.update(keys)
        enemies.update()
        artifacts.update()
        decor.update()

        camera.update(player)

        if pygame.sprite.spritecollide(player, enemies, False):
            player.health -= 1
            if player.health <= 0:
                selected_option = show_game_over()
                if selected_option == 0:
                    main()
                elif selected_option == 1:
                    return
                else:
                    pygame.quit()
                    sys.exit()

        collected_artifacts = pygame.sprite.spritecollide(player, artifacts, True)
        for artifact in collected_artifacts:
            player.health = min(player.health + 20, player.max_health)
            player.gain_experience(20)
            if artifact_sound:
                artifact_sound.play()

        if len(artifacts) < 3:
            artifact_respawn_time += 1
            if artifact_respawn_time >= 180:
                artifact = Artifact()
                artifacts.add(artifact)
                all_sprites.add(artifact)
                artifact_respawn_time = 0

        if len(enemies) == 0:
            wave += 1
            show_dialog(f"Волна {wave} пройдена!")
            for _ in range(5 + wave):
                enemy = Enemy(difficulty)
                enemies.add(enemy)
                all_sprites.add(enemy)

        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            for y in range(HEIGHT):
                color = tuple(c1 + (c2 - c1) * y / HEIGHT for c1, c2 in zip((30, 30, 50), (10, 10, 20)))
                pygame.draw.line(screen, color, (0, y), (WIDTH, y))

        border_width = 50
        border_surface = pygame.Surface((WIDTH + border_width * 2, HEIGHT + border_width * 2), pygame.SRCALPHA)
        pygame.draw.rect(border_surface, (255, 255, 255, 30),
                         (border_width, border_width, WIDTH, HEIGHT),
                         width=5, border_radius=15)
        screen.blit(border_surface, (-border_width, -border_width))

        for entity in all_sprites:
            screen.blit(entity.image, camera.apply(entity))

        draw_health_bar(player)
        draw_level_indicator(player)
        draw_experience_bar(player)
        draw_cooldown_bar(player)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    load_settings()
    set_resolution(*settings['resolution'], settings['fullscreen'])
    player = Player()
    while True:
        selected_option = show_menu()
        if selected_option == 0:
            main()
        elif selected_option == 1:
            show_settings()
        elif selected_option == 2:
            show_shop(player)
        elif selected_option == 3:
            pygame.quit()
            sys.exit()
