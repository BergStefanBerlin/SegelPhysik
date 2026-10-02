# ============================================================
# math_utils.py - Quaternionen, Rotationsmatrizen, Euler-Winkel
# ------------------------------------------------------------
# Rein funktionale Helfer ohne weitere Abhaengigkeiten (nur numpy).
# Konvention: Quaternion (w, x, y, z); Drehmatrix R = Rx(r)Ry(p)Rz(y).
# ============================================================
import numpy as np


def quat_mul(a, b):
    """Hamilton-Produkt zweier Quaternions (w, x, y, z)."""
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2])


def quat_from_euler(roll, pitch, yaw=0.0):
    """Quaternion zur Drehmatrix R = Rx(roll) @ Ry(pitch) @ Rz(yaw)."""
    qx = np.array([np.cos(roll/2),  np.sin(roll/2), 0.0, 0.0])
    qy = np.array([np.cos(pitch/2), 0.0, np.sin(pitch/2), 0.0])
    qz = np.array([np.cos(yaw/2),   0.0, 0.0, np.sin(yaw/2)])
    return quat_mul(quat_mul(qx, qy), qz)


def quat_to_R(q):
    q = np.asarray(q, float)
    q = q / np.linalg.norm(q)
    w, x, y, z = q
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-w*z),   2*(x*z+w*y)],
        [2*(x*y+w*z),   1-2*(x*x+z*z), 2*(y*z-w*x)],
        [2*(x*z-w*y),   2*(y*z+w*x),   1-2*(x*x+y*y)]])


def rotationsmatrix(roll, pitch, yaw=0.0):
    return quat_to_R(quat_from_euler(roll, pitch, yaw))


def euler_aus_R(R):
    """Anzeige-Winkel zu R = Rx(r)Ry(p)Rz(y):
       R02 = sin(p), R12 = -sin(r)cos(p), R22 = cos(r)cos(p),
       R01 = -cos(p)sin(y), R00 = cos(p)cos(y)."""
    pitch = np.arcsin(np.clip(R[0, 2], -1.0, 1.0))
    roll = np.arctan2(-R[1, 2], R[2, 2])
    yaw = np.arctan2(-R[0, 1], R[0, 0])
    return roll, pitch, yaw
