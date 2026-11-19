# Weather data: pytrnsys standard

All weather data used by the simulations is converted once into one **standard file** and read with one ddck,
`Weather_SPF/weather_data_base_type9.ddck` (Type 9 reader + Type 16 radiation processor + Type 33 + Type 69).
The ddck has the same output names as the Type 109 version (`weatherTamb`, `weatherIT_surfUser_1`, ...), so
collectors, shading and PV ddcks do not depend on the source of the data.

| Old readers (kept until all projects are moved) | |
|---|---|
| `Weather_SPF/weather_data_base.ddck` | Type 109, SPF user format `*.99` or TMY2 |
| `Weather/weather_data_base_type15.ddck` | Type 15, TMY/TMY2/TMY3/EPW/TM2 |

## Folders

```
Weather/                                    data only (no parentheses in paths: the ddck grammar rejects them)
  <Source>/<Country>/<Station>/<Station>_<period>_<step>.csv   standard file
  <Source>/<Country>/<Station>/<Station>_<period>_<step>.json  metadata (source, conversions, flags)
  <Source>/raw/                             original downloads, unchanged
  converters/weather_standard.py            converters (one reader per source)
Weather_SPF/                                ddcks
  weather_data_base_type9.ddck              reader + processing of the standard file
  <Source>/<Country>/<Site>.ddck            site ddck: location, statistics, ASSIGN of the file
```

`<Source>`: `ERA5`, `Meteonorm`, `MeteoSwiss`, `DWD`, ... Measured data of a plant that may not be shared stays in
the project (`<project>/ddck/weather/`), with its site ddck and the converter spec next to it.

## File format

* CSV, comma separated, **2 header lines** (names, units), then one line per time step.
* **Interval-ending averages** in **local standard time** (no daylight saving). Line 1 = interval
  1 January 00:00-01:00 of the first year of the file; the file is continuous (hours > 8760 for the next years).
  Type 9 (mode 6) skips the lines up to `START`, so `START`/`STOP` count from 1 January 00:00 of the first year of
  the file (e.g. 1 July of the second year = 8760 + 4344).
* Columns, fixed order, always present, `-9999` = not available:

| Column | Unit | |
|---|---|---|
| hour | h | end of the interval since 1 January 00:00 of the first year |
| Tamb | degC | dry bulb |
| RH | % | relative humidity |
| GHI | W/m2 | global horizontal |
| DHI | W/m2 | diffuse horizontal |
| DNI | W/m2 | direct normal |
| vWind | m/s | wind speed |
| dirWind | deg | wind direction, north = 0, east = 90 |
| pAmb | Pa | ambient pressure |
| GPOAmeas | W/m2 | measured irradiance in a plane (plant pyranometers), kept for validation |
| flag | - | 0 measured / primary, 1 gap filled from the secondary source, 2 secondary only, 3 synthetic |

* The **JSON sidecar** documents: site (latitude, longitude east +, altitude, UTC offset, Type 16 shift), time
  convention, kind of data (`measured`, `reanalysis`, `tmy`, `synthetic`), primary and secondary source, the
  source of each column, every conversion applied (method, plane, albedo, residuals) and the flag counts.

## Converters

`converters/weather_standard.py` (pytrnsys_gui venv), one reader per source:

| `--source` | Input |
|---|---|
| `era5-openmeteo` | Open-Meteo historical archive CSV (`models=era5`, `timezone=GMT`, `wind_speed_unit=ms`) |
| `epw` | EnergyPlus weather file |
| `tmy3` | TMY3 CSV (NREL, Meteonorm export) |
| `type109` | SPF user format `*.99` (e.g. MeteoSwiss IDAweb) |
| `measured` | any CSV of a plant or station, described by a JSON spec (below) |

Radiation of the primary source (`--radiation`) and how the missing components are obtained
(interval averages, sun position at the middle of the interval, Spencer 1971):

