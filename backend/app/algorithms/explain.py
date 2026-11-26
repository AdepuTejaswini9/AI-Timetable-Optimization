"""Explainable constraint handling: structured violation reports and infeasibility proofs."""
from app.algorithms.problem import DAY_NAMES

def _n(prob, kind, id_):
    return prob.names.get(kind, {}).get(id_, f"{kind}#{id_}")

def _slot(d, p):
    return f"{DAY_NAMES[d] if d is not None and 0 <= d < 6 else d} P{(p or 0) + 1}"

SUGGEST = {
    "FACULTY_CLASH": "Move one of the classes to a period where the faculty member is free, or assign a substitute faculty.",
    "ROOM_CLASH": "Assign one of the classes to another free room of the same type, or move it to another period.",
    "SECTION_CLASH": "Move one class of the section to a free period.",
    "ROOM_CAPACITY": "Use a larger room or split the section.",
    "ROOM_TYPE": "Use a laboratory for lab sessions and a classroom for theory sessions.",
    "FACULTY_UNAVAILABLE": "Reschedule the class outside the faculty member's unavailable periods or assign a substitute.",
    "ROOM_UNAVAILABLE": "Move the class to another room or period; the room is marked unavailable.",
    "INVALID_SLOT": "Choose a period range inside the working day; lab blocks cannot cross the lunch break.",
    "FACULTY_DAILY_LOAD": "Spread this faculty member's classes over more days.",
    "FACULTY_WEEKLY_LOAD": "Reduce the teaching load or reassign a subject to another faculty member.",
    "REQUIRED_HOURS": "Schedule the missing sessions or remove the extra ones so weekly hours match the subject definition.",
    "INVALID_REFERENCE": "The entry references a faculty/subject/section combination that is not in the subject assignments.",
}

def describe(prob, genes):
    """Structured report for every hard violation of a chromosome."""
    out = []
    for typ, idxs, info in prob.analyze(genes):
        s = prob.sessions[idxs[0]]
        d = info.get("day", int(genes[idxs[0]][0])); p = info.get("period", int(genes[idxs[0]][1]))
        ri = info.get("room", int(genes[idxs[0]][2]))
        room = prob.rooms[ri] if 0 <= ri < len(prob.rooms) else None
        fac, sub, sec = _n(prob, "faculty", s.faculty_id), _n(prob, "subject", s.subject_id), _n(prob, "section", s.section_id)
        txt = {
            "FACULTY_CLASH": f"{fac} is assigned to {len(idxs)} classes at {_slot(d, p)}.",
            "ROOM_CLASH": f"Room {room['name'] if room else ri} is used by {len(idxs)} classes at {_slot(d, p)}.",
            "SECTION_CLASH": f"Section {sec} has {len(idxs)} classes at {_slot(d, p)}.",
            "ROOM_CAPACITY": f"Room {room['name'] if room else ri} (capacity {room['capacity'] if room else '?'}) is too small for {sec} ({s.size} students).",
            "ROOM_TYPE": f"{sub} ({'lab' if s.is_lab else 'theory'}) is placed in an unsuitable room type.",
            "FACULTY_UNAVAILABLE": f"{fac} is unavailable at {_slot(d, p)}.",
            "ROOM_UNAVAILABLE": f"Room {room['name'] if room else ri} is unavailable at {_slot(d, p)}.",
            "INVALID_SLOT": f"{sub} for {sec} starts at an invalid period ({_slot(d, p)}) for its duration.",
            "FACULTY_DAILY_LOAD": f"{fac} exceeds the maximum daily hours on {_slot(d, 0).split()[0]}.",
            "FACULTY_WEEKLY_LOAD": f"{fac} exceeds the maximum weekly hours.",
        }[typ]
        out.append({"type": typ, "severity": "hard", "faculty_id": s.faculty_id, "faculty": fac,
                    "subject_id": s.subject_id, "subject": sub, "section_id": s.section_id, "section": sec,
                    "room_id": room["id"] if room else None, "room": room["name"] if room else None,
                    "day": d, "period": p, "slot": _slot(d, p), "explanation": txt,
                    "suggestion": SUGGEST[typ], "sessions": idxs})
    return out

def proof_of_infeasibility(prob):
    """Sound necessary-condition checks. A non-empty result PROVES that no feasible timetable exists.
    An empty result does NOT prove feasibility (the search may still fail within its limit)."""
    reasons = []
    for s in prob.sessions:
        if not prob.cand_rooms[s.idx]:
            reasons.append({"type": "NO_SUITABLE_ROOM", "explanation":
                f"No available {'laboratory' if s.is_lab else 'classroom'} fits {_n(prob,'section',s.section_id)} "
                f"({s.size} students) for {_n(prob,'subject',s.subject_id)}.",
                "suggestion": "Add or enable a larger room of the right type."})
        if not prob.cand_slots[s.idx]:
            reasons.append({"type": "NO_FACULTY_SLOT", "explanation":
                f"{_n(prob,'faculty',s.faculty_id)} has no available slot that fits {_n(prob,'subject',s.subject_id)} "
                f"({s.duration}h block).", "suggestion": "Relax the faculty availability or assign a substitute."})
    seen = set()
    fac_h, sec_h = {}, {}
    for s in prob.sessions:
        fac_h[s.faculty_id] = fac_h.get(s.faculty_id, 0) + s.duration
        sec_h[s.section_id] = sec_h.get(s.section_id, 0) + s.duration
    total = prob.days * prob.periods
    for f, h in fac_h.items():
        fa = prob.faculty[f]; avail = total - len({t for t in fa["unavailable"]})
        cap = min(fa["max_weekly"], fa["max_daily"] * prob.days, avail)
        if h > cap:
            reasons.append({"type": "REQUIRED_HOURS_EXCEED_CAPACITY", "explanation":
                f"{_n(prob,'faculty',f)} must teach {h}h/week but can teach at most {cap}h "
                "(weekly/daily limits and availability).", "suggestion": "Reassign a subject or raise limits."})
    for sec, h in sec_h.items():
        if h > total:
            reasons.append({"type": "SECTION_OVERLOADED", "explanation":
                f"Section {_n(prob,'section',sec)} needs {h}h but only {total} periods exist per week.",
                "suggestion": "Reduce weekly hours or add periods/days."})
    for lab in (True, False):
        need = sum(s.duration for s in prob.sessions if s.is_lab == lab)
        rooms = [r for r in prob.rooms if r["is_lab"] == lab and r["available"]]
        if need > len(rooms) * total:
            reasons.append({"type": "ROOM_HOURS_EXCEED_CAPACITY", "explanation":
                f"{need} {'lab' if lab else 'classroom'} hours are required but rooms offer only {len(rooms) * total}.",
                "suggestion": "Add rooms or reduce hours."})
    return reasons
