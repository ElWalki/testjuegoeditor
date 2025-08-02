import pygame
import sys
import math
import random
import json
import os # Importar para manejar directorios y archivos

# --- Constantes del Juego ---
# Modificado para permitir redimensionamiento
WIDTH, HEIGHT = 1200, 900
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.SCALED)
pygame.display.set_caption("Juego Plataformero Detallado con IA y Niveles")

# --- Constantes de Físicas ---
GRAVITY = 0.5
BULLET_GRAVITY_EFFECT = 0.2 # Aumentado para más caída
JUMP_FORCE = -12
MAX_JUMPS = 2
INVULNERABILITY_DURATION = 2000 # 2 segundos en milisegundos
DASH_SPEED_MULTIPLIER = 3 # Velocidad extra durante el dash
DASH_DURATION = 150 # Duración del dash en milisegundos
DASH_COOLDOWN = 1000 # Tiempo de recarga del dash en milisegundos
SPEED_BOOST_DURATION = 5000 # Duración del aumento de velocidad en milisegundos

# --- Constantes del Cono de Puntería ---
AIM_CONE_BASE_LENGTH = 50 # Longitud mínima del cono al empezar a cargar
AIM_CONE_MAX_LENGTH = 400 # Longitud máxima del cono al 100% de carga
AIM_CONE_WIDTH = 30   # Ancho de la base del cono (afecta el ángulo de apertura)
AIM_CONE_COLOR = (255, 0, 0, 100) # Rojo translúcido (RGBA)
AIM_CONE_BLINK_INTERVAL = 75 # Intervalo de parpadeo del cono cuando está cargado al máximo

# --- Constantes de Balas Cargadas (para arma ROJA) ---
RED_BULLET_BASE_SPEED = 20 # Velocidad inicial de la bala de francotirador (mínima)
RED_BULLET_MAX_SPEED = 50 # Velocidad máxima de la bala de francotirador
RED_BULLET_BASE_DAMAGE = 2 # Daño base de la bala de francotirador (mínima)
RED_BULLET_MAX_DAMAGE = 10 # Daño máximo de la bala de francotirador
CHARGED_BULLET_BLINK_INTERVAL = 50 # Parpadeo muy rápido para la bala cargada
CHARGED_BULLET_COLOR_PRIMARY = (255, 255, 255) # Blanco
CHARGED_BULLET_COLOR_SECONDARY = (255, 0, 0) # Rojo

# --- Constantes de Carga (para arma ROJA y PURPLE) ---
CHARGE_DURATION = 2000 # Tiempo para alcanzar la carga máxima (2 segundos)
PURPLE_ARC_MAX_HEIGHT = 200 # Altura máxima del arco del proyectil violeta
PURPLE_ARC_SPEED_FACTOR = 0.05 # Factor para la velocidad horizontal del proyectil violeta
PURPLE_HOOK_RANGE_CELLS = 6 # Rango del gancho en número de celdas
PURPLE_HOOK_PULL_SPEED = 25 # Velocidad de arrastre del gancho
PURPLE_HOOK_DETECTION_SIZE = 30 # Tamaño del cuadrado de detección para el gancho (aumentado)

# --- Estados del Juego ---
GAME_STATE_MENU = 0
GAME_STATE_PLAYING = 1
GAME_STATE_GAME_OVER = 2
GAME_STATE_WIN = 3
GAME_STATE_EDITOR = 4 # Nuevo estado para el editor
GAME_STATE_SAVING_LEVEL_INPUT = 5 # Nuevo estado para la entrada de nombre de archivo
GAME_STATE_EDITING_PROPERTIES = 6 # Nuevo estado para editar propiedades de elementos
GAME_STATE_LOAD_LEVEL_MENU = 7 # Nuevo estado para el menú de carga de niveles
GAME_STATE_PLAYING_FROM_EDITOR = 8 # Nuevo estado para jugar un nivel desde el editor

# --- Gestor de Sonidos ---
class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {
            "jump": pygame.mixer.Sound(self.create_simple_sound(440, 0.1)),
            "shoot": pygame.mixer.Sound(self.create_simple_sound(880, 0.05)),
            "charged_shoot": pygame.mixer.Sound(self.create_simple_sound(1200, 0.1, 0.9)), # Sonido para disparo cargado
            "hit": pygame.mixer.Sound(self.create_simple_sound(220, 0.1, 0.5)),
            "collect": pygame.mixer.Sound(self.create_simple_sound(1000, 0.08)),
            "level_complete": pygame.mixer.Sound(self.create_simple_sound(600, 0.3, 0.8)),
            "game_over": pygame.mixer.Sound(self.create_simple_sound(150, 0.5, 0.2)),
            "dash": pygame.mixer.Sound(self.create_simple_sound(1200, 0.07)),
            "health_pickup": pygame.mixer.Sound(self.create_simple_sound(700, 0.1)),
            "speed_pickup": pygame.mixer.Sound(self.create_simple_sound(1500, 0.1)),
            "charge_powerup_pickup": pygame.mixer.Sound(self.create_simple_sound(1800, 0.1)), # Sonido para power-up de carga
            "spike_hit": pygame.mixer.Sound(self.create_simple_sound(100, 0.1, 0.3)),
            "reload": pygame.mixer.Sound(self.create_simple_sound(300, 0.2)),
            "weapon_pickup": pygame.mixer.Sound(self.create_simple_sound(1600, 0.1)), # Sonido para recoger arma
            "explosion": pygame.mixer.Sound(self.create_simple_sound(100, 0.2, 0.1)), # Sonido para explosión
            "hook_attach": pygame.mixer.Sound(self.create_simple_sound(900, 0.05, 0.7)), # Sonido para gancho
            "hook_pull": pygame.mixer.Sound(self.create_simple_sound(1100, 0.03, 0.8)) # Sonido para arrastre de gancho
        }

    def create_simple_sound(self, frequency, duration, decay_factor=1.0):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = bytearray(n_samples * 2)
        amplitude = 32767

        for i in range(n_samples):
            value = int(amplitude * math.sin(2 * math.pi * frequency * i / sample_rate) * (1 - i / n_samples * (1 - decay_factor)))
            buf[i*2] = value & 0xFF
            buf[i*2 + 1] = (value >> 8) & 0xFF
        
        return pygame.mixer.Sound(buffer=buf)

    def play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].play()

# --- Clases de Sprites ---

