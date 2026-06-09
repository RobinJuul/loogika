"""
Juhtumiuuring: haigla infosüsteemi ligipääsukontroll
====================================================

Stsenaarium
-----------
Haigla infosüsteemis on patsiendi terviseandmed (ressurss `andmed`). Ligipääsu
reguleerivad kolm agenti:

    arst       -- patsienti ravib arst
    oe         -- valveõde
    admin      -- süsteemiadministraator

Poliitika (mitteformaalselt):
    - Arst pääseb terviseandmetele ligi, KUI ta on patsiendi raviarst.
    - Õde pääseb ligi, KUI ta on patsiendiga seotud valves.
    - Administraator EI tohi sisu näha, kuid peab teadma, KAS arstil on ligipääs
      (auditeerimiskohustus). See on "kõrgema astme teadmine": K_admin (K_arst andmed).

Me modelleerime poliitika kolmel viisil ja kontrollime mudelikontrollijaga, et
epistemiline kodeering peegeldab samu otsuseid mis RBAC/ABAC, AGA suudab lisaks
väljendada administraatori teadmist arsti ligipääsust.

Kripke mudeli idee
------------------
Iga maailm on üks võimalik süsteemi konfiguratsioon (kes on raviarst jne).
Aatomid:
    raviarst    -- "arst on selle patsiendi raviarst"
    valves      -- "õde on valves selle patsiendiga"
    ligipaas_a  -- "arstil on andmetele ligipääs"
    ligipaas_o  -- "õel on andmetele ligipääs"

Agendi seos R_a sisaldab maailmu, mida agent a oma info põhjal eristada ei suuda.
"""

from mudelikontrollija import (
    KripkeMudel, kehtib, leia_kontranaide, valem_str,
    aatom, mitte, ja, voi, implies, K, M,
)


# --------------------------------------------------------------------------
# 1. RBAC kodeering (taustana, lauseloogika tasemel)
# --------------------------------------------------------------------------
# RBAC: ligipääs = rolli omamine. Rollid on staatilised omistused.
#   roll(arst) ∧ määratud(arst, patsient)  →  ligipaas_a
# RBAC-s pole agendi "teadmise" mõistet — see on puhtalt rollide ja
# õiguste vaheline funktsioon. Esitame selle tavalise implikatsioonina.

def rbac_arsti_ligipaas():
    # Rollipõhine: kui on raviarst-roll, siis ligipääs.
    return implies(aatom("raviarst"), aatom("ligipaas_a"))


# --------------------------------------------------------------------------
# 2. ABAC kodeering (taustana)
# --------------------------------------------------------------------------
# ABAC: ligipääs = atribuutide loogiline tingimus. Paindlikum kui RBAC,
# kuid endiselt "kas-ligipääs" otsus, mitte teadmine.
#   (atribuut.raviarst = tõene) ∨ (atribuut.valves = tõene)  →  ligipääs

def abac_ligipaas():
    return implies(voi(aatom("raviarst"), aatom("valves")),
                   voi(aatom("ligipaas_a"), aatom("ligipaas_o")))


# --------------------------------------------------------------------------
# 3. Epistemiline kodeering — see on projekti tuum
# --------------------------------------------------------------------------
# Administraatori auditeerimisomadus, mida RBAC/ABAC EI väljenda:
#   K_admin (raviarst → K_arst ligipaas_a)
# "Administraator teab, et KUI arst on raviarst, SIIS arst teab oma ligipääsu."

def admin_audit():
    return K("admin", implies(aatom("raviarst"), K("arst", aatom("ligipaas_a"))))

# Turvaomadus: arst ei tea kunagi õe ligipääsu sisu kohta rohkem kui vaja
#   ¬K_arst ligipaas_o   (arst ei pruugi teada õe ligipääsu)
def arst_ei_tea_oe():
    return mitte(K("arst", aatom("ligipaas_o")))


# --------------------------------------------------------------------------
# Konkreetne mudel
# --------------------------------------------------------------------------
# Maailmad:
#   w1: arst on raviarst, õde valves, mõlemal ligipääs
#   w2: arst EI ole raviarst, õde valves -> ainult õel ligipääs
#   w3: arst on raviarst, õde EI ole valves -> ainult arstil ligipääs
#
# Eristatavus:
#   - arst eristab maailmu oma raviarst-staatuse järgi (teab, kas on raviarst),
#     kuid ei näe õe valvestaatust -> ei erista w1 ja w3.
#   - admin näeb kõike (refleksiivne, eristab kõiki) -> teab kogu konfiguratsiooni.

def ehita_mudel():
    maailmad = {"w1", "w2", "w3"}
    valuatsioon = {
        "w1": {"raviarst", "valves", "ligipaas_a", "ligipaas_o"},
        "w2": {"valves", "ligipaas_o"},
        "w3": {"raviarst", "ligipaas_a"},
    }
    # Arst teab oma raviarst-staatust => ei sega w2 (pole raviarst) teistega.
    # Ei näe õe valvet => w1 ja w3 (mõlemas on ta raviarst) on talle eristamatud.
    R_arst = {
        ("w1", "w1"), ("w1", "w3"),
        ("w3", "w1"), ("w3", "w3"),
        ("w2", "w2"),
    }
    # Õde teab oma valvestaatust => w3 (pole valves) eristatud; w1, w2 (valves) seotud.
    R_oe = {
        ("w1", "w1"), ("w1", "w2"),
        ("w2", "w1"), ("w2", "w2"),
        ("w3", "w3"),
    }
    # Admin näeb täielikku konfiguratsiooni => ainult refleksiivne (teab kõike).
    R_admin = {("w1", "w1"), ("w2", "w2"), ("w3", "w3")}

    return KripkeMudel(
        maailmad=maailmad,
        seosed={"arst": R_arst, "oe": R_oe, "admin": R_admin},
        valuatsioon=valuatsioon,
    )


