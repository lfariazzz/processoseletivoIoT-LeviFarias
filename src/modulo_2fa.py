# Módulo de Autenticação de 2 Fatores - com Proteção contra Força Bruta
# Máquina de estados para controle de acesso

from utime import ticks_ms, ticks_diff
from utils import led_green, led_red, led_yellow, buzzer
from utils import todos_leds_off, beep

#Constantes
TIMEOUT_F2_MS     = 5000   # janela de tempo para o fator 2 (5 segundos)
MAX_TENTATIVAS    = 3      # tentativas antes de bloquear
TEMPO_BLOQUEIO_MS = 10000  # tempo de bloqueio após falhas (10 segundos)

#Estados
IDLE      = "IDLE"
FATOR1    = "FATOR1"
APROVADO  = "APROVADO"
EXPIRADO  = "EXPIRADO"
BLOQUEADO = "BLOQUEADO"

#Variáveis
estado_atual   = IDLE
tentativas     = 0
tempo_inicio   = 0

#Feedback visual e sonoro
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

#Transição de estados
def transitar(novo_estado):
    global estado_atual, tempo_inicio
    todos_leds_off()
    estado_atual = novo_estado
    tempo_inicio = ticks_ms()
    print(f"[2FA] Estado: {novo_estado}")

# Proteção contra força bruta:
# Após MAX_TENTATIVAS falhas consecutivas, o sistema bloqueia por
# TEMPO_BLOQUEIO_MS milissegundos antes de aceitar novas tentativas.
# O contador só é zerado após autenticação bem-sucedida ou reset manual.

def verificar_bloqueio():
    global tentativas
    if tentativas >= MAX_TENTATIVAS:
        feedback_bloqueado()
        transitar(BLOQUEADO)
        return True
    restantes = MAX_TENTATIVAS - tentativas
    print(f"Tentativas restantes: {restantes}")
    return False

#Handlers de botões — chamados pelo orquestrador

def on_btn_f1():
    if estado_atual == IDLE:
        feedback_aguardando()
        transitar(FATOR1)

def on_btn_f2():
    global tentativas
    if estado_atual == FATOR1:
        tentativas += 1
        if not verificar_bloqueio():
            feedback_aprovado()
            transitar(APROVADO)

def on_reset():
    global tentativas
    buzzer.duty(0)
    tentativas = 0
    print("Reset manual.")
    transitar(IDLE)

# Loop — chamado a cada iteração do loop principal
# Retorna True quando a autenticação foi concluída com sucesso
# (transição APROVADO → IDLE), para sinalizar ao orquestrador.

def atualizar():
    global tentativas

    # Fator 1 — LED amarelo enquanto aguarda fator 2
    if estado_atual == FATOR1:
        led_yellow.on()
        if ticks_diff(ticks_ms(), tempo_inicio) > TIMEOUT_F2_MS:
            tentativas += 1
            feedback_negado()
            print("Tempo esgotado.")
            if not verificar_bloqueio():
                transitar(EXPIRADO)

    # Status aprovado — aguarda 3s e sinaliza conclusão
    elif estado_atual == APROVADO:
        if ticks_diff(ticks_ms(), tempo_inicio) > 3000:
            transitar(IDLE)
            return True

    # Status expirado — timeout
    elif estado_atual == EXPIRADO:
        if ticks_diff(ticks_ms(), tempo_inicio) > 2000:
            transitar(IDLE)

    # Status bloqueado — aguarda tempo de bloqueio
    elif estado_atual == BLOQUEADO:
        if ticks_diff(ticks_ms(), tempo_inicio) > TEMPO_BLOQUEIO_MS:
            tentativas = 0
            feedback_desbloqueado()
            transitar(IDLE)

    return False
