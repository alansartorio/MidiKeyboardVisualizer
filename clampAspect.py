

class AspectClamper:
    def __init__(self, minAspect, maxAspect) -> None:
        self.minAspect = minAspect
        self.maxAspect = maxAspect

    def clamp(self, width, height):
        aspect = width / height
        if aspect < self.minAspect:
            return width, width / self.minAspect
        if aspect > self.maxAspect:
            return height * self.maxAspect, height
        return width, height