# --------------------------------------------------------------------------
# Testjuhud
# --------------------------------------------------------------------------

def jooksuta_testid():
    m = ehita_mudel()
    print("=" * 70)
    print("HAIGLA LIGIPÄÄSUKONTROLL — EPISTEMILINE MUDELIKONTROLL")
    print("=" * 70)

    print("\nAgendi seoste süsteemiklassid (K / T / S4):")
    for a in ("arst", "oe", "admin"):
        print(f"  R_{a:6s}: {m.susteem(a)}"
              f"  (refleksiivne={m.on_refleksiivne(a)}, "
              f"transitiivne={m.on_transitiivne(a)})")

    testid = [
        # (kirjeldus, maailm, valem, oodatud)
        ("Arst teab oma ligipääsu, kui on raviarst (w1)",
         "w1", implies(aatom("raviarst"), K("arst", aatom("ligipaas_a"))), True),

        ("Arst ei tea õe ligipääsu (w1) — privaatsus",
         "w1", arst_ei_tea_oe(), True),

        ("Admin teab, et arst teab oma ligipääsu (audit, w1)",
         "w1", admin_audit(), True),

        ("Admin teab arsti raviarst-staatust (w3)",
         "w3", voi(K("admin", aatom("raviarst")),
                   K("admin", mitte(aatom("raviarst")))), True),

        ("Arst EI tea, kas õde on valves (w1) — w1/w3 eristamatud",
         "w1", mitte(voi(K("arst", aatom("valves")),
                         K("arst", mitte(aatom("valves"))))), True),

        ("RBAC: raviarst → ligipääs kehtib kõikjal",
         "w1", rbac_arsti_ligipaas(), True),

        ("ABAC: atribuut → ligipääs kehtib kõikjal",
         "w1", abac_ligipaas(), True),
    ]

    print("\nTestjuhud:")
    koik_ok = True
    for kirjeldus, w, valem, oodatud in testid:
        tulemus = kehtib(m, w, valem)
        ok = (tulemus == oodatud)
        koik_ok = koik_ok and ok
        mark = "✓" if ok else "✗ VIGA"
        print(f"  [{mark}] {kirjeldus}")
        print(f"         {valem_str(valem)}  @ {w}  =>  {tulemus}")

    # Kontranäite demonstratsioon: RBAC ei "tea" arsti teadmist.
    print("\nKontranäide — epistemilise omaduse mitte-väljendatavus RBAC-s:")
    audit = admin_audit()
    kn = leia_kontranaide(m, audit)
    if kn is None:
        print(f"  Audit-valem {valem_str(audit)} kehtib KÕIGIS maailmades.")
        print("  RBAC/ABAC valem sisaldab ainult ligipääsu-aatomeid, mitte")
        print("  K_admin/K_arst operaatoreid — seda omadust seal sõnastada ei saa.")

    demo_susteemivahe()

    print("\n" + ("KÕIK TESTID LÄBITUD ✓" if koik_ok else "MÕNI TEST EBAÕNNESTUS ✗"))
    print("=" * 70)
    return koik_ok


def demo_susteemivahe():
    """
    Demonstreerib K vs T erinevust: uskumus vs teadmine.

    Kui agendi seos EI ole refleksiivne (süsteem K, mitte T), võib agent
    "uskuda" midagi, mis tegelikus maailmas väär on — st K_a f võib kehtida
    maailmas, kus f ise on väär. T-aksioom (K_a f → f) seda välistab.
    Ligipääsukontekstis: ekslik volituse-uskumus on turvarisk.
    """
    print("\n" + "-" * 70)
    print("K vs T: uskumus vs teadmine (turvarelevantsus)")
    print("-" * 70)
    # u1: ligipääsu EI ole; agent peab võimalikuks ainult u2, kus ligipääs on.
    # Seos pole refleksiivne (u1 ei näe iseennast) => süsteem K, mitte T.
    m = KripkeMudel(
        maailmad={"u1", "u2"},
        seosed={"x": {("u1", "u2"), ("u2", "u2")}},
        valuatsioon={"u1": set(), "u2": {"ligipaas_a"}},
    )
    valem = K("x", aatom("ligipaas_a"))
    print(f"  Süsteem agendile x: {m.susteem('x')}  (refleksiivne={m.on_refleksiivne('x')})")
    print(f"  {valem_str(valem)} @ u1 = {kehtib(m, 'u1', valem)}"
          f"  aga ligipaas_a @ u1 = {kehtib(m, 'u1', aatom('ligipaas_a'))}")
    print("  => K-süsteemis võib agent EKSLIKULT 'teada' (uskuda) ligipääsu,")
    print("     mida tegelikult pole. T-aksioom (K_x f → f) keelaks selle.")


if __name__ == "__main__":
    jooksuta_testid()
