import pygame


class SpriteSheet(object):
    """
    Class to load images from a spritesheet
    """
    def __init__(self, filename):
        try:
            # load sheet as image
            self.sheet = pygame.image.load(filename).convert_alpha()
        except pygame.error as e:
            raise SystemExit(e, "Could not load spritesheet:" + filename)

    def image_at(self, rect):
        """
        Return the image at the target location selected by a rectangle.

        :param rect: pygame.Rect
        :return: pygame.Surface
        """
        return self.sheet.subsurface(rect)

    def images_at(self, rects):
        """
        Returns a list of images selected by a supplied list of rectangles

        :param rects: tuple(pygame.Rect)
        :return: list
        """
        return [self.image_at(rect) for rect in rects]

    def load_strip(self, start_rect, image_count):
        """
        Returns a specified number of images after a defined selector as a list

        :param start_rect: pygame.Rect
        :param image_count: int
        :return: list
        """
        return self.images_at([(start_rect[0] + start_rect[2] * x, start_rect[1], start_rect[2], start_rect[3])
                               for x in range(image_count)])


class SpriteSheetAnimator(object):
    def __init__(self, filename, rect, count, loop=False, frames=1):
        self.filename = filename
        self.ss = SpriteSheet(self.filename)

        self.images = self.ss.load_strip(rect, count)
        self.loop = loop

        self.max_frames = frames
        self.cur_frame = self.max_frames

        self.i = 0

    def iter(self):
        self.i = 0
        self.cur_frame = self.max_frames
        return self

    def next(self):
        if self.i >= len(self.images):
            if not self.loop:
                raise StopIteration
            else:
                self.i = 0

        image = self.images[self.i]
        self.cur_frame -= 1

        if self.cur_frame == 0:
            self.i += 1
            self.cur_frame = self.max_frames
        return image

    def __add__(self, other):
        self.images.extend(other.images)
        return self

