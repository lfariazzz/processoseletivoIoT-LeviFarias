# Processo Seletivo – Intensivo Maker | IoT

---

### 👤 Identificação do Candidato

- **Nome completo:** Levi Farias Leite
- **GitHub:** [lfariazzz](https://github.com/lfariazzz)

---

## 1️⃣ Visão Geral da Solução

O projeto simula um **painel de autenticação de dois fatores (2FA)** para controle de acesso físico, semelhante aos sistemas utilizados em datacenters, salas de servidor e laboratórios de TI.

O sistema exige que o usuário apresente dois fatores de autenticação em sequência dentro de um intervalo de tempo. Caso o usuário falhe repetidamente, o sistema aplica um bloqueio temporário como proteção contra ataques de força bruta.

O usuário interage com o sistema através de dois botões de autenticação (F1 e F2) e um botão de reset (RST). O feedback é fornecido visualmente via LEDs coloridos e sonoramente via buzzer.

---

## 2️⃣ Arquitetura do Sistema Embarcado

### Fluxo principal

O programa inicializa os periféricos, registra as interrupções dos botões e entra no loop principal, onde a máquina de estados é executada continuamente.

A detecção dos botões utiliza **IRQ (interrupção por hardware)** com trigger `IRQ_FALLING` — garantindo que nenhum clique seja perdido independentemente da velocidade do loop. Flags booleanas são setadas nas ISRs e processadas no loop principal.

A temporização utiliza `ticks_ms()` e `ticks_diff()` — abordagem **não-bloqueante** que permite ao sistema monitorar múltiplos temporizadores simultaneamente sem travar o loop.

### Máquina de estados

```
IDLE → FATOR1 → APROVADO → IDLE
              → EXPIRADO → IDLE
              → BLOQUEADO → IDLE (após 10s)
```

| Estado | Condição de entrada | Condição de saída |
|---|---|---|
| IDLE | Inicialização ou reset | F1 pressionado |
| FATOR1 | F1 pressionado | F2 pressionado (→ APROVADO) ou timeout 5s (→ EXPIRADO) |
| APROVADO | F2 pressionado corretamente | 3 segundos |
| EXPIRADO | Timeout do fator 2 | 2 segundos |
| BLOQUEADO | 3 tentativas falhas | 10 segundos |

### Temporização não-bloqueante

```python
# Em vez de sleep(5) que trava tudo:
if ticks_diff(ticks_ms(), tempo_inicio) > TIMEOUT_F2_MS:
    # ação após 5 segundos
```

---

## 3️⃣ Componentes Utilizados na Simulação

| Componente | GPIO | Tipo | Função |
|---|---|---|---|
| LED Verde | GPIO21 | Saída digital | Acesso autorizado |
| LED Vermelho | GPIO19 | Saída digital | Acesso negado / sistema bloqueado |
| LED Amarelo | GPIO18 | Saída digital | Aguardando fator 2 |
| Botão F1 | GPIO13 | Entrada (PULL_UP) | Primeiro fator de autenticação |
| Botão F2 | GPIO12 | Entrada (PULL_UP) | Segundo fator de autenticação |
| Botão RST | GPIO14 | Entrada (PULL_UP) | Reset manual do sistema |
| Buzzer | GPIO26 | PWM | Feedback sonoro de alerta |

**Placa:** ESP32 DevKit C V4 com MicroPython

---

## 4️⃣ Decisões Técnicas Relevantes

**IRQ ao invés de polling:** A detecção de botões utiliza interrupções por hardware (`Pin.IRQ_FALLING`) em vez de verificação contínua no loop. Isso garante que nenhum clique seja perdido e reduz o custo computacional do loop principal.

**Temporização não-bloqueante:** O uso de `ticks_ms()` e `ticks_diff()` permite que múltiplos temporizadores rodem em paralelo — timeout do fator 2, tempo de bloqueio e tempo de exibição do resultado — sem que um bloqueie o outro.

**Contador de tentativas persistente:** O contador só é zerado após reset manual (RST) ou após o desbloqueio automático — não após autenticação bem-sucedida. Isso garante que tentativas de força bruta intercaladas com sucessos não resetem a proteção.

**Feedback multimodal:** Cada estado tem feedback visual (LED) e sonoro (buzzer) distintos, facilitando a identificação do estado mesmo sem acesso ao Serial Monitor — comportamento esperado em sistemas embarcados reais.

---

## 5️⃣ Resultados Obtidos

O sistema funciona corretamente na simulação Wokwi:

- **Autenticação bem-sucedida:** F1 → F2 dentro de 5s → LED verde + "ACESSO AUTORIZADO"
- **Timeout:** F1 → aguarda 5s sem F2 → LED vermelho + "ACESSO NEGADO"
- **Bloqueio:** 3 timeouts consecutivos → LED vermelho fixo + buzzer contínuo + "SISTEMA BLOQUEADO"
- **Desbloqueio automático:** após 10s → "Sistema desbloqueado"
- **Reset manual:** RST a qualquer momento → retorno imediato ao IDLE

O pipeline de CI/CD executa com sucesso — o GitHub Actions builda o firmware via Docker, gera o `fs.bin` e valida a simulação via Wokwi CLI.

---

## 6️⃣ Comentários Adicionais

**Dificuldades encontradas:** A configuração correta dos pinos no `diagram.json` para o `board-esp32-devkit-c-v4` exigiu iteração — o formato correto usa números simples (`esp:21`) ao invés de prefixos (`esp:GPIO21`). A detecção de botões via polling no loop principal não funcionou adequadamente no Wokwi, sendo necessário migrar para IRQ.

**Limitações:** O sistema simula 2FA com dois botões físicos — em produção, os fatores seriam tecnologias distintas como RFID + PIN ou biometria + token. O tempo de bloqueio de 10 segundos é adequado para demonstração mas seria maior em ambiente real.

**Aprendizados:** O projeto evidenciou a importância da temporização não-bloqueante em sistemas embarcados — `sleep()` trava o sistema inteiro, enquanto `ticks_ms()` permite múltiplas tarefas simultâneas. A máquina de estados se mostrou essencial para manter o comportamento previsível e auditável do sistema.