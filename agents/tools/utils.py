"""
Utilidades comunes para las herramientas de los agentes.
Formato español de números y moneda.
"""

import locale

def formato_euro(valor: float) -> str:
    """
    Formatea un número como euros en formato español.
    Ejemplo: 1234567.89 -> 1.234.567,89€
    """
    try:
        if valor >= 0:
            return f"{valor:,.2f}€".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            return f"-{abs(valor):,.2f}€".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"{valor}€"


def formato_numero(valor: float, decimales: int = 2) -> str:
    """
    Formatea un número en formato español sin símbolo de moneda.
    Ejemplo: 1234567.89 -> 1.234.567,89
    """
    try:
        formato = f"{valor:,.{decimales}f}"
        return formato.replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(valor)


def formato_porcentaje(valor: float) -> str:
    """
    Formatea un porcentaje en formato español.
    Ejemplo: 85.5 -> 85,5%
    """
    try:
        return f"{valor:.1f}%".replace(".", ",")
    except:
        return f"{valor}%"
