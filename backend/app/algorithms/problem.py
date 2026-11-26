"""Timetable problem model: chromosome encoding, hard-constraint validator, soft objectives,
timetable-aware construction / repair / mutation / crossover operators.

Chromosome: int array (n_sessions, 3) -> columns [day, period, room_index].
Row i is the placement of session i; a session already fixes (section, subject, faculty, duration),
so every required weekly hour is scheduled by construction (and re-verified for DB-loaded timetables).
"""
import random
from dataclasses import dataclass
import numpy as np

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
OBJ_NAMES = ["student_free_periods", "faculty_preference_violations", "excess_consecutive_teaching",
             "room_underutilization", "subject_distribution"]
MAX_RUN = 3  # consecutive teaching periods allowed before the soft penalty applies


@dataclass
class Sess:
    idx: int
    section_id: int
    subject_id: int
    faculty_id: int
    duration: int
    is_lab: bool
    size: int
    key: tuple


class Occ:
    """Occupancy counters used for O(1) feasibility checks while constructing/repairing."""
    def __init__(self, prob, genes=None):
        self.p = prob
        self.fac, self.sec, self.room, self.fday = {}, {}, {}, {}
        if genes is not None:
            for i in range(len(prob.sessions)):
                self.place(i, int(genes[i][0]), int(genes[i][1]), int(genes[i][2]))

    def _mod(self, i, d, p, r, delta):
        s = self.p.sessions[i]
        for k in range(s.duration):
            for dct, key in ((self.fac, (s.faculty_id, d, p + k)), (self.sec, (s.section_id, d, p + k)),
                             (self.room, (r, d, p + k))):
                dct[key] = dct.get(key, 0) + delta
        self.fday[(s.faculty_id, d)] = self.fday.get((s.faculty_id, d), 0) + delta * s.duration

    def place(self, i, d, p, r): self._mod(i, d, p, r, 1)
    def remove(self, i, d, p, r): self._mod(i, d, p, r, -1)

    def free(self, i, d, p, r):
        pr = self.p
        s = pr.sessions[i]
        if (d, p) not in pr.slot_set[i] or r not in pr.room_set[i]:
            return False
        if self.fday.get((s.faculty_id, d), 0) + s.duration > pr.faculty[s.faculty_id]["max_daily"]:
            return False
        ru = pr.rooms[r]["unavailable"]
        for k in range(s.duration):
            t = p + k
            if self.fac.get((s.faculty_id, d, t), 0) or self.sec.get((s.section_id, d, t), 0) \
               or self.room.get((r, d, t), 0) or (d, t) in ru:
                return False
        return True


