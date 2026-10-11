"""Recordatorio de Entregas - punto de entrada.

Uso rápido:
    python recordatorio.py                      # revisa y avisa (lo que corre la tarea programada)
    python recordatorio.py --dry-run            # solo muestra qué avisaría, sin enviar nada
    python recordatorio.py --probar-correo      # manda un correo de prueba
    python recordatorio.py --hoy 2026-10-03     # simula otra fecha (útil para probar)
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from logging.handlers import RotatingFileHandler
from pathlib import Path

from entregas import __version__
from entregas.config import Config
from entregas.core import Estado, agrupar, mensaje, proximas
from entregas.excel import leer_filas
from entregas.notify import aviso_escritorio, enviar_correo, enviar_prueba

log = logging.getLogger("entregas")


def configurar_logs(carpeta: Path) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s  %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S")
    archivo = RotatingFileHandler(carpeta / "recordatorio.log", maxBytes=500_000, backupCount=3, encoding="utf-8")
    archivo.setFormatter(fmt)
    log.addHandler(archivo)
    if sys.stdout is not None:  # con pythonw (sin ventana) no hay consola
        consola = logging.StreamHandler(sys.stdout)
        consola.setFormatter(logging.Formatter("%(message)s"))
        log.addHandler(consola)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Avisa cuando una orden de compra está por vencer.")
    p.add_argument("--dry-run", action="store_true", help="muestra los avisos sin enviarlos ni registrarlos")
    p.add_argument("--probar-correo", action="store_true", help="envía un correo de prueba y termina")
    p.add_argument("--hoy", help="simula esta fecha (AAAA-MM-DD)")
    p.add_argument("--excel", help="ruta del Excel (sobrescribe EXCEL_PATH)")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = p.parse_args(argv)

    raiz = Path(__file__).resolve().parent
    cfg = Config.desde_entorno(raiz)
    if args.excel:
        cfg.excel = Path(args.excel)
    configurar_logs(cfg.carpeta_datos)

    if args.probar_correo:
        if errores := cfg.problemas(revisar_correo=True):
            log.error("\n".join(errores))
            return 2
        enviar_prueba(cfg)
        return 0

    if errores := cfg.problemas(revisar_correo=cfg.correo_activo and not args.dry_run):
        log.error("Configuración incompleta:\n  - " + "\n  - ".join(errores))
        return 2

    hoy = date.fromisoformat(args.hoy) if args.hoy else date.today()

    try:
        filas, advertencias = leer_filas(cfg.excel)
    except Exception as exc:  # noqa: BLE001
        log.error("No pude leer el Excel: %s", exc)
        return 1
    for a in advertencias:
        log.warning(a)

    estado = Estado(cfg.carpeta_datos / "estado.json")
    cercanas = proximas(agrupar(filas), hoy, cfg.dias_aviso)
    nuevas = [(e, d) for e, d in cercanas if not estado.ya_avisada(e)]
    log.info("%s: %d filas, %d entregas en los próximos %d días, %d por avisar.",
             hoy, len(filas), len(cercanas), cfg.dias_aviso, len(nuevas))

    if not nuevas:
        return 0

    if args.dry_run:
        for e, d in nuevas:
            log.info("  * %s", mensaje(e, d))
        return 0

    ok_correo = ok_escritorio = False
    if cfg.correo_activo:
        try:
            enviar_correo(cfg, nuevas)
            ok_correo = True
        except Exception as exc:  # noqa: BLE001
            log.error("Falló el envío del correo (se reintentará en la próxima ejecución): %s", exc)
    if cfg.escritorio_activo:
        ok_escritorio = aviso_escritorio(nuevas)

    # Si el correo está activo, solo se da por avisado cuando el correo salió.
    if ok_correo if cfg.correo_activo else ok_escritorio:
        for e, _ in nuevas:
            estado.marcar(e, hoy)
        estado.limpiar(hoy)
        estado.guardar()
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
