import struct
import unittest

import numpy as np

from ctod.core.raster.renderer import (
    compute_hillshade,
    crop_buffer,
    encode_png_rgba,
    render_dem_tile,
)
from ctod.core.raster.style import RasterStyle, hex_to_rgb, normalize_hex


class RasterRendererTests(unittest.TestCase):
    def test_normalize_hex_supports_short_and_long_hex(self):
        self.assertEqual(normalize_hex("#0f0"), "#00ff00")
        self.assertEqual(normalize_hex("fe0000"), "#fe0000")
        self.assertEqual(hex_to_rgb("#000000"), (0.0, 0.0, 0.0))
        self.assertEqual(hex_to_rgb("#ffffff"), (1.0, 1.0, 1.0))

    def test_compute_hillshade_returns_finite_values_in_unit_range(self):
        dem = np.array(
            [
                [10.0, 11.0, 12.0],
                [11.0, 12.0, 13.0],
                [12.0, 13.0, 14.0],
            ]
        )
        shade = compute_hillshade(dem, (110.0, 32.0, 111.0, 33.0), RasterStyle())

        self.assertEqual(shade.shape, dem.shape)
        self.assertTrue(np.all(np.isfinite(shade)))
        self.assertGreaterEqual(float(shade.min()), 0.0)
        self.assertLessEqual(float(shade.max()), 1.0)

    def test_render_dem_tile_outputs_png_with_expected_core_size(self):
        dem = np.arange(36, dtype=np.float64).reshape((6, 6))
        style = RasterStyle(
            min_height=0.0,
            max_height=35.0,
            no_data=None,
            buffer=1,
            tile_size=4,
        )

        png = render_dem_tile(dem, (110.0, 32.0, 111.0, 33.0), style)

        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        width, height = struct.unpack(">II", png[16:24])
        self.assertEqual((width, height), (4, 4))

    def test_crop_buffer_removes_outer_pixels(self):
        data = np.arange(36).reshape((6, 6))
        cropped = crop_buffer(data, 1)
        self.assertEqual(cropped.shape, (4, 4))
        self.assertEqual(int(cropped[0, 0]), 7)

    def test_encode_png_rgba_rejects_non_rgba_arrays(self):
        with self.assertRaises(ValueError):
            encode_png_rgba(np.zeros((4, 4, 3), dtype=np.uint8))


if __name__ == "__main__":
    unittest.main()
