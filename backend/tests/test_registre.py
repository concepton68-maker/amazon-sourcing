"""Le registre des règles et les tests restent alignés : toute règle « codée »
cite des tests qui existent réellement."""
import ast
import pathlib
import re
import unittest

RACINE = pathlib.Path(__file__).resolve().parents[2]
REGISTRE = RACINE / "docs" / "regles" / "registre.md"


def tests_existants() -> set[str]:
    noms = set()
    for f in pathlib.Path(__file__).parent.glob("test_*.py"):
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_"):
                noms.add(n.name)
    return noms


class TestRegistre(unittest.TestCase):
    def test_regles_codees_ont_leurs_tests(self):
        existants = tests_existants()
        lignes = [l for l in REGISTRE.read_text(encoding="utf-8").splitlines() if l.startswith("| RM-AMZ-")]
        self.assertTrue(lignes, "registre vide")
        for ligne in lignes:
            cols = [c.strip() for c in ligne.strip("|").split("|")]
            num, tests, etat = cols[0], cols[5], cols[6]
            if etat != "codé":
                continue
            for t in re.findall(r"`(test_\w+)`", tests):
                with self.subTest(regle=num, test=t):
                    self.assertIn(t, existants, f"{num} cite {t}, introuvable")


if __name__ == "__main__":
    unittest.main()
