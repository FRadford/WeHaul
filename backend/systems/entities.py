import math
from random import gauss, randint

import pygame

from pygame.math import Vector2


def collision_normal(left_mask, right_mask, left_rect, right_rect):
    left_pos = Vector2(left_rect.x, left_rect.y)
    right_pos = Vector2(right_rect.x, right_rect.y)

    offset = Vector2(list(map(int, left_pos - right_pos)))
    overlap = left_mask.overlap_area(right_mask, list(map(int, offset)))

    if not overlap:
        return

    nx = (left_mask.overlap_area(right_mask, list(map(int, Vector2(offset.x + 1, offset.y)))) -
          left_mask.overlap_area(right_mask, list(map(int, Vector2(offset.x - 1, offset.y)))))
    ny = (left_mask.overlap_area(right_mask, list(map(int, Vector2(offset.x, offset.y + 1)))) -
          left_mask.overlap_area(right_mask, list(map(int, Vector2(offset.x, offset.y - 1)))))

    return Vector2(nx, ny)


def gaussian(mu, inverse_scale):
    # return a random integer from a gaussian distribution with mean mu and standard deviation mu / inverse_scale
    return int(gauss(mu, round(mu / inverse_scale)))


def clamp(n, minimum, maximum):
    # clamp any number n between minimum and maximum values
    return max(minimum, min(n, maximum))


def linear_conversion(old_value, old_range, new_range):
    # convert a number from a range to a number in a new range, maintaining the relative position of the number
    return (((old_value - old_range[0]) * (new_range[1] - new_range[0])) / (old_range[1] - old_range[0])) + new_range[0]


def load_sprites(sprite_paths, scale):
    for name, path in sprite_paths.items():
        if type(path) is str:
            sprite_paths[name] = pygame.image.load(path).convert_alpha()
        sprite_paths[name] = pygame.transform.scale(sprite_paths[name],
                                                    [int(x * scale) for x in sprite_paths[name].get_size()])
    return sprite_paths


class StaticSprite(pygame.sprite.Sprite):
    """
    Basic sprite class for static objects

    Adds automatic image loading from files
    """

    def __init__(self, x, y, sprite_paths=None, scale=1.0):
        super(StaticSprite, self).__init__()

        if sprite_paths:
            self.sprites = load_sprites(sprite_paths, scale)
            self.sprites["no_rotation"] = self.sprites["base"]
            self.image = self.sprites["base"]
            self.rect = pygame.Rect((x, y), self.image.get_size())
            self.mask = pygame.mask.from_surface(self.image)
        else:
            self.rect = pygame.Rect((x, y), (8, 8))

    def check_collisions(self, offset, index, obstacles):
        """
        This function checks if a collision would occur after moving offset
        pixels.  If a collision is detected position is decremented by one
        pixel and retested. This continues until we find exactly how far we can
        safely move, or we decide we can't move.
        """
        unaltered = True
        self.rect.move_ip(offset)
        collisions = pygame.sprite.spritecollide(self, obstacles, False)
        if self in collisions:
            collisions.remove(self)

        current_collision = pygame.sprite.spritecollideany(self, collisions, pygame.sprite.collide_mask)
        while current_collision:
            self.rect[index] += (1 if offset[index] < 0 else -1)

            unaltered = False
            current_collision = pygame.sprite.spritecollideany(self, collisions, pygame.sprite.collide_mask)
        return unaltered

    def get_hit_box(self):
        return self.rect


class DynamicSprite(StaticSprite):
    """
    Basic sprite class meant to move

    Adds movement with collision checking and rotation
    """

    def __init__(self, x, y, sprite_paths=None, scale=1.0, angle=0.0):
        super(DynamicSprite, self).__init__(x, y, sprite_paths, scale)

        self.angle = angle
        self.speed = 1
        self.x_speed_buffer = 0
        self.y_speed_buffer = 0

    def rotate(self, angle):
        center = self.rect.center  # save old center

        self.image = pygame.transform.rotate(self.sprites["no_rotation"], angle)  # rotate image

        self.rect = self.image.get_rect()  # set rect to new image's dimensions
        self.rect.center = center  # reset center, keep image from moving

        self.angle = angle % 360  # update angle
        self.mask = pygame.mask.from_surface(self.image)  # update mask

    def move(self, dx, dy, colliders):
        if dx != 0:
            self.check_collisions((dx, 0), 0, colliders)
        if dy != 0:
            self.check_collisions((0, dy), 1, colliders)

    def off_surface(self, surface):
        if self.rect.right < 0 or \
                self.rect.left > surface.get_rect().width or \
                self.rect.bottom < 0 or \
                self.rect.top > surface.get_rect().height:
            return True
        return False


