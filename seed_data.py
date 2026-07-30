"""
Seed script to populate the database with Pro Motos Soluccion course content
Real YouTube videos about motorcycle mechanics in Spanish
Run with: python seed_data.py
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# YouTube base URL helper
YT = "https://www.youtube.com/watch?v="

# Real YouTube videos related to motorcycle mechanics (in Spanish)
VIDEOS = {
    # Electricidad
    "bateria_diagnostico": YT + "m67FZEMxAAA",         # Cómo diagnosticar la batería de tu moto (verificado)
    "sistema_electrico": YT + "2z4JY1Ibhw4",           # Sistema Eléctrico de Motos - Componentes y Conexiones (verificado)
    "sistema_carga": YT + "if2e5ov7Nig",               # ESTATOR y REGULADOR de MOTO - sistema de carga, estator y regulador (verificado)
    "cambiar_bateria": YT + "7QDX16qKsUw",             # Cambiar batería AGM y ácido
    "activar_bateria": YT + "SMbKBkGQOBM",             # Activar batería moto
    "encendido_cdi": YT + "sR8CRzc-52w",               # Cómo funciona el sistema de encendido: alternador, CDI, bobina, bujía (verificado)
    "volante_magnetico": YT + "w-0P1fDrU-w",           # Extraer un volante magnético de motocicleta (verificado)
    "motor_arranque": YT + "ncmRqpzQlAM",              # Cómo desarmar y armar un motor de arranque de moto (verificado)

    # Electricidad - ítems faltantes (7-14)
    "elec_carga_trifasico_tci": YT + "pnK3ItIsaWg",     # Qué es un TCI de moto y cómo conectarlo (verificado)
    "elec_carga_trifasico": YT + "9y3uwx3DZCs",         # Cómo funciona y fallas del sistema de carga trifásica (verificado)
    "elec_motor_monocilindrico": YT + "dit4QqgTa0M",    # Cómo funciona un motor 4 tiempos monocilíndrico (verificado)
    "elec_uso_tester": YT + "jvZhAo0iYIc",              # Cómo usar el multímetro correctamente en la motocicleta (verificado)
    "elec_indicador_combustible": YT + "YCWRB9VrIJg",   # Función del sensor de gasolina de una moto (verificado)
    "elec_lampara_estroboscopica": YT + "bhfE-Vo7xtw",  # Uso de lámpara estroboscópica y medición de avance (verificado)
    "elec_mitos_bujias": YT + "m7faToTJ_qc",            # Todo sobre bujías de moto - mitos y consultas (verificado)
    "elec_clase_bujias": YT + "fwGs-pLSFwo",            # Todo lo que tienes que saber sobre bujías (verificado)
    
    # Frenos
    "frenos_tambor": YT + "V9mrT8MYNsM",                # Sistema de freno tipo tambor - curso ATEC (verificado)
    "frenos_disco_partes": YT + "wjUhQXB6AGc",          # Partes y elementos del sistema de freno disco (verificado)
    "frenos_circuito_hidraulico": YT + "gVMr-LJEv2s",   # Cómo funcionan realmente los frenos hidráulicos (verificado)
    "frenos_tipos_mordaza": YT + "WKGbHLKplHA",         # Componentes de un caliper (verificado)
    "frenos_verificar_disco": YT + "s3qrMR3Xdmw",       # Discos de freno: qué son y cuándo cambiarlos (verificado)

    # Frenos - ítems faltantes (6-10) + Seminario
    "frenos_cambio_pastillas": YT + "0w0WHKzmI7Q",      # Cómo cambiar pastillas de freno a tu moto (verificado)
    "frenos_purga_liquido": YT + "MJ9etLfqhgk",         # Cambiar líquido de frenos, purgar y quitar aire del circuito (verificado)
    "frenos_cbs_mecanico": YT + "1nmVUxfDJzs",          # Sistema de freno combinado (CBS) para motos (verificado)
    "frenos_abs": YT + "DB969ejqB6w",                   # Frenos ABS vs CBS en motos: funcionamiento, ventajas y desventajas (verificado)
    "frenos_cbs_abs_electronico": YT + "v2MnZcXW3Jk",   # ¿Qué son los frenos ABS y CBS? (verificado)
    "frenos_sem_dinamometro": YT + "UhPig2fK1dQ",       # Banco de pruebas / dinamómetro para motos (verificado)
    "frenos_sem_zapatas_fluido": YT + "V9mrT8MYNsM",    # Sistema de freno tipo tambor: zapatas y componentes (verificado, reutilizado)
    "frenos_sem_pastilla_asbesto": YT + "fggaiSQek0k",  # Pastillas de freno orgánicas y sinterizadas: composición (verificado)
    "frenos_sem_frenada": YT + "7IkAuk_2o84",           # Técnica de frenada de emergencia en moto (verificado)

    # Distribución
    "distribucion_componentes": YT + "zVblX-MO5hc",     # TODO sobre el árbol de levas de la moto: fallas y función (verificado, específico de motos)
    "distribucion_descompresor": YT + "sIy--R0CEiI",    # Cómo funciona el descompresor automático (verificado)
    "distribucion_asiento_valvulas": YT + "Tuwj_Jo4K4Y",# Rectificación de asientos de válvulas de motocicletas (verificado)
    "distribucion_regulacion_valvulas": YT + "S2N-ZWXxT-U", # Cómo calibrar las válvulas de tu moto (verificado)

    # Chasis, Suspensión y Rodados
    "chasis_suspension_delantera": YT + "SmPA9JqeBo4",  # Funcionamiento de la horquilla telescópica (verificado)
    "chasis_direccion": YT + "_LG-0duuH9c",             # Cómo revisar los rodamientos del tren de dirección (verificado)
    "chasis_basculante": YT + "7OPpd1YtETA",            # Cambio de rodamientos del basculante (verificado)
    "chasis_pinchaduras": YT + "5LrE-sxKiZ4",           # Reparar pinchazo moto: 2 maneras diferentes (verificado)

    # Chasis - resumen condensado (títulos y estructura propios)
    "chasis_tipos": YT + "5lMK5LI6IHw",                 # Diferentes tipos de chasis de moto (verificado)
    "chasis_control_traccion": YT + "93d5LkixObE",      # Cómo funciona el control de tracción (verificado)
    "susp_amortiguadores_resortes": YT + "oJNYxvrBjY0", # Suspensiones de moto: hidráulico y precarga (verificado)
    "susp_service_reparacion": YT + "qqun6KjXvPY",      # Cómo realizar un service a un sistema de suspensión (verificado)
    "susp_horquilla_invertida": YT + "sAvU4mcvKVw",     # Cómo adaptar una horquilla invertida a cualquier moto (verificado)

    # Motores 2T y 4T
    "motores_2t_vs_4t": YT + "tzGitXVmRiw",             # Motor 2 tiempos vs 4 tiempos: diferencias (verificado)
    "motores_4t_partes": YT + "43ocgJqupzQ",            # Motor de 4 tiempos: funcionamiento y partes (verificado)
    "motores_2t_funcionamiento": YT + "4FPUS5CwhUo",    # Cómo funcionan los motores 2T y 4T (verificado)
    "motores_2t_lubricacion": YT + "yI81h1V62f8",       # Mezcla de aceite y gasolina en motores 2 tiempos (verificado)

    # Motores - ítems faltantes
    "motores_2t_video1": YT + "28wUFKwt3u4",            # Cómo funciona un motor de 2 tiempos moto (verificado)
    "motores_2t_video2": YT + "eKY31VPWi-E",            # ¿Cómo funciona un motor de 2 tiempos? (verificado)
    "motores_pair_escape": YT + "yTu5qBhnQAw",          # Válvula PAIR en motocicletas: para qué sirve (verificado)
    "motores_exup": YT + "Aef084v19cw",                 # Avería de la válvula de escape EXUP: diagnóstico y reparación (verificado)
    "motores_v_bicilindrico": YT + "ZUDHD5kbEl0",       # El motor bicilíndrico en moto: equilibrio y polivalencia (verificado)
    "motores_camara_combustion": YT + "bJGUaHXAm5k",    # La cámara de combustión en motos (verificado)
    "motores_silenciadores": YT + "-_9zsPrwZHw",        # Silenciadores: ¿cómo funcionan? (verificado)

    # Embrague, Cilindro y Pistón
    "embrague_sacar_cilindro": YT + "YqBVtxDsw4k",      # Cómo sacar el cilindro de una moto (verificado)
    "embrague_lubricacion": YT + "mc1YaBzyWIw",         # Cómo funciona la lubricación de la moto (verificado)
    "embrague_funcionamiento": YT + "evgmLWnZ_lA",      # Cómo funciona el embrague de una moto (verificado)
    "embrague_desarme": YT + "hTddxZL3yVs",             # Embrague de moto: por qué desarmarlo y cambiarlo (verificado)

    # Embrague/Pistón - ítems adicionales (títulos y orden reformulados)
    "emb_piston_armado": YT + "ttcaC0tA3mg",            # Cómo armar un cilindro de moto: posición de aros y pistón (verificado)
    "emb_piston_medicion": YT + "IokcTY8_Zic",          # Medición de aros y pistón con galgas (verificado)
    "emb_piston_tipos": YT + "mEcPmbK3uT4",             # Pistones forjados de motos (verificado, específico de motos)
    "emb_compresion": YT + "OX4uw56IzAU",               # Cómo medir la compresión de tu moto con compresómetro (verificado)
    "emb_animacion": YT + "g8gpn4spgo0",                # Principio de funcionamiento y animación del embrague (verificado)
    "emb_antirrebote": YT + "XBxSIgge2bY",              # Slipper clutch: sistema antirrebote (verificado)
    "emb_centrifugo": YT + "BsNzsyh-nPQ",               # Funcionamiento del embrague centrífugo de moto (verificado)
    "emb_centrifugo_animacion": YT + "lufS9gKQobQ",     # Cómo funciona un embrague centrífugo (verificado)
    "emb_galerias_lubricacion": YT + "DfpwwNEKlfI",     # Proceso de lubricación del motor bien explicado (verificado)
    "emb_bomba_aceite": YT + "ns00Qba0Zlo",             # Bomba de aceite de la moto: funcionamiento (verificado)
    "emb_bomba_aceite_verificacion": YT + "q3EyJNQylvY",# Funcionamiento de bomba de aceite moto: verificación (verificado)
    "emb_balanceador_cigüeñal": YT + "eaosICj6ca0",     # Cómo funciona el cigüeñal en las motos (verificado)
    "emb_carter_desarme": YT + "_QYECtSi5No",           # Desensamble del cárter del motor de una moto (verificado)
    "emb_aditivos_aceite": YT + "dSA7C0kav4I",          # Aditivos para combustible y aceite de motor, explicados (verificado)

    # Caja de Velocidades
    "caja_funcionamiento": YT + "0x54jrjtSrU",          # Sistema de transmisión de 5 velocidades en moto (verificado)
    "caja_componentes": YT + "aGGzDNKoUws",             # Cómo funciona una caja de cambios de moto (animación) (verificado)
    "caja_tambor_horquillas": YT + "f_bdNeBg8T8",       # Marcha primaria, secundaria y tambor selector de cambios (verificado)

    # Carburador y Línea de Combustible
    "carburador_ubicacion": YT + "CPXU6APIYoQ",         # Funcionamiento y partes del carburador de una moto (verificado)
    "carburador_extraccion": YT + "oYi3WgMWzoQ",        # Cómo desmontar, lavar y montar el carburador (verificado)
    "carburador_tipos": YT + "wmcmK3Sn8yU",             # ¿Conoces los tipos de carburador? (verificado)

    # Refrigeración
    "refrigeracion_general": YT + "H3zylj20-1A",        # Tipos de refrigeración del motor de una moto (verificado)
    "refrigeracion_termostato": YT + "ca0br0S0YbQ",     # Cómo funciona el termostato de una moto (verificado)

    # Transmisión
    "transmision_cadena": YT + "RhgQAT-flx8",           # Cómo tensar la cadena de una moto de enduro (verificado)
    "transmision_cvt": YT + "9Hahmy3z6aI",              # ¿Variador automático de scooter? ¿Cómo funciona? (verificado)

    # Teoría de la electricidad
    "teoria_conceptos_basicos": YT + "_GbHx9cBMgU",     # Electricidad básica: voltaje, corriente y resistencia (verificado)
    "teoria_ley_ohm": YT + "wHQrMuJAjak",                # Ley de OHM explicación fácil (verificado)
    "teoria_circuito_simple": YT + "YNBq0dSjlsM",       # Los 5 componentes básicos de un circuito eléctrico (verificado)
    "teoria_seccion_conductores": YT + "LEqK6eeDEnA",   # Calcular la sección de un cable de una instalación eléctrica de moto (verificado)
    "teoria_bateria_fuente": YT + "RqF1ikcFwDE",        # Cómo funcionan las baterías (verificado)
    "teoria_volante_generador": YT + "u_MlJv-qA5k",     # Cómo saber si sirve el volante magnético (magneto) (verificado)
    "teoria_mono_trifasico": YT + "lVSz1BZBM8I",        # Bobinas y estatores: monofásico, trifásico, media onda, onda completa (verificado)
    "teoria_diodos": YT + "pgOBLbtUBKU",                # Qué es un diodo rectificador y cómo funciona (verificado)
    "teoria_puente_diodos": YT + "ZzXc1QRyxAM",         # El puente de diodos o rectificador de onda completa (verificado)
    "teoria_diagrama_trifasico": YT + "COH-6LEKXw8",    # Diagrama eléctrico de una motocicleta (explicación) (verificado)
    "teoria_interpretar_diagrama": YT + "Tdp9uo6uzxY",  # Cómo leer los diagramas del sistema eléctrico de moto (verificado)
    "teoria_encendido_platinos": YT + "GLRwZ0qH-oU",    # El encendido por platinos ¿cómo funciona? (verificado)
    "teoria_cdi_alterna": YT + "zEqPRr9kO18",           # CDI de corriente alterna: funcionamiento y diagrama (verificado)

    # Inyección Electrónica
    "iny_componentes": YT + "OEViS9chOoo",              # Sistemas de inyección electrónica en motocicletas (verificado)
    "iny_esquema_animado": YT + "kXy_7zMVrQ8",          # Cómo funciona la inyección electrónica (verificado)
    "iny_motores_refrigerados": YT + "cqIRxuwEvJI",     # Inyección electrónica en motos - explicación básica (verificado)
    "iny_escaner": YT + "NxFF7aLEd4g",                  # Escáner para motocicletas Motodiag (verificado)
    "iny_cuerpo_mariposa": YT + "_-hD4yhdEtE",          # Cómo funciona el sensor TPS - mariposa de aceleración (verificado)
    "iny_linea_combustible": YT + "goI1s17-eEQ",        # Medición de presión en bomba de inyección moto (verificado)
    "iny_descripcion_componentes": YT + "ISU3MvBcuc0",  # Motos con inyección electrónica: detalles y cuidados (verificado)
    "iny_armado_escaneo": YT + "WHX-T3jfXTE",           # Diagnóstico inyección electrónica KTM Duke 390 con escáner (verificado)
    "iny_error_temperatura": YT + "LC3Cg3YaQMg",        # Qué pasa si falla el sensor de temperatura del motor (verificado)
    "iny_control_tps": YT + "oXvpsTskh_c",              # Tutorial para calibrar sensor TPS (verificado)
    "iny_error_tps": YT + "qUQZjrILPWk",                # Sensor TPS: qué es, ubicación, funcionamiento y fallas (verificado)
    "iny_error_lambda": YT + "QnpRQV_4MI0",             # Cómo comprobar y/o cambiar sensor de oxígeno / sonda lambda (verificado)
    "iny_ventajas": YT + "_oX9paTalZg",                 # Carburador VS Inyección ¿Cuál es mejor en motos? (verificado)
    "iny_sensores": YT + "OEViS9chOoo",                 # Sistemas de inyección electrónica en motocicletas (verificado)
    "iny_bomba_combustible": YT + "Vk5NshzAcjE",        # Todo sobre bombas de inyección de combustible en motos (verificado)
    "iny_duracion_inyeccion": YT + "1qDKUFAqtiE",       # Todo sobre inyectores de combustible (verificado)
    "iny_ecu": YT + "CJiXG84aopw",                      # Unidad de control del motor: qué es y para qué sirve (verificado)
    "iny_diagnostico_ecu": YT + "NxFF7aLEd4g",          # Escáner para motocicletas Motodiag (verificado)
    "iny_modo_diagnostico_lectura": YT + "WHX-T3jfXTE", # Diagnóstico inyección electrónica KTM Duke 390 con escáner (verificado)
    "iny_modo_diagnostico": YT + "hfFhuA2EtBI",         # Cómo diagnosticar cualquier moto con cualquier escáner (verificado)
    "iny_solucion_problemas": YT + "2jE8FYECB_k",       # Cómo se diagnostica una motocicleta a inyección electrónica (verificado)

    # Diagnóstico de motocicletas
    "diag_arranque_dificultoso": YT + "_aXy5OTYOq4",    # Moto no arranca: 4 causas y soluciones (verificado)
    "diag_perdida_potencia": YT + "qSdV1yHtuMk",        # Por qué mi moto pierde fuerza y potencia (verificado)
    "diag_mediciones_calibre": YT + "CEJuZ2_kXmI",      # Aprende a usar el calibrador Vernier / pie de rey (verificado)
    "diag_rectificacion_cigenal": YT + "gm53JGY4EhY",   # Rectificado del cigüeñal de un motor (verificado)
    "diag_estado_bujia": YT + "zDb1sLSA4eM",            # Por qué la bujía de mi moto sale negra, marrón o blanca (verificado)
    "diag_seminario_no_arranca": YT + "lr8-ZSQgKR0",    # ¿Por qué no arranca mi moto? (verificado)

    # Herramientas del Taller
    "herr_basicas": YT + "Mm4vh4j5Pd4",                 # Herramientas imprescindibles en nuestro taller (verificado)
    "herr_compresor_aire": YT + "OIsYa3-dmJE",          # Aprende a elegir un compresor para tu taller (verificado)
    "herr_torquimetro": YT + "z3Q7bSbsI8A",             # Llave dinamométrica o torquímetro: guía completa (verificado)
    "herr_torquimetro_click": YT + "hS8zhocO9eE",       # Cómo se usa el torquímetro digital en moto (verificado)

    # Caja de Velocidades - resumen condensado
    "caja_desarme": YT + "WBm6mKFj6oQ",                 # Desmontar caja de cambios moto (verificado, específico de motos)
    "caja_rodamientos_bujes": YT + "cYaM91pVJYI",       # Rodamientos y canastilla de la caja de cambios (verificado)
    "caja_armado_ejes": YT + "E1HI8qCEB2w",             # Cómo armar la caja de velocidades: ejes primario y secundario (verificado)
    "caja_palanca_cambios": YT + "Q8lFPbBjnC4",         # Cómo arreglar el selector de cambios de una moto (verificado)

    # Carburador - resumen condensado
    "carb_partes_circuitos": YT + "32wKhQeU2SQ",        # Circuitos del carburador y sus partes (verificado)
    "carb_filtro_grifo": YT + "Krvwfza-YS4",            # Así se cambia el filtro de aire de tu moto (verificado)
    "carb_diafragma_cebador": YT + "eRuVF1HBEdM",       # Así funciona un carburador con diafragma (verificado)
    "carb_tipos_vm_su": YT + "68Wq_7tsHG4",             # Carburador diafragma vs carburador campana: funcionamiento (verificado)
    "carb_nivel_cuba": YT + "CQWkpUcmQuc",              # Así funciona la cuba de nivel constante del carburador (verificado)

    # Refrigeración - resumen condensado
    "refrig_radiador_aceite": YT + "wg1CmMtixAk",       # Cómo funciona el enfriamiento por aceite en las motos (verificado)

    # Transmisión - resumen condensado
    "trans_variador_desarme": YT + "pYDI3ZF8nrQ",       # Transmisión scooter: variador, correa y embrague - desmontar y montar (verificado)
    "trans_variador_caso": YT + "Um97xzXq7d8",          # Desarme motor TVS NTORQ 125: variador automático (verificado)
    "trans_cadena_oring": YT + "paD7iz0a1Zk",           # ¿Qué es una cadena con O-Rings? (verificado)
}

# Course content
course_data = {
    "modules": [
        {
            "module_id": "mod_electricidad",
            "title": "Electricidad",
            "description": "Aprende sobre el sistema eléctrico de motocicletas",
            "order": 1,
            "exam_id": "exam_electricidad"
        },
        {
            "module_id": "mod_frenos",
            "title": "Frenos",
            "description": "Sistemas de frenos: tambor, disco, hidráulicos, ABS",
            "order": 2,
            "exam_id": "exam_frenos"
        },
        {
            "module_id": "mod_seminario_frenos",
            "title": "Seminario: Frenos",
            "description": "Dinamómetro, materiales de fricción y técnica de frenada",
            "order": 2.5,
            "exam_id": "exam_seminario_frenos"
        },
        {
            "module_id": "mod_distribucion",
            "title": "Distribución",
            "description": "Componentes y funcionamiento de la distribución",
            "order": 3,
            "exam_id": "exam_distribucion"
        },
        {
            "module_id": "mod_chasis",
            "title": "Chasis, Suspensión y Rodados",
            "description": "Suspensión, amortiguación, neumáticos y más",
            "order": 4,
            "exam_id": "exam_chasis"
        },
        {
            "module_id": "mod_suspension_avanzada",
            "title": "Suspensión Avanzada: Amortiguadores y Horquillas",
            "description": "Funcionamiento, service y reparación de amortiguadores y horquillas",
            "order": 4.5,
            "exam_id": "exam_suspension_avanzada"
        },
        {
            "module_id": "mod_motores",
            "title": "Tipos de Motores",
            "description": "Motores 2T, 4T, bicilíndricos y más",
            "order": 5,
            "exam_id": "exam_motores"
        },
        {
            "module_id": "mod_embrague",
            "title": "Embrague, Cilindro y Pistón",
            "description": "Componentes internos del motor",
            "order": 6,
            "exam_id": "exam_embrague"
        },
        {
            "module_id": "mod_lubricacion_avanzada",
            "title": "Lubricación Avanzada en Motores",
            "description": "Aditivos, depósitos de carbón y diagramas de lubricación",
            "order": 6.5,
            "exam_id": "exam_lubricacion_avanzada"
        },
        {
            "module_id": "mod_caja",
            "title": "Caja de Velocidades",
            "description": "Funcionamiento y mantenimiento de la transmisión",
            "order": 7,
            "exam_id": "exam_caja"
        },
        {
            "module_id": "mod_carburador",
            "title": "Carburador y Línea de Combustible",
            "description": "Sistemas de alimentación de combustible",
            "order": 8,
            "exam_id": "exam_carburador"
        },
        {
            "module_id": "mod_refrigeracion",
            "title": "Refrigeración",
            "description": "Sistemas de enfriamiento del motor",
            "order": 9,
            "exam_id": "exam_refrigeracion"
        },
        {
            "module_id": "mod_transmision",
            "title": "Transmisión",
            "description": "Cadena, corona, piñón y variador CVT",
            "order": 10,
            "exam_id": "exam_transmision"
        },
        {
            "module_id": "mod_teoria_electricidad",
            "title": "Teoría de la Electricidad",
            "description": "Fundamentos de electricidad aplicados a la motocicleta: ley de Ohm, circuitos, diodos y encendido",
            "order": 11,
            "exam_id": "exam_teoria_electricidad"
        },
        {
            "module_id": "mod_inyeccion",
            "title": "Inyección Electrónica",
            "description": "Componentes, sensores, ECU y diagnóstico de sistemas de inyección electrónica",
            "order": 12,
            "exam_id": "exam_inyeccion"
        },
        {
            "module_id": "mod_diagnostico",
            "title": "Diagnóstico de Motocicletas",
            "description": "Diagnóstico de fallas comunes: arranque, pérdida de potencia y más",
            "order": 13,
            "exam_id": "exam_diagnostico"
        },
        {
            "module_id": "mod_herramientas",
            "title": "Herramientas del Taller",
            "description": "Herramientas manuales, neumáticas y de medición para el taller de motos",
            "order": 14,
            "exam_id": "exam_herramientas"
        }
    ],
    "lessons": {
        "mod_electricidad": [
            {"title": "Batería y comprobaciones", "duration": "14:49", "video_url": VIDEOS["bateria_diagnostico"], "is_free": True},
            {"title": "Componentes del sistema eléctrico", "duration": "03:48", "video_url": VIDEOS["sistema_electrico"], "is_free": True},
            {"title": "Sistema de carga", "duration": "07:27", "video_url": VIDEOS["sistema_carga"], "is_free": True},
            {"title": "Extracción del volante magnético", "duration": "10:48", "video_url": VIDEOS["volante_magnetico"], "is_free": False},
            {"title": "Desarme del motor de arranque", "duration": "08:08", "video_url": VIDEOS["motor_arranque"], "is_free": False},
            {"title": "Componentes y tipos de encendido", "duration": "11:38", "video_url": VIDEOS["encendido_cdi"], "is_free": False},
            {"title": "Sistema de carga trifásico y encendido TCI", "duration": "05:30", "video_url": VIDEOS["elec_carga_trifasico_tci"], "is_free": False},
            {"title": "Sistema de carga trifásico", "duration": "06:32", "video_url": VIDEOS["elec_carga_trifasico"], "is_free": False},
            {"title": "Funcionamiento de motor monocilíndrico", "duration": "04:40", "video_url": VIDEOS["elec_motor_monocilindrico"], "is_free": False},
            {"title": "Uso del tester o multímetro", "duration": "08:51", "video_url": VIDEOS["elec_uso_tester"], "is_free": False},
            {"title": "Caso de estudio: Indicador de nivel de combustible", "duration": "03:46", "video_url": VIDEOS["elec_indicador_combustible"], "is_free": False},
            {"title": "Uso de lámpara estroboscópica", "duration": "06:24", "video_url": VIDEOS["elec_lampara_estroboscopica"], "is_free": False},
            {"title": "Mitos sobre las bujías", "duration": "02:54", "video_url": VIDEOS["elec_mitos_bujias"], "is_free": False},
            {"title": "Clase extra: Las bujías", "duration": "03:45", "video_url": VIDEOS["elec_clase_bujias"], "is_free": False},
        ],
        "mod_frenos": [
            {"title": "Frenos a tambor", "duration": "08:51", "video_url": VIDEOS["frenos_tambor"], "is_free": True},
            {"title": "Frenos a disco", "duration": "09:50", "video_url": VIDEOS["frenos_disco_partes"], "is_free": True},
            {"title": "Circuito de freno a disco", "duration": "11:08", "video_url": VIDEOS["frenos_circuito_hidraulico"], "is_free": False},
            {"title": "Tipos de mordaza", "duration": "10:19", "video_url": VIDEOS["frenos_tipos_mordaza"], "is_free": False},
            {"title": "Verificaciones en el disco de freno", "duration": "04:43", "video_url": VIDEOS["frenos_verificar_disco"], "is_free": False},
            {"title": "Frenos hidráulicos: cambio de pastillas de freno", "duration": "03:50", "video_url": VIDEOS["frenos_cambio_pastillas"], "is_free": False},
            {"title": "Frenos hidráulicos: purga de líquido", "duration": "04:58", "video_url": VIDEOS["frenos_purga_liquido"], "is_free": False},
            {"title": "Sistema CBS Mecánico", "duration": "04:51", "video_url": VIDEOS["frenos_cbs_mecanico"], "is_free": False},
            {"title": "Sistema ABS", "duration": "02:22", "video_url": VIDEOS["frenos_abs"], "is_free": False},
            {"title": "Sistema CBS electrónico con ABS", "duration": "07:02", "video_url": VIDEOS["frenos_cbs_abs_electronico"], "is_free": False},
        ],
        "mod_seminario_frenos": [
            {"title": "Introducción", "duration": "04:07", "video_url": VIDEOS["frenos_disco_partes"], "is_free": True},
            {"title": "El dinamómetro", "duration": "03:32", "video_url": VIDEOS["frenos_sem_dinamometro"], "is_free": False},
            {"title": "Recomendaciones para el service de frenos", "duration": "02:15", "video_url": VIDEOS["frenos_verificar_disco"], "is_free": False},
            {"title": "Componentes de las zapatas y características del fluído", "duration": "06:20", "video_url": VIDEOS["frenos_sem_zapatas_fluido"], "is_free": False},
            {"title": "Rango de temperatura de funcionamiento", "duration": "02:40", "video_url": VIDEOS["frenos_sem_pastilla_asbesto"], "is_free": False},
            {"title": "Componentes de la pastilla y el asbesto", "duration": "08:52", "video_url": VIDEOS["frenos_sem_pastilla_asbesto"], "is_free": False},
            {"title": "La frenada en la motocicleta", "duration": "03:57", "video_url": VIDEOS["frenos_sem_frenada"], "is_free": False},
        ],
        "mod_distribucion": [
            {"title": "La distribución y sus componentes", "duration": "16:09", "video_url": VIDEOS["distribucion_componentes"], "is_free": True},
            {"title": "Descompresor automático y balancines", "duration": "07:52", "video_url": VIDEOS["distribucion_descompresor"], "is_free": False},
            {"title": "Asiento de válvulas", "duration": "08:13", "video_url": VIDEOS["distribucion_asiento_valvulas"], "is_free": False},
            {"title": "Regulación de válvulas", "duration": "05:35", "video_url": VIDEOS["distribucion_regulacion_valvulas"], "is_free": False},
        ],
        "mod_chasis": [
            {"title": "Suspensión delantera", "duration": "05:18", "video_url": VIDEOS["chasis_suspension_delantera"], "is_free": True},
            {"title": "Movimientos de dirección", "duration": "08:02", "video_url": VIDEOS["chasis_direccion"], "is_free": False},
            {"title": "El basculante y sus partes", "duration": "03:00", "video_url": VIDEOS["chasis_basculante"], "is_free": False},
            {"title": "Tipos de chasis: cuna, doble viga y perimetral", "duration": "06:00", "video_url": VIDEOS["chasis_tipos"], "is_free": False},
            {"title": "Control de tracción en motos", "duration": "04:30", "video_url": VIDEOS["chasis_control_traccion"], "is_free": False},
            {"title": "Pinchaduras y cambio de cámara de rueda", "duration": "11:41", "video_url": VIDEOS["chasis_pinchaduras"], "is_free": False},
        ],
        "mod_suspension_avanzada": [
            {"title": "Amortiguadores: hidráulico, resortes y precarga", "duration": "09:00", "video_url": VIDEOS["susp_amortiguadores_resortes"], "is_free": True},
            {"title": "Service y reparación de amortiguadores y horquillas", "duration": "08:00", "video_url": VIDEOS["susp_service_reparacion"], "is_free": False},
            {"title": "La horquilla invertida", "duration": "06:53", "video_url": VIDEOS["susp_horquilla_invertida"], "is_free": False},
        ],
        "mod_motores": [
            {"title": "Motores de 2 y 4 tiempos", "duration": "09:08", "video_url": VIDEOS["motores_2t_vs_4t"], "is_free": True},
            {"title": "Características de motores 4T", "duration": "06:58", "video_url": VIDEOS["motores_4t_partes"], "is_free": True},
            {"title": "El motor 2T y sus diferencias", "duration": "09:07", "video_url": VIDEOS["motores_2t_funcionamiento"], "is_free": False},
            {"title": "La lubricación en el 2T", "duration": "07:41", "video_url": VIDEOS["motores_2t_lubricacion"], "is_free": False},
            {"title": "El motor de dos tiempos", "duration": "05:58", "video_url": VIDEOS["motores_2t_video1"], "is_free": False},
            {"title": "Motor de cuatro tiempos", "duration": "01:45", "video_url": VIDEOS["motores_4t_partes"], "is_free": False},
            {"title": "Motor de dos tiempos", "duration": "01:38", "video_url": VIDEOS["motores_2t_video2"], "is_free": False},
            {"title": "Motores con inyectora de aire fresco al escape", "duration": "06:40", "video_url": VIDEOS["motores_pair_escape"], "is_free": False},
            {"title": "Caso de estudio: La válvula EXUP", "duration": "02:03", "video_url": VIDEOS["motores_exup"], "is_free": False},
            {"title": "Motor bicilíndrico en V", "duration": "01:59", "video_url": VIDEOS["motores_v_bicilindrico"], "is_free": False},
            {"title": "La cámara de combustión", "duration": "03:01", "video_url": VIDEOS["motores_camara_combustion"], "is_free": False},
            {"title": "Silenciadores en el escape", "duration": "04:19", "video_url": VIDEOS["motores_silenciadores"], "is_free": False},
        ],
        "mod_embrague": [
            {"title": "Extracción del cilindro", "duration": "03:23", "video_url": VIDEOS["embrague_sacar_cilindro"], "is_free": True},
            {"title": "Montaje de pistón, aros y cilindro (2T y 4T)", "duration": "04:19", "video_url": VIDEOS["emb_piston_armado"], "is_free": False},
            {"title": "Medición de aros y pistón con galgas", "duration": "07:52", "video_url": VIDEOS["emb_piston_medicion"], "is_free": False},
            {"title": "Pistones fundidos vs. forjados", "duration": "01:55", "video_url": VIDEOS["emb_piston_tipos"], "is_free": False},
            {"title": "Relación y medición de compresión del cilindro", "duration": "03:42", "video_url": VIDEOS["emb_compresion"], "is_free": False},
            {"title": "Cómo funciona el embrague", "duration": "07:40", "video_url": VIDEOS["embrague_funcionamiento"], "is_free": False},
            {"title": "Animación: funcionamiento del embrague", "duration": "05:39", "video_url": VIDEOS["emb_animacion"], "is_free": False},
            {"title": "Desarme del embrague", "duration": "09:07", "video_url": VIDEOS["embrague_desarme"], "is_free": False},
            {"title": "Embrague antirrebote (sistema antibloqueo)", "duration": "03:10", "video_url": VIDEOS["emb_antirrebote"], "is_free": False},
            {"title": "El embrague centrífugo", "duration": "05:37", "video_url": VIDEOS["emb_centrifugo"], "is_free": False},
            {"title": "Animación: embrague centrífugo", "duration": "04:20", "video_url": VIDEOS["emb_centrifugo_animacion"], "is_free": False},
            {"title": "Sistema de lubricación del motor", "duration": "06:10", "video_url": VIDEOS["embrague_lubricacion"], "is_free": False},
            {"title": "Galerías y circuitos de lubricación", "duration": "02:05", "video_url": VIDEOS["emb_galerias_lubricacion"], "is_free": False},
            {"title": "Bomba de aceite: funcionamiento", "duration": "02:58", "video_url": VIDEOS["emb_bomba_aceite"], "is_free": False},
            {"title": "Verificación de la bomba de aceite", "duration": "03:37", "video_url": VIDEOS["emb_bomba_aceite_verificacion"], "is_free": False},
            {"title": "El balanceador del cigüeñal", "duration": "01:19", "video_url": VIDEOS["emb_balanceador_cigüeñal"], "is_free": False},
            {"title": "Relación entre caja de cambios y cigüeñal", "duration": "04:43", "video_url": VIDEOS["caja_funcionamiento"], "is_free": False},
            {"title": "Desarme del cárter", "duration": "10:51", "video_url": VIDEOS["emb_carter_desarme"], "is_free": False},
        ],
        "mod_lubricacion_avanzada": [
            {"title": "Aditivos en el aceite de motor", "duration": "02:29", "video_url": VIDEOS["emb_aditivos_aceite"], "is_free": True},
            {"title": "Lubricación combinada en motores 2T", "duration": "02:56", "video_url": VIDEOS["motores_2t_lubricacion"], "is_free": False},
            {"title": "Depósitos de carbón en el pistón", "duration": "04:05", "video_url": VIDEOS["emb_galerias_lubricacion"], "is_free": False},
            {"title": "Lubricación del embrague", "duration": "02:57", "video_url": VIDEOS["embrague_lubricacion"], "is_free": False},
            {"title": "Lubricación de la caja de velocidades", "duration": "02:00", "video_url": VIDEOS["emb_bomba_aceite"], "is_free": False},
            {"title": "Cómo interpretar un diagrama de lubricación", "duration": "13:08", "video_url": VIDEOS["emb_galerias_lubricacion"], "is_free": False},
        ],
        "mod_caja": [
            {"title": "Funcionamiento de la caja de velocidades", "duration": "06:19", "video_url": VIDEOS["caja_funcionamiento"], "is_free": True},
            {"title": "Componentes y funcionamiento", "duration": "02:58", "video_url": VIDEOS["caja_componentes"], "is_free": False},
            {"title": "El árbol de levas y las horquillas", "duration": "06:48", "video_url": VIDEOS["caja_tambor_horquillas"], "is_free": False},
            {"title": "Desarme y desmontaje de la caja de cambios", "duration": "06:00", "video_url": VIDEOS["caja_desarme"], "is_free": False},
            {"title": "Rodamientos y bujes de la caja de velocidades", "duration": "05:00", "video_url": VIDEOS["caja_rodamientos_bujes"], "is_free": False},
            {"title": "Armado de ejes primario y secundario", "duration": "07:00", "video_url": VIDEOS["caja_armado_ejes"], "is_free": False},
            {"title": "Colocación de palanca de cambios y comprobación final", "duration": "05:00", "video_url": VIDEOS["caja_palanca_cambios"], "is_free": False},
        ],
        "mod_carburador": [
            {"title": "Ubicación y acceso al carburador", "duration": "04:19", "video_url": VIDEOS["carburador_ubicacion"], "is_free": True},
            {"title": "Extracción del carburador", "duration": "04:18", "video_url": VIDEOS["carburador_extraccion"], "is_free": False},
            {"title": "Tipos de carburadores", "duration": "12:17", "video_url": VIDEOS["carburador_tipos"], "is_free": False},
            {"title": "Partes y circuitos internos del carburador", "duration": "08:00", "video_url": VIDEOS["carb_partes_circuitos"], "is_free": False},
            {"title": "Filtro de aire y grifo de combustible", "duration": "06:00", "video_url": VIDEOS["carb_filtro_grifo"], "is_free": False},
            {"title": "Carburadores de diafragma (CV) y cebador automático", "duration": "08:00", "video_url": VIDEOS["carb_diafragma_cebador"], "is_free": False},
            {"title": "VM de tiro directo vs. SU a depresión", "duration": "07:00", "video_url": VIDEOS["carb_tipos_vm_su"], "is_free": False},
            {"title": "Nivel de cuba y flotador: puesta a punto", "duration": "05:00", "video_url": VIDEOS["carb_nivel_cuba"], "is_free": False},
        ],
        "mod_refrigeracion": [
            {"title": "Refrigeración general", "duration": "11:35", "video_url": VIDEOS["refrigeracion_general"], "is_free": True},
            {"title": "Extracción del termostato", "duration": "03:08", "video_url": VIDEOS["refrigeracion_termostato"], "is_free": False},
            {"title": "Radiador de aceite: enfriamiento por aceite", "duration": "04:00", "video_url": VIDEOS["refrig_radiador_aceite"], "is_free": False},
        ],
        "mod_transmision": [
            {"title": "Las cadenas y piñones", "duration": "09:09", "video_url": VIDEOS["transmision_cadena"], "is_free": True},
            {"title": "Funcionamiento del variador CVT", "duration": "03:33", "video_url": VIDEOS["transmision_cvt"], "is_free": False},
            {"title": "Desarme y despiece del variador CVT", "duration": "08:00", "video_url": VIDEOS["trans_variador_desarme"], "is_free": False},
            {"title": "Caso de estudio: desarme real de un variador CVT", "duration": "10:00", "video_url": VIDEOS["trans_variador_caso"], "is_free": False},
            {"title": "Cadenas con O-Rings: qué son y cómo funcionan", "duration": "05:00", "video_url": VIDEOS["trans_cadena_oring"], "is_free": False},
        ],
        "mod_teoria_electricidad": [
            {"title": "Conceptos básicos 01", "duration": "05:19", "video_url": VIDEOS["teoria_conceptos_basicos"], "is_free": True},
            {"title": "Conceptos básicos 02", "duration": "05:36", "video_url": VIDEOS["teoria_conceptos_basicos"], "is_free": True},
            {"title": "Ley de ohm", "duration": "04:16", "video_url": VIDEOS["teoria_ley_ohm"], "is_free": False},
            {"title": "Circuito eléctrico simple", "duration": "05:29", "video_url": VIDEOS["teoria_circuito_simple"], "is_free": False},
            {"title": "Sección de conductores", "duration": "02:49", "video_url": VIDEOS["teoria_seccion_conductores"], "is_free": False},
            {"title": "Batería como fuente de poder", "duration": "03:21", "video_url": VIDEOS["teoria_bateria_fuente"], "is_free": False},
            {"title": "Volante generador de CA", "duration": "03:40", "video_url": VIDEOS["teoria_volante_generador"], "is_free": False},
            {"title": "Sistemas monofásicos y trifásicos", "duration": "03:48", "video_url": VIDEOS["teoria_mono_trifasico"], "is_free": False},
            {"title": "Los diodos", "duration": "08:08", "video_url": VIDEOS["teoria_diodos"], "is_free": False},
            {"title": "Puente de diodos", "duration": "04:14", "video_url": VIDEOS["teoria_puente_diodos"], "is_free": False},
            {"title": "Diagrama Trifásico", "duration": "04:16", "video_url": VIDEOS["teoria_diagrama_trifasico"], "is_free": False},
            {"title": "Sistema de encendido", "duration": "05:38", "video_url": VIDEOS["encendido_cdi"], "is_free": False},
            {"title": "Interpretación de Diagrama eléctrico", "duration": "07:24", "video_url": VIDEOS["teoria_interpretar_diagrama"], "is_free": False},
            {"title": "El encendido con platinos", "duration": "03:21", "video_url": VIDEOS["teoria_encendido_platinos"], "is_free": False},
            {"title": "Funcionamiento del CDI de corriente alterna", "duration": "11:19", "video_url": VIDEOS["teoria_cdi_alterna"], "is_free": False},
        ],
        "mod_inyeccion": [
            {"title": "Componentes y funcionamiento de la Inyección Electrónica", "duration": "38:03", "video_url": VIDEOS["iny_componentes"], "is_free": True},
            {"title": "Esquema animado del sistema de inyección", "duration": "03:08", "video_url": VIDEOS["iny_esquema_animado"], "is_free": False},
            {"title": "Inyección en motores refrigerados por aire y por agua", "duration": "04:15", "video_url": VIDEOS["iny_motores_refrigerados"], "is_free": False},
            {"title": "El diagnosticador o escáner", "duration": "01:51", "video_url": VIDEOS["iny_escaner"], "is_free": False},
            {"title": "Identificación de componentes y extracción de cuerpo mariposa", "duration": "08:46", "video_url": VIDEOS["iny_cuerpo_mariposa"], "is_free": False},
            {"title": "La línea de combustible", "duration": "02:34", "video_url": VIDEOS["iny_linea_combustible"], "is_free": False},
            {"title": "Descripción de componentes del sistema", "duration": "09:29", "video_url": VIDEOS["iny_descripcion_componentes"], "is_free": False},
            {"title": "Armado del sistema de inyección y escaneo", "duration": "05:38", "video_url": VIDEOS["iny_armado_escaneo"], "is_free": False},
            {"title": "Error de sonda de temperatura", "duration": "02:41", "video_url": VIDEOS["iny_error_temperatura"], "is_free": True},
            {"title": "Cómo controlar los valores del TPS", "duration": "01:06", "video_url": VIDEOS["iny_control_tps"], "is_free": False},
            {"title": "Error en sensor de TPS", "duration": "02:16", "video_url": VIDEOS["iny_error_tps"], "is_free": False},
            {"title": "Error en sonda lambda", "duration": "02:14", "video_url": VIDEOS["iny_error_lambda"], "is_free": False},
            {"title": "Ventajas de la inyección electrónica en motos", "duration": "02:36", "video_url": VIDEOS["iny_ventajas"], "is_free": False},
            {"title": "Los sensores en un sistema de inyección electrónica", "duration": "02:55", "video_url": VIDEOS["iny_sensores"], "is_free": False},
            {"title": "La bomba de combustible", "duration": "01:58", "video_url": VIDEOS["iny_bomba_combustible"], "is_free": False},
            {"title": "Gestión de la duración de la inyección", "duration": "02:52", "video_url": VIDEOS["iny_duracion_inyeccion"], "is_free": False},
            {"title": "La ECU: Engine Control Unit", "duration": "03:04", "video_url": VIDEOS["iny_ecu"], "is_free": False},
            {"title": "Sistema de diagnostico de la ECU", "duration": "04:43", "video_url": VIDEOS["iny_diagnostico_ecu"], "is_free": False},
            {"title": "Modo diagnóstico y lectura de sensores", "duration": "02:01", "video_url": VIDEOS["iny_modo_diagnostico_lectura"], "is_free": False},
            {"title": "El modo diagnóstico", "duration": "02:36", "video_url": VIDEOS["iny_modo_diagnostico"], "is_free": False},
            {"title": "Pasos para solución de problemas", "duration": "06:14", "video_url": VIDEOS["iny_solucion_problemas"], "is_free": False},
        ],
        "mod_diagnostico": [
            {"title": "Arranque dificultoso o marcha breve", "duration": "03:59", "video_url": VIDEOS["diag_arranque_dificultoso"], "is_free": True},
            {"title": "Pérdida de potencia del motor", "duration": "05:47", "video_url": VIDEOS["diag_perdida_potencia"], "is_free": False},
            {"title": "Mediciones con calibre", "duration": "03:16", "video_url": VIDEOS["diag_mediciones_calibre"], "is_free": False},
            {"title": "Rectificación de cigueñal", "duration": "02:54", "video_url": VIDEOS["diag_rectificacion_cigenal"], "is_free": False},
            {"title": "Diagnóstico según el estado de la bujía", "duration": "07:04", "video_url": VIDEOS["diag_estado_bujia"], "is_free": False},
            {"title": "Seminario Grabado: ¿Por qué mi moto no arranca?", "duration": "27:01", "video_url": VIDEOS["diag_seminario_no_arranca"], "is_free": False},
        ],
        "mod_herramientas": [
            {"title": "Tornillos y destornilladores", "duration": "03:39", "video_url": VIDEOS["herr_basicas"], "is_free": True},
            {"title": "Pinzas, alicates y llaves tubo", "duration": "03:31", "video_url": VIDEOS["herr_basicas"], "is_free": False},
            {"title": "Encastres y llaves tipo crique", "duration": "04:43", "video_url": VIDEOS["herr_basicas"], "is_free": False},
            {"title": "Tipos de puntas y ranura", "duration": "03:00", "video_url": VIDEOS["herr_basicas"], "is_free": False},
            {"title": "Destornillador y puntas", "duration": "03:42", "video_url": VIDEOS["herr_basicas"], "is_free": False},
            {"title": "Adaptadores de movimiento y prolongadores", "duration": "06:32", "video_url": VIDEOS["herr_basicas"], "is_free": False},
            {"title": "Llaves allen, destornillador y tubos", "duration": "03:38", "video_url": VIDEOS["herr_basicas"], "is_free": False},
            {"title": "Sacabujías, tubos y prolongadores", "duration": "03:48", "video_url": VIDEOS["herr_basicas"], "is_free": False},
            {"title": "Llaves fijas", "duration": "01:43", "video_url": VIDEOS["herr_basicas"], "is_free": False},
            {"title": "Compresor de Aire: Características", "duration": "07:01", "video_url": VIDEOS["herr_compresor_aire"], "is_free": False},
            {"title": "Compresor de Aire: Filtros y herramientas", "duration": "05:36", "video_url": VIDEOS["herr_compresor_aire"], "is_free": False},
            {"title": "Compresor de Aire: Pistola Neumática y Trampa de Agua", "duration": "02:51", "video_url": VIDEOS["herr_compresor_aire"], "is_free": False},
            {"title": "La llave dinamométrica o torquímetro", "duration": "13:04", "video_url": VIDEOS["herr_torquimetro"], "is_free": False},
            {"title": "Uso y funcionamiento del torquímetro de click", "duration": "06:12", "video_url": VIDEOS["herr_torquimetro_click"], "is_free": False},
        ]
    },
    "exams": [
        {
            "exam_id": "exam_electricidad",
            "module_id": "mod_electricidad",
            "title": "Examen: Electricidad",
            "passing_score": 70,
            "questions": [
                {
                    "text": "¿Cuál es la función principal de la batería en una motocicleta?",
                    "type": "multiple_choice",
                    "options": ["Enfriar el motor", "Almacenar energía eléctrica", "Lubricar componentes", "Regular la velocidad"],
                    "correct_answer": "Almacenar energía eléctrica"
                },
                {
                    "text": "El regulador rectificador convierte corriente alterna en corriente continua.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                },
                {
                    "text": "¿Qué componente genera la electricidad en una moto?",
                    "type": "multiple_choice",
                    "options": ["Batería", "Bujía", "Generador/Alternador", "CDI"],
                    "correct_answer": "Generador/Alternador"
                }
            ]
        },
        {
            "exam_id": "exam_frenos",
            "module_id": "mod_frenos",
            "title": "Examen: Frenos",
            "passing_score": 70,
            "questions": [
                {
                    "text": "Los frenos a disco son más eficientes que los frenos a tambor.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                },
                {
                    "text": "¿Qué significa ABS en sistemas de frenos?",
                    "type": "multiple_choice",
                    "options": ["Sistema de Freno Absoluto", "Sistema Antibloqueo de Frenos", "Asistente de Frenado", "Sistema de Freno Automático"],
                    "correct_answer": "Sistema Antibloqueo de Frenos"
                }
            ]
        },
        {
            "exam_id": "exam_seminario_frenos",
            "module_id": "mod_seminario_frenos",
            "title": "Examen: Seminario de Frenos",
            "passing_score": 70,
            "questions": [
                {
                    "text": "El material de fricción de las pastillas de freno puede ser orgánico, semimetálico o sinterizado.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                },
                {
                    "text": "¿Para qué se utiliza un dinamómetro en el taller?",
                    "type": "multiple_choice",
                    "options": ["Para medir potencia y torque", "Para cambiar aceite", "Para pintar la moto", "Para inflar neumáticos"],
                    "correct_answer": "Para medir potencia y torque"
                }
            ]
        },
        {
            "exam_id": "exam_distribucion",
            "module_id": "mod_distribucion",
            "title": "Examen: Distribución",
            "passing_score": 70,
            "questions": [
                {
                    "text": "¿Qué componente controla la apertura y cierre de las válvulas?",
                    "type": "multiple_choice",
                    "options": ["Pistón", "Árbol de levas", "Cigüeñal", "Biela"],
                    "correct_answer": "Árbol de levas"
                },
                {
                    "text": "La regulación de válvulas es importante para el correcto funcionamiento del motor.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                }
            ]
        },
        {
            "exam_id": "exam_chasis",
            "module_id": "mod_chasis",
            "title": "Examen: Chasis y Suspensión",
            "passing_score": 70,
            "questions": [
                {
                    "text": "¿Cuál es la función principal de la suspensión?",
                    "type": "multiple_choice",
                    "options": ["Aumentar velocidad", "Absorber impactos del camino", "Enfriar el motor", "Mejorar la aerodinámica"],
                    "correct_answer": "Absorber impactos del camino"
                },
                {
                    "text": "El basculante es parte del sistema de suspensión trasera.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                }
            ]
        },
        {
            "exam_id": "exam_suspension_avanzada",
            "module_id": "mod_suspension_avanzada",
            "title": "Examen: Suspensión Avanzada",
            "passing_score": 70,
            "questions": [
                {
                    "text": "La precarga del resorte determina la altura inicial de la suspensión.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                },
                {
                    "text": "¿Qué caracteriza a una horquilla invertida?",
                    "type": "multiple_choice",
                    "options": ["Los tubos fijos van arriba y las botellas abajo", "No tiene resortes", "Es más pesada siempre", "Solo se usa en scooters"],
                    "correct_answer": "Los tubos fijos van arriba y las botellas abajo"
                }
            ]
        },
        {
            "exam_id": "exam_motores",
            "module_id": "mod_motores",
            "title": "Examen: Tipos de Motores",
            "passing_score": 70,
            "questions": [
                {
                    "text": "¿Cuántos tiempos tiene un ciclo completo en un motor 4T?",
                    "type": "multiple_choice",
                    "options": ["2", "3", "4", "5"],
                    "correct_answer": "4"
                },
                {
                    "text": "Los motores 2T requieren mezcla de aceite en el combustible.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                }
            ]
        },
        {
            "exam_id": "exam_embrague",
            "module_id": "mod_embrague",
            "title": "Examen: Embrague y Cilindro",
            "passing_score": 70,
            "questions": [
                {
                    "text": "¿Cuál es la función del embrague?",
                    "type": "multiple_choice",
                    "options": ["Enfriar el motor", "Conectar/desconectar la transmisión", "Filtrar aceite", "Regular combustible"],
                    "correct_answer": "Conectar/desconectar la transmisión"
                },
                {
                    "text": "El pistón se mueve dentro del cilindro.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                }
            ]
        },
        {
            "exam_id": "exam_lubricacion_avanzada",
            "module_id": "mod_lubricacion_avanzada",
            "title": "Examen: Lubricación Avanzada",
            "passing_score": 70,
            "questions": [
                {
                    "text": "Los aditivos antidesgaste protegen los engranajes formando una capa sobre las superficies metálicas.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                },
                {
                    "text": "¿Qué puede indicar la presencia de depósitos de carbón en el pistón?",
                    "type": "multiple_choice",
                    "options": ["Aceite de mala calidad o combustión incompleta", "Exceso de refrigerante", "Presión de neumáticos baja", "Batería descargada"],
                    "correct_answer": "Aceite de mala calidad o combustión incompleta"
                }
            ]
        },
        {
            "exam_id": "exam_caja",
            "module_id": "mod_caja",
            "title": "Examen: Caja de Velocidades",
            "passing_score": 70,
            "questions": [
                {
                    "text": "¿Qué componente permite cambiar de marcha?",
                    "type": "multiple_choice",
                    "options": ["Embrague", "Caja de velocidades", "Carburador", "Bujía"],
                    "correct_answer": "Caja de velocidades"
                }
            ]
        },
        {
            "exam_id": "exam_carburador",
            "module_id": "mod_carburador",
            "title": "Examen: Carburador",
            "passing_score": 70,
            "questions": [
                {
                    "text": "El carburador mezcla aire y combustible.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                }
            ]
        },
        {
            "exam_id": "exam_refrigeracion",
            "module_id": "mod_refrigeracion",
            "title": "Examen: Refrigeración",
            "passing_score": 70,
            "questions": [
                {
                    "text": "¿Cuál es la función del sistema de refrigeración?",
                    "type": "multiple_choice",
                    "options": ["Acelerar la moto", "Mantener temperatura óptima", "Limpiar filtros", "Cambiar marchas"],
                    "correct_answer": "Mantener temperatura óptima"
                }
            ]
        },
        {
            "exam_id": "exam_transmision",
            "module_id": "mod_transmision",
            "title": "Examen: Transmisión",
            "passing_score": 70,
            "questions": [
                {
                    "text": "La cadena transmite potencia del motor a la rueda trasera.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                }
            ]
        },
        {
            "exam_id": "exam_teoria_electricidad",
            "module_id": "mod_teoria_electricidad",
            "title": "Examen: Teoría de la electricidad",
            "passing_score": 70,
            "questions": [
                {
                    "text": "Según la Ley de Ohm, ¿qué relación existe entre voltaje, corriente y resistencia?",
                    "type": "multiple_choice",
                    "options": ["V = I / R", "V = I x R", "V = R / I", "No están relacionados"],
                    "correct_answer": "V = I x R"
                },
                {
                    "text": "Un diodo permite el paso de corriente en un solo sentido.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                },
                {
                    "text": "¿Qué función cumple el puente de diodos?",
                    "type": "multiple_choice",
                    "options": ["Genera corriente alterna", "Convierte corriente alterna en continua", "Almacena energía", "Regula la temperatura"],
                    "correct_answer": "Convierte corriente alterna en continua"
                }
            ]
        },
        {
            "exam_id": "exam_inyeccion",
            "module_id": "mod_inyeccion",
            "title": "Examen: Inyección Electrónica",
            "passing_score": 70,
            "questions": [
                {
                    "text": "¿Qué componente es considerado el 'cerebro' del sistema de inyección electrónica?",
                    "type": "multiple_choice",
                    "options": ["El inyector", "La ECU", "La sonda lambda", "El carburador"],
                    "correct_answer": "La ECU"
                },
                {
                    "text": "El sensor TPS mide la posición de la mariposa de aceleración.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                },
                {
                    "text": "¿Qué mide la sonda lambda?",
                    "type": "multiple_choice",
                    "options": ["La temperatura del motor", "El oxígeno en los gases de escape", "La presión de combustible", "La velocidad del motor"],
                    "correct_answer": "El oxígeno en los gases de escape"
                }
            ]
        },
        {
            "exam_id": "exam_diagnostico",
            "module_id": "mod_diagnostico",
            "title": "Examen: Diagnóstico de Motocicletas",
            "passing_score": 70,
            "questions": [
                {
                    "text": "Una bujía con depósitos negros y húmedos suele indicar exceso de combustible o aceite.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                },
                {
                    "text": "¿Qué herramienta se utiliza para tomar mediciones precisas de piezas del motor?",
                    "type": "multiple_choice",
                    "options": ["Destornillador", "Calibre o pie de rey", "Llave de tubo", "Martillo"],
                    "correct_answer": "Calibre o pie de rey"
                }
            ]
        },
        {
            "exam_id": "exam_herramientas",
            "module_id": "mod_herramientas",
            "title": "Examen: Herramientas del Taller",
            "passing_score": 70,
            "questions": [
                {
                    "text": "¿Para qué se utiliza la llave dinamométrica o torquímetro?",
                    "type": "multiple_choice",
                    "options": ["Para medir voltaje", "Para aplicar el par de apriete correcto a un tornillo", "Para medir temperatura", "Para cortar cables"],
                    "correct_answer": "Para aplicar el par de apriete correcto a un tornillo"
                },
                {
                    "text": "El compresor de aire se utiliza en el taller para accionar herramientas neumáticas.",
                    "type": "true_false",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero"
                }
            ]
        }
    ]
}

async def seed_database():
    print("🌱 Starting database seeding with REAL YouTube videos...")
    
    try:
        # Clear existing data
        print("🗑️  Clearing existing data...")
        await db.modules.delete_many({})
        await db.lessons.delete_many({})
        await db.exams.delete_many({})
        
        # Insert modules
        print("📚 Inserting modules...")
        await db.modules.insert_many(course_data["modules"])
        
        # Insert lessons
        print("🎥 Inserting lessons with real motorcycle videos...")
        order = 1
        for module_id, lessons in course_data["lessons"].items():
            for lesson_data in lessons:
                lesson = {
                    "lesson_id": f"lesson_{order}",
                    "module_id": module_id,
                    "title": lesson_data["title"],
                    "duration": lesson_data["duration"],
                    "video_url": lesson_data["video_url"],
                    "order": order,
                    "is_free": lesson_data["is_free"]
                }
                await db.lessons.insert_one(lesson)
                order += 1
        
        # Insert exams
        print("📝 Inserting exams...")
        for exam in course_data["exams"]:
            for i, question in enumerate(exam["questions"]):
                question["question_id"] = f"q_{exam['exam_id']}_{i+1}"
            await db.exams.insert_one(exam)
        
        print("✅ Database seeded successfully!")
        print(f"   - {len(course_data['modules'])} modules")
        total_lessons = sum(len(lessons) for lessons in course_data['lessons'].values())
        print(f"   - {total_lessons} lessons with REAL motorcycle mechanics videos")
        print(f"   - {len(course_data['exams'])} exams")
        print(f"   - {len(VIDEOS)} unique YouTube videos")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
