import pygame
from pygame.locals import *
import random
import json


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((130, 24), SRCALPHA)
        self.rect = self.image.get_rect()
        pygame.draw.rect(self.image, Color('white'), self.rect, border_radius=12)
        self.velocity = pygame.math.Vector2()
        self.speed = 6

    def update(self):
        self.rect.center += self.velocity * self.speed
        self.on_border_check()

    def on_border_check(self):
        if self.rect.left <= 0:
            self.rect.left = 0
        elif self.rect.right >= game.screen_h:
            self.rect.right = game.screen_h


class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((25, 25), SRCALPHA)
        self.rect = self.image.get_rect()
        pygame.draw.ellipse(self.image, Color('white'), self.rect)
        self.velocity = pygame.math.Vector2()

    def update(self):
        self.check_collision()
        self.on_border_check()
        self.velocity.y += game.gravity
        self.rect.center += self.velocity

    def check_collision(self):
        if pygame.sprite.spritecollide(self, game.player, False):
            if self.velocity.y > 0:
                self.velocity.y *= -(1 + game.score * 0.01)
                self.velocity.x = random.randint(3, 7) * random.choice((-1, 1))
                game.score_sound.play()
                game.score += 1

    def on_border_check(self):
        if self.rect.top >= game.screen_h:
            game.game_over()
        if self.rect.left <= 0 or self.rect.right >= game.screen_w:
            self.velocity.x *= -1
            game.pong_sound.play()
            if self.rect.bottom < 0:
                if self.rect.left <= 0:
                    guide = AudioGuide()
                    guide.rect.topleft = 4, 4
                else:
                    guide = AudioGuide(-1)
                    guide.rect.topright = game.screen_w - 4, 4
                game.audioguide.add(guide)


class TutorialKey(pygame.sprite.Sprite):
    def __init__(self, key, size=50):
        super().__init__()
        self.image = pygame.Surface((size, size), SRCALPHA)
        self.rect = self.image.get_rect()
        # Text
        font = pygame.font.Font('Font/Infinitona-Regular.otf', 36)
        text_surf = font.render(key, True, Color('gray'))
        text_rect = text_surf.get_rect(center=(size/2, size/2))
        self.image.blit(text_surf, text_rect)
        # Border
        border_rect = pygame.Rect(0, 0, size, size)
        pygame.draw.rect(self.image, Color('gray'), border_rect, 5)


class AudioGuide(pygame.sprite.Sprite):
    def __init__(self, direction=1):
        super().__init__()
        self.imgs = [pygame.image.load(f'Images/guide_{i}.png') for i in range(3)]
        if direction < 0:
            self.imgs = [pygame.transform.flip(i, True, False) for i in self.imgs]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect()
        self.counter = 0
        self.direction = direction

    def update(self):
        self.image = self.imgs[int(self.counter)]
        if self.direction > 0:
            self.rect = self.image.get_rect(topleft=self.rect.topleft)
        else:
            self.rect = self.image.get_rect(topright=self.rect.topright)
        self.counter += 0.15
        if self.counter >= 3:
            self.kill()