class LivingSprite(DynamicSprite):
    """
    Basic sprite class meant for living objects

    Adds health, damage, particles, and death
    """

    def __init__(self, x, y, sprite_paths=None, scale=1.0, angle=0.0, run_particles=True):
        super(LivingSprite, self).__init__(x, y, sprite_paths, scale, angle)

        self.health = 1
        self.hurt_bool = False
        self.blood = 50
        self.hurt_blood = round(self.blood / 4)
        self.base_hurt_time = 20
        self.hurt_time = self.base_hurt_time
        self.projectiles = pygame.sprite.Group()

        self.run_particles = run_particles

        if self.run_particles:
            self.particles = pygame.sprite.Group()

            self.particle_rgb = (200, 25, 25)
            self.particle_duration = 50
            self.particle_variation = 4

    def damage(self, value, *groups, **kwargs):
        self.health -= value
        self.hurt_bool = True

        try:
            self.sprites["no_rotation"] = self.sprites["hurt"]
            self.rotate(self.angle)
        except KeyError:
            pass

        if self.health <= 0:
            self.remove(*groups)

            if self.run_particles:
                num_particles = gaussian(self.blood, 4)
        elif self.run_particles:
            num_particles = gaussian(self.hurt_blood, 4)

        if self.run_particles:
            self.particles.add(
                *[Particle(self.rect.centerx, self.rect.centery, self.particle_rgb, self.particle_duration,
                           self.particle_variation) for _ in range(num_particles)])

    def update(self, colliders, surface, cam):
        if self.hurt_bool and self.hurt_time > 0:
            self.hurt_time -= 1
        elif self.hurt_bool:
            self.sprites["no_rotation"] = self.sprites["base"]
            self.rotate(self.angle)
            self.hurt_bool = False
            self.hurt_time = self.base_hurt_time

        if self.run_particles:
            self.particles.update(colliders, surface, cam)
            if self.health <= 0 and len(self.particles) == 0:
                self.kill()
        elif self.health <= 0:
            self.kill()


class Particle(DynamicSprite):
    """
    Basic particle class with automatic random motion, built in timer with random distribution, and colour variation
    """

    def __init__(self, x, y, rgb, duration, seed):
        super(Particle, self).__init__(x, y)

        self.rgb = (clamp(gaussian(rgb[0], seed), 0, 255),
                    clamp(gaussian(rgb[1], seed), 0, 255),
                    clamp(gaussian(rgb[2], seed), 0, 255))
        self.duration = gaussian(duration, seed)
        self.move_gen = self.move_random(seed)

    @staticmethod
    def move_random(mag):
        for _ in range(randint(-mag, mag)):
            x = randint(-mag, mag)
            y = randint(-mag, mag)
            yield (x, y)

    def update(self, colliders, surface, cam):
        if self.duration > 0:
            try:
                self.move(*next(self.move_gen), colliders)
            except StopIteration:
                pass
            finally:
                pygame.draw.rect(surface, self.rgb, cam.apply(self))
            self.duration -= 1
        else:
            self.kill()


class Player(LivingSprite):
    """
    Basic player class

    Should be extended to suit the particular genre of game
    """

    def __init__(self, x, y, sprites, scale=1.0):
        super(Player, self).__init__(x, y, sprites, scale)

    @staticmethod
    def shake_screen():
        s = -1
        for _ in range(0, 3):
            for x in range(0, 2):
                yield (x * s, x * s)
            for x in range(2, 0):
                yield (x * s, x * s)
            s *= -1

    def rotate_to_target(self, target):
        # get vector between player and target
        vector = (self.rect.x - target[0], self.rect.y - target[1])

        # calculate angle between player and target
        try:
            theta = -math.degrees(math.atan2(vector[1], vector[0])) + 90
        except ZeroDivisionError:
            theta = 0

        self.rotate(theta)


class Enemy(LivingSprite):
    """
    Placeholder enemy class

    Should be extended to suit the particular genre of game
    """

    def __init__(self, x, y, sprites):
        super(Enemy, self).__init__(x, y, sprites)