class Problem:
    def __init__(self, days, periods, break_after, sections, subjects, faculty, rooms, assignments,
                 weights=None, names=None):
        self.days, self.periods, self.break_after = days, periods, break_after
        self.sections, self.subjects, self.faculty = sections, subjects, faculty
        self.rooms, self.assignments = rooms, assignments
        self.weights = weights or {n: 1.0 for n in OBJ_NAMES}
        self.names = names or {}
        for f in faculty.values():
            f.setdefault("unavailable", set()); f.setdefault("avoid", set()); f.setdefault("prefer", set())
        for r in rooms:
            r.setdefault("unavailable", set()); r.setdefault("available", True)
        self._build()

    # ------------------------------------------------------------------ construction
    def _build(self):
        self.sessions = []
        for sec, sub, fac in self.assignments:
            s = self.subjects[sub]
            if s["is_lab"]:
                b = max(1, s.get("block", 2)); full, rem = divmod(s["hours"], b)
                durs = [b] * full + ([rem] if rem else [])
            else:
                durs = [1] * s["hours"]
            for d in durs:
                self.sessions.append(Sess(len(self.sessions), sec, sub, fac, d, bool(s["is_lab"]),
                                          self.sections[sec]["size"], (sec, sub)))
        self.by_key = {}
        for s in self.sessions:
            self.by_key.setdefault(s.key, []).append(s.idx)
        self.refresh()

    def block_ok(self, p, dur):
        if p < 0 or p + dur > self.periods: return False
        ba = self.break_after
        return not (dur > 1 and ba is not None and p <= ba < p + dur - 1)

    def refresh(self):
        """Recompute candidate slots/rooms (call after availability changes)."""
        self.cand_slots, self.cand_rooms, self.slot_set, self.room_set = [], [], [], []
        for s in self.sessions:
            fu = self.faculty[s.faculty_id]["unavailable"]
            slots = [(d, p) for d in range(self.days) for p in range(self.periods)
                     if self.block_ok(p, s.duration) and all((d, p + k) not in fu for k in range(s.duration))]
            rooms = [ri for ri, r in enumerate(self.rooms)
                     if r["is_lab"] == s.is_lab and r["capacity"] >= s.size and r["available"]]
            self.cand_slots.append(slots); self.cand_rooms.append(rooms)
            self.slot_set.append(set(slots)); self.room_set.append(set(rooms))

    # ------------------------------------------------------------------ hard constraints
    def analyze(self, genes):
        """Return list of hard violations: (type, [session idx], info dict)."""
        V, fac, sec, room, fday, fweek = [], {}, {}, {}, {}, {}
        for i, s in enumerate(self.sessions):
            d, p, ri = int(genes[i][0]), int(genes[i][1]), int(genes[i][2])
            if not (0 <= d < self.days) or not self.block_ok(p, s.duration) or not (0 <= ri < len(self.rooms)):
                V.append(("INVALID_SLOT", [i], {"day": d, "period": p})); continue
            r = self.rooms[ri]
            if r["is_lab"] != s.is_lab: V.append(("ROOM_TYPE", [i], {"day": d, "period": p, "room": ri}))
            if r["capacity"] < s.size: V.append(("ROOM_CAPACITY", [i], {"day": d, "period": p, "room": ri}))
            if not r["available"]: V.append(("ROOM_UNAVAILABLE", [i], {"day": d, "period": p, "room": ri}))
            fu = self.faculty[s.faculty_id]["unavailable"]
            f_bad = r_bad = False
            for k in range(s.duration):
                t = (d, p + k)
                if t in fu and not f_bad:
                    V.append(("FACULTY_UNAVAILABLE", [i], {"day": d, "period": p + k})); f_bad = True
                if t in r["unavailable"] and r["available"] and not r_bad:
                    V.append(("ROOM_UNAVAILABLE", [i], {"day": d, "period": p + k, "room": ri})); r_bad = True
                fac.setdefault((s.faculty_id,) + t, []).append(i)
                sec.setdefault((s.section_id,) + t, []).append(i)
                room.setdefault((ri,) + t, []).append(i)
            fday[(s.faculty_id, d)] = fday.get((s.faculty_id, d), []) + [i]
            fweek.setdefault(s.faculty_id, []).append(i)
        for dct, typ in ((fac, "FACULTY_CLASH"), (sec, "SECTION_CLASH"), (room, "ROOM_CLASH")):
            for key, lst in dct.items():
                if len(lst) > 1:
                    V.append((typ, sorted(set(lst)), {"key": key[0], "day": key[1], "period": key[2]}))
        for (f, d), lst in fday.items():
            if sum(self.sessions[i].duration for i in lst) > self.faculty[f]["max_daily"]:
                V.append(("FACULTY_DAILY_LOAD", lst, {"faculty": f, "day": d}))
        for f, lst in fweek.items():
            if sum(self.sessions[i].duration for i in lst) > self.faculty[f]["max_weekly"]:
                V.append(("FACULTY_WEEKLY_LOAD", lst, {"faculty": f}))
        return V

    def hard_count(self, genes): return len(self.analyze(genes))

    # ------------------------------------------------------------------ soft objectives (all minimised)
    def objectives(self, genes):
        sec_day, fac_day, dup = {}, {}, {}
        pref = 0; waste = 0.0
        for i, s in enumerate(self.sessions):
            d, p, ri = int(genes[i][0]), int(genes[i][1]), int(genes[i][2])
            fa = self.faculty[s.faculty_id]
            for k in range(s.duration):
                sec_day.setdefault((s.section_id, d), set()).add(p + k)
                fac_day.setdefault((s.faculty_id, d), set()).add(p + k)
                if (d, p + k) in fa["avoid"]: pref += 1
            r = self.rooms[ri]
            waste += max(0.0, (r["capacity"] - s.size) / r["capacity"])
            if not s.is_lab: dup[(s.key, d)] = dup.get((s.key, d), 0) + 1
        gaps = sum((max(ps) - min(ps) + 1) - len(ps) for ps in sec_day.values())
        consec = 0
        for ps in fac_day.values():
            run, prev = 0, None
            for p in sorted(ps):
                run = run + 1 if prev is not None and p == prev + 1 else 1
                if run > MAX_RUN: consec += 1
                prev = p
        dist = sum(c - 1 for c in dup.values() if c > 1)
        return np.array([gaps, pref, consec, round(waste, 4), dist], dtype=float)

    def evaluate(self, genes):
        return self.hard_count(genes), self.objectives(genes)

    def scalar(self, hard, obj):
        w = [self.weights.get(n, 1.0) for n in OBJ_NAMES]
        return hard * 1000.0 + float(np.dot(w, obj))

    # ------------------------------------------------------------------ operators
    def place_random(self, occ, i, rng):
        slots = self.cand_slots[i][:]; rng.shuffle(slots)
        for d, p in slots:
            rooms = self.cand_rooms[i][:]; rng.shuffle(rooms)
            for r in rooms:
                if occ.free(i, d, p, r): return (d, p, r)
        return None

    def random_solution(self, rng):
        n = len(self.sessions)
        order = sorted(range(n), key=lambda i: len(self.cand_slots[i]) * len(self.cand_rooms[i]) * (0.5 + rng.random())
                       / (self.sessions[i].duration))
        genes = np.zeros((n, 3), dtype=int); occ = Occ(self)
        for i in order:
            pos = self.place_random(occ, i, rng)
            if pos is None:  # infeasible fallback; repair() will try again
                sl = rng.choice(self.cand_slots[i] or [(0, 0)]); rm = rng.choice(self.cand_rooms[i] or [0])
                pos = (sl[0], sl[1], rm)
            genes[i] = pos; occ.place(i, *pos)
        return self.repair(genes, rng)

    def repair(self, genes, rng, rounds=4):
        genes = np.array(genes, dtype=int).reshape(-1, 3)
        for _ in range(rounds):
            V = self.analyze(genes)
            if not V: break
            bad = sorted({i for v in V for i in v[1]}); rng.shuffle(bad)
            occ = Occ(self, genes)
            for i in bad:
                cur = tuple(genes[i]); occ.remove(i, *cur)
                new = self.place_random(occ, i, rng) or cur
                occ.place(i, *new); genes[i] = new
        return genes

    def mutate(self, genes, rng, n_moves=2):
        genes = np.array(genes, dtype=int).reshape(-1, 3); n = len(self.sessions)
        occ = Occ(self, genes)
        for _ in range(n_moves):
            i = rng.randrange(n); cur = tuple(genes[i]); mv = rng.random()
            if mv < 0.6:  # reschedule
                occ.remove(i, *cur); new = self.place_random(occ, i, rng) or cur
                occ.place(i, *new); genes[i] = new
            elif mv < 0.85:  # swap slots of two same-duration sessions
                j = rng.randrange(n); cj = tuple(genes[j])
                if i == j or self.sessions[i].duration != self.sessions[j].duration: continue
                occ.remove(i, *cur); occ.remove(j, *cj)
                a, b = (cj[0], cj[1], cur[2]), (cur[0], cur[1], cj[2])
                if occ.free(i, *a):
                    occ.place(i, *a)
                    if occ.free(j, *b):
                        occ.place(j, *b); genes[i] = a; genes[j] = b; continue
                    occ.remove(i, *a)
                occ.place(i, *cur); occ.place(j, *cj)
            else:  # change room only
                rooms = [r for r in self.cand_rooms[i] if r != cur[2]]
                if not rooms: continue
                occ.remove(i, *cur); r = rng.choice(rooms)
                new = (cur[0], cur[1], r) if occ.free(i, cur[0], cur[1], r) else cur
                occ.place(i, *new); genes[i] = new
        return genes

    def crossover(self, a, b, rng):
        """Uniform crossover at (section, subject) granularity, followed by repair."""
        a = np.array(a).reshape(-1, 3); b = np.array(b).reshape(-1, 3)
        c1, c2 = a.copy(), b.copy()
        for idxs in self.by_key.values():
            if rng.random() < 0.5:
                c1[idxs], c2[idxs] = b[idxs], a[idxs]
        return self.repair(c1, rng), self.repair(c2, rng)

    # ------------------------------------------------------------------ analysis helpers
    def neighbors_move(self, genes, rng):
        """One random feasible neighbour (move / swap / room change) or None."""
        g = self.mutate(genes, rng, n_moves=1)
        return g if not np.array_equal(g, genes) else None
