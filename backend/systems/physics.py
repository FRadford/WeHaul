import pygame

import pygame.math


class PhysicsMixin(object):
    """
    A simplified physics class. Using a 'real' gravity function here, though
    it is questionable whether or not it is worth the effort. Compare to the
    effect of gravity in fall_rect and decide for yourself.
    """
    def __init__(self, *args, **kwargs):
        """You can experiment with different gravity here."""
        super(PhysicsMixin, self).__init__(*args, *kwargs)
        self.x_vel = self.y_vel = self.y_vel_i = 0
        self.grav = 10
        self.fall = False
        self.time = None

    def physics_update(self):
        """If the player is falling, calculate current y velocity."""
        if self.fall:
            time_now = pygame.time.get_ticks()
            if not self.time:
                self.time = time_now
            self.y_vel = self.grav*((time_now-self.time)/1000.0)+self.y_vel_i
        else:
            self.time = None
            self.y_vel = self.y_vel_i = 0

    def check_falling(self, obstacles):
        """If player is not contacting the ground, enter fall state."""
        self.rect.move_ip((0, 1))
        collisions = pygame.sprite.spritecollide(self, obstacles, False)
        if self in collisions:
            collisions.remove(self)
        if not pygame.sprite.spritecollideany(self, collisions, pygame.sprite.collide_mask):
            self.fall = True
        self.rect.move_ip((0, -1))
