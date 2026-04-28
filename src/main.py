# Orquestrador do Sistema de Segurança IoT
# Gerencia a interação entre os módulos 2FA e IDS

from machine import Pin
from utime import sleep_ms
from utils import btn_f1, btn_f2, btn_rst
import modulo_2fa

print("Teste")
print("=" * 40)
print("Sistema de Seguranca IoT inicializando...")
print("=" * 40)

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

print("Modulos carregados: 2FA")
print("Sistema pronto. Pressione F1 para iniciar autenticacao.")
print("Iniciando loop principal...")

# Loop principal
while True:

    if flag_f1:
        flag_f1 = False
        modulo_2fa.on_btn_f1()

    if flag_f2:
        flag_f2 = False
        modulo_2fa.on_btn_f2()

    if flag_rst:
        flag_rst = False
        modulo_2fa.on_reset()

    # Atualizar máquina de estados do 2FA
    autenticado = modulo_2fa.atualizar()

    if autenticado:
        print("[SISTEMA] Autenticacao concluida com sucesso.")

    sleep_ms(10)