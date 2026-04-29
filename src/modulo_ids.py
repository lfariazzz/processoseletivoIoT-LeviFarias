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
TEMPO_ESCALACAO_MS = 5000   # tempo em ALERTA antes de escalar para CRITICO (5 segundos)
TEMPO_LOCKDOWN_MS  = 10000  # tempo em CRITICO antes de LOCKDOWN (10 segundos)

#Estados
DESARMADO   = "DESARMADO"
ARMANDO     = "ARMANDO"
VIGILANCIA  = "VIGILANCIA"
AVISO       = "AVISO"
ALERTA      = "ALERTA"
CRITICO     = "CRITICO"
LOCKDOWN    = "LOCKDOWN"

#Variáveis de estado
estado_atual      = DESARMADO
tempo_inicio      = 0
ldr_baseline      = 0
tempo_anomalia    = 0     # quando a anomalia começou (para escalação)
anomalia_ativa    = False # se há anomalia em curso
ultimo_feedback   = 0     # último momento que feedback foi emitido (evita flood)

#Calibração do LDR — lê 10 amostras e calcula a média como referência
def calibrar_ldr():
    global ldr_baseline
    soma = 0
    for _ in range(10):
        soma += sensor_ldr.read()
    ldr_baseline = soma // 10
    print(f"[IDS] LDR calibrado: baseline = {ldr_baseline}")

#Leitura dos sensores
def ler_pir():
    # PIR retorna 1 (HIGH) quando detecta movimento
    return sensor_pir.value() == 1

def ler_ldr():
    # Compara leitura atual com o baseline calibrado
    # Retorna True se a variação exceder o limiar percentual
    leitura = sensor_ldr.read()
    if ldr_baseline == 0:
        return False
    variacao = abs(leitura - ldr_baseline) * 100 // ldr_baseline
    return variacao > LIMIAR_LDR_PERCENT

#Fusão de sensores — determina nível de ameaça combinando PIR e LDR
# Movimento isolado (PIR) = pode ser falso positivo (vento, animal)
# Movimento + variação de luz (PIR + LDR) = provável intrusão real
def avaliar_ameaca():
    movimento = ler_pir()
    luz_anormal = ler_ldr()

    if movimento and luz_anormal:
        return ALERTA    # provável intrusão
    elif movimento:
        return AVISO     # possível falso positivo
    else:
        return None      # sem ameaça

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
    todos_leds_off()
    buzzer.duty(0)
    print("[IDS] Sistema desarmado.")

# Feedback não-bloqueante por nível de ameaça
# Usa temporização para alternar LEDs sem travar o loop
def feedback_aviso():
    # LED amarelo pisca + beep curto
    todos_leds_off()
    led_blue.on()
    led_yellow.on()
    beep(50, 800)

def feedback_alerta():
    # LED vermelho pisca + buzzer intermitente
    todos_leds_off()
    led_blue.on()
    led_red.on()
    buzzer.freq(600)
    buzzer.duty(512)

def feedback_critico():
    # LED vermelho fixo + buzzer contínuo agudo
    todos_leds_off()
    led_blue.on()
    led_red.on()
    led_yellow.on()
    buzzer.freq(1000)
    buzzer.duty(512)

def parar_alarme():
    buzzer.duty(0)
    todos_leds_off()
    led_blue.on()

#Interface pública para o orquestrador

def armar():
    # Chamado pelo orquestrador quando a autenticação 2FA é concluída
    feedback_armando()
    calibrar_ldr()
    transitar(ARMANDO)

def desarmar():
    # Chamado pelo orquestrador no reset
    global anomalia_ativa, tempo_anomalia, ultimo_feedback
    anomalia_ativa = False
    tempo_anomalia = 0
    ultimo_feedback = 0
    led_blue.off()
    buzzer.duty(0)
    transitar(DESARMADO)
    feedback_desarmado()

