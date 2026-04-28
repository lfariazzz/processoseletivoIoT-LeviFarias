# Funções e hardware compartilhados entre módulos

from machine import Pin, PWM
from utime import ticks_ms, ticks_diff, sleep_ms

#Pinos - LEDs
led_green  = Pin(21, Pin.OUT)
led_red    = Pin(19, Pin.OUT)
led_yellow = Pin(18, Pin.OUT)

#Buzzer
buzzer = PWM(Pin(26), freq=1000, duty=0)

#Botões
btn_f1  = Pin(13, Pin.IN, Pin.PULL_UP)
btn_f2  = Pin(12, Pin.IN, Pin.PULL_UP)
btn_rst = Pin(14, Pin.IN, Pin.PULL_UP)

#Leds e Buzzer
def todos_leds_off():
    led_green.off()
    led_red.off()
    led_yellow.off()

def beep(duracao_ms=100, freq=1000):
    buzzer.freq(freq)
    buzzer.duty(512)
    sleep_ms(duracao_ms)
    buzzer.duty(0)
