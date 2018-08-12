import random

import backend.systems.physics
import pygame


# class Oliver(backend.systems.physics.PhysicsMixin, backend.systems.entities.Player):
#     def __init__(self, x, y, sprites, scale=1.0):
#         super(Oliver, self).__init__(x, y, sprites, scale)
#         self.speed = 5
#         self.jump_power = 10
#
#     def jump(self):
#         """Called when the user presses the jump button."""
#         if not self.fall:
#             self.y_vel_i = -self.jump_power
#             self.fall = True
#
#     def update(self, colliders, surface, cam):
#         super(Oliver, self).update(colliders, surface, cam)
#         if not self.fall:
#             self.check_falling(colliders)
#         else:
#             self.fall = self.check_collisions((0, self.y_vel), 1, colliders)
#         self.physics_update()

class RestartGameException(Exception):
    pass


class Timer(pygame.font.Font):
    def __init__(self, size, max_time, aa=True):
        super(Timer, self).__init__(None, size)
        self.max_time = max_time
        self.time = max_time
        self.aa = aa

        self.low_time = False

    def update(self, milliseconds_passed):
        self.time -= milliseconds_passed / 1000

        if self.time < self.max_time / 10 and not self.low_time:
            pygame.mixer.music.load("assets/sound/time_low.wav")
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1)
            self.low_time = True

        if self.time <= 0:
            self.time = 0
            return None

        m, s = divmod(self.time, 60)
        return self.render(f"{m:02.0f}:{s:02.0f}", self.aa, (0, 0, 0))


class Score(pygame.font.Font):
    def __init__(self, size, score=0, aa=True):
        super(Score, self).__init__(None, size)
        self.score = score
        self.boxes_in_truck = []
        self.aa = aa

        self.item_values = {"large crate": 1000,
                            "small crate": 250,
                            "long crate": 500,
                            "small box": 250,
                            "table": 2500,
                            "dog": 50000,
                            "pipe": 750,
                            "big table": 5000,
                            "chair": 2500}

    def update(self, box_controller, truck):
        area, boxes_in_truck = box_controller.area_in_truck(truck)
        if boxes_in_truck != self.boxes_in_truck:
            new_boxes = [x for x in boxes_in_truck if x not in self.boxes_in_truck]

            if new_boxes:
                self.boxes_in_truck = boxes_in_truck
                return self.update_score(self.calc_score(area, new_boxes, truck))
            else:
                removed_boxes = [x for x in self.boxes_in_truck if x not in boxes_in_truck]
                self.boxes_in_truck = boxes_in_truck
                return self.update_score(self.calc_score(area, removed_boxes, truck, remove=True))

        return self.render(f"{self.score:011.0f}", self.aa, (0, 0, 0))

    def calc_score(self, area, new_boxes, truck, remove=False):
        values = [self.item_values[box.shape] for box in new_boxes]
        if remove:
            score = -sum(values)
            area += sum([box.get_area() for box in new_boxes])
        else:
            score = sum(values)

        score *= area / truck.trailer_area

        return score

    def update_score(self, increment):
        self.score += increment
        return self.render(f"{self.score:011.0f}", self.aa, (0, 0, 0))


