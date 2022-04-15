from pygame import Surface
import math
import pygame
from pygame.constants import KEYDOWN, K_ESCAPE, VIDEORESIZE
from pygame.event import Event
from pygamestate import Game, GameState
from random import random, uniform
import colorsys
from functools import cache
from clampAspect import AspectClamper

def removeWhile(pred, l: list):
    while l and pred(l[0]):
        l.pop(0)

def draw_circle_alpha(surface, color, center, radius):
    target_rect = pygame.Rect(center, (0, 0)).inflate((radius * 2, radius * 2))
    shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    pygame.draw.circle(shape_surf, color, (radius, radius), radius)
    surface.blit(shape_surf, target_rect)
def hsv2rgb(h,s,v):
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))

class Particle:
    ax = 0
    ay = 500
    life = 1

    def __init__(self, x: float, y: float, vx: float, vy: float, size: float) -> None:
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.size = size
    
    def update(self, dt):
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
    
    def colorMap(self):
        v = self.life / Particle.life
        return (*hsv2rgb(3/6 + (1-v) / 3, 1, 1), 200 * self.life / Particle.life)

    
    def draw(self, surface):
        draw_circle_alpha(surface, self.colorMap(), (self.x, self.y), self.size)
    
class Source:
    def __init__(self, x: float, y: float) -> None:
        self.x, self.y = x, y

class ParticleSystem:
    emissionInterval = 0.01
    time = 0

    def __init__(self) -> None:
        self.particles: list[Particle] = []
        self.sources: list[Source] = []

    def emit(self):
        for source in self.sources:
            self.particles.append(Particle(source.x, source.y, uniform(-1, 1)*60, -600 - 20*uniform(-1, 1), uniform(2, 5)))

    def update(self, dt):
        self.time += dt
        while self.time > self.emissionInterval:
            self.time -= self.emissionInterval
            self.emit()
        newParticles = []
        for particle in self.particles:
            particle.update(dt)
            if particle.life >= 0:
                newParticles.append(particle)
        self.particles = newParticles

    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)

