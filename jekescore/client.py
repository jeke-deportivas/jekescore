"""Cliente HTTP para Sofascore."""

import json
import re
from pathlib import Path

import requests

from jekescore.models import (
    Coordinates,
    DrawCoordinates,
    Player,
    Shot,
    ShotMap,
)

# User-Agents por plataforma
USER_AGENTS = {
    "windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "macos": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "linux": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
}

DEFAULT_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "es,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


class JekeScoreClient:
    """Cliente para obtener datos de Sofascore."""

    BASE_URL = "https://www.sofascore.com/api/v1"

    def __init__(
        self,
        cookies: dict[str, str] | None = None,
        cookies_file: str | None = None,
        user_agent: str | None = None,
        platform: str = "windows",
    ):
        """
        Inicializa el cliente.

        Args:
            cookies: Diccionario de cookies para autenticación.
            cookies_file: Ruta a archivo JSON con cookies (formato de Chrome DevTools).
            user_agent: User-Agent personalizado. Si no se provee, usa uno según platform.
            platform: Plataforma para User-Agent automático: "windows", "macos", "linux".
        """
        self.session = requests.Session()

        # Configurar User-Agent
        if user_agent:
            ua = user_agent
        else:
            ua = USER_AGENTS.get(platform.lower(), USER_AGENTS["windows"])

        headers = {**DEFAULT_HEADERS, "User-Agent": ua}
        self.session.headers.update(headers)

        if cookies_file:
            self._load_cookies_from_file(cookies_file)
        elif cookies:
            self.session.cookies.update(cookies)

    def _load_cookies_from_file(self, filepath: str) -> None:
        """Carga cookies desde un archivo JSON."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Archivo de cookies no encontrado: {filepath}")

        with open(path) as f:
            cookies_data = json.load(f)

        # Soporta formato de Selenium (lista) o diccionario simple
        if isinstance(cookies_data, list):
            for cookie in cookies_data:
                self.session.cookies.set(cookie["name"], cookie["value"])
        else:
            self.session.cookies.update(cookies_data)

    def _parse_shot(self, data: dict) -> Shot:
        """Convierte un diccionario de tiro a modelo Shot."""
        player_data = data.get("player", {})
        player = Player(
            id=player_data.get("id", 0),
            name=player_data.get("name", ""),
            short_name=player_data.get("shortName"),
            position=player_data.get("position"),
            jersey_number=player_data.get("jerseyNumber"),
        )

        gk_data = data.get("goalkeeper")
        goalkeeper = None
        if gk_data:
            goalkeeper = Player(
                id=gk_data.get("id", 0),
                name=gk_data.get("name", ""),
                short_name=gk_data.get("shortName"),
                position=gk_data.get("position"),
                jersey_number=gk_data.get("jerseyNumber"),
            )

        player_coords = data.get("playerCoordinates", {})
        goal_coords = data.get("goalMouthCoordinates", {})
        block_coords = data.get("blockCoordinates")

        draw_data = data.get("draw")
        draw = None
        if draw_data:
            draw = DrawCoordinates(
                start=Coordinates(**draw_data.get("start", {"x": 0, "y": 0})),
                end=Coordinates(**draw_data.get("end", {"x": 0, "y": 0})),
                goal=Coordinates(**draw_data.get("goal", {"x": 0, "y": 0})),
                block=Coordinates(**draw_data["block"]) if draw_data.get("block") else None,
            )

        return Shot(
            id=data.get("id", 0),
            time=data.get("time", 0),
            time_seconds=data.get("timeSeconds", 0),
            is_home=data.get("isHome", False),
            shot_type=data.get("shotType", ""),
            situation=data.get("situation", ""),
            body_part=data.get("bodyPart", ""),
            player=player,
            player_coordinates=Coordinates(
                x=player_coords.get("x", 0),
                y=player_coords.get("y", 0),
                z=player_coords.get("z", 0),
            ),
            goal_mouth_location=data.get("goalMouthLocation", ""),
            goal_mouth_coordinates=Coordinates(
                x=goal_coords.get("x", 0),
                y=goal_coords.get("y", 0),
                z=goal_coords.get("z", 0),
            ),
            goalkeeper=goalkeeper,
            block_coordinates=Coordinates(**block_coords) if block_coords else None,
            draw=draw,
            goal_type=data.get("goalType"),
        )

    def get_shotmap(self, match_id: int | str, referer_url: str | None = None) -> ShotMap:
        """
        Obtiene el mapa de tiros de un partido.

        Args:
            match_id: ID del partido en Sofascore.
            referer_url: URL del partido para el header Referer (opcional).

        Returns:
            ShotMap con todos los tiros del partido.

        Raises:
            requests.HTTPError: Si la petición falla.
        """
        url = f"{self.BASE_URL}/event/{match_id}/shotmap"

        headers = {}
        if referer_url:
            headers["Referer"] = referer_url

        response = self.session.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        shots_data = data.get("shotmap", [])
        shots = [self._parse_shot(s) for s in shots_data]

        return ShotMap(match_id=int(match_id), shots=shots)

    @staticmethod
    def get_match_id_from_url(url: str) -> int | None:
        """
        Extrae el match_id de una URL de Sofascore.

        Args:
            url: URL completa del partido.

        Returns:
            El match_id o None si no se encuentra.
        """
        # Formato: https://www.sofascore.com/.../match-slug#id:12345678
        match = re.search(r"#id:(\d+)", url)
        if match:
            return int(match.group(1))

        # Formato alternativo en la URL
        match = re.search(r"/event/(\d+)", url)
        if match:
            return int(match.group(1))

        return None


# Funciones de conveniencia
def get_shotmap(
    match_id: int | str,
    cookies: dict[str, str] | None = None,
    cookies_file: str | None = None,
    platform: str = "windows",
) -> ShotMap:
    """
    Obtiene el mapa de tiros de un partido.

    Args:
        match_id: ID del partido en Sofascore.
        cookies: Diccionario de cookies (opcional).
        cookies_file: Ruta a archivo de cookies (opcional).
        platform: Plataforma para User-Agent: "windows", "macos", "linux".

    Returns:
        ShotMap con todos los tiros del partido.
    """
    client = JekeScoreClient(cookies=cookies, cookies_file=cookies_file, platform=platform)
    return client.get_shotmap(match_id)
