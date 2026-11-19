"""Convert weather data of any source into the pytrnsys standard weather file (read by Type 9 + Type 16).

See ../README.md for the format. Summary:

* CSV, 2 header lines (names, units), then one line per time step, interval-ending AVERAGES,
  local STANDARD time (no daylight saving), first line = first interval of 1 January 00:00 of the first year,
  continuous (hour > 8760 for the following years).
* Columns (fixed order, always present, -9999 = not available):
  hour, Tamb, RH, GHI, DHI, DNI, vWind, dirWind, pAmb, GPOAmeas, flag
* A JSON sidecar (<file>.json) documents source, kind of data (measured / reanalysis / tmy / synthetic),
  site, time conventions, the original radiation quantities and every conversion applied.

Radiation conversions (all on interval averages, sun position at the middle of the interval):
* GHI only                -> DHI with the Erbs et al. (1982) decomposition (or Reindl et al. 1990 with
                             --decomposition reindl), DNI = (GHI - DHI) / cos(zenith)
* GHI + DHI               -> DNI = (GHI - DHI) / cos(zenith)
* GHI + DNI               -> DHI = GHI - DNI cos(zenith)
* DNI + DHI               -> GHI = DHI + DNI cos(zenith)
* POA (plane of array)    -> GHI by inverting "Erbs decomposition + Perez (1990) transposition" with bisection,
  for a fixed plane, a 2-axis tracking plane or a 1-axis horizontal N-S tracking plane. The measured POA is kept
  in the column GPOAmeas.
Solar position: Spencer (1971) declination and equation of time, interval midpoint.

Usage (pytrnsys_gui venv): python weather_standard.py --help
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import json
import pathlib as _pl

import numpy as np
import pandas as pd

VERSION = "1.0 (2026-11-18)"
MISSING = -9999.0
COLUMNS = ["hour", "Tamb", "RH", "GHI", "DHI", "DNI", "vWind", "dirWind", "pAmb", "GPOAmeas", "flag"]
UNITS = ["h", "degC", "%", "W/m2", "W/m2", "W/m2", "m/s", "deg", "Pa", "W/m2", "-"]
FLAG_MEASURED = 0  # main variables from the primary (measured) source
FLAG_FILLED = 1  # gap filled from a secondary source
FLAG_SECONDARY = 2  # only the secondary source (outside the measured period)
FLAG_SYNTHETIC = 3  # synthetic / typical year
SOLAR_CONSTANT = 1367.0  # W/m2


# ----------------------------------------------------------------------------------------------------------------------
# Site and solar geometry
# ----------------------------------------------------------------------------------------------------------------------
@dataclasses.dataclass
class Site:
    name: str
    latitude: float  # deg, north positive
    longitude: float  # deg, EAST positive
    altitude: float  # m
    utc_offset_standard: float  # h, standard time of the site (CET = 1)

    @property
    def trnsys_shift(self) -> float:
        """Type 16 parameter 7: shift in solar time = longitude (east +) - 15 * UTC offset [deg]."""
        return self.longitude - 15.0 * self.utc_offset_standard


def solar_position(t_mid_utc: pd.DatetimeIndex, site: Site) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Zenith [rad], azimuth [rad, 0 = south, west +] and extraterrestrial normal irradiance [W/m2]."""
    doy = t_mid_utc.dayofyear.to_numpy()
    hours = (t_mid_utc.hour + t_mid_utc.minute / 60 + t_mid_utc.second / 3600).to_numpy()
    b = 2 * np.pi * (doy - 1) / 365.0
    decl = (
        0.006918 - 0.399912 * np.cos(b) + 0.070257 * np.sin(b) - 0.006758 * np.cos(2 * b)
        + 0.000907 * np.sin(2 * b) - 0.002697 * np.cos(3 * b) + 0.00148 * np.sin(3 * b)
    )
    eot_min = 229.18 * (
        0.000075 + 0.001868 * np.cos(b) - 0.032077 * np.sin(b) - 0.014615 * np.cos(2 * b) - 0.04089 * np.sin(2 * b)
    )
    solar_time = hours + site.longitude / 15.0 + eot_min / 60.0
    omega = np.radians(15.0 * (solar_time - 12.0))
    lat = np.radians(site.latitude)
    cos_z = np.sin(lat) * np.sin(decl) + np.cos(lat) * np.cos(decl) * np.cos(omega)
    zen = np.arccos(np.clip(cos_z, -1, 1))
    sin_z = np.maximum(np.sin(zen), 1e-6)
    cos_az = (np.sin(decl) * np.cos(lat) - np.cos(decl) * np.sin(lat) * np.cos(omega)) / sin_z  # from north
    az_north = np.arccos(np.clip(cos_az, -1, 1))
    az_north = np.where(omega > 0, 2 * np.pi - az_north, az_north)
    az_south_west_pos = az_north - np.pi  # 0 = south, +90 = west
    i0n = SOLAR_CONSTANT * (1 + 0.033 * np.cos(2 * np.pi * doy / 365.0))
    return zen, az_south_west_pos, i0n


