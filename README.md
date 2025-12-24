[![CI](https://github.com/jeke-deportivas/jekescore/actions/workflows/ci.yml/badge.svg)](https://github.com/jeke-deportivas/jekescore/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/jekescore)](https://pypi.org/project/jekescore/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

# JekeScore

Scraper minimalista para obtener datos de tiros (shotmap) de Sofascore.

## Requisitos

- Python 3.13+
- pyenv (recomendado)

## Instalación

### 1. Configurar Python con pyenv

```bash
# Instalar Python 3.13.11
pyenv install 3.13.11

# Clonar el repositorio
git clone https://github.com/jekedelasdeportivas/jekescore.git
cd jekescore

# pyenv usará automáticamente la versión del archivo .python-version
python --version  # Debería mostrar 3.13.11
```

### 2. Crear entorno virtual

```bash
# Crear venv
python -m venv venv

# Activar venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -e ".[dev]"
```

## Uso rápido

```python
from jekescore import get_shotmap

# Obtener tiros de un partido
shots = get_shotmap(match_id=12557619)

# Iterar sobre los tiros
for shot in shots:
    print(f"{shot.player.name}: ({shot.x}, {shot.y}) - {shot.shot_type}")

# Filtrar solo goles
for goal in shots.goals:
    print(f"GOL de {goal.player.name} min {goal.time}'")

# Tiros por equipo
print(f"Tiros local: {len(shots.home_shots)}")
print(f"Tiros visitante: {len(shots.away_shots)}")
```

## Configuración

### Plataforma

Por defecto usa User-Agent de Windows. Puedes cambiarlo:

```python
from jekescore import get_shotmap

# Para macOS
shots = get_shotmap(match_id=12557619, platform="macos")

# Para Linux
shots = get_shotmap(match_id=12557619, platform="linux")
```

### Cookies (si hay problemas de acceso)

Si Sofascore bloquea las peticiones, puedes usar cookies de tu navegador:

```python
from jekescore import JekeScoreClient

# Opción 1: Diccionario de cookies
client = JekeScoreClient(cookies={"session": "abc123"})

# Opción 2: Archivo JSON (exportado de Selenium o DevTools)
client = JekeScoreClient(cookies_file="cookies.json")

shots = client.get_shotmap(12557619)
```

## Estructura de datos

### Shot

Cada tiro contiene:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | int | ID único del tiro |
| `time` | int | Minuto del partido |
| `player` | Player | Jugador que disparó |
| `x`, `y` | float | Coordenadas del disparo |
| `shot_type` | str | `goal`, `save`, `miss`, `block` |
| `situation` | str | `corner`, `assisted`, `set-piece`, `fast-break` |
| `body_part` | str | `head`, `right-foot`, `left-foot` |
| `is_goal` | bool | True si fue gol |

### Coordenadas

Las coordenadas están normalizadas:
- `x`: 0-100 (ancho del campo, 0 = portería rival)
- `y`: 0-100 (alto del campo)

## Obtener match_id

El `match_id` está en la URL del partido:

```
https://www.sofascore.com/football/match/team1-team2/ABC#id:12557619
                                                          ^^^^^^^^
                                                          match_id
```

También puedes extraerlo programáticamente:

```python
from jekescore import JekeScoreClient

url = "https://www.sofascore.com/football/match/barcelona-atalanta/OgbsKgb#id:12557619"
match_id = JekeScoreClient.get_match_id_from_url(url)
print(match_id)  # 12557619
```

## Desarrollo

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar linter
ruff check .

# Ejecutar formatter
ruff format .

# Ejecutar type checker
pyright .

# Ejecutar tests
pytest

# Ejecutar tests con coverage
pytest --cov
```

## Licencia

MIT
