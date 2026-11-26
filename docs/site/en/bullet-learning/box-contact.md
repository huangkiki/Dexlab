# Bullet Physics: Step through a box drop and read the support force

A 1 kg box resting on a horizontal floor should have an average upward support force close to its weight, 9.81 N. Read the contact force with collision enabled, then turn off collision for that body pair and see whether the support disappears.

## Run the two controls

{download}`Download bullet_box_contact.py <../../../learning/examples/bullet_box_contact.py>` and run these commands in the download directory. They apply to Linux x86-64 with a matching wheel.

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: pybullet==3.2.7 numpy==2.2.6
.venv/bin/python bullet_box_contact.py
```

This PyBullet wheel imports NumPy, so the command installs both explicitly.

The script uses `GEOM_BOX` to make a 0.20 m cube. Its center starts 1.00 m above a fixed plane at Z=0. Each `stepSimulation()` advances 1/240 s, then the script reads the contacts for that step. Both cases advance 480 steps. The second run only disables collision between the box and floor.

```{literalinclude} ../../../learning/examples/bullet_box_contact.py
:language: python
```

## Read the output

DexLab ran the script above on Linux x86-64 with Python 3.11.14 and PyBullet 3.2.7.

| Signal | Collision enabled | Collision disabled |
| --- | --- | --- |
| First upward support | Step 104, 0.433 s | `null` |
| Center height and vertical velocity at 2 s | 0.09999 m, about 0 m/s | −18.661 m, −19.62 m/s |
| Mean support over the last 0.5 s | 9.81 N | 0 N |

`getContactPoints(box, floor)` reports contacts from the last simulation step. Each `contactNormalOnB` points toward Box. Multiply its Z component by `normalForce` and sum over the points to get the vertical normal support. On level ground the normal is nearly vertical. On an incline, project in the direction you need. Use `getClosestPoints` for a geometry distance query. Distance alone cannot tell you whether the floor is carrying a load. [Official PyBullet guide](https://github.com/bulletphysics/bullet3/blob/master/docs/pybullet_quickstartguide.pdf) · [Upstream contact-force example](https://github.com/bulletphysics/bullet3/blob/master/examples/pybullet/examples/contactFriction.py)

If the box lacks support, first check whether it entered the contact region and whether the two bodies were allowed to collide. Once contacts exist, look for the change in vertical velocity from the normal force. The collision-disabled control checks that the contact measurement responds to filtering. Grasping and real materials require separate evidence.

[Course contents](index.md) · [Next: sliding and load at a joint](friction-and-joints.md)
