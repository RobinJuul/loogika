"""
Epistemilise modaalloogika mudelikontrollija
=============================================

Loogika arvutiteaduses — projekt: ligipääsukontroll epistemilise modaalloogikana.

Programm võtab sisendiks Kripke mudeli (maailmad, iga agendi ligipääsuseos,
valuatsioon) ja mitme-agendilise epistemilise valemi ning kontrollib semantilise
rekursiooni teel, kas valem kehtib antud maailmas.

Toetatud süntaks (abstraktne süntaksipuu n-tikutena):
    ("aatom", p)            -- aatomlause p
    ("mitte", f)            -- ¬f
    ("ja", f, g)            -- f ∧ g
    ("voi", f, g)           -- f ∨ g
    ("implies", f, g)       -- f → g
    ("K", a, f)             -- K_a f  ("agent a teab, et f")
    ("M", a, f)             -- M_a f = ¬K_a¬f  ("a peab f-i võimalikuks")

Semantika (Kripke):
    M, w ⊨ K_a f   ssa   iga v korral, kui (w, v) ∈ R_a, siis M, v ⊨ f.

Autor: Robin Juul, Tartu Ülikool.
"""

from dataclasses import dataclass, field
from typing import Callable


# --------------------------------------------------------------------------
# Kripke mudel
# --------------------------------------------------------------------------

@dataclass
class KripkeMudel:
    """
    Mitme-agendiline Kripke mudel epistemiliseks loogikaks.

    maailmad   -- maailmade hulk (nt {"w1", "w2"})
    seosed     -- sõnastik agent -> ligipääsuseos, kus seos on paaride hulk.
                  (w, v) ∈ seosed[a] tähendab: maailmas w peab agent a
                  maailma v võimalikuks (oma teadmiste põhjal eristamatuks).
    valuatsioon-- sõnastik maailm -> selles maailmas tõeste aatomite hulk.
    """
    maailmad: set
    seosed: dict          # agent -> set[(w, v)]
    valuatsioon: dict     # maailm -> set[aatom]

    def jargijad(self, agent, w):
        """Maailmad, mida agent maailmas w võimalikuks peab."""
        return {v for (x, v) in self.seosed.get(agent, set()) if x == w}

    # --- süsteemiomaduste kontroll (K, T, S4 eristamiseks) -----------------

    def on_refleksiivne(self, agent):
        """T-aksioom: iga maailm näeb iseennast (teadmine on tõene)."""
        R = self.seosed.get(agent, set())
        return all((w, w) in R for w in self.maailmad)

    def on_transitiivne(self, agent):
        """4-aksioom: positiivne introspektsioon (a teab, et ta teab)."""
        R = self.seosed.get(agent, set())
        for (w, v) in R:
            for (v2, u) in R:
                if v == v2 and (w, u) not in R:
                    return False
        return True

    def susteem(self, agent):
        """Tagastab tugevaima standardsüsteemi, mida agendi seos rahuldab."""
        r = self.on_refleksiivne(agent)
        t = self.on_transitiivne(agent)
        if r and t:
            return "S4"
        if r:
            return "T"
        return "K"


# --------------------------------------------------------------------------
# Valemikonstruktorid (loetavuse huvides)
# --------------------------------------------------------------------------

def aatom(p):            return ("aatom", p)
def mitte(f):            return ("mitte", f)
def ja(f, g):            return ("ja", f, g)
def voi(f, g):           return ("voi", f, g)
def implies(f, g):       return ("implies", f, g)
def K(a, f):             return ("K", a, f)
def M(a, f):             return ("M", a, f)


# --------------------------------------------------------------------------
# Mudelikontroll — rekursiivne semantika
# --------------------------------------------------------------------------

def kehtib(mudel: KripkeMudel, w, valem) -> bool:
    """
    Kontrollib, kas mudel, w ⊨ valem.

    See on epistemilise modaalloogika tõeväärtussemantika otsene rakendus:
    iga valemikuju käsitletakse vastava semantilise tingimusega.
    """
    liik = valem[0]

    if liik == "aatom":
        return valem[1] in mudel.valuatsioon.get(w, set())

    if liik == "mitte":
        return not kehtib(mudel, w, valem[1])

    if liik == "ja":
        return kehtib(mudel, w, valem[1]) and kehtib(mudel, w, valem[2])

    if liik == "voi":
        return kehtib(mudel, w, valem[1]) or kehtib(mudel, w, valem[2])

    if liik == "implies":
        return (not kehtib(mudel, w, valem[1])) or kehtib(mudel, w, valem[2])

    if liik == "K":
        # K_a f : f kehtib KÕIGIS maailmades, mida a maailmas w võimalikuks peab.
        agent, f = valem[1], valem[2]
        return all(kehtib(mudel, v, f) for v in mudel.jargijad(agent, w))

    if liik == "M":
        # M_a f = ¬K_a¬f : leidub vähemalt üks võimalik maailm, kus f kehtib.
        agent, f = valem[1], valem[2]
        return any(kehtib(mudel, v, f) for v in mudel.jargijad(agent, w))

    raise ValueError(f"Tundmatu valemikuju: {liik}")


def kehtib_kogu_mudelis(mudel: KripkeMudel, valem) -> bool:
    """Kas valem kehtib mudeli igas maailmas (mudelis samaselt tõene)?"""
    return all(kehtib(mudel, w, valem) for w in mudel.maailmad)


def leia_kontranaide(mudel: KripkeMudel, valem):
    """Tagastab maailma, kus valem on väär, või None, kui valem kehtib kõikjal."""
    for w in sorted(mudel.maailmad):
        if not kehtib(mudel, w, valem):
            return w
    return None


def valem_str(valem) -> str:
    """Valemi inimloetav esitus."""
    liik = valem[0]
    if liik == "aatom":   return valem[1]
    if liik == "mitte":   return f"¬{valem_str(valem[1])}"
    if liik == "ja":      return f"({valem_str(valem[1])} ∧ {valem_str(valem[2])})"
    if liik == "voi":     return f"({valem_str(valem[1])} ∨ {valem_str(valem[2])})"
    if liik == "implies": return f"({valem_str(valem[1])} → {valem_str(valem[2])})"
    if liik == "K":       return f"K_{valem[1]}{valem_str(valem[2])}"
    if liik == "M":       return f"M_{valem[1]}{valem_str(valem[2])}"
    return "?"