class ScoreBreakdown(object):
    def __init__(self, score, box_controller, truck, aa=True):
        self.score = score
        self.box_controller = box_controller
        self.truck = truck
        self.aa = aa

        self.base_score = pygame.font.Font(None, 96)
        self.efficiency = pygame.font.Font(None, 96)
        self.total_score = pygame.font.Font(None, 128)

    @staticmethod
    def closest_value(n, ls):
        closest = 0
        key = 0
        for item in ls:
            if n > item:
                if abs(n - item) < closest or closest == 0:
                    closest = abs(n - item)
                    key = item

        return key

    def get_grade(self, efficiency):
        grades = {95: "A+", 80: "A", 75: "B+", 70: "B", 65: "C+", 60: "C", 55: "D+", 50: "D", 45: "F+", 40: "F",
                  0: "F-"}

        return grades[self.closest_value(efficiency, grades.keys())]

    def update(self):
        base_value = sum([self.score.item_values[box.shape] for box in self.score.boxes_in_truck])
        area, boxes_in_truck = self.box_controller.area_in_truck(self.truck)
        efficiency = area / self.truck.trailer_area
        total_score = base_value * efficiency
        return self.base_score.render(f"Base Score: {base_value:.0f}", self.aa, (0, 0, 0)), \
               self.efficiency.render(f"Grade: {self.get_grade(efficiency * 100)}", self.aa, (0, 0, 0)), \
               self.total_score.render(f"Final Score: {total_score:.0f}", self.aa, (0, 0, 0))


class Button(backend.systems.entities.StaticSprite):
    def __init__(self, sprite_paths, scale=1.0):
        super(Button, self).__init__(0, 0, sprite_paths, scale)
        self.cooldown = 0
        self.select_sound = pygame.mixer.Sound("assets/sound/select.wav")
        self.select_sound.set_volume(0.25)
        self.select_played = False

    def set_pos(self, x, y):
        self.rect.topleft = x, y

    def update(self, *args):
        if not self.cooldown:
            mouse = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse[0], mouse[1]):
                self.image = self.sprites["hover"]
                if not self.select_played:
                    self.select_sound.play()
                    self.select_played = True
            else:
                self.image = self.sprites["base"]
                self.select_played = False
        else:
            self.cooldown -= 1

    def pressed(self):
        mouse = pygame.mouse.get_pos()

        self.image = self.sprites["pressed"]
        self.cooldown = 25
        return True if self.rect.collidepoint(mouse[0], mouse[1]) else False


class RestartButton(Button):
    def __init__(self, scale=1.0):
        super(RestartButton, self).__init__({"base": "assets/sprites/buttons/restart_button.png",
                                             "hover": "assets/sprites/buttons/restart_button_hover.png",
                                             "pressed": "assets/sprites/buttons/restart_button_pressed.png"}, scale)


class QuitButton(Button):
    def __init__(self, scale=1.0):
        super(QuitButton, self).__init__({"base": "assets/sprites/buttons/quit_button.png",
                                          "hover": "assets/sprites/buttons/quit_button_hover.png",
                                          "pressed": "assets/sprites/buttons/quit_button_pressed.png"}, scale)


class StartButton(Button):
    def __init__(self, scale=1.0):
        super(StartButton, self).__init__({"base": "assets/sprites/buttons/start_button.png",
                                           "hover": "assets/sprites/buttons/start_button_hover.png",
                                           "pressed": "assets/sprites/buttons/start_button_pressed.png"}, scale)


class ControlsButton(Button):
    def __init__(self, scale=1.0):
        super(ControlsButton, self).__init__({"base": "assets/sprites/buttons/controls_button.png",
                                              "hover": "assets/sprites/buttons/controls_button_hover.png",
                                              "pressed": "assets/sprites/buttons/controls_button_pressed.png"}, scale)


class Truck(backend.systems.entities.StaticSprite):
    def __init__(self, x, y, sprite, scale=1.0):
        super(Truck, self).__init__(x, y, {"base": sprite}, scale)
        self._trailer_area = None

        self.trailer_area = None

    @property
    def trailer_area(self):
        if not self._trailer_area:
            self.trailer_area = None
        return self._trailer_area

    @trailer_area.setter
    def trailer_area(self, value=None):
        if value:
            self._trailer_area = value
        else:
            image_size = self.image.get_size()
            count = 0
            for x in range(image_size[0]):
                for y in range(image_size[1]):
                    if self.image.get_at((x, y))[3] == 50:
                        count += 1
            self._trailer_area = count


