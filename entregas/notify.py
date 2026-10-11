"""Canales de aviso: correo (SMTP) y notificación de escritorio de Windows."""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage
from html import escape

from .config import Config
from .core import Entrega, mensaje

log = logging.getLogger("entregas")

Item = tuple[Entrega, int]


def _asunto(items: list[Item]) -> str:
    n = len(items)
    return f"Recordatorio: {n} entrega próxima" if n == 1 else f"Recordatorio: {n} entregas próximas"


def _texto(items: list[Item]) -> str:
    lineas = ["Hola, estas órdenes de compra están por vencer:", ""]
    for e, d in items:
        lineas.append(f"- {mensaje(e, d)}")
        lineas.append(f"    {e.piezas} pza(s): " + "; ".join(e.descripciones)[:200])
    lineas += ["", "Mensaje automático de Recordatorio de Entregas."]
    return "\n".join(lineas)


def _html(items: list[Item]) -> str:
    filas = ""
    for e, d in items:
        color = "#c0392b" if d <= 2 else "#e67e22" if d <= 4 else "#2c7be5"
        filas += (
            f'<tr><td style="padding:10px 12px;border-bottom:1px solid #eee;border-left:4px solid {color}">'
            f"{escape(mensaje(e, d))}<br>"
            f'<span style="color:#777;font-size:12px">{e.piezas} pza(s): '
            f'{escape("; ".join(e.descripciones)[:160])}</span></td></tr>'
        )
    return (
        '<div style="font-family:Segoe UI,Arial,sans-serif;max-width:640px">'
        '<h2 style="margin:0 0 12px">Entregas por vencer</h2>'
        f'<table style="width:100%;border-collapse:collapse;font-size:14px">{filas}</table>'
        '<p style="color:#999;font-size:11px">Mensaje automático de Recordatorio de Entregas.</p></div>'
    )


def enviar_correo(cfg: Config, items: list[Item]) -> None:
    msg = EmailMessage()
    msg["Subject"] = _asunto(items)
    msg["From"] = cfg.remitente
    msg["To"] = ", ".join(cfg.destinatarios)
    msg.set_content(_texto(items))
    msg.add_alternative(_html(items), subtype="html")
    _smtp_enviar(cfg, msg)


def enviar_prueba(cfg: Config) -> None:
    msg = EmailMessage()
    msg["Subject"] = "Prueba - Recordatorio de Entregas"
    msg["From"] = cfg.remitente
    msg["To"] = ", ".join(cfg.destinatarios)
    msg.set_content("Si lees esto, el correo quedó bien configurado.")
    _smtp_enviar(cfg, msg)


def _smtp_enviar(cfg: Config, msg: EmailMessage) -> None:
    contexto = ssl.create_default_context()
    if cfg.smtp_port == 465:
        with smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, context=contexto, timeout=30) as s:
            s.login(cfg.smtp_user, cfg.smtp_password)
            s.send_message(msg)
    else:
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=30) as s:
            s.starttls(context=contexto)
            s.login(cfg.smtp_user, cfg.smtp_password)
            s.send_message(msg)
    log.info("Correo enviado a %s", msg["To"])


def aviso_escritorio(items: list[Item]) -> bool:
    """Notificación nativa de Windows (necesita `pip install winotify`). Devuelve True si salió."""
    try:
        from winotify import Notification
    except ImportError:
        log.warning("Notificación de escritorio omitida: winotify no está instalado (solo Windows).")
        return False
    try:
        visibles = [mensaje(e, d) for e, d in items[:3]]
        if len(items) > 3:
            visibles.append(f"... y {len(items) - 3} más.")
        titulo = "Entrega próxima" if len(items) == 1 else f"{len(items)} entregas próximas"
        Notification(
            app_id="Recordatorio de Entregas", title=titulo, msg="\n".join(visibles)[:250], duration="long"
        ).show()
        return True
    except Exception as exc:  # noqa: BLE001 - un fallo del aviso no debe tumbar el programa
        log.warning("No pude mostrar la notificación: %s", exc)
        return False