def surface_orientation(mode: str, zen: np.ndarray, az: np.ndarray, slope_deg: float, azimuth_deg: float):
    """Slope and azimuth [rad] of the irradiance sensor plane. Azimuth TRNSYS convention: 0 = south, west +.

    mode: 'fixed' (slope, azimuth), 'tracking_2axis' (normal to the sun), 'tracking_1axis_ns' (horizontal N-S axis,
    east-west tracking, plane normal in the plane of the sun and the vertical E-W plane).
    """
    if mode == "fixed":
        return np.full_like(zen, np.radians(slope_deg)), np.full_like(zen, np.radians(azimuth_deg))
    if mode == "tracking_2axis":
        return zen.copy(), az.copy()
    if mode == "tracking_1axis_ns":
        # rotation angle of a horizontal N-S axis (Braun & Mitchell 1983)
        rot = np.arctan2(np.sin(zen) * np.sin(az), np.cos(zen))
        slope = np.abs(rot)
        azim = np.where(rot >= 0, np.pi / 2, -np.pi / 2)
        return slope, azim
    raise ValueError(f"unknown orientation mode {mode}")


def cos_incidence(zen, az, slope, azim):
    return np.cos(zen) * np.cos(slope) + np.sin(zen) * np.sin(slope) * np.cos(az - azim)


# ----------------------------------------------------------------------------------------------------------------------
# Radiation models
# ----------------------------------------------------------------------------------------------------------------------
def erbs_diffuse_fraction(kt: np.ndarray) -> np.ndarray:
    """Erbs, Klein and Duffie (1982)."""
    kt = np.clip(kt, 0, 1)
    return np.where(
        kt <= 0.22,
        1.0 - 0.09 * kt,
        np.where(kt <= 0.80, 0.9511 - 0.1604 * kt + 4.388 * kt**2 - 16.638 * kt**3 + 12.336 * kt**4, 0.165),
    )


def reindl_diffuse_fraction(kt, zen, tamb=None, rh=None):
    """Reindl, Beckman and Duffie (1990): full correlation (kT, solar altitude, Tamb, RH) when Tamb and RH are given,
    otherwise the reduced correlation (kT, solar altitude). RH in %. Same correlations as TRNSYS Type 16 modes 1/2
    and Type 109 with global radiation only."""
    kt = np.clip(kt, 0, 1)
    sin_alt = np.clip(np.cos(zen), 0, 1)
    if tamb is None or rh is None:
        d1 = np.minimum(1.0, 1.020 - 0.254 * kt + 0.0123 * sin_alt)
        d2 = np.clip(1.400 - 1.749 * kt + 0.177 * sin_alt, 0.1, 0.97)
        d3 = np.maximum(0.1, 0.486 * kt - 0.182 * sin_alt)
    else:
        phi = np.clip(rh, 0, 100) / 100.0
        d1 = np.minimum(1.0, 1.000 - 0.232 * kt + 0.0239 * sin_alt - 0.000682 * tamb + 0.0195 * phi)
        d2 = np.clip(1.329 - 1.716 * kt + 0.267 * sin_alt - 0.00357 * tamb + 0.106 * phi, 0.1, 0.97)
        d3 = np.maximum(0.1, 0.426 * kt - 0.256 * sin_alt + 0.00349 * tamb + 0.0734 * phi)
    return np.where(kt <= 0.3, d1, np.where(kt < 0.78, d2, d3))


_PEREZ = np.array(
    [  # Perez et al. (1990), all sites composite: eps upper bound, f11 f12 f13 f21 f22 f23
        [1.065, -0.008, 0.588, -0.062, -0.060, 0.072, -0.022],
        [1.230, 0.130, 0.683, -0.151, -0.019, 0.066, -0.029],
        [1.500, 0.330, 0.487, -0.221, 0.055, -0.064, -0.026],
        [1.950, 0.568, 0.187, -0.295, 0.109, -0.152, -0.014],
        [2.800, 0.873, -0.392, -0.362, 0.226, -0.462, 0.001],
        [4.500, 1.132, -1.237, -0.412, 0.288, -0.823, 0.056],
        [6.200, 1.060, -1.600, -0.359, 0.264, -1.127, 0.131],
        [np.inf, 0.678, -0.327, -0.250, 0.156, -1.377, 0.251],
    ]
)