class Game:
    def __init__(self):
        pygame.init()

        # Data
        try:
            with open('save.txt') as data_file:
                self.data = json.load(data_file)
        except FileNotFoundError:
            self.data = {'best score': 0, 'tutorial': True}

        # Screen
        self.screen_w, self.screen_h = 640, 640
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption("Foreveralone Pong")
        pygame.display.set_icon(pygame.image.load('Images/icon.png').convert_alpha())
        pygame.mouse.set_visible(False)

        # Properties
        self.gravity = .1
        self.clock = pygame.time.Clock()
        self.events = pygame.event.get()
        self.game_state = self.main_menu
        self.font = pygame.font.Font('Font/Infinitona-Regular.otf', 50)

        # Score
        self.score = 0

        self.player = pygame.sprite.GroupSingle(Player())
        self.ball = pygame.sprite.GroupSingle(Ball())
        self.tutokeys = pygame.sprite.Group()
        self.audioguide = pygame.sprite.Group()

        # Images
        self.img_intro = pygame.image.load('Images/intro.png').convert_alpha()

        # Sounds
        self.score_sound = pygame.mixer.Sound('Sound/score.ogg')
        self.pong_sound = pygame.mixer.Sound('Sound/pong.ogg')

        self.loop = True

    def run(self):
        while self.loop:
            self.game_state()
            pygame.display.update()
            self.clock.tick(60)
        self.save()
        pygame.quit()

    def main_game(self):
        # Events Check
        self.events = pygame.event.get()
        for event in self.events:
            if event.type == KEYDOWN:
                if event.key == K_a:
                    self.player.sprite.velocity.x = -1
                    if self.data['tutorial']:
                        self.data['tutorial'] = False
                elif event.key == K_d:
                    self.player.sprite.velocity.x = 1
                    if self.data['tutorial']:
                        self.data['tutorial'] = False
            if event.type == KEYUP:
                if event.key == K_a or event.key == K_d:
                    self.player.sprite.velocity.x = 0
            if event.type == QUIT:
                self.loop = False

        # Updates
        self.audioguide.update()
        self.player.update()
        self.ball.update()

        # Draws
        self.screen.fill((63, 63, 63))
        self.draw_score('main game')
        self.audioguide.draw(self.screen)
        self.player.draw(self.screen)
        self.ball.draw(self.screen)

        # Extra
        if self.data['tutorial']:
            self.tutokeys.update()
            self.tutokeys.draw(self.screen)

    def main_menu(self):
        # Event Check
        self.events = pygame.event.get()
        for event in self.events:
            if event.type == QUIT:
                self.loop = False
            if event.type == KEYDOWN:
                self.start()

        # Draws
        self.screen.fill((63, 63, 63))
        self.draw_score('main menu')
        self.screen.blit(self.img_intro, self.img_intro.get_rect(center=(320, 320)))

    def start(self):
        player_rect = self.player.sprite.rect
        # Reset positions
        player_rect.midbottom = self.screen_w / 2, self.screen_h - 30
        self.ball.sprite.rect.midtop = self.screen_w / 2, 1 / 3 * self.screen_h
        if self.data['tutorial']:
            tutokey_left, tutokey_right = TutorialKey('a'), TutorialKey('d')
            tutokey_left.rect.midright = player_rect.left - 8, player_rect.centery
            tutokey_right.rect.midleft = player_rect.right + 8, player_rect.centery
            self.tutokeys.add(tutokey_left, tutokey_right)
        # Reset velocities
        self.player.sprite.velocity.x = 0
        self.ball.sprite.velocity.xy = 0, 0

        self.score = 0
        self.game_state = self.main_game

    def game_over(self):
        if self.score > self.data['best score']:
            self.data['best score'] = self.score
        self.game_state = self.main_menu

    def draw_score(self, game_state):
        if game_state == 'main game':
            score_surf = self.font.render(str(self.score), True, Color('gray'))
            score_rect = score_surf.get_rect(midtop=(self.screen_w/2, 10))
            self.screen.blit(score_surf, score_rect)
        else:
            score_surface = self.font.render(f'score: {self.score}', True, Color('gray'))
            best_score_surf = self.font.render(f'best score: {self.data["best score"]}', True, Color('gray'))
            score_rect = score_surface.get_rect(midtop=(self.screen_w / 2, 10))
            best_score_rect = best_score_surf.get_rect(midbottom=(self.screen_w / 2, self.screen_h - 10))
            self.screen.blit(score_surface, score_rect)
            self.screen.blit(best_score_surf, best_score_rect)

    def save(self):
        with open('save.txt', 'w') as data_file:
            json.dump(self.data, data_file)


if __name__ == '__main__':
    game = Game()
    game.run()