| `--radiation` | Conversion |
|---|---|
| `ghi_dhi_dni` | none |
| `ghi_dhi` | DNI = (GHI - DHI) / cos(zenith) |
| `ghi_dni` | DHI = GHI - DNI cos(zenith) |
| `dni_dhi` | GHI = DHI + DNI cos(zenith) |
| `ghi` | DHI with Erbs et al. (1982), then DNI |
| `poa` | GHI found by bisection so that Erbs decomposition + Perez (1990) transposition give the measured plane-of-array irradiance; `--poa-orientation fixed` (with `--poa-slope`, `--poa-azimuth` in the TRNSYS convention: 0 = facing the equator, east -, west +), `tracking_2axis` or `tracking_1axis_ns`. Below 3 W/m2 or sun elevation < 5 deg: isotropic diffuse. The measured value is kept in `GPOAmeas`. |

`--fill-era5 <file>` adds a secondary source for the variables the primary source does not have (humidity, wind,
pressure) and for its gaps (flag 1 or 2). Without a secondary source, humidity, wind and pressure get constant
defaults (70 %, 2 m/s, barometric pressure at the altitude), written in the JSON. `--synthetic` sets flag 3.

### Measured data spec (JSON)

```json
{
  "source": "plant monitoring, sheet ..., sensors ...",
  "read_csv": {"header": 1, "encoding": "utf-8"},
  "time_column": "Date-time (local, start of hour)",
  "time_zone": "Europe/Berlin",
  "time_convention": "start",
  "step_h": 1.0,
  "radiation_input": "POA, fixed plane 35 deg, azimuth -12.5 deg",
  "columns": {"Tamb": "T ambient TTAmb [degC]", "GPOA": "Irradiance G GMeas [W/m2]"},
  "factors": {}
}
```

`time_zone`: `UTC`, a fixed offset (`Etc/GMT-1` = UTC+1) or a zone with daylight saving (`Europe/Berlin`; the
ambiguous hour of October and the missing hour of March are dropped and interpolated, up to 3 h gaps are
interpolated). `time_convention`: whether the
time stamp is the `start`, `end` or `center` of the averaging interval. Column keys: `Tamb`, `RH`, `GHI`, `DHI`,
`DNI`, `GPOA`, `vWind`, `dirWind`, `pAmb`.

### Example (Bad Rappenau, measured + ERA5)

```
python weather_standard.py --name BadRappenau --lat 49.2633 --lon 9.1321 --alt 250 --utc-offset 1 ^
  --first-year 2025 --hours 13104 --source measured --file hourly_integrated.csv ^
  --spec monitoring_spec_hourly_integrated.json --radiation poa --poa-orientation fixed --poa-slope 35 ^
  --poa-azimuth -12.5 --fill-era5 ERA5/raw/openmeteo_era5_49.2633_9.1321_2025-01_2026-06.csv ^
  --out BadRappenau_2025-2026_1h.csv
```

The converter prints the site constants for the site ddck (`TambAvg`, `dTambAmpl`, `tTambShift`, `TambD`).

## Site ddck

Copy `Weather_SPF/ERA5/DE/BadRappenau_ERA5_2025-2026.ddck` and change: `Lat`, `Long` (east +), `utcOffset`
(`shiftSolarTime = Long - 15*utcOffset`), `altid`, the temperature statistics, `weatherDataKind`,
`firstYearWeather` and the `ASSIGN`. In the config, both included `as weather`:

```
COMMON$ Weather_SPF/ERA5/DE/BadRappenau_ERA5_2025-2026 as weather
COMMON$ Weather_SPF/weather_data_base_type9 as weather
deck weatherslopeSurfUser_1 35
deck weatheraziSurfUser_1 -12.5
deck weatherusePOAmeas 0    # 1: measured plane-of-array irradiance on surface 1 (validation)
```

## Equations used by the converters (`weather_standard.py`)

All radiation values are interval averages; the sun position is taken at the middle of the interval.
Angles: zenith θz, solar azimuth γs (0 = south, west +, geographic, both hemispheres), declination δ, hour angle ω
(wrapped to ±180°), latitude φ, surface slope β and azimuth γ. The `--poa-azimuth` of the command line is in the
TRNSYS convention and converted (southern hemisphere: γ = 180° − γTRNSYS), see below.

