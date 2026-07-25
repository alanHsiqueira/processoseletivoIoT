import machine
import time

# --- Configuração dos Pinos do HX711 ---
DT_PIN = 22
SCK_PIN = 23

pin_dt = machine.Pin(DT_PIN, machine.Pin.IN)
pin_sck = machine.Pin(SCK_PIN, machine.Pin.OUT)
pin_sck.value(0)

def read_hx711():
    # Leitura 100% não-bloqueante: se o pino estiver em 1, não está pronto.
    # O loop principal continua rodando sem travar o simulador.
    if pin_dt.value() == 1:
        return None
    
    count = 0
    for _ in range(24):
        pin_sck.value(1)
        count = count << 1
        pin_sck.value(0)
        if pin_dt.value() == 1:
            count += 1
    
    # 25º pulso de clock para finalizar a leitura (ganho 128)
    pin_sck.value(1)
    pin_sck.value(0)
    
    # Tratamento matemático de sinal (Complemento de Dois de 24 bits)
    if count & 0x800000:
        count -= 0x1000000
        
    # O Wokwi simula o peso usando exatamente o fator 420.0
    peso = int(count / 420.0)
    return peso

# --- Máquina de Estados ---
ESTADO_INICIAL = 0
ESTADO_REGULAR = 1
ESTADO_ALERTA = 2
ESTADO_ERRO = 3

estado_atual = ESTADO_INICIAL
ultimo_peso_reportado = -1

ultimo_tempo_leitura = time.ticks_ms()
INTERVALO_LEITURA_MS = 100 

print("Sistema Kanban Inicializado")

while True:
    tempo_atual = time.ticks_ms()
    
    if time.ticks_diff(tempo_atual, ultimo_tempo_leitura) >= INTERVALO_LEITURA_MS:
        ultimo_tempo_leitura = tempo_atual
        
        peso = read_hx711()
        
        if peso is not None:
            # 1. Validação de Anomalia (0g)
            if peso <= 0:
                if estado_atual != ESTADO_ERRO:
                    print("ALERTA: Caixa ausente ou erro de calibração no sensor HX711!")
                    estado_atual = ESTADO_ERRO
            
            # 2. Caixa Vazia / Consumo Crítico (<= 150g)
            elif peso > 0 and peso <= 150:
                if estado_atual != ESTADO_ALERTA:
                    print("Evento de reposição disparado! Caixa vazia detectada.")
                    estado_atual = ESTADO_ALERTA
                    
            # 3. Caixa Cheia / Reabastecimento (Retorno para 5000g)
            elif peso >= 4900:
                if estado_atual == ESTADO_ALERTA:
                    print("Abastecimento concluído. Caixa cheia.")
                estado_atual = ESTADO_REGULAR
                ultimo_peso_reportado = -1 # Força a re-impressão ao sair dos 5000g
                
            # 4. Consumo Parcial / Estoque Regular (Entre 151g e 4899g)
            elif peso > 150 and peso < 4900:
                if peso != ultimo_peso_reportado:
                    print(f"Status: Estoque Regular ({peso}g)")
                    ultimo_peso_reportado = peso
                    estado_atual = ESTADO_REGULAR