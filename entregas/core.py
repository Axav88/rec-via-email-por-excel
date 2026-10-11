"""Lógica pura (sin red, sin Excel): agrupar, filtrar por ventana de aviso y recordar qué ya se avisó."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

DIAS_SEMANA = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
SIN_OC = "(sin número)"


@dataclass(frozen=True)
class Fila:
    """Un renglón del Excel (un artículo de una orden)."""

    oc: str
    cliente: str
    fecha: date
    piezas: int
    descripcion: str


@dataclass(frozen=True)
class Entrega:
    """Una orden de compra con su fecha de entrega (varios renglones se agrupan en una)."""

    oc: str
    cliente: str
    fecha: date
    piezas: int
    descripciones: tuple[str, ...]

    @property
    def clave(self) -> str:
        """Identificador estable. Si cambia la fecha de entrega, se considera un aviso nuevo."""
        base = f"{self.oc}|{self.cliente.lower()}|{self.fecha.isoformat()}"
        if self.oc == SIN_OC:
            base += "|" + "|".join(self.descripciones)
        return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def agrupar(filas: list[Fila]) -> list[Entrega]:
    """Junta los renglones con la misma orden + cliente + fecha en una sola entrega."""
    grupos: dict[tuple, list[Fila]] = {}
    for f in filas:
        extra = f.descripcion if f.oc == SIN_OC else ""
        grupos.setdefault((f.oc, f.cliente.lower(), f.fecha, extra), []).append(f)

    entregas = []
    for items in grupos.values():
        primero = items[0]
        descripciones = tuple(dict.fromkeys(i.descripcion for i in items if i.descripcion))
        entregas.append(
            Entrega(primero.oc, primero.cliente, primero.fecha, sum(i.piezas for i in items), descripciones)
        )
    return entregas


def proximas(entregas: list[Entrega], hoy: date, dias: int = 7) -> list[tuple[Entrega, int]]:
    """Entregas que vencen entre hoy y `dias` días. Devuelve (entrega, días_restantes) ordenadas.

    Se usa un rango (no "exactamente 7 días") para que, si la compu estuvo apagada
    ese día, el aviso salga igual la próxima vez que se encienda.
    """
    out = [(e, (e.fecha - hoy).days) for e in entregas]
    out = [(e, d) for e, d in out if 0 <= d <= dias]
    return sorted(out, key=lambda x: (x[1], x[0].cliente.lower(), x[0].oc))


def cuando(dias: int, fecha: date) -> str:
    f = f"{DIAS_SEMANA[fecha.weekday()]} {fecha:%d/%m/%Y}"
    if dias == 0:
        return f"HOY ({f})"
    if dias == 1:
        return f"mañana ({f})"
    if dias == 7:
        return f"la próxima semana ({f})"
    return f"en {dias} días ({f})"


def mensaje(e: Entrega, dias: int) -> str:
    return f'La orden de compra número "{e.oc}" del cliente "{e.cliente}" vence {cuando(dias, e.fecha)}.'


class Estado:
    """Bitácora en JSON de las entregas ya avisadas, para no repetir correos."""

    def __init__(self, ruta: Path):
        self.ruta = Path(ruta)
        try:
            self._datos: dict = json.loads(self.ruta.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            self._datos = {}

    def ya_avisada(self, e: Entrega) -> bool:
        return e.clave in self._datos

    def marcar(self, e: Entrega, hoy: date) -> None:
        self._datos[e.clave] = {
            "oc": e.oc,
            "cliente": e.cliente,
            "entrega": e.fecha.isoformat(),
            "avisado": hoy.isoformat(),
        }

    def limpiar(self, hoy: date, dias: int = 90) -> None:
        limite = (hoy - timedelta(days=dias)).isoformat()
        self._datos = {k: v for k, v in self._datos.items() if v.get("entrega", "") >= limite}

    def guardar(self) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.ruta.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._datos, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.ruta)
