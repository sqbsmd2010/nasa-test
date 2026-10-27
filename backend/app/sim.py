"""Server-authoritative simulation. The client never sees the incident schedule,
only noisy telemetry, like real mission control."""
import random
from dataclasses import dataclass, field


@dataclass
class State:
    sol: int = 0
    power_kw: float = 40.0
    o2_pct: float = 21.0
    water_l: float = 800.0
    food_kcal: float = 120_000.0
    dose_msv: float = 0.0
    morale: float = 1.0
    # player controls (continuous, 0..1)
    alloc: dict = field(default_factory=lambda: {"life": 0.4, "thermal": 0.2, "crops": 0.3, "comms": 0.1})
    shield_m: float = 1.0  # regolith depth in metres


class Sim:
    def __init__(self, seed: int | None = None, crew: int = 4):
        self.rng = random.Random(seed)
        self.s = State()
        self.crew = crew
        self._hidden: list[dict] = []  # never sent to client
        self._schedule()

    def _schedule(self):
        kinds = ["micrometeorite", "equipment_failure", "solar_particle_event", "supply_delay"]
        self._hidden = sorted(
            ({"sol": self.rng.randint(3, 60), "kind": self.rng.choice(kinds)} for _ in range(6)),
            key=lambda e: e["sol"],
        )

    def inject_real_flare(self):
        """Called when DONKI reports a real flare: becomes a real in-game incident."""
        self._hidden.append({"sol": self.s.sol + 1, "kind": "solar_particle_event"})

    def set_controls(self, alloc: dict, shield_m: float):
        total = sum(max(v, 0) for v in alloc.values()) or 1
        self.s.alloc = {k: max(v, 0) / total for k, v in alloc.items()}
        self.s.shield_m = min(max(shield_m, 0.0), 3.0)

    def step(self):
        s = self.s
        s.sol += 1
        s.food_kcal -= 2500 * self.crew * (1 - 0.3 * s.alloc["crops"])
        s.water_l -= 3 * self.crew * (1 - 0.8 * s.alloc["life"])
        s.dose_msv += 0.6 * (0.5 ** s.shield_m)  # placeholder attenuation, replace with real model
        events = [e for e in self._hidden if e["sol"] == s.sol]
        for e in events:
            self._apply(e["kind"])
        return [e["kind"] for e in events]

    def _apply(self, kind: str):
        s = self.s
        if kind == "solar_particle_event":
            s.dose_msv += 30 * (0.5 ** s.shield_m)
        elif kind == "micrometeorite":
            s.o2_pct -= 0.8
        elif kind == "equipment_failure":
            s.power_kw *= 0.85
        elif kind == "supply_delay":
            s.morale -= 0.1

    def telemetry(self):
        """What the player sees: noisy readings, no incident data."""
        s, n = self.s, lambda v, p=0.02: v * (1 + self.rng.uniform(-p, p))
        return {
            "sol": s.sol,
            "power_kw": round(n(s.power_kw), 1),
            "o2_pct": round(n(s.o2_pct, 0.005), 2),
            "water_l": round(n(s.water_l)),
            "food_kcal": round(n(s.food_kcal)),
            "dose_msv": round(n(s.dose_msv, 0.05), 2),
            "morale": round(s.morale, 2),
            "alloc": s.alloc,
            "shield_m": s.shield_m,
        }
