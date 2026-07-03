"""Thermoelectric engine calculations for the Asphalt-TEG project."""

from __future__ import annotations

from math import pow
from typing import Any

import numpy as np

from data.temperature_data import TEMPERATURE_TABLE

ALPHA = 0.05
R_INT = 2.0
R_LOAD = 10.0
K_TEG = 0.6
K_COPPER = 385.0
PLATE_LENGTH = 0.50
PLATE_WIDTH = 0.20
PLATE_THICKNESS = 0.0015
PLATE_DEPTH = 0.03
NUM_TEG = 2
TEG_AREA = 0.04 * 0.04
T_PCM = 18.0
P_MAX_FIELD = 34.0
P_AVE_FIELD = 29.0
COST_UNIT = 150.0
LIFETIME = 20
DISCOUNT_RATE = 0.03
PAPER_ROAD_LCOE_USD_KWH = 0.9


def validate_temperature_pair(T_h: float, T_c: float) -> None:
    """Validate the thermal gradient used by equations (1) to (4)."""

    if not (-50.0 <= T_h <= 250.0 and -50.0 <= T_c <= 250.0):
        raise ValueError("Las temperaturas deben estar en el rango fisico [-50, 250] C")
    if T_h <= T_c:
        raise ValueError("T_h debe ser mayor que T_c")


def mean_temperature(min_value: float, max_value: float) -> float:
    """Return the mean of a measured temperature interval."""

    return float(np.mean([min_value, max_value]))


def get_table_hour(hora: str) -> dict[str, Any] | None:
    """Retrieve a temperature row from the paper table by hour."""

    for row in TEMPERATURE_TABLE:
        if row["hora"] == hora:
            return row
    return None


def calculate_voltage(alpha: float, T_h: float, T_c: float) -> float:
    """Equation (1): V = alpha * (T_h - T_c)."""

    validate_temperature_pair(T_h, T_c)
    return alpha * (T_h - T_c)


def calculate_current(V: float, R: float, R_L: float) -> float:
    """Equation (2): I = V / (R + R_L)."""

    if R <= 0 or R_L <= 0:
        raise ValueError("R y R_L deben ser mayores que cero")
    return V / (R + R_L)


def calculate_power(I: float, R_L: float) -> float:
    """Equation (3): P = I**2 * R_L."""

    if R_L <= 0:
        raise ValueError("R_L debe ser mayor que cero")
    return (I**2) * R_L


def calculate_heat(alpha: float, I: float, T_c: float, K: float, T_h: float, T_c_2: float, R_L: float) -> float:
    """Equation (4): Q = alpha * I * T_c + K * (T_h - T_c) - 0.5 * I**2 * R_L."""

    validate_temperature_pair(T_h, T_c_2)
    return alpha * I * T_c + K * (T_h - T_c_2) - 0.5 * (I**2) * R_L


def calculate_copper_flux(k_copper: float, area: float, delta_T: float, delta_x: float) -> float:
    """Fourier heat flow: q = k_copper * A * delta_T / delta_x."""

    if area <= 0 or delta_x <= 0:
        raise ValueError("Area y delta_x deben ser mayores que cero")
    return k_copper * area * delta_T / delta_x


def calculate_efficiency(P: float, Q: float) -> float:
    """Efficiency percentage: eta = P / Q * 100."""

    if Q <= 0:
        raise ValueError("Q debe ser mayor que cero")
    return (P / Q) * 100.0


def calculate_annualized_cost(cost_capital: float, life_years: int, discount_rate: float) -> float:
    """Capital recovery factor annualization used for LCOE."""

    if cost_capital < 0 or life_years <= 0 or discount_rate < 0:
        raise ValueError("Parametros economicos invalidos")
    if discount_rate == 0:
        return cost_capital / life_years
    factor = pow(1 + discount_rate, life_years)
    return cost_capital * ((discount_rate * factor) / (factor - 1))


def calculate_lcoe(cost_annualized: float, energy_annual_kwh: float) -> float:
    """LCOE = costo_anualizado / energia_anual_kwh."""

    if energy_annual_kwh <= 0:
        raise ValueError("La energia anual debe ser mayor que cero")
    return cost_annualized / energy_annual_kwh


