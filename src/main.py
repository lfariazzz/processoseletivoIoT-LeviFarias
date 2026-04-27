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

# Loop principal — máquina de estados 

def transitar(novo_estado):
    global estado_atual, tempo_inicio
    estado_atual = novo_estado
    tempo_inicio = ticks_ms()
    print(f"Estado: {novo_estado}")

def botao_pressionado(pino):
    global ultimo_botao
    agora = ticks_ms()
    if pino.value() == 0:
        if ticks_diff(agora, ultimo_botao) > DEBOUNCE_MS:
            ultimo_botao = agora
            return True
    return False

# Proteção contra força bruta:
# Após MAX_TENTATIVAS falhas consecutivas, o sistema bloqueia por TEMPO_BLOQUEIO_MS milissegundos antes de aceitar novas tentativas.
# O contador só é zerado após autenticação bem-sucedida ou reset manual.

def verificar_bloqueio():
    if tentativas >= MAX_TENTATIVAS:
        feedback_bloqueado()
        transitar(BLOQUEADO)
        return True
    restantes = MAX_TENTATIVAS - tentativas
    print(f"Tentativas restantes: {restantes}")
    return False

print("Iniciando loop principal...")

while True:

    # Aguarda início
    if estado_atual == IDLE:
        todos_leds_off()
        if botao_pressionado(btn_f1):
            feedback_aguardando()
            transitar(FATOR1)

    # Fator 1 — aguardando fator 2 dentro do tempo 
    elif estado_atual == FATOR1:
        led_yellow.on()
        if botao_pressionado(btn_f2):
            tentativas += 1
            if not verificar_bloqueio():
                feedback_aprovado()
                transitar(APROVADO)

    # Status aprovado
    elif estado_atual == APROVADO:
        if ticks_diff(ticks_ms(), tempo_inicio) > 3000:
            tentativas = 0
            transitar(IDLE)

    # Status Expirado - Timeout
    elif estado_atual == EXPIRADO:
        if ticks_diff(ticks_ms(), tempo_inicio) > 2000:
            transitar(IDLE)

    # Status bloqueado - Aguarda tempo de bloqueio
    elif estado_atual == BLOQUEADO:
        if ticks_diff(ticks_ms(), tempo_inicio) > TEMPO_BLOQUEIO_MS:
            tentativas = 0
            feedback_desbloqueado()
            transitar(IDLE)

    # Reset Manual
    if botao_pressionado(btn_rst):
        buzzer.duty(0)
        tentativas = 0
        print("Reset manual.")
        transitar(IDLE)