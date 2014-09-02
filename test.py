from __future__ import division

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *

from PIL import Image

from rainbowalga.core import Position
from rainbowalga.hardware import (Detector, DetectorLine, DOM) 
from rainbowalga.tools import (CoordinateSystem, Camera, Clock)

clock = Clock()
camera = Camera(distance=10)
camera.is_rotating = True
coordinate_system = CoordinateSystem()
detector = Detector()
logo = Image.open('km3net_logo.bmp')

# Create a raw string from the image data - data will be unsigned bytes
# RGBpad, no stride (0), and first line is top of image (-1)
logo_bytes = logo.tobytes("raw", "RGB", 0, -1)

detector_lines = []
for x in range(20):
    for z in range(20):
        detector_line = DetectorLine(x-10, 0, z-10, 5)
        detector_lines.append(detector_line)


doms = []
n = 3
for x in range(n):
    for y in range(n):
        for z in range(n):
            dom = DOM(pos=Position(x - n/2, y - n/2, z - n/2))
            doms.append(dom)


def resize(width, height):
    if height == 0:
        height = 1

    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, float(width)/float(height), 0.1, 10000.0)
    glMatrixMode(GL_MODELVIEW)



def draw():
    clock.record_frame_time()
    if not clock.snoozed:
        glutSetWindowTitle("FPS: {0:.1f}".format(clock.fps));
        clock.snooze()

    # 3D stuff
    glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)

    camera.rotate_z(0.5)
    camera.look()

    coordinate_system.draw()

    detector.draw_lines()
    detector.draw_doms()

    #for detector_line in detector_lines:
    #    detector_line.draw(1)
    for dom in doms:
        dom.draw()


    # 2D stuff
    menubar_height = logo.size[1] 
    width = glutGet(GLUT_WINDOW_WIDTH)
    height = glutGet(GLUT_WINDOW_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0.0, width, height, 0.0, -1.0, 10.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glDisable(GL_CULL_FACE)

    glClear(GL_DEPTH_BUFFER_BIT)

    glBegin(GL_QUADS)
    glColor3f(0.14, 0.49, 0.87)
    glVertex2f(0, 0)
    glVertex2f(width-logo.size[0], 0)
    glVertex2f(width-logo.size[0], menubar_height)
    glVertex2f(0, menubar_height)
    glEnd()

    glPushMatrix()
    glLoadIdentity()
    glRasterPos(width-logo.size[0], logo.size[1])
    glDrawPixels(logo.size[0], logo.size[1], GL_RGB, GL_UNSIGNED_BYTE, logo_bytes)
    glPopMatrix()

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


    glutSwapBuffers()

def drag(x, y):
    print("Moving: {0} {1}".format(x, y))

def process_keyboard(key,  x,  y):
    if(key == chr(27)):
        raise SystemExit


def process_special_keys(key, x, z):
    if key == GLUT_KEY_LEFT:
        print("rotating left")
        camera.rotate(0.1)

def mouse(button, state, x, y):
    print button, state, x, y
    if button == 0:
        if state == 0:
            camera.is_rotating = False
        else:
            camera.is_rotating = True
    if button == 3:
        camera.distance = camera.distance + 1
    if button == 4:
        camera.distance = camera.distance - 1


VOID, RESET, QUIT = range(3)

def reset():
    global camera
    print("Debug...")
    camera = Camera()



def doquit():
    raise SystemExit

menudict ={RESET : reset,  
           QUIT : doquit}

def dmenu(item):
    menudict[item]()
    return 0

if __name__ == "__main__":
    width = 800
    height = 600

    glutInit()

    #print 'Vendor: %s' % (glGetString(GL_VENDOR))
    #print 'Opengl version: %s' % (glGetString(GL_VERSION))
    #print 'GLSL Version: %s' % (glGetString(GL_SHADING_LANGUAGE_VERSION))
    #print 'Renderer: %s' % (glGetString(GL_RENDERER))

    glutInitWindowPosition(112, 84)
    glutInitWindowSize(width, height)
    # use multisampling if available 
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH | GLUT_MULTISAMPLE)
    wintitle = "RainbowAlga"
    glutCreateWindow(wintitle)
    glutDisplayFunc(draw)
    glutIdleFunc(draw)
    glutReshapeFunc(resize)
    glutKeyboardFunc(process_keyboard)
    glutSpecialFunc(process_special_keys)
    glutMouseFunc(mouse)
    glutMotionFunc(drag)
    
    glutCreateMenu(dmenu)
    glutAddMenuEntry("Debug", RESET)
    glutAddMenuEntry("Quit", QUIT)
    glutAttachMenu(GLUT_RIGHT_BUTTON)

    # setup OpenGL state 
    glClearDepth(1.0)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glFrustum(-1.0, 1.0, -1.0, 1.0, 1.0, 3000)

    #glMatrixMode(GL_MODELVIEW)


    light_ambient = (0.0, 0.0, 0.0, 1.0)
    light_diffuse = (1.0, 1.0, 1.0, 1.0)
    light_specular = (1.0, 1.0, 1.0, 1.0)
    light_position = (-100.0, 100.0, 100.0, 0.0)

    mat_ambient = (0.7, 0.7, 0.7, 1.0)
    mat_diffuse = (0.8, 0.8, 0.8, 1.0)
    mat_specular = (1.0, 1.0, 1.0, 1.0)
    high_shininess = (100)

    glEnable(GL_LIGHT0)
    glEnable(GL_NORMALIZE)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_LIGHTING)
    
    glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    glLightfv(GL_LIGHT0, GL_SPECULAR,  light_specular)
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)

    glMaterialfv(GL_FRONT, GL_AMBIENT,   mat_ambient)
    glMaterialfv(GL_FRONT, GL_DIFFUSE,   mat_diffuse)
    glMaterialfv(GL_FRONT, GL_SPECULAR,  mat_specular)
    glMaterialfv(GL_FRONT, GL_SHININESS, high_shininess)

    # start event processing */
    print 'RIGHT-CLICK to display the menu.'
    glutMainLoop()

