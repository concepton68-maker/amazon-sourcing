"""Document du bon de commande (PDF et Excel) — [RM-AMZ-127, 128].

PDF écrit sans bibliothèque : police standard Helvetica, codage WinAnsi (accents français et « € »), A4.
Les libellés sont ceux du document envoyé au fournisseur (français).
"""
from __future__ import annotations

import io
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional
from zoneinfo import ZoneInfo

L = {"titre": "BON DE COMMANDE", "date": "Date", "acheteur": "Acheteur", "fournisseur": "Fournisseur",
     "livraison": "Adresse de livraison", "tva": "TVA intracommunautaire", "ref": "Réf. fournisseur",
     "designation": "Désignation", "quantite": "Quantité", "prix": "Prix unitaire", "total": "Total",
     "total_bon": "Total du bon", "montants": "Montants en", "a_completer": "Société à compléter",
     "page": "Page", "tel": "Tél."}


def _q(x: Decimal, n: int = 2) -> Decimal:
    return x.quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP)


def montant(x: Decimal) -> str:
    """1 234,50 (deux décimales)."""
    s = f"{_q(x):,.2f}"
    return s.replace(",", " ").replace(".", ",")


def prix(x: Decimal) -> str:
    """Prix unitaire : 2 à 4 décimales, sans zéros inutiles au-delà de 2."""
    s = f"{_q(x, 4):,.4f}".replace(",", " ")
    ent, dec = s.split(".")
    dec = dec.rstrip("0").ljust(2, "0")
    return f"{ent},{dec}"


def lignes_document(bon, codes: Optional[dict] = None) -> list[dict]:
    """[RM-AMZ-128] Lignes en unités du fournisseur ; l'ASIN et la prévision restent internes."""
    out = []
    for l in bon.lignes:
        k = max(1, l.unites_lot or 1)
        out.append({"ref": l.code or (codes or {}).get(l.asin) or "", "designation": l.designation or "",
                    "quantite": l.quantite * k, "prix": l.prix_unitaire / k, "total": l.prix_unitaire * l.quantite})
    return out


def entete(bon, fournisseur, societe: dict, quand: Optional[datetime] = None) -> dict:
    quand = quand or datetime.now(ZoneInfo("Europe/Paris"))
    s = societe or {}
    acheteur = [s["raison_sociale"]] if s.get("raison_sociale") else [L["a_completer"]]
    acheteur += [x for x in (s.get("adresse") or "").splitlines() if x.strip()]
    if s.get("tva_intra"):
        acheteur.append(f"{L['tva']} : {s['tva_intra']}")
    acheteur += [x for x in (s.get("courriel"), (f"{L['tel']} {s['telephone']}" if s.get("telephone") else None)) if x]
    four = [fournisseur.nom] + [x for x in (fournisseur.courriel, fournisseur.pays) if x]
    livraison = [x for x in (s.get("adresse_livraison") or s.get("adresse") or "").splitlines() if x.strip()]
    if livraison and s.get("raison_sociale"):
        livraison = [s["raison_sociale"]] + livraison
    return {"reference": bon.reference, "date": quand.strftime("%d/%m/%Y"), "acheteur": acheteur,
            "fournisseur": four, "livraison": livraison, "devise": fournisseur.devise,
            "complete": bool(s.get("raison_sociale") and s.get("adresse"))}


# ------------------------------------------------------------------------------------------------------- PDF
_LARG = {" ": 278, ",": 278, ".": 278, "-": 333, ":": 278, "/": 278, "(": 333, ")": 333, "'": 191, "°": 400,
         "€": 556, "i": 222, "l": 222, "j": 222, "t": 278, "f": 278, "r": 333, "I": 278, "m": 833, "w": 722,
         "M": 833, "W": 944}


def largeur(texte: str, taille: float) -> float:
    total = 0
    for ch in texte:
        if ch in _LARG:
            total += _LARG[ch]
        elif ch.isdigit():
            total += 556
        elif ch.isupper():
            total += 667
        else:
            total += 556
    return total * taille / 1000


def _couper(texte: str, taille: float, maxi: float) -> str:
    if largeur(texte, taille) <= maxi:
        return texte
    while texte and largeur(texte + "…", taille) > maxi:
        texte = texte[:-1]
    return texte.rstrip() + "…"


def _echapper(texte: str) -> bytes:
    b = texte.encode("cp1252", errors="replace")
    return b.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


class _Page:
    def __init__(self):
        self.ops: list[bytes] = []

    def texte(self, x: float, y: float, t: str, taille: float = 9, gras: bool = False, droite: bool = False):
        if droite:
            x -= largeur(t, taille)
        self.ops.append(b"BT /%s %.1f Tf %.2f %.2f Td (" % (b"F2" if gras else b"F1", taille, x, y)
                        + _echapper(t) + b") Tj ET")

    def trait(self, x1: float, y1: float, x2: float, y2: float, epaisseur: float = 0.5):
        self.ops.append(b"%.2f w %.2f %.2f m %.2f %.2f l S" % (epaisseur, x1, y1, x2, y2))

    def fond(self, x: float, y: float, w: float, h: float, gris: float = 0.93):
        self.ops.append(b"q %.2f g %.2f %.2f %.2f %.2f re f Q" % (gris, x, y, w, h))


