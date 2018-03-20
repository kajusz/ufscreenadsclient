#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

import pyglet
#import comms
#comms.server(comms.address)

class  pygletScreenConsumer():
    def __init__(self, contentProvider, params):
        self.contentProvider = contentProvider
        self.params = params

        # Init pyglet
        screens = pyglet.canvas.get_display().get_screens()
        self.window = pyglet.window.Window(resizable=True)#, fullscreen=self.params['fullscreen'], screen=screens[self.params['screen']])
        self.window.set_caption(self.params['title'])

        if self.params['screen']:
            self.window.set_location(screens[self.params['screen']].x + 40, screens[self.params['screen']].y + 40)

        if self.params['fullscreen']:
            pyglet.clock.schedule_once(self.toggleFullscreen, 5)
            #self.window.set_fullscreen(fullscreen=self.params['fullscreen'], screen=screens[self.params['screen']])

        # Init events
        self.on_draw = self.window.event(self.on_draw)
        self.on_key_press = self.window.event(self.on_key_press)
        self.on_draw = self.window.event(self.on_resize)

        # Setup canvas
        self.spriteGroup = pygletSpriteOrderedGroup()
        self.nextImage = 0
        self.paused = self.params['paused']
        self.imageRefreshTime = self.params['durDefault']

        if self.params['splash']:
            img = pyglet.image.load(self.params['splashImg'])
            sprite = self.spriteGroup.getVisible()
            sprite.img(img)
            sprite.resize(img.width, img.height)
            sprite.pos((self.window.width - img.width)/2, (self.window.height - img.height)/2)
            self.imageRefreshTime = 2
        else:
            newImage = self.getImageDetails(self.nextImage)
            self.imageRefreshTime = newImage['duration']
            sprite = self.spriteGroup.getVisible()
            sprite.img(pyglet.image.load(newImage['path']))
            sprite.resize(self.window.width, self.window.height)
            self.nextImage += 1

        self.fadeLoopsToDo = self.params['fps'] * self.params['fadeTime']
        self.fadeLoopCount = 0

        # Debug fps display
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            self.fps_display = pyglet.clock.ClockDisplay()

        # Image refresh
        pyglet.clock.schedule_once(self.updateImage, self.imageRefreshTime)
        # Content refresh
        pyglet.clock.schedule_interval(self.contentProvider.refresh, 60)
        # Comms
#        pyglet.clock.schedule_interval(self.commsCheck, 0.2)

        # State
        self.state_fullscreen = self.window.fullscreen
        self.state_screen = self.window.screen

        # Let it rip!
        pyglet.app.run()

    def on_draw(self):
        self.window.clear()
        self.spriteGroup.draw()
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            self.fps_display.draw()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.L or symbol == pyglet.window.key.RIGHT:      # Next
            self.skipImage()
            logger.info('Next')
        elif symbol == pyglet.window.key.J or symbol == pyglet.window.key.LEFT:     # Prev
            self.skipImage(nextImg=False)
            logger.info('Prev')
        elif symbol == pyglet.window.key.K or symbol == pyglet.window.key.SPACE:    # Pause/Resume
            self.togglePlay()
        elif symbol == pyglet.window.key.F:                                         # Full Screen
            self.toggleFullscreen()
        else:
            pass

    def on_resize(self, width, height):
        if width == 0 or height == 0: return
        self.spriteGroup.getVisible().resize(width, height)
        self.spriteGroup.getHidden().resize(width, height)