class MainState(GameState):
    timeScale = 200
    firstNote = 36
    time = 0

    def __init__(self, game: Game, notes: int) -> None:
        self.octaveAspectClamper = AspectClamper(1.2, 1.6)
        self.game = game
        self.noteCount = notes
        self.history: list[tuple[int, float, float]] = []
        self.pressedKeys: dict[int, float] = dict()
        self.particles = ParticleSystem()
        self.reshape(self.game.width, self.game.height)

    @property
    def middleNote(self):
        return self.firstNote + self.noteCount // 2

    # @cache
    def getNoteX(self, pitch):
        if pitch < self.middleNote:
            return self.getNoteX(pitch + 1) - (self.getNoteWidth(pitch + 1) + self.getNoteWidth(pitch)) / 2
        if pitch > self.middleNote:
            return self.getNoteX(pitch - 1) + (self.getNoteWidth(pitch - 1) + self.getNoteWidth(pitch)) / 2
        return self.game.width / 2
    def isNoteBlack(self, pitch):
        return (0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0)[pitch % 12]
    def getNoteWidth(self, pitch):
        return ((12 - 0.7*5) / 7, 0.7)[self.isNoteBlack(pitch)] * self.octaveWidth / 12

    def update(self, dt: float, events: list[Event]):
        self.time += dt
        self.particles.update(dt)
        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.game.popState()
            elif event.type == VIDEORESIZE:
                self.reshape(*event.dict['size'])
        self.particles.sources = [Source(self.getNoteX(pitch) + uniform(-0.5, 0.5) * self.getNoteWidth(pitch), self.historyHeight) for pitch in self.pressedKeys.keys()]
        

        isOut = lambda pitch, start, end: self.getTimeY(end) < 0
        removeWhile(lambda v:isOut(*v), self.history)
    
    def getTimeY(self, time: float):
        return self.historyHeight - (-time + self.time) * self.timeScale

    def drawNote(self, surface: Surface, pitch: int, timePressed: float, timeReleased: float):
        width = self.getNoteWidth(pitch)
        rect = (self.getNoteX(pitch) - width / 2, self.getTimeY(timePressed), width, (timeReleased - timePressed) * self.timeScale)
        pygame.draw.rect(surface, (0, 100, 255) if self.isNoteBlack(pitch) else (0, 150, 255), rect)
        pygame.draw.rect(surface, (0, 50, 150) if self.isNoteBlack(pitch) else (0, 75, 255), rect, 4)

    @property
    def historyHeight(self):
        return self.game.height - self.pianoHeight

    def reshape(self, width, height):
        # self.getNoteX.cache_clear()
        self.game.width, self.game.height = width, height
        self.octaveWidth, self.pianoHeight = self.octaveAspectClamper.clamp(width / (self.noteCount / 12), height * .1)
        

    def drawOctave(self, surface, x, pressed):
        y = self.historyHeight
        for n in range(7):
            color = (100, 100, 100) if pressed[(0, 2, 4, 5, 7, 9, 11)[n]] else (200, 200, 200)
            pygame.draw.rect(surface, color, (x + (n / 7) * self.octaveWidth, y, self.octaveWidth / 7 - 1, self.pianoHeight))
        for n in (1, 2, 4, 5, 6):
            width = 0.5
            color = (50, 50, 50) if pressed[(-1, 1, 3, -1, 6, 8, 10)[n]] else (0, 0, 0)
            pygame.draw.rect(surface, color, (x + ((n - width / 2) / 7) * self.octaveWidth, y, width * self.octaveWidth / 7, self.pianoHeight * 0.7))

    def draw(self, surface: Surface):
        divider = 2

        # Draw time dividers
        for t in range(int(self.historyHeight) // (self.timeScale // divider) + 1):
            p = self.historyHeight - (t + ((self.time * divider) % 1)) * (self.timeScale / divider)
            pygame.draw.line(surface, (50, 50, 50), (0, p), (self.game.width, p))

        octavesLeft = math.ceil(self.getNoteX(self.firstNote) / int(self.octaveWidth))
        octavesRight = math.ceil(self.getNoteX(self.firstNote + self.noteCount) / int(self.octaveWidth))
        # print(octavesLeft, octavesRight)

        # Draw note dividers
        for o in range(-octavesLeft, octavesRight):
            for t in (0, 5):
                p = t + 12*o
                x = self.getNoteX(p + self.firstNote) - self.getNoteWidth(p + self.firstNote) / 2
                pygame.draw.line(surface, (50, 50, 50), (x, 0), (x, self.historyHeight), 2)

        # Draw notes
        for (pitch, start, end) in self.history:
            self.drawNote(surface, pitch, start, end)
        for (pitch, start) in self.pressedKeys.items():
            self.drawNote(surface, pitch, start, self.time)
        

        # Draw piano
        for o in range(-octavesLeft, octavesRight):
            self.drawOctave(surface, self.getNoteX(self.firstNote) - self.getNoteWidth(self.firstNote) / 2 + o * self.octaveWidth, [(n + o * 12 + self.firstNote) in self.pressedKeys.keys() for n in range(12)])


        self.particles.draw(surface)

    def keyPressed(self, pitch):
        self.pressedKeys[pitch] = self.time
        
    def keyReleased(self, pitch):
        if pitch not in self.pressedKeys:return
        self.history.append((pitch, self.pressedKeys[pitch], self.time))
        del self.pressedKeys[pitch]
        


class Window:
    def __init__(self) -> None:
        game = Game(1000, 600)
        self.state = MainState(game, 49)
        game.pushState(self.state)
        self.game = game
    
    def run(self):
        self.game.run(144)

    def keyPressed(self, pitch):
        self.state.keyPressed(pitch)

    def keyReleased(self, pitch):
        self.state.keyReleased(pitch)