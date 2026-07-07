import binascii
import math
import struct
import zlib

import numpy as np

from ctod.core.raster.style import RasterStyle, hex_to_rgb


def encode_png_rgba(rgba: np.ndarray) -> bytes:
    if rgba.dtype != np.uint8:
        raise ValueError("PNG encoder expects uint8 data")
    if rgba.ndim != 3 or rgba.shape[2] != 4:
        raise ValueError("PNG encoder expects an HxWx4 RGBA array")

    height, width, _ = rgba.shape
    raw_rows = [b"\x00" + rgba[row].tobytes() for row in range(height)]
    raw = b"".join(raw_rows)

    def chunk(chunk_type: bytes, payload: bytes) -> bytes:
        crc = binascii.crc32(chunk_type + payload) & 0xFFFFFFFF
        return (
            struct.pack(">I", len(payload))
            + chunk_type
            + payload
            + struct.pack(">I", crc)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def empty_png(size: int = 256) -> bytes:
    return encode_png_rgba(np.zeros((size, size, 4), dtype=np.uint8))


def render_dem_tile(
    dem: np.ndarray,
    bounds,
    style: RasterStyle,
    valid_mask: np.ndarray | None = None,
) -> bytes:
    dem = np.asarray(dem, dtype=np.float64)
    if valid_mask is None:
        valid_mask = np.ones(dem.shape, dtype=bool)
    else:
        valid_mask = np.asarray(valid_mask, dtype=bool)

    valid_mask = valid_mask & np.isfinite(dem)
    if style.no_data is not None:
        valid_mask = valid_mask & (dem != style.no_data)

    if not np.any(valid_mask):
        return empty_png(style.tile_size)

    shade = compute_hillshade(dem, bounds, style)
    rgb = colorize_elevation(dem, style, valid_mask)
    lit = apply_lighting(rgb, shade, style)
    lit = apply_gamma(lit, style.gamma)
    lit = apply_saturation(lit, style.saturation)

    rgba = np.zeros((dem.shape[0], dem.shape[1], 4), dtype=np.uint8)
    rgba[..., :3] = np.clip(lit * 255.0, 0.0, 255.0).astype(np.uint8)
    rgba[..., 3] = np.where(valid_mask, 255, 0).astype(np.uint8)

    rgba = crop_buffer(rgba, style.buffer)
    if rgba.shape[0] != style.tile_size or rgba.shape[1] != style.tile_size:
        rgba = resize_nearest(rgba, style.tile_size, style.tile_size)

    return encode_png_rgba(rgba)


def crop_buffer(array: np.ndarray, buffer: int) -> np.ndarray:
    if buffer <= 0:
        return array
    if array.shape[0] <= buffer * 2 or array.shape[1] <= buffer * 2:
        return array
    return array[buffer:-buffer, buffer:-buffer]


def resize_nearest(array: np.ndarray, height: int, width: int) -> np.ndarray:
    y_idx = np.linspace(0, array.shape[0] - 1, height).round().astype(np.int64)
    x_idx = np.linspace(0, array.shape[1] - 1, width).round().astype(np.int64)
    return array[np.ix_(y_idx, x_idx)]


def compute_hillshade(dem: np.ndarray, bounds, style: RasterStyle) -> np.ndarray:
    spacing_x, spacing_y = pixel_spacing_meters(bounds, dem.shape, style.buffer)
    z = dem * style.vertical_exaggeration
    row_gradient, col_gradient = np.gradient(z, spacing_y, spacing_x)

    dz_dx = col_gradient
    dz_dy_north = -row_gradient

    primary = np.maximum(
        lambert_from_gradient(
            dz_dx,
            dz_dy_north,
            style.light_azimuth,
            style.light_altitude,
        ),
        0.0,
    )
    fill = np.maximum(
        lambert_from_gradient(
            dz_dx,
            dz_dy_north,
            style.light_azimuth + 95.0,
            style.light_altitude * 0.55,
        ),
        0.0,
    )
    back = np.maximum(
        lambert_from_gradient(
            dz_dx,
            dz_dy_north,
            style.light_azimuth + 180.0,
            style.light_altitude * 0.45,
        ),
        0.0,
    )

    shade = primary * 0.9 + fill * 0.075 + back * 0.025
    shade = np.power(np.clip(shade * style.shade_strength, 0.0, 1.0), style.shade_contrast)
    shade = smoothstep(style.shadow_cutoff, style.highlight_cutoff, shade)
    return np.power(np.clip(shade, 0.0, 1.0), style.atlas_shadow_power)


def pixel_spacing_meters(bounds, shape, buffer: int) -> tuple[float, float]:
    west, south, east, north = bounds
    height, width = shape
    core_width = max(width - buffer * 2, 1)
    core_height = max(height - buffer * 2, 1)
    lat = math.radians((south + north) * 0.5)
    meters_per_degree_lon = max(111_320.0 * math.cos(lat), 1.0)
    meters_per_degree_lat = 111_320.0
    spacing_x = abs(east - west) * meters_per_degree_lon / core_width
    spacing_y = abs(north - south) * meters_per_degree_lat / core_height
    return max(spacing_x, 0.001), max(spacing_y, 0.001)


def lambert_from_gradient(
    dz_dx: np.ndarray,
    dz_dy_north: np.ndarray,
    azimuth_degrees: float,
    altitude_degrees: float,
) -> np.ndarray:
    altitude = math.radians(altitude_degrees)
    azimuth = math.radians(azimuth_degrees)

    light_x = math.cos(altitude) * math.sin(azimuth)
    light_y = math.cos(altitude) * math.cos(azimuth)
    light_z = math.sin(altitude)

    normal_x = -dz_dx
    normal_y = -dz_dy_north
    normal_z = np.ones_like(dz_dx)
    normal_length = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)

    return (
        normal_x * light_x + normal_y * light_y + normal_z * light_z
    ) / np.maximum(normal_length, 1e-9)


def smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    if edge0 == edge1:
        return np.where(value >= edge1, 1.0, 0.0)
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def colorize_elevation(
    dem: np.ndarray,
    style: RasterStyle,
    valid_mask: np.ndarray,
) -> np.ndarray:
    min_height = style.min_height
    max_height = style.max_height
    if min_height is None:
        min_height = float(np.nanmin(dem[valid_mask]))
    if max_height is None:
        max_height = float(np.nanmax(dem[valid_mask]))
    height_range = max(max_height - min_height, 1.0)
    t = np.clip((dem - min_height) / height_range, 0.0, 1.0)

    colors = np.array([hex_to_rgb(value) for value in style.colors], dtype=np.float64)
    stops = np.array([0.0, *style.ramp_stops, 1.0], dtype=np.float64)
    rgb = np.zeros((dem.shape[0], dem.shape[1], 3), dtype=np.float64)

    for channel in range(3):
        rgb[..., channel] = np.interp(t, stops, colors[:, channel])

    return rgb


def apply_lighting(rgb: np.ndarray, shade: np.ndarray, style: RasterStyle) -> np.ndarray:
    shadow = (1.0 - style.hillshade_blend) + shade * style.hillshade_blend
    lit = rgb * np.maximum(style.ambient, shadow[..., np.newaxis])
    return lit * style.base_brightness


def apply_gamma(rgb: np.ndarray, gamma: float) -> np.ndarray:
    return np.power(np.maximum(rgb, 0.0), gamma)


def apply_saturation(rgb: np.ndarray, saturation: float) -> np.ndarray:
    gray = rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114
    return gray[..., np.newaxis] * (1.0 - saturation) + rgb * saturation
