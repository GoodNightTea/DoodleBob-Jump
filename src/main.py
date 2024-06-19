import pygame
from sys import exit
import random
from tkinter import Tk, filedialog
import pickle

# Initialisiert Pygame und die Schriftart
pygame.init()
pygame.font.init()
font = pygame.font.Font('font/Pixeltype.ttf', 50)

# Legt die Fenstergröße fest und erstellt das Hauptfenster
width = 480
height = 800
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Doodle Jump')
clock = pygame.time.Clock()

# Lädt die Grafiken für das Spiel
Background_surf = pygame.image.load('graphics/doodlejumpbg.png').convert()
player_surf = pygame.image.load('graphics/player/doodlefuckingbob.png').convert_alpha()
player_surf = pygame.transform.scale(player_surf, (70, 70))
platform_surf = pygame.image.load('graphics/platform.png').convert_alpha()
broken_platform_surf = pygame.image.load('graphics/platform-broken.png').convert_alpha()
trampoline_surf = pygame.image.load('graphics/trampoline_platform.png').convert_alpha()
propeller_surf = pygame.image.load('graphics/propeller.png').convert_alpha()
jetpack_surf = pygame.image.load('graphics/jetpack.png').convert_alpha()

# Lädt die Soundeffekte und stellt die Lautstärke ein
jump_sound = pygame.mixer.Sound('sounds/jump.mp3')
super_jump_sound = pygame.mixer.Sound('sounds/jump.mp3')
jetpack_sound = pygame.mixer.Sound('sounds/jetpack.mp3')
propeller_sound = pygame.mixer.Sound('sounds/propellor.mp3')
jump_sound.set_volume(0.1)
super_jump_sound.set_volume(0.1)

# Startbildschirm Grafik und Text laden
start_screen_surf = pygame.image.load('graphics\göööööööööööööt.png').convert()
start_screen_surf = pygame.transform.scale(start_screen_surf, (width, height))  # Bild auf Fenstergröße skalieren
start_text_surf = font.render('Klicke eine beliebige Taste zum Spielen', False, 'Black')

music_playing = True
display_string = 'on' if music_playing else 'off'
music_surf = font.render('Music: ' + display_string, False, 'LightBlue')
Paused_surf = font.render('Paused', False, 'Black')

