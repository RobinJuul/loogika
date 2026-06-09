# Epistemiline mudelikontrollija — ligipääsukontroll

Ligipääsukontrolli poliitikate formaliseerimine epistemilise modaalloogikaga ning
võrdlus traditsiooniliste mudelitega RBAC ja ABAC.

**Tartu Ülikool – Loogika arvutiteaduses, projekt (2026).**
Autor: Robin Juul.

## Ülevaade

Projekt uurib, millised ligipääsukontrolli omadused on epistemilises
modaalloogikas loomulikult väljendatavad, kuid RBAC/ABAC raamistikes raskesti või
üldse mitte formaliseeritavad. Eelkõige agendi teadmised ressursside kohta ja
kõrgema astme teadmised (nt administraatori auditeerimiskohustus "administraator
teab, et arstil on ligipääs").

Artefakt koosneb kolmest osast:

1. **Juhtumiuuring** — haigla infosüsteemi ligipääsukontroll, formaliseeritud
   kolmel viisil (RBAC, ABAC, epistemiline modaalloogika Kripke struktuuriga).
2. **Mudelikontrollija** — Pythoni programm, mis kontrollib epistemilise valemi
   kehtivust antud Kripke mudeli maailmas.
3. **Võrdlustabel ja järeldused** — milliseid omadusi iga raamistik väljendab
   (vt tehniline kirjeldus).

Täielik teoreetiline taust, formaalne analüüs ja piirangud on eraldi failis
*tehniline kirjeldus* (esitatud Moodle'is).

## Failid

| Fail | Sisu |
|------|------|
| `mudelikontrollija.py` | Kripke mudel ja epistemilise valemi mudelikontroll (rekursiivne semantika). |
| `juhtumiuuring.py` | Haigla stsenaarium kolme formaliseeringuga + testjuhud + K/T/S4 demo. |

## Käivitamine

Eeldab Python 3.7+ (ainult standardteek, lisapakke pole vaja):

```bash
python3 juhtumiuuring.py
```

See ehitab haigla mudeli, tuvastab iga agendi seose süsteemiklassi (K / T / S4),
jooksutab testjuhud ja demonstreerib K-vs-T erinevust (uskumus vs teadmine).

## Näide: sisend ja väljund

Mudel defineeritakse Kripke struktuurina (maailmad, agentide ligipääsuseosed,
valuatsioon). Valem ehitatakse konstruktoritest, nt administraatori
auditeerimisomadus:

```python
from juhtumiuuring import ehita_mudel
from mudelikontrollija import kehtib, K, implies, aatom

m = ehita_mudel()
kehtib(m, "w1",
       K("admin", implies(aatom("raviarst"), K("arst", aatom("ligipaas_a")))))
# -> True
```

Väljundi väljavõte:

```
K_admin(raviarst → K_arstligipaas_a)  @ w1  =>  True
¬K_arstligipaas_o                     @ w1  =>  True   (privaatsus)
```

## Operaatorid

| Konstruktor | Tähendus | Valem |
|-------------|----------|-------|
| `aatom(p)` | aatomlause | p |
| `mitte(f)` | eitus | ¬f |
| `ja / voi / implies` | konnektiivid | ∧ ∨ → |
| `K(a, f)` | agent a teab f | K_a f |
| `M(a, f)` | a peab f võimalikuks | M_a f |

## Semantika

Epistemilise operaatori tõeväärtus Kripke mudelis M = (W, {R_a}, V):

```
M, w ⊨ K_a φ   ⟺   iga v korral: kui (w, v) ∈ R_a, siis M, v ⊨ φ.
```

Seose omadused määravad süsteemi: refleksiivsus annab T (K_a φ → φ, teadmine on
tõene), refleksiivsus + transitiivsus annab S4 (positiivne introspektsioon).

## Litsents

MIT — vt `LICENSE`.
