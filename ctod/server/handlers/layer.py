import json
import os
import hashlib

from ctod.core.layer import generate_layer_json
from morecantile import TileMatrixSet

from ctod.server.queries import QueryParameters


def get_layer_json(tms: TileMatrixSet, qp: QueryParameters, tile_cache_path: str = None):
    """Generate and return a layer.json based on the COG, with optional disk caching."""

    if tile_cache_path:
        filename = os.path.basename(qp.get_cog())
        hash_suffix = hashlib.md5(qp.get_cog().encode("utf-8")).hexdigest()[:8]
        cache_key = f"{filename}_{hash_suffix}"
        meshing_method = qp.get_meshing_method()
        cache_grid_dir = os.path.join(tile_cache_path, cache_key, meshing_method)
        cached_path = os.path.join(cache_grid_dir, "layer.json")

        if os.path.exists(cached_path):
            with open(cached_path, "r") as f:
                return json.load(f)

        layer_json = generate_layer_json(tms, qp, cache_grid_dir)

        if not os.path.exists(cache_grid_dir):
            os.makedirs(cache_grid_dir)

        with open(cached_path, "w") as f:
            json.dump(layer_json, f)

        return layer_json

    return generate_layer_json(tms, qp)
