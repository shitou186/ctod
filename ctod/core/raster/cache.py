import hashlib
import os

import aiofiles


def get_raster_root_folder(path: str, cog: str, style_key: str) -> str:
    filename = os.path.basename(cog)
    cog_hash = hashlib.md5(cog.encode("utf-8")).hexdigest()[:8]
    return os.path.join(path, f"{filename}_{cog_hash}", "raster", style_key)


def get_raster_tile_folder(
    path: str,
    cog: str,
    style_key: str,
    z: int,
    x: int,
) -> str:
    return os.path.join(get_raster_root_folder(path, cog, style_key), str(z), str(x))


def get_raster_tile_filepath(
    path: str,
    cog: str,
    style_key: str,
    z: int,
    x: int,
    y: int,
) -> str:
    return os.path.join(
        get_raster_tile_folder(path, cog, style_key, z, x),
        f"{y}.png",
    )


async def get_raster_from_disk(
    path: str,
    cog: str,
    style_key: str,
    z: int,
    x: int,
    y: int,
) -> bytes | None:
    if path is None:
        return None

    file_path = get_raster_tile_filepath(path, cog, style_key, z, x, y)
    if not os.path.exists(file_path):
        return None

    async with aiofiles.open(file_path, "rb") as f:
        return await f.read()


async def save_raster_to_disk(
    path: str,
    cog: str,
    style_key: str,
    z: int,
    x: int,
    y: int,
    data: bytes,
):
    if path is None:
        return

    tile_path = get_raster_tile_folder(path, cog, style_key, z, x)
    if not os.path.exists(tile_path):
        os.makedirs(tile_path)

    file_path = get_raster_tile_filepath(path, cog, style_key, z, x, y)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(data)
