import machine
import time

# --- Configuração dos Pinos do HX711 ---
DT_PIN = 22
SCK_PIN = 23

pin_dt = machine.Pin(DT_PIN, machine.Pin.IN)
pin_sck = machine.Pin(SCK_PIN, machine.Pin.OUT)
pin_sck.value(0)

def read_hx711():
    # Leitura 100% não-bloqueante
    if pin_dt.value() == 1:
        return None
    
    count = 0
    for _ in range(24):
        pin_sck.value(1)
        count = count << 1
        if pin_dt.value() == 1:
            count += 1
        pin_sck.value(0) 
    
    # 25º pulso para finalizar a leitura
    pin_sck.value(1)
    pin_sck.value(0)
    
    # Tratamento de sinal (Complemento de Dois)
    if count & 0x800000:
        count -= 0x1000000
        
    peso_bruto = count / 420.0
    
    # Filtro de Passo (Step de 10g): Remove o ruído (ex: 2498 vira 2500)
    peso_estabilizado = int(round(peso_bruto / 10.0) * 10)
    return peso_estabilizado

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
            # 1. Validação de Anomalia
            if peso <= 0:
                if estado_atual != ESTADO_ERRO:
                    print("ALERTA: Caixa ausente ou erro de calibração no sensor HX711!")
                    estado_atual = ESTADO_ERRO
            
            # 2. Caixa Vazia
            elif peso > 0 and peso <= 150:
                if estado_atual != ESTADO_ALERTA:
                    print("Evento de reposição disparado! Caixa vazia detectada.")
                    estado_atual = ESTADO_ALERTA
                    
            # 3. Caixa Cheia
            elif peso >= 4900:
                if estado_atual == ESTADO_ALERTA:
                    print("Abastecimento concluído. Caixa cheia.")
                estado_atual = ESTADO_REGULAR
                ultimo_peso_reportado = -1 
                
            # 4. Consumo Parcial
            elif peso > 150 and peso < 4900:
                if peso != ultimo_peso_reportado:
                    print(f"Status: Estoque Regular ({peso}g)")
                    ultimo_peso_reportado = peso
                    estado_atual = ESTADO_REGULAR