def build_calculation(
    T_h: float,
    T_c: float,
    R_L: float = R_LOAD,
    num_teg: int = NUM_TEG,
    alpha: float = ALPHA,
    R_int: float = R_INT,
    K_teg: float = K_TEG,
    k_copper: float = K_COPPER,
    plate_area: float = PLATE_LENGTH * PLATE_WIDTH,
    plate_depth: float = PLATE_DEPTH,
) -> dict[str, Any]:
    """Run equations (1) to (4) and the copper heat-flow relation."""

    validate_temperature_pair(T_h, T_c)

    delta_T = T_h - T_c
    V = calculate_voltage(alpha, T_h, T_c)
    I = calculate_current(V, R_int, R_L)
    P = calculate_power(I, R_L)
    Q = calculate_heat(alpha, I, T_c, K_teg, T_h, T_c, R_L)
    q = calculate_copper_flux(k_copper, plate_area, delta_T, plate_depth)
    eta = calculate_efficiency(P, Q)

    power_total = P * num_teg
    heat_total = Q * num_teg

    return {
        "inputs": {
            "T_h": round(T_h, 6),
            "T_c": round(T_c, 6),
            "delta_T": round(delta_T, 6),
            "R_L_ohm": round(R_L, 6),
            "R_int_ohm": round(R_int, 6),
            "alpha_V_K": round(alpha, 6),
            "K_TEG_W_K": round(K_teg, 6),
            "num_teg": int(num_teg),
            "A_placa_m2": round(plate_area, 6),
            "delta_x_m": round(plate_depth, 6),
        },
        "resultados": {
            "V_teg_V": round(V, 6),
            "I_A": round(I, 6),
            "P_electrica_W": round(P, 6),
            "P_electrica_mW": round(P * 1000.0, 6),
            "P_total_W": round(power_total, 6),
            "P_total_mW": round(power_total * 1000.0, 6),
            "Q_calor_total_W": round(Q, 6),
            "Q_total_modulos_W": round(heat_total, 6),
            "eta_porcentaje": round(eta, 6),
            "q_flujo_calor_W": round(q, 6),
        },
        "formulas_aplicadas": {
            "ec1": f"V = alpha * (Th - Tc) = {alpha} * ({T_h} - {T_c})",
            "ec2": f"I = V / (R + RL) = {V} / ({R_int} + {R_L})",
            "ec3": f"P = I^2 * RL = {I}^2 * {R_L}",
            "ec4": "Q = alpha * I * Tc + K * (Th - Tc) - 0.5 * I^2 * RL",
            "fourier": "q = k_copper * A * delta_T / delta_x",
            "eta": "eta = P / Q * 100",
        },
        "fuente": "Ecuaciones (1)-(4) y Fourier, paper Tahami et al. 2019",
    }


def build_hour_simulation(hora: str, T_c: float = T_PCM, R_L: float = R_LOAD, num_teg: int = NUM_TEG) -> dict[str, Any]:
    """Simulate one hour using the mean asphalt temperature from the paper table."""

    row = get_table_hour(hora)
    if row is None:
        raise ValueError(f"No existe una fila para la hora {hora}")
    T_h = mean_temperature(row["T_asf_min"], row["T_asf_max"])
    return {
        "hora": hora,
        "origen_dato": "tabla_paper",
        "temperaturas": {
            "T_h_media": round(T_h, 6),
            "T_c": round(T_c, 6),
            "T_asf_min": row["T_asf_min"],
            "T_asf_max": row["T_asf_max"],
            "nota": row["nota"],
        },
        "calculo": build_calculation(T_h=T_h, T_c=T_c, R_L=R_L, num_teg=num_teg),
    }


