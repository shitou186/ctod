from dataclasses import asdict, dataclass
import hashlib
import json
import re


DEFAULT_RAMP_STOPS = (0.38, 0.58, 0.76, 0.9)
DEFAULT_COLORS = {
    "water": "#0025fe",
    "valley": "#04fe00",
    "low": "#c5fe00",
    "middle": "#febb00",
    "high": "#fe5a00",
    "peak": "#fe0000",
}


@dataclass(frozen=True)
class RasterStyle:
    min_height: float | None = None
    max_height: float | None = None
    no_data: float | None = 0.0
    light_azimuth: float = 315.0
    light_altitude: float = 45.0
    vertical_exaggeration: float = 3.2
    shade_strength: float = 1.0
    shade_contrast: float = 1.2
    hillshade_blend: float = 0.98
    atlas_shadow_power: float = 2.35
    ambient: float = 0.035
    base_brightness: float = 1.08
    gamma: float = 1.08
    saturation: float = 1.25
    shadow_cutoff: float = 0.16
    highlight_cutoff: float = 0.94
    ramp_stops: tuple[float, float, float, float] = DEFAULT_RAMP_STOPS
    water_color: str = DEFAULT_COLORS["water"]
    valley_color: str = DEFAULT_COLORS["valley"]
    low_color: str = DEFAULT_COLORS["low"]
    middle_color: str = DEFAULT_COLORS["middle"]
    high_color: str = DEFAULT_COLORS["high"]
    peak_color: str = DEFAULT_COLORS["peak"]
    buffer: int = 1
    tile_size: int = 256
    flip_y: bool = False

    @property
    def colors(self) -> tuple[str, str, str, str, str, str]:
        return (
            self.valley_color,
            self.low_color,
            self.middle_color,
            self.high_color,
            self.peak_color,
            self.peak_color,
        )

    def cache_key(self) -> str:
        payload = asdict(self)
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.md5(serialized.encode("utf-8")).hexdigest()[:12]


def hex_to_rgb(value: str) -> tuple[float, float, float]:
    value = normalize_hex(value)
    return (
        int(value[1:3], 16) / 255.0,
        int(value[3:5], 16) / 255.0,
        int(value[5:7], 16) / 255.0,
    )


def normalize_hex(value: str) -> str:
    if value is None:
        raise ValueError("Color cannot be None")
    value = value.strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return value.lower()
    if re.fullmatch(r"[0-9a-fA-F]{6}", value):
        return f"#{value.lower()}"
    if re.fullmatch(r"#[0-9a-fA-F]{3}", value):
        return "#" + "".join(ch * 2 for ch in value[1:].lower())
    if re.fullmatch(r"[0-9a-fA-F]{3}", value):
        return "#" + "".join(ch * 2 for ch in value.lower())
    raise ValueError(f"Unsupported color value: {value}")
