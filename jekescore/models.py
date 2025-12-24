"""Modelos de datos para jekescore."""

from pydantic import BaseModel, ConfigDict


class Coordinates(BaseModel):
    """Coordenadas x, y, z en el campo."""

    x: float
    y: float
    z: float = 0


class DrawCoordinates(BaseModel):
    """Coordenadas para visualizar el tiro."""

    start: Coordinates
    end: Coordinates
    goal: Coordinates
    block: Coordinates | None = None


class Player(BaseModel):
    """Información básica del jugador."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    short_name: str | None = None
    position: str | None = None
    jersey_number: str | None = None


class Shot(BaseModel):
    """Representa un tiro/disparo en el partido."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    time: int
    time_seconds: int
    is_home: bool
    shot_type: str  # goal, save, miss, block
    situation: str  # corner, assisted, set-piece, fast-break, regular
    body_part: str  # head, right-foot, left-foot
    player: Player
    player_coordinates: Coordinates
    goal_mouth_location: str
    goal_mouth_coordinates: Coordinates
    goalkeeper: Player | None = None
    block_coordinates: Coordinates | None = None
    draw: DrawCoordinates | None = None
    goal_type: str | None = None  # regular, own-goal, penalty

    @property
    def is_goal(self) -> bool:
        """Retorna True si el tiro fue gol."""
        return self.shot_type == "goal"

    @property
    def x(self) -> float:
        """Coordenada X del disparo."""
        return self.player_coordinates.x

    @property
    def y(self) -> float:
        """Coordenada Y del disparo."""
        return self.player_coordinates.y


class ShotMap(BaseModel):
    """Colección de tiros de un partido."""

    match_id: int
    shots: list[Shot]

    @property
    def goals(self) -> list[Shot]:
        """Retorna solo los goles."""
        return [s for s in self.shots if s.is_goal]

    @property
    def home_shots(self) -> list[Shot]:
        """Retorna tiros del equipo local."""
        return [s for s in self.shots if s.is_home]

    @property
    def away_shots(self) -> list[Shot]:
        """Retorna tiros del equipo visitante."""
        return [s for s in self.shots if not s.is_home]

    def __len__(self) -> int:
        return len(self.shots)