def extend_day_hours() -> list[dict[str, Any]]:
    """Extend the paper table to 19:00 using a transparent linear trend estimate."""

    extended = list(TEMPERATURE_TABLE)
    last = extended[-1]
    previous = extended[-2]
    last_mean = mean_temperature(last["T_asf_min"], last["T_asf_max"])
    prev_mean = mean_temperature(previous["T_asf_min"], previous["T_asf_max"])
    drop = last_mean - prev_mean

    last_aire = mean_temperature(last["T_aire_min"], last["T_aire_max"])
    prev_aire = mean_temperature(previous["T_aire_min"], previous["T_aire_max"])
    air_drop = last_aire - prev_aire

    current_hour = 17
    current_asf = last_mean + drop
    current_aire = last_aire + air_drop

    while current_hour <= 19:
        extended.append(
            {
                "hora": f"{current_hour:02d}:00",
                "T_aire_min": round(current_aire - 1.0, 6),
                "T_aire_max": round(current_aire + 1.0, 6),
                "T_asf_min": round(current_asf - 2.5, 6),
                "T_asf_max": round(current_asf + 2.5, 6),
                "nota": "Estimacion lineal a partir de la tendencia del paper",
            }
        )
        current_hour += 1
        current_asf += drop
        current_aire += air_drop

    return extended


def build_day_simulation(T_c: float = T_PCM, R_L: float = R_LOAD, num_teg: int = NUM_TEG) -> dict[str, Any]:
    """Simulate 10:00 to 19:00 hour by hour using mean asphalt temperatures."""

    hours = extend_day_hours()
    series = []
    for row in hours:
        T_h = mean_temperature(row["T_asf_min"], row["T_asf_max"])
        calc = build_calculation(T_h=T_h, T_c=T_c, R_L=R_L, num_teg=num_teg)
        series.append(
            {
                "hora": row["hora"],
                "origen_dato": "tabla_paper" if row["hora"] <= "16:00" else "estimado",
                "temperaturas": {
                    "T_h_media": round(T_h, 6),
                    "T_c": round(T_c, 6),
                    "T_asf_min": row["T_asf_min"],
                    "T_asf_max": row["T_asf_max"],
                    "nota": row["nota"],
                },
                "calculo": calc,
            }
        )
    return {
        "rango_horario": "10:00-19:00",
        "serie": series,
        "fuente": "Temperaturas reales del paper + extrapolacion lineal para 17:00-19:00",
    }


def build_road_scaling(ancho: float, longitud: float, p_ave_mW: float = P_AVE_FIELD, horas: float = 8.0) -> dict[str, Any]:
    """Scale average power from the prototype area to a road section."""

    if ancho <= 0 or longitud <= 0 or horas <= 0 or p_ave_mW < 0:
        raise ValueError("Dimensiones, horas y potencia deben ser validas")

    A_placa = PLATE_LENGTH * PLATE_WIDTH
    A_carretera = ancho * longitud
    P_ave_W = p_ave_mW / 1000.0
    Psm = P_ave_W / A_placa
    Pps = Psm * A_carretera
    P_8h_J = Pps * horas * 3600.0
    P_8h_kWh = P_8h_J / 3_600_000.0

    return {
        "inputs": {
            "ancho_m": round(ancho, 6),
            "longitud_m": round(longitud, 6),
            "A_placa_m2": round(A_placa, 6),
            "A_carretera_m2": round(A_carretera, 6),
            "p_ave_mW": round(p_ave_mW, 6),
            "horas": round(horas, 6),
        },
        "resultados": {
            "Psm_W_m2": round(Psm, 6),
            "Pps_W": round(Pps, 6),
            "P_8h_J": round(P_8h_J, 6),
            "P_8h_kWh": round(P_8h_kWh, 6),
        },
        "formulas_aplicadas": {
            "Psm": "Psm = P_ave / A_placa",
            "Pps": "Pps = Psm * A_carretera",
            "P_8h": "P_8h = Pps * horas * 3600",
            "kWh": "P_kwh = P_8h / 3_600_000",
        },
        "fuente": "Escalado a carretera real, ecuaciones derivadas del paper",
    }