class BoxController(pygame.sprite.Group):
    def __init__(self, spritesheet, surface, scale, *sprites):
        super(BoxController, self).__init__(*sprites)
        self.box_selected = None
        self.scale = scale
        self.surface = surface
        self.weights = [0.04, 0.04, 0.04, 0.04, 0.5, 0.01, 0.2, 0.5, 0.5]
        self.images = {"large crate": spritesheet.image_at(pygame.Rect(0, 0, 32, 32)),
                       "small crate": spritesheet.image_at(pygame.Rect(32, 0, 16, 16)),
                       "long crate": spritesheet.image_at(pygame.Rect(32, 16, 32, 16)),
                       "small box": spritesheet.image_at(pygame.Rect(48, 0, 16, 16)),
                       "table": spritesheet.image_at(pygame.Rect(64, 0, 32, 32)),
                       "dog": spritesheet.image_at(pygame.Rect(96, 0, 32, 32)),
                       "pipe": spritesheet.image_at(pygame.Rect(128, 0, 32, 32)),
                       "big table": spritesheet.image_at(pygame.Rect(160, 0, 64, 32)),
                       "chair": spritesheet.image_at(pygame.Rect(224, 0, 32, 64))}

    def populate(self, num_boxes, *other_groups):
        width, height = self.surface.get_size()
        for box in range(num_boxes):
            selector = random.choices(list(self.images.keys()), self.weights)[0]
            Box(random.randint(width / 2, width), random.randint(0, height - 96 * self.scale),
                self.images[selector], selector, self.scale).add(self, *other_groups)

    def toggle(self):
        if not self.box_selected:
            for box in self.sprites():
                if box.rect.collidepoint(pygame.mouse.get_pos()):
                    box.toggle()
                    self.box_selected = box
                    break
        else:
            self.box_selected.toggle()
            self.box_selected = None

    def rotate_selected(self, angle):
        if self.box_selected:
            self.box_selected.rotate(self.box_selected.angle + angle)

    def area_in_truck(self, truck):
        boxes_in_truck = []
        for box in self.sprites():
            if pygame.sprite.collide_rect(box, truck):
                boxes_in_truck.append(box)

        return sum([box.get_area() for box in boxes_in_truck]), boxes_in_truck

    def draw(self, surface):
        for sprite in self.sprites():
            sprite.draw(surface)


class Box(backend.systems.physics.PhysicsMixin, backend.systems.entities.DynamicSprite):
    def __init__(self, x, y, sprite, shape, scale=1.0):
        super(Box, self).__init__(x, y, {"base": sprite}, scale)

        self.held = False
        self.shape = shape

    def update(self, colliders, surface, cam):
        if not self.fall:
            self.check_falling(colliders)
        else:
            self.fall = self.check_collisions((0, self.y_vel), 1, colliders)
        self.physics_update()

        if self.held:
            self.move_to_target(pygame.mouse.get_pos(), colliders)

        super(Box, self).update(colliders, surface, cam)

    def draw(self, surface):
        if self.held:
            self.draw_selector(surface)

    def toggle(self):
        self.held = False if self.held else True

    def move_to_target(self, target, colliders):
        dx = target[0] - self.rect.center[0]
        dy = target[1] - self.rect.center[1]

        self.move(dx, dy, colliders)

    def draw_selector(self, surface):
        color_key = (127, 33, 33)
        overlay = pygame.Surface(self.rect.size)
        overlay.fill(color_key)
        overlay.set_colorkey(color_key)
        pygame.draw.circle(overlay, (255, 255, 0), [x // 2 for x in self.rect.size], self.rect.width // 4, 5)
        overlay.set_alpha(75)

        surface.blit(overlay, self.rect.topleft)

    def get_area(self):
        return self.mask.count()


class Ground(backend.systems.entities.StaticSprite):
    def __init__(self, x, y, sprite, scale=1.0):
        super(Ground, self).__init__(x, y, {"base": sprite}, scale)
