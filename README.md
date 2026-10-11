<div align="center">

# 📦 Recordatorio de Entregas

**Te avisa por correo y con una notificación de Windows cuando una orden de compra está por vencer.**

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![Plataforma](https://img.shields.io/badge/Windows-0078D4?logo=windows&logoColor=white)
![Licencia](https://img.shields.io/badge/licencia-MIT-green)

</div>

> *La orden de compra número "4505536481" del cliente "arca zapopan" vence la próxima semana (domingo 25/10/2026).*

Lee tu Excel de pedidos, busca la columna **ENTREGA** y, cuando falta una semana o menos, manda **un solo correo resumen** con todas las órdenes por vencer. No necesita servidor, no cuesta nada y no sube tus datos a ningún lado.

## Q hace

-  **Correo** con resumen en HTML colores según urgencia rojo/azul +  **notificación nativa de Windows**.
- **Validación: No repite avisos**: guarda qué ya avisó. Si cambias la fecha de entrega, avisa de nuevo!!!.
-  **Aguanta compus apagadas**: avisa en un rango (≤ 7 días), no "exactamente 7 días antes", así que si ese día no se prendió la compu, avisa en cuanto se prenda.
-  **Tolerante con el Excel**: encuentra las columnas por nombre (da igual su posición), acepta fechas como fecha real o texto, funciona aunque el archivo esté abierto, y agrupa varios renglones de una misma orden en un solo aviso.
-  **Reintenta solo** si el correo falla (sin internet, por ejemplo).
-  Modo `--dry-run` para probar sin enviar nada.

##  Instalación (Windows)

Necesitas [Python 3.10+](https://www.python.org/downloads/) (marca *"Add Python to PATH"* al instalar).

```powershell
git clone https://github.com/TU_USUARIO/recordatorio-entregas.git
cd recordatorio-entregas
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
notepad .env
```

### Configurar el correo (Gmail)

1. Usa (o crea) una cuenta de Gmail para enviar los avisos.
2. Activa la **verificación en dos pasos** y genera una **contraseña de aplicación** en <https://myaccount.google.com/apppasswords>.
3. Pega esa contraseña en `SMTP_PASSWORD` dentro de `.env`, y pon en `MAIL_TO` el correo que recibirá los avisos.

Prueba que funcione:

```powershell
.venv\Scripts\python recordatorio.py --probar-correo
.venv\Scripts\python recordatorio.py --dry-run
```

### Que corra solo

```powershell
powershell -ExecutionPolicy Bypass -File scripts\instalar_tarea.ps1
```

Crea una tarea programada que se ejecuta **al iniciar sesión** y **todos los días a las 9:00** (si la compu estaba apagada, corre en cuanto se pueda). Si marca "acceso denegado", abre PowerShell como administrador. Para quitarla: `scripts\desinstalar_tarea.ps1`.

##  Configuración (`.env`)

| Variable | Qué hace | Por defecto |
|---|---|---|
| `EXCEL_PATH` | Ruta del Excel de pedidos | — |
| `DIAS_AVISO` | Días de anticipación | `7` |
| `AVISO_CORREO` / `AVISO_ESCRITORIO` | Activar canales (`si`/`no`) | `si` |
| `SMTP_HOST` / `SMTP_PORT` | Servidor de correo | `smtp.gmail.com` / `587` |
| `SMTP_USER` / `SMTP_PASSWORD` | Cuenta que envía | — |
| `MAIL_TO` | Destinatarios (separados por coma) | `SMTP_USER` |

##  Formato del Excel

Solo se necesitan estos encabezados (mayúsculas, acentos y espacios extra no importan):

| Columna | Uso |
|---|---|
| `ENTREGA` | **Obligatoria.** Fecha límite |
| `CLIENTE` | **Obligatoria** |
| `ORDEN DE COMPRA` | Opcional (si falta, el aviso dice "(sin número)") |
| `CANT/PZS`, `DESCRIPCION` | Opcionales, salen como detalle en el correo |

##  Estructura

```
recordatorio.py        # punto de entrada (CLI)
entregas/
  core.py              # lógica pura: agrupar, ventana de aviso, estado
  excel.py             # lectura del Excel
  notify.py            # correo SMTP + notificación de Windows
  config.py            # lectura del .env
scripts/               # instalar/desinstalar la tarea programada
tests/                 # pruebas (python -m unittest discover -s tests)
```

##  Tests

```powershell
python -m unittest discover -s tests -v
python recordatorio.py --dry-run --hoy 2026-10-18   # simula otra fecha
```

##  Privacidad

El Excel se lee localmente y nunca se sube a ningún lado. 

## Ideas a futuro

- Aviso por WhatsApp o Telegram.
- Empaquetar como `.exe` con PyInstaller para no instalar Python.

##  Licencia

[MIT](LICENSE)
