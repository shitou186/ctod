import asyncio
import logging

import numpy as np
from fastapi import Response
from fastapi.responses import JSONResponse

from ctod.core import utils
from ctod.core.raster.cache import get_raster_from_disk, save_raster_to_disk
from ctod.core.raster.renderer import empty_png, render_dem_tile
from ctod.core.raster.style import RasterStyle
from ctod.server.queries import QueryParameters


class RasterTileHandler:
    def __init__(self, cog_reader_pool, tile_cache_path: str | None):
        self.cog_reader_pool = cog_reader_pool
        self.tile_cache_path = tile_cache_path

    async def get(
        self,
        tms,
        z: int,
        x: int,
        y: int,
        qp: QueryParameters,
        style: RasterStyle,
    ):
        cog = qp.get_cog()
        tile_x, tile_y, tile_z = self._get_reader_tile(tms, x, y, z, style)
        style_key = style.cache_key()

        if not qp.get_skip_cache():
            cached = await get_raster_from_disk(
                self.tile_cache_path,
                cog,
                style_key,
                tile_z,
                tile_x,
                tile_y,
            )
            if cached is not None:
                return self._create_response(cached)

        image_data = await self._read_tile(tms, tile_x, tile_y, tile_z, qp, style)
        if image_data is None:
            png = empty_png(style.tile_size)
        else:
            try:
                dem, valid_mask = self._extract_dem(image_data, style)
                bounds = utils.get_tile_bounds(tms, tile_x, tile_y, tile_z)
                png = render_dem_tile(dem, bounds, style, valid_mask)
            except Exception as exc:
                logging.exception("Error rendering raster tile")
                return JSONResponse(
                    status_code=500,
                    content={"message": f"Error rendering raster tile: {exc}"},
                )

        await save_raster_to_disk(
            self.tile_cache_path,
            cog,
            style_key,
            tile_z,
            tile_x,
            tile_y,
            png,
        )

        return self._create_response(png)

    def _get_reader_tile(self, tms, x: int, y: int, z: int, style: RasterStyle):
        if style.flip_y:
            return utils.invert_y(tms, x, y, z)
        return x, y, z

    async def _read_tile(
        self,
        tms,
        x: int,
        y: int,
        z: int,
        qp: QueryParameters,
        style: RasterStyle,
    ):
        reader = await self.cog_reader_pool.get_reader(qp.get_cog(), tms)
        loop = asyncio.get_running_loop()
        try:
            return await asyncio.to_thread(
                reader.download_tile,
                x,
                y,
                z,
                loop,
                qp.get_no_data(),
                qp.get_resampling_method(),
                buffer=style.buffer,
            )
        finally:
            reader.return_reader()

    def _extract_dem(self, image_data, style: RasterStyle):
        band = image_data.data[0]
        mask = np.ones(band.shape, dtype=bool)

        if np.ma.isMaskedArray(band):
            mask = mask & ~np.ma.getmaskarray(band)
            band = np.ma.getdata(band)

        if getattr(image_data, "mask", None) is not None:
            image_mask = np.asarray(image_data.mask)
            if image_mask.ndim == 3:
                image_mask = image_mask[0]
            mask = mask & (image_mask > 0)

        dem = np.asarray(band, dtype=np.float64)
        if style.no_data is not None:
            mask = mask & (dem != style.no_data)
        mask = mask & np.isfinite(dem)
        return dem, mask

    def _create_response(self, png: bytes):
        return Response(
            content=png,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=31536000"},
        )
