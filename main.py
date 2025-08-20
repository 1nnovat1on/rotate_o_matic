import math
import sys
import pygame

# =========================
# Config
# =========================
WIDTH, HEIGHT = 1000, 700
FPS = 60

RADIUS = 2.0                 # Sphere radius in world units
CAM_DIST = 8.0               # Camera distance on +Z axis (must be > RADIUS)
FOCAL = 900.0                # Perspective focal length (pixels-ish)
LAT_LINES = 12               # wireframe density (latitude)
LON_LINES = 12               # wireframe density (longitude)
CIRCLE_RES = 64              # resolution per circle polyline

AXIS_LEN = 3.0               # length of axis lines
POINT_SIZE = 8               # screen pixels
STEP_COARSE = math.radians(6)
STEP_FINE = math.radians(1.5)

BG_COLOR = (14, 18, 24)
WIRE_COLOR = (80, 100, 140)
AXIS_X_COLOR = (220, 80, 80)
AXIS_Y_COLOR = (80, 220, 120)
AXIS_Z_COLOR = (120, 160, 255)
POINT_COLOR = (255, 230, 90)
TEXT_COLOR = (210, 220, 230)

# =========================
# Math helpers
# =========================

def sph_to_cart(theta, phi, r=1.0):
    """
    Spherical to Cartesian.
    theta: polar angle from +Z axis (0 at +Z, pi at -Z)
    phi: azimuth from +X toward +Y around +Z
    """
    st, ct = math.sin(theta), math.cos(theta)
    cp, sp = math.cos(phi), math.sin(phi)
    x = r * st * cp
    y = r * st * sp
    z = r * ct
    return x, y, z

def cart_to_sph(x, y, z):
    r = math.sqrt(x*x + y*y + z*z)
    if r == 0:
        return 0.0, 0.0, 0.0
    theta = math.acos(z / r)               # [0, pi]
    phi = math.atan2(y, x)                 # (-pi, pi]
    return theta, phi, r

def project_point(x, y, z, cx, cy):
    """
    Simple pinhole projection from camera at (0,0,CAM_DIST), looking toward origin.
    Screen center (cx, cy). Returns (sx, sy) or None if behind the camera.
    """
    denom = CAM_DIST - z
    if denom <= 1e-6:
        return None
    sx = cx + FOCAL * (x / denom)
    sy = cy - FOCAL * (y / denom)
    return (int(sx), int(sy))

def clamp_hemisphere(p, hemi):
    """
    Enforce hemisphere constraint.
    hemi is one of: None, '+X','-X','+Y','-Y','+Z','-Z'
    Returns a vector on/inside hemisphere (by rejecting illegal moves).
    Here we choose 'reject' approach: we don't alter p; caller decides.
    """
    if hemi is None:
        return True
    x, y, z = p
    if hemi == '+X': return x >= -1e-9
    if hemi == '-X': return x <= +1e-9
    if hemi == '+Y': return y >= -1e-9
    if hemi == '-Y': return y <= +1e-9
    if hemi == '+Z': return z >= -1e-9
    if hemi == '-Z': return z <= +1e-9
    return True

def try_move(theta, phi, dtheta, dphi, hemi):
    """Attempt to update (theta,phi) by deltas while honoring hemisphere constraint."""
    nt = theta + dtheta
    np_ = phi + dphi
    # wrap ranges
    # theta in [0, pi]
    nt = max(0.0, min(math.pi, nt))
    # phi wrap (-pi, pi] for readability
    np_ = (np_ + math.pi) % (2*math.pi) - math.pi

    x, y, z = sph_to_cart(nt, np_, 1.0)
    if clamp_hemisphere((x, y, z), hemi):
        return nt, np_
    # If blocked, allow sliding by zeroing one component at a time
    # Try only dphi
    x2, y2, z2 = sph_to_cart(theta, np_, 1.0)
    if clamp_hemisphere((x2, y2, z2), hemi):
        return theta, np_
    # Try only dtheta
    x3, y3, z3 = sph_to_cart(nt, phi, 1.0)
    if clamp_hemisphere((x3, y3, z3), hemi):
        return nt, phi
    # Otherwise stay put
    return theta, phi

# =========================
# Drawing helpers
# =========================

def draw_axes(screen, cx, cy):
    # build endpoints
    axes = [
        ((-AXIS_LEN, 0, 0), ( AXIS_LEN, 0, 0), AXIS_X_COLOR),
        ((0, -AXIS_LEN, 0), (0,  AXIS_LEN, 0), AXIS_Y_COLOR),
        ((0, 0, -AXIS_LEN), (0, 0,  AXIS_LEN), AXIS_Z_COLOR),
    ]
    for (x1,y1,z1), (x2,y2,z2), color in axes:
        p1 = project_point(x1,y1,z1,cx,cy)
        p2 = project_point(x2,y2,z2,cx,cy)
        if p1 and p2:
            pygame.draw.line(screen, color, p1, p2, 2)

