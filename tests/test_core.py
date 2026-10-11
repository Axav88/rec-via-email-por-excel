import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook

from entregas.core import SIN_OC, Entrega, Estado, Fila, agrupar, mensaje, proximas
from entregas.excel import leer_filas

HOY = date(2026, 10, 3)


def fila(oc="123", cliente="acme", fecha=date(2026, 10, 10), piezas=1, desc="tornillo"):
    return Fila(oc, cliente, fecha, piezas, desc)


class TestLogica(unittest.TestCase):
    def test_agrupa_renglones_de_la_misma_orden(self):
        e = agrupar([fila(piezas=2, desc="a"), fila(piezas=3, desc="b"), fila(oc="999")])
        self.assertEqual(len(e), 2)
        grande = next(x for x in e if x.oc == "123")
        self.assertEqual(grande.piezas, 5)
        self.assertEqual(grande.descripciones, ("a", "b"))

    def test_misma_orden_con_dos_fechas_son_dos_entregas(self):
        e = agrupar([fila(fecha=date(2026, 10, 10)), fila(fecha=date(2026, 10, 20))])
        self.assertEqual(len(e), 2)

    def test_ventana_de_aviso(self):
        e = agrupar([fila(fecha=HOY.replace(day=2)), fila(oc="a", fecha=HOY),
                     fila(oc="b", fecha=date(2026, 10, 10)), fila(oc="c", fecha=date(2026, 10, 11))])
        cerca = {x.oc: d for x, d in proximas(e, HOY, 7)}
        self.assertEqual(cerca, {"a": 0, "b": 7})  # ayer y dentro de 8 días quedan fuera

    def test_mensaje_proxima_semana(self):
        e = agrupar([fila(oc="4505", cliente="arca")])[0]
        self.assertEqual(
            mensaje(e, 7),
            'La orden de compra número "4505" del cliente "arca" vence la próxima semana (sábado 10/10/2026).',
        )

    def test_orden_sin_numero_no_mezcla_articulos(self):
        e = agrupar([fila(oc=SIN_OC, desc="a"), fila(oc=SIN_OC, desc="b")])
        self.assertEqual(len(e), 2)
        self.assertNotEqual(e[0].clave, e[1].clave)

    def test_estado_evita_duplicados_y_persiste(self):
        e = agrupar([fila()])[0]
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "estado.json"
            s = Estado(ruta)
            self.assertFalse(s.ya_avisada(e))
            s.marcar(e, HOY)
            s.guardar()
            self.assertTrue(Estado(ruta).ya_avisada(e))

    def test_cambiar_fecha_genera_aviso_nuevo(self):
        a, b = Entrega("1", "x", date(2026, 10, 10), 1, ()), Entrega("1", "x", date(2026, 10, 12), 1, ())
        self.assertNotEqual(a.clave, b.clave)


class TestExcel(unittest.TestCase):
    def test_lee_encabezados_con_espacios_y_formatos_mixtos(self):
        wb = Workbook()
        ws = wb.active
        ws.append(["ORDEN DE COMPRA", "CLIENTE", "CANT/PZS", "DESCRIPCION", "ENTREGA "])  # espacio al final
        ws.append([4505536481, "arca", 2, "rodillo", datetime(2026, 10, 10)])
        ws.append([None, "kia", 1, "cadena", "11/10/2026"])
        ws.append([555.0, "otro", 1, "x", "no es fecha"])
        ws.append([1, "vacío", 1, "x", None])
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "t.xlsx"
            wb.save(ruta)
            filas, avisos = leer_filas(ruta)
        self.assertEqual([f.oc for f in filas], ["4505536481", SIN_OC])
        self.assertEqual(filas[1].fecha, date(2026, 10, 11))
        self.assertEqual(len(avisos), 1)


if __name__ == "__main__":
    unittest.main()
