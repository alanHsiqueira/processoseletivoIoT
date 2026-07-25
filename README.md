# Relatório Técnico: Monitor de Estoque Kanban Inteligente

### Identificação do Candidato
- **Nome completo:** Alan Herculino Siqueira
- **GitHub:** https://github.com/alanHsiqueira

---

### Visão Geral da Solução
O projeto consiste em um sistema automatizado para monitoramento de estoque em tempo real voltado para almoxarifados industriais. Utilizando a variação de peso como indicador, o sistema embarcado identifica a quantidade de insumos disponíveis em uma caixa. O usuário (ou sistema de supervisão) interage de forma passiva, recebendo os alertas seriais para tomada de decisão (abastecimento) de acordo com o nível crítico atingido, prevenindo interrupções na linha de montagem.

---

### Arquitetura do Sistema Embarcado
A lógica do firmware (`main.py`) foi estruturada em um loop contínuo utilizando o conceito de **Máquina de Estados Finita (FSM)**.
- **Fluxo Principal:** O sistema opera sob um polling constante baseado em temporização não-bloqueante (`time.ticks_ms`), permitindo a rápida captura de eventos externos.
- **Estados Lógicos:** 
  1. `ESTADO_INICIAL`: Setup de pinos e inicialização do sistema.
  2. `ESTADO_REGULAR`: Operação normal, reportando dinamicamente mudanças parciais de peso (entre 151g e 4999g).
  3. `ESTADO_ALERTA`: Engatilhado quando o peso atinge o limiar de sub-estoque (<= 150g).
  4. `ESTADO_ERRO`: Estado de segurança isolado caso a leitura retorne peso estrutural zerado.

---

### Componentes Utilizados na Simulação
Conforme modelado no arquivo `diagram.json`, a arquitetura utiliza:
- **ESP32 DevKit C v4:** Placa microcontroladora responsável por orquestrar a lógica, executar o firmware em MicroPython e enviar a telemetria via Serial (UART).
- **Módulo HX711 (Célula de Carga):** Atua como o sensor de peso (ID: `hx711`). Os pinos de comunicação digital (DT) e clock (SCK) foram alocados nas portas 22 e 23 do ESP32, respectivamente, e a alimentação (3V3/GND) conectada diretamente na placa.

---

### Decisões Técnicas Relevantes
- **Abordagem Não-Bloqueante:** O uso da função `time.sleep()` foi estritamente evitado. Optou-se pelo uso de `time.ticks_diff()` para garantir respostas em tempo real, impedindo a perda de quadros durante a execução dos testes automatizados (CI).
- **Driver Embutido:** Como o simulador Wokwi não possui uma biblioteca HX711 nativa no ambiente MicroPython padrão, uma função otimizada (`read_hx711`) de escuta direta de bitshift foi incorporada ao firmware para ler os pulsos lógicos dos pinos.
- **Eficiência do Terminal:** Variáveis de estado (`ultimo_peso_reportado`) foram implementadas para garantir que mensagens de *Estoque Regular* só sejam disparadas na UART quando houver uma alteração real na carga, evitando sobrecarga de I/O.

---

### Resultados Obtidos
O sistema atendeu completamente aos requisitos propostos no escopo:
- Reagiu dinamicamente e com precisão aos cenários de **Consumo Parcial**, atualizando o peso lido em tempo real.
- Executou o **Ciclo Completo** com sucesso, disparando o alerta de caixa vazia apenas uma vez e identificando imediatamente a reposição de carga cheia.
- O filtro lógico identificou a **Anomalia de Leitura** perfeitamente, acionando o estado de alerta de manutenção crítica ao receber o estímulo atípico de 0 gramas.
- Total integração alcançada no ambiente Wokwi CI.