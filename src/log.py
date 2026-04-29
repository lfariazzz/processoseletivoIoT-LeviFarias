# Sistema de Log em Memória
# Registra eventos do sistema com timestamp relativo ao boot

from utime import ticks_ms, ticks_diff

MAX_ENTRADAS = 20

_log = []
_inicio = ticks_ms()

def registrar(evento, detalhe=""):
    ts_s = ticks_diff(ticks_ms(), _inicio) // 1000
    _log.append((ts_s, evento, detalhe))
    if len(_log) > MAX_ENTRADAS:
        _log.pop(0)

def imprimir_log():
    print("=" * 44)
    print(f"[LOG] {len(_log)} evento(s) registrado(s):")
    for ts, evento, detalhe in _log:
        linha = f"  T+{ts:5d}s | {evento}"
        if detalhe:
            linha += f" | {detalhe}"
        print(linha)
    print("=" * 44)

def limpar_log():
    global _log
    _log = []