| Quantity | Equation | Reference |
|---|---|---|
| Day angle | B = 2π (n − 1) / 365, n = day of the year | Spencer (1971) |
| Declination | δ = 0.006918 − 0.399912 cos B + 0.070257 sin B − 0.006758 cos 2B + 0.000907 sin 2B − 0.002697 cos 3B + 0.00148 sin 3B | Spencer (1971) |
| Equation of time [min] | E = 229.18 (0.000075 + 0.001868 cos B − 0.032077 sin B − 0.014615 cos 2B − 0.04089 sin 2B) | Spencer (1971), as in Duffie & Beckman (2013) eq. 1.5.3 |
| Solar time, hour angle | t_sol = t_UTC + λ/15 + E/60 (λ east +), ω = 15 (t_sol − 12) | Duffie & Beckman (2013) §1.5 |
| Zenith | cos θz = sin φ sin δ + cos φ cos δ cos ω | Duffie & Beckman (2013) eq. 1.6.5 |
| Solar azimuth | cos γs(from north) = (sin δ cos φ − cos δ sin φ cos ω) / sin θz, sign of ω | Duffie & Beckman (2013) §1.6 |
| Extraterrestrial normal irradiance | G0n = 1367 (1 + 0.033 cos(360 n / 365)) W/m2 | Duffie & Beckman (2013) eq. 1.4.1a |
| Incidence on a plane | cos θ = cos θz cos β + sin θz sin β cos(γs − γ) | Duffie & Beckman (2013) eq. 1.6.3 |
| Clearness index | kT = GHI / (G0n cos θz) | Duffie & Beckman (2013) §2.9 |
| Diffuse fraction (decomposition) | kT ≤ 0.22: 1 − 0.09 kT; 0.22 < kT ≤ 0.80: 0.9511 − 0.1604 kT + 4.388 kT² − 16.638 kT³ + 12.336 kT⁴; kT > 0.80: 0.165 | Erbs, Klein & Duffie (1982) |
| Closure | GHI = DHI + DNI cos θz | Duffie & Beckman (2013) eq. 2.15.1 |
| Air mass | m = 1 / (cos θz + 0.50572 (96.07995 − θz[deg])^−1.6364) | Kasten & Young (1989) |
| Sky diffuse on a plane | D_s = DHI [ (1 − F1)(1 + cos β)/2 + F1 a/b + F2 sin β ], a = max(0, cos θ), b = max(cos 85°, cos θz); ε = ((DHI + DNI)/DHI + 1.041 θz³)/(1 + 1.041 θz³), Δ = DHI m / G0n, F1 = max(0, f11 + f12 Δ + f13 θz), F2 = f21 + f22 Δ + f23 θz, coefficients for 8 ε bins | Perez et al. (1990), "all sites composite" coefficient table |
| Ground reflected | D_g = GHI ρ (1 − cos β)/2 | Duffie & Beckman (2013) eq. 2.15.1 |
| Plane of array | POA = DNI cos θ + D_s + D_g | Duffie & Beckman (2013) §2.16 |
| POA inversion | GHI solved by bisection (50 steps on [0, 1.2 G0n cos θz]) so that POA(Erbs(GHI)) = measured POA; isotropic (GHI = DHI = POA / ((1 + cos β)/2 + ρ (1 − cos β)/2)) below 3 W/m2 or θz > 85° | method of this converter; same principle as the GTI inversion of Marion (2015) |
| 1-axis horizontal N-S tracking | rotation R = atan2(sin θz sin γs, cos θz), β = abs(R), γ = ±90° | Braun & Mitchell (1983); Marion & Dobos (2013) |
| 2-axis tracking | β = θz, γ = γs (cos θ = 1) | Duffie & Beckman (2013) §1.7 |
| Site constants | TambAvg = mean; dTambAmpl, tTambShift = amplitude and phase of the first harmonic of the hourly Tamb; TambD = 1 % percentile | this converter |
| Type 16 shift in solar time | shift = λ_east − 15 · UTC offset [deg] | TRNSYS 18 Type 16 source (SolarRadiationRoutines.f90) |