def _assembler(pages: list[_Page]) -> bytes:
    objets: list[bytes] = []
    n_pages = len(pages)
    # 1 catalogue, 2 pages, 3 F1, 4 F2, puis (page, contenu) par page
    kids = " ".join(f"{5 + 2 * i} 0 R" for i in range(n_pages)).encode()
    objets.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objets.append(b"<< /Type /Pages /Kids [" + kids + b"] /Count %d >>" % n_pages)
    objets.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    objets.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    for i, p in enumerate(pages):
        flux = b"\n".join(p.ops)
        objets.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                      b"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents %d 0 R >>" % (6 + 2 * i))
        objets.append(b"<< /Length %d >>\nstream\n" % len(flux) + flux + b"\nendstream")
    sortie = io.BytesIO()
    sortie.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    positions = []
    for i, o in enumerate(objets, start=1):
        positions.append(sortie.tell())
        sortie.write(b"%d 0 obj\n" % i + o + b"\nendobj\n")
    xref = sortie.tell()
    sortie.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objets) + 1))
    for pos in positions:
        sortie.write(b"%010d 00000 n \n" % pos)
    sortie.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objets) + 1, xref))
    return sortie.getvalue()


def pdf(bon, fournisseur, societe: dict, codes: Optional[dict] = None, quand: Optional[datetime] = None) -> bytes:
    """[RM-AMZ-128]"""
    e = entete(bon, fournisseur, societe, quand)
    lignes = lignes_document(bon, codes)
    G, D = 40, 555
    cols = [(G, L["ref"]), (G + 95, L["designation"]), (D - 175, L["quantite"]), (D - 85, L["prix"]), (D, L["total"])]
    pages: list[_Page] = []

    def nouvelle(premiere: bool) -> tuple[_Page, float]:
        p = _Page()
        pages.append(p)
        y = 800
        p.texte(G, y, L["titre"], 16, True)
        p.texte(D, y, e["reference"], 14, True, droite=True)
        y -= 18
        p.texte(D, y, f"{L['date']} : {e['date']}", 9, droite=True)
        if premiere:
            y -= 22
            blocs = [(G, L["acheteur"], e["acheteur"]), (G + 260, L["fournisseur"], e["fournisseur"])]
            bas = y
            for x, titre, contenu in blocs:
                yy = y
                p.texte(x, yy, titre.upper(), 7.5, True)
                for t in contenu[:8]:
                    yy -= 12
                    p.texte(x, yy, _couper(t, 9, 250), 9)
                bas = min(bas, yy)
            y = bas - 20
            if e["livraison"]:
                p.texte(G, y, L["livraison"].upper(), 7.5, True)
                for t in e["livraison"][:6]:
                    y -= 12
                    p.texte(G, y, _couper(t, 9, 500), 9)
                y -= 20
        p.fond(G - 4, y - 5, D - G + 8, 17)
        for i, (x, t) in enumerate(cols):
            p.texte(x, y, t, 8.5, True, droite=i >= 2)
        return p, y - 18

    page, y = nouvelle(True)
    total = Decimal(0)
    for l in lignes:
        if y < 80:
            page, y = nouvelle(False)
        page.texte(cols[0][0], y, _couper(l["ref"], 9, 90), 9)
        page.texte(cols[1][0], y, _couper(l["designation"], 9, D - 175 - 55 - cols[1][0]), 9)
        page.texte(cols[2][0], y, f"{l['quantite']:,}".replace(",", " "), 9, droite=True)
        page.texte(cols[3][0], y, prix(l["prix"]), 9, droite=True)
        page.texte(cols[4][0], y, montant(l["total"]), 9, droite=True)
        page.trait(G - 4, y - 5, D + 4, y - 5, 0.3)
        total += l["total"]
        y -= 17
    if y < 90:
        page, y = nouvelle(False)
    y -= 6
    page.texte(D - 85, y, L["total_bon"], 10, True, droite=True)
    page.texte(D, y, f"{montant(total)} {e['devise']}", 10, True, droite=True)
    y -= 14
    page.texte(D, y, f"{L['montants']} {e['devise']}", 8, droite=True)
    for i, p in enumerate(pages, start=1):
        p.texte(D, 30, f"{L['page']} {i} / {len(pages)}", 8, droite=True)
        p.texte(G, 30, e["reference"], 8)
    return _assembler(pages)


# ------------------------------------------------------------------------------------------------------ Excel
def excel(bon, fournisseur, societe: dict, codes: Optional[dict] = None, quand: Optional[datetime] = None) -> bytes:
    """[RM-AMZ-128] Même contenu que le PDF, une feuille."""
    from openpyxl import Workbook
    from openpyxl.styles import Font
    e = entete(bon, fournisseur, societe, quand)
    wb = Workbook()
    ws = wb.active
    ws.title = e["reference"]
    ws.append([L["titre"], e["reference"]])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([L["date"], e["date"]])
    ws.append([])
    ws.append([L["acheteur"], " · ".join(e["acheteur"])])
    ws.append([L["fournisseur"], " · ".join(e["fournisseur"])])
    if e["livraison"]:
        ws.append([L["livraison"], " · ".join(e["livraison"])])
    ws.append([])
    ws.append([L["ref"], L["designation"], L["quantite"], L["prix"], L["total"]])
    for c in ws[ws.max_row]:
        c.font = Font(bold=True)
    total = Decimal(0)
    for l in lignes_document(bon, codes):
        ws.append([l["ref"], l["designation"], l["quantite"], float(_q(l["prix"], 4)), float(_q(l["total"]))])
        total += l["total"]
    ws.append([])
    ws.append(["", "", "", L["total_bon"], float(_q(total))])
    ws.append(["", "", "", L["montants"], e["devise"]])
    for col, w in zip("ABCDE", (18, 60, 12, 14, 14)):
        ws.column_dimensions[col].width = w
    sortie = io.BytesIO()
    wb.save(sortie)
    return sortie.getvalue()
