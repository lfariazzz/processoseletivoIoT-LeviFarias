# Sistema de Autenticação de 2 Fatotes robusto - com Proteção contra Força Bruta

from machine import Pin, PWM
from utime import ticks_ms, ticks_diff, sleep_ms

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
    todos_leds_off()
    estado_atual = novo_estado
    tempo_inicio = ticks_ms()
    print(f"Estado: {novo_estado}")

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

# Flags de botões via interrupção 
flag_f1  = False
flag_f2  = False
flag_rst = False

def isr_f1(pin):
    global flag_f1
    flag_f1 = True

def isr_f2(pin):
    global flag_f2
    flag_f2 = True

def isr_rst(pin):
    global flag_rst
    flag_rst = True

btn_f1.irq(trigger=Pin.IRQ_FALLING, handler=isr_f1)
btn_f2.irq(trigger=Pin.IRQ_FALLING, handler=isr_f2)
btn_rst.irq(trigger=Pin.IRQ_FALLING, handler=isr_rst)

print("Iniciando loop principal...")

while True:

    # Aguarda início
    if flag_f1:
        flag_f1 = False
        if estado_atual == IDLE:
            feedback_aguardando()
            transitar(FATOR1)

    # Fator 1 — aguardando fator 2 dentro do tempo
    if flag_f2:
        flag_f2 = False
        if estado_atual == FATOR1:
            tentativas += 1
            if not verificar_bloqueio():
                feedback_aprovado()
                transitar(APROVADO)

    # Reset Manual
    if flag_rst:
        flag_rst = False
        buzzer.duty(0)
        tentativas = 0
        print("Reset manual.")
        transitar(IDLE)

    # Fator 1 — LED amarelo piscando enquanto aguarda fator 2
    if estado_atual == FATOR1:
        led_yellow.on()
        if ticks_diff(ticks_ms(), tempo_inicio) > TIMEOUT_F2_MS:
            tentativas += 1
            feedback_negado()
            print("Tempo esgotado.")
            if not verificar_bloqueio():
                transitar(EXPIRADO)

    # Status aprovado
    elif estado_atual == APROVADO:
        if ticks_diff(ticks_ms(), tempo_inicio) > 3000:
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

    sleep_ms(10)