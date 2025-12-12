from datetime import timedelta

from dateutil.relativedelta import relativedelta


def get_next_period(current_date, global_end_date, months=6):
    """
    Calcula el rango de fechas para la consulta.
    Retorna: (query_end_date, next_cycle_start_date)

    - query_end_date: Fecha fin para la API (día anterior al salto).
    - next_cycle_start_date: Fecha inicio del siguiente bucle.
    """
    # 1. Calcular el salto lógico (ej: 1 Ene -> 1 Jul)
    next_cycle_start = current_date + relativedelta(months=months)

    # 2. Calcular el fin de la consulta (ej: 30 Jun) para evitar duplicados
    query_end = next_cycle_start - timedelta(days=1)

    # 3. Aplicar el tope global (No pasar de 2025)
    if query_end > global_end_date:
        query_end = global_end_date

    return query_end, next_cycle_start