def perez_poa(ghi, dhi, dni, zen, cos_inc, slope, i0n, albedo):
    """Total irradiance on a tilted plane, Perez (1990) sky diffuse + isotropic ground reflection."""
    cz = np.maximum(np.cos(zen), np.cos(np.radians(85.0)))
    zen_deg = np.minimum(np.degrees(zen), 89.9)
    airmass = 1.0 / (np.cos(np.radians(zen_deg)) + 0.50572 * (96.07995 - zen_deg) ** -1.6364)  # Kasten-Young
    airmass = np.where(np.degrees(zen) < 90, airmass, 40.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        eps = np.where(dhi > 0, ((dhi + dni) / dhi + 1.041 * zen**3) / (1 + 1.041 * zen**3), 1.0)
    delta = dhi * airmass / i0n
    idx = np.searchsorted(_PEREZ[:, 0], eps, side="right").clip(0, 7)
    f = _PEREZ[idx]
    f1 = np.maximum(0.0, f[:, 1] + f[:, 2] * delta + f[:, 3] * zen)
    f2 = f[:, 4] + f[:, 5] * delta + f[:, 6] * zen
    a = np.maximum(cos_inc, 0.0)
    sky = dhi * ((1 - f1) * (1 + np.cos(slope)) / 2 + f1 * a / cz + f2 * np.sin(slope))
    sky = np.maximum(sky, 0.0)
    beam = dni * a
    ground = ghi * albedo * (1 - np.cos(slope)) / 2
    return beam + sky + ground


def complete_radiation(kind: str, zen, i0n, ghi=None, dhi=None, dni=None, decomposition="erbs", tamb=None, rh=None):
    """Return GHI, DHI, DNI from the available horizontal/normal components (see module docstring).

    decomposition (kind 'ghi'): 'erbs' (default), 'reindl' (full if tamb and rh are given, else reduced)."""
    cz = np.cos(zen)
    up = cz > 0.01
    i0h = np.where(up, i0n * cz, 0.0)
    if kind == "ghi":
        kt = np.where(i0h > 1, ghi / np.maximum(i0h, 1e-6), 0.0)
        if decomposition == "reindl":
            fd = reindl_diffuse_fraction(kt, zen, tamb, rh)
        else:
            fd = erbs_diffuse_fraction(kt)
        dhi = np.where(up, fd * ghi, ghi)
        dni = np.where(up, (ghi - dhi) / np.maximum(cz, 0.01), 0.0)
    elif kind == "ghi_dhi":
        dni = np.where(up, (ghi - dhi) / np.maximum(cz, 0.01), 0.0)
    elif kind == "ghi_dni":
        dhi = np.where(up, ghi - dni * cz, ghi)
    elif kind == "dni_dhi":
        ghi = dhi + np.where(up, dni * cz, 0.0)
    else:
        raise ValueError(kind)
    ghi, dhi = np.maximum(ghi, 0), np.maximum(np.minimum(dhi, ghi), 0)
    dni = np.clip(dni, 0, i0n)
    return ghi, dhi, dni


def invert_poa(poa, zen, az, i0n, orientation: str, slope_deg: float, azimuth_deg: float, albedo: float):
    """GHI, DHI, DNI from irradiance measured on a (fixed or tracking) plane.

    For each step the GHI is found by bisection so that Erbs decomposition + Perez transposition give the measured
    POA. Below 3 W/m2 or with the sun below 5 deg elevation the step is taken as isotropic diffuse
    (GHI = DHI = POA / ((1 + cos slope) / 2 + albedo (1 - cos slope) / 2)).
    """
    slope, azim = surface_orientation(orientation, zen, az, slope_deg, azimuth_deg)
    cos_inc = cos_incidence(zen, az, slope, azim)
    cz = np.cos(zen)
    i0h = np.maximum(i0n * cz, 0.0)
    lo = np.zeros_like(poa)
    hi = np.maximum(1.2 * i0h, 1.0)

    def model(ghi):
        g, d, b = complete_radiation("ghi", zen, i0n, ghi=ghi)
        return perez_poa(g, d, b, zen, cos_inc, slope, i0n, albedo)

    for _ in range(50):
        mid = (lo + hi) / 2
        too_high = model(mid) > poa
        hi = np.where(too_high, mid, hi)
        lo = np.where(too_high, lo, mid)
    ghi = (lo + hi) / 2
    iso = (1 + np.cos(slope)) / 2 + albedo * (1 - np.cos(slope)) / 2
    simple = (poa < 3) | (np.degrees(zen) > 85)
    ghi = np.where(simple, np.maximum(poa, 0) / iso, ghi)
    ghi, dhi, dni = complete_radiation("ghi", zen, i0n, ghi=ghi)
    dhi = np.where(simple, ghi, dhi)
    dni = np.where(simple, 0.0, dni)
    residual = np.where(simple, 0.0, model(ghi) - poa)  # the simple (isotropic) steps are not a model inversion
    return ghi, dhi, dni, residual


# ----------------------------------------------------------------------------------------------------------------------
# Time handling
# ----------------------------------------------------------------------------------------------------------------------
def to_interval_end_standard(times: pd.Series, tz: str, convention: str, step_h: float, site: Site) -> pd.Series:
    """Timestamps of any source -> interval END in local STANDARD time (naive).

    tz: 'UTC', 'Etc/GMT-1' (fixed offset) or an IANA zone with daylight saving ('Europe/Berlin').
    convention: 'start', 'end' or 'center' of the averaging interval.
    """
    t = pd.to_datetime(times)
    if t.dt.tz is None:
        if tz in ("UTC", "GMT"):
            t = t.dt.tz_localize("UTC")
        else:
            t = t.dt.tz_localize(tz, ambiguous="NaT", nonexistent="NaT")
    shift = {"start": step_h, "end": 0.0, "center": step_h / 2}[convention]
    t_utc = t.dt.tz_convert("UTC") + pd.to_timedelta(shift, unit="h")
    return (t_utc + pd.to_timedelta(site.utc_offset_standard, unit="h")).dt.tz_localize(None)


def hour_index(t_end_standard: pd.Series, first_year: int) -> pd.Series:
    origin = pd.Timestamp(year=first_year, month=1, day=1)
    return (t_end_standard - origin) / pd.Timedelta(hours=1)


# ----------------------------------------------------------------------------------------------------------------------
# Readers per source: each returns a DataFrame indexed by interval-end standard time with any of the columns
# Tamb, RH, GHI, DHI, DNI, vWind, dirWind, pAmb, GPOA (W/m2, degC, %, m/s, deg, Pa)
# ----------------------------------------------------------------------------------------------------------------------
def read_openmeteo_era5(path: _pl.Path, site: Site) -> tuple[pd.DataFrame, dict]:
    """Open-Meteo archive CSV (models=era5, timezone=GMT, wind in m/s). Radiation = mean of the preceding hour."""
    df = pd.read_csv(path, skiprows=3)
    t = to_interval_end_standard(df["time"], "UTC", "end", 1.0, site)
    out = pd.DataFrame(
        {
            "Tamb": df.filter(like="temperature_2m").iloc[:, 0].to_numpy(),
            "RH": df.filter(like="relative_humidity_2m").iloc[:, 0].to_numpy(),
            "GHI": df.filter(like="shortwave_radiation").iloc[:, 0].to_numpy(),
            "DHI": df.filter(like="diffuse_radiation").iloc[:, 0].to_numpy(),
            "DNI": df.filter(like="direct_normal_irradiance").iloc[:, 0].to_numpy(),
            "vWind": df.filter(like="wind_speed_10m").iloc[:, 0].to_numpy(),
            "dirWind": df.filter(like="wind_direction_10m").iloc[:, 0].to_numpy(),
            "pAmb": df.filter(like="surface_pressure").iloc[:, 0].to_numpy() * 100.0,
        },
        index=pd.DatetimeIndex(t),
    )
    meta = {
        "source": "ERA5 reanalysis (ECMWF) via Open-Meteo historical archive API",
        "kind": "reanalysis",
        "radiation_input": "GHI + DHI + DNI (hourly means of the preceding hour)",
        "notes": "Temperature, humidity, wind (10 m) and pressure are instantaneous values at the end of the hour.",
    }
    return out, meta


def read_epw(path: _pl.Path, site: Site, year: int | None = None) -> tuple[pd.DataFrame, dict]:
    """EnergyPlus weather file: local standard time, hour 1 = interval 00:00-01:00 (interval end)."""
    names = ["Y", "M", "D", "H", "Min"] + [f"c{i}" for i in range(30)]
    df = pd.read_csv(path, skiprows=8, header=None, names=names[:35], usecols=range(22))
    y = year or int(df["Y"].iloc[0])
    t = pd.to_datetime(dict(year=y, month=df.M, day=df.D)) + pd.to_timedelta(df.H, unit="h")
    out = pd.DataFrame(
        {
            "Tamb": df.c1.to_numpy(), "RH": df.c3.to_numpy(), "pAmb": df.c4.to_numpy(),
            "GHI": df.c8.to_numpy(), "DNI": df.c9.to_numpy(), "DHI": df.c10.to_numpy(),
            "dirWind": df.c15.to_numpy(), "vWind": df.c16.to_numpy(),
        },
        index=pd.DatetimeIndex(t),
    )
    return out, {"source": f"EPW file {path.name}", "kind": "tmy", "radiation_input": "GHI + DNI + DHI"}


def read_tmy3(path: _pl.Path, site: Site, year: int | None = None) -> tuple[pd.DataFrame, dict]:
    """TMY3 CSV (NREL / Meteonorm export): local standard time, 'HH:MM' = interval end."""
    df = pd.read_csv(path, skiprows=1)
    date = pd.to_datetime(df.iloc[:, 0], format="%m/%d/%Y")
    if year:
        date = date.apply(lambda d: d.replace(year=year))
    hh = df.iloc[:, 1].str.slice(0, 2).astype(int)
    t = date + pd.to_timedelta(hh, unit="h")
    col = lambda key: df.filter(like=key).iloc[:, 0].to_numpy()  # noqa: E731
    out = pd.DataFrame(
        {
            "GHI": col("GHI (W/m^2)"), "DNI": col("DNI (W/m^2)"), "DHI": col("DHI (W/m^2)"),
            "Tamb": col("Dry-bulb (C)"), "RH": col("RHum (%)"), "pAmb": col("Pressure (mbar)") * 100,
            "dirWind": col("Wdir (degrees)"), "vWind": col("Wspd (m/s)"),
        },
        index=pd.DatetimeIndex(t),
    )
    return out, {"source": f"TMY3 file {path.name}", "kind": "tmy", "radiation_input": "GHI + DNI + DHI"}


def read_type109_user(path: _pl.Path, site: Site, year: int) -> tuple[pd.DataFrame, dict]:
    """User format of Type 99/109 (*.99, e.g. MeteoSwiss IDAweb), TRNSYS 18 Mathematical Reference, Type 99.

    Header between <userdefined> and <data>: <longitude> (east negative), <latitude>, <gmt>, <interval> td [h],
    <firsttime> [h], and one line per variable: <var> NAME <col> c <interp> i <add> a <mult> m <samp> s
    (c = 0: not available; value = column * m + a; s = -1 mean over td ENDING at the line time, 0 centred,
    1 mean over td STARTING at the line time). Line k (k = 0, 1, ...) has the time firsttime + k td of the year
    `year`. Radiation in W/m2, Tamb degC, RHUM %, WSPEED m/s, WDIR deg; a variable named pamb is the pressure [Pa].
    """
    lines = path.read_text(errors="replace").splitlines()
    data_start = next(i for i, line in enumerate(lines) if line.strip().lower().startswith("<data>")) + 1
    header = {}
    variables = []
    for line in lines[:data_start]:
        txt = line.split("!")[0].strip()
        if not txt.startswith("<"):
            continue
        key = txt.split(">")[0] + ">"
        if key.lower() == "<var>":
            tok = txt.replace("<", " <").split()
            name = tok[1]
            val = {tok[i].lower(): float(tok[i + 1]) for i in range(2, len(tok) - 1, 2) if tok[i].startswith("<")}
            variables.append((name, val))
        elif key.lower() in ("<interval>", "<firsttime>", "<gmt>", "<longitude>", "<latitude>"):
            header[key.lower()] = txt.split(">", 1)[1].split()[0]
    data = pd.read_csv(path, skiprows=data_start, sep=r"\s+", header=None, comment="!")
    step = float(header.get("<interval>", 1))
    first = float(header.get("<firsttime>", 0))
    t_line = first + np.arange(len(data)) * step
    mapping = {"IGLOB_H": "GHI", "IDIFF_H": "DHI", "IBEAM_N": "DNI", "IBEAM_H": "IBH", "TAMB": "Tamb",
               "RHUM": "RH", "WSPEED": "vWind", "WDIR": "dirWind", "PAMB": "pAmb"}
    out = pd.DataFrame()
    shifts = set()
    for name, val in variables:
        col = int(val.get("<col>", 0))
        dst = mapping.get(name.upper())
        if col <= 0 or dst is None:
            continue
        samp = val.get("<samp>", -1)
        shift = {-1: 0.0, 0: step / 2, 1: step}[int(samp)]
        shifts.add(shift)
        t_end = pd.Timestamp(year=year, month=1, day=1) + pd.to_timedelta(t_line + shift, unit="h")
        series = pd.Series(data.iloc[:, col - 1].to_numpy() * val.get("<mult>", 1.0) + val.get("<add>", 0.0),
                           index=pd.DatetimeIndex(t_end))
        out = out.reindex(out.index.union(series.index)) if len(out) else pd.DataFrame(index=series.index)
        out[dst] = series
    if "IBH" in out and "DHI" not in out and "GHI" in out:
        out["DHI"] = out["GHI"] - out.pop("IBH")
    kinds = [k for k in ("GHI", "DHI", "DNI") if k in out]
    meta = {
        "source": f"Type 99/109 user file {path.name}",
        "kind": "measured",
        "radiation_input": " + ".join(kinds),
        "header": header,
        "notes": f"time of line k = firsttime + k * interval; samp shifts to interval end: {sorted(shifts)} h",
    }
    return out, meta


def read_measured_csv(path: _pl.Path, site: Site, spec: dict) -> tuple[pd.DataFrame, dict]:
    """Measured data of a plant or station, described by a JSON spec (see README, 'Measured data spec')."""
    df = pd.read_csv(path, **spec.get("read_csv", {}))
    t = to_interval_end_standard(df[spec["time_column"]], spec["time_zone"], spec["time_convention"],
                                 spec["step_h"], site)
    out = pd.DataFrame(index=pd.DatetimeIndex(t))
    for dst, src in spec["columns"].items():
        out[dst] = pd.to_numeric(df[src], errors="coerce").to_numpy() * spec.get("factors", {}).get(dst, 1.0)
    out = out[~out.index.isna()]
    out = out.groupby(level=0).mean()  # duplicated hour of the daylight saving change
    meta = {"source": spec.get("source", path.name), "kind": "measured",
            "radiation_input": spec.get("radiation_input", "")}
    return out, meta


# ----------------------------------------------------------------------------------------------------------------------
# Build the standard file
# ----------------------------------------------------------------------------------------------------------------------
def build_standard(
    site: Site,
    first_year: int,
    n_hours: int,
    primary: pd.DataFrame,
    primary_meta: dict,
    radiation_kind: str,
    secondary: pd.DataFrame | None = None,
    secondary_meta: dict | None = None,
    poa: dict | None = None,
    albedo: float = 0.2,
    synthetic: bool = False,
    decomposition: str = "erbs",
) -> tuple[pd.DataFrame, dict]:
    """Standard table on a complete hourly grid.

    radiation_kind of the primary source: 'ghi', 'ghi_dhi', 'ghi_dni', 'dni_dhi', 'ghi_dhi_dni' or 'poa'
    (poa = {'orientation': 'fixed' | 'tracking_2axis' | 'tracking_1axis_ns', 'slope': deg, 'azimuth': deg}).
    Variables missing in the primary source, and gaps, are taken from the secondary source (flag 1 / 2).
    """
    grid = pd.date_range(pd.Timestamp(year=first_year, month=1, day=1, hour=1), periods=n_hours, freq="h")
    t_mid_utc = (grid - pd.Timedelta(minutes=30) - pd.Timedelta(hours=site.utc_offset_standard)).tz_localize("UTC")
    zen, az, i0n = solar_position(t_mid_utc, site)
    conversions = []

    prim = primary.reindex(grid)
    # radiation of the primary source -> GHI, DHI, DNI
    if radiation_kind == "poa":
        g = prim["GPOA"].to_numpy(dtype=float)
        ok = ~np.isnan(g)
        ghi = np.full(len(grid), np.nan)
        dhi, dni = ghi.copy(), ghi.copy()
        res = np.full(len(grid), np.nan)
        r = invert_poa(g[ok], zen[ok], az[ok], i0n[ok], poa["orientation"], poa.get("slope", 0.0),
                       poa.get("azimuth", 0.0), albedo)
        ghi[ok], dhi[ok], dni[ok], res[ok] = r
        prim["GHI"], prim["DHI"], prim["DNI"] = ghi, dhi, dni
        conversions.append(
            {
                "what": "GHI, DHI, DNI from the irradiance measured on the plane of array (GPOAmeas)",
                "method": "inversion of Erbs (1982) decomposition + Perez (1990) transposition by bisection; "
                "isotropic diffuse below 3 W/m2 or sun elevation < 5 deg",
                "plane": poa,
                "albedo": albedo,
                "max_abs_residual_Wm2": float(np.nanmax(np.abs(res))) if ok.any() else None,
                "steps_abs_residual_above_10_Wm2": int(np.nansum(np.abs(res) > 10)),
                "note": "a residual remains when the measured POA cannot be reached with any GHI (e.g. sun behind "
                "the plane at low elevation): GHI is then the value that gives the closest POA",
            }
        )
    elif radiation_kind in ("ghi", "ghi_dhi", "ghi_dni", "dni_dhi"):
        cols = {k: prim[k].to_numpy(dtype=float) for k in ("GHI", "DHI", "DNI") if k in prim}
        tamb = prim["Tamb"].to_numpy(dtype=float) if "Tamb" in prim else None
        rh = prim["RH"].to_numpy(dtype=float) if "RH" in prim else None
        g, d, b = complete_radiation(radiation_kind, zen, i0n, ghi=cols.get("GHI"), dhi=cols.get("DHI"),
                                     dni=cols.get("DNI"), decomposition=decomposition, tamb=tamb, rh=rh)
        prim["GHI"], prim["DHI"], prim["DNI"] = g, d, b
        decomp_txt = ("Reindl, Beckman & Duffie (1990) " + ("full (kT, altitude, Tamb, RH)" if tamb is not None and rh
                      is not None else "reduced (kT, altitude)")) if decomposition == "reindl" else "Erbs (1982)"
        method = {"ghi": f"{decomp_txt} decomposition", "ghi_dhi": "DNI = (GHI - DHI)/cos(zenith)",
                  "ghi_dni": "DHI = GHI - DNI cos(zenith)", "dni_dhi": "GHI = DHI + DNI cos(zenith)"}[radiation_kind]
        conversions.append({"what": f"radiation from {radiation_kind}", "method": method})

    out = pd.DataFrame(index=grid)
    flag = np.full(len(grid), FLAG_SYNTHETIC if synthetic else FLAG_MEASURED, dtype=int)
    sec = secondary.reindex(grid) if secondary is not None else None
    sources = {}
    for col in ("Tamb", "RH", "GHI", "DHI", "DNI", "vWind", "dirWind", "pAmb"):
        has_primary = col in prim and prim[col].notna().any()
        p = prim[col] if has_primary else pd.Series(np.nan, index=grid)
        if sec is not None and col in sec:
            filled = (p.isna() & sec[col].notna()).to_numpy()
            if col in ("Tamb", "GHI") and has_primary:
                flag[filled] = FLAG_FILLED
            p = p.where(~filled, sec[col])
            sources[col] = "primary, gaps from secondary" if has_primary else "secondary"
        else:
            sources[col] = "primary" if has_primary else "not available (-9999)"
        out[col] = p.interpolate(limit=3).to_numpy()
    defaults = {"RH": 70.0, "vWind": 2.0, "dirWind": 0.0,
                "pAmb": 101325.0 * (1 - 2.25577e-5 * site.altitude) ** 5.25588}
    for col, value in defaults.items():
        if np.isnan(out[col].to_numpy(dtype=float)).all():
            out[col] = value
            sources[col] = f"default constant {value:.1f} (no source)"
    if not synthetic:
        primary_main =[prim[c].isna().to_numpy() for c in ("Tamb", "GHI") if c in prim and prim[c].notna().any()]
        if primary_main:
            flag[np.logical_and.reduce(primary_main)] = FLAG_SECONDARY
    out["GPOAmeas"] = prim["GPOA"].to_numpy() if "GPOA" in prim else np.nan
    out.insert(0, "hour", hour_index(pd.Series(grid), first_year).to_numpy())
    out["flag"] = flag
    out = out.fillna(MISSING)

    meta = {
        "format": "pytrnsys standard weather file " + VERSION,
        "site": dataclasses.asdict(site) | {"trnsys_shift_deg": site.trnsys_shift},
        "time": {
            "first_line": f"interval ending {first_year}-01-01 01:00 local standard time",
            "convention": "interval-ending averages, local standard time (UTC%+g), no daylight saving"
            % site.utc_offset_standard,
            "step_h": 1.0,
            "n_lines": n_hours,
        },
        "kind": "synthetic" if synthetic else primary_meta.get("kind", "measured"),
        "primary": primary_meta,
        "secondary": secondary_meta,
        "column_sources": sources,
        "conversions": conversions,
        "flags": {"0": "measured (primary)", "1": "gap filled from secondary", "2": "secondary only",
                  "3": "synthetic"},
        "flag_counts": {str(k): int(v) for k, v in zip(*np.unique(flag, return_counts=True))},
        "created": _dt.datetime.now().isoformat(timespec="seconds"),
        "converter": f"weather_standard.py {VERSION}",
    }
    return out, meta


def write_standard(df: pd.DataFrame, meta: dict, path: _pl.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        f.write(",".join(COLUMNS) + "\n")
        f.write(",".join(UNITS) + "\n")
        df[COLUMNS].to_csv(f, header=False, index=False, float_format="%.2f", lineterminator="\n")
    path.with_suffix(".json").write_text(json.dumps(meta, indent=2, default=str))


def site_constants(df: pd.DataFrame) -> dict:
    """Constants for the site ddck (TambAvg, amplitude and shift of the first harmonic, design temperature)."""
    t = df.loc[df.Tamb > MISSING, "Tamb"].to_numpy()[:8760]
    hours = np.arange(len(t))
    w = 2 * np.pi / 8760
    a, b = 2 / len(t) * np.sum(t * np.cos(w * hours)), 2 / len(t) * np.sum(t * np.sin(w * hours))
    amp = float(np.hypot(a, b))
    t_min_h = (np.degrees(np.arctan2(b, a)) / 360 * 8760 + 8760 / 2) % 8760
    return {"TambAvg": round(float(t.mean()), 2), "dTambAmpl": round(amp, 2), "tTambShift": round(float(t_min_h)),
            "TambD": round(float(np.percentile(t, 1)), 1)}


# ----------------------------------------------------------------------------------------------------------------------
# Command line
# ----------------------------------------------------------------------------------------------------------------------
def _main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", required=True)
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True, help="east positive")
    p.add_argument("--alt", type=float, required=True)
    p.add_argument("--utc-offset", type=float, required=True, help="standard time of the site, CET = 1")
    p.add_argument("--first-year", type=int, required=True)
    p.add_argument("--hours", type=int, required=True, help="number of lines (8760 for one year)")
    p.add_argument("--source", required=True, choices=["era5-openmeteo", "epw", "tmy3", "type109", "measured"])
    p.add_argument("--file", type=_pl.Path, required=True)
    p.add_argument("--spec", type=_pl.Path, help="JSON spec for --source measured")
    p.add_argument("--radiation", default="ghi_dhi_dni",
                   choices=["ghi", "ghi_dhi", "ghi_dni", "dni_dhi", "ghi_dhi_dni", "poa"])
    p.add_argument("--poa-orientation", default="fixed", choices=["fixed", "tracking_2axis", "tracking_1axis_ns"])
    p.add_argument("--poa-slope", type=float, default=0.0)
    p.add_argument("--poa-azimuth", type=float, default=0.0, help="0 = south, west +")
    p.add_argument("--albedo", type=float, default=0.2)
    p.add_argument("--decomposition", default="erbs", choices=["erbs", "reindl"],
                   help="GHI-only data: Erbs (1982) or Reindl (1990, as TRNSYS Type 16 mode 2 / Type 109)")
    p.add_argument("--fill-era5", type=_pl.Path, help="Open-Meteo ERA5 CSV used as secondary source")
    p.add_argument("--synthetic", action="store_true", help="flag the data as synthetic / typical year")
    p.add_argument("--out", type=_pl.Path, required=True)
    a = p.parse_args()

    site = Site(a.name, a.lat, a.lon, a.alt, a.utc_offset)
    if a.source == "era5-openmeteo":
        prim, pm = read_openmeteo_era5(a.file, site)
    elif a.source == "epw":
        prim, pm = read_epw(a.file, site, a.first_year)
    elif a.source == "tmy3":
        prim, pm = read_tmy3(a.file, site, a.first_year)
    elif a.source == "type109":
        prim, pm = read_type109_user(a.file, site, a.first_year)
    else:
        prim, pm = read_measured_csv(a.file, site, json.loads(a.spec.read_text(encoding="utf-8")))
    sec, sm = (read_openmeteo_era5(a.fill_era5, site) if a.fill_era5 else (None, None))
    poa = {"orientation": a.poa_orientation, "slope": a.poa_slope, "azimuth": a.poa_azimuth}
    df, meta = build_standard(site, a.first_year, a.hours, prim, pm, a.radiation, sec, sm,
                              poa if a.radiation == "poa" else None, a.albedo, a.synthetic, a.decomposition)
    meta["site_constants"] = site_constants(df)
    write_standard(df, meta, a.out)
    print(json.dumps({k: meta[k] for k in ("kind", "flag_counts", "conversions", "site_constants")}, indent=2))


if __name__ == "__main__":
    _main()
