"""Pydantic v2 models for the Asphalt-TEG backend."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BaseApiModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class CalculationRequest(BaseApiModel):
    T_h: float = Field(..., description="Temperatura lado caliente [C]")
    T_c: float = Field(..., description="Temperatura lado frio [C]")
    R_L: float = Field(10.0, gt=0, description="Resistencia de carga [ohm]")
    num_teg: int = Field(2, ge=1, description="Numero de modulos TEG")

    @field_validator("T_h", "T_c")
    @classmethod
    def validate_temperature_range(cls, value: float) -> float:
        if value < -50.0 or value > 250.0:
            raise ValueError("Las temperaturas deben estar en el rango fisico [-50, 250] C")
        return value

    @model_validator(mode="after")
    def validate_gradient(self) -> "CalculationRequest":
        if self.T_h <= self.T_c:
            raise ValueError("T_h debe ser mayor que T_c")
        return self


class HourSimulationRequest(BaseApiModel):
    hora: str = Field(..., description="Hora a simular, por ejemplo 13:00")
    T_c: Optional[float] = Field(None, description="Temperatura lado frio opcional [C]")
    R_L: float = Field(10.0, gt=0, description="Resistencia de carga [ohm]")
    num_teg: int = Field(2, ge=1, description="Numero de modulos TEG")


class RoadScalingRequest(BaseApiModel):
    ancho: float = Field(..., gt=0, description="Ancho de la carretera [m]")
    longitud: float = Field(..., gt=0, description="Longitud de la seccion [m]")
    p_ave_mW: float = Field(29.0, ge=0, description="Potencia media de campo [mW]")
    horas: float = Field(8.0, gt=0, description="Horas de operacion")


class CompareConfigurationsRequest(BaseApiModel):
    T_h: float = Field(..., description="Temperatura base lado caliente [C]")
    T_c: float = Field(..., description="Temperatura lado frio [C]")
    R_L: float = Field(10.0, gt=0, description="Resistencia de carga [ohm]")
    num_teg: int = Field(2, ge=1, description="Numero de modulos TEG")
    mejora_L_C: float = Field(8.0, description="Mejora termica de la configuracion L [C]")

    @model_validator(mode="after")
    def validate_gradient(self) -> "CompareConfigurationsRequest":
        if self.T_h <= self.T_c:
            raise ValueError("T_h debe ser mayor que T_c")
        return self


class GenericApiResponse(BaseApiModel):
    inputs: dict[str, Any]
    resultados: dict[str, Any]
    formulas_aplicadas: dict[str, str]
    fuente: str


class TemperaturesResponse(BaseApiModel):
    temperaturas: list[dict[str, Any]]
    prueba_campo: dict[str, Any]
    fuente: str

