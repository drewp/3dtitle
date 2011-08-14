#!/usr/bin/python
"""
users of ubuntu 11.04 may need to follow
https://bugs.launchpad.net/ubuntu/+source/pyglet/+bug/786516 and get a
newer pyglet release
"""
from __future__ import division
import pyglet, numpy as N, tempfile, os, subprocess, shutil

W,H = 640, 480
FPS = 30
window = pyglet.window.Window(width=W, height=H)
clock_display = pyglet.clock.ClockDisplay()

class Particles(object):
    def setup(self):
        img = self.makeTextImage()
        self.pos = N.asfarray(self.findPoints(img))
        self.pos = N.concatenate([self.pos,
                                  N.zeros((self.pos.shape[0], 1))], axis=1)
        # pos = [[x0,y0,z0],
        #        [x1,y1,z0],
        #        ...

        self.pos = N.repeat(self.pos, 1, axis=0)
        npts = self.pos.shape[0]
        print "%d particles" % npts
        
        self.vel = N.zeros((npts, 3))
        # vel = [[dx0,dy0,dz0], # pixels/sec
        #        [dx1,dy1,dz1],
        #        ...

        self.pt_start_time = 1 + self.pos[:,0] / W * 6
        self.pt_start_time += N.random.randn(self.pt_start_time.shape[0]) * .1
        
        self.escape_vel = N.random.randn(npts, 3) * 5
        self.escaped_pts = N.array([False])
        self.escaped_pts.resize(npts)

        for axis in [0,1,2]:
            self.escape_vel[:,axis] = N.convolve(self.escape_vel[:,axis],
                                                 N.hamming(50))[:npts]

        self.elapsed = 0

    def loadFont(self, filename, font_name):
        pyglet.font.add_file(filename)
        pyglet.font.load(font_name)

    def makeTextImage(self):
        self.loadFont("/usr/share/fonts/truetype/msttcorefonts/georgia.ttf",
                      "Georgia")
        text = pyglet.text.HTMLLabel('''
            <p align="center">
              <font color="#ffffff" face="Georgia" size="+3">Example<br>Title</font>
            </p>
            <p align="center">
              <font color="#ffffff" face="Georgia">With a subtitle</font>
            </p>''',
            multiline=True, dpi=int(H * .6),
            width=W, y=H/2, anchor_y='center')
        text.draw()
        b = pyglet.image.get_buffer_manager().get_color_buffer()
        return b.get_image_data()

    def findPoints(self, img):
        # (profile shows width*height calls to re.filter inside _convert!)
        data = N.fromstring(img.get_data("I", img.width), dtype=N.uint8)
        data.shape = (img.height, img.width)
        coords = N.fliplr(N.transpose(N.nonzero(data > 128)))
        return coords
        
    def update(self, dt):
        prevTime = self.elapsed
        self.elapsed += dt
        new_escape_pts = ((prevTime <= self.pt_start_time) &
                          (self.pt_start_time < self.elapsed))
        self.escaped_pts |= new_escape_pts
        new_escape_mask = N.column_stack(
            (new_escape_pts, new_escape_pts, new_escape_pts))
        N.putmask(self.vel, new_escape_mask, self.escape_vel)

        self.pos += self.vel * dt
        self.vel[:,1] += self.escaped_pts * -2

    def draw(self, showFps=True):
        zscl = .1
        projected = self.pos[:, :2].copy()
        projected[:, 0] = (projected[:, 0] + self.pos[:, 2] * zscl) / 2
        right = self.pos[:, :2].copy()
        right[:, 0] = (right[:, 0] - self.pos[:, 2] * zscl) / 2 + W / 2
        projected = N.concatenate([projected, right])
        pyglet.graphics.draw(projected.shape[0], pyglet.gl.GL_POINTS,
                             ('v2f', projected.reshape((-1,))))
        if showFps:
            clock_display.draw()

def outputFinal(duration=10):
    outDir = tempfile.mkdtemp(prefix="make3dtitle_out")
    try:
        for frame in range(FPS * duration):
            window.clear()
            particles.update(1 / FPS)
            particles.draw(showFps=False)
            out = os.path.join(outDir, "frame.%03d.png" % frame)
            pyglet.image.get_buffer_manager().get_color_buffer().save(out)
            print "wrote", out
            window.flip()

        subprocess.check_call(['ffmpeg',
                               '-f', 'image2',
                               '-i', os.path.join(outDir, 'frame.%03d.png'),
                               '-r', str(FPS),
                               '-vcodec', 'mpeg4',
                               '-qscale', '10',
                               '-y', 'title.mp4'])
    finally:
        shutil.rmtree(outDir)
    pyglet.app.exit()

particles = Particles()

@window.event
def on_show():
    window.clear()
    particles.setup()
    #outputFinal() # enable this to switch from live preview to final movie

@window.event
def on_draw():
    window.clear()
    particles.draw()

pyglet.clock.schedule_interval(particles.update, 1/FPS)
pyglet.app.run()
