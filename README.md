# Processo Seletivo – Intensivo Maker | IoT

---

### 👤 Identificação do Candidato

- **Nome completo:** Levi Farias Leite
- **GitHub:** [lfariazzz](https://github.com/lfariazzz)

---

## 1️⃣ Visão Geral da Solução

O projeto simula um sistema de segurança física em duas camadas: autenticação por dois fatores (2FA) para controle de acesso e detecção de intrusão (IDS) para monitorar o ambiente após a entrada. O desenvolvimento ocorreu em duas fases — a primeira entregou o módulo 2FA isolado; a segunda expandiu para um sistema integrado com IDS, orquestrador e registro de eventos.

O usuário interage com o sistema via dois botões de autenticação (F1 e F2) e um botão de reset (RST). O feedback é dado por LEDs coloridos e buzzer.

---

## 2️⃣ Arquitetura do Sistema Embarcado

### Fase 1 — até 27/04 | Módulo 2FA standalone

O módulo implementa uma máquina de estados com proteção contra força bruta:

```
IDLE → FATOR1 → APROVADO → IDLE
              → EXPIRADO → IDLE
              → BLOQUEADO → IDLE  (desbloqueio automático após 10s)
```

F1 inicia a autenticação; F2 precisa ser pressionado dentro de 5 segundos. Três falhas consecutivas travam o sistema. O contador de tentativas só é zerado após reset manual ou desbloqueio automático — não após um sucesso — para impedir que tentativas intercaladas com acertos anulem a proteção.

### Fase 2 — até 04/05 | Sistema completo com IDS

O código foi reorganizado em quatro módulos com responsabilidades claras:

```
main.py  ←  orquestrador
├── modulo_2fa.py   — autenticação, sinaliza conclusão
├── modulo_ids.py   — vigilância, sinaliza lockdown
├── log.py          — registro de eventos com timestamp
└── utils.py        — hardware compartilhado
```

O `main.py` não contém lógica de negócio: despacha eventos de botão e reage ao que os módulos retornam. O IDS é armado automaticamente quando o 2FA conclui; se o IDS entra em lockdown, o 2FA é resetado forçando nova autenticação.

```
[F1/F2/RST] → main.py → modulo_2fa → retorna "autenticado"
                                ↓
                         modulo_ids.armar()
                                ↓ retorna "lockdown"
                         modulo_2fa.on_reset()
```

O módulo IDS implementa escalação progressiva de ameaças:

```
DESARMADO → ARMANDO (3s) → VIGILANCIA
                                ↓ PIR ativo
                              AVISO → VIGILANCIA (ameaça cessa)
                                ↓ PIR + LDR simultâneos
                              ALERTA → VIGILANCIA (ameaça cessa)
                                ↓ persistente > 5s
                              CRITICO
                                ↓ persistente > 10s
                              LOCKDOWN → força re-autenticação
```

---

## 3️⃣ Componentes Utilizados na Simulação

**Placa:** ESP32 DevKit C V4 com MicroPython

| Componente | GPIO | Módulo | Função |
|---|---|---|---|
| LED Verde | GPIO21 | 2FA | Acesso autorizado |
| LED Vermelho | GPIO19 | 2FA / IDS | Acesso negado / alerta |
| LED Amarelo | GPIO18 | 2FA / IDS | Aguardando fator 2 / aviso |
| LED Azul | GPIO5 | IDS | Vigilância ativa |
| Botão F1 | GPIO13 | 2FA | Primeiro fator |
| Botão F2 | GPIO12 | 2FA | Segundo fator |
| Botão RST | GPIO14 | Orquestrador | Reset geral |
| Buzzer | GPIO26 | 2FA / IDS | Feedback sonoro (PWM) |
| Sensor PIR | GPIO27 | IDS | Detecção de movimento |
| Sensor LDR | GPIO34 (ADC) | IDS | Detecção de variação de luz |

---

## 4️⃣ Decisões Técnicas Relevantes

**Padrão orquestrador com módulos independentes:** A alternativa seria um único arquivo monolítico. A opção modular foi tomada já na Fase 1 — e foi o que tornou possível adicionar o IDS na Fase 2 sem tocar no código do 2FA. Cada módulo expõe apenas três funções públicas e não conhece a existência do outro; o orquestrador é o único ponto de integração.

**Interrupção por hardware (IRQ) nos botões:** Polling no Wokwi apresentou cliques perdidos porque o loop principal é mais lento que a interação do usuário. IRQ garante que cada acionamento seja registrado como uma flag booleana, processada na próxima iteração do loop, independente da velocidade de execução.

**Temporização não-bloqueante com `ticks_ms()`:** `sleep()` travaria o loop inteiro durante cada espera — impossível manter múltiplos temporizadores simultâneos (timeout do 2FA, escalação do IDS, feedback periódico de LEDs). `ticks_ms()` + `ticks_diff()` permitem verificar cada timer a cada iteração sem bloquear os demais.

**Fusão de sensores PIR + LDR:** PIR isolado gera falsos positivos com facilidade (correntes de ar, variações de temperatura). LDR isolado não detecta presença em ambientes com iluminação estável. A combinação dos dois eleva a confiança da detecção: apenas quando ambos disparam simultaneamente o sistema classifica como ALERTA. Movimento isolado gera apenas AVISO, com retorno automático à vigilância se a ameaça cessar.

**Calibração dinâmica do LDR:** O threshold de luminosidade não está fixo em código — é calculado como média de 10 leituras no momento exato em que o IDS é armado. Um valor fixo falharia em ambientes com iluminação diferente da esperada; calibrar no momento do arme adapta o sistema às condições reais sem custo extra.

**Buffer circular no log:** Uma lista sem limite cresceria indefinidamente em memória — em MicroPython no ESP32, isso resulta em `MemoryError` em sessões longas. O limite de 20 entradas garante que o sistema nunca falhe por falta de memória, descartando os eventos mais antigos quando o buffer enche.

---

## 5️⃣ Resultados Obtidos

**Fase 1 — módulo 2FA:** O sistema autenticou corretamente em todos os cenários testados: sucesso (F1 → F2 em até 5s), timeout (sem F2 em 5s) e bloqueio após três falhas consecutivas com desbloqueio automático em 10s. A janela de 5 segundos se mostrou adequada — confortável para interação humana e curta o suficiente para que tentativas automatizadas não consigam preparar uma resposta entre os dois fatores.

**Fase 2 — sistema completo:** A cadeia de escalação funcionou conforme projetado. O ponto mais importante observado foi a interação entre o threshold de 30% do LDR e o timer de 5 segundos para escalar de ALERTA para CRITICO: uma variação de luz passageira (sombra, reflexo) não aciona o lockdown porque a anomalia precisa ser sustentada. Uma intrusão real — movimento contínuo com variação de luz persistente — atingiu LOCKDOWN de forma consistente nos testes. O log foi impresso corretamente no Serial Monitor ao entrar em lockdown, com os eventos de cada módulo em ordem cronológica.

O pipeline de CI/CD executa sem falhas — o GitHub Actions builda o firmware via Docker, gera o `fs.bin` e valida a simulação via Wokwi CLI.

---

## 6️⃣ Comentários Adicionais

**Dificuldades:** A configuração dos pinos no `diagram.json` exigiu iteração — o Wokwi usa `esp:21` e não `esp:GPIO21`. O feedback periódico nos estados de alerta do IDS (LEDs piscando, buzzer intermitente) inicialmente travava o loop; a solução foi aplicar a mesma lógica de `ticks_ms()` usada nos timers de estado.

**Limitações:** O buffer de 20 eventos no log pode ser insuficiente em sessões com muitas tentativas de autenticação — eventos iniciais seriam descartados, o que comprometeria uma análise forense completa. Mais importante: PIR e LDR compartilham uma vulnerabilidade fundamental — ambos detectam presença pelos mesmos fenômenos físicos. Um sistema real precisaria de modalidades adicionais (sensor térmico, vibração) para cobrir vetores de ataque que os dois não capturam.

**Aprendizado principal:** A decisão de modularizar o código desde a Fase 1 — quando só existia o 2FA — foi validada diretamente pela Fase 2. O IDS foi integrado sem nenhuma alteração no módulo de autenticação. Isso confirmou na prática que pensar na extensibilidade da arquitetura antes de precisar dela tem valor concreto, não apenas teórico.
