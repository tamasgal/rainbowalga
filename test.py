from __future__ import division

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *

from rainbowalga.core import Position
from rainbowalga.hardware import (Detector, DetectorLine, DOM) 
from rainbowalga.tools import (CoordinateSystem, Camera)


camera = Camera(distance=10)
coordinate_system = CoordinateSystem()
detector = Detector()

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


def draw():
    glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)

    camera.rotate_y(0.5)
    camera.look()

    coordinate_system.draw()

    detector.draw_lines()
    detector.draw_doms()

    #for detector_line in detector_lines:
    #    detector_line.draw(1)
    for dom in doms:
        dom.draw()

    glutSwapBuffers()


def process_keyboard(key,  x,  y):
    if(key == chr(27)):
        raise SystemExit


def process_special_keys(key, x, z):
    if key == GLUT_KEY_LEFT:
        print("rotating left")
        camera.rotate(0.1)

def mouse(button, state, x, y):
    #print button, state, x, y
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
    global quadratic
    quadratic = gluNewQuadric()
    gluQuadricNormals(quadratic, GLU_SMOOTH)

    glutInit()

    #print 'Vendor: %s' % (glGetString(GL_VENDOR))
    #print 'Opengl version: %s' % (glGetString(GL_VERSION))
    #print 'GLSL Version: %s' % (glGetString(GL_SHADING_LANGUAGE_VERSION))
    #print 'Renderer: %s' % (glGetString(GL_RENDERER))

    glutInitWindowPosition(112, 84)
    glutInitWindowSize(800, 600)
    # use multisampling if available 
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH | GLUT_MULTISAMPLE)
    wintitle = "RainbowAlga"
    glutCreateWindow(wintitle)
    glutDisplayFunc(draw)
    glutIdleFunc(draw)
    glutKeyboardFunc(process_keyboard)
    glutSpecialFunc(process_special_keys)
    glutMouseFunc(mouse)
    
    glutCreateMenu(dmenu)
    glutAddMenuEntry("Debug", RESET)
    glutAddMenuEntry("Quit", QUIT)
    glutAttachMenu(GLUT_RIGHT_BUTTON)

    # setup OpenGL state 
    glClearDepth(1.0)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    #glViewport(0, 0, 800, 600)
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