# Richtet die Spielerposition und Variablen ein
player_rect = player_surf.get_rect(midbottom=(width // 2, height - 100))
y_velocity = 0
on_groundf = False
using_jetpack = False
using_propeller = False
jetpack_duration = 0
propeller_duration = 0

# Initialisiert den Spielzustand
paused = False
score = 0
show_start_screen = True

# Hintergrundmusik laden und abspielen
pygame.mixer.music.load('sounds/background_music.mp3')
pygame.mixer.music.play(-1)  # Endlosschleife

# Lautstärkeregelung initialisieren
volume = 1.0  # Standardlautstärke
pygame.mixer.music.set_volume(volume)

# Funktionen zum Speichern und Laden von Highscores
def save_high_score(high_scores):
    with open('high_scores.pkl', 'wb') as f:
        pickle.dump(high_scores, f)

def load_high_scores():
    try:
        with open('high_scores.pkl', 'rb') as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError):
        return [0] * 5  # Top 5 Highscores

high_scores = load_high_scores()

# Schwerkraft und Sprungkraft
gravity = 0.4
JUMP = -12
SUPER_JUMP = -20

def create_initial_platforms():
    initial_platforms = [{'rect': pygame.Rect((width - platform_surf.get_width()) // 2, height - 150, platform_surf.get_width(), platform_surf.get_height()), 'type': 'normal', 'dir': 0, 'break_time': 0, 'stepped_on': False}]
    for i in range(1, 10):
        initial_platforms.append({
            'rect': pygame.Rect(random.randint(0, width - platform_surf.get_width()), height - (i * 150), platform_surf.get_width(), platform_surf.get_height()),
            'type': 'normal',
            'dir': 0,
            'break_time': 0,
            'stepped_on': False
        })
    return initial_platforms

platforms = create_initial_platforms()
gadgets = []
last_gadget_y = -height * 2  # Großer Anfangsabstand für das erste Gadget

# Funktionen für das Spiel
def select_file():
    Tk().withdraw()
    music_file = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3;*.wav;*.ogg")])
    if music_file:
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play(-1)
        return True
    return False

def spawn_platform(y_pos):
    x_pos = random.randint(0, width - platform_surf.get_width())
    platform_type = 'normal'
    dir = 0
    if random.random() < 0.1:  # 10% Chance für eine kaputte Plattform
        platform_type = 'broken'
    elif random.random() < 0.2:  # 20% Chance für eine bewegliche Plattform
        platform_type = 'moving'
        dir = random.choice([-1, 1])
    elif random.random() < 0.1:  # 10% Chance für eine Trampolin-Plattform
        platform_type = 'trampoline'
    return {'rect': pygame.Rect(x_pos, y_pos, platform_surf.get_width(), platform_surf.get_height()), 'type': platform_type, 'dir': dir, 'break_time': 0, 'stepped_on': False}

def spawn_gadget():
    # Erstellt ein neues Gadget wenn die Bedingungen erfüllt sind
    global last_gadget_y
    if random.random() < 0.001 and player_rect.y - last_gadget_y > height // 2:
        gadget_type = random.choice(['jetpack', 'propeller'])
        x_pos = random.randint(0, width - jetpack_surf.get_width())
        y_pos = random.randint(-height, -50)
        last_gadget_y = y_pos
        return {'rect': pygame.Rect(x_pos, y_pos, jetpack_surf.get_width(), jetpack_surf.get_height()), 'type': gadget_type}
    return None

def move_platforms(dy):
    # Bewegt die Plattformen und Gadgets
    for platform in platforms:
        platform['rect'].y += dy
        if platform['type'] == 'moving':
            platform['rect'].x += platform['dir'] * 2
            if platform['rect'].left <= 0 or platform['rect'].right >= width:
                platform['dir'] *= -1
    while platforms and platforms[0]['rect'].y > height:
        platforms.pop(0)
    if platforms and platforms[-1]['rect'].y > 0:
        while len(platforms) < 10:
            new_platform_y = platforms[-1]['rect'].y - random.randint(100, 150)
            platforms.append(spawn_platform(new_platform_y))
    ensure_path()

    for gadget in gadgets:
        gadget['rect'].y += dy
    while gadgets and gadgets[0]['rect'].y > height:
        gadgets.pop(0)
    if len(gadgets) < 3:
        new_gadget = spawn_gadget()
        if new_gadget:
            gadgets.append(new_gadget)

def ensure_path():
    # Stellt sicher, dass es immer mindestens eine normale Plattform im sichtbaren Bereich gibt
    visible_platforms = [p for p in platforms if p['rect'].y < height]
    if not any(p['type'] == 'normal' for p in visible_platforms):
        new_platform = spawn_platform(visible_platforms[-1]['rect'].y - random.randint(100, 150))
        new_platform['type'] = 'normal'
        platforms.append(new_platform)

def reset_game():
    # Setzt das Spiel zurück und speichert Highscores
    global player_rect, y_velocity, score, platforms, gadgets, using_jetpack, using_propeller, jetpack_duration, propeller_duration, high_scores, last_gadget_y
    if score > high_scores[-1]:
        high_scores.append(score)
        high_scores = sorted(high_scores, reverse=True)[:5]
        save_high_score(high_scores)
    player_rect = player_surf.get_rect(midbottom=(width // 2, height - 100))
    y_velocity = 0
    score = 0
    platforms = create_initial_platforms()
    gadgets = []
    using_jetpack = False
    using_propeller = False
    jetpack_duration = 0
    propeller_duration = 0
    last_gadget_y = -height  # Anfangsabstand für das erste Gadget zurücksetzen

# Hauptschleife des Spiels
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame.KEYDOWN:
            if show_start_screen:
                show_start_screen = False
            elif event.key == pygame.K_SPACE and on_ground and not paused:
                y_velocity = JUMP
                on_ground = False
                jump_sound.play()
            if event.key == pygame.K_s:
                paused = not paused
            if event.key == pygame.K_m:
                music_playing = not music_playing
                if music_playing:
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.pause()
            if event.key == pygame.K_r:
                reset_game()
            if event.key == pygame.K_UP and paused:  # Erhöht die Lautstärke
                volume = min(volume + 0.1, 1.0)
                pygame.mixer.music.set_volume(volume)
            if event.key == pygame.K_DOWN and paused:  # Verringert die Lautstärke
                volume = max(volume - 0.1, 0.0)
                pygame.mixer.music.set_volume(volume)

    if show_start_screen:
        # Zeigt den Startbildschirm
        screen.blit(start_screen_surf, (0, 0))
        screen.blit(start_text_surf, (width // 2 - start_text_surf.get_width() // 2, height - 100))
    else:
        if not paused:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]:
                player_rect.x -= 8
            if keys[pygame.K_d]:
                player_rect.x += 8

            if using_jetpack:
                y_velocity = -5
                jetpack_duration -= 1
                if jetpack_duration <= 0:
                    using_jetpack = False
            elif using_propeller:
                y_velocity = -5
                propeller_duration -= 1
                if propeller_duration <= 0:
                    using_propeller = False
            else:
                y_velocity += gravity

            player_rect.y += y_velocity

            if player_rect.x < -70:
                player_rect.x = width
            elif player_rect.x > width:
                player_rect.x = -70

            # Plattformkollisionen prüfen
            on_ground = False
            for platform in platforms:
                if platform['rect'].colliderect(player_rect) and y_velocity > 0:
                    if platform['type'] == 'normal' or platform['type'] == 'moving':
                        player_rect.bottom = platform['rect'].top
                        y_velocity = JUMP
                        score += 1
                        on_ground = True
                        jump_sound.play()
                    elif platform['type'] == 'trampoline':
                        player_rect.bottom = platform['rect'].top
                        y_velocity = SUPER_JUMP
                        score += 1
                        on_ground = True
                        super_jump_sound.play()
                    elif platform['type'] == 'broken':
                        if not platform['stepped_on']:
                            platform['stepped_on'] = True
                            platform['break_time'] = pygame.time.get_ticks() + 1000
                        if pygame.time.get_ticks() < platform['break_time']:
                            player_rect.bottom = platform['rect'].top
                            y_velocity = JUMP
                            score += 1
                            on_ground = True
                            jump_sound.play()
                        elif pygame.time.get_ticks() >= platform['break_time']:
                            platforms.remove(platform)

            for gadget in gadgets:
                if gadget['rect'].colliderect(player_rect):
                    if gadget['type'] == 'jetpack':
                        using_jetpack = True
                        jetpack_duration = 180
                        jetpack_sound.play()
                        gadgets.remove(gadget)
                    elif gadget['type'] == 'propeller':
                        using_propeller = True
                        propeller_duration = 180
                        propeller_sound.play()
                        gadgets.remove(gadget)

            # Hintergrund und Plattformen bewegen, wenn der Spieler springt
            if player_rect.top <= height // 3 and y_velocity < 0:
                player_rect.y = height // 3
                move_platforms(int(-y_velocity))

            if y_velocity > 0:
                move_platforms(1)

            if player_rect.y > height:
                reset_game()

        display_string = 'on' if music_playing else 'off'
        music_surf = font.render('Music: ' + display_string, False, 'LightBlue')

        screen.fill((255, 255, 255))
        screen.blit(Background_surf, (0, 0))

        # Plattformen und Gadgets einfügen
        for platform in platforms:
            if platform['type'] == 'normal':
                screen.blit(platform_surf, platform['rect'].topleft)
            elif platform['type'] == 'moving':
                screen.blit(platform_surf, platform['rect'].topleft)
            elif platform['type'] == 'trampoline':
                screen.blit(trampoline_surf, platform['rect'].topleft)
            else:
                screen.blit(broken_platform_surf, platform['rect'].topleft)

        for gadget in gadgets:
            if gadget['type'] == 'jetpack':
                screen.blit(jetpack_surf, gadget['rect'].topleft)
            elif gadget['type'] == 'propeller':
                screen.blit(propeller_surf, gadget['rect'].topleft)

        # Spieler einfügen
        screen.blit(player_surf, player_rect)
        
        # Punktestand und Highscores anzeigen
        score_surf = font.render('Score: ' + str(score), False, 'Black')
        screen.blit(score_surf, (10, 10))
        for i, high_score in enumerate(high_scores):
            high_score_surf = font.render(f'{i + 1}. {high_score}', False, 'Black')
            screen.blit(high_score_surf, (10, 60 + i * 50))

        if paused:
            screen.blit(Paused_surf, (width // 2 - Paused_surf.get_width() // 2, height // 2 - Paused_surf.get_height() // 2))
            screen.blit(music_surf, (width // 2 - music_surf.get_width() // 2, height // 2 + Paused_surf.get_height()))
            volume_surf = font.render(f'Volume: {int(volume * 100)}%', False, 'Black')
            screen.blit(volume_surf, (width // 2 - volume_surf.get_width() // 2, height // 2 + Paused_surf.get_height() + music_surf.get_height()))

    pygame.display.update()
    clock.tick(60)
