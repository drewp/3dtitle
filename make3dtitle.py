#!/usr/bin/python

"""
users of ubuntu 11.04 may need to follow
https://bugs.launchpad.net/ubuntu/+source/pyglet/+bug/786516 and get a
newer pyglet release

"""
from __future__ import division
import pyglet, numpy as N

window = pyglet.window.Window(width=640, height=480)
pyglet.font.add_file("/usr/share/fonts/truetype/msttcorefonts/georgia.ttf")
font_name = "Georgia"
font = pyglet.font.load(font_name)
clock_display = pyglet.clock.ClockDisplay()

class Particles(object):
    def setup(self):
        self.elapsed = 0

        img = self.makeTextImage()
        self.pos = N.asfarray(self.findPoints(img))
        # pos = [[x0,y0,z0],
        #        [x1,y1,z0],
        #        ...

        self.pos = N.repeat(self.pos, 2, axis=0)
        
        self.vel = N.zeros((self.pos.shape[0], 2))
        # vel = [[dx0,dy0,dz0], # pixels/sec
        #        [dx1,dy1,dz1],
        #        ...

        self.escapeTime = 2 + self.pos[:,0] / window.width * 8
        #self.escapeTime += N.random.randn(self.escapeTime.shape[0]) * .1
        
        self.escapeVel = N.random.randn(self.pos.shape[0], 2) * 10
        self.escaped_pts = N.array([False])
        self.escaped_pts.resize(self.pos.shape[0])

        self.escapeVel[:,0] = N.convolve(self.escapeVel[:,0], N.hamming(50))[:self.escapeVel.shape[0]]
        self.escapeVel[:,1] = N.convolve(self.escapeVel[:,1], N.hamming(50))[:self.escapeVel.shape[0]]

    def makeTextImage(self):
        text = pyglet.text.HTMLLabel('''
        <p align="center">
        <font color="#ffffff" size="+3">Example<br>Title</font>
        </p>
        <p align="center">
        <font color="#ffffff">With a subtitle</font>
        </p>

        ''',
                                 
                                     multiline=True,
                                     dpi=int(window.height * .6),
                                     width=window.width,
                                     y=window.height/2, 
                                     anchor_y='center')
        text.draw()
        b = pyglet.image.get_buffer_manager().get_color_buffer()
        return b.get_image_data()


    def findPoints(self, img):
        data = N.fromstring(img.get_data("I", img.width), dtype=N.uint8)
        data.shape = (img.height, img.width)
        coords = N.fliplr(N.transpose(N.nonzero(data > 128)))
        return coords
        
    def update(self, dt):
        prevTime = self.elapsed
        self.elapsed += dt
        new_escape_pts = ((prevTime <= self.escapeTime) &
                          (self.escapeTime < self.elapsed))
        self.escaped_pts |= new_escape_pts
        new_escape_mask = N.column_stack((new_escape_pts, new_escape_pts))
        N.putmask(self.vel, new_escape_mask, self.escapeVel)

        self.pos += self.vel * dt
        self.vel[:,1] += self.escaped_pts * -2

    def draw(self):
        pyglet.graphics.draw(self.pos.shape[0], pyglet.gl.GL_POINTS,
                             ('v2f', self.pos.reshape((-1,))))

        clock_display.draw()

particles = Particles()
@window.event
def on_show():
    window.clear()
    particles.setup()

@window.event
def on_draw():
    window.clear()
    particles.draw()

pyglet.clock.schedule_interval(particles.update, 1/30)
pyglet.app.run()