def draw_wire_sphere(screen, cx, cy):
    # Latitude lines (theta constant)
    for i in range(1, LAT_LINES):
        theta = math.pi * i / LAT_LINES
        pts = []
        for j in range(CIRCLE_RES+1):
            phi = 2*math.pi * j / CIRCLE_RES
            x, y, z = sph_to_cart(theta, phi, RADIUS)
            sp = project_point(x, y, z, cx, cy)
            if sp:
                pts.append(sp)
        if len(pts) >= 2:
            pygame.draw.lines(screen, WIRE_COLOR, False, pts, 1)

    # Longitude lines (phi constant)
    for i in range(LON_LINES):
        phi = 2*math.pi * i / LON_LINES
        pts = []
        for j in range(CIRCLE_RES+1):
            theta = math.pi * j / CIRCLE_RES
            x, y, z = sph_to_cart(theta, phi, RADIUS)
            sp = project_point(x, y, z, cx, cy)
            if sp:
                pts.append(sp)
        if len(pts) >= 2:
            pygame.draw.lines(screen, WIRE_COLOR, False, pts, 1)

def draw_point_and_radius(screen, cx, cy, p):
    x, y, z = p
    # draw radius line from center to point
    origin = project_point(0,0,0,cx,cy)
    tip = project_point(x, y, z, cx, cy)
    if origin and tip:
        pygame.draw.line(screen, POINT_COLOR, origin, tip, 2)
        pygame.draw.circle(screen, POINT_COLOR, tip, POINT_SIZE)

def text(screen, font, s, x, y):
    img = font.render(s, True, TEXT_COLOR)
    screen.blit(img, (x, y))

def format_vec(v):
    return "({:+.3f}, {:+.3f}, {:+.3f})".format(v[0], v[1], v[2])

# =========================
# Main
# =========================

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Sphere Navigator — Arrow keys to move. 0-6 to constrain hemisphere.")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 20)
    big = pygame.font.SysFont(None, 28, bold=True)

    cx, cy = WIDTH // 2, HEIGHT // 2

    # Start at +X pole (theta=pi/2, phi=0)
    theta = math.pi / 2
    phi = 0.0

    hemisphere = None  # None, '+X','-X','+Y','-Y','+Z','-Z'

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

                elif event.key == pygame.K_r:
                    theta, phi = math.pi/2, 0.0

                elif event.key == pygame.K_0:
                    hemisphere = None
                elif event.key == pygame.K_1:
                    hemisphere = '+X'
                elif event.key == pygame.K_2:
                    hemisphere = '-X'
                elif event.key == pygame.K_3:
                    hemisphere = '+Y'
                elif event.key == pygame.K_4:
                    hemisphere = '-Y'
                elif event.key == pygame.K_5:
                    hemisphere = '+Z'
                elif event.key == pygame.K_6:
                    hemisphere = '-Z'

        # Key hold movement
        keys = pygame.key.get_pressed()
        fine = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        step = STEP_FINE if fine else STEP_COARSE

        dtheta = 0.0
        dphi = 0.0
        if keys[pygame.K_LEFT]:
            dphi -= step
        if keys[pygame.K_RIGHT]:
            dphi += step
        if keys[pygame.K_UP]:
            dtheta -= step
        if keys[pygame.K_DOWN]:
            dtheta += step

        if dtheta != 0.0 or dphi != 0.0:
            theta, phi = try_move(theta, phi, dtheta, dphi, hemisphere)

        # Compute current point on unit sphere, then scale to RADIUS for drawing
        ux, uy, uz = sph_to_cart(theta, phi, 1.0)
        px, py, pz = ux*RADIUS, uy*RADIUS, uz*RADIUS

        # Draw
        screen.fill(BG_COLOR)
        draw_wire_sphere(screen, cx, cy)
        draw_axes(screen, cx, cy)
        draw_point_and_radius(screen, cx, cy, (px, py, pz))

        # HUD
        text(screen, big, "Sphere Navigator", 16, 16)
        text(screen, font, "Arrows: move on surface   Shift: fine step   R: reset   0: free   1..6: hemisphere (+X,-X,+Y,-Y,+Z,-Z)   Esc/Q: quit", 16, 48)
        text(screen, font, f"Hemisphere: {hemisphere or 'None'}", 16, 72)
        text(screen, font, f"Unit direction: {format_vec((ux, uy, uz))}", 16, 96)
        text(screen, font, f"Theta (deg): {math.degrees(theta):.2f}   Phi (deg): {math.degrees(phi):.2f}", 16, 120)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
