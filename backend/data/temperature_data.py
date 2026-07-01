"""Temperature tables extracted from the requested paper."""

TEMPERATURE_TABLE = [
    {
        "hora": "10:00",
        "T_aire_min": 21,
        "T_aire_max": 23,
        "T_asf_min": 44,
        "T_asf_max": 49,
        "nota": "Calentamiento rapido",
    },
    {
        "hora": "11:00",
        "T_aire_min": 23,
        "T_aire_max": 25,
        "T_asf_min": 50,
        "T_asf_max": 55,
        "nota": "Radiacion muy intensa",
    },
    {
        "hora": "12:00",
        "T_aire_min": 24,
        "T_aire_max": 26,
        "T_asf_min": 56,
        "T_asf_max": 61,
        "nota": "Subida acelerada",
    },
    {
        "hora": "13:00",
        "T_aire_min": 25,
        "T_aire_max": 27,
        "T_asf_min": 59,
        "T_asf_max": 64,
        "nota": "Pico maximo de calor",
    },
    {
        "hora": "14:00",
        "T_aire_min": 24,
        "T_aire_max": 26,
        "T_asf_min": 57,
        "T_asf_max": 62,
        "nota": "Se mantiene muy alto",
    },
    {
        "hora": "15:00",
        "T_aire_min": 23,
        "T_aire_max": 25,
        "T_asf_min": 53,
        "T_asf_max": 58,
        "nota": "Empieza a descender",
    },
    {
        "hora": "16:00",
        "T_aire_min": 22,
        "T_aire_max": 24,
        "T_asf_min": 48,
        "T_asf_max": 53,
        "nota": "Bajada gradual",
    },
]

FIELD_TEST = {
    "T_asfalto_superficie": (55, 62),
    "T_placa_cobre": (48, 50),
    "T_suelo_10cm": (34, 38),
    "T_disipador_PCM": (18.3, 18.8),
    "delta_T_max": 34,
    "P_max_mW": 34,
    "P_ave_mW": 29,
}

