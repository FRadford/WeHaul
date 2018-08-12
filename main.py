import math
import sys

import pygame

import backend
import extend.entities

# Colours
WHITE = 255, 255, 255
SKY = 176, 210, 232


class Game(object):
    """
    Control main loop and game states
    """

    def __init__(self):
        self.running = True
        self.game_ended = False
        self.menu_shown = False

        # pygame setup
        pygame.init()
        monitor_info = pygame.display.Info()
        self.screen = pygame.display.set_mode((monitor_info.current_w, monitor_info.current_h), pygame.FULLSCREEN)
        self.RESOLUTION = self.width, self.height = self.screen.get_size()
        self.SPRITE_SCALE = self.RESOLUTION[0] // 512

        self.camera = backend.systems.camera.Camera(backend.systems.camera.simple_camera, (self.width, self.height))
        self.clock = pygame.time.Clock()

        self.fps = 60
        self.keys = None
        self.game_time = 120

        self.timer = extend.entities.Timer(32, self.game_time)
        self.score_counter = extend.entities.Score(40)

        self.timer_display = None
        self.score_display = None

        # spritesheets
        self.box_sprites = backend.systems.spritesheets.SpriteSheet("assets/sprites/boxes.png")
        self.environment = backend.systems.spritesheets.SpriteSheet("assets/sprites/environment.png")

        # group setup
        self.all_sprites = pygame.sprite.Group()
        self.colliders = pygame.sprite.Group()

        self.boxes = extend.entities.BoxController(self.box_sprites, self.screen, self.SPRITE_SCALE)
        self.truck = extend.entities.Truck(32, self.height - (self.SPRITE_SCALE * 160),
                                           self.environment.image_at(pygame.Rect(0, 0, 256, 128)), self.SPRITE_SCALE)

        self.final_score = extend.entities.ScoreBreakdown(self.score_counter, self.boxes, self.truck)
        self.restart_button = extend.entities.RestartButton(self.SPRITE_SCALE)
        self.quit_button = extend.entities.QuitButton(self.SPRITE_SCALE)

        self.start_button = extend.entities.StartButton(self.SPRITE_SCALE)
        # self.controls_button = extend.entities.ControlsButton(self.SPRITE_SCALE)
        self.logo = backend.systems.entities.StaticSprite(0, 0, {"base": "assets/sprites/logo.png"}, self.SPRITE_SCALE)

        # sound setup
        pygame.mixer.music.load("assets/sound/theme.wav")
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)

        self.show_menu()

    def create_floor(self):
        for x in range(int(math.ceil(self.width / (self.SPRITE_SCALE * 32)))):
            extend.entities.Ground(x * (self.SPRITE_SCALE * 32), self.height - (self.SPRITE_SCALE * 32),
                                   self.environment.image_at(pygame.Rect(32 * 8, 0, 32, 32)),
                                   self.SPRITE_SCALE).add(self.colliders, self.all_sprites)

    def show_menu(self):
        self.menu_shown = True

        self.logo.rect.topleft = (self.width / 2 - self.logo.rect.width / 2,
                                  self.height / 5 - self.logo.rect.height / 5)
        self.logo.add(self.all_sprites)

        self.start_button.set_pos(self.width / 2 - self.start_button.rect.width / 2,
                                  self.height - (self.height / 3 - self.start_button.rect.height / 3))
        self.start_button.add(self.all_sprites)

        # self.controls_button.set_pos(self.width / 2 - self.start_button.rect.width / 2,
        #                           self.height - (self.height / 5 - self.start_button.rect.height / 5))
        # self.controls_button.add(self.all_sprites)

    def start_game(self):
        pygame.mixer.music.load("assets/sound/game_start.wav")
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pass

        pygame.mixer.music.load("assets/sound/theme.wav")
        pygame.mixer.music.play(-1)

        self.menu_shown = False
        self.logo.kill()
        self.start_button.kill()
        # self.controls_button.kill()

        self.create_floor()  # add gorund to the scene
        self.boxes.populate(50, self.colliders, self.all_sprites)  # add boxes to the scene
        self.truck.add(self.all_sprites, self.colliders)  # add truck to scene

    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or self.keys[pygame.K_ESCAPE]:
                self.running = False
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.boxes.toggle()
                if event.button == 4:
                    self.boxes.rotate_selected(5)
                if event.button == 5:
                    self.boxes.rotate_selected(-5)

            if self.keys[pygame.K_LEFTBRACKET]:
                self.boxes.rotate_selected(5)
            if self.keys[pygame.K_RIGHTBRACKET]:
                self.boxes.rotate_selected(-5)
            if self.keys[pygame.K_r]:
                self.restart()

            if self.menu_shown:
                if event.type == pygame.MOUSEBUTTONUP:
                    if self.start_button.pressed():
                        self.start_game()

            if self.game_ended:
                if event.type == pygame.MOUSEBUTTONUP:
                    if self.restart_button.pressed():
                        self.restart()
                    if self.quit_button.pressed():
                        self.running = False

    def update(self):
        self.keys = pygame.key.get_pressed()
        self.all_sprites.update(self.colliders, self.screen, self.camera)

        if not self.game_ended and not self.menu_shown:
            self.timer_display = self.timer.update(self.clock.get_time())
            self.score_display = self.score_counter.update(self.boxes, self.truck)

    def draw(self):
        self.screen.fill(SKY)
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, self.camera.apply(sprite))

        self.boxes.draw(self.screen)

        if self.score_display:
            self.screen.blit(self.score_display, self.screen.blit(self.score_display, (
            self.width / 2 - self.score_display.get_rect().width / 2, 16)))
        if self.timer_display:
            self.screen.blit(self.timer_display, (self.width / 2 - self.timer_display.get_rect().width / 2, 48))
        if self.timer.time <= 0:
            self.game_over()

    def game_over(self):
        self.game_ended = True
        base_score, efficiency, total_score = self.final_score.update()
        self.all_sprites.empty()

        self.restart_button.set_pos(self.width / 2 - self.restart_button.rect.width / 2,
                                    self.height - (self.height / 3 - self.restart_button.rect.height / 3))
        self.restart_button.add(self.all_sprites)

        self.quit_button.set_pos(self.width / 2 - self.quit_button.rect.width / 2,
                                 self.height - (self.height / 5 - self.quit_button.rect.height / 5))
        self.quit_button.add(self.all_sprites)

        self.screen.blit(base_score, (
        self.width / 2 - base_score.get_rect().width / 2, self.height / 4 - base_score.get_rect().height))
        self.screen.blit(efficiency, (
        self.width / 2 - efficiency.get_rect().width / 2, self.height / 3 - efficiency.get_rect().height))
        self.screen.blit(total_score, (
        self.width / 2 - total_score.get_rect().width / 2, self.height / 2 - total_score.get_rect().height))

    def restart(self):
        self.__init__()
        raise extend.entities.RestartGameException("Restarting Game")

    def main_loop(self):
        while self.running:
            try:
                self.update()
                self.event_loop()
                self.draw()
                pygame.display.flip()
                self.clock.tick(self.fps)
            except extend.entities.RestartGameException:
                continue


if __name__ == '__main__':
    game = Game()
    game.main_loop()
    pygame.quit()
    sys.exit()
