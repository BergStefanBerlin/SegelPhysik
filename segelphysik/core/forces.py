"""Kraftmodule (Spec §4/§5, Plan Issue 8-9, M3).

Alle Module implementieren ForceModule.apply(body, environment, dt) und
addieren Kraft/Moment auf den Körper (Spec §7.1: austauschbare Kraftmodelle,
Andockpunkt für Segelkräfte in v0.3).

Physik:
  - Auftrieb: F_A = rho_W * V_eingetaucht * g nach oben (Spec §2),
    Angriff im Körperschwerpunkt (Moment: v0.2-Dokumentvereinfachung).
    Wasseroberfläche z = 0 (Spec §2); Wellen-Oberfläche folgt in M4+.
  - Wasserwiderstand: F = -1/2 rho_W c_w A_ref |v_rel| v_rel mit
    v_rel = v_Körper - v_Fluid(lokal, SPH-Abfrage velocity_at),
    skaliert mit dem Eintauchanteil alpha = V_sub/V (Spec §4, §5).
  - Luftwiderstand: analog mit rho_L und v_rel = v - v_Wind
    (quadratisches Gesetz, Spec §3); Wind über WindField (Pflichtfeature).
    Ein ruhender Körper wird VOM Wind MITGERISSEN (Kraft in Windrichtung).
  - Impulsübertrag (Spec §5): die Reaktionskraft der Wasserreibung wird
    über fluid.apply_body_force() auf die umliegenden SPH-Partikel
    verteilt (zweiwege Kopplung, vereinfacht als Kraftverteilung).
  - c_w: pro Körper überschreibbar (Attribut cw), sonst Defaults aus
    config.defaults_body (Kugel 0,47 / Quader 1,05 - Spec §4).
"""
import numpy as np
from abc import ABC, abstractmethod


class ForceModule(ABC):
    @abstractmethod
    def apply(self, body, environment, dt):
        """Addiert Kraft/Moment auf body."""


class WindField:
    """Homogenes Windfeld (Spec §3, Pflichtfeature). Schnittstelle für
    ortsabhängige Felder in v0.3: Methode velocity(pos) überschreiben."""

    def __init__(self, speed=0.0, azimuth_deg=0.0):
        self.speed = float(speed)
        self.azimuth_deg = float(azimuth_deg)

    def velocity(self, pos=None):
        a = np.deg2rad(self.azimuth_deg)
        return self.speed * np.array([np.cos(a), np.sin(a), 0.0])


class Environment:
    """Übergabeobjekt für Kraftmodule: Config, Fluid, Wind (Spec §7.1)."""

    def __init__(self, cfg, fluid):
        self.cfg = cfg
        self.fluid = fluid
        self.wind = WindField(float(cfg.wind.get("speed", 0.0)),
                              float(cfg.wind.get("azimuth_deg", 0.0)))

    @property
    def g(self):
        return self.cfg.g

    def cw_default(self, body):
        db = self.cfg.defaults_body
        from .bodies import Sphere, Box
        if isinstance(body, Sphere):
            return float(db.get("cw_sphere", 0.47))
        if isinstance(body, Box):
            return float(db.get("cw_box", 1.05))
        return 1.0


class Gravity(ForceModule):
    def apply(self, body, environment, dt):
        body.apply_force(np.array([0.0, 0.0, -environment.g]) * body.mass)


class Buoyancy(ForceModule):
    """Archimedes: F_A = rho_W * V_eingetaucht * g (Spec §2)."""

    def apply(self, body, environment, dt):
        rho_w = float(environment.cfg.water["rho"])
        v_sub = body.submerged_volume(0.0)
        if v_sub <= 0.0:
            return
        body.apply_force(np.array([0.0, 0.0, rho_w * v_sub * environment.g]))


def _submerged_fraction(body):
    v = body.volume()
    return body.submerged_volume(0.0) / v if v > 0 else 0.0


class WaterDrag(ForceModule):
    """Quadratischer Widerstand gegen die lokale SPH-Fluidgeschwindigkeit;
    Reaktionskraft geht als Impuls auf die Partikel zurück (Spec §5)."""

    def apply(self, body, environment, dt):
        alpha = _submerged_fraction(body)
        if alpha <= 0.0:
            return
        rho_w = float(environment.cfg.water["rho"])
        v_rel = body.vel - environment.fluid.velocity_at(body.pos)
        sp = float(np.linalg.norm(v_rel))
        if sp < 1e-9:
            return
        cw = getattr(body, "cw", None) or environment.cw_default(body)
        a_ref = body.a_ref(v_rel)
        f = -0.5 * rho_w * cw * a_ref * sp * v_rel * alpha
        body.apply_force(f)
        environment.fluid.apply_body_force(body.pos, -f, dt)


class AirDrag(ForceModule):
    """Quadratischer Luftwiderstand relativ zum Wind (Spec §3)."""

    def apply(self, body, environment, dt):
        alpha = _submerged_fraction(body)
        frac_air = 1.0 - alpha
        if frac_air <= 0.0:
            return
        rho_l = float(environment.cfg.air["rho"])
        v_rel = body.vel - environment.wind.velocity(body.pos)
        sp = float(np.linalg.norm(v_rel))
        if sp < 1e-9:
            return
        cw = getattr(body, "cw", None) or environment.cw_default(body)
        a_ref = body.a_ref(v_rel)
        body.apply_force(-0.5 * rho_l * cw * a_ref * sp * v_rel * frac_air)
