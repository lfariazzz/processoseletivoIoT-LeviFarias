# Sistema de Autenticação de 2 Fatotes robusto - com Proteção contra Força Bruta

from machine import Pin, PWM
from utime import ticks_ms, ticks_diff

print("Teste")
print("=" * 40)
print("Sistema 2FA inicializando...")
print("=" * 40)

#Pinos
led_green  = Pin(21, Pin.OUT)
led_red    = Pin(19, Pin.OUT)
led_yellow = Pin(18, Pin.OUT)

btn_f1  = Pin(13, Pin.IN, Pin.PULL_UP)
btn_f2  = Pin(12, Pin.IN, Pin.PULL_UP)
btn_rst = Pin(14, Pin.IN, Pin.PULL_UP)

buzzer = PWM(Pin(26), freq=1000, duty=0)

#Constantes
TIMEOUT_F2_MS     = 5000   # janela de tempo para o fator 2 (5 segundos)
MAX_TENTATIVAS    = 3      # tentativas antes de bloquear
TEMPO_BLOQUEIO_MS = 10000  # tempo de bloqueio após falhas (10 segundos)
DEBOUNCE_MS       = 200    # debounce dos botões

#Estados
IDLE      = "IDLE"
FATOR1    = "FATOR1"
FATOR2    = "FATOR2"
APROVADO  = "APROVADO"
EXPIRADO  = "EXPIRADO"
BLOQUEADO = "BLOQUEADO"

#Variáveis
estado_atual   = IDLE
tentativas     = 0
tempo_inicio   = 0
ultimo_botao   = 0

print("Sistema pronto. Pressione F1 para iniciar autenticacao.")

#Leds e Buzzers
def todos_leds_off():
    led_green.off()
    led_red.off()
    led_yellow.off()

def beep(duracao_ms=100, freq=1000):
    buzzer.freq(freq)
    buzzer.duty(512)
    from utime import sleep_ms
    sleep_ms(duracao_ms)
    buzzer.duty(0)

def feedback_aprovado():
    todos_leds_off()
    led_green.on()
    beep(200, 1200)
    print("ACESSO AUTORIZADO")

def feedback_negado():
    todos_leds_off()
    led_red.on()
    beep(500, 400)
    print("ACESSO NEGADO")

def feedback_aguardando():
    todos_leds_off()
    led_yellow.on()
    beep(50, 800)
    print("Aguardando fator 2...")

def feedback_bloqueado():
    todos_leds_off()
    led_red.on()
    buzzer.freq(300)
    buzzer.duty(512)
    print("SISTEMA BLOQUEADO!")

def feedback_desbloqueado():
    buzzer.duty(0)
    todos_leds_off()
    print("Sistema desbloqueado. Aguardando...")

print("Funcoes de feedback carregadas.")