class Player(pygame.sprite.Sprite):
    def __init__(self, player_color, game_instance): # Add game_instance
        super().__init__()
        self.game = game_instance # Store game instance
        self.player_color = player_color
        self.secondary_color = (200, 200, 200)

        self.width = 35
        self.height = 45 
        self.image = pygame.Surface([self.width, self.height], pygame.SRCALPHA)
        self.rect = self.image.get_rect()

        self.speed_horizontal = 5
        self.original_speed_horizontal = 5 
        self.velocity_y = 0
        self.on_ground = False
        self.jump_count = 0
        self.last_shot_time = pygame.time.get_ticks()
        self.shoot_delay = 250

        self.health = 100
        self.max_health = 100
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.blink_interval = 100

        self.is_dashing = False
        self.dash_timer = 0
        self.last_dash_time = 0
        self.current_horizontal_direction = 1 

        self.speed_boost_active = False
        self.speed_boost_timer = 0

        # Weapon System
        self.weapon_data = {
            "normal": {
                "max_ammo": 5,
                "current_ammo": 5,
                "shoot_delay": 250,
                "bullet_speed": 20,
                "bullet_damage": 1,
                "is_charged_shot": False,
                "bullet_size": (10, 5),
                "color": (255, 255, 50), # Amarillo
                "reload_duration": 500 # Añadido para evitar KeyError
            },
            "blue": { # Ametralladora
                "max_ammo": 25,
                "current_ammo": 25,
                "shoot_delay": 50, # Disparo rápido
                "reload_duration": 1500,
                "bullet_speed": 25,
                "bullet_damage": 0.5, # Menor daño por bala
                "is_charged_shot": False,
                "bullet_size": (8, 4),
                "color": (0, 100, 255) # Azul
            },
            "red": { # Francotirador (disparo cargado en click IZQ)
                "max_ammo": 1,
                "current_ammo": 1,
                "shoot_delay": 0, # Manejado por la carga
                "reload_duration": 3000,
                "bullet_speed": 0, # Manejado por la carga
                "bullet_damage": 0, # Manejado por la carga
                "is_charged_shot": True, # Esta arma usa mecánica de carga
                "bullet_size": (20, 10), # Bala de francotirador más grande
                "color": (255, 50, 0) # Rojo
            },
            "purple": { # Explosiva / Gancho
                "max_ammo": 2,
                "current_ammo": 2,
                "shoot_delay": 500, # Retraso entre disparos explosivos
                "reload_duration": 2000,
                "bullet_speed": 0, # Manejado por la carga/arco
                "bullet_damage": 0, # El proyectil principal no hace daño, la metralla sí
                "is_charged_shot": True, # Disparo cargado con click IZQ
                "bullet_size": (18, 18), # Proyectil explosivo redondo
                "color": (150, 0, 255) # Violeta
            }
        }
        self.current_weapon = "normal"
        self.has_weapon_powerup = {"blue": False, "red": False, "purple": False} # Rastrea power-ups de arma recogidos

        # Charge Shot attributes (for power-up, right click)
        self.is_charging_powerup_shot = False # For the special power-up charge shot
        self.charge_powerup_start_time = 0
        self.charge_powerup_level = 0.0 # 0.0 to 1.0
        self.has_charge_powerup = False # Indicates if player has the special charge power-up

        # Charge Shot attributes (for RED weapon, left click)
        self.is_charging_red_weapon = False
        self.red_charge_start_time = 0
        self.red_charge_level = 0.0

        # Purple Weapon specific attributes
        self.is_charging_purple_shot = False # For purple weapon's arc shot (left click)
        self.purple_charge_start_time = 0
        self.purple_charge_level = 0.0

        self.is_grappling = False # For purple weapon's hook (right click)
        self.grapple_target_pos = None # World coordinates where hook is aiming/attached
        self.grapple_attached_sprite = None # The sprite the hook is attached to
        self.grapple_pull_timer = 0 # Timer for pulling duration
        self.grapple_max_pull_duration = 1000 # Max time to pull if attached

        self.is_reloading = False
        self.reload_timer = 0

        self.shooting_animation_active = False
        self.shooting_animation_timer = 0
        self.shooting_animation_duration = 100

        self._draw_player_image()

    def _draw_player_image(self):
        self.image.fill((0, 0, 0, 0))

        # Body (main armor)
        body_points = [
            (self.width // 4, 0), (self.width * 3 // 4, 0),
            (self.width, self.height // 4), (self.width, self.height * 3 // 4),
            (self.width * 3 // 4, self.height), (self.width // 4, self.height),
            (0, self.height * 3 // 4), (0, self.height // 4)
        ]
        pygame.draw.polygon(self.image, self.player_color, body_points)

        # Helmet (rounded top)
        pygame.draw.ellipse(self.image, self.player_color, (self.width // 4, -5, self.width // 2, 15))
        pygame.draw.rect(self.image, self.player_color, (self.width // 4, 5, self.width // 2, 10))
        # Visor
        pygame.draw.rect(self.image, (0, 200, 255), (self.width // 4 + 5, 7, self.width // 2 - 10, 5))

        # Shoulder pads
        pygame.draw.circle(self.image, self.secondary_color, (self.width // 4, self.height // 4), 7)
        pygame.draw.circle(self.image, self.secondary_color, (self.width * 3 // 4, self.height // 4), 7)

        # Arm Cannon (Right Arm) - Color based on current weapon
        cannon_x = self.width * 3 // 4 + 5
        cannon_y = self.height // 4 + 5
        cannon_width = 15
        cannon_height = 8

        cannon_color = self.weapon_data[self.current_weapon]["color"]

        if self.shooting_animation_active:
            cannon_length_extension = 10 
            cannon_glow_color = (255, 200, 0, 150) 
            pygame.draw.rect(self.image, cannon_glow_color, (cannon_x, cannon_y - cannon_height // 2, cannon_width + cannon_length_extension, cannon_height), border_radius=3)
        else:
            cannon_length_extension = 0
        
        pygame.draw.rect(self.image, cannon_color, (cannon_x, cannon_y - cannon_height // 2, cannon_width + cannon_length_extension, cannon_height), border_radius=3)
        pygame.draw.circle(self.image, cannon_color, (cannon_x + cannon_width + cannon_length_extension, cannon_y), cannon_height // 2)

        # Left Arm (simple)
        pygame.draw.rect(self.image, self.secondary_color, (self.width // 4 - 10, self.height // 4 + 5, 15, 8), border_radius=3)

        # Legs (simple, armored)
        leg_width = self.width // 3
        leg_height = self.height // 3
        pygame.draw.rect(self.image, self.secondary_color, (self.width // 4 - 5, self.height - leg_height, leg_width, leg_height), border_radius=3)
        pygame.draw.rect(self.image, self.secondary_color, (self.width * 3 // 4 - leg_width + 5, self.height - leg_height, leg_width, leg_height), border_radius=3)


    def update(self, platforms, doors): # Added doors to update parameters
        keys = pygame.key.get_pressed()
        
        current_speed = self.speed_horizontal
        if self.is_dashing:
            current_speed *= DASH_SPEED_MULTIPLIER

        # Store original position for collision resolution
        original_x = self.rect.x
        original_y = self.rect.y

        # --- Horizontal Movement ---
        if keys[pygame.K_a]:
            self.rect.x -= current_speed
            self.current_horizontal_direction = -1
        if keys[pygame.K_d]:
            self.rect.x += current_speed
            self.current_horizontal_direction = 1
        
        # Player movement is no longer clamped to level_width/height.
        # It's only limited by collision with platforms/doors.

        # Horizontal collision with platforms and CLOSED doors
        for obj in list(platforms) + [d for d in doors if not d.is_open]:
            if self.rect.colliderect(obj.rect):
                if self.rect.x < original_x: # Moving left
                    self.rect.left = obj.rect.right
                elif self.rect.x > original_x: # Moving right
                    self.rect.right = obj.rect.left

        # --- Vertical Movement ---
        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y

        # Player movement is no longer clamped to level_width/height.
        # It's only limited by collision with platforms/doors.

        self.on_ground = False
        # Vertical collision with platforms and CLOSED doors
        for obj in list(platforms) + [d for d in doors if not d.is_open]:
            if self.rect.colliderect(obj.rect):
                if self.velocity_y > 0: # Falling
                    self.rect.bottom = obj.rect.top
                    self.velocity_y = 0
                    self.on_ground = True
                    self.jump_count = 0
                elif self.velocity_y < 0: # Jumping up
                    self.rect.top = obj.rect.bottom
                    self.velocity_y = 0
        
        now = pygame.time.get_ticks()
        
        if self.invulnerable:
            if now - self.invulnerable_timer > INVULNERABILITY_DURATION:
                self.invulnerable = False
                if not self.is_dashing and not self.speed_boost_active and not self.shooting_animation_active:
                    self._draw_player_image()
            else:
                if (now // self.blink_interval) % 2 == 0:
                    self.image.fill((0, 0, 0, 0))
                else:
                    self._draw_player_image()

        if self.is_dashing:
            if now - self.dash_timer > DASH_DURATION:
                self.is_dashing = False
                if not self.invulnerable and not self.speed_boost_active and not self.shooting_animation_active:
                    self._draw_player_image()
            else:
                if not self.invulnerable:
                    if (now // (self.blink_interval / 2)) % 2 == 0:
                        self.image.fill((0, 0, 0, 0))
                    else:
                        self._draw_player_image()
                
                # Dash movement is handled by adding to rect.x directly
                # Ensure dash doesn't push player through walls
                dash_move_x = self.current_horizontal_direction * (DASH_SPEED_MULTIPLIER * self.speed_horizontal - self.speed_horizontal)
                self.rect.x += dash_move_x
                
                # Re-check collisions after dash movement
                for obj in list(platforms) + [d for d in doors if not d.is_open]:
                    if self.rect.colliderect(obj.rect):
                        if dash_move_x > 0: # Dashing right
                            self.rect.right = obj.rect.left
                        elif dash_move_x < 0: # Dashing left
                            self.rect.left = obj.rect.right

                # Player movement is no longer clamped to level_width/height.

        if self.speed_boost_active:
            if now - self.speed_boost_timer > SPEED_BOOST_DURATION:
                self.speed_boost_active = False
                self.speed_horizontal = self.original_speed_horizontal
                if not self.is_dashing and not self.invulnerable and not self.shooting_animation_active:
                    self._draw_player_image()
            else:
                self.speed_horizontal = self.original_speed_horizontal * 1.5
        
        # Reloading for current weapon
        if self.is_reloading:
            # Check if 'reload_duration' exists for the current weapon before accessing it
            if "reload_duration" in self.weapon_data[self.current_weapon] and \
               now - self.reload_timer > self.weapon_data[self.current_weapon]["reload_duration"]:
                self.is_reloading = False
                self.weapon_data[self.current_weapon]["current_ammo"] = self.weapon_data[self.current_weapon]["max_ammo"]
        
        if self.shooting_animation_active:
            if now - self.shooting_animation_timer > self.shooting_animation_duration:
                self.shooting_animation_active = False
                if not self.invulnerable and not self.is_dashing and not self.speed_boost_active:
                    self._draw_player_image()
            else:
                self._draw_player_image()

        # Charge shot update (for power-up, right click)
        if self.is_charging_powerup_shot:
            elapsed = now - self.charge_powerup_start_time
            self.charge_powerup_level = min(1.0, elapsed / CHARGE_DURATION)
        else:
            self.charge_powerup_level = 0.0 # Reset charge level if not charging

        # Charge shot update (for RED weapon, left click)
        if self.is_charging_red_weapon:
            elapsed = now - self.red_charge_start_time
            self.red_charge_level = min(1.0, elapsed / CHARGE_DURATION)
        else:
            self.red_charge_level = 0.0

        # Charge shot update (for PURPLE weapon, left click)
        if self.is_charging_purple_shot:
            elapsed = now - self.purple_charge_start_time
            self.purple_charge_level = min(1.0, elapsed / CHARGE_DURATION)
        else:
            self.purple_charge_level = 0.0

        # Grappling Hook update (for PURPLE weapon, right click)
        if self.is_grappling and self.grapple_attached_sprite:
            # Calculate direction to attached point
            target_x, target_y = self.grapple_target_pos
            dx = target_x - self.rect.centerx
            dy = target_y - self.rect.centery
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 10: # Keep pulling until close
                norm_dx, norm_dy = dx / distance, dy / distance
                self.rect.x += norm_dx * PURPLE_HOOK_PULL_SPEED
                self.rect.y += norm_dy * PURPLE_HOOK_PULL_SPEED
                self.velocity_y = 0 # Cancel gravity while pulling
                self.sound_manager.play_sound("hook_pull") # Play pull sound
            else:
                self.is_grappling = False
                self.grapple_attached_sprite = None
                self.grapple_target_pos = None
                self.sound_manager.play_sound("hook_attach") # Play a "finished" sound
        elif self.is_grappling and not self.grapple_attached_sprite:
            # If not attached, but still "grappling" (hook is flying)
            # Check for attachment
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # Convert mouse pos to world coords
            mouse_x_world = mouse_x + self.game.camera_offset_x
            mouse_y_world = mouse_y + self.game.camera_offset_y

            # Calculate the hook's current "visual" end point (limited by range)
            player_center_world = pygame.math.Vector2(self.rect.centerx, self.rect.centery)
            mouse_world_vec = pygame.math.Vector2(mouse_x_world, mouse_y_world)
            
            direction_vec = (mouse_world_vec - player_center_world)
            if direction_vec.length() > PURPLE_HOOK_RANGE_CELLS * self.game.GRID_SIZE:
                direction_vec.scale_to_length(PURPLE_HOOK_RANGE_CELLS * self.game.GRID_SIZE)
            
            hook_end_point_world = player_center_world + direction_vec
            
            # Create a small rect at the hook's end for collision detection
            # CORRECCIÓN: Aumentar el tamaño del rectángulo de detección del gancho
            hook_rect = pygame.Rect(hook_end_point_world.x - PURPLE_HOOK_DETECTION_SIZE // 2, 
                                    hook_end_point_world.y - PURPLE_HOOK_DETECTION_SIZE // 2, 
                                    PURPLE_HOOK_DETECTION_SIZE, PURPLE_HOOK_DETECTION_SIZE)

            # Check for collision with hookable sprites
            found_hookable = False
            for sprite in self.game.platforms.sprites() + self.game.doors.sprites():
                if hasattr(sprite, 'is_hookable') and sprite.is_hookable and hook_rect.colliderect(sprite.rect):
                    self.grapple_attached_sprite = sprite
                    self.grapple_target_pos = hook_end_point_world # Attach to the point where it hit
                    self.grapple_pull_timer = now
                    self.sound_manager.play_sound("hook_attach")
                    found_hookable = True
                    break
            
            # If hook is active but not attached and time runs out, or mouse released (handled in handle_events)
            # For now, if not attached, it will just draw the line and wait for attachment or mouse release.


        if not self.invulnerable and not self.is_dashing and not self.speed_boost_active and not self.is_grappling:
            self._draw_player_image()


    def jump(self, sound_manager):
        if self.jump_count < MAX_JUMPS:
            self.velocity_y = JUMP_FORCE
            self.jump_count += 1
            self.on_ground = False
            sound_manager.play_sound("jump")
            # If grappling, a jump should release the hook
            if self.is_grappling:
                self.is_grappling = False
                self.grapple_attached_sprite = None
                self.grapple_target_pos = None

    def shoot(self, target_x, target_y, sound_manager, click_type="left"):
        now = pygame.time.get_ticks()
        current_weapon_data = self.weapon_data[self.current_weapon]

        if self.is_reloading:
            return False

        if click_type == "left":
            if self.current_weapon == "red": # Red weapon uses left-click for charge
                if self.is_charging_red_weapon and current_weapon_data["current_ammo"] > 0:
                    self.shooting_animation_active = True
                    self.shooting_animation_timer = now
                    sound_manager.play_sound("charged_shoot")
                    current_weapon_data["current_ammo"] -= 1
                    return True
            elif self.current_weapon == "purple": # Purple weapon uses left-click for arc shot
                if self.is_charging_purple_shot and current_weapon_data["current_ammo"] > 0:
                    self.shooting_animation_active = True
                    self.shooting_animation_timer = now
                    sound_manager.play_sound("charged_shoot") # Use charged sound for purple arc shot
                    current_weapon_data["current_ammo"] -= 1
                    return True
            else: # Normal and Blue weapons use left-click for continuous/single fire
                if current_weapon_data["current_ammo"] > 0 and now - self.last_shot_time > current_weapon_data["shoot_delay"]:
                    self.last_shot_time = now
                    self.shooting_animation_active = True
                    self.shooting_animation_timer = now
                    sound_manager.play_sound("shoot")
                    current_weapon_data["current_ammo"] -= 1
                    return True
        elif click_type == "right": # Special power-up charge shot OR Purple Grappling Hook
            if self.has_charge_powerup and self.is_charging_powerup_shot:
                self.shooting_animation_active = True
                self.shooting_animation_timer = now
                sound_manager.play_sound("charged_shoot")
                self.has_charge_powerup = False # Consume power-up
                return True
            elif self.current_weapon == "purple" and self.is_grappling: # Grappling hook release
                # If hook was attached, it's handled in update. If not attached, just stop.
                self.is_grappling = False
                self.grapple_attached_sprite = None
                self.grapple_target_pos = None
                return False # Not a "shot" that consumes ammo
        return False

    def start_dash(self, sound_manager):
        now = pygame.time.get_ticks()
        if not self.is_dashing and (now - self.last_dash_time > DASH_COOLDOWN):
            self.is_dashing = True
            self.dash_timer = now
            self.last_dash_time = now
            sound_manager.play_sound("dash")
            # If grappling, a dash should release the hook
            if self.is_grappling:
                self.is_grappling = False
                self.grapple_attached_sprite = None
                self.grapple_target_pos = None
            return True
        return False

    def start_reload(self, sound_manager):
        now = pygame.time.get_ticks()
        current_weapon_data = self.weapon_data[self.current_weapon]
        # Only allow reload if reload_duration exists for the current weapon
        if "reload_duration" in current_weapon_data and \
           not self.is_reloading and current_weapon_data["current_ammo"] < current_weapon_data["max_ammo"]:
            self.is_reloading = True
            self.reload_timer = now
            sound_manager.play_sound("reload")
            return True
        return False

    def start_charge(self, click_type="right"):
        if self.is_reloading:
            return

        if click_type == "right":
            if self.has_charge_powerup: # Special power-up charge shot
                if not self.is_charging_powerup_shot:
                    self.is_charging_powerup_shot = True
                    self.charge_powerup_start_time = pygame.time.get_ticks()
            elif self.current_weapon == "purple": # Purple weapon grappling hook
                if not self.is_grappling:
                    self.is_grappling = True
                    self.grapple_attached_sprite = None # Not attached yet
                    self.sound_manager.play_sound("hook_attach") # Play initial hook sound
        elif click_type == "left":
            if self.current_weapon == "red" and self.weapon_data["red"]["current_ammo"] > 0:
                if not self.is_charging_red_weapon:
                    self.is_charging_red_weapon = True
                    self.red_charge_start_time = pygame.time.get_ticks()
            elif self.current_weapon == "purple" and self.weapon_data["purple"]["current_ammo"] > 0:
                if not self.is_charging_purple_shot:
                    self.is_charging_purple_shot = True
                    self.purple_charge_start_time = pygame.time.get_ticks()

    def stop_charge(self, click_type="right"):
        if click_type == "right":
            self.is_charging_powerup_shot = False
            if self.current_weapon == "purple" and self.is_grappling and not self.grapple_attached_sprite: # If hook was flying and not attached, stop it
                self.is_grappling = False
                self.grapple_target_pos = None
        elif click_type == "left":
            self.is_charging_red_weapon = False
            self.is_charging_purple_shot = False

    def equip_weapon(self, weapon_type, sound_manager):
        if weapon_type in self.weapon_data and (weapon_type == "normal" or self.has_weapon_powerup[weapon_type]):
            self.current_weapon = weapon_type
            sound_manager.play_sound("weapon_pickup") # Play sound when equipping a new weapon
            self.is_reloading = False # Cancel any ongoing reload
            self.is_charging_powerup_shot = False # Cancel special charge
            self.is_charging_red_weapon = False # Cancel red weapon charge
            self.is_charging_purple_shot = False # Cancel purple weapon charge
            self.is_grappling = False # Cancel grappling
            self.grapple_attached_sprite = None
            self.grapple_target_pos = None
            self._draw_player_image() # Update player appearance

    def activate_speed_boost(self):
        self.speed_boost_active = True
        self.speed_boost_timer = pygame.time.get_ticks()

    def heal(self, amount):
        self.health += amount
        if self.health > self.max_health:
            self.health = self.max_health

    def take_damage(self, amount, sound_manager):
        if not self.invulnerable:
            self.health -= amount
            sound_manager.play_sound("hit")
            self.invulnerable = True
            self.invulnerable_timer = pygame.time.get_ticks()
            if self.health <= 0:
                self.health = 0
                return True
        return False
# --- Clases de Sprites (continuación) ---

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dir_x, dir_y, weapon_type, charge_level=0.0, game_instance=None): # Added game_instance
        super().__init__()
        self.game = game_instance # Store game instance
        self.weapon_type = weapon_type
        self.charge_level = charge_level
        self.damage = 1 # Default damage

        self.is_explosive = False
        self.is_shrapnel = False
        self.bounces_remaining = 0
        self.is_arc_projectile = False # For purple weapon's arc shot

        if self.weapon_type == "red": # Sniper weapon
            self.speed = RED_BULLET_BASE_SPEED + (RED_BULLET_MAX_SPEED - RED_BULLET_BASE_SPEED) * self.charge_level
            self.damage = RED_BULLET_BASE_DAMAGE + (RED_BULLET_MAX_DAMAGE - RED_BULLET_BASE_DAMAGE) * self.charge_level
            self.original_image = pygame.Surface([20, 10], pygame.SRCALPHA)
            self.blink_timer = 0
            self._draw_charged_bullet_image(CHARGED_BULLET_COLOR_PRIMARY, CHARGED_BULLET_COLOR_SECONDARY)
        elif self.weapon_type == "purple": # Explosive weapon (arc shot)
            self.is_explosive = True
            self.is_arc_projectile = True
            # Speed and damage will be determined by charge_level and arc physics
            self.speed = 0 # Initial speed is calculated in Game.shoot
            self.damage = 0 # Main projectile does no direct damage
            self.original_image = pygame.Surface([18, 18], pygame.SRCALPHA)
            pygame.draw.circle(self.original_image, (150, 0, 255), (9, 9), 9) # Purple circle
            pygame.draw.circle(self.original_image, (255, 255, 0), (9, 9), 4) # Yellow core
        elif self.weapon_type == "shrapnel": # Shrapnel from purple explosion
            self.is_shrapnel = True
            self.speed = 15 # Shrapnel speed
            self.damage = 1
            self.bounces_remaining = 2 # Shrapnel can bounce a few times
            self.original_image = pygame.Surface([6, 6], pygame.SRCALPHA)
            pygame.draw.circle(self.original_image, (255, 255, 0), (3, 3), 3) # Small yellow yellow circle
        else: # Normal or Blue weapon
            self.speed = 20 if self.weapon_type == "normal" else 25 # Speed for normal/blue
            self.damage = 1 if self.weapon_type == "normal" else 0.5 # Damage for normal/blue
            self.original_image = pygame.Surface([10, 5], pygame.SRCALPHA)
            self.original_image.fill((255, 255, 50) if self.weapon_type == "normal" else (0, 100, 255)) # Yellow or Blue

        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        # CORRECCIÓN: Para balas de arco (purple), dir_x y dir_y ya son las velocidades
        if self.is_arc_projectile:
            self.vel_x = dir_x
            self.vel_y = dir_y
        else:
            self.vel_x = dir_x * self.speed
            self.vel_y = dir_y * self.speed
        
        self.angle = math.degrees(math.atan2(-self.vel_y, self.vel_x))

    def _draw_charged_bullet_image(self, fill_color, outline_color):
        self.original_image.fill((0, 0, 0, 0)) # Clear for redraw
        pygame.draw.ellipse(self.original_image, fill_color, self.original_image.get_rect(), 0) # Fill
        pygame.draw.ellipse(self.original_image, outline_color, self.original_image.get_rect(), 2) # Outline

    def update(self, platforms):
        self.vel_y += BULLET_GRAVITY_EFFECT
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        
        self.angle = math.degrees(math.atan2(-self.vel_y, self.vel_x))
        
        if self.weapon_type == "red": # Charged bullet blink
            now = pygame.time.get_ticks()
            if (now // CHARGED_BULLET_BLINK_INTERVAL) % 2 == 0:
                self._draw_charged_bullet_image(CHARGED_BULLET_COLOR_PRIMARY, CHARGED_BULLET_COLOR_SECONDARY)
            else:
                self._draw_charged_bullet_image(CHARGED_BULLET_COLOR_SECONDARY, CHARGED_BULLET_COLOR_PRIMARY)
            
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

        hits_platforms = pygame.sprite.spritecollide(self, platforms, False)
        if hits_platforms:
            if self.is_explosive:
                # Signal for explosion
                return "explode"
            elif self.is_shrapnel and self.bounces_remaining > 0:
                # Simple bounce logic for shrapnel
                for platform in hits_platforms:
                    # Determine collision side and reverse velocity component
                    if self.vel_x > 0 and self.rect.right > platform.rect.left and self.rect.left < platform.rect.left:
                        self.vel_x *= -1
                        self.rect.right = platform.rect.left -1 # Move out of collision
                    elif self.vel_x < 0 and self.rect.left < platform.rect.right and self.rect.right > platform.rect.right:
                        self.vel_x *= -1
                        self.rect.left = platform.rect.right + 1

                    if self.vel_y > 0 and self.rect.bottom > platform.rect.top and self.rect.top < platform.rect.top:
                        self.vel_y *= -1
                        self.rect.bottom = platform.rect.top - 1
                    elif self.vel_y < 0 and self.rect.top < platform.rect.bottom and self.rect.bottom > platform.rect.bottom:
                        self.vel_y *= -1
                        self.rect.top = platform.rect.bottom + 1
                self.bounces_remaining -= 1
            else:
                self.kill() # Remove bullet if it hits a platform and is not explosive/shrapnel or no bounces left

        # Remove if off-screen (using game's level dimensions - though camera moves freely, bullets should still be culled)
        # We'll use a large arbitrary boundary if no specific level_width/height is set to prevent infinite bullets
        boundary_x = self.game.level_width if self.game and self.game.level_width else WIDTH * 3
        boundary_y = self.game.level_height if self.game and self.game.level_height else HEIGHT * 3

        if self.rect.right < -boundary_x or self.rect.left > boundary_x * 2 or \
           self.rect.bottom < -boundary_y or self.rect.top > boundary_y * 2:
            if self.is_explosive:
                return "explode" # Explode if goes off screen
            self.kill()
        return None # No special action

class ChaserEnemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_color):
        super().__init__()
        self.image = pygame.Surface([40, 40], pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, enemy_color, (0, 0, 40, 40))
        pygame.draw.circle(self.image, (255, 255, 255), (15, 15), 5)
        pygame.draw.circle(self.image, (255, 255, 255), (25, 15), 5)
        pygame.draw.circle(self.image, (0, 0, 0), (15, 15), 2)
        pygame.draw.circle(self.image, (0, 0, 0), (25, 15), 2)

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed_horizontal = 2
        self.velocity_y = 0
        self.health = 3
        self.detection_range = 300

    def update(self, player_rect, platforms):
        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0
                elif self.velocity_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity_y = 0

        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        
        distance = math.sqrt(dx**2 + dy**2)

        if distance <= self.detection_range:
            if abs(dx) > 5:
                if dx > 0:
                    self.rect.x += self.speed_horizontal
                else:
                    self.rect.x -= self.speed_horizontal
        
        # Enemy movement is not clamped to level_width/height.

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()
            return True
        return False

    # Method to get editable properties
    def get_properties(self):
        return {"detection_range": self.detection_range} # Using detection_range as an example

    # Method to set properties
    def set_properties(self, props):
        if "detection_range" in props:
            self.detection_range = int(props["detection_range"])


class PatrolEnemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_color, patrol_range=100):
        super().__init__()
        self.image = pygame.Surface([35, 35], pygame.SRCALPHA)
        pygame.draw.circle(self.image, enemy_color, (17, 17), 17)
        pygame.draw.circle(self.image, (255, 255, 255), (17, 17), 5)
        pygame.draw.circle(self.image, (0, 0, 0), (17, 17), 2)

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed_horizontal = 1.5
        self.velocity_y = 0
        self.health = 2
        self.patrol_start_x = x
        self.patrol_range = patrol_range
        self.direction = 1

    def update(self, player_rect, platforms):
        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0
                elif self.velocity_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity_y = 0

        self.rect.x += self.speed_horizontal * self.direction

        if self.direction == 1 and self.rect.centerx > self.patrol_start_x + self.patrol_range:
            self.direction = -1
        elif self.direction == -1 and self.rect.centerx < self.patrol_start_x - self.patrol_range:
            self.direction = 1
        
        # Enemy movement is not clamped to level_width/height.

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()
            return True
        return False

    # Method to get editable properties
    def get_properties(self):
        return {"patrol_range": self.patrol_range}

    # Method to set properties
    def set_properties(self, props):
        if "patrol_range" in props:
            self.patrol_range = int(props["patrol_range"])
            self.patrol_start_x = self.rect.centerx # Reset patrol start to current position


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, platform_color, orientation="horizontal", dies_on_touch=False, is_hookable=False):
        super().__init__()
        self.platform_color = platform_color
        self.orientation = orientation
        self.dies_on_touch = dies_on_touch # New property
        self.is_hookable = is_hookable # New property
        self.image = pygame.Surface([width, height])
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self._draw_image()

    def _draw_image(self):
        self.image = pygame.Surface([self.rect.width, self.rect.height])
        self.image.fill(self.platform_color)
        if self.dies_on_touch: # Add a visual indicator for death blocks
            pygame.draw.rect(self.image, (255, 0, 0), self.image.get_rect(), 3) # Red border
            pygame.draw.line(self.image, (255, 0, 0), (0, 0), (self.rect.width, self.rect.height), 3)
            pygame.draw.line(self.image, (255, 0, 0), (self.rect.width, 0), (0, self.rect.height), 3)
        if self.is_hookable: # Add a visual indicator for hookable platforms
            pygame.draw.rect(self.image, (150, 0, 255), self.image.get_rect(), 2) # Purple border


    # Method to get editable properties
    def get_properties(self):
        return {
            "width": self.rect.width,
            "height": self.rect.height,
            "orientation": self.orientation,
            "dies_on_touch": self.dies_on_touch,
            "is_hookable": self.is_hookable
        }

    # Method to set properties
    def set_properties(self, props):
        if "width" in props and "height" in props:
            new_width = int(props["width"])
            new_height = int(props["height"])
            self.rect.width = new_width
            self.rect.height = new_height
        if "orientation" in props:
            self.orientation = props["orientation"]
        if "dies_on_touch" in props:
            self.dies_on_touch = props["dies_on_touch"] in ['True', 'true', True] # Convert string to bool
        if "is_hookable" in props:
            self.is_hookable = props["is_hookable"] in ['True', 'true', True] # Convert string to bool
        self._draw_image() # Redraw image after property changes


class Collectible(pygame.sprite.Sprite):
    def __init__(self, x, y, collectible_type, colors):
        super().__init__()
        self.type = collectible_type
        self.colors = colors
        self.image = self._create_image(collectible_type, colors)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def _create_image(self, collectible_type, colors):
        if collectible_type == "score":
            image = pygame.Surface([20, 20])
            image.fill(colors.COLLECTIBLE_COLOR)
        elif collectible_type == "health":
            image = pygame.Surface([25, 25])
            image.fill(colors.PLAYER_COLOR)
            pygame.draw.rect(image, colors.WHITE, image.get_rect(), 2)
            pygame.draw.line(image, colors.WHITE, (image.get_width() // 2, 5), (image.get_width() // 2, image.get_height() - 5), 3)
            pygame.draw.line(image, colors.WHITE, (5, image.get_height() // 2), (image.get_width() - 5, image.get_height() // 2), 3)
        elif collectible_type == "speed":
            image = pygame.Surface([25, 25])
            image.fill(colors.BULLET_COLOR)
            points = [(12, 0), (24, 12), (18, 12), (24, 24), (0, 12), (6, 12), (0, 0)]
            pygame.draw.polygon(image, colors.WHITE, points)
        elif collectible_type == "charge_powerup":
            image = pygame.Surface([25, 25], pygame.SRCALPHA)
            pygame.draw.circle(image, (255, 100, 0), (12, 12), 10) # Orange core
            pygame.draw.circle(image, (255, 200, 0), (12, 12), 12, 2) # Yellow outline
            pygame.draw.line(image, (255, 255, 255), (5, 12), (20, 12), 2) # Plus sign horizontal
            pygame.draw.line(image, (255, 255, 255), (12, 5), (12, 20), 2) # Plus sign vertical
        elif collectible_type == "blue_weapon_powerup":
            image = pygame.Surface([25, 25], pygame.SRCALPHA)
            pygame.draw.rect(image, (0, 100, 255), (5, 10, 15, 5)) # Blue rectangle
            pygame.draw.circle(image, (0, 100, 255), (20, 12), 3) # Barrel
            pygame.draw.polygon(image, (200, 200, 200), [(5,10), (0,15), (5,20)]) # Handle
        elif collectible_type == "red_weapon_powerup":
            image = pygame.Surface([25, 25], pygame.SRCALPHA)
            pygame.draw.rect(image, (255, 50, 0), (5, 10, 18, 5)) # Red rectangle
            pygame.draw.circle(image, (255, 50, 0), (23, 12), 4) # Barrel
            pygame.draw.line(image, (200, 200, 200), (5, 10), (0, 15), 3) # Handle
            pygame.draw.line(image, (200, 200, 200), (0, 15), (5, 20), 3)
        elif collectible_type == "purple_weapon_powerup":
            image = pygame.Surface([25, 25], pygame.SRCALPHA)
            pygame.draw.circle(image, (150, 0, 255), (12, 12), 10) # Purple circle
            pygame.draw.circle(image, (255, 255, 0), (12, 12), 4) # Yellow core
            pygame.draw.line(image, (200, 200, 200), (5, 12), (20, 12), 2) # Plus sign horizontal
            pygame.draw.line(image, (200, 200, 200), (12, 5), (12, 20), 2) # Plus sign vertical
        return image

    def get_properties(self):
        return {} # Type is read-only for now

    def set_properties(self, props):
        pass # No settable properties for now


class Key(pygame.sprite.Sprite):
    def __init__(self, x, y, key_id, key_color):
        super().__init__()
        self.key_id = key_id
        self.key_color = key_color
        self.image = pygame.Surface([20, 20], pygame.SRCALPHA)
        self._draw_key_image()
        self.rect = self.image.get_rect(center=(x, y))

    def _draw_key_image(self):
        self.image.fill((0, 0, 0, 0)) # Clear for redraw
        pygame.draw.circle(self.image, self.key_color, (10, 5), 5) # Head
        pygame.draw.rect(self.image, self.key_color, (8, 10, 4, 10)) # Body
        pygame.draw.line(self.image, self.key_color, (8, 18), (5, 18), 2) # Teeth
        pygame.draw.line(self.image, self.key_color, (8, 15), (5, 15), 2)

    def get_properties(self):
        return {"id": self.key_id}

    def set_properties(self, props):
        if "id" in props:
            self.key_id = str(props["id"])


class Door(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, door_id, door_color, required_key_id=None, required_weapon_type=None, dies_on_touch=False, is_hookable=False):
        super().__init__()
        self.door_id = door_id
        self.required_key_id = required_key_id
        self.required_weapon_type = required_weapon_type
        self.width = width
        self.height = height
        self.door_color = door_color
        self.dies_on_touch = dies_on_touch # New property
        self.is_hookable = is_hookable # New property
        self.image = pygame.Surface([width, height])
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_open = False
        self._draw_image()

    def _draw_image(self):
        self.image.fill(self.door_color)
        pygame.draw.rect(self.image, (0,0,0), (0,0,self.width,self.height), 3) # Border
        if self.dies_on_touch: # Add a visual indicator for death blocks
            pygame.draw.rect(self.image, (255, 0, 0), self.image.get_rect(), 3) # Red border
            pygame.draw.line(self.image, (255, 0, 0), (0, 0), (self.width, self.height), 3)
            pygame.draw.line(self.image, (255, 0, 0), (self.width, 0), (0, self.height), 3)
        if self.is_hookable: # Add a visual indicator for hookable platforms
            pygame.draw.rect(self.image, (150, 0, 255), self.image.get_rect(), 2) # Purple border

    def open_door(self):
        self.kill() # Remove the door when opened
        self.is_open = True

    def get_properties(self):
        return {
            "id": self.door_id,
            "required_key_id": self.required_key_id if self.required_key_id else "",
            "required_weapon_type": self.required_weapon_type if self.required_weapon_type else "",
            "dies_on_touch": self.dies_on_touch,
            "is_hookable": self.is_hookable
        }

    def set_properties(self, props):
        if "id" in props:
            self.door_id = str(props["id"])
        if "required_key_id" in props:
            # Ensure empty string is converted to None
            self.required_key_id = str(props["required_key_id"]) if props["required_key_id"] else None
        if "required_weapon_type" in props:
            # Ensure empty string is converted to None
            self.required_weapon_type = str(props["required_weapon_type"]) if props["required_weapon_type"] else None
        if "dies_on_touch" in props:
            self.dies_on_touch = props["dies_on_touch"] in ['True', 'true', True]
        if "is_hookable" in props:
            self.is_hookable = props["is_hookable"] in ['True', 'true', True]
        self._draw_image() # Redraw image after property changes


class Spike(pygame.sprite.Sprite):
    def __init__(self, x, y, spike_color, instant_kill=False): # Added instant_kill
        super().__init__()
        self.width = 30
        self.height = 20
        self.instant_kill = instant_kill # New property
        self.image = pygame.Surface([self.width, self.height], pygame.SRCALPHA)
        # Draw a triangle pointing upwards
        points = [(0, self.height), (self.width // 2, 0), (self.width, self.height)]
        pygame.draw.polygon(self.image, spike_color, points)
        # Position rect directly at given x, y (which should be its topleft)
        self.rect = self.image.get_rect(topleft=(x, y))
        self._draw_image()

    def _draw_image(self):
        self.image.fill((0, 0, 0, 0)) # Clear for redraw
        points = [(0, self.height), (self.width // 2, 0), (self.width, self.height)]
        pygame.draw.polygon(self.image, (120, 120, 120), points) # Base color
        if self.instant_kill: # Add a visual indicator for instant kill spikes
            pygame.draw.polygon(self.image, (255, 0, 0), points, 2) # Red outline
            pygame.draw.line(self.image, (255, 0, 0), (self.width // 4, self.height // 2), (self.width * 3 // 4, self.height // 2), 2)
            pygame.draw.line(self.image, (255, 0, 0), (self.width // 2, self.height // 4), (self.width // 2, self.height * 3 // 4), 2)


    def get_properties(self):
        return {"instant_kill": self.instant_kill}

    def set_properties(self, props):
        if "instant_kill" in props:
            self.instant_kill = props["instant_kill"] in ['True', 'true', True]
        self._draw_image() # Redraw image after property changes


class LevelExit(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        pygame.draw.rect(self.image, (255, 255, 255), (0, 0, width, height), 3) # White border
        self.rect = self.image.get_rect(topleft=(x, y))

    def get_properties(self):
        return {} # No editable properties for now

    def set_properties(self, props):
        pass # No settable properties for now


# --- Level Data (simulating a level editor) ---
# This will now serve as a fallback if no levels are found in the 'levels' folder.
LEVEL_DATA = [
    {   # Level 1 (Maze-like, now spanning a larger world)
        "level_width": WIDTH * 2, # Define level width (for camera clamping, not player movement)
        "level_height": HEIGHT * 2, # Define level height (for camera clamping, not player movement)
        "player_start": (50, HEIGHT - 65), # Start near bottom-left
        "platforms": [
            (0, HEIGHT - 50, WIDTH * 2, 50, "horizontal", False, False), # Ground floor, spans entire world width
            (0, HEIGHT - 200, 200, 20, "horizontal", False, True), # Hookable platform
            (250, HEIGHT - 200, 150, 20, "horizontal", False, False),
            (450, HEIGHT - 200, 100, 20, "horizontal", True, False), # Death platform
            (600, HEIGHT - 200, 200, 20, "horizontal", False, False),
            (850, HEIGHT - 200, 150, 20, "horizontal", False, True),
            (1050, HEIGHT - 200, 150, 20, "horizontal", False, False),

            (200, HEIGHT - 350, 150, 20, "horizontal", False, True),
            (400, HEIGHT - 350, 200, 20, "horizontal", False, False),
            (650, HEIGHT - 350, 100, 20, "horizontal", True, False),
            (900, HEIGHT - 350, 200, 20, "horizontal", False, True),

            (0, HEIGHT - 500, 100, 20, "horizontal", False, False),
            (150, HEIGHT - 500, 250, 20, "horizontal", False, True),
            (450, HEIGHT - 500, 150, 20, "horizontal", False, False),
            (700, HEIGHT - 500, 200, 20, "horizontal", True, False),
            (1000, HEIGHT - 500, 200, 20, "horizontal", False, True),

            (100, HEIGHT - 650, 200, 20, "horizontal", False, False),
            (350, HEIGHT - 650, 100, 20, "horizontal", False, True),
            (500, HEIGHT - 650, 250, 20, "horizontal", False, False),
            (800, HEIGHT - 650, 150, 20, "horizontal", True, False),
            (1050, HEIGHT - 650, 150, 20, "horizontal", False, True),
            (300, HEIGHT - 450, 20, 100, "vertical", False, False), # Example vertical platform

            # New platforms to extend into the larger world
            (WIDTH + 50, HEIGHT - 150, 200, 20, "horizontal", False, True),
            (WIDTH + 300, HEIGHT - 300, 150, 20, "horizontal", True, False),
            (WIDTH + 600, HEIGHT - 450, 250, 20, "horizontal", False, True),
            (WIDTH + 100, HEIGHT - 600, 100, 20, "horizontal", False, False),
            (WIDTH + 400, HEIGHT - 750, 200, 20, "horizontal", True, False)
        ],
        "enemies": [
            {"type": "chaser", "pos": (300, HEIGHT - 250)},
            {"type": "patrol", "pos": (700, HEIGHT - 250), "range": 80},
            {"type": "chaser", "pos": (100, HEIGHT - 550)},
            {"type": "patrol", "pos": (600, HEIGHT - 550), "range": 50},
            {"type": "chaser", "pos": (WIDTH + 150, HEIGHT - 200)}, # New enemy in extended area
            {"type": "patrol", "pos": (WIDTH + 400, HEIGHT - 350), "range": 100} # New enemy
        ],
        "collectibles": [
            {"type": "score", "pos": (100, HEIGHT - 100)},
            {"type": "health", "pos": (300, HEIGHT - 300)},
            {"type": "speed", "pos": (950, HEIGHT - 100)},
            {"type": "charge_powerup", "pos": (WIDTH // 2, HEIGHT - 100)}, # Power-up de disparo cargado
            {"type": "blue_weapon_powerup", "pos": (50, HEIGHT - 400)},
            {"type": "red_weapon_powerup", "pos": (WIDTH - 50, HEIGHT - 400)},
            {"type": "purple_weapon_powerup", "pos": (WIDTH // 2, HEIGHT - 600)},
            {"type": "score", "pos": (500, HEIGHT - 450)},
            {"type": "health", "pos": (850, HEIGHT - 450)},
            {"type": "score", "pos": (WIDTH + 100, HEIGHT - 100)}, # New collectibles
            {"type": "speed", "pos": (WIDTH + 500, HEIGHT - 250)}
        ],
        "obstacles": [
            {"type": "spike", "pos": (200, HEIGHT - 70), "instant_kill": False},
            {"type": "spike", "pos": (400, HEIGHT - 70), "instant_kill": True}, # Instant kill spike
            {"type": "spike", "pos": (600, HEIGHT - 70), "instant_kill": False},
            {"type": "spike", "pos": (800, HEIGHT - 70), "instant_kill": True},
            {"type": "spike", "pos": (1000, HEIGHT - 70), "instant_kill": False},
            {"type": "spike", "pos": (250, HEIGHT - 220), "instant_kill": False},
            {"type": "spike", "pos": (450, HEIGHT - 220), "instant_kill": True},
            {"type": "spike", "pos": (WIDTH + 200, HEIGHT - 70), "instant_kill": False} # New spike
        ],
        "keys": [
            {"id": "red_key", "pos": (100, HEIGHT - 300), "color": (255, 0, 0)},
            {"id": "blue_key", "pos": (WIDTH - 100, HEIGHT - 300), "color": (0, 0, 255)},
            {"id": "gold_key", "pos": (WIDTH + 700, HEIGHT - 500), "color": (255, 215, 0)} # New key
        ],
        "doors": [
            {"id": "door_1", "pos": (400, HEIGHT - 250, 50, 100), "color": (100, 50, 50), "required_key_id": "red_key", "dies_on_touch": False, "is_hookable": True},
            {"id": "door_2", "pos": (800, HEIGHT - 250, 50, 100), "color": (50, 50, 100), "required_weapon_type": "blue", "dies_on_touch": True, "is_hookable": False}, # Death door
            {"id": "door_gold", "pos": (WIDTH + 800, HEIGHT - 600, 50, 100), "color": (200, 150, 0), "required_key_id": "gold_key", "required_weapon_type": "red", "dies_on_touch": False, "is_hookable": True} # New door with key and weapon
        ],
        "exit": (WIDTH * 2 - 100, HEIGHT - 700, 50, 50) # Exit near top-right of the larger world
    },
    {   # Level 2 (Another Maze-like)
        "level_width": WIDTH, # This level remains screen-sized
        "level_height": HEIGHT, # This level remains screen-sized
        "player_start": (50, HEIGHT - 65),
        "platforms": [
            (0, HEIGHT - 50, WIDTH, 50, "horizontal", False, False), # Ground
            (100, HEIGHT - 150, 150, 20, "horizontal", False, True),
            (WIDTH - 250, HEIGHT - 150, 200, 20, "horizontal", True, False),
            (WIDTH // 2 - 100, HEIGHT - 250, 200, 20, "horizontal", False, True),
            (0, HEIGHT - 350, 180, 20, "horizontal", False, False),
            (WIDTH - 180, HEIGHT - 350, 180, 20, "horizontal", True, False),
            (250, HEIGHT - 450, 150, 20, "horizontal", False, True),
            (WIDTH - 400, HEIGHT - 450, 150, 20, "horizontal", False, False),
            (WIDTH // 2 - 50, HEIGHT - 550, 100, 20, "horizontal", True, False),
            (0, HEIGHT - 650, 120, 20, "horizontal", False, True),
            (WIDTH - 120, HEIGHT - 650, 120, 20, "horizontal", False, False)
        ],
        "enemies": [
            {"type": "chaser", "pos": (WIDTH // 2, HEIGHT - 100)},
            {"type": "patrol", "pos": (175, HEIGHT - 200), "range": 50},
            {"type": "chaser", "pos": (WIDTH - 175, HEIGHT - 200)},
            {"type": "patrol", "pos": (WIDTH // 2, HEIGHT - 300), "range": 70},
            {"type": "chaser", "pos": (100, HEIGHT - 400)}
        ],
        "collectibles": [
            {"type": "score", "pos": (150, HEIGHT - 100)},
            {"type": "health", "pos": (WIDTH - 100, HEIGHT - 100)},
            {"type": "speed", "pos": (WIDTH // 2, HEIGHT - 300)},
            {"type": "charge_powerup", "pos": (200, HEIGHT - 400)}, # Power-up de disparo cargado
            {"type": "blue_weapon_powerup", "pos": (50, HEIGHT - 500)},
            {"type": "red_weapon_powerup", "pos": (WIDTH - 50, HEIGHT - 500)},
            {"type": "purple_weapon_powerup", "pos": (WIDTH // 2, HEIGHT - 100)},
            {"type": "score", "pos": (50, HEIGHT - 400)},
            {"type": "health", "pos": (WIDTH - 50, HEIGHT - 400)},
            {"type": "score", "pos": (WIDTH // 2, HEIGHT - 600)}
        ],
        "obstacles": [
            {"type": "spike", "pos": (50, HEIGHT - 70), "instant_kill": False},
            {"type": "spike", "pos": (WIDTH - 100, HEIGHT - 70), "instant_kill": True},
            {"type": "spike", "pos": (WIDTH // 2 - 25, HEIGHT - 270), "instant_kill": False},
            {"type": "spike", "pos": (100, HEIGHT - 370), "instant_kill": True},
            {"type": "spike", "pos": (WIDTH - 150, HEIGHT - 370), "instant_kill": False}
        ],
        "keys": [
            {"id": "green_key", "pos": (WIDTH // 2 + 50, HEIGHT - 500), "color": (0, 255, 0)}
        ],
        "doors": [
            {"id": "door_3", "pos": (WIDTH // 2 - 25, HEIGHT - 400, 50, 100), "color": (80, 80, 80), "required_key_id": "green_key", "dies_on_touch": False, "is_hookable": True},
            {"id": "door_4", "pos": (WIDTH // 2 + 100, HEIGHT - 400, 50, 100), "color": (80, 80, 80), "required_weapon_type": "purple", "dies_on_touch": True, "is_hookable": False}
        ],
        "exit": (WIDTH // 2 - 25, HEIGHT - 600, 50, 50)
    }
    # Add more levels here
]
# --- Custom Input Box (for saving filename and editing properties) ---
class InputBox:
    def __init__(self, x, y, w, h, font, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = (100, 100, 100)
        self.color_active = (200, 200, 200)
        self.color = self.color_inactive
        self.text = text
        self.font = font
        self.active = False
        self.txt_surface = self.font.render(text, True, (255, 255, 255))
        self.placeholder = ""
        self.is_numeric = False # Flag to allow only numeric input
        self.is_boolean = False # Flag for boolean (True/False) input
        self.dropdown_options = None # List of options for a dropdown
        self.show_dropdown = False
        self.dropdown_rects = [] # To store rects for each dropdown option

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if a dropdown option was clicked first, if dropdown is currently visible
            if self.show_dropdown and self.dropdown_options:
                for i, option_rect in enumerate(self.dropdown_rects):
                    if option_rect.collidepoint(event.pos):
                        self.set_text(self.dropdown_options[i])
                        self.show_dropdown = False
                        self.active = False
                        self.color = self.color_inactive
                        return "submit" # Selection made, consume event

            # Now, handle clicks on the input box itself
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
                if self.dropdown_options:
                    self.show_dropdown = self.active # Show dropdown only if input box is active
                else:
                    self.show_dropdown = False
            
            self.color = self.color_active if self.active else self.color_inactive
        
        if event.type == pygame.KEYDOWN and self.active and not self.show_dropdown: # Only process keydown if dropdown is not shown
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
                self.color = self.color_inactive
                return "submit" # Signal that input is complete
            else:
                if self.is_numeric:
                    if event.unicode.isdigit():
                        self.text += event.unicode
                elif self.is_boolean:
                    # Allow only 't', 'r', 'u', 'e', 'f', 'a', 'l', 's', 'e'
                    if event.unicode.lower() in 'truefals':
                        self.text += event.unicode
                else:
                    self.text += event.unicode
            self.txt_surface = self.font.render(self.text, True, (255, 255, 255))
        return None

    def draw(self, screen):
        # Render the text
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        # Render the input box
        pygame.draw.rect(screen, self.color, self.rect, 2)

        # Render placeholder if text is empty and not active
        if not self.text and not self.active and self.placeholder:
            placeholder_surface = self.font.render(self.placeholder, True, (150, 150, 150))
            screen.blit(placeholder_surface, (self.rect.x + 5, self.rect.y + 5))

        # Draw dropdown if active
        if self.show_dropdown and self.dropdown_options:
            dropdown_y = self.rect.bottom + 5
            self.dropdown_rects = [] # Clear for new drawing
            for option in self.dropdown_options:
                option_rect = pygame.Rect(self.rect.x, dropdown_y, self.rect.width, self.rect.height)
                self.dropdown_rects.append(option_rect)
                pygame.draw.rect(screen, (80, 80, 80), option_rect) # Dropdown background
                pygame.draw.rect(screen, (150, 150, 150), option_rect, 1) # Dropdown border
                option_surface = self.font.render(option, True, (255, 255, 255))
                screen.blit(option_surface, (option_rect.x + 5, option_rect.y + 5))
                dropdown_y += self.rect.height + 2

    def get_text(self):
        return self.text
    
    def set_text(self, text):
        self.text = str(text)
        self.txt_surface = self.font.render(self.text, True, (255, 255, 255))

    def set_placeholder(self, placeholder):
        self.placeholder = placeholder

    def set_numeric(self, is_numeric):
        self.is_numeric = is_numeric
        self.is_boolean = False # Cannot be both

    def set_boolean(self, is_boolean):
        self.is_boolean = is_boolean
        self.is_numeric = False # Cannot be both

    def set_dropdown_options(self, options):
        self.dropdown_options = options
        if not options:
            self.show_dropdown = False


# --- Editor Panel UI ---
class EditorPanel:
    def __init__(self, x, y, width, height, game_instance):
        self.rect = pygame.Rect(x, y, width, height)
        self.game = game_instance
        self.font = pygame.font.Font(None, 24)
        self.button_height = 30
        self.padding = 5
        self.buttons = []
        self._create_buttons()

    def _create_buttons(self):
        # Define buttons with their tool type and display text
        button_data = [
            ("player_start", "Inicio del Jugador"),
            ("platform", "Plataforma Horizontal"), # Renamed for clarity
            ("vertical_platform", "Plataforma Vertical"), # New button
            ("spike", "Spike"),
            ("chaser_enemy", "Enemigo Perseguidor"),
            ("patrol_enemy", "Enemigo Patrulla"),
            ("score_collectible", "Puntuación"),
            ("health_collectible", "Vida"),
            ("speed_collectible", "Velocidad"),
            ("charge_powerup_collectible", "Power-up Carga"),
            ("blue_weapon_powerup_collectible", "Arma Azul"),
            ("red_weapon_powerup_collectible", "Arma Roja"),
            ("purple_weapon_powerup_collectible", "Arma Púrpura"),
            ("key", "Llave"),
            ("door", "Puerta"),
            ("level_exit", "Salida de Nivel"),
            ("load_level", "Cargar Nivel"), # New button
            ("test_level", "Probar Nivel") # New button
        ]

        current_y = self.rect.top + self.padding
        for tool_type, text in button_data:
            button_rect = pygame.Rect(self.rect.left + self.padding, current_y, self.rect.width - 2 * self.padding, self.button_height)
            self.buttons.append({"rect": button_rect, "tool_type": tool_type, "text": text})
            current_y += self.button_height + self.padding

    def draw(self, screen):
        pygame.draw.rect(screen, (60, 60, 80), self.rect, border_radius=5) # Panel background
        pygame.draw.rect(screen, (100, 100, 120), self.rect, 2, border_radius=5) # Panel border

        for button in self.buttons:
            color = (100, 100, 120)
            text_color = (255, 255, 255)
            if self.game.editor_selected_tool == button["tool_type"]:
                color = (0, 150, 0) # Highlight selected tool
            
            pygame.draw.rect(screen, color, button["rect"], border_radius=3)
            pygame.draw.rect(screen, (200, 200, 200), button["rect"], 1, border_radius=3) # Button border

            text_surface = self.font.render(button["text"], True, text_color)
            text_rect = text_surface.get_rect(center=button["rect"].center)
            screen.blit(text_surface, text_rect)

    def handle_click(self, pos):
        for button in self.buttons:
            if button["rect"].collidepoint(pos):
                if button["tool_type"] == "load_level":
                    self.game.game_state = GAME_STATE_LOAD_LEVEL_MENU # Change state to load menu
                    self.game.available_levels_for_load = self.game._get_level_filenames_from_folder() # Refresh list
                    print("Abriendo menú de carga de niveles.")
                elif button["tool_type"] == "test_level":
                    self.game._save_current_editor_state()
                    self.game.game_state = GAME_STATE_PLAYING_FROM_EDITOR
                    self.game.load_level_from_dict(self.game.editor_saved_level_state)
                    print("Iniciando prueba de nivel.")
                else:
                    self.game.editor_selected_tool = button["tool_type"]
                    self.game.editor_selected_sprite = None # Clear selected sprite when changing tool
                    self.game.resizing_platform = False # Stop resizing
                    print(f"Herramienta seleccionada: {button['text']}")
                return True
        return False


# --- Game Class ---
class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = SCREEN
        self.clock = pygame.time.Clock()
        self.sound_manager = SoundManager()

        # Define colors as instance attributes (Metroid-like palette)
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0) 
        self.PLAYER_COLOR = (0, 180, 0)
        self.CHASER_ENEMY_COLOR = (200, 50, 50)
        self.PATROL_ENEMY_COLOR = (200, 120, 0)
        self.BULLET_COLOR = (255, 215, 0) # Default bullet color (Gold)
        self.GRID_COLOR = (40, 40, 40)
        self.BACKGROUND_COLOR = (20, 20, 30)
        self.PLATFORM_COLOR = (80, 80, 90)
        self.COLLECTIBLE_COLOR = (255, 215, 0)
        self.EXIT_COLOR = (0, 150, 0)
        self.SPIKE_COLOR = (120, 120, 120)
        self.AIM_CONE_COLOR = (255, 0, 0, 100)
        self.LINK_HIGHLIGHT_COLOR = (255, 255, 0) # Yellow for linking
        self.PURPLE_ARC_COLOR = (150, 0, 255, 100) # Purple with transparency for arc
        self.PURPLE_HOOK_COLOR = (150, 0, 255) # Solid purple for hook line

        self.font_large = pygame.font.Font(None, 74)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.font_tiny = pygame.font.Font(None, 24)


        self.game_state = GAME_STATE_MENU
        self.score = 0
        self.current_level_idx = 0
        self.FPS = 60

        self.all_sprites = pygame.sprite.Group()
        self.players = pygame.sprite.GroupSingle()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.collectibles = pygame.sprite.Group()
        self.level_exit = pygame.sprite.GroupSingle()
        self.obstacles = pygame.sprite.Group()
        self.keys = pygame.sprite.Group() # New group for keys
        self.doors = pygame.sprite.Group() # New group for doors

        # Default level dimensions (will be overwritten by loaded level data)
        # These are now conceptual boundaries for camera clamping, not hard player limits.
        self.level_width = WIDTH * 2
        self.level_height = HEIGHT * 2

        self.player = Player(self.PLAYER_COLOR, self) # Pass self (Game instance)
        self.players.add(self.player)

        self.camera_offset_x = 0
        self.camera_offset_y = 0

        self.player_keys = {} # Dictionary to store collected keys: {key_id: True}

        self.editor_selected_tool = "platform" # Default tool for editor
        self.editor_tool_size = (100, 20) # Default size for horizontal platforms
        self.GRID_SIZE = 50 # Define grid size for snapping

        # Initialize EditorPanel
        self.editor_panel = EditorPanel(10, 10, 200, HEIGHT - 20, self) # Panel on left side

        # For saving level input
        self.filename_input_box = InputBox(WIDTH // 2 - 200, HEIGHT // 2 - 25, 400, 50, self.font_medium)
        self.filename_input_box.set_placeholder("Nombre del nivel")

        # For editing properties
        self.property_input_boxes = {} # {property_name: InputBox_instance}
        self.editing_sprite = None # The sprite currently being edited
        self.property_edit_message = ""
        self.available_property_ids = {} # For displaying hints in property editor

        # Editor drag and drop variables
        self.editor_dragging = False
        self.editor_dragged_sprite = None
        self.editor_drag_offset_x = 0
        self.editor_drag_offset_y = 0
        self.last_click_time_editor = 0 # For double click detection in editor

        # Editor selection and resizing variables
        self.editor_selected_sprite = None # The sprite currently selected for rotation/resizing
        self.resizing_platform = False
        self.resizing_edge = None # "left" or "right"
        self.initial_mouse_pos = None
        self.initial_platform_rect = None

        # Editor camera panning variables
        self.editor_panning = False
        self.editor_pan_start_mouse_pos = None
        self.editor_camera_offset_x = 0
        self.editor_camera_offset_y = 0
        self.initial_editor_camera_offset_x = 0
        self.initial_editor_camera_offset_y = 0


        self.loaded_levels_from_files = [] # List to store level data loaded from files
        self.editor_saved_level_state = None # To store level data when testing from editor

        # For loading levels in editor
        self.available_levels_for_load = []
        self.load_level_overlay_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 250, 400, 500)


        self._load_levels_from_files() # Load levels from files at startup

    def _get_level_filenames_from_folder(self):
        levels_dir = "levels"
        if not os.path.exists(levels_dir):
            os.makedirs(levels_dir)
            return []
        
        json_files = [f for f in os.listdir(levels_dir) if f.endswith('.json')]
        json_files.sort()
        return json_files

    def _load_levels_from_files(self):
        self.loaded_levels_from_files = []
        levels_dir = "levels"
        if not os.path.exists(levels_dir):
            os.makedirs(levels_dir) # Create directory if it doesn't exist
            print(f"Carpeta '{levels_dir}' creada.")
            # If no folder, no files, so use default data directly
            for i, data in enumerate(LEVEL_DATA):
                self.loaded_levels_from_files.append({"filename": f"default_level_{i+1}.json", "data": data})
            return

        json_files = [f for f in os.listdir(levels_dir) if f.endswith('.json')]
        json_files.sort() # Sort alphabetically for consistent level order

        if not json_files:
            print(f"No se encontraron archivos .json en la carpeta '{levels_dir}'. Se usarán los niveles por defecto.")
            for i, data in enumerate(LEVEL_DATA):
                self.loaded_levels_from_files.append({"filename": f"default_level_{i+1}.json", "data": data})
            return

        for filename in json_files:
            file_path = os.path.join(levels_dir, filename)
            try:
                with open(file_path, 'r') as f:
                    level_data = json.load(f)
                    self.loaded_levels_from_files.append({"filename": filename, "data": level_data})
                print(f"Nivel '{filename}' cargado desde archivo.")
            except json.JSONDecodeError as e:
                print(f"Error al decodificar JSON en '{filename}': {e}")
            except Exception as e:
                print(f"Error al cargar '{filename}': {e}")
        
        if not self.loaded_levels_from_files:
            print("No se pudieron cargar niveles válidos desde la carpeta. Se usarán los niveles por defecto.")
            for i, data in enumerate(LEVEL_DATA):
                self.loaded_levels_from_files.append({"filename": f"default_level_{i+1}.json", "data": data})


    def _clear_all_sprites(self):
        self.all_sprites.empty()
        self.enemies.empty()
        self.bullets.empty()
        self.platforms.empty()
        self.collectibles.empty()
        self.level_exit = pygame.sprite.GroupSingle() # Re-initialize as empty GroupSingle
        self.obstacles.empty()
        self.keys.empty()
        self.doors.empty()
        self.all_sprites.add(self.player) # Always keep player

    def load_level_from_dict(self, level_data):
        self._clear_all_sprites()

        # Set level dimensions from data, or default to screen size if not specified
        # These are now for camera clamping, not hard player limits.
        self.level_width = level_data.get("level_width", WIDTH * 2) # Default to 2x screen size
        self.level_height = level_data.get("level_height", HEIGHT * 2) # Default to 2x screen size

        self.player.rect.center = level_data["player_start"]
        self.player.velocity_y = 0
        self.player.on_ground = False
        self.player.jump_count = 0
        self.player.health = self.player.max_health
        self.player.speed_horizontal = self.player.original_speed_horizontal
        self.player.speed_boost_active = False
        
        # Reset all weapon ammo and power-ups
        for weapon in self.player.weapon_data:
            self.player.weapon_data[weapon]["current_ammo"] = self.player.weapon_data[weapon]["max_ammo"]
        self.player.current_weapon = "normal"
        self.player.is_reloading = False
        self.player.reload_timer = 0
        self.player.has_weapon_powerup = {"blue": False, "red": False, "purple": False}

        self.player.invulnerable = True
        self.player.invulnerable_timer = pygame.time.get_ticks()
        self.player._draw_player_image() 
        self.player.is_dashing = False

        # Reset charge shot state
        self.player.is_charging_powerup_shot = False
        self.player.charge_powerup_start_time = 0
        self.player.charge_powerup_level = 0.0
        self.player.has_charge_powerup = False # Asegurarse de que el power-up se reinicie por nivel
        
        self.player.is_charging_red_weapon = False
        self.player.red_charge_start_time = 0
        self.player.red_charge_level = 0.0

        self.player.is_charging_purple_shot = False
        self.player.purple_charge_start_time = 0
        self.player.purple_charge_level = 0.0
        self.player.is_grappling = False
        self.player.grapple_attached_sprite = None
        self.player.grapple_target_pos = None

        self.player_keys = {} # Clear collected keys for new level

        for p_data in level_data["platforms"]:
            # Ensure orientation, dies_on_touch, is_hookable are passed when loading from file
            platform = Platform(p_data[0], p_data[1], p_data[2], p_data[3], self.PLATFORM_COLOR,
                                p_data[4] if len(p_data) > 4 else "horizontal",
                                p_data[5] if len(p_data) > 5 else False, # dies_on_touch
                                p_data[6] if len(p_data) > 6 else False) # is_hookable
            self.all_sprites.add(platform)
            self.platforms.add(platform)
        
        for e_data in level_data["enemies"]:
            if e_data["type"] == "chaser":
                enemy = ChaserEnemy(e_data["pos"][0], e_data["pos"][1], self.CHASER_ENEMY_COLOR)
            elif e_data["type"] == "patrol":
                enemy = PatrolEnemy(e_data["pos"][0], e_data["pos"][1], self.PATROL_ENEMY_COLOR, e_data.get("range", 100))
            self.all_sprites.add(enemy)
            self.enemies.add(enemy)

        for c_data in level_data["collectibles"]:
            collectible = Collectible(c_data["pos"][0], c_data["pos"][1], c_data["type"], self)
            self.all_sprites.add(collectible)
            self.collectibles.add(collectible)

        if "obstacles" in level_data:
            for o_data in level_data["obstacles"]:
                if o_data["type"] == "spike":
                    # Spikes now take their topleft directly, and instant_kill property
                    spike = Spike(o_data["pos"][0], o_data["pos"][1], self.SPIKE_COLOR, o_data.get("instant_kill", False))
                    self.all_sprites.add(spike)
                    self.obstacles.add(spike)
        
        if "keys" in level_data:
            for k_data in level_data["keys"]:
                key = Key(k_data["pos"][0], k_data["pos"][1], k_data["id"], tuple(k_data["color"])) # Convert list to tuple for color
                self.all_sprites.add(key)
                self.keys.add(key)
        
        if "doors" in level_data:
            for d_data in level_data["doors"]:
                door_color_val = d_data.get("color")
                if isinstance(door_color_val, list):
                    door_color_val = tuple(door_color_val)
                elif not isinstance(door_color_val, tuple):
                    door_color_val = (100, 100, 100) # Default if format is wrong

                door = Door(d_data.get("pos")[0], d_data.get("pos")[1], d_data.get("pos")[2], d_data.get("pos")[3], 
                            d_data.get("id"), door_color_val, d_data.get("required_key_id"), d_data.get("required_weapon_type"),
                            d_data.get("dies_on_touch", False), d_data.get("is_hookable", False)) # New properties
                self.all_sprites.add(door)
                self.doors.add(door)

        exit_data = level_data["exit"]
        if exit_data: # Ensure exit_data is not None
            exit_obj = LevelExit(exit_data[0], exit_data[1], exit_data[2], exit_data[3], self.EXIT_COLOR)
            self.all_sprites.add(exit_obj)
            self.level_exit.add(exit_obj)

        print(f"Nivel cargado desde diccionario.")
        return True

    def load_level_from_file_by_name(self, filename):
        levels_dir = "levels"
        file_path = os.path.join(levels_dir, filename)
        try:
            with open(file_path, 'r') as f:
                level_data = json.load(f)
                self.load_level_from_dict(level_data)
                self.game_state = GAME_STATE_EDITOR # Return to editor after loading
                print(f"Nivel '{filename}' cargado para edición.")
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON en '{filename}': {e}")
        except FileNotFoundError:
            print(f"Archivo de nivel '{filename}' no encontrado.")
        except Exception as e:
            print(f"Error al cargar '{filename}': {e}")

    def _get_current_editor_level_data(self):
        current_level_data = {
            "level_width": self.level_width, # Include level dimensions
            "level_height": self.level_height, # Include level dimensions
            "player_start": (self.player.rect.centerx, self.player.rect.centery),
            "platforms": [],
            "enemies": [],
            "collectibles": [],
            "obstacles": [],
            "keys": [],
            "doors": [],
            "exit": None 
        }
        for s in self.all_sprites:
            if s == self.player:
                continue # Player position handled separately
            if isinstance(s, Platform):
                current_level_data["platforms"].append((s.rect.x, s.rect.y, s.rect.width, s.rect.height, s.orientation, s.dies_on_touch, s.is_hookable))
            elif isinstance(s, ChaserEnemy):
                current_level_data["enemies"].append({"type": "chaser", "pos": (s.rect.centerx, s.rect.centery), "detection_range": s.detection_range})
            elif isinstance(s, PatrolEnemy):
                current_level_data["enemies"].append({"type": "patrol", "pos": (s.rect.centerx, s.rect.centery), "range": s.patrol_range})
            elif isinstance(s, Collectible):
                current_level_data["collectibles"].append({"type": s.type, "pos": (s.rect.centerx, s.rect.centery)})
            elif isinstance(s, Spike):
                current_level_data["obstacles"].append({"type": "spike", "pos": (s.rect.x, s.rect.y), "instant_kill": s.instant_kill})
            elif isinstance(s, Key):
                current_level_data["keys"].append({"id": s.key_id, "pos": (s.rect.centerx, s.rect.centery), "color": s.key_color})
            elif isinstance(s, Door):
                door_data = {"id": s.door_id, "pos": (s.rect.x, s.rect.y, s.rect.width, s.rect.height), "color": s.door_color}
                if s.required_key_id:
                    door_data["required_key_id"] = s.required_key_id
                if s.required_weapon_type:
                    door_data["required_weapon_type"] = s.required_weapon_type
                door_data["dies_on_touch"] = s.dies_on_touch
                door_data["is_hookable"] = s.is_hookable
                current_level_data["doors"].append(door_data)
            elif isinstance(s, LevelExit):
                current_level_data["exit"] = (s.rect.x, s.rect.y, s.rect.width, s.rect.height)
        return current_level_data

    def _save_current_editor_state(self):
        self.editor_saved_level_state = self._get_current_editor_level_data()
        print("Estado actual del editor guardado para prueba.")

    def _restore_editor_state(self):
        if self.editor_saved_level_state:
            self.load_level_from_dict(self.editor_saved_level_state)
            self.editor_saved_level_state = None # Clear saved state after restoring
            self.game_state = GAME_STATE_EDITOR
            self.editor_selected_sprite = None # Clear selection
            # Reset editor camera offset when restoring state
            self.editor_camera_offset_x = 0
            self.editor_camera_offset_y = 0
            print("Estado del editor restaurado.")
        else:
            print("No hay estado de editor guardado para restaurar.")
            self.game_state = GAME_STATE_EDITOR # Just go back to empty editor if no state


    def save_level_to_file(self, filename):
        # Create 'levels' directory if it doesn't exist
        levels_dir = "levels"
        if not os.path.exists(levels_dir):
            os.makedirs(levels_dir)
        
        file_path = os.path.join(levels_dir, f"{filename}.json")

        current_level_data_for_save = self._get_current_editor_level_data()

        try:
            with open(file_path, 'w') as f:
                json.dump(current_level_data_for_save, f, indent=4)
            print(f"Nivel guardado exitosamente en: {file_path}")
            self._load_levels_from_files() # Reload levels after saving to update load menu
        except IOError as e:
            print(f"Error al guardar el nivel: {e}")

    def handle_events(self):
        global WIDTH, HEIGHT, SCREEN # Declare global to modify
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.SCALED)
                # Adjust positions of UI elements if necessary
                self.editor_panel.rect.height = HEIGHT - 20 # Adjust panel height
                self.filename_input_box.rect.center = (WIDTH // 2, HEIGHT // 2 - 25)
                self.load_level_overlay_rect.center = (WIDTH // 2, HEIGHT // 2)
                print(f"Ventana redimensionada a: {WIDTH}x{HEIGHT}")
                return True # Event handled, prevent further processing for this event

            if self.game_state == GAME_STATE_PLAYING or self.game_state == GAME_STATE_PLAYING_FROM_EDITOR:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False
                    if event.key == pygame.K_SPACE:
                        self.player.jump(self.sound_manager)
                    if event.key == pygame.K_e:
                        self.player.start_dash(self.sound_manager)
                    if event.key == pygame.K_r:
                        self.player.start_reload(self.sound_manager)
                    
                    # Return to editor from play test
                    if self.game_state == GAME_STATE_PLAYING_FROM_EDITOR and event.key == pygame.K_F1:
                        self._restore_editor_state()
                        return True # Event handled

                    # Weapon switching
                    if event.key == pygame.K_1:
                        self.player.equip_weapon("normal", self.sound_manager)
                    elif event.key == pygame.K_2 and self.player.has_weapon_powerup["blue"]:
                        self.player.equip_weapon("blue", self.sound_manager)
                    elif event.key == pygame.K_3 and self.player.has_weapon_powerup["red"]:
                        self.player.equip_weapon("red", self.sound_manager)
                    elif event.key == pygame.K_4 and self.player.has_weapon_powerup["purple"]:
                        self.player.equip_weapon("purple", self.sound_manager)


                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    target_x_world = mouse_x + self.camera_offset_x
                    target_y_world = mouse_y + self.camera_offset_y
                    
                    if event.button == 1: # Left mouse button
                        if self.player.current_weapon == "red": # Red weapon uses left-click for charge
                            self.player.start_charge(click_type="left")
                        elif self.player.current_weapon == "purple": # Purple weapon uses left-click for arc shot
                            self.player.start_charge(click_type="left")
                        else: # Normal and Blue weapons use left-click for continuous/single fire
                            if self.player.shoot(target_x_world, target_y_world, self.sound_manager, click_type="left"):
                                start_x, start_y = self.player.rect.centerx, self.player.rect.centery
                                dx = target_x_world - start_x
                                dy = target_y_world - start_y
                                
                                distance = math.sqrt(dx**2 + dy**2)
                                if distance == 0:
                                    norm_dx, norm_dy = 1, 0
                                else:
                                    norm_dx = dx / distance
                                    norm_dy = dy / distance
                                
                                bullet = Bullet(start_x, start_y, norm_dx, norm_dy, self.player.current_weapon, game_instance=self) # Pass game instance
                                self.all_sprites.add(bullet)
                                self.bullets.add(bullet)
                    
                    elif event.button == 3: # Right mouse button (Special power-up charge shot OR Purple Grappling Hook)
                        if self.player.current_weapon == "purple":
                            self.player.start_charge(click_type="right") # Start grappling
                        else:
                            self.player.start_charge(click_type="right") # Start special power-up charge

                elif event.type == pygame.MOUSEBUTTONUP:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    target_x_world = mouse_x + self.camera_offset_x
                    target_y_world = mouse_y + self.camera_offset_y

                    if event.button == 1: # Left mouse button release
                        if self.player.current_weapon == "red" and self.player.is_charging_red_weapon:
                            if self.player.shoot(target_x_world, target_y_world, self.sound_manager, click_type="left"):
                                start_x, start_y = self.player.rect.centerx, self.player.rect.centery
                                dx = target_x_world - start_x
                                dy = target_y_world - start_y
                                
                                distance = math.sqrt(dx**2 + dy**2)
                                if distance == 0:
                                    norm_dx, norm_dy = 1, 0
                                else:
                                    norm_dx = dx / distance
                                    norm_dy = dy / distance
                                
                                # Pass the red_charge_level directly to Bullet constructor
                                bullet = Bullet(start_x, start_y, norm_dx, norm_dy, "red", charge_level=self.player.red_charge_level, game_instance=self) # Pass game instance
                                self.all_sprites.add(bullet)
                                self.bullets.add(bullet)
                            self.player.stop_charge(click_type="left") # Stop charging regardless if shot was fired
                        elif self.player.current_weapon == "purple" and self.player.is_charging_purple_shot:
                            if self.player.shoot(target_x_world, target_y_world, self.sound_manager, click_type="left"):
                                start_x, start_y = self.player.rect.centerx, self.player.rect.centery
                                
                                # Calculate initial velocities for arc shot
                                # This is a simplified arc calculation. A more realistic one would involve solving for initial velocity given target.
                                # For now, we'll aim for target_x and adjust initial_vy to get a peak.
                                
                                # Horizontal velocity based on distance and charge level
                                vx = (target_x_world - start_x) * PURPLE_ARC_SPEED_FACTOR * (0.5 + self.player.purple_charge_level * 0.5)
                                
                                # Calculate required initial vertical velocity for arc, considering gravity
                                # This is a simplified approach, assuming a fixed peak height for max charge
                                # A more accurate parabola would involve:
                                # dy = vy0*t + 0.5*g*t^2
                                # dx = vx*t
                                # t = dx / vx
                                # vy0 = (dy - 0.5*g*(dx/vx)^2) * (vx/dx)
                                
                                # Let's use a simpler approach: fixed initial upward velocity, and let gravity do the rest.
                                # The 'charge_level' will influence the initial upward velocity and thus the arc height.
                                initial_vy = - (PURPLE_ARC_MAX_HEIGHT * (0.5 + self.player.purple_charge_level * 0.5)) / 10 # Scale down for reasonable velocity
                                
                                bullet = Bullet(start_x, start_y, vx, initial_vy, "purple", game_instance=self)
                                self.all_sprites.add(bullet)
                                self.bullets.add(bullet)
                            self.player.stop_charge(click_type="left")

                    elif event.button == 3: # Right mouse button release (Special power-up charge shot OR Purple Grappling Hook)
                        if self.player.is_charging_powerup_shot: # Special power-up charge shot
                            if self.player.shoot(target_x_world, target_y_world, self.sound_manager, click_type="right"):
                                start_x, start_y = self.player.rect.centerx, self.player.rect.centery
                                dx = target_x_world - start_x
                                dy = target_y_world - start_y
                                
                                distance = math.sqrt(dx**2 + dy**2)
                                if distance == 0:
                                    norm_dx, norm_dy = 1, 0
                                else:
                                    norm_dx = dx / distance
                                    norm_dy = dy / distance
                                
                                # This bullet is the special power-up charged shot, distinct from red weapon
                                # Pass the charge_powerup_level directly to Bullet constructor
                                bullet = Bullet(start_x, start_y, norm_dx, norm_dy, "red", charge_level=self.player.charge_powerup_level, game_instance=self) # Pass game instance
                                self.all_sprites.add(bullet)
                                self.bullets.add(bullet)
                            self.player.stop_charge(click_type="right")
                        elif self.player.current_weapon == "purple" and self.player.is_grappling: # Purple Grappling Hook release
                            self.player.stop_charge(click_type="right") # Stop grappling (if not attached, it will just stop the line)
            
            elif self.game_state == GAME_STATE_GAME_OVER or self.game_state == GAME_STATE_WIN:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    if event.key == pygame.K_ESCAPE:
                        return False
            
            elif self.game_state == GAME_STATE_EDITOR:
                # Handle clicks on the editor panel first
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.editor_panel.handle_click(event.pos):
                        return True # If click was on panel, don't process as map click

                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                # Adjust grid_x if it falls inside the panel
                # These are screen coordinates, not world coordinates
                if mouse_x < self.editor_panel.rect.right:
                    grid_x_screen = self.editor_panel.rect.right
                else:
                    grid_x_screen = (mouse_x // self.GRID_SIZE) * self.GRID_SIZE
                
                grid_y_screen = (mouse_y // self.GRID_SIZE) * self.GRID_SIZE

                # Convert screen coordinates to world coordinates for placement/interaction
                grid_x_world = grid_x_screen - self.editor_camera_offset_x
                grid_y_world = grid_y_screen - self.editor_camera_offset_y

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Double-click detection
                    now = pygame.time.get_ticks()
                    is_double_click = (now - self.last_click_time_editor < 300)
                    self.last_click_time_editor = now # Update last click time for next double-click check

                    # Find if an existing sprite was clicked (outside the panel)
                    clicked_sprite = None
                    # Iterate through sprites in reverse order to click on top-most if overlapping
                    for group in [self.level_exit, self.doors, self.keys, self.collectibles, self.obstacles, self.enemies, self.platforms]:
                        for sprite in reversed(group.sprites()): # Iterate in reverse
                            # Check collision with mouse position, adjusted by editor camera offset
                            sprite_rect_screen = sprite.rect.move(self.editor_camera_offset_x, self.editor_camera_offset_y)
                            if sprite_rect_screen.collidepoint(mouse_x, mouse_y) and sprite.rect.x >= self.editor_panel.rect.right - self.editor_camera_offset_x: # Ensure it's not in the panel area in world coords
                                clicked_sprite = sprite
                                break
                        if clicked_sprite: break
                    
                    if event.button == 1: # Left click
                        if clicked_sprite and clicked_sprite != self.player: # Only editable sprites, not player
                            if is_double_click:
                                self.editing_sprite = clicked_sprite
                                self.property_input_boxes = {} # Clear previous inputs
                                
                                if hasattr(self.editing_sprite, 'get_properties'):
                                    properties = self.editing_sprite.get_properties()
                                else:
                                    properties = {}

                                self.available_property_ids = {} # Clear for new context
                                if isinstance(self.editing_sprite, Door):
                                    self.available_property_ids["keys"] = sorted([k.key_id for k in self.keys])
                                    self.available_property_ids["weapons"] = sorted(list(self.player.weapon_data.keys()))
                                elif isinstance(self.editing_sprite, Key):
                                    self.available_property_ids["doors"] = sorted([d.door_id for d in self.doors])

                                if properties:
                                    self.property_edit_message = f"Editar propiedades de {type(self.editing_sprite).__name__}:"
                                    y_offset = HEIGHT // 2 - 100
                                    for prop_name, prop_value in properties.items():
                                        input_box = InputBox(WIDTH // 2 - 150, y_offset + 50, 300, 40, self.font_small)
                                        input_box.set_placeholder(prop_name.replace("_", " ").capitalize())
                                        input_box.set_text(str(prop_value))
                                        if isinstance(prop_value, (int, float)):
                                            input_box.set_numeric(True)
                                        elif isinstance(prop_value, bool):
                                            input_box.set_boolean(True)
                                            input_box.set_dropdown_options(["True", "False"])
                                        
                                        if prop_name == "required_key_id":
                                            input_box.set_dropdown_options([""] + sorted([k.key_id for k in self.keys]))
                                        elif prop_name == "required_weapon_type":
                                            input_box.set_dropdown_options([""] + sorted(list(self.player.weapon_data.keys())))

                                        self.property_input_boxes[prop_name] = input_box
                                        y_offset += 60
                                    
                                    self.game_state = GAME_STATE_EDITING_PROPERTIES
                                else:
                                    print(f"El elemento {type(self.editing_sprite).__name__} no tiene propiedades editables.")
                                    self.property_edit_message = f"Este elemento no tiene propiedades editables."
                                    self.editing_sprite = None
                                return True # Event handled (double click)
                            else: # Single click on an existing sprite
                                self.editor_selected_sprite = clicked_sprite # Select the clicked sprite
                                
                                # Check for resizing handles (only for platforms)
                                if isinstance(self.editor_selected_sprite, Platform) and self.editor_selected_sprite.orientation == "horizontal":
                                    tolerance = 10
                                    # Adjust mouse_x to sprite's local coordinates for resize check
                                    mouse_x_local = mouse_x - (self.editor_selected_sprite.rect.x + self.editor_camera_offset_x)
                                    if abs(mouse_x_local - 0) < tolerance: # Left edge
                                        self.resizing_platform = True
                                        self.resizing_edge = "left"
                                        self.initial_mouse_pos = event.pos
                                        self.initial_platform_rect = self.editor_selected_sprite.rect.copy()
                                        return True
                                    elif abs(mouse_x_local - self.editor_selected_sprite.rect.width) < tolerance: # Right edge
                                        self.resizing_platform = True
                                        self.resizing_edge = "right"
                                        self.initial_mouse_pos = event.pos
                                        self.initial_platform_rect = self.editor_selected_sprite.rect.copy()
                                        return True

                                # If not resizing, start dragging or duplicate
                                keys_pressed = pygame.key.get_pressed()
                                if keys_pressed[pygame.K_LALT] or keys_pressed[pygame.K_RALT]:
                                    # Duplicate sprite logic (as before)
                                    if isinstance(clicked_sprite, Platform):
                                        new_sprite = Platform(clicked_sprite.rect.x, clicked_sprite.rect.y, clicked_sprite.rect.width, clicked_sprite.rect.height, clicked_sprite.platform_color, clicked_sprite.orientation, clicked_sprite.dies_on_touch, clicked_sprite.is_hookable)
                                    elif isinstance(clicked_sprite, ChaserEnemy):
                                        new_sprite = ChaserEnemy(clicked_sprite.rect.centerx, clicked_sprite.rect.centery, self.CHASER_ENEMY_COLOR)
                                        if hasattr(clicked_sprite, 'detection_range'):
                                            new_sprite.detection_range = clicked_sprite.detection_range
                                    elif isinstance(clicked_sprite, PatrolEnemy):
                                        new_sprite = PatrolEnemy(clicked_sprite.rect.centerx, clicked_sprite.rect.centery, self.PATROL_ENEMY_COLOR, clicked_sprite.patrol_range)
                                    elif isinstance(clicked_sprite, Collectible):
                                        new_sprite = Collectible(clicked_sprite.rect.centerx, clicked_sprite.rect.centery, clicked_sprite.type, self)
                                    elif isinstance(clicked_sprite, Spike):
                                        new_sprite = Spike(clicked_sprite.rect.x, clicked_sprite.rect.y, self.SPIKE_COLOR, clicked_sprite.instant_kill)
                                    elif isinstance(clicked_sprite, Key):
                                        new_key_id = f"key_{random.randint(1000,9999)}"
                                        new_sprite = Key(clicked_sprite.rect.centerx, clicked_sprite.rect.centery, new_key_id, clicked_sprite.key_color)
                                    elif isinstance(clicked_sprite, Door):
                                        new_door_id = f"door_{random.randint(1000,9999)}"
                                        new_sprite = Door(clicked_sprite.rect.x, clicked_sprite.rect.y, clicked_sprite.width, clicked_sprite.height, new_door_id, clicked_sprite.door_color, clicked_sprite.required_key_id, clicked_sprite.required_weapon_type, clicked_sprite.dies_on_touch, clicked_sprite.is_hookable)
                                    elif isinstance(clicked_sprite, LevelExit):
                                        new_sprite = None # Cannot duplicate exit
                                        print("No se puede duplicar la salida de nivel. Se moverá el existente.")
                                    else:
                                        new_sprite = None

                                    if new_sprite:
                                        self.all_sprites.add(new_sprite)
                                        if isinstance(new_sprite, Platform): self.platforms.add(new_sprite)
                                        elif isinstance(new_sprite, (ChaserEnemy, PatrolEnemy)): self.enemies.add(new_sprite)
                                        elif isinstance(new_sprite, Collectible): self.collectibles.add(new_sprite)
                                        elif isinstance(new_sprite, Spike): self.obstacles.add(new_sprite)
                                        elif isinstance(new_sprite, Key): self.keys.add(new_sprite)
                                        elif isinstance(new_sprite, Door): self.doors.add(new_sprite)
                                        self.editor_dragged_sprite = new_sprite
                                        self.editor_selected_sprite = new_sprite
                                        print(f"Elemento duplicado: {type(new_sprite).__name__}")
                                    else:
                                        self.editor_dragged_sprite = clicked_sprite # Fallback to just dragging
                                else:
                                    self.editor_dragged_sprite = clicked_sprite
                                
                                self.editor_dragging = True
                                self.editor_drag_offset_x = mouse_x - (self.editor_dragged_sprite.rect.x + self.editor_camera_offset_x) # Offset relative to screen position
                                self.editor_drag_offset_y = mouse_y - (self.editor_dragged_sprite.rect.y + self.editor_camera_offset_y) # Offset relative to screen position
                                return True # Consume event, started dragging
                        else: # No existing sprite clicked, attempt to place new
                            # Ensure click is outside the editor panel area for placement
                            if mouse_x >= self.editor_panel.rect.right:
                                # Placement logic (as before)
                                if self.editor_selected_tool == "player_start":
                                    # Place player at world coordinates
                                    self.player.rect.center = (grid_x_world + self.GRID_SIZE // 2, grid_y_world + self.GRID_SIZE // 2)
                                    print(f"Inicio del jugador movido a ({self.player.rect.centerx}, {self.player.rect.centery})")
                                elif self.editor_selected_tool == "spike":
                                    # Spikes are placed with their base at the bottom of the grid cell
                                    new_spike = Spike(grid_x_world, grid_y_world + self.GRID_SIZE - 20, self.SPIKE_COLOR) # 20 is spike height
                                    self.all_sprites.add(new_spike)
                                    self.obstacles.add(new_spike)
                                    self.editor_selected_sprite = new_spike
                                    print(f"Spike añadido en ({grid_x_world}, {grid_y_world})")
                                elif self.editor_selected_tool == "platform":
                                    new_platform = Platform(grid_x_world, grid_y_world, self.editor_tool_size[0], self.editor_tool_size[1], self.PLATFORM_COLOR, "horizontal")
                                    self.all_sprites.add(new_platform)
                                    self.platforms.add(new_platform)
                                    self.editor_selected_sprite = new_platform
                                    print(f"Plataforma horizontal añadida en ({grid_x_world}, {grid_y_world})")
                                elif self.editor_selected_tool == "vertical_platform":
                                    new_platform = Platform(grid_x_world, grid_y_world, self.GRID_SIZE, self.GRID_SIZE * 2, self.PLATFORM_COLOR, "vertical")
                                    self.all_sprites.add(new_platform)
                                    self.platforms.add(new_platform)
                                    self.editor_selected_sprite = new_platform
                                    print(f"Plataforma vertical añadida en ({grid_x_world}, {grid_y_world})")
                                elif self.editor_selected_tool == "chaser_enemy":
                                    new_enemy = ChaserEnemy(grid_x_world + self.GRID_SIZE // 2, grid_y_world + self.GRID_SIZE // 2, self.CHASER_ENEMY_COLOR)
                                    self.all_sprites.add(new_enemy)
                                    self.enemies.add(new_enemy)
                                    self.editor_selected_sprite = new_enemy
                                    print(f"Enemigo Perseguidor añadido en ({grid_x_world}, {grid_y_world})")
                                elif self.editor_selected_tool == "patrol_enemy":
                                    new_enemy = PatrolEnemy(grid_x_world + self.GRID_SIZE // 2, grid_y_world + self.GRID_SIZE // 2, self.PATROL_ENEMY_COLOR)
                                    self.all_sprites.add(new_enemy)
                                    self.enemies.add(new_enemy)
                                    self.editor_selected_sprite = new_enemy
                                    print(f"Enemigo Patrulla añadido en ({grid_x_world}, {grid_y_world})")
                                elif self.editor_selected_tool == "score_collectible":
                                    new_collectible = Collectible(grid_x_world + self.GRID_SIZE // 2, grid_y_world + self.GRID_SIZE // 2, "score", self)
                                    self.all_sprites.add(new_collectible)
                                    self.collectibles.add(new_collectible)
                                    self.editor_selected_sprite = new_collectible
                                    print(f"Coleccionable de Puntuación añadido en ({grid_x_world}, {grid_y_world})")
                                elif self.editor_selected_tool == "health_collectible":
                                    new_collectible = Collectible(grid_x_world + self.GRID_SIZE // 2, grid_y_world + self.GRID_SIZE // 2, "health", self)
                                    self.all_sprites.add(new_collectible)
                                    self.collectibles.add(new_collectible)
                                    self.editor_selected_sprite = new_collectible
                                    print(f"Coleccionable de Vida añadido en ({grid_x_world}, {grid_y_world})")
                                elif self.editor_selected_tool == "speed_collectible":
                                    new_collectible = Collectible(grid_x_world + self.GRID_SIZE // 2, grid_y_world + self.GRID_SIZE // 2, "speed", self)
                                    self.all_sprites.add(new_collectible)
                                    self.collectibles.add(new_collectible)
                                    self.editor_selected_sprite = new_collectible
                                    print(f"Coleccionable de Velocidad añadido en ({grid_x_world}, {grid_y_world})")
                                elif self.editor_selected_tool == "charge_powerup_collectible":
                                    new_collectible = Collectible(grid_x_world + self.GRID_SIZE // 2, grid_y_world + self.GRID_SIZE // 2, "charge_powerup", self)
                                    self.all_sprites.add(new_collectible)
                                    self.collectibles.add(new_collectible)
                                    self.editor_selected_sprite = new_collectible
                                    print(f"Power-up de Carga añadido en ({grid_x_world}, {grid_y_world})")
                                elif self.editor_selected_tool == "blue_weapon_powerup_collectible":
                                    new_collectible = Collectible(grid_x_world + self.GRID_SIZE // 2, grid_y_world + self.GRID_SIZE // 2, "blue_weapon_powerup", self)
                                    self.all_sprites.add(new_collectible)
                                    self.collectibles.add(new_collectible)
                                    self.editor_selected_sprite = new_collectible
                                    print(f"Power-up Arma Azul añadido en ({grid_x_world}, {grid_y_world})")
                                elif self.editor_selected_tool == "red_weapon_powerup_collectible":
                                    new_collectible = Collectible(grid_x_world + self.GRID_SIZE // 2, grid_y_world + self.GRID_SIZE // 2, "red_weapon_powerup", self)
                                    self.all_sprites.add(new_collectible)
                                    self.collectibles.add(new_collectible)
                                    self.editor_selected_sprite = new_collectible
                                    print(f"Power-up Arma Roja añadido en ({grid_x_world}, {grid_y_world})")
                                elif self.editor_selected_tool == "purple_weapon_powerup_collectible":
                                    new_collectible = Collectible(grid_x_world + self.GRID_SIZE // 2, grid_y_world + self.GRID_SIZE // 2, "purple_weapon_powerup", self)
                                    self.all_sprites.add(new_collectible)
                                    self.collectibles.add(new_collectible)
                                    self.editor_selected_sprite = new_collectible
                                    print(f"Power-up Arma Púrpura añadido en ({grid_x_world}, {grid_y_world})")
                                elif self.editor_selected_tool == "key":
                                    new_key = Key(grid_x_world + self.GRID_SIZE // 2, grid_y_world + self.GRID_SIZE // 2, f"key_{random.randint(1000,9999)}", (random.randint(50,255), random.randint(50,255), random.randint(50,255)))
                                    self.all_sprites.add(new_key)
                                    self.keys.add(new_key)
                                    self.editor_selected_sprite = new_key
                                    print(f"Llave añadida en ({grid_x_world}, {grid_y_world}) con ID: {new_key.key_id}")
                                elif self.editor_selected_tool == "door":
                                    new_door = Door(grid_x_world, grid_y_world, self.GRID_SIZE, self.GRID_SIZE * 2, f"door_{random.randint(1000,9999)}", (random.randint(50,200), random.randint(50,200), random.randint(50,200)))
                                    self.all_sprites.add(new_door)
                                    self.doors.add(new_door)
                                    self.editor_selected_sprite = new_door
                                    print(f"Puerta añadida en ({grid_x_world}, {grid_y_world}) con ID: {new_door.door_id}")
                                elif self.editor_selected_tool == "level_exit":
                                    if self.level_exit.sprite:
                                        self.level_exit.sprite.kill()
                                        print("Salida de nivel existente eliminada.")
                                    new_exit = LevelExit(grid_x_world, grid_y_world, self.GRID_SIZE, self.GRID_SIZE, self.EXIT_COLOR)
                                    self.all_sprites.add(new_exit)
                                    self.level_exit.add(new_exit)
                                    self.editor_selected_sprite = new_exit
                                    print(f"Salida de nivel añadida/movida a ({grid_x_world}, {grid_y_world})")
                                return True # Consume event
                    
                    elif event.button == 3: # Right click to remove
                        removed_something = False
                        # Check if click is outside the editor panel
                        if mouse_x > self.editor_panel.rect.right:
                            # Remove from all relevant groups
                            # Iterate in reverse order for correct removal if overlapping
                            for group in [self.level_exit, self.doors, self.keys, self.collectibles, self.obstacles, self.enemies, self.platforms]:
                                for sprite in reversed(group.sprites()):
                                    # Check collision with mouse position, adjusted by editor camera offset
                                    sprite_rect_screen = sprite.rect.move(self.editor_camera_offset_x, self.editor_camera_offset_y)
                                    if sprite_rect_screen.collidepoint(mouse_x, mouse_y) and sprite.rect.x >= self.editor_panel.rect.right - self.editor_camera_offset_x:
                                        sprite.kill()
                                        removed_something = True
                                        if self.editor_selected_sprite == sprite:
                                            self.editor_selected_sprite = None # Deselect if removed
                                        print(f"Elemento eliminado en ({sprite.rect.x}, {sprite.rect.y})")
                                        break # Remove only one per click
                                if removed_something:
                                    break
                            if not removed_something:
                                print("No se encontró ningún elemento para eliminar en esa posición.")
                        else:
                            print("Click en el panel del editor, no se puede eliminar un elemento aquí.")
                    
                    elif event.button == 2: # Middle click for panning
                        self.editor_panning = True
                        self.editor_pan_start_mouse_pos = event.pos
                        self.initial_editor_camera_offset_x = self.editor_camera_offset_x
                        self.initial_editor_camera_offset_y = self.editor_camera_offset_y
                        print("Iniciando paneo de cámara.")
                        return True # Consume event

                elif event.type == pygame.MOUSEMOTION:
                    if self.editor_dragging and self.editor_dragged_sprite:
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        
                        # Calculate new world position based on mouse and drag offset
                        new_x_world = mouse_x - self.editor_drag_offset_x - self.editor_camera_offset_x
                        new_y_world = mouse_y - self.editor_drag_offset_y - self.editor_camera_offset_y
                        
                        # Snap to grid in world coordinates
                        grid_x_world_snapped = (new_x_world // self.GRID_SIZE) * self.GRID_SIZE
                        grid_y_world_snapped = (new_y_world // self.GRID_SIZE) * self.GRID_SIZE

                        # Ensure dragged sprite stays within valid area (right of panel, in world coords)
                        # The panel is fixed on screen, so its right edge in world coords changes with camera offset
                        panel_right_world_edge = self.editor_panel.rect.right - self.editor_camera_offset_x
                        if grid_x_world_snapped < panel_right_world_edge:
                            grid_x_world_snapped = panel_right_world_edge
                        
                        self.editor_dragged_sprite.rect.x = grid_x_world_snapped
                        self.editor_dragged_sprite.rect.y = grid_y_world_snapped
                    
                    elif self.resizing_platform and self.editor_selected_sprite and isinstance(self.editor_selected_sprite, Platform) and self.editor_selected_sprite.orientation == "horizontal":
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        delta_x = mouse_x - self.initial_mouse_pos[0]
                        
                        min_width = self.GRID_SIZE # 1 cell
                        max_width = self.GRID_SIZE * 10 # 10 cells

                        if self.resizing_edge == "left":
                            # Calculate new world X based on initial world X and mouse delta
                            new_x_world = self.initial_platform_rect.x + delta_x
                            # Snap new_x_world to grid
                            new_x_world_snapped = (new_x_world // self.GRID_SIZE) * self.GRID_SIZE
                            
                            new_width = self.initial_platform_rect.right - new_x_world_snapped
                            
                            # Apply width constraints
                            if new_width < min_width:
                                new_width = min_width
                                new_x_world_snapped = self.initial_platform_rect.right - min_width
                            elif new_width > max_width:
                                new_width = max_width
                                new_x_world_snapped = self.initial_platform_rect.right - max_width
                            
                            self.editor_selected_sprite.rect.x = new_x_world_snapped
                            self.editor_selected_sprite.rect.width = new_width

                        elif self.resizing_edge == "right":
                            # Calculate new width based on initial width and mouse delta
                            new_width = self.initial_platform_rect.width + delta_x
                            # Snap new_width to grid
                            new_width_snapped = (new_width // self.GRID_SIZE) * self.GRID_SIZE
                            
                            # Apply width constraints
                            if new_width_snapped < min_width:
                                new_width_snapped = min_width
                            elif new_width_snapped > max_width:
                                new_width_snapped = max_width
                            
                            self.editor_selected_sprite.rect.width = new_width_snapped
                        
                        self.editor_selected_sprite._draw_image() # Redraw the platform image
                    
                    elif self.editor_panning:
                        current_mouse_x, current_mouse_y = pygame.mouse.get_pos()
                        delta_x = current_mouse_x - self.editor_pan_start_mouse_pos[0]
                        delta_y = current_mouse_y - self.editor_pan_start_mouse_pos[1]
                        
                        # Update camera offset
                        self.editor_camera_offset_x = self.initial_editor_camera_offset_x + delta_x
                        self.editor_camera_offset_y = self.initial_editor_camera_offset_y + delta_y


                elif event.type == pygame.MOUSEBUTTONUP:
                    self.editor_dragging = False
                    self.editor_dragged_sprite = None
                    self.resizing_platform = False
                    self.resizing_edge = None
                    self.initial_mouse_pos = None
                    self.initial_platform_rect = None
                    
                    if event.button == 2: # Middle click release
                        self.editor_panning = False
                        print("Paneo de cámara finalizado.")


                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1: # Tecla para salir del modo editor
                        self.game_state = GAME_STATE_MENU # Vuelve al menú principal
                        self.editor_selected_sprite = None # Clear selected sprite
                        self.resizing_platform = False # Stop resizing
                        self.editor_camera_offset_x = 0 # Reset editor camera offset
                        self.editor_camera_offset_y = 0
                        print("Saliendo del modo editor y volviendo al menú principal.")
                    elif event.key == pygame.K_s: # Guardar nivel (inicia el proceso de entrada de nombre)
                        self.game_state = GAME_STATE_SAVING_LEVEL_INPUT
                        self.filename_input_box.set_text("") # Clear previous input
                        self.filename_input_box.active = True # Activate input box
                        print("Introduce el nombre del archivo para guardar el nivel. Presiona ENTER para confirmar, ESC para cancelar.")
                    elif event.key == pygame.K_r: # Rotate/Invert selected element
                        if self.editor_selected_sprite and isinstance(self.editor_selected_sprite, Platform):
                            platform = self.editor_selected_sprite
                            # Store original center to maintain position after rotation
                            original_center_x = platform.rect.centerx
                            original_center_y = platform.rect.centery

                            # Swap width and height
                            new_width = platform.rect.height
                            new_height = platform.rect.width
                            
                            # Ensure new dimensions are multiples of GRID_SIZE
                            new_width = (new_width // self.GRID_SIZE) * self.GRID_SIZE
                            new_height = (new_height // self.GRID_SIZE) * self.GRID_SIZE
                            
                            # Ensure minimum size is 1 grid cell
                            if new_width == 0: new_width = self.GRID_SIZE
                            if new_height == 0: new_height = self.GRID_SIZE

                            # Update orientation
                            if platform.orientation == "horizontal":
                                platform.orientation = "vertical"
                            else:
                                platform.orientation = "horizontal"

                            platform.rect.width = new_width
                            platform.rect.height = new_height
                            platform._draw_image() # Redraw the image with new dimensions

                            # Re-center the platform on the grid after rotation
                            # Calculate new top-left based on original center and new dimensions
                            platform.rect.centerx = original_center_x
                            platform.rect.centery = original_center_y

                            # Snap to grid after re-centering
                            platform.rect.x = (platform.rect.x // self.GRID_SIZE) * self.GRID_SIZE
                            platform.rect.y = (platform.rect.y // self.GRID_SIZE) * self.GRID_SIZE

                            print(f"Plataforma rotada a {platform.orientation}. Nuevas dimensiones: {platform.rect.width}x{platform.rect.height}")
                        else:
                            print("No hay plataforma seleccionada o el elemento no es una plataforma para rotar.")
            
            elif self.game_state == GAME_STATE_SAVING_LEVEL_INPUT:
                result = self.filename_input_box.handle_event(event)
                if result == "submit":
                    if self.filename_input_box.get_text():
                        self.save_level_to_file(self.filename_input_box.get_text())
                        self.game_state = GAME_STATE_EDITOR # Volver al editor después de guardar
                    else:
                        print("El nombre del archivo no puede estar vacío.")
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.game_state = GAME_STATE_EDITOR # Cancelar y volver al editor
                    print("Guardado de nivel cancelado.")
            
            elif self.game_state == GAME_STATE_EDITING_PROPERTIES:
                for prop_name, input_box in self.property_input_boxes.items():
                    result = input_box.handle_event(event)
                    if result == "submit":
                        # Apply properties and exit editing state
                        updated_props = {}
                        all_valid = True
                        for p_name, i_box in self.property_input_boxes.items():
                            val = i_box.get_text()
                            if i_box.is_numeric:
                                try:
                                    num_val = int(val)
                                    if num_val <= 0: # Basic validation for size/range
                                        print(f"Error: {p_name} debe ser un número positivo.")
                                        all_valid = False
                                        break
                                    updated_props[p_name] = num_val
                                except ValueError:
                                    print(f"Error: '{val}' no es un número válido para {p_name}.")
                                    all_valid = False
                                    break
                            elif i_box.is_boolean:
                                if val.lower() in ['true', 'false']:
                                    updated_props[p_name] = (val.lower() == 'true')
                                else:
                                    print(f"Error: '{val}' no es un valor booleano válido para {p_name}. Usa 'True' o 'False'.")
                                    all_valid = False
                                    break
                            else:
                                updated_props[p_name] = val
                        
                        if all_valid:
                            # Check if the sprite has a set_properties method
                            if hasattr(self.editing_sprite, 'set_properties'):
                                self.editing_sprite.set_properties(updated_props)
                                print(f"Propiedades actualizadas para {type(self.editing_sprite).__name__}.")
                            else:
                                print(f"El elemento {type(self.editing_sprite).__name__} no tiene un método set_properties.")

                            self.game_state = GAME_STATE_EDITOR
                            self.editing_sprite = None
                            self.property_input_boxes = {}
                            self.property_edit_message = ""
                            self.available_property_ids = {} # Clear available IDs
                        else:
                            print("Por favor, corrige los errores en las propiedades.")
                        return True # Consume event
                
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.game_state = GAME_STATE_EDITOR # Cancelar y volver al editor
                    self.editing_sprite = None
                    self.property_input_boxes = {}
                    self.property_edit_message = ""
                    self.available_property_ids = {} # Clear available IDs
                    print("Edición de propiedades cancelada.")
            
            elif self.game_state == GAME_STATE_LOAD_LEVEL_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos
                    # Check "Cancel" button
                    cancel_button_rect = pygame.Rect(self.load_level_overlay_rect.x + self.load_level_overlay_rect.width // 2 - 50, self.load_level_overlay_rect.bottom - 40, 100, 30)
                    if cancel_button_rect.collidepoint(mouse_x, mouse_y):
                        self.game_state = GAME_STATE_EDITOR # Go back to editor
                        print("Carga de nivel cancelada.")
                        return True
                    
                    # Check level list items
                    item_y = self.load_level_overlay_rect.y + 50
                    for filename in self.available_levels_for_load:
                        item_rect = pygame.Rect(self.load_level_overlay_rect.x + 10, item_y, self.load_level_overlay_rect.width - 20, 30)
                        if item_rect.collidepoint(mouse_x, mouse_y):
                            self.load_level_from_file_by_name(filename)
                            # load_level_from_file_by_name will set game_state to EDITOR
                            return True
                        item_y += 35
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.game_state = GAME_STATE_EDITOR # Cancel and go back to editor
                    print("Carga de nivel cancelada.")
                    return True

    def draw_grid_editor(self):
        # Draw vertical lines
        for x in range(self.editor_panel.rect.right, WIDTH + self.GRID_SIZE, self.GRID_SIZE):
            # Adjust for camera offset
            line_x = x + self.editor_camera_offset_x % self.GRID_SIZE
            if line_x > self.editor_panel.rect.right: # Only draw grid lines to the right of the panel
                pygame.draw.line(self.screen, self.GRID_COLOR, (line_x, 0), (line_x, HEIGHT), 1)
        
        # Draw horizontal lines
        for y in range(0, HEIGHT + self.GRID_SIZE, self.GRID_SIZE):
            # Adjust for camera offset
            line_y = y + self.editor_camera_offset_y % self.GRID_SIZE
            pygame.draw.line(self.screen, self.GRID_COLOR, (self.editor_panel.rect.right, line_y), (WIDTH, line_y), 1)

    def draw_hud(self):
        score_text = self.font_medium.render(f"Puntuación: {self.score}", True, self.WHITE)
        self.screen.blit(score_text, (10, 10))

        health_bar_width = 200
        health_bar_height = 20
        health_bar_x = 10
        health_bar_y = 50
        
        pygame.draw.rect(self.screen, self.BLACK, (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2)
        
        current_health_width = int((self.player.health / self.player.max_health) * health_bar_width)
        health_color = self.PLAYER_COLOR if self.player.health > 50 else (255, 165, 0) if self.player.health > 20 else self.CHASER_ENEMY_COLOR
        pygame.draw.rect(self.screen, health_color, (health_bar_x, health_bar_y, current_health_width, health_bar_height))

        health_text = self.font_small.render(f"Vida: {self.player.health}/{self.player.max_health}", True, self.WHITE)
        self.screen.blit(health_text, (health_bar_x + health_bar_width + 10, health_bar_y))

        # Current Weapon and Ammo
        weapon_ammo_text = self.font_small.render(
            f"Arma: {self.player.current_weapon.capitalize()} ({self.player.weapon_data[self.player.current_weapon]['current_ammo']}/{self.player.weapon_data[self.player.current_weapon]['max_ammo']})", True, self.WHITE)
        self.screen.blit(weapon_ammo_text, (10, 90))

        # Reload Cooldown / Active Indicator
        if "reload_duration" in self.player.weapon_data[self.player.current_weapon]:
            if self.player.is_reloading:
                time_elapsed_reload = pygame.time.get_ticks() - self.player.reload_timer
                remaining_reload = (self.player.weapon_data[self.player.current_weapon]["reload_duration"] - time_elapsed_reload) / 1000.0
                if remaining_reload > 0:
                    reload_text = self.font_small.render(f"Recargando: {remaining_reload:.1f}s", True, self.BULLET_COLOR)
                    self.screen.blit(reload_text, (10, 130))
                else:
                    reload_text = self.font_small.render("Recarga Completa!", True, self.PLAYER_COLOR)
                    self.screen.blit(reload_text, (10, 130))
            else:
                if self.player.weapon_data[self.player.current_weapon]["current_ammo"] < self.player.weapon_data[self.player.current_weapon]["max_ammo"]:
                    reload_hint_text = self.font_small.render("Presiona 'R' para Recargar", True, self.WHITE)
                    self.screen.blit(reload_hint_text, (10, 130))
        else: # For weapons without explicit reload_duration (like 'normal' if it didn't have it)
            if self.player.weapon_data[self.player.current_weapon]["current_ammo"] < self.player.weapon_data[self.player.current_weapon]["max_ammo"]:
                reload_hint_text = self.font_small.render("Recarga Automática", True, self.WHITE)
                self.screen.blit(reload_hint_text, (10, 130))


        # Dash Cooldown / Active Indicator (adjusted position)
        dash_y_pos = 170
        if self.player.is_reloading or self.player.weapon_data[self.player.current_weapon]["current_ammo"] < self.player.weapon_data[self.player.current_weapon]["max_ammo"]:
            dash_y_pos = 170
        else:
            dash_y_pos = 130

        if self.player.is_dashing:
            dash_text = self.font_small.render("DASHING!", True, self.BULLET_COLOR)
            self.screen.blit(dash_text, (10, dash_y_pos))
        else:
            time_since_last_dash = pygame.time.get_ticks() - self.player.last_dash_time
            if time_since_last_dash < DASH_COOLDOWN:
                remaining_cooldown = (DASH_COOLDOWN - time_since_last_dash) / 1000.0
                dash_cooldown_text = self.font_small.render(f"Dash CD: {remaining_cooldown:.1f}s", True, self.WHITE)
                self.screen.blit(dash_cooldown_text, (10, dash_y_pos))
            else:
                dash_ready_text = self.font_small.render("Dash READY", True, self.PLAYER_COLOR)
                self.screen.blit(dash_ready_text, (10, dash_y_pos))

        # Speed Boost Timer (adjusted position)
        boost_y_pos = dash_y_pos + 40
        if self.player.speed_boost_active:
            time_elapsed_boost = pygame.time.get_ticks() - self.player.speed_boost_timer
            remaining_boost = (SPEED_BOOST_DURATION - time_elapsed_boost) / 1000.0
            if remaining_boost > 0:
                boost_text = self.font_small.render(f"Velocidad: {remaining_boost:.1f}s", True, self.BULLET_COLOR)
                self.screen.blit(boost_text, (10, boost_y_pos))

        # Charge Shot Power-up Indicator (Right Click)
        if self.player.has_charge_powerup:
            charge_powerup_text = self.font_small.render("Disparo Cargado (R-Click): LISTO", True, (255, 200, 0))
            self.screen.blit(charge_powerup_text, (WIDTH - charge_powerup_text.get_width() - 10, 10))
        else:
            charge_powerup_text = self.font_small.render("Disparo Cargado (R-Click): NO", True, (150, 150, 150))
            self.screen.blit(charge_powerup_text, (WIDTH - charge_powerup_text.get_width() - 10, 10))

        if self.player.is_charging_powerup_shot:
            charge_level_text = self.font_small.render(f"Cargando (R-Click): {self.player.charge_powerup_level*100:.0f}%", True, self.WHITE)
            self.screen.blit(charge_level_text, (WIDTH - charge_level_text.get_width() - 10, 50))
        
        # Red Weapon Charge Indicator (Left Click)
        if self.player.current_weapon == "red" and self.player.is_charging_red_weapon:
            red_charge_text = self.font_small.render(f"Cargando (Francotirador): {self.player.red_charge_level*100:.0f}%", True, self.WHITE)
            self.screen.blit(red_charge_text, (WIDTH - red_charge_text.get_width() - 10, 90))

        # Purple Weapon Charge Indicator (Left Click)
        if self.player.current_weapon == "purple" and self.player.is_charging_purple_shot:
            purple_charge_text = self.font_small.render(f"Cargando (Violeta): {self.player.purple_charge_level*100:.0f}%", True, self.WHITE)
            self.screen.blit(purple_charge_text, (WIDTH - purple_charge_text.get_width() - 10, 130))

        # Grappling Hook Status (Right Click for Purple Weapon)
        if self.player.current_weapon == "purple":
            if self.player.is_grappling:
                if self.player.grapple_attached_sprite:
                    grapple_status_text = self.font_small.render("Gancho: ENGANCHADO", True, (0, 255, 255))
                else:
                    grapple_status_text = self.font_small.render("Gancho: BUSCANDO...", True, (0, 200, 200))
            else:
                grapple_status_text = self.font_small.render("Gancho: LISTO (R-Click)", True, (100, 100, 255))
            self.screen.blit(grapple_status_text, (WIDTH - grapple_status_text.get_width() - 10, 170))

        # Collected Keys
        if self.player_keys:
            key_text = self.font_tiny.render("Llaves:", True, self.WHITE)
            self.screen.blit(key_text, (WIDTH - key_text.get_width() - 10, HEIGHT - 70))
            y_offset = 0
            for key_id in self.player_keys:
                key_name_text = self.font_tiny.render(f"- {key_id}", True, self.WHITE)
                self.screen.blit(key_name_text, (WIDTH - key_name_text.get_width() - 10, HEIGHT - 50 + y_offset))
                y_offset += 20

        # "Return to Editor" button for play-test mode
        if self.game_state == GAME_STATE_PLAYING_FROM_EDITOR:
            return_button_text = self.font_small.render("Volver al Editor (F1)", True, self.WHITE)
            return_button_rect = return_button_text.get_rect(topright=(WIDTH - 10, 10))
            pygame.draw.rect(self.screen, (50, 50, 50), return_button_rect.inflate(20, 10), border_radius=5)
            pygame.draw.rect(self.screen, (100, 100, 100), return_button_rect.inflate(20, 10), 2, border_radius=5)
            self.screen.blit(return_button_text, return_button_rect)


    def draw_game_over_screen(self):
        self.screen.fill(self.BLACK)
        game_over_text = self.font_large.render("¡FIN DEL JUEGO!", True, self.CHASER_ENEMY_COLOR)
        restart_text = self.font_medium.render("Presiona 'R' para Reiniciar o 'ESC' para Salir", True, self.WHITE)
        score_text = self.font_medium.render(f"Puntuación Final: {self.score}", True, self.WHITE)

        game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))

        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(restart_text, restart_rect)

    def draw_win_screen(self):
        self.screen.fill(self.BLACK)
        win_text = self.font_large.render("¡HAS GANADO!", True, self.PLAYER_COLOR)
        restart_text = self.font_medium.render("Presiona 'R' para Reiniciar o 'ESC' para Salir", True, self.WHITE)
        score_text = self.font_medium.render(f"Puntuación Final: {self.score}", True, self.WHITE)

        win_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))

        self.screen.blit(win_text, win_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(restart_text, restart_rect)

    def draw_menu_screen(self):
        self.screen.fill(self.BACKGROUND_COLOR)
        title_text = self.font_large.render("Juego Plataformero", True, self.WHITE)
        play_text = self.font_medium.render("Presiona 'P' para Jugar", True, self.WHITE)
        editor_text = self.font_medium.render("Presiona 'E' para Modo Editor", True, self.WHITE)
        
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
        play_rect = play_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        editor_rect = editor_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))

        self.screen.blit(title_text, title_rect)
        self.screen.blit(play_text, play_rect)
        self.screen.blit(editor_text, editor_rect)

    def draw_editor_screen(self):
        self.screen.fill((50, 50, 70)) # Un color diferente para el editor
        editor_title_text = self.font_large.render("MODO EDITOR", True, self.WHITE)
        exit_text = self.font_medium.render("Presiona 'F1' para Salir al Menú Principal", True, self.WHITE)
        save_text = self.font_medium.render("Presiona 'S' para Guardar Nivel", True, self.WHITE)
        tool_text = self.font_medium.render(f"Herramienta: {self.editor_selected_tool.replace('_', ' ').capitalize()}", True, self.WHITE)
        
        editor_title_rect = editor_title_text.get_rect(center=(WIDTH // 2, 50))
        exit_rect = exit_text.get_rect(center=(WIDTH // 2, HEIGHT - 80))
        save_rect = save_text.get_rect(center=(WIDTH // 2, HEIGHT - 40))
        tool_rect = tool_text.get_rect(center=(self.editor_panel.rect.right + (WIDTH - self.editor_panel.rect.right) // 2, 120)) # New position for tool text

        self.screen.blit(editor_title_text, editor_title_rect)
        self.screen.blit(exit_text, exit_rect)
        self.screen.blit(save_text, save_rect)
        self.screen.blit(tool_text, tool_rect) # Display current tool

        # Instructions for editor tools (simplified due to panel)
        instructions_text = [
            "Click IZQ en cuadrícula: Añadir elemento",
            "Click DER en cuadrícula: Eliminar elemento",
            "Arrastrar: Mover elemento",
            "Alt + Arrastrar: Duplicar elemento",
            "Doble Click IZQ: Editar propiedades",
            "Click Central: Panear cámara",
            "Seleccionar Plataforma + R: Rotar Plataforma",
            "Arrastrar bordes de Plataforma Horizontal: Redimensionar"
        ]
        
        y_offset = 180
        for line in instructions_text:
            line_surface = self.font_tiny.render(line, True, self.WHITE)
            self.screen.blit(line_surface, (self.editor_panel.rect.right + 20, y_offset))
            y_offset += 25


        self.draw_grid_editor() # Draw the fixed grid in editor mode

        # Draw existing sprites in editor mode (with camera offset)
        for sprite in self.all_sprites:
            # Draw player at its editor-defined start position
            # Ensure sprites are only drawn if they are within the visible screen area (after applying camera offset)
            sprite_screen_rect = sprite.rect.move(self.editor_camera_offset_x, self.editor_camera_offset_y)
            if sprite_screen_rect.right > self.editor_panel.rect.right and sprite_screen_rect.left < WIDTH and \
               sprite_screen_rect.bottom > 0 and sprite_screen_rect.top < HEIGHT:
                self.screen.blit(sprite.image, sprite_screen_rect)
                
                # Draw labels for Doors and Keys
                if isinstance(sprite, Door):
                    label_text = f"Puerta: {sprite.door_id}"
                    label_surface = self.font_tiny.render(label_text, True, self.WHITE)
                    label_rect = label_surface.get_rect(centerx=sprite_screen_rect.centerx, bottom=sprite_screen_rect.top - 5)
                    self.screen.blit(label_surface, label_rect)
                elif isinstance(sprite, Key):
                    label_text = f"Llave: {sprite.key_id}"
                    label_surface = self.font_tiny.render(label_text, True, self.WHITE)
                    label_rect = label_surface.get_rect(centerx=sprite_screen_rect.centerx, bottom=sprite_screen_rect.top - 5)
                    self.screen.blit(label_surface, label_rect)
            
            # Draw selection border for selected sprite (always, even if partially off-screen)
            if self.editor_selected_sprite == sprite:
                pygame.draw.rect(self.screen, (0, 255, 0), sprite.rect.move(self.editor_camera_offset_x, self.editor_camera_offset_y), 3) # Green border

        # Draw linking lines and highlight linked elements
        if self.editor_selected_sprite:
            if isinstance(self.editor_selected_sprite, Door):
                if self.editor_selected_sprite.required_key_id:
                    linked_key = next((k for k in self.keys if k.key_id == self.editor_selected_sprite.required_key_id), None)
                    if linked_key:
                        pygame.draw.line(self.screen, self.LINK_HIGHLIGHT_COLOR, 
                                         (self.editor_selected_sprite.rect.centerx + self.editor_camera_offset_x, self.editor_selected_sprite.rect.centery + self.editor_camera_offset_y), 
                                         (linked_key.rect.centerx + self.editor_camera_offset_x, linked_key.rect.centery + self.editor_camera_offset_y), 2)
                        pygame.draw.rect(self.screen, self.LINK_HIGHLIGHT_COLOR, linked_key.rect.move(self.editor_camera_offset_x, self.editor_camera_offset_y), 3) # Highlight linked key
            elif isinstance(self.editor_selected_sprite, Key):
                for door in self.doors:
                    if door.required_key_id == self.editor_selected_sprite.key_id:
                        pygame.draw.line(self.screen, self.LINK_HIGHLIGHT_COLOR, 
                                         (self.editor_selected_sprite.rect.centerx + self.editor_camera_offset_x, self.editor_selected_sprite.rect.centery + self.editor_camera_offset_y), 
                                         (door.rect.centerx + self.editor_camera_offset_x, door.rect.centery + self.editor_camera_offset_y), 2)
                        pygame.draw.rect(self.screen, self.LINK_HIGHLIGHT_COLOR, door.rect.move(self.editor_camera_offset_x, self.editor_camera_offset_y), 3) # Highlight linked door


        # Draw the editor panel on top
        self.editor_panel.draw(self.screen)


    def _draw_load_level_overlay(self):
        # Darken background
        overlay_bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay_bg.fill((0, 0, 0, 180))
        self.screen.blit(overlay_bg, (0, 0))

        # Draw the overlay panel
        pygame.draw.rect(self.screen, (60, 60, 80), self.load_level_overlay_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 100, 120), self.load_level_overlay_rect, 3, border_radius=10)

        title_text = self.font_medium.render("Seleccionar Nivel para Cargar", True, self.WHITE)
        title_rect = title_text.get_rect(center=(self.load_level_overlay_rect.centerx, self.load_level_overlay_rect.y + 25))
        self.screen.blit(title_text, title_rect)

        # List levels
        item_y = self.load_level_overlay_rect.y + 50
        for filename in self.available_levels_for_load:
            item_rect = pygame.Rect(self.load_level_overlay_rect.x + 10, item_y, self.load_level_overlay_rect.width - 20, 30)
            
            # Highlight on hover (for visual feedback)
            mouse_pos = pygame.mouse.get_pos()
            if item_rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, (100, 100, 150), item_rect, border_radius=5)
            else:
                pygame.draw.rect(self.screen, (80, 80, 100), item_rect, border_radius=5)
            
            pygame.draw.rect(self.screen, (150, 150, 200), item_rect, 1, border_radius=5)

            item_text = self.font_small.render(filename, True, self.WHITE)
            item_text_rect = item_text.get_rect(midleft=(item_rect.x + 10, item_rect.centery))
            self.screen.blit(item_text, item_text_rect)
            item_y += 35
        
        # Cancel button
        cancel_button_rect = pygame.Rect(self.load_level_overlay_rect.centerx - 50, self.load_level_overlay_rect.bottom - 40, 100, 30)
        pygame.draw.rect(self.screen, (150, 50, 50), cancel_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, (200, 100, 100), cancel_button_rect, 2, border_radius=5)
        cancel_text = self.font_small.render("Cancelar", True, self.WHITE)
        cancel_text_rect = cancel_text.get_rect(center=cancel_button_rect.center)
        self.screen.blit(cancel_text, cancel_text_rect)


    def draw_saving_level_input_screen(self):
        self.screen.fill(self.BACKGROUND_COLOR)
        prompt_text = self.font_medium.render("Introduce el nombre del archivo del nivel:", True, self.WHITE)
        
        self.screen.blit(prompt_text, prompt_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))
        self.filename_input_box.draw(self.screen)

        confirm_text = self.font_small.render("Presiona ENTER para guardar, ESC para cancelar", True, self.WHITE)
        self.screen.blit(confirm_text, confirm_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))
    
    def draw_editing_properties_screen(self):
        self.screen.fill(self.BACKGROUND_COLOR)
        
        title_text = self.font_medium.render(self.property_edit_message, True, self.WHITE)
        self.screen.blit(title_text, title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150)))

        y_offset = HEIGHT // 2 - 100
        for prop_name, input_box in self.property_input_boxes.items():
            prop_label = self.font_small.render(f"{prop_name.replace('_', ' ').capitalize()}:", True, self.WHITE)
            self.screen.blit(prop_label, (input_box.rect.x - prop_label.get_width() - 10, input_box.rect.y + 10))
            input_box.draw(self.screen)
            y_offset += 60
        
        # Display available IDs as hints (still useful even with dropdowns for overview)
        if self.editing_sprite:
            hint_y_offset = y_offset + 20
            if isinstance(self.editing_sprite, Door):
                keys_hint = ", ".join(self.available_property_ids.get("keys", []))
                weapons_hint = ", ".join(self.available_property_ids.get("weapons", []))
                if keys_hint:
                    keys_text = self.font_tiny.render(f"Llaves disponibles: {keys_hint}", True, (150, 150, 150))
                    self.screen.blit(keys_text, (WIDTH // 2 - keys_text.get_width() // 2, hint_y_offset))
                    hint_y_offset += 25
                if weapons_hint:
                    weapons_text = self.font_tiny.render(f"Armas disponibles: {weapons_hint}", True, (150, 150, 150))
                    self.screen.blit(weapons_text, (WIDTH // 2 - weapons_text.get_width() // 2, hint_y_offset))
                    hint_y_offset += 25
            elif isinstance(self.editing_sprite, Key):
                doors_hint = ", ".join(self.available_property_ids.get("doors", []))
                if doors_hint:
                    doors_text = self.font_tiny.render(f"Puertas disponibles: {doors_hint}", True, (150, 150, 150))
                    self.screen.blit(doors_text, (WIDTH // 2 - doors_text.get_width() // 2, hint_y_offset))
                    hint_y_offset += 25

        confirm_text = self.font_small.render("Presiona ENTER para aplicar, ESC para cancelar", True, self.WHITE)
        self.screen.blit(confirm_text, confirm_text.get_rect(center=(WIDTH // 2, hint_y_offset + 30)))


    def draw(self):
        self.screen.fill(self.BACKGROUND_COLOR)

        if self.game_state == GAME_STATE_PLAYING or self.game_state == GAME_STATE_PLAYING_FROM_EDITOR:
            # Calculate camera offset to center player
            self.camera_offset_x = self.player.rect.centerx - WIDTH // 2
            self.camera_offset_y = self.player.rect.centery - HEIGHT // 2

            # CORRECCIÓN: Eliminar el clamping de la cámara para que siga al jugador sin límites
            # self.camera_offset_x = max(0, min(self.camera_offset_x, self.level_width - WIDTH))
            # self.camera_offset_y = max(0, min(self.camera_offset_y, self.level_height - HEIGHT))

            # DO NOT draw grid in play mode

            for sprite in self.all_sprites:
                self.screen.blit(sprite.image, (sprite.rect.x - self.camera_offset_x, sprite.rect.y - self.camera_offset_y))

            # Draw player aiming cone only when charging AND has powerup (right click)
            if self.player.is_charging_powerup_shot and self.player.has_charge_powerup:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                player_screen_x = self.player.rect.centerx - self.camera_offset_x
                player_screen_y = self.player.rect.centery - self.camera_offset_y

                dir_x = mouse_x - player_screen_x
                dir_y = mouse_y - player_screen_y
                
                angle_rad = math.atan2(-dir_y, dir_x)
                angle_deg = math.degrees(angle_rad)

                current_cone_length = AIM_CONE_BASE_LENGTH + (AIM_CONE_MAX_LENGTH - AIM_CONE_BASE_LENGTH) * self.player.charge_powerup_level

                p1 = (player_screen_x, player_screen_y)

                cone_dir_x = current_cone_length * math.cos(angle_rad)
                cone_dir_y = -current_cone_length * math.sin(angle_rad)

                perp_dir_x = -AIM_CONE_WIDTH / 2 * math.sin(angle_rad)
                perp_dir_y = -AIM_CONE_WIDTH / 2 * math.cos(angle_rad)

                p2 = (player_screen_x + cone_dir_x + perp_dir_x, player_screen_y + cone_dir_y + perp_dir_y)
                p3 = (player_screen_x + cone_dir_x - perp_dir_x, player_screen_y + cone_dir_y - perp_dir_y)

                cone_points = [p1, p2, p3]

                cone_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                
                current_cone_color = self.AIM_CONE_COLOR
                if self.player.charge_powerup_level == 1.0:
                    now = pygame.time.get_ticks()
                    if (now // AIM_CONE_BLINK_INTERVAL) % 2 == 0:
                        current_cone_color = (255, 255, 0, 150)
                    else:
                        current_cone_color = self.AIM_CONE_COLOR

                pygame.draw.polygon(cone_surface, current_cone_color, cone_points)
                self.screen.blit(cone_surface, (0, 0))
            
            # Draw red weapon aiming cone only when charging (left click)
            if self.player.current_weapon == "red" and self.player.is_charging_red_weapon:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                player_screen_x = self.player.rect.centerx - self.camera_offset_x
                player_screen_y = self.player.rect.centery - self.camera_offset_y

                dir_x = mouse_x - player_screen_x
                dir_y = mouse_y - player_screen_y
                
                angle_rad = math.atan2(-dir_y, dir_x)
                angle_deg = math.degrees(angle_rad)

                current_cone_length = AIM_CONE_BASE_LENGTH + (AIM_CONE_MAX_LENGTH - AIM_CONE_BASE_LENGTH) * self.player.red_charge_level

                p1 = (player_screen_x, player_screen_y)

                cone_dir_x = current_cone_length * math.cos(angle_rad)
                cone_dir_y = -current_cone_length * math.sin(angle_rad)

                perp_dir_x = -AIM_CONE_WIDTH / 2 * math.sin(angle_rad)
                perp_dir_y = -AIM_CONE_WIDTH / 2 * math.cos(angle_rad)

                p2 = (player_screen_x + cone_dir_x + perp_dir_x, player_screen_y + cone_dir_y + perp_dir_y)
                p3 = (player_screen_x + cone_dir_x - perp_dir_x, player_screen_y + cone_dir_y - perp_dir_y)

                cone_points = [p1, p2, p3]

                cone_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                
                current_cone_color = (255, 50, 0, 100) # Red weapon cone color
                if self.player.red_charge_level == 1.0:
                    now = pygame.time.get_ticks()
                    if (now // AIM_CONE_BLINK_INTERVAL) % 2 == 0:
                        current_cone_color = (255, 255, 0, 150) # Yellowish blink
                    else:
                        current_cone_color = (255, 50, 0, 100) # Original red

                pygame.draw.polygon(cone_surface, current_cone_color, cone_points)
                self.screen.blit(cone_surface, (0, 0))

            # Draw purple weapon arc trajectory when charging (left click)
            if self.player.current_weapon == "purple" and self.player.is_charging_purple_shot:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                player_screen_x = self.player.rect.centerx - self.camera_offset_x
                player_screen_y = self.player.rect.centery - self.camera_offset_y

                # Calculate initial velocities based on mouse position and charge level
                target_x_world = mouse_x + self.camera_offset_x
                target_y_world = mouse_y + self.camera_offset_y
                
                dx = target_x_world - self.player.rect.centerx
                # The dy for aiming is relative to player, but for arc calculation it's from player to target
                dy = target_y_world - self.player.rect.centery

                # Simplified arc calculation for visualization
                # vx is influenced by horizontal distance and charge
                vx = dx * PURPLE_ARC_SPEED_FACTOR * (0.5 + self.player.purple_charge_level * 0.5)
                # vy is influenced by vertical distance and charge (for initial upward push)
                # We want a higher arc for higher charge
                initial_vy = - (PURPLE_ARC_MAX_HEIGHT * (0.5 + self.player.purple_charge_level * 0.5)) / 10 # Scale down for reasonable velocity

                arc_points = []
                num_steps = 50
                for i in range(num_steps):
                    t = i / float(self.FPS) # Time step
                    
                    # Calculate position at time t
                    px = self.player.rect.centerx + vx * t
                    py = self.player.rect.centery + initial_vy * t + 0.5 * BULLET_GRAVITY_EFFECT * t**2
                    
                    # Convert to screen coordinates
                    screen_px = px - self.camera_offset_x
                    screen_py = py - self.camera_offset_y
                    arc_points.append((screen_px, screen_py))

                if len(arc_points) > 1:
                    pygame.draw.lines(self.screen, self.PURPLE_ARC_COLOR, False, arc_points, 2)
            
            # Draw purple grappling hook line (right click)
            if self.player.current_weapon == "purple" and self.player.is_grappling:
                player_screen_x = self.player.rect.centerx - self.camera_offset_x
                player_screen_y = self.player.rect.centery - self.camera_offset_y
                
                if self.player.grapple_attached_sprite:
                    # Draw line to attached point
                    target_screen_x = self.player.grapple_target_pos[0] - self.camera_offset_x
                    target_screen_y = self.player.grapple_target_pos[1] - self.camera_offset_y
                    pygame.draw.line(self.screen, self.PURPLE_HOOK_COLOR, (player_screen_x, player_screen_y), (target_screen_x, target_screen_y), 3)
                else:
                    # Draw line towards mouse, limited by hook range
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    player_center_screen = pygame.math.Vector2(player_screen_x, player_screen_y)
                    mouse_screen_vec = pygame.math.Vector2(mouse_x, mouse_y)
                    
                    direction_vec = (mouse_screen_vec - player_center_screen)
                    
                    max_hook_length_pixels = PURPLE_HOOK_RANGE_CELLS * self.GRID_SIZE
                    if direction_vec.length() > max_hook_length_pixels:
                        direction_vec.scale_to_length(max_hook_length_pixels)
                    
                    hook_end_point_screen = player_center_screen + direction_vec
                    pygame.draw.line(self.screen, self.PURPLE_HOOK_COLOR, (player_screen_x, player_screen_y), hook_end_point_screen, 3)
                    # Draw a small circle at the end of the hook line to indicate potential attachment point
                    pygame.draw.circle(self.screen, self.PURPLE_HOOK_COLOR, (int(hook_end_point_screen.x), int(hook_end_point_screen.y)), 5)


            self.draw_hud()
        
        elif self.game_state == GAME_STATE_GAME_OVER:
            self.draw_game_over_screen()
        
        elif self.game_state == GAME_STATE_WIN:
            self.draw_win_screen()
        
        elif self.game_state == GAME_STATE_MENU:
            self.draw_menu_screen()
        
        elif self.game_state == GAME_STATE_EDITOR:
            self.draw_editor_screen()
        
        elif self.game_state == GAME_STATE_SAVING_LEVEL_INPUT:
            self.draw_saving_level_input_screen()
        
        elif self.game_state == GAME_STATE_EDITING_PROPERTIES:
            self.draw_editing_properties_screen()
        
        elif self.game_state == GAME_STATE_LOAD_LEVEL_MENU:
            self.draw_editor_screen() # Draw editor as background
            self._draw_load_level_overlay() # Draw overlay on top


        pygame.display.flip()

    def reset_game(self):
        self.score = 0
        self.current_level_idx = 0
        self.game_state = GAME_STATE_PLAYING # Start playing the first level again
        # Reload the first level from the loaded files
        if self.loaded_levels_from_files:
            self.load_level_from_dict(self.loaded_levels_from_files[0]["data"])
        else:
            print("No hay niveles cargados para reiniciar. Volviendo al menú.")
            self.game_state = GAME_STATE_MENU # Fallback to menu if no levels

    def run(self):
        running = True
        while running:
            if self.game_state == GAME_STATE_MENU:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.VIDEORESIZE: # Handle resize in menu too
                        global WIDTH, HEIGHT, SCREEN
                        WIDTH, HEIGHT = event.w, event.h
                        SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.SCALED)
                        # Reajustar la posición del panel del editor y otros elementos de la interfaz si es necesario
                        self.editor_panel.rect.height = HEIGHT - 20
                        self.filename_input_box.rect.center = (WIDTH // 2, HEIGHT // 2 - 25)
                        self.load_level_overlay_rect.center = (WIDTH // 2, HEIGHT // 2)
                        print(f"Ventana redimensionada a: {WIDTH}x{HEIGHT}")
                    if event.type == pygame.KEYDOWN: 
                        if event.key == pygame.K_p: # Press P to Play
                            self.game_state = GAME_STATE_PLAYING
                            # Start from the first level loaded from files
                            if self.loaded_levels_from_files:
                                self.load_level_from_dict(self.loaded_levels_from_files[0]["data"])
                                self.current_level_idx = 0 # Reset level index for playing
                            else:
                                print("No hay niveles cargados. Volviendo al menú.")
                                self.game_state = GAME_STATE_MENU # Go back to menu if no levels
                        if event.key == pygame.K_e: # Press E for Editor
                            self.game_state = GAME_STATE_EDITOR
                            # When entering editor, clear existing sprites and load a blank canvas
                            self._clear_all_sprites()
                            # Place player at a fixed world coordinate, not screen coordinate
                            self.player.rect.center = (250, 250) # Example fixed world coordinate
                            self.editor_selected_sprite = None # Clear selected sprite
                            self.resizing_platform = False # Stop resizing
                            self.editor_camera_offset_x = 0
                            self.editor_camera_offset_y = 0
                            # Set default level dimensions for a new editor level
                            self.level_width = WIDTH * 2
                            self.level_height = HEIGHT * 2
                            print("Modo editor iniciado. Canvas limpio.")
            
            else: # All other game states
                running = self.handle_events()
                if not running: break

                if self.game_state == GAME_STATE_PLAYING or self.game_state == GAME_STATE_PLAYING_FROM_EDITOR:
                    self.update()
                elif self.game_state == GAME_STATE_EDITOR:
                    self.update() # Llama a la lógica de actualización del editor (actualmente vacía)
                elif self.game_state == GAME_STATE_SAVING_LEVEL_INPUT:
                    self.update() # No update logic, just waiting for input
                elif self.game_state == GAME_STATE_EDITING_PROPERTIES:
                    self.update() # No update logic, just waiting for input
                elif self.game_state == GAME_STATE_LOAD_LEVEL_MENU:
                    self.update() # No update logic, just waiting for input

            self.draw()
            self.clock.tick(self.FPS)
        
        pygame.quit()
        sys.exit()

# --- Main Game Loop Execution ---
if __name__ == "__main__":
    game = Game()
    game.run()