#    def commsCheck(self, dt):
#        msg = comms.recv()
#        if msg == None:
#            return
#
#        print(msg)
#        print(type(msg))
#
#        if msg == b'test':
#            print('YAY')
#        elif msg == b'toggle-fullscreen':
#            self.toggleFullscreen()
#        elif msg == b'toggle-play':
#            self.togglePlay()
#        elif msg == b'toggle-visibility':
#            self.toggleVisibility()
#
#        elif msg == b'next':
#            self.skipImage()
#        elif msg == b'prev':
#            self.skipImage(nextImg=False)
#        elif msg == b'refresh':
#            self.contentProvider.refresh()
#        elif msg.startswith(b'get'):
#            print('get?')
#        elif msg.startswith(b'target'):
#            print('target?')
#        elif msg.startswith(b'disable'):
#            print('disable?')
#        elif msg.startswith(b'enable'):
#            print('enable?')

    def toggleFullscreen(self, dt=None):
        self.state_fullscreen = self.window.fullscreen
        self.state_screen = self.window.screen
        print('info: state_fullscreen', self.state_fullscreen)
        print('info: state_screen', self.state_screen)

        if self.state_fullscreen:
            self.window.set_fullscreen(fullscreen=False, screen=self.state_screen)
            logger.info('Windowed')
        else:
            self.window.set_fullscreen(fullscreen=True, screen=self.state_screen)
            logger.info('Fullscreen')

    def togglePlay(self, dt=None):
        if self.paused:
            self.play()
        else:
            self.pause()

    def pause(self):
        if not self.paused:
            pyglet.clock.unschedule(self.updateImage)
            self.paused = True
            logger.info('Paused')

    def play(self):
        if self.paused:
            pyglet.clock.schedule_once(self.updateImage, self.imageRefreshTime)
            self.paused = False
            logger.info('Resumed')

    def toggleVisibility(self, dt=None):
        self.state_fullscreen = self.window.fullscreen
        self.state_screen = self.window.screen
        print(self.state_fullscreen)
        print(self.state_screen)

        if self.window.visible:
            self.window.set_visible(visible=False)
            logger.info('Hidden')
        else:
            self.window.set_visible(visible=True)
            self.window.set_fullscreen(fullscreen=self.state_fullscreen, screen=self.state_screen)
            logger.info('Visible')

    def skipImage(self, nextImg=True):
        pyglet.clock.unschedule(self.updateImage)
        pyglet.clock.unschedule(self.xfadeTick)

        if self.fadeLoopCount > 0:
            self.fadeLoopCount = 0
            if nextImg:
                self.spriteGroup.getVisible().alpha(255)
                self.spriteGroup.getHidden().alpha(0)
            else:
                self.spriteGroup.getVisible().alpha(0)
                self.spriteGroup.getHidden().alpha(255)
        else:
            if not nextImg:
                self.nextImage = self.nextImage - 2
            newImage = self.getImageDetails(self.nextImage)
            self.imageRefreshTime = newImage['duration']
            self.spriteGroup.update(pyglet.image.load(newImage['path']), self.window.width, self.window.height)
            self.spriteGroup.alpha(255)
            self.nextImage += 1

        if not self.paused:
            pyglet.clock.schedule_once(self.updateImage, self.imageRefreshTime)

    def updateImage(self, dt=None):
        newImage = self.getImageDetails(self.nextImage)
        self.imageRefreshTime = newImage['duration']
        self.spriteGroup.update(pyglet.image.load(newImage['path']), self.window.width, self.window.height)
        if not self.paused:
            pyglet.clock.schedule_once(self.updateImage, self.imageRefreshTime)
        self.nextImage += 1
        pyglet.clock.schedule_interval(self.xfadeTick, 1/self.params['fps'])

    def xfadeTick(self, dt):
        self.fadeLoopCount += 1
        self.spriteGroup.alpha((self.fadeLoopCount / self.fadeLoopsToDo) * 255)
        if (self.fadeLoopCount == self.fadeLoopsToDo):
            self.fadeLoopCount = 0
            pyglet.clock.unschedule(self.xfadeTick)

    def getImageDetails(self, idx=None):
        if (self.contentProvider.listDetailed(-1) == 0):
            return self.params['splashImg']

        if (idx == None or idx < -1 or idx >= self.contentProvider.listDetailed(-1)):
            idx = 0
            self.nextImage = 0
        elif idx == -1:
            idx = self.contentProvider.listDetailed(-1)
            self.nextImage = idx

        return self.contentProvider.listDetailed(idx)

class pygletSprite():
    def __init__(self):
        self.sprite = None
        self.imgHeight = 0
        self.imgWidth = 0

    def alpha(self, a):
        #logger.debug('Alpha:%d', a)
        self.sprite.opacity = a

    def draw(self):
        if (self.sprite != None):
            self.sprite.draw()

    def img(self, image, width=None, height=None):
        if (self.sprite != None):
            self.sprite.delete()
        self.sprite = pyglet.sprite.Sprite(image)
        self.imgWidth, self.imgHeight = image.width, image.height
        logger.debug('Image:%dx%d', self.imgWidth, self.imgHeight)
        if width != None and height != None:
            self.resize(width, height)

    def obj(self):
        return self.sprite

    def pos(self, x, y):
        logger.debug('Pos:%dx%d', x, y)
        self.sprite.set_position(x, y)

    def resize(self, wWidth, wHeight):
        if self.imgWidth == 0 or self.imgHeight == 0:
            return

        logger.debug('Resize:Window=%dx%d:Image=%dx%d', wWidth, wHeight, self.imgWidth, self.imgHeight)

        if ((wWidth == self.imgWidth) and (wHeight == self.imgHeight)):
            self.sprite.set_position(0, 0)
#        elif (wHeight == self.imgHeight):
#            self.sprite.set_position((wWidth - self.imgWidth)/2, 0)
#        elif (wWidth == self.imgWidth):
#            self.sprite.set_position(0, (wHeight - self.imgHeight)/2)
        else:
            if ((float(wWidth) / self.imgWidth) < (float(wHeight) / self.imgHeight)):
                scale = (float(wWidth) / self.imgWidth)
            else:
                scale = (float(wHeight) / self.imgHeight)

            if (wHeight - (self.imgHeight * scale) < 1):
                self.sprite.x, self.sprite.y = int((wWidth - (self.imgWidth * scale))/2), 0
            else:
                self.sprite.x, self.sprite.y = 0, int((wHeight - (self.imgHeight * scale))/2)
            self.sprite.scale = scale

class pygletSpriteOrderedGroup():
    def __init__(self):
        self.sprite1 = pygletSprite()
        self.sprite2 = pygletSprite()
        self.spriteZIndex = 1

    def alpha(self, f):
        if (self.spriteZIndex == 0):
            self.sprite2.alpha(f)
            self.sprite1.alpha(255 - f)
        else:
            self.sprite1.alpha(f)
            self.sprite2.alpha(255 - f)

    def draw(self):
        if (self.spriteZIndex == 0):
            self.sprite2.draw()
            self.sprite1.draw()
        else:
            self.sprite1.draw()
            self.sprite2.draw()

    def getHidden(self):
        if (self.spriteZIndex == 0):
            return self.sprite1
        else:
            return self.sprite2

    def getVisible(self):
        if (self.spriteZIndex == 1):
            return self.sprite1
        else:
            return self.sprite2

    def flip(self):
        if (self.spriteZIndex == 1):
            self.spriteZIndex = 0
        else:
            self.spriteZIndex = 1

    def update(self, img, wWidth, wHeight):
        sprite = self.getHidden()
        sprite.img(img, width=wWidth, height=wHeight)
        sprite.alpha(0)
        self.flip()
