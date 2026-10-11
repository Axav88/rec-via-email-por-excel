"""Configuración desde el archivo .env (sin dependencias externas)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

VERDADERO = {"1", "true", "yes", "si", "sí", "on"}


def cargar_env(ruta: Path) -> None:
    """Lee líneas CLAVE=valor de un .env y las pone en os.environ (sin pisar las ya definidas)."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8-sig").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def _bool(nombre: str, defecto: bool) -> bool:
    valor = os.environ.get(nombre)
    return defecto if valor is None else valor.strip().lower() in VERDADERO


@dataclass
class Config:
    excel: Path
    dias_aviso: int = 7
    correo_activo: bool = True
    escritorio_activo: bool = True
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    remitente: str = ""
    destinatarios: list[str] = field(default_factory=list)
    carpeta_datos: Path = Path("datos")

    @classmethod
    def desde_entorno(cls, raiz: Path) -> "Config":
        cargar_env(raiz / ".env")
        usuario = os.environ.get("SMTP_USER", "").strip()
        destinos = [d.strip() for d in os.environ.get("MAIL_TO", "").split(",") if d.strip()]
        return cls(
            excel=Path(os.environ.get("EXCEL_PATH", "").strip().strip('"')),
            dias_aviso=int(os.environ.get("DIAS_AVISO", "7")),
            correo_activo=_bool("AVISO_CORREO", True),
            escritorio_activo=_bool("AVISO_ESCRITORIO", True),
            smtp_host=os.environ.get("SMTP_HOST", "smtp.gmail.com").strip(),
            smtp_port=int(os.environ.get("SMTP_PORT", "587")),
            smtp_user=usuario,
            smtp_password=os.environ.get("SMTP_PASSWORD", "").replace(" ", ""),
            remitente=os.environ.get("MAIL_FROM", usuario).strip() or usuario,
            destinatarios=destinos or ([usuario] if usuario else []),
            carpeta_datos=raiz / "datos",
        )

    def problemas(self, revisar_correo: bool) -> list[str]:
        errores = []
        if not str(self.excel) or str(self.excel) == ".":
            errores.append("Falta EXCEL_PATH en el archivo .env")
        if revisar_correo:
            if not self.smtp_user:
                errores.append("Falta SMTP_USER en el archivo .env")
            if not self.smtp_password:
                errores.append("Falta SMTP_PASSWORD en el archivo .env")
        return errores
