````markdown
# Sphere Navigator

A simple Python tool to visualize and control rotation on a 3D sphere.  
It displays a **wireframe sphere**, **XYZ axes**, and a **point** on the sphere’s surface that you can move using the arrow keys.  
This is useful for prototyping direction control for **cameras, drones, turrets, or vehicles**.

---

## Features

- Wireframe 3D sphere drawn with `pygame`
- XYZ axis visualization
- A movable control point that always stays on the sphere’s surface
- Hemisphere constraints (lock the point to one half of the sphere)
- Readout of current direction vector `(x, y, z)` and spherical coordinates `(θ, φ)`
- Keyboard controls for coarse and fine movement

---

## Installation

1. Clone this repository or copy the files.
2. Make sure you have Python 3.8+ installed.
3. Install dependencies:

```bash
pip install pygame
````

---

## Usage

Run the script:

```bash
python sphere_navigator.py
```

---

## Controls

* **Arrow Left / Right** → rotate azimuth (φ) around Z axis
* **Arrow Up / Down** → change polar angle (θ) toward/away from Z
* **Shift + Arrows** → fine adjustment
* **R** → reset point to +X pole
* **0** → free movement (no hemisphere constraint)
* **1..6** → constrain to hemisphere:

  * `1`: +X
  * `2`: -X
  * `3`: +Y
  * `4`: -Y
  * `5`: +Z
  * `6`: -Z
* **Esc / Q** → quit

---

## Output

The HUD shows:

* Current hemisphere constraint
* Unit direction vector `(x, y, z)`
* Current spherical angles `(θ, φ)` in degrees

This unit vector can be used to drive:

* **Gimbal angles** for a camera
* **Turret aiming**
* **Drone navigation**
* Any system that needs a normalized orientation vector

---

## Example

Starting position is the +X pole `(1, 0, 0)`.
Press the arrow keys to rotate the point along the sphere’s surface.
The bottom HUD will show the updated direction vector, e.g.:

```
Unit direction: (+0.707, +0.000, +0.707)
Theta (deg): 45.00   Phi (deg): 0.00
```

---

## Extending

* Add mouse drag for free camera-like orbiting
* Stream the vector over UDP or serial to hardware
* Export yaw/pitch angles for servo-based gimbals
* Replace the wireframe with a textured globe

---

## License

MIT License — use and modify freely.
