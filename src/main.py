import machine
import time

# --- Configuração dos Pinos do HX711 ---
DT_PIN = 22
SCK_PIN = 23

pin_dt = machine.Pin(DT_PIN, machine.Pin.IN)
pin_sck = machine.Pin(SCK_PIN, machine.Pin.OUT)

# Função simplificada para ler o HX711 no simulador
def read_hx711():
    count = 0
    while pin_dt.value() == 1:
        pass
    for _ in range(24):
        pin_sck.value(1)
        count = count << 1
        pin_sck.value(0)
        if pin_dt.value() == 0:
            count += 1
    pin_sck.value(1)
    pin_sck.value(0)
    
    # O Wokwi retorna o peso ajustado no valor bruto usando fator padrão na simulação (aprox 419.8)
    # Essa divisão simples normaliza a leitura para as gramas que o simulador envia:
    peso = int(count / 419.8)
    return peso

# --- Máquina de Estados ---
ESTADO_INICIAL = 0
ESTADO_REGULAR = 1
ESTADO_ALERTA = 2
ESTADO_ERRO = 3

estado_atual = ESTADO_INICIAL
ultimo_peso_reportado = -1

# Variáveis para controle de tempo não-bloqueante
ultimo_tempo_leitura = time.ticks_ms()
INTERVALO_LEITURA_MS = 100 

print("Sistema Kanban Inicializado")

while True:
    tempo_atual = time.ticks_ms()
    
    # Executa a leitura apenas se o intervalo não-bloqueante foi atingido
    if time.ticks_diff(tempo_atual, ultimo_tempo_leitura) >= INTERVALO_LEITURA_MS:
        ultimo_tempo_leitura = tempo_atual
        
        peso = read_hx711()
        
        # 1. Validação de Anomalia
        if peso <= 0:
            if estado_atual != ESTADO_ERRO:
                print("ALERTA: Caixa ausente ou erro de calibração no sensor HX711!")
                estado_atual = ESTADO_ERRO
        
        # 2. Caixa Vazia (Consumo Crítico)
        elif peso > 0 and peso <= 150:
            if estado_atual != ESTADO_ALERTA:
                print("Evento de reposição disparado! Caixa vazia detectada.")
                estado_atual = ESTADO_ALERTA
                
        # 3. Caixa Cheia (Reabastecimento)
        elif peso >= 4900:  # Margem de tolerância para 5000g
            if estado_atual == ESTADO_ALERTA:
                print("Abastecimento concluído. Caixa cheia.")
            estado_atual = ESTADO_REGULAR
            ultimo_peso_reportado = -1 # Reseta para forçar a impressão de estoque regular caso volte a cair
            
        # 4. Consumo Parcial (Estoque Regular)
        elif peso > 150 and peso < 4900:
            # Só reporta se o peso mudou para não floodar o terminal
            if peso != ultimo_peso_reportado:
                print(f"Status: Estoque Regular ({peso}g)")
                ultimo_peso_reportado = peso
                estado_atual = ESTADO_REGULAR