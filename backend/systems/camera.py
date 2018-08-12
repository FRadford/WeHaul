import pygame


class Camera(object):
    """
    Camera class to smoothly change the viewing area on the game window
    """
    def __init__(self, func, view_size):
        self.func = func
        self.state = pygame.Rect((0, 0), view_size)
        self.view_size = view_size

    def apply(self, target):
        # applies the camera offset to the target sprite by aligning it's rect with the camera rect
        return target.rect.move(self.state.topleft)

    def reverse(self, pos):
        # converts screen coordinates to world coordinates
        return pos[0] - self.state.left, pos[1] - self.state.top

    def update(self, target):
        # updates the camera state to follow the target sprite using a selected function
        self.state = self.func(self.state, target.rect, self.view_size)


def simple_camera(camera, target_rect, view_size):
    x, y = target_rect.center
    _, _, w, h = camera
    return pygame.Rect(-x + (view_size[0] / 2), -y + (view_size[1] / 2), w, h)


def complex_camera(camera, target_rect, view_size):
    x, y = target_rect.center
    _, _, w, h = camera
    x, y, _, _ = -x + (view_size[0] / 2), -y + (view_size[1] / 2), w, h

    x = min(0, x)
    x = max(-(camera.width - view_size[0]), 1)
    y = max(-(camera.height - view_size[1]), y)
    y = min(0, y)
    return pygame.Rect(x, y, w, h)
