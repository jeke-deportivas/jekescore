"""
JekeScore - Scraper minimalista para datos de tiros de Sofascore.

Uso básico:
    from jekescore import get_shotmap

    shots = get_shotmap(match_id=12557619)
    for shot in shots:
        print(f"{shot.player.name}: ({shot.x}, {shot.y}) - {shot.shot_type}")
"""

from jekescore.client import JekeScoreClient, get_shotmap
from jekescore.models import Coordinates, DrawCoordinates, Player, Shot, ShotMap

__version__ = "0.1.0"
__all__ = [
    "JekeScoreClient",
    "get_shotmap",
    "Shot",
    "ShotMap",
    "Player",
    "Coordinates",
    "DrawCoordinates",
]