TRNSYS itself (Type 16, `SkyModel = 4`) also uses the Perez model, with its own implementation
(Perez et al. 1988/1990, TRNSYS 18 Mathematical Reference). A POA inverted here and transposed again by Type 16
therefore differs a little from the measured POA; for validation use `usePOAmeas = 1` (measured POA on surface 1).

### References

* Braun, J.E., Mitchell, J.C. (1983). Solar geometry for fixed and tracking surfaces. Solar Energy 31(5), 439-444.
* Duffie, J.A., Beckman, W.A. (2013). Solar Engineering of Thermal Processes, 4th ed. Wiley.
* Erbs, D.G., Klein, S.A., Duffie, J.A. (1982). Estimation of the diffuse radiation fraction for hourly, daily and
  monthly-average global radiation. Solar Energy 28(4), 293-302.
* Hersbach, H. et al. (2020). The ERA5 global reanalysis. Q. J. R. Meteorol. Soc. 146, 1999-2049.
* Kasten, F., Young, A.T. (1989). Revised optical air mass tables and approximation formula. Applied Optics 28(22),
  4735-4738.
* Marion, B. (2015). A model for deriving the direct normal and diffuse horizontal irradiance from the global tilted
  irradiance. Solar Energy 122, 1037-1046.
* Marion, W.F., Dobos, A.P. (2013). Rotation angle for the optimum tracking of one-axis trackers. NREL/TP-6A20-58891.
* Perez, R., Ineichen, P., Seals, R., Michalsky, J., Stewart, R. (1990). Modeling daylight availability and
  irradiance components from direct and global irradiance. Solar Energy 44(5), 271-289.
* Spencer, J.W. (1971). Fourier series representation of the position of the sun. Search 2(5), 172.
* Open-Meteo historical weather API (ERA5), https://open-meteo.com, data licence CC BY 4.0.

## Tracking surfaces (parabolic troughs, trackers)

See the description block of `Weather_SPF/weather_data_base_type9.ddck`: the 4 user surfaces can each be fixed or
tracked (`TrackSurfUser_k`), with one tracking mode (`ModeTracking`) for the tracked ones; in mode 3 the slope and
azimuth of a user surface are those of the tracking AXIS (troughs with a horizontal N-S axis: slope 0, azimuth 0).
The actual aperture orientation is given by `slopeActSurfUser_k` and `aziActSurfUser_k`.

## Hemispheres and azimuth convention

TRNSYS (Type 16, solar azimuth and surface azimuth) measures the azimuth from the EQUATOR, east negative, west
positive, in both hemispheres: in the southern hemisphere 0 = north and 180 = south. A collector facing the
equator has azimuth 0 everywhere; the facades `AA_S` / `AA_N` of the weather ddck face north / south in the south.
The converter computes the sun position geographically (0 = south) and converts the `--poa-azimuth` given in the
TRNSYS convention.

Checked with ERA5 2023 for Zurich, Sevilla, Santiago de Chile and Melbourne (DigiSolar
`Simulations/weather_check/era5_hemispheres`): with the isotropic sky Type 9 + 16 reproduce the Open-Meteo tilted
irradiance of a fixed plane (slope = latitude, facing the equator) within 0.1 % per year in both hemispheres, and an
independent calculation of single-axis trackers with a horizontal N-S axis within 0.7-1.5 % and with a horizontal
E-W axis within 0.3-0.6 %, without time shift. The Open-Meteo "tracker" (`tilt=nan`) is not a single-axis
tracker: it keeps the azimuth and sets the tilt equal to the solar zenith angle.

## Data sources

* ERA5: Hersbach et al. (2023), ERA5 hourly data, Copernicus Climate Change Service; downloaded through the
  Open-Meteo historical weather API (https://open-meteo.com, CC BY 4.0). Grid about 0.25 deg (~25 km): wind and
  radiation are area means.
