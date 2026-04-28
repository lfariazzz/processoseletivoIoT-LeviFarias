# Módulo IDS — Sistema de Detecção de Intrusão Física
# Monitora o ambiente com PIR e LDR após autenticação bem-sucedida

from machine import Pin, ADC
from utime import ticks_ms, ticks_diff
from utils import led_green, led_red, led_yellow, buzzer
from utils import todos_leds_off, beep

#Pinos - Sensores e LED do IDS
sensor_pir = Pin(27, Pin.IN)
sensor_ldr = ADC(Pin(34))
sensor_ldr.atten(ADC.ATTN_11DB)  # faixa de 0-3.3V
led_blue   = Pin(5, Pin.OUT)

#Constantes
TEMPO_ARMANDO_MS   = 3000   # countdown antes de ativar vigilância (3 segundos)
LIMIAR_LDR_PERCENT = 30     # variação percentual do LDR para detectar anomalia

#Estados
DESARMADO   = "DESARMADO"
ARMANDO     = "ARMANDO"
VIGILANCIA  = "VIGILANCIA"
AVISO       = "AVISO"
ALERTA      = "ALERTA"
CRITICO     = "CRITICO"
LOCKDOWN    = "LOCKDOWN"

#Variáveis
estado_atual   = DESARMADO
tempo_inicio   = 0
ldr_baseline   = 0

#Calibração do LDR — lê 10 amostras e calcula a média como referência
def calibrar_ldr():
    global ldr_baseline
    soma = 0
    for _ in range(10):
        soma += sensor_ldr.read()
    ldr_baseline = soma // 10
    print(f"[IDS] LDR calibrado: baseline = {ldr_baseline}")

#Transição de estados
def transitar(novo_estado):
    global estado_atual, tempo_inicio
    estado_atual = novo_estado
    tempo_inicio = ticks_ms()
    print(f"[IDS] Estado: {novo_estado}")

#Feedback do IDS
def feedback_armando():
    todos_leds_off()
    led_blue.on()
    beep(100, 600)
    print("[IDS] Armando sistema... Saida da zona em 3s.")

def feedback_vigilancia():
    todos_leds_off()
    led_blue.on()
    print("[IDS] Vigilancia ativa.")

def feedback_desarmado():
    led_blue.off()
    print("[IDS] Sistema desarmado.")

#Interface pública para o orquestrador

def armar():
    """Chamado pelo orquestrador quando a autenticação 2FA é concluída."""
    feedback_armando()
    calibrar_ldr()
    transitar(ARMANDO)

def desarmar():
    """Chamado pelo orquestrador no reset."""
    led_blue.off()
    transitar(DESARMADO)
    feedback_desarmado()

def atualizar():
    """Chamado a cada iteração do loop principal.
    Retorna True quando o IDS entra em LOCKDOWN (força re-autenticação)."""

    # Countdown antes de ativar vigilância
    if estado_atual == ARMANDO:
        if ticks_diff(ticks_ms(), tempo_inicio) > TEMPO_ARMANDO_MS:
            feedback_vigilancia()
            transitar(VIGILANCIA)

    # Vigilância ativa — detecção será implementada na próxima etapa
    elif estado_atual == VIGILANCIA:
        pass

    return False
