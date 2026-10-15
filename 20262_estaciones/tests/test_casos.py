"""Casos oficiales de la guía (casos_ej_001_parte1/2/3). Ejecutar: python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from estaciones import (cargar_instancia, calcular_alcance, heuristica_base,
                        mejor_propuesta_exacta)

CASOS_P1 = [
    ("pequena", "L3", "accidente", 2800, [1, 2, 4, 6]),
    ("pequena", "L2", "hurto", 1500, [9, 10, 11, 12, 13]),
]
CASOS_P2 = [
    ("pequena", [("L1", "incendio")], 5500, {"hurto": 0, "accidente": 0, "incendio": 3}, 15),
    ("comuna", [("L05", "accidente"), ("L06", "hurto"), ("L08", "accidente"),
                ("L09", "incendio"), ("L13", "hurto"), ("L14", "hurto"), ("L15", "accidente")],
     11950, {"hurto": 486, "accidente": 296, "incendio": 31}, 1529),
]
CASO_P3 = ([("L1", "hurto"), ("L3", "accidente"), ("L4", "hurto")], 5400,
           {"hurto": 8, "accidente": 4, "incendio": 0}, 20)


class TestCasos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.al = {n: calcular_alcance(cargar_instancia(n)) for n in ("pequena", "comuna")}

    def test_parte1(self):
        for inst, lote, tipo, costo, ids in CASOS_P1:
            al = self.al[inst]
            self.assertEqual(al.costo[(lote, tipo)], costo)
            self.assertEqual(al.cubiertos[(lote, tipo)], ids)

    def test_parte2_base(self):
        for inst, est, costo, casos, valor in CASOS_P2:
            p = heuristica_base(self.al[inst])
            self.assertEqual(p.estaciones, est)
            self.assertEqual((p.costo_total, p.casos_cubiertos, p.valor), (costo, casos, valor))

    def test_parte3_exacto_pequena(self):
        p, _ = mejor_propuesta_exacta(self.al["pequena"])
        est, costo, casos, valor = CASO_P3
        self.assertEqual(p.estaciones, est)
        self.assertEqual((p.costo_total, p.casos_cubiertos, p.valor), (costo, casos, valor))


if __name__ == "__main__":
    unittest.main()
