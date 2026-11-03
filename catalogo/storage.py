"""Escritura segura de archivos JSON (se usa para usuarios.json)."""

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from threading import RLock



_bloqueo = RLock()


@contextmanager
def editar_json(ruta, cargar):
    """Bloquea lectura/modificación y publica un archivo JSON de forma atómica."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with _bloqueo, ruta.with_suffix(".lock").open("a+b") as bloqueo:
        if os.name == "nt":
            import msvcrt
            bloqueo.seek(0)
            bloqueo.write(b"0")
            bloqueo.flush()
            bloqueo.seek(0)
            msvcrt.locking(bloqueo.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(bloqueo.fileno(), fcntl.LOCK_EX)
        try:
            datos = cargar()
            yield datos
            temporal = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=ruta.parent, delete=False) as archivo:
                    temporal = archivo.name
                    json.dump(datos, archivo, ensure_ascii=False, indent=2)
                    archivo.flush()
                    os.fsync(archivo.fileno())
                os.replace(temporal, ruta)
            finally:
                if temporal and os.path.exists(temporal):
                    os.unlink(temporal)
        finally:
            if os.name == "nt":
                bloqueo.seek(0)
                msvcrt.locking(bloqueo.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(bloqueo.fileno(), fcntl.LOCK_UN)