def build_viability() -> dict[str, Any]:
    """Compute annualized cost, annual energy, and LCOE for the lab prototype,
    and report the paper's own road-scale LCOE figure alongside it for comparison.

    The two LCOE figures are not directly comparable: the prototype LCOE prices a
    single 0.1 m^2 lab unit in isolation (a scale at which TEG harvesting is not
    meant to be economical), while the paper's 0.9 USD/kWh applies to a 10 m wide
    paved road. The paper does not disclose the capital-cost assumption behind that
    road-scale figure (a naive per-unit scaling of COST_UNIT lands near 90-120
    USD/kWh, not 0.9), so it is reported here as a direct citation rather than a
    value re-derived from this module's formulas.
    """

    cost_annualized = calculate_annualized_cost(COST_UNIT, LIFETIME, DISCOUNT_RATE)
    annual_energy_kwh = (P_AVE_FIELD / 1000.0) * 8.0 * 365.0 / 1000.0
    lcoe_prototype = calculate_lcoe(cost_annualized, annual_energy_kwh)
    return {
        "inputs": {
            "costo_capital_USD": COST_UNIT,
            "vida_util_anios": LIFETIME,
            "tasa_descuento": DISCOUNT_RATE,
            "P_ave_field_mW": P_AVE_FIELD,
            "horas_operacion_diarias": 8.0,
        },
        "resultados": {
            "costo_anualizado_USD": round(cost_annualized, 6),
            "energia_anual_kWh": round(annual_energy_kwh, 6),
            "LCOE_prototipo_USD_kWh": round(lcoe_prototype, 6),
            "LCOE_carretera_paper_USD_kWh": PAPER_ROAD_LCOE_USD_KWH,
            "interpretacion": (
                "LCOE_prototipo evalua comprar una sola placa/TEG de laboratorio aislada, no es una cifra "
                "economicamente representativa por si sola. LCOE_carretera_paper es el valor que el paper "
                "reporta para una carretera pavimentada de 10 m de ancho; el paper no detalla el costo de "
                "capital asumido a esa escala, por lo que se cita directo del paper en vez de recalcularse."
            ),
        },
        "formulas_aplicadas": {
            "capital_recovery": "costo_anualizado = costo_capital * (r*(1+r)^n) / ((1+r)^n - 1)",
            "lcoe": "LCOE = costo_anualizado / energia_anual_kwh",
        },
        "fuente": (
            "Analisis economico del prototipo basado en parametros del paper; LCOE de carretera citado "
            "directo del paper (Tahami et al. 2019)"
        ),
    }


def build_compare_configurations(
    T_h: float,
    T_c: float,
    R_L: float = R_LOAD,
    num_teg: int = NUM_TEG,
    mejora_L_C: float = 8.0,
) -> dict[str, Any]:
    """Compare Z-shape and L-shape assuming the L-shape gains 8 C on the hot side."""

    validate_temperature_pair(T_h, T_c)
    z = build_calculation(T_h=T_h, T_c=T_c, R_L=R_L, num_teg=num_teg)
    l = build_calculation(T_h=T_h + mejora_L_C, T_c=T_c, R_L=R_L, num_teg=num_teg)
    return {
        "supuesto": "La configuracion L se modela con +8 C en T_h respecto a Z, siguiendo la nota del paper",
        "inputs": {
            "T_h_base": T_h,
            "T_c": T_c,
            "R_L": R_L,
            "num_teg": num_teg,
            "mejora_L_C": mejora_L_C,
        },
        "resultados": {
            "Z_shape": z["resultados"],
            "L_shape": l["resultados"],
            "diferencia_potencia_mW": round(l["resultados"]["P_total_mW"] - z["resultados"]["P_total_mW"], 6),
            "mejora_relativa_porcentaje": round(
                ((l["resultados"]["P_total_mW"] - z["resultados"]["P_total_mW"]) / z["resultados"]["P_total_mW"]) * 100.0,
                6,
            ),
        },
        "formulas_aplicadas": {
            "comparacion": "P_L > P_Z al aumentar T_h en 8 C",
        },
        "fuente": "Comparacion inferida de la mejora termica L-shape reportada en el paper",
    }


def build_max_density() -> dict[str, Any]:
    """Return the paper's maximum normalized power density."""

    value_mW_cm3 = 3.02
    value_W_m3 = value_mW_cm3 * 1000.0
    return {
        "resultados": {
            "densidad_potencia_max_mW_cm3": value_mW_cm3,
            "densidad_potencia_max_W_m3": round(value_W_m3, 6),
        },
        "formulas_aplicadas": {
            "conversion": "1 mW/cm^3 = 1000 W/m^3",
        },
        "fuente": "Valor normalizado reportado en el paper",
    }
