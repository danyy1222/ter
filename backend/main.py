"""FastAPI application for the Asphalt-TEG Energy Harvesting System."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from data.temperature_data import FIELD_TEST, TEMPERATURE_TABLE
from models import (
    CalculationRequest,
    CompareConfigurationsRequest,
    GenericApiResponse,
    HourSimulationRequest,
    RoadScalingRequest,
    TemperaturesResponse,
)
from teg_engine import (
    ALPHA,
    COST_UNIT,
    DISCOUNT_RATE,
    K_COPPER,
    K_TEG,
    NUM_TEG,
    P_AVE_FIELD,
    P_MAX_FIELD,
    R_INT,
    R_LOAD,
    T_PCM,
    build_calculation,
    build_compare_configurations,
    build_day_simulation,
    build_hour_simulation,
    build_max_density,
    build_road_scaling,
    build_viability,
)

app = FastAPI(
    title="Asphalt-TEG Energy Harvesting System",
    version="1.0.0",
    description="API REST para calculos termoelectricos del prototipo TEG en asfalto.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check() -> dict[str, object]:
    """Return service information and available constants."""

    return {
        "status": "ok",
        "sistema": "Asphalt-TEG Energy Harvesting System",
        "constantes": {
            "ALPHA": ALPHA,
            "R_INT": R_INT,
            "R_LOAD": R_LOAD,
            "K_TEG": K_TEG,
            "K_COPPER": K_COPPER,
            "T_PCM": T_PCM,
            "NUM_TEG": NUM_TEG,
            "P_MAX_FIELD_mW": P_MAX_FIELD,
            "P_AVE_FIELD_mW": P_AVE_FIELD,
            "COST_UNIT_USD": COST_UNIT,
            "DISCOUNT_RATE": DISCOUNT_RATE,
        },
        "endpoints": [
            "/calcular",
            "/simular-hora",
            "/simular-dia-completo",
            "/temperaturas",
            "/escalar-carretera",
            "/viabilidad",
            "/comparar-configuraciones",
            "/maxima-densidad-potencia",
        ],
    }


@app.post("/calcular", response_model=GenericApiResponse)
def calcular(payload: CalculationRequest) -> GenericApiResponse:
    """Run the full thermoelectric calculation for a given T_h and T_c."""

    data = build_calculation(T_h=payload.T_h, T_c=payload.T_c, R_L=payload.R_L, num_teg=payload.num_teg)
    return GenericApiResponse(**data)


@app.post("/simular-hora", response_model=GenericApiResponse)
def simular_hora(payload: HourSimulationRequest) -> GenericApiResponse:
    """Simulate a specific hour using the paper temperature table."""

    try:
        data = build_hour_simulation(
            hora=payload.hora,
            T_c=payload.T_c if payload.T_c is not None else T_PCM,
            R_L=payload.R_L,
            num_teg=payload.num_teg,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GenericApiResponse(
        inputs={
            "hora": payload.hora,
            "T_c": payload.T_c if payload.T_c is not None else T_PCM,
            "R_L": payload.R_L,
            "num_teg": payload.num_teg,
        },
        resultados=data,
        formulas_aplicadas={
            "base": "Se usa la media de T_asf_min y T_asf_max de la hora solicitada",
        },
        fuente="Temperaturas reales del paper",
    )


@app.get("/simular-dia-completo")
def simular_dia_completo() -> dict[str, object]:
    """Simulate the full day from 10:00 to 19:00."""

    return build_day_simulation(T_c=T_PCM, R_L=R_LOAD, num_teg=NUM_TEG)


@app.get("/temperaturas", response_model=TemperaturesResponse)
def temperaturas() -> TemperaturesResponse:
    """Return the real temperature table and field test data."""

    return TemperaturesResponse(
        temperaturas=TEMPERATURE_TABLE,
        prueba_campo=FIELD_TEST,
        fuente="Tabla de temperaturas reales medida en el paper",
    )


@app.post("/escalar-carretera", response_model=GenericApiResponse)
def escalar_carretera(payload: RoadScalingRequest) -> GenericApiResponse:
    """Scale the prototype average power to a road section."""

    data = build_road_scaling(
        ancho=payload.ancho,
        longitud=payload.longitud,
        p_ave_mW=payload.p_ave_mW,
        horas=payload.horas,
    )
    return GenericApiResponse(**data)


@app.get("/viabilidad", response_model=GenericApiResponse)
def viabilidad() -> GenericApiResponse:
    """Return economic viability and LCOE analysis."""

    data = build_viability()
    return GenericApiResponse(
        inputs=data["inputs"],
        resultados=data["resultados"],
        formulas_aplicadas=data["formulas_aplicadas"],
        fuente=data["fuente"],
    )


@app.post("/comparar-configuraciones", response_model=GenericApiResponse)
def comparar_configuraciones(payload: CompareConfigurationsRequest) -> GenericApiResponse:
    """Compare the Z-shape and L-shape configurations."""

    data = build_compare_configurations(
        T_h=payload.T_h,
        T_c=payload.T_c,
        R_L=payload.R_L,
        num_teg=payload.num_teg,
        mejora_L_C=payload.mejora_L_C,
    )
    return GenericApiResponse(
        inputs=data["inputs"],
        resultados=data["resultados"],
        formulas_aplicadas=data["formulas_aplicadas"],
        fuente=data["fuente"],
    )


@app.get("/maxima-densidad-potencia")
def maxima_densidad_potencia() -> dict[str, object]:
    """Return the maximum power density reported in the paper."""

    return build_max_density()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