def atualizar():
    # Chamado a cada iteração do loop principal
    # Retorna True quando o IDS entra em LOCKDOWN (força re-autenticação)
    global anomalia_ativa, tempo_anomalia, ultimo_feedback

    # Countdown antes de ativar vigilância
    if estado_atual == ARMANDO:
        if ticks_diff(ticks_ms(), tempo_inicio) > TEMPO_ARMANDO_MS:
            feedback_vigilancia()
            transitar(VIGILANCIA)

    # Vigilância ativa — detecção multi-modal
    elif estado_atual == VIGILANCIA:
        ameaca = avaliar_ameaca()

        if ameaca:
            # Início de nova anomalia — registra timestamp
            if not anomalia_ativa:
                anomalia_ativa = True
                tempo_anomalia = ticks_ms()
                print(f"[IDS] Anomalia detectada: {ameaca}")

            # Transita para o nível de ameaça detectado
            if ameaca == ALERTA and estado_atual != ALERTA:
                transitar(ALERTA)
            elif ameaca == AVISO and estado_atual == VIGILANCIA:
                transitar(AVISO)
        else:
            # Sem ameaça — volta para vigilância normal se estava em AVISO
            if anomalia_ativa:
                anomalia_ativa = False
                tempo_anomalia = 0
                print("[IDS] Anomalia cessou. Retornando a vigilancia.")
                transitar(VIGILANCIA)

    # Em AVISO — monitora se a ameaça persiste ou escala
    elif estado_atual == AVISO:
        ameaca = avaliar_ameaca()

        # Feedback periódico (a cada 500ms para não travar)
        if ticks_diff(ticks_ms(), ultimo_feedback) > 500:
            feedback_aviso()
            ultimo_feedback = ticks_ms()

        if ameaca == ALERTA:
            print("[IDS] Ameaca escalou: movimento + luz anormal")
            feedback_alerta()
            transitar(ALERTA)
        elif not ameaca:
            anomalia_ativa = False
            tempo_anomalia = 0
            parar_alarme()
            print("[IDS] Ameaca cessou. Retornando a vigilancia.")
            transitar(VIGILANCIA)

    # Em ALERTA — escalação temporal para CRITICO após 5s
    elif estado_atual == ALERTA:
        ameaca = avaliar_ameaca()

        # Feedback periódico
        if ticks_diff(ticks_ms(), ultimo_feedback) > 300:
            feedback_alerta()
            ultimo_feedback = ticks_ms()

        # Escalação: ALERTA persistente > 5s → CRITICO
        if anomalia_ativa and ticks_diff(ticks_ms(), tempo_anomalia) > TEMPO_ESCALACAO_MS:
            print("[IDS] Ameaca persistente! Escalando para CRITICO.")
            print("[IDS] !!! INTRUSAO CONFIRMADA !!!")
            feedback_critico()
            transitar(CRITICO)
        elif not ameaca:
            anomalia_ativa = False
            tempo_anomalia = 0
            parar_alarme()
            print("[IDS] Ameaca cessou. Retornando a vigilancia.")
            transitar(VIGILANCIA)

    # Em CRITICO — escalação para LOCKDOWN após 10s
    elif estado_atual == CRITICO:
        # Feedback contínuo
        if ticks_diff(ticks_ms(), ultimo_feedback) > 200:
            feedback_critico()
            ultimo_feedback = ticks_ms()

        # Escalação: CRITICO persistente > 10s → LOCKDOWN
        if ticks_diff(ticks_ms(), tempo_anomalia) > TEMPO_LOCKDOWN_MS:
            print("[IDS] LOCKDOWN ATIVADO! Re-autenticacao necessaria.")
            buzzer.duty(0)
            transitar(LOCKDOWN)
            return True

        ameaca = avaliar_ameaca()
        if not ameaca:
            anomalia_ativa = False
            tempo_anomalia = 0
            parar_alarme()
            print("[IDS] Ameaca cessou. Retornando a vigilancia.")
            transitar(VIGILANCIA)

    return False
