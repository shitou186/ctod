from fastapi import Query

from ctod.core.raster.style import DEFAULT_COLORS, DEFAULT_RAMP_STOPS, RasterStyle


query_min_height = Query(None, title="Minimum height for color ramp")
query_max_height = Query(None, title="Maximum height for color ramp")
query_light_azimuth = Query(315.0, title="Hillshade light azimuth")
query_light_altitude = Query(45.0, title="Hillshade light altitude")
query_vertical_exaggeration = Query(3.2, title="Vertical exaggeration for hillshade")
query_shade_strength = Query(1.0, title="Hillshade strength")
query_shade_contrast = Query(1.2, title="Hillshade contrast")
query_hillshade_blend = Query(0.98, title="Hillshade blend")
query_atlas_shadow_power = Query(2.35, title="Atlas shadow power")
query_ambient = Query(0.035, title="Ambient shade floor")
query_base_brightness = Query(1.08, title="Base brightness")
query_gamma = Query(1.08, title="Gamma")
query_saturation = Query(1.25, title="Saturation")
query_shadow_cutoff = Query(0.16, title="Shadow cutoff")
query_highlight_cutoff = Query(0.94, title="Highlight cutoff")
query_ramp_stops = Query(None, title="Comma separated color ramp stops")
query_buffer = Query(1, title="Pixel buffer for hillshade gradients")
query_flip_y = Query(False, title="Flip incoming y before reading the COG")
query_water_color = Query(DEFAULT_COLORS["water"], title="Water color")
query_valley_color = Query(DEFAULT_COLORS["valley"], title="Valley color")
query_low_color = Query(DEFAULT_COLORS["low"], title="Low color")
query_middle_color = Query(DEFAULT_COLORS["middle"], title="Middle color")
query_high_color = Query(DEFAULT_COLORS["high"], title="High color")
query_peak_color = Query(DEFAULT_COLORS["peak"], title="Peak color")


class RasterQueryParameters:
    def __init__(
        self,
        minHeight: float | None = None,
        maxHeight: float | None = None,
        noData: float | None = 0.0,
        lightAzimuth: float = 315.0,
        lightAltitude: float = 45.0,
        verticalExaggeration: float = 3.2,
        shadeStrength: float = 1.0,
        shadeContrast: float = 1.2,
        hillshadeBlend: float = 0.98,
        atlasShadowPower: float = 2.35,
        ambient: float = 0.035,
        baseBrightness: float = 1.08,
        gamma: float = 1.08,
        saturation: float = 1.25,
        shadowCutoff: float = 0.16,
        highlightCutoff: float = 0.94,
        rampStops: str | None = None,
        buffer: int = 1,
        flipY: bool = False,
        waterColor: str = DEFAULT_COLORS["water"],
        valleyColor: str = DEFAULT_COLORS["valley"],
        lowColor: str = DEFAULT_COLORS["low"],
        middleColor: str = DEFAULT_COLORS["middle"],
        highColor: str = DEFAULT_COLORS["high"],
        peakColor: str = DEFAULT_COLORS["peak"],
    ):
        self.minHeight = minHeight
        self.maxHeight = maxHeight
        self.noData = noData
        self.lightAzimuth = lightAzimuth
        self.lightAltitude = lightAltitude
        self.verticalExaggeration = verticalExaggeration
        self.shadeStrength = shadeStrength
        self.shadeContrast = shadeContrast
        self.hillshadeBlend = hillshadeBlend
        self.atlasShadowPower = atlasShadowPower
        self.ambient = ambient
        self.baseBrightness = baseBrightness
        self.gamma = gamma
        self.saturation = saturation
        self.shadowCutoff = shadowCutoff
        self.highlightCutoff = highlightCutoff
        self.rampStops = rampStops
        self.buffer = buffer
        self.flipY = flipY
        self.waterColor = waterColor
        self.valleyColor = valleyColor
        self.lowColor = lowColor
        self.middleColor = middleColor
        self.highColor = highColor
        self.peakColor = peakColor

    def to_style(self) -> RasterStyle:
        return RasterStyle(
            min_height=self.minHeight,
            max_height=self.maxHeight,
            no_data=self.noData,
            light_azimuth=self.lightAzimuth,
            light_altitude=self.lightAltitude,
            vertical_exaggeration=self.verticalExaggeration,
            shade_strength=self.shadeStrength,
            shade_contrast=self.shadeContrast,
            hillshade_blend=self.hillshadeBlend,
            atlas_shadow_power=self.atlasShadowPower,
            ambient=self.ambient,
            base_brightness=self.baseBrightness,
            gamma=self.gamma,
            saturation=self.saturation,
            shadow_cutoff=self.shadowCutoff,
            highlight_cutoff=self.highlightCutoff,
            ramp_stops=parse_ramp_stops(self.rampStops),
            buffer=max(int(self.buffer), 0),
            flip_y=self.flipY,
            water_color=self.waterColor,
            valley_color=self.valleyColor,
            low_color=self.lowColor,
            middle_color=self.middleColor,
            high_color=self.highColor,
            peak_color=self.peakColor,
        )


def parse_ramp_stops(value: str | None) -> tuple[float, float, float, float]:
    if value is None:
        return DEFAULT_RAMP_STOPS

    stops = tuple(float(part.strip()) for part in value.split(",") if part.strip())
    if len(stops) != 4:
        raise ValueError("rampStops must contain exactly four comma separated values")
    return stops
