import pygame
import os
from network import NetworkManager
from Game import startRound#,
from Turn import drawCard, refillDeck
import time 
from Round import Round
from Deck import Deck
from Card import Card
import threading


network_manager = None   #NetworkManager()
jugadores = []           #network_manager.connected_players
print(f"Jugadore ... {jugadores}")

pygame.init()

icon = pygame.image.load("assets/icon.png")  # Reemplaza con la ruta correcta a tu imagen
pygame.display.set_icon(icon)
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("RUMMY 500")


mensaje_orden = ""
tiempo_inicio_orden = 0

#player1.isHand = True 
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Rummy 500 - Layout Base")

# Cargar fondo
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")
fondo_path = os.path.join(ASSETS_PATH, "fondo_juego.png")
fondo_img = pygame.image.load(fondo_path).convert()
fondo_img = pygame.transform.scale(fondo_img, (WIDTH, HEIGHT))

# Colores (con alpha para transparencia)
CAJA_JUG = (70, 130, 180, 60)   # Más transparente
CAJA_BAJ = (100, 200, 100, 60)
CENTRAL = (50, 50, 80, 60)
TEXTO = (255, 255, 255)
BORDER = (0, 0, 0, 180)

font = pygame.font.SysFont("arial", 16, bold=True)

# Proporciones relativas
bajada_h_pct = 0.125
bajada_w_pct = 0.083
jug_w_pct = 0.092
jug_h_pct = 0.137

# Diccionario para identificar cada caja
boxes = {}

cartas_apartadas = set()
cartas_ocultas = set()

zona_cartas_snapshot = None

mazo_descarte = []  # Lista para el mazo de descarte

# guarda la última carta tomada y por quién (para impedir descartarla en el mismo turno)
last_taken_card = None
last_taken_player = None

def register_taken_card(player, card):
    global last_taken_card, last_taken_player
    last_taken_card = card
    last_taken_player = player

def clear_taken_card_for_player(player):
    global last_taken_card, last_taken_player
    if last_taken_player is not player:
        last_taken_card = None
        last_taken_player = None

def can_discard(player, cards):
    # devuelve False si el jugador intentara descartar la carta que tomó este turno
    global last_taken_card, last_taken_player
    # si no es el mismo jugador o no hay carta registrada, permitir
    if last_taken_player is not player or last_taken_card is None:
        return True

    # normaliza a lista
    if isinstance(cards, (list, tuple, set)):
        items = list(cards)
    else:
        items = [cards]

    for c in items:
        # compara por identidad primero, luego por igualdad de string/valor
        try:
            if c is last_taken_card or c == last_taken_card:
                return False
        except Exception:
            if str(c) == str(last_taken_card):
                return False
    return True

def string_to_card(card_str):
    #verificamos si card_str es una lista
    if isinstance(card_str, list):
        for c in card_str:
            if c == "Joker":
                return Card("Joker", "", joker=True)
            value = c[:-1]
            suit = c[-1]
            return Card(value, suit)
    elif not isinstance(card_str, str) and not isinstance(card_str, list):
        return card_str
    else:
        if card_str == "Joker":
            return Card("Joker", "", joker=True)
        value = card_str[:-1]    # todo menos el último carácter (valor)
        suit = card_str[-1]      # último carácter (palo)
        return Card(value, suit)

# Nueva función: valida tipos y llama insertCard solo si todo está correcto
def safe_insert_card(current_player, target_player, target_index, card_to_insert, position):
    """
    Comprueba que card_to_insert y las cartas en la jugada objetivo sean objetos Card.
    Devuelve True si llamó a current_player.insertCard(...) con éxito, False y print de debug en consola si falla.
    """
    from Card import Card
    # Comprueba que la carta a insertar sea un Card (no un str)
    if not isinstance(card_to_insert, Card):
        print("safe_insert_card: card_to_insert NO es Card:", type(card_to_insert), repr(card_to_insert))
        return False

    # Obtiene la jugada objetivo y extrae la lista de cartas
    plays = getattr(target_player, "playMade", [])
    if target_index < 0 or target_index >= len(plays):
        print("safe_insert_card: target_index fuera de rango:", target_index, "len(playMade)=", len(plays))
        return False

    target_play = plays[target_index]
    # target_play puede ser dict con 'trio' o 'straight' o una lista
    if isinstance(target_play, dict):
        cartas_jugada = target_play.get("trio") or target_play.get("straight") or []
    else:
        cartas_jugada = target_play or []

    # Verifica que todas las cartas de la jugada sean Card
    for c in cartas_jugada:
        if not isinstance(c, Card):
            print("safe_insert_card: elemento en la jugada objetivo NO es Card:", type(c), repr(c))
            # imprime estado completo para debugging
            print("target_player.playMade[{}] = {}".format(target_index, target_play))
            return False

    # Todo correcto: llama al método real de inserción
    try:
        current_player.insertCard(targetPlayer=target_player, targetPlayIndex=target_index, cardToInsert=card_to_insert, position=position)
        return True
    except Exception as e:
        print("safe_insert_card: excepción al llamar insertCard:", e)
        return False

def draw_transparent_rect(surface, color, rect, border=1):
    temp_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    temp_surface.fill(color)
    surface.blit(temp_surface, (rect.x, rect.y))
    pygame.draw.rect(surface, BORDER, rect, border)

def draw_label(rect, text):
    label = font.render(text, True, TEXTO)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)

def get_clicked_box(mouse_pos, cuadros):
    """
    Retorna el nombre del cuadro clickeado o None si no se clickeó ninguno.
    Si hay solapamiento (como en las cartas), prioriza la carta más a la derecha (la que está encima).
    """
    # Recorre los cuadros en orden inverso para que la última carta (más a la derecha) tenga prioridad
    for nombre, rect in reversed(list(cuadros.items())):
        if rect.collidepoint(mouse_pos):
            return nombre
                
    return None

def get_card_image(card):
    """
    Devuelve la imagen pygame de la carta según su string (por ejemplo, '2♣.png').
    Si es Joker, busca JokerV2.png.
    Si no existe, devuelve una imagen de carta genérica.
    """
    if hasattr(card, "joker") and card.joker:
        nombre = "JokerV2.png"
    else:
        nombre = str(card) + ".png"
    ruta = os.path.join(ASSETS_PATH, "cartas", nombre)
    if os.path.exists(ruta):
        return pygame.image.load(ruta).convert_alpha()
    else:
        # Imagen genérica si no existe la carta
        generic_path = os.path.join(ASSETS_PATH, "cartas", "back.png")
        if os.path.exists(generic_path):
            return pygame.image.load(generic_path).convert_alpha()
        else:
            # Si tampoco existe back.png, crea una carta vacía
            img = pygame.Surface((60, 90), pygame.SRCALPHA)
            pygame.draw.rect(img, (200, 200, 200), img.get_rect(), border_radius=8)
            return img

def draw_player_hand(player, rect, cuadros_interactivos=None, cartas_ref=None, ocultas=None):
    """
    Dibuja la mano del jugador alineada horizontalmente, solapada, sin curva ni inclinación.
    """
    hand = getattr(player, "playerHand", [])
    n = len(hand)
    if n == 0:
        return

    card_height = rect.height - 6
    card_width = int(card_height * 0.68)

    # Solapamiento horizontal
    if n > 1:
        base_sep = int(card_width * 1.25)
        min_sep = int(card_width * 0.65)
        if n <= 6:
            solapamiento = base_sep
        elif n >= 12:
            solapamiento = min_sep
        else:
            solapamiento = int(base_sep - (base_sep - min_sep) * (n - 6) / 6)
        total_width = card_width + (n - 1) * solapamiento
        if total_width > rect.width:
            solapamiento = max(8, (rect.width - card_width) // (n - 1))
        start_x = rect.x + (rect.width - (card_width + (n - 1) * solapamiento)) // 2
    else:
        solapamiento = 0
        start_x = rect.x + (rect.width - card_width) // 2

    y_base = rect.y + 18  # Puedes ajustar este valor si quieres subir/bajar las cartas

    for i in range(n):
        if ocultas and i in ocultas:
            continue
        card = hand[i]
        string_to_card(card)
        img = get_card_image(card)
        img = pygame.transform.smoothscale(img, (card_width, card_height))
        # Sin curva ni inclinación
        img_rect = img.get_rect(topleft=(start_x + i * solapamiento, y_base))
        screen.blit(img, img_rect.topleft)

        if cuadros_interactivos is not None:
            cuadros_interactivos[f"Carta_{i}"] = img_rect
        if cartas_ref is not None:
            cartas_ref[f"Carta_{i}"] = card

def draw_vertical_back_hand(player, rect):
    """
    Dibuja cartas boca abajo en vertical, tipo lluvia, según la cantidad real de cartas del jugador.
    """
    n = len(getattr(player, "playerHand", []))
    if n == 0:
        return

    # Tamaño de carta
    card_width = rect.width - 8
    card_height = int(card_width / 0.68)
    if card_height > rect.height // 2:
        card_height = rect.height // 2
        card_width = int(card_height * 0.68)

    # Solapamiento vertical
    if n > 1:
        solapamiento = (rect.height - card_height) // (n - 1)
        if solapamiento > card_height * 0.7:
            solapamiento = int(card_height * 0.7)
    else:
        solapamiento = 0

    start_y = rect.y + rect.height - card_height - (n - 1) * solapamiento

    # Imagen de reverso
    back_img = get_card_image("back")

    for i in range(n):
        img = pygame.transform.smoothscale(back_img, (card_width, card_height))
        card_rect = pygame.Rect(rect.x + (rect.width - card_width) // 2,
                                start_y + i * solapamiento,
                                card_width, card_height)
        screen.blit(img, card_rect.topleft)

def draw_back_cards_by_count(count, rect):
    """
    Dibuja 'count' cartas boca abajo en vertical (tipo lluvia) en el rectángulo dado.
    """
    if count == 0:
        return

    # Tamaño de carta
    card_width = rect.width - 8
    card_height = int(card_width / 0.68)
    if card_height > rect.height // 2:
        card_height = rect.height // 2
        card_width = int(card_height * 0.68)

    # Solapamiento vertical
    if count > 1:
        solapamiento = (rect.height - card_height) // (count - 1)
        if solapamiento > card_height * 0.7:
            solapamiento = int(card_height * 0.7)
    else:
        solapamiento = 0

    start_y = rect.y + rect.height - card_height - (count - 1) * solapamiento

    # Imagen de reverso
    back_img = get_card_image("back")

    for i in range(count):
        img = pygame.transform.smoothscale(back_img, (card_width, card_height))
        card_rect = pygame.Rect(rect.x + (rect.width - card_width) // 2,
                                start_y + i * solapamiento,
                                card_width, card_height)
        screen.blit(img, card_rect.topleft)

def draw_horizontal_pt_hand(player, rect):
    """
    Dibuja cartas horizontales usando PT.png, según la cantidad real de cartas del jugador.
    """
    n = len(getattr(player, "playerHand", []))
    if n == 0:
        return

    # Tamaño de carta
    card_height = rect.height - 8
    card_width = int(card_height * 0.68)
    if n > 1:
        max_width = rect.width - 8
        solapamiento = (max_width - card_width) // (n - 1)
        if solapamiento > card_width * 0.7:
            solapamiento = int(card_width * 0.7)
    else:
        solapamiento = 0

    start_x = rect.x
    y = rect.y + (rect.height - card_height) // 2

    # Imagen PT.png
    pt_img_path = os.path.join(ASSETS_PATH, "cartas", "PT.png")
    if os.path.exists(pt_img_path):
        pt_img = pygame.image.load(pt_img_path).convert_alpha()
    else:
        pt_img = get_card_image("back")

    for i in range(n):
        img = pygame.transform.smoothscale(pt_img, (card_width, card_height))
        card_rect = pygame.Rect(start_x + i * solapamiento, y, card_width, card_height)
        screen.blit(img, card_rect.topleft)

def draw_vertical_pt_hand(player, rect):
    """
    Dibuja cartas verticales usando PT.png, según la cantidad real de cartas del jugador.
    """
    n = len(getattr(player, "playerHand", []))
    if n == 0:
        return

    # Tamaño de carta
    card_width = rect.width - 8
    card_height = int(card_width / 0.68)
    if n > 1:
        max_height = rect.height - 8
        solapamiento = (max_height - card_height) // (n - 1)
        if solapamiento > card_height * 0.7:
            solapamiento = int(card_height * 0.7)
    else:
        solapamiento = 0

    x = rect.x + (rect.width - card_width) // 2
    start_y = rect.y

    # Imagen PT.png
    pt_img_path = os.path.join(ASSETS_PATH, "cartas", "PT.png")
    if os.path.exists(pt_img_path):
        pt_img = pygame.image.load(pt_img_path).convert_alpha()
    else:
        pt_img = get_card_image("back")

    for i in range(n):
        img = pygame.transform.smoothscale(pt_img, (card_width, card_height))
        card_rect = pygame.Rect(x, start_y + i * solapamiento, card_width, card_height)
        screen.blit(img, card_rect.topleft)

def draw_horizontal_rain_hand_rotated(player, rect):
    """
    Dibuja cartas en modo 'lluvia horizontal' pero verticalmente (cartas apiladas horizontalmente, rotadas 90 grados).
    El ancho de la carta es igual al de las cartas superiores y el ALTO (largo real de la carta) es más fino.
    """
    n = len(getattr(player, "playerHand", []))
    if n == 0:
        return

    # MISMO ancho que las cartas superiores, pero más finas (menos alto)
    card_width = 120   # igual que cuadro_w_carta
    card_height = 120  # más fino que las superiores (antes era 188)

    if n > 1:
        max_height = rect.height - 8
        solapamiento = (max_height - card_height) // (n - 1)
        if solapamiento > card_height * 0.7:
            solapamiento = int(card_height * 0.7)
        if solapamiento < 0:
            solapamiento = 0
    else:
        solapamiento = 0

    x = rect.x + (rect.width - card_height) // 2
    start_y = rect.y

    pt_img_path = os.path.join(ASSETS_PATH, "cartas", "PT.png")
    if os.path.exists(pt_img_path):
        pt_img = pygame.image.load(pt_img_path).convert_alpha()
    else:
        pt_img = get_card_image("back")

    for i in range(n):
        img = pygame.transform.smoothscale(pt_img, (card_height, card_width))
        img = pygame.transform.rotate(img, 90)
        card_rect = pygame.Rect(x, start_y + i * solapamiento, card_width, card_height)
        # No dibujar si se sale del recuadro
        if card_rect.bottom <= rect.bottom:
            screen.blit(img, card_rect.topleft)


def main(manager_de_red): # <-- Acepta el manager de red
    global screen, WIDTH, HEIGHT, fondo_img, organizar_habilitado, fase
    global network_manager, jugadores , players, cartas_eleccion
    global cuadros_interactivos, cartas_ref, zona_cartas, visual_hand
    global dragging, carta_arrastrada, drag_rect, drag_offset_x, cartas_congeladas
    global cartas_ocultas, organizar_habilitado, mensaje_temporal, mensaje_tiempo
    global fase_fin_tiempo, mazo_descarte, deckForRound, round
    global mostrar_joker_fondo, tiempo_joker_fondo

    global player1   #NUEVO PARA PRUEBA
    global jugador_local  #NUEVO PARA PRUEBA Reeplazo de player1 :'(
    global siguiente_jugador_local


    pygame.mixer.init()
    inicio_sound_path = os.path.join(os.path.dirname(__file__), "assets", "sonido", "inicio.wav")
    inicio_sound = pygame.mixer.Sound(inicio_sound_path)
    inicio_sound.play()

    # Asignar toda la informacion del manager de red de ui.py
    network_manager = manager_de_red 
    
    # Obtener los datos compartidos
    jugadores = network_manager.connected_players
    print(f"Jugadores conectados en ui2.py: {jugadores}")
    
    from Card import Card
    from Player import Player

    # NUEVA INICIALIZACIÓN PARA EL JUGADOR
    players = []         # Lista de jugadores (vacía hasta que la reciba del host)
    cartas_eleccion = [] # Lista de cartas de elección (vacía hasta que la reciba del host)
    player1 = None # NUEVO PARA PRUEBA
    
    if network_manager.is_host:
        players = []
        print(f" puerto del servidor {jugadores[0][1][1]}")
        host_port = jugadores[0][1][1]
        # --- Jugador 1 ---
        player1 = Player(host_port, "Host")

        players.append(player1)
        #player1.isHand = True
        jugador_local = player1  # NUEVO PARA PRUEBA

        for jugador_socket_info in network_manager.connected_players[1:]:
            # Obtener el puerto del cliente
            cliente_port = jugador_socket_info[1][1] 
            cliente_name = jugador_socket_info[2]
            player_cliente = Player( cliente_port, str(cliente_name)) 
            # Asignando mano inicial a los jugadores... Preguntar a Louis por la función
            players.append(player_cliente)
            #player_cliente.isHand = True
    
        print(f"Jugadores creados: {len(players)}")
        fase = "eleccion"        
    else:
        # El Jugador va directo a la fase de eleccion
        jugador_local = None  # NUEVO PARA PRUEBA
        fase = "eleccion"
    
    #from test3 import players
    running = True

    cuadros_interactivos = {}
    cartas_ref = {}

    zona_cartas = [[], [], []]  # [0]=Seguidilla, [1]=Trio, [2]=Descarte

    # Crea un set para ids de cartas "congeladas"
    cartas_congeladas = set()

    # Variables para el arrastre visual
    dragging = False
    carta_arrastrada = None
    drag_rect = None
    drag_offset_x = 0

    cartas_ocultas = set()  # Al inicio de main()
    organizar_habilitado = True  # Inicializa la variable

    # Variables temporales:
    mensaje_temporal = ""
    mensaje_tiempo = 0

    fase_fin_tiempo = 0  # Para controlar cuánto tiempo mostrar la pantalla final
           
    # --- CARTAS DE ELECCIÓN ---
    if network_manager.is_host:
        # El host genera las cartas de elección
        deck = Deck()
        cartas_eleccion = deck.drawInElectionPhase(len(players))
        visual_hand = list(player1.playerHand)  # Copia inicial para el orden visual
        # Asigna un id único a cada carta de la mano visual
        for idx, carta in enumerate(visual_hand):
            if not hasattr(carta, "id_visual"):
                carta.id_visual = id(carta)  # O usa idx para algo más simple

        msgEleccion = {
                    "type": "ELECTION_CARDS",
                    "players": players,
                    "election_cards": cartas_eleccion
                    }
        print(f"Transmitiendo lista de jugadores.................")
        recalcular_posiciones_eleccion(cartas_eleccion, WIDTH, HEIGHT)
        network_manager.broadcast_message(msgEleccion) 
        fase = "eleccion"
    
    # Cargar sonido de carta
    carta_sound_path = os.path.join(ASSETS_PATH, "sonido", "carta.wav")
    carta_sound = pygame.mixer.Sound(carta_sound_path)

    # Cargar sonido de bajarse
    bajarse_sound_path = os.path.join(ASSETS_PATH, "sonido", "bajarse.wav")
    bajarse_sound = pygame.mixer.Sound(bajarse_sound_path)

    #contJugador = 0
    #contHost = 0

    while running:
        # --- SOLO FASE DE ELECCIÓN ---
        if fase == "eleccion":
            screen.blit(fondo_img, (0, 0))  # Nuevo pero se puede quedar :)

            # Procesando mensaje con datos de seleccion de cartas y la lista de jugadores...
            if not network_manager.is_host:
                # Recuperar los mensajes recibidos del buffer de red
                msg = network_manager.get_game_state() 
                # Verificar si el mensaje contiene los datos esperados
                if isinstance(msg, dict) and msg.get("type") == "ELECTION_CARDS":
                    print(f"Este es el mensaje recibido en fase eleccion  {type(msg)} {msg}{msg.get('type')}")
                    players[:] = msg.get("players")
                    cartas_eleccion = msg.get("election_cards")
                    player1 = players[0]

                # Procesar mensajes entrantes para actualizaciones de elecciones o orden
                msgList = network_manager.get_incoming_messages()
                #print(f"Este es el mensaje recibido en fase eleccion ORDENNNN  {type(msgList)} {msgList}")
                for msg in msgList:
                    if isinstance(msg[1], dict):
                        if msg[1].get("type") == "PLAYER_ORDER":
                            print("📥 Cliente: Recibido orden de jugadores")
                            players[:] = msg[1].get("players", [])
                            deckForRound = msg[1].get("deckForRound")
                            mazo_descarte = msg[1].get("mazo_descarte")
                            hands = msg[1].get("hands")
                            round = msg[1].get("round")
                            received_round = msg[1].get("round")
                            
                            if received_round:
                                round = received_round
                                deckForRound = round.pile
                                mazo_descarte = round.discards
                            else:
                                # Crear una instancia mínima de Round y rellenar pilas si vienen en el mensaje
                                round = Round(players)
                                deck_for_round = msg[1].get("deckForRound")
                                mazo_descarte_msg = msg[1].get("mazo_descarte")
                                if deck_for_round is not None:
                                    round.pile = list(deck_for_round)
                                if mazo_descarte_msg is not None:
                                    round.discards = list(mazo_descarte_msg)
                                # asegurar que round.players apunte a la lista de objetos Player
                                round.players = players
                                print("Cliente: creado Round local con pile/discards recibidos.")
                            # Buscar y actualizar jugador local
                            puerto_local = network_manager.player.getsockname()[1]
                            for p in players:
                                if p.playerId == puerto_local:
                                    jugador_local = p
                                    break

                            jugador_local.playerHand = hands[jugador_local.playerId] 
                            visual_hand = list(jugador_local.playerHand)  # Copia inicial para el orden visual
                            for idx, carta in enumerate(visual_hand):
                                if not hasattr(carta, "id_visual"):
                                    carta.id_visual = id(carta)  # O usa idx para algo más simple

                            # Cambiar fase
                            mensaje_orden = msg[1].get("orden_str", "")
                            tiempo_inicio_orden = time.time()
                            fase = "mostrar_orden"
                # Fin procesar Mensajes de INICIO----  Cargar Mazos, Mano, e isHand... PARA EL JUGADOR...       

            if network_manager.is_host:
                from Game import electionPhase
                playerOrder = electionPhase(players, deck)
                # Lista de jugadores Ordenada
                players[:] = playerOrder
                players[0].isHand = True    # El primer jugador es mano
                player1 = None
                
                #for p in players:
                if players[0].playerId == host_port:
                    jugador_local = players[0]
                    print(f"nombrel del jugador_local   {jugador_local.playerName}")  

                # Construir mensaje de orden
                orden_str = "Orden de juego:\n"
                for idx, jugador in enumerate(players):
                    orden_str += f"{idx+1}. {jugador.playerName}\n"
                round = startRound(players, screen)[0]
                print(f"deck para la ronda: {[c for c in round.pile]}")
                print(f"descartes de la ronda: {[c for c in round.discards]}")
                for c in round.discards:
                    mazo_descarte.append(c)
                deckForRound = round.pile
                print(f"Las manos a repartir ...... {round.hands}")
                # Enviar orden a todos
                msgOrden = {
                    "type": "PLAYER_ORDER",
                    "players": players,
                    "orden_str": orden_str,
                    "round": round,
                    "hands":round.hands,
                    "deckForRound": deckForRound,
                    "mazo_descarte": mazo_descarte
                }
                network_manager.broadcast_message(msgOrden)
                # Cambiar fase
                mensaje_orden = orden_str.strip()
                tiempo_inicio_orden = time.time()
                fase = "mostrar_orden"

            # Dibujar
            screen.blit(fondo_img, (0, 0))
            #mostrar_cartas_eleccion(screen, cartas_eleccion)
            pygame.display.flip()
            continue  # <-- Esto es CLAVE: salta el resto del ciclo si estás en la fase de elección
        # Fin de la fase "eleccion"   ---- Está alineado... Mejor ubicacion..

        
        # --- FASE DE JUEGO NORMAL ---
        # Procesando mensajes del juego
        if not network_manager.is_host:
            msgGame = network_manager.get_moves_game()
        else:
            msgGame = network_manager.get_moves_gameServer()
        if msgGame:
            print(f"TURNO DEL JUGADOR: {[p.playerName for p in players if p.isHand]}")
            print(f"llego esto de get_moves_game.. {type(msgGame)} {msgGame}")
        
        for msg in msgGame:
            if isinstance(msg,dict) and msg.get("type")=="BAJARSE":
                player_id_que_se_bajo = msg.get("playerId")
                #mano_restante = msg.get("playerHand")  # Lista de objetos Card
                jugadas_en_mesa = msg.get("jugadas_bajadas")  # Lista con las combinaciones (tríos/escaleras)
                Jugadas_en_mesa2 = msg.get("playMade")    ## Lista con las combinaciones (tríos/escaleras) en INGLES :D
                round = msg.get("round")

                print(f"Mensaje de BAJARSE recibido del Player ID: {player_id_que_se_bajo}")
                for p in players:
                    if p.playerId == player_id_que_se_bajo:
                        p.playerHand = mano_restante
                        p.jugadas_bajadas = jugadas_en_mesa
                        p.playMade = Jugadas_en_mesa2
            
            elif isinstance(msg,dict) and msg.get("type")=="TOMAR_DESCARTE":
                player_id_que_tomoD = msg.get("playerId")
                mano_restante = msg.get("playerHand")  # Lista de objetos Card
                carta_tomada = msg.get("cardTakenD")  # Lista con las combinaciones (tríos/escaleras)
                mazo_de_descarte = msg.get("mazo_descarte")
                round = msg.get("round")
                
                print(f"Mensaje de TOMAR DESCARTE recibido del Player ID: {player_id_que_tomoD}")
                for p in players:
                    if p.playerId == player_id_que_tomoD:
                        p.playerHand = mano_restante
                        #pass
                cardTakenD = carta_tomada
                mazo_descarte = mazo_de_descarte   #round.discards #mazo_de_descarte

            elif isinstance(msg,dict) and msg.get("type")=="TOMAR_CARTA":
                player_id_que_tomoC = msg.get("playerId")
                mano_restante = msg.get("playerHand")  # Lista de objetos Card
                carta_tomada = msg.get("cardTaken")  # Lista con las combinaciones (tríos/escaleras)
                mazoBocaAbajo = msg.get("mazo")
                round = msg.get("round")
                
                print(f"Mensaje de TOMAR CARTA recibido del Player ID: {player_id_que_tomoC}")
                for p in players:
                    if p.playerId == player_id_que_tomoC:
                        p.playerHand = mano_restante
                        #pass
                cardTaken = carta_tomada
                deckForRound = mazoBocaAbajo #round.pile

            elif isinstance(msg,dict) and msg.get("type")=="DESCARTE":
                #print(f"Prueba de isHand ANTES JUGADOR: {[p.isHand for p in players]}")
                player_id_que_descarto = msg.get("playerId")
                mano_restante = msg.get("playerHand")  # Lista de objetos Card
                cartasDescartadas = msg.get("cartas_descartadas")
                mazo_de_descarte = msg.get("mazo_descarte")
                players[:] = msg.get("players")
                deck_for_round = msg.get("deckForRound")
                round = msg.get("round")
                
                received_round = msg.get("round")
                
                if received_round:
                    round = received_round
                    deckForRound = round.pile
                    mazo_descarte = round.discards
                else:
                    # Crear una instancia mínima de Round y rellenar pilas si vienen en el mensaje
                    round = Round(players)
                    deck_for_round = msg.get("deckForRound")
                    mazo_descarte_msg = msg.get("mazo_descarte")
                    if deck_for_round is not None:
                        round.pile = list(deck_for_round)
                    if mazo_descarte_msg is not None:
                        round.discards = list(mazo_descarte_msg)
                    round.players = players

                for p in players:
                    if network_manager.is_host:
                        if p.isHand and p.playerId == host_port:
                            jugador_local = p
                            break
                    else:
                        puerto_local = network_manager.player.getsockname()[1]
                        if p.isHand and p.playerId == puerto_local:
                            jugador_local = p
                            break

                cartas_descartadas = cartasDescartadas
                mazo_descarte = mazo_de_descarte
                
            elif isinstance(msg,dict) and msg.get("type")=="COMPRAR_CARTA":   # Revisar la lógica... No vi la función append>>> Por es lo digo
                player_id_que_tomoC = msg.get("playerId")
                mano_restante = msg.get("playerHand")  # Lista de objetos Card
                cartasDescartadas = msg.get("cartas_descartadas")
                round = msg.get("round")

                print(f"Mensaje de DESCARTE recibido del Player ID: {player_id_que_se_bajo}")
                for p in players:
                    if p.playerId == player_id_que_tomoC:
                        #p.playerHand = mano_restante
                        #???cartas_descartadas = cartasDescartadas
                        #mazo_descarte = mazo_de_descarte
                        #zona_cartas = zonaCartas
                        pass
        # Fin procesar mensajes del juego...
        ###### SIgo aqui...
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                fondo_img = pygame.transform.scale(pygame.image.load(fondo_path).convert(), (WIDTH, HEIGHT))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # --- Detecta clic en inicio o final de cada jugada ---
                mouse_x, mouse_y = event.pos
                for jugador, jugadas in rects_jugadas.items():
                    for idx, jugada in enumerate(jugadas):
                        if jugada["inicio"].collidepoint(mouse_x, mouse_y):
                            print(f"Clic en INICIO de la jugada {idx+1} de {jugador} ({jugada['tipo']})")
                        elif jugada["final"].collidepoint(mouse_x, mouse_y):
                            print(f"Clic en FINAL de la jugada {idx+1} de {jugador} ({jugada['tipo']})")
                nombre = get_clicked_box(event.pos, cuadros_interactivos)
                if nombre and nombre.startswith("Carta_"):
                    idx = int(nombre.split("_")[1])
                    if idx in cartas_ocultas:
                        mensaje_temporal = "No puedes organizar una carta mientras ejecutas una jugada."
                        mensaje_tiempo = time.time()
                    else:
                        carta_arrastrada = cartas_ref[nombre]
                        drag_rect = cuadros_interactivos[nombre]
                        drag_offset_x = event.pos[0] - drag_rect.x
                        dragging = True

                elif nombre:
                    if nombre == "Tomar carta":
                        if jugador_local.cardDrawn:
                            mensaje_temporal = "Ya tomaste una carta en este turno."
                            mensaje_tiempo = time.time()
                        elif not jugador_local.isHand:
                            mensaje_temporal = "No puedes tomar cartas porque no es tu turno."
                            mensaje_tiempo = time.time()
                        else:
                            #print(f"jugadors {[p for p in players]}")
                            #print(f"El jugador local {jugador_local}")
                            cardTaken = drawCard(jugador_local, round, False)
                            #jugador_local.playerHand.append(cardTaken)
                            jugador_local.playerHand = round.hands[jugador_local.playerId]
                            jugador_local.cardDrawn = True
                            #print(f"DEPURACION DECKFORROUND AL TOMAR CARTA: {[c for c in deckForRound]}")

                            if not deckForRound or len(deckForRound) == 0:
                                print(f"DECKFORROUND VACÍOOOOOO: {[c for c in deckForRound]}")
                                refillDeck(round)
                                deckForRound = round.pile
                                mazo_descarte = round.discards 

                                print(f"DECKFORROUND Recargado :)  ... : {[c for c in deckForRound]}")
                                

                            visual_hand = compactar_visual_hand(visual_hand) 
                            msgTomarC = {
                                "type": "TOMAR_CARTA",
                                "cardTaken": cardTaken,
                                "playerHand": jugador_local.playerHand,
                                "playerId": jugador_local.playerId,
                                "mazo": deckForRound, #  El mazo se debe actualizar
                                "round": round
                                }
                            if network_manager.is_host:
                                network_manager.broadcast_message(msgTomarC)
                            elif network_manager.player:
                                network_manager.sendData(msgTomarC)
                    elif nombre == "Tomar descarte":
                        if jugador_local.cardDrawn:
                            mensaje_temporal = "Ya tomaste una carta."
                            mensaje_tiempo = time.time()
                        elif not jugador_local.isHand:
                            mensaje_temporal = "No puedes tomar cartas porque no es tu turno."
                            mensaje_tiempo = time.time()
                        else:
                            #print(f"Mano del jugador ANTES DE tomar la carta: {[str(c) for c in jugador_local.playerHand]}")
                            cardTakenD = drawCard(jugador_local, round, True)
                            #print(f"Mano del jugador al tomar la carta:........ {[str(c) for c in jugador_local.playerHand]}")

                            if mazo_descarte:
                                mazo_descarte.pop()  # Quita la carta del mazo de descarte
                            #jugador_local.playerHand.append(cardTakenD)
                            jugador_local.playerHand = round.hands[jugador_local.playerId]
                            register_taken_card(jugador_local, cardTakenD)
                            mensaje_temporal = "Tomaste una carta: no puedes descartarla este turno."
                            mensaje_tiempo = time.time()
                            #cardTakenInDiscards.append(cardTakenD)
                            visual_hand = compactar_visual_hand(visual_hand)
                            actualizar_indices_visual_hand(visual_hand)
                            visual_hand.clear()
                            for idx, carta in enumerate(jugador_local.playerHand):
                                carta.id_visual = idx
                                visual_hand.append(carta)
                            #reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                            print(f"Carta tomada: {str(cardTakenD)}")
                            print(f"Mano del jugador al tomar la carta: {[str(c) for c in jugador_local.playerHand]}")
                            print(f"Mano visual: {[str(c) for c in visual_hand]}")
                            jugador_local.cardDrawn = True
                            organizar_habilitado = True

                            msgTomarDescarte = {
                                "type": "TOMAR_DESCARTE",
                                "cardTakenD": cardTakenD,
                                "playerHand": jugador_local.playerHand,
                                "playerId": jugador_local.playerId,
                                "mazo_descarte": mazo_descarte,
                                "round": round
                                }
                            if network_manager.is_host:
                                network_manager.broadcast_message(msgTomarDescarte)
                            elif network_manager.player:
                                network_manager.sendData(msgTomarDescarte)


                    elif nombre == "Bajarse":
                        resultado = jugador_local.getOff(zona_cartas[0], zona_cartas[1])
                        cartas_ocultas.clear()
                        if resultado:
                            trios_bajados, seguidillas_bajadas = resultado
                            # Guarda las jugadas bajadas en jugador_local.jugadas_bajadas
                            if not hasattr(jugador_local, "jugadas_bajadas"):
                                jugador_local.jugadas_bajadas = []
                            if trios_bajados:
                                jugador_local.jugadas_bajadas.append(list(trios_bajados))
                            if seguidillas_bajadas:
                                jugador_local.jugadas_bajadas.append(list(seguidillas_bajadas))
                            for carta in trios_bajados + seguidillas_bajadas:
                                if carta in visual_hand:
                                    visual_hand.remove(carta)
                            for i, jugada in enumerate(jugador_local.playMade):
                                print(f"Lainfo de jugador_local>>>>   {[str(c) for c in jugada["trio"]]}")
                        else:
                            cartas_ocultas.clear()
                            zona_cartas[0] = []
                            zona_cartas[0].clear()
                            zona_cartas[1] = []
                            zona_cartas[1].clear()
                        # Actualiza visual_hand y permite organizar
                        visual_hand.clear()
                        for carta in jugador_local.playerHand:
                            visual_hand.append(carta)
                        reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                        organizar_habilitado = True
                        
                        msgBajarse = {
                            "type":"BAJARSE",
                            "playerHand": jugador_local.playerHand,
                            "jugadas_bajadas": jugador_local.jugadas_bajadas,
                            "playMade": jugador_local.playMade,
                            "playerId": jugador_local.playerId,
                            "round": round
                            }
                        if network_manager.is_host:
                            if msgBajarse:
                                network_manager.broadcast_message(msgBajarse)
                            else: 
                                print("Mensaje vacio... No enviado")
                        else:
                            if msgBajarse:
                                network_manager.sendData(msgBajarse)
                            else: 
                                print("Mensaje vacio... No enviado")

                    elif nombre == "Descarte":
                            # Determinar la carta seleccionada (click sobre Carta_x) o usar la zona de arrastre (zona_cartas[2])
                            selected_card = None
                            for key, rect in cuadros_interactivos.items():
                                if key.startswith("Carta_") and rect.collidepoint(event.pos):
                                    selected_card = cartas_ref.get(key)
                                    break

                            if zona_cartas[2]:
                                # si hay cartas arrastradas al área de descarte, úsalas
                                selected_cards = list(zona_cartas[2])
                            elif selected_card is not None:
                                selected_cards = [selected_card]
                            else:
                                mensaje_temporal = "Selecciona una carta para descartar o arrástrala al área de Descarte."
                                mensaje_tiempo = time.time()
                                continue
                            # Llama al método del jugador para descartar (se espera que devuelva lista de Card o None)
                            cartas_descartadas = jugador_local.discardCard(selected_cards, round)

                            # Asegurarse que cartas_descartadas es una lista de Card (o False/None si fallo)
                            if not cartas_descartadas:
                                # No se descartó: devolver visuales si hacía falta
                                mensaje_temporal = "No se pudo descartar esa(s) carta(s)."
                                mensaje_tiempo = time.time()
                                cartas_ocultas.clear()
                                zona_cartas[2] = []
                                continue

                            # Validaciones de turno y regla "no descartar carta tomada este turno"
                            if not jugador_local.isHand:
                                mensaje_temporal = "No puedes descartar si no es tu turno."
                                mensaje_tiempo = time.time()
                                # devolver cartas a la mano si el método las removió
                                for c in selected_cards:
                                    if c not in jugador_local.playerHand:
                                        jugador_local.playerHand.append(c)
                                cartas_ocultas.clear()
                                zona_cartas[2] = []
                            elif not can_discard(jugador_local, cartas_descartadas):
                                mensaje_temporal = "No puedes descartar la carta que acabas de tomar."
                                mensaje_tiempo = time.time()
                                # devolver cartas a la mano si fue necesario
                                for c in cartas_descartadas:
                                    if c not in jugador_local.playerHand:
                                        jugador_local.playerHand.append(c)
                                cartas_ocultas.clear()
                                zona_cartas[2] = []
                                jugador_local.isHand = True
                            else:
                                # descarte válido: sincronizar vistas y limpiar bloqueo
                                visual_hand = compactar_visual_hand(visual_hand)
                                actualizar_indices_visual_hand(visual_hand)
                                visual_hand.clear()
                                last_taken_card = None
                                last_taken_player = None
                                jugador_local.isHand = False
                                for idx, carta in enumerate(jugador_local.playerHand):
                                    carta.id_visual = idx
                                    visual_hand.append(carta)
                                reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                                organizar_habilitado = True
                                jugador_local.cardDrawn = False
                                # Guarda la carta descartada en el mazo de descarte
                                for carta in cartas_descartadas:
                                    if len(cartas_descartadas) == 2 and hasattr(cartas_descartadas[1], "joker") and cartas_descartadas[1].joker:
                                        mazo_descarte.append(cartas_descartadas[1])
                                        mazo_descarte.append(cartas_descartadas[0])
                                        #break
                                    else:
                                        #mazo_descarte.append(carta)
                                        mazo_descarte = round.discards  #Luego de reiniciado el mazo, se duplicaron las cartas
                                zona_cartas[2] = []
                                #print(f"Mano del jugador: {[str(c) for c in jugador_local.playerHand]}")
                                #print(f"Prueba de isHand ANTES: {[p.isHand for p in players]}")
                                for idx, p in enumerate(players):
                                    if p.playerId == jugador_local.playerId:
                                        #print(f"indice... Jugador_local... {idx}")
                                        next_idx = (idx + 1) % len(players)
                                        #print(f"indice... proximo Jugador_local... {next_idx}")
                                        break
                                players[next_idx].isHand = True
                                #print(f"Prueba de isHand DESPUES: {[p.isHand for p in players]}")

                                
                                msgDescarte = {
                                    "type": "DESCARTE",
                                    "cartas_descartadas": cartas_descartadas,
                                    "playerHand": jugador_local.playerHand,
                                    "playerId": jugador_local.playerId,
                                    "mazo_descarte": mazo_descarte,#  El mazo se debe actualizar
                                    "players": players,   # La lista deberia Mantener el orden, pero con la MANO actualizada
                                    "deckForRound":deckForRound,
                                    "round": round
                                    }
                                if network_manager.is_host:
                                    network_manager.broadcast_message(msgDescarte)
                                else:
                                    network_manager.sendData(msgDescarte)
                    elif nombre == "Comprar carta":
                        jugador_local.playerBuy = True
                        # Aquí deberías tener la lógica de comprar carta
                        if jugador_local.playerTurn:
                            boughtCards = jugador_local.buyCard(round)
                            for carta in boughtCards:
                                mazo_descarte.remove(carta)
                                deckForRound.remove(carta)
                            jugador_local.playerTurn = False
                            jugador_local.playerBuy = False
                            cartas_ocultas.clear()
                            organizar_habilitado = True
                            visual_hand = compactar_visual_hand(visual_hand)
                            actualizar_indices_visual_hand(visual_hand)
                            visual_hand.clear()
                            for idx, carta in enumerate(jugador_local.playerHand):
                                carta.id_visual = idx
                                visual_hand.append(carta)

                            # Creo que no está la lógica para comprar la Carta... para comprar, No debe ser su turno... 
                            msgComprarC = {
                                "type": "COMPRAR_CARTA",
                                #?    "cartas_descartadas": cartas_descartadas,
                                    "playerHand": jugador_local.playerHand,
                                    "playerId": jugador_local.playerId,
                                    "mazo_descarte": mazo_descarte,#  El mazo se debe actualizar
                                    "round": round
                                }
                            if network_manager.is_host:
                                network_manager.broadcast_message(msgComprarC)
                            else:
                                network_manager.sendData(msgComprarC)
                            
            
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and dragging:
                if carta_arrastrada is not None:
                    mouse_x, mouse_y = event.pos
                    nueva_pos = None
                    for nombre, rect in cuadros_interactivos.items():
                        if nombre.startswith("Carta_") and rect.collidepoint(mouse_x, mouse_y):
                            idx = int(nombre.split("_")[1])
                            nueva_pos = idx
                            string_to_card(nombre)
                            break

                    trio_rect = cuadros_interactivos.get("Trio")
                    seguidilla_rect = cuadros_interactivos.get("Seguidilla")
                    descarte_rect = cuadros_interactivos.get("Descarte")
                    # --- LÓGICA NUEVA: Insertar carta en jugada hecha (inicio/final) ---
                    insertado_en_jugada = False
                    if not insertado_en_jugada:
                        for jugador, jugadas in rects_jugadas.items():
                            for idx_jugada, jugada in enumerate(jugadas):
                                # recupera el índice real de playMade (si lo guardamos)
                                play_index = jugada.get("play_index", idx_jugada)
                                if jugada["inicio"].collidepoint(mouse_x, mouse_y):
                                    print(f"Insertar carta al INICIO de la jugada {idx_jugada+1} (play_index {play_index}) de {jugador} ({jugada['tipo']})")
                                    target_player = next((p for p in players if p.playerName == jugador), None)
                                    if target_player:
                                        jugador_local.insertCard(
                                            targetPlayer=target_player,
                                            targetPlayIndex=idx_jugada,
                                            cardToInsert=string_to_card(carta_arrastrada),
                                            position="start"
                                        )
                                        ok = safe_insert_card(jugador_local, target_player, idx_jugada, carta_arrastrada, "start")
                                        ok = safe_insert_card(jugador_local, target_player, play_index, carta_arrastrada, "start")
                                        if not ok:
                                            mensaje_temporal = "Error al insertar: la jugada objetivo o la carta no son objetos válidos. Revisa consola."
                                            mensaje_tiempo = time.time()
                                        visual_hand.remove(carta_arrastrada)
                                        
                                    insertado_en_jugada = True
                                    print(f"Mano visual del jugador después de insertar: {[str(c) for c in visual_hand]}")
                                    print(f"Mano del jugador1 después de insertar: {[str(c) for c in jugador_local.playerHand]}")
                                    break
                                elif jugada["final"].collidepoint(mouse_x, mouse_y):
                                    print(f"Insertar carta al FINAL de la jugada {idx_jugada+1} (play_index {play_index}) de {jugador} ({jugada['tipo']})")
                                    target_player = next((p for p in players if p.playerName == jugador), None)
                                    
                                    if target_player:
                                        jugador_local.insertCard(
                                            targetPlayer=target_player,
                                            targetPlayIndex=idx_jugada,
                                            cardToInsert=string_to_card(carta_arrastrada),
                                            position="end"
                                        )
                                        ok = safe_insert_card(jugador_local, target_player, idx_jugada, carta_arrastrada, "start")
                                        ok = safe_insert_card(jugador_local, target_player, play_index, carta_arrastrada, "end")
                                        if ok:
                                            if carta_arrastrada in visual_hand:
                                                visual_hand.remove(carta_arrastrada)
                                            reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                                        else:
                                            mensaje_temporal = "Error al insertar: la jugada objetivo o la carta no son objetos válidos. Revisa consola."
                                            mensaje_tiempo = time.time()
                                    insertado_en_jugada = True
                                    print(f"Mano visual del jugador después de insertar: {[str(c) for c in visual_hand]}")
                                    print(f"Mano del jugador1 después de insertar: {[str(c) for c in jugador_local.playerHand]}")
                                    break
                                # --- NUEVO: Si se suelta sobre un Joker de la jugada ---
                                else:
                                    cartas_jugada = jugada["cartas"]
                                    bloque_nombre = None
                                    for idx, p in enumerate(players):
                                        if p.playerName == jugador:
                                            bloque_nombre = {
                                                0: "baj1", 1: "baj2", 2: "baj3", 3: "baj4", 4: "baj5", 5: "baj6", 6: "baj7"
                                            }.get(idx)
                                            break
                                    bloque_rect = boxes.get(bloque_nombre)
                                    if not bloque_rect:
                                        continue

                                    if bloque_nombre in ["baj2", "baj3", "baj6", "baj7"]:
                                        # Vertical (rotada)
                                        card_width = int(bloque_rect.width * 0.45)
                                        card_height = int(card_width / 0.68)
                                        solapamiento = int(card_height * 0.55) if len(cartas_jugada) > 1 else 0
                                        x = bloque_rect.x + (bloque_rect.width - card_height) // 2
                                        y = jugada["inicio"].y
                                        for i, carta in enumerate(cartas_jugada):
                                            card_rect = pygame.Rect(x, y + i * solapamiento, card_height, card_width)
                                            if hasattr(carta, "joker") and carta.joker:
                                                if card_rect.collidepoint(mouse_x, mouse_y):
                                                    # Llama a insertCard para sustituir el Joker
                                                    target_player = next((p for p in players if p.playerName == jugador), None)
                                                    
                                                    if target_player:
                                                        jugador_local.insertCard(
                                                            targetPlayer=target_player,
                                                            targetPlayIndex=idx_jugada,
                                                            cardToInsert=string_to_card(carta_arrastrada),
                                                            position=None
                                                        )
                                                        ok = safe_insert_card(jugador_local, target_player, idx_jugada, carta_arrastrada, "start")
                                                        if not ok:
                                                            mensaje_temporal = "Error al insertar: la jugada objetivo o la carta no son objetos válidos. Revisa consola."
                                                            mensaje_tiempo = time.time()
                                                        ok = safe_insert_card(jugador_local, target_player, idx_jugada, carta_arrastrada, "start")
                                                    insertado_en_jugada = True
                                                    print(f"Mano visual del jugador después de insertar: {[str(c) for c in visual_hand]}")
                                                    print(f"Mano del jugador1 después de insertar: {[str(c) for c in jugador_local.playerHand]}")
                                                    break
                                    else:
                                        # Horizontal
                                        card_height = bloque_rect.height - 8
                                        card_width = int(card_height * 0.68)
                                        solapamiento = int(card_width * 0.65) if len(cartas_jugada) > 1 else 0
                                        x = jugada["inicio"].x
                                        y = bloque_rect.y + (bloque_rect.height - card_height) // 2 - 18
                                        for i, carta in enumerate(cartas_jugada):
                                            card_rect = pygame.Rect(x + i * solapamiento, y, card_width, card_height)
                                            if hasattr(carta, "joker") and carta.joker:
                                                if card_rect.collidepoint(mouse_x, mouse_y):
                                                    # Llama a insertCard para sustituir el Joker
                                                    target_player = next((p for p in players if p.playerName == jugador), None)
                                                    
                                                    if target_player:
                                                        jugador_local.insertCard(
                                                            targetPlayer=target_player,
                                                            targetPlayIndex=idx_jugada,
                                                            cardToInsert=carta_arrastrada,
                                                            position=None  # Indica sustitución de Joker
                                                        )
                                                        ok = safe_insert_card(jugador_local, target_player, idx_jugada, carta_arrastrada, None)
                                                        if not ok:
                                                            mensaje_temporal = "Error al insertar: la jugada objetivo o la carta no son objetos válidos. Revisa consola."
                                                            mensaje_tiempo = time.time()
                                                    insertado_en_jugada = True
                                                    print(f"Mano visual del jugador después de insertar: {[str(c) for c in visual_hand]}")
                                                    print(f"Mano del jugador1 después de insertar: {[str(c) for c in jugador_local.playerHand]}")
                                                    break
                                if insertado_en_jugada:
                                    break
                if not insertado_en_jugada:
                    if trio_rect and trio_rect.collidepoint(mouse_x, mouse_y):
                        zona_cartas[1].append(carta_arrastrada)
                        if carta_arrastrada in visual_hand:
                            idx_carta = visual_hand.index(carta_arrastrada)
                            cartas_ocultas.add(idx_carta)
                        organizar_habilitado = False

                    elif seguidilla_rect and seguidilla_rect.collidepoint(mouse_x, mouse_y):
                        zona_cartas[0].append(carta_arrastrada)
                        if carta_arrastrada in visual_hand:
                            idx_carta = visual_hand.index(carta_arrastrada)
                            cartas_ocultas.add(idx_carta)
                        organizar_habilitado = False

                    elif descarte_rect and descarte_rect.collidepoint(mouse_x, mouse_y):
                        zona_cartas[2].append(carta_arrastrada)
                        if carta_arrastrada in visual_hand:
                            idx_carta = visual_hand.index(carta_arrastrada)
                            cartas_ocultas.add(idx_carta)
                        organizar_habilitado = False

                    # Solo permite reorganizar si organizar_habilitado está en True
                    elif nueva_pos is not None and organizar_habilitado:
                        if carta_arrastrada in visual_hand:
                            visual_hand.remove(carta_arrastrada)
                        if mouse_x < cuadros_interactivos[f"Carta_{nueva_pos}"].centerx:
                            visual_hand.insert(nueva_pos, carta_arrastrada)
                        else:
                            visual_hand.insert(nueva_pos + 1, carta_arrastrada)
                    elif nueva_pos is not None and not organizar_habilitado:
                        mensaje_temporal = "No puedes organizar una carta mientras ejecutas una jugada."
                        mensaje_tiempo = time.time()

                dragging = False
                carta_arrastrada = None
                drag_rect = None
            elif event.type == pygame.MOUSEMOTION and dragging:
                pass  # El dibujo se maneja abajo
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Click derecho
                for zona in zona_cartas:
                    for carta in zona:
                        if carta not in visual_hand:
                            visual_hand.append(carta)
                zona_cartas = [[], [], []]
                cartas_ocultas.clear()
                organizar_habilitado = True  # Vuelve a habilitar organización
        # Fin evento de pygame...

        process_received_messagesUi2()  
        #------ Hasta aqui el bucle de event de PYGAME ------------

        # Sincroniza visual_hand con el backend si hay nuevas cartas
        if len(visual_hand) != len(jugador_local.playerHand) or any(c not in visual_hand for c in jugador_local.playerHand):
            # Añade nuevas cartas al final de visual_hand
            for c in jugador_local.playerHand:
                if c not in visual_hand and c not in cartas_apartadas:
                    visual_hand.append(c)
            # Elimina cartas que ya no están
            visual_hand = [c for c in visual_hand if c in jugador_local.playerHand and c not in cartas_apartadas]

        # Dibujar fondo
        screen.blit(fondo_img, (0, 0))

        # Cálculo de tamaños relativos
        bajada_h = int(HEIGHT * bajada_h_pct)
        bajada_w = int(WIDTH * bajada_w_pct)
        jug_w = int(WIDTH * jug_w_pct)
        jug_h = int(HEIGHT * jug_h_pct)
        
        # --- Inferior (Jugador 1) ---
        # Hacemos J1 más ancho (horizontalmente) y más alto (verticalmente)
        extra_ancho_j1 = int(WIDTH * 0.18)  # Más ancho horizontalmente
        extra_alto_j1 = int(HEIGHT * 0.06)  # Más alto verticalmente
        jug1 = pygame.Rect(
            jug_w + bajada_w - extra_ancho_j1 // 2,
            HEIGHT - jug_h - extra_alto_j1 // 2,
            WIDTH - 2 * (jug_w + bajada_w) + extra_ancho_j1,
            jug_h + extra_alto_j1
        )
        boxes["jug1"] = jug1
        # draw_transparent_rect(screen, CAJA_JUG, jug1)
        # draw_label(jug1, "J1")
        # cuadros_interactivos["J1"] = jug1
        #bajada_h = int(HEIGHT * (bajada_h_pct + 0.05))  # ahora será 17.5% de la altura total
        # B1 igual de ancho que antes, para no chocar con las cajas laterales
        baj1 = pygame.Rect(
            jug_w + bajada_w,
            HEIGHT - jug_h - bajada_h,
            WIDTH - 2 * (jug_w + bajada_w),
            bajada_h
        )
        boxes["baj1"] = baj1
        # draw_transparent_rect(screen, CAJA_BAJ, baj1)
        # draw_label(baj1, "B1")
        cuadros_interactivos["B1"] = baj1

        # --- Izquierda (Jugadores 2 y 3) --- (INVERTIDO: J2 más cerca del centro, J3 arriba)
        lado_total_h = HEIGHT - jug_h - bajada_h
        lado_h = lado_total_h // 2

        # J3 ARRIBA
        jug3 = pygame.Rect(0, jug_h, jug_w, lado_h)
        boxes["jug3"] = jug3
        # draw_transparent_rect(screen, CAJA_JUG, jug3)
        # draw_label(jug3, "J3")
        cuadros_interactivos["J3"] = jug3

        baj3 = pygame.Rect(jug_w, jug_h, bajada_w, lado_h)
        boxes["baj3"] = baj3
        # draw_transparent_rect(screen, CAJA_BAJ, baj3)
        # draw_label(baj3, "B3")
        cuadros_interactivos["B3"] = baj3

        # J2 ABAJO (más cerca del centro)
        jug2 = pygame.Rect(0, jug_h + lado_h, jug_w, lado_h)
        boxes["jug2"] = jug2
        # draw_transparent_rect(screen, CAJA_JUG, jug2)
        # draw_label(jug2, "J2")
        cuadros_interactivos["J2"] = jug2

        baj2 = pygame.Rect(jug_w, jug_h + lado_h, bajada_w, lado_h)
        boxes["baj2"] = baj2
        # draw_transparent_rect(screen, CAJA_BAJ, baj2)
        # draw_label(baj2, "B2")
        cuadros_interactivos["B2"] = baj2

        # --- Derecha (Jugadores 6 y 7) ---
        jug6 = pygame.Rect(WIDTH - jug_w, jug_h, jug_w, lado_h)
        boxes["jug6"] = jug6
        # draw_transparent_rect(screen, CAJA_JUG, jug6)
        # draw_label(jug6, "J6")
        cuadros_interactivos["B6"] = jug6

        baj6 = pygame.Rect(WIDTH - jug_w - bajada_w, jug_h, bajada_w, lado_h)
        boxes["baj6"] = baj6
        # draw_transparent_rect(screen, CAJA_BAJ, baj6)
        # draw_label(baj6, "B6")
        cuadros_interactivos["B6"] = baj6

        jug7 = pygame.Rect(WIDTH - jug_w, jug_h + lado_h, jug_w, lado_h)
        boxes["jug7"] = jug7
        # draw_transparent_rect(screen, CAJA_JUG, jug7)
        # draw_label(jug7, "J7")
        cuadros_interactivos["B7"] = jug7

        baj7 = pygame.Rect(WIDTH - jug_w - bajada_w, jug_h + lado_h, bajada_w, lado_h)
        boxes["baj7"] = baj7
        # draw_transparent_rect(screen, CAJA_BAJ, baj7)
        # draw_label(baj7, "B7")
        cuadros_interactivos["B7"] = baj7

        # --- Arriba (Jugadores 4 y 5) ---
        arriba_total_w = WIDTH - 2 * (jug_w + bajada_w)
        arriba_w = arriba_total_w // 2

        jug4 = pygame.Rect(jug_w + bajada_w, 0, arriba_w, jug_h)
        boxes["jug4"] = jug4
        # draw_transparent_rect(screen, CAJA_JUG, jug4)
        # draw_label(jug4, "J4")
        cuadros_interactivos["J4"] = jug4

        baj4 = pygame.Rect(jug_w + bajada_w, jug_h, arriba_w, bajada_h)
        boxes["baj4"] = baj4
        # draw_transparent_rect(screen, CAJA_BAJ, baj4)
        # draw_label(baj4, "B4")
        cuadros_interactivos["B4"] = baj4

        jug5 = pygame.Rect(jug_w + bajada_w + arriba_w, 0, arriba_w, jug_h)
        boxes["jug5"] = jug5
        # draw_transparent_rect(screen, CAJA_JUG, jug5)
        # draw_label(jug5, "J5")
        cuadros_interactivos["J5"] = jug5

        baj5 = pygame.Rect(jug_w + bajada_w + arriba_w, jug_h, arriba_w, bajada_h)
        boxes["baj5"] = baj5
        # draw_transparent_rect(screen, CAJA_BAJ, baj5)
        # draw_label(baj5, "B5")
        cuadros_interactivos["B5"] = baj5

        # --- Área central (mesa) ---
        mesa_x = jug_w + bajada_w
        mesa_y = jug_h + bajada_h
        mesa_w = WIDTH - 2 * (jug_w + bajada_w)
        mesa_h = HEIGHT - 2 * (jug_h + bajada_h)
        mesa = pygame.Rect(mesa_x, mesa_y, mesa_w, mesa_h)
        boxes["mesa"] = mesa
        # draw_transparent_rect(screen, CENTRAL, mesa)
        # draw_label(mesa, "Mesa")  # Quitado para que no aparezca la palabra "Mesa"

        # --- RECUADROS EN LA MESA (UNO AL LADO DEL OTRO) ---
        # Calcula las posiciones de los cuadros centrales
        margin = 10
        cuadro_w_fino = int(mesa_w * 0.16)
        cuadro_h = int(mesa_h * 0.85)
        cuadro_h_carta = int(mesa_h * 0.32)
        cuadro_w_carta = 120
        cuadro_h_carta = 188
        total_width = cuadro_w_fino * 3 + cuadro_w_carta * 2 + margin * 4
        start_x = mesa_x + (mesa_w - total_width) // 2
        cuadro_y = mesa_y + (mesa_h - cuadro_h) // 2

        # Calcula las posiciones X de cada cuadro central
        x_trio = start_x
        x_seguidilla = x_trio + cuadro_w_fino + margin
        x_descarte = x_seguidilla + cuadro_w_fino + margin
        x_tomar_carta = x_descarte + cuadro_w_fino + margin
        x_tomar_descarte = x_tomar_carta + cuadro_w_carta + margin

        # Altura de los botones
        boton_h = int(cuadro_h * 0.22)
        boton_w_fino = cuadro_w_fino
        boton_w_carta = cuadro_w_carta

        # Y de los botones (justo encima de los cuadros pequeños)
        boton_y = cuadro_y - boton_h + (cuadro_h - cuadro_h_carta) // 2 - 10  # Ajusta -10 si quieres más separación

        # --- Botón "Bajarse" ---
        bajarse_x = x_trio + cuadro_w_fino + margin // 2 - boton_w_fino // 2
        bajarse_rect = pygame.Rect(
            bajarse_x,
            boton_y,
            boton_w_fino,
            boton_h
        )
        # --- Botón "Bajarse" ---
        bajarse_visible = True  # Controla la visibilidad del botón "Bajarse"
        if bajarse_visible:
            bajarse_img_path = os.path.join(ASSETS_PATH, "bajarse.png")
            if os.path.exists(bajarse_img_path):
                bajarse_img = pygame.image.load(bajarse_img_path).convert_alpha()
                img = pygame.transform.smoothscale(bajarse_img, (boton_w_fino, boton_h))
                screen.blit(img, bajarse_rect.topleft)
            else:
                draw_transparent_rect(screen, (180, 180, 220, 110), bajarse_rect, border=1)
                draw_label(bajarse_rect, "Bajarse")
            cuadros_interactivos["Bajarse"] = bajarse_rect
        else:
            cuadros_interactivos.pop("Bajarse", None)

        # --- Botón "Descartar" ---
        descartar_rect = pygame.Rect(
            x_descarte,
            boton_y,
            boton_w_fino,
            boton_h
        )
        # --- Botón "Descartar" ---
        descartar_img_path = os.path.join(ASSETS_PATH, "descartar.png")
        if os.path.exists(descartar_img_path):
            descartar_img = pygame.image.load(descartar_img_path).convert_alpha()
            img = pygame.transform.smoothscale(descartar_img, (boton_w_fino, boton_h))
            screen.blit(img, descartar_rect.topleft)
        else:
            draw_transparent_rect(screen, (180, 180, 220, 110), descartar_rect, border=1)
            draw_label(descartar_rect, "Descartar")
        cuadros_interactivos["Descartar"] = descartar_rect

        # --- Botón "Comprar carta" ---
        comprar_rect = pygame.Rect(
            (x_tomar_descarte + x_tomar_carta + cuadro_w_carta) // 2 - boton_w_carta // 2,
            boton_y,
            boton_w_carta,
            boton_h
        )
        comprar_img_path = os.path.join(ASSETS_PATH, "comprar_carta.png")
        if os.path.exists(comprar_img_path):
            comprar_img = pygame.image.load(comprar_img_path).convert_alpha()
            img = pygame.transform.smoothscale(comprar_img, (boton_w_carta, boton_h))
            screen.blit(img, comprar_rect.topleft)
        else:
            draw_transparent_rect(screen, (180, 180, 220, 110), comprar_rect, border=1)
            draw_label(comprar_rect, "Comprar carta")
        cuadros_interactivos["Comprar carta"] = comprar_rect

        # --- Cuadros: Trio, Seguidilla, Descarte, Tomar descarte, Tomar carta (todos alineados y centrados verticalmente) ---
        textos = ["Trio", "Seguidilla", "Descarte", "Tomar descarte", "Tomar carta"]
        x = start_x
        for i, texto in enumerate(textos):
            if i < 3:
                w = cuadro_w_carta
                h = cuadro_h
            else:
                w = cuadro_w_carta
                h = cuadro_h_carta
            # Centrado vertical: calcula y ajusta el y para los cuadros pequeños
            if i < 3:
                rect_y = cuadro_y
            else:
                rect_y = cuadro_y + (cuadro_h - cuadro_h_carta) // 2
            rect = pygame.Rect(x, rect_y, w, h)
            if texto == "Trio":
                trio_img_path = os.path.join(ASSETS_PATH, "trio.png")
                if os.path.exists(trio_img_path):
                    trio_img = pygame.image.load(trio_img_path).convert_alpha()
                    img = pygame.transform.smoothscale(trio_img, (cuadro_w_carta - 8, cuadro_h_carta - 8))
                    img_rect = img.get_rect(center=rect.center)
                    screen.blit(img, img_rect.topleft)
            elif texto == "Seguidilla":
                seguidilla_img_path = os.path.join(ASSETS_PATH, "seguidilla.png")
                if os.path.exists(seguidilla_img_path):
                    seguidilla_img = pygame.image.load(seguidilla_img_path).convert_alpha()
                    img = pygame.transform.smoothscale(seguidilla_img, (cuadro_w_carta - 8, cuadro_h_carta - 8))
                    img_rect = img.get_rect(center=rect.center)
                    screen.blit(img, img_rect.topleft)
            elif texto == "Descarte":
                descarte_img_path = os.path.join(ASSETS_PATH, "descarte.png")
                if os.path.exists(descarte_img_path):
                    descarte_img = pygame.image.load(descarte_img_path).convert_alpha()
                    img = pygame.transform.smoothscale(descarte_img, (cuadro_w_carta - 8, cuadro_h_carta - 8))
                    img_rect = img.get_rect(center=rect.center)
                    screen.blit(img, img_rect.topleft)
            elif texto == "Tomar carta":
                back_img_path = os.path.join(ASSETS_PATH, "cartas", "PT2.png")
                if os.path.exists(back_img_path):
                    back_img = pygame.image.load(back_img_path).convert_alpha()
                    img = pygame.transform.smoothscale(back_img, (w - 8, h - 8))
                    img_rect = img.get_rect(center=rect.center)
                    screen.blit(img, img_rect.topleft)
            elif texto == "Tomar descarte":
                plantilla_img_path = os.path.join(ASSETS_PATH, "plantilla.png")
                if os.path.exists(plantilla_img_path):
                    plantilla_img = pygame.image.load(plantilla_img_path).convert_alpha()
                    img = pygame.transform.smoothscale(plantilla_img, (w - 8, h - 8))
                    img_rect = img.get_rect(center=rect.center)
                    screen.blit(img, img_rect.topleft)
            cuadros_interactivos[texto] = rect
            x += w + margin

        # --- Caja superior izquierda: Ronda y Turno (pegada arriba a la izquierda) ---
        ronda_turno_x = 0
        ronda_turno_y = 0
        ronda_turno_w = int(jug_w * 1.5)
        ronda_turno_h = jug_h

        ronda_turno_rect = pygame.Rect(ronda_turno_x, ronda_turno_y, ronda_turno_w, ronda_turno_h)
        # draw_transparent_rect(screen, (200, 200, 200, 80), ronda_turno_rect, border=1)
        cuadros_interactivos["Ronda/Turno"] = ronda_turno_rect

        ronda_rect = pygame.Rect(ronda_turno_x, ronda_turno_y, ronda_turno_w, ronda_turno_h // 2)
        # draw_transparent_rect(screen, (180, 180, 180, 80), ronda_rect, border=1)
        # draw_label(ronda_rect, "Ronda")
        cuadros_interactivos["Ronda"] = ronda_rect

        turno_rect = pygame.Rect(ronda_turno_x, ronda_turno_y + ronda_turno_h // 2, ronda_turno_w, ronda_turno_h // 2)
        # draw_transparent_rect(screen, (180, 180, 180, 80), turno_rect, border=1)
        # draw_label(turno_rect, "Turno")
        cuadros_interactivos["Turno"] = turno_rect

        # --- Caja superior derecha: Solo Menú (centrado en la esquina superior derecha, sin cuadro de sonido) ---
        menu_w = int(jug_w * 1.1)
        menu_h = int(jug_h * 0.5)
        margin_menu = 10

        menu_x = WIDTH - menu_w - margin_menu
        menu_y = margin_menu

        menu_rect = pygame.Rect(menu_x, menu_y, menu_w, menu_h)

        menu_img_path = os.path.join(ASSETS_PATH, "menu.png")
        if os.path.exists(menu_img_path):
            menu_img = pygame.image.load(menu_img_path).convert_alpha()
            img = pygame.transform.smoothscale(menu_img, (menu_rect.width, menu_rect.height))
            screen.blit(img, menu_rect.topleft)
        cuadros_interactivos["Menú"] = menu_rect

        # Elimina o comenta cualquier bloque relacionado con sonido_rect, draw_label(sonido_rect, "Sonido") y draw_transparent_rect para sonido.

        # --- Caja inferior izquierda: Tablero y posiciones (más pequeña y más abajo) ---
        tablero_w = ronda_turno_w
        tablero_h = int(jug_h * 0.6)
        tablero_x = 0
        tablero_y = HEIGHT - tablero_h
        tablero_rect = pygame.Rect(tablero_x, tablero_y, tablero_w, tablero_h)
        # draw_transparent_rect(screen, (200, 200, 200, 80), tablero_rect, border=1)
        # draw_label(tablero_rect, "Tablero y posiciones")
        cuadros_interactivos["Tablero y posiciones"] = tablero_rect

        # --- Botón "Tablero y posiciones" ---
        tablero_img_path = os.path.join(ASSETS_PATH, "tablero_de_posiciones.png")
        if os.path.exists(tablero_img_path):
            tablero_img = pygame.image.load(tablero_img_path).convert_alpha()
            img = pygame.transform.smoothscale(tablero_img, (tablero_rect.width, tablero_rect.height))
            screen.blit(img, tablero_rect.topleft)
        cuadros_interactivos["Tablero y posiciones"] = tablero_rect

        # --- Mostrar cartas del jugador 1 en J1 (interactivas y auto-organizadas) ---
        # Usar visual_hand en vez de jugador_local.playerHand
        class VisualPlayer:
            pass
        visual_player = VisualPlayer()
        visual_player.playerHand = visual_hand
        draw_player_hand(visual_player, jug1, cuadros_interactivos, cartas_ref, ocultas=cartas_ocultas)

        # Dibuja la carta arrastrada como copia transparente, si corresponde (arrastre visual independiente)
        if dragging and carta_arrastrada is not None:
            card_height = jug1.height - 6
            card_width = int(card_height * 0.68)
            mouse_x, mouse_y = pygame.mouse.get_pos()
            img = get_card_image(carta_arrastrada).copy()
            img = pygame.transform.smoothscale(img, (card_width, card_height))
            img.set_alpha(120)  # Transparente
            x = mouse_x - drag_offset_x
            y = mouse_y - card_height // 2
            screen.blit(img, (x, y))

        # Lado izquierdo
        #from test3 import players

        # Ejemplo para 2 a 7 jugadores (ajusta según tu layout)
        jugadores_laterales = []
        jugadores_superiores = []

        if len(players) >= 2:
            jugadores_laterales.append((players[1], jug2))
        if len(players) >= 3:
            jugadores_laterales.append((players[2], jug3))
        if len(players) >= 4:
            jugadores_superiores.append((players[3], jug4))
        if len(players) >= 5:
            jugadores_superiores.append((players[4], jug5))
        if len(players) >= 6:
            jugadores_laterales.append((players[5], jug6))
        if len(players) >= 7:
            jugadores_laterales.append((players[6], jug7))
        

        # Dibuja solo los jugadores activos en los recuadros correspondientes
        for jugador, recuadro in jugadores_laterales:
            draw_horizontal_rain_hand_rotated(jugador, recuadro)

        for jugador, recuadro in jugadores_superiores:
            draw_horizontal_pt_hand(jugador, recuadro)

        # Dibuja cartas en Seguidilla (zona_cartas[0])
        if zona_cartas[0]:
            rect = cuadros_interactivos.get("Seguidilla")
            if rect:
                n = len(zona_cartas[0])
                card_width = rect.width - 8
                card_height = int(card_width / 0.68)
                # Aumenta el alto del cuadro en la definición de cuadro_h (ver más abajo)
                if n > 1:
                    solapamiento = (rect.height - card_height) // (n - 1)
                    if solapamiento > card_height * 0.7:
                        solapamiento = int(card_height * 0.7)
                else:
                    solapamiento = 0
                x = rect.x + (rect.width - card_width) // 2
                start_y = rect.y + 70
                # Dibuja de atrás hacia adelante (la última encima)
                for i in range(n):
                    idx = i  # Si quieres la última encima, usa el orden normal
                    card = zona_cartas[0][idx]
                    img = get_card_image(card)
                    img = pygame.transform.smoothscale(img, (card_width, card_height))
                    card_rect = pygame.Rect(x, start_y + i * solapamiento, card_width, card_height)
                    screen.blit(img, card_rect.topleft)

        # Dibuja cartas en Trio (zona_cartas[1])
        if zona_cartas[1]:
            rect = cuadros_interactivos.get("Trio")
            if rect:
                n = len(zona_cartas[1])
                card_width = rect.width - 8
                card_height = int(card_width / 0.68)
                if n > 1:
                    max_height = rect.height - 8
                    solapamiento = (max_height - card_height) // (n - 1)
                    if solapamiento > card_height * 0.7:
                        solapamiento = int(card_height * 0.7)
                else:
                    solapamiento = 0
                x = rect.x + (rect.width - card_width) // 2
                start_y = rect.y + 70
                for i, card in enumerate(zona_cartas[1]):
                    img = get_card_image(card)
                    img = pygame.transform.smoothscale(img, (card_width, card_height))
                    card_rect = pygame.Rect(x, start_y + i * solapamiento, card_width, card_height)
                    screen.blit(img, card_rect.topleft)

        # Dibuja cartas en Descarte (zona_cartas[2])
        # Deben haber como mucho 2 cartas
        if zona_cartas[2]:
            rect = cuadros_interactivos.get("Descarte")
            if rect:
                card = zona_cartas[2][-1]  # Solo la última carta
                card_width = rect.width - 8
                card_height = int(card_width / 0.68)
                x = rect.x + (rect.width - card_width) // 2
                y = rect.y + (rect.height - card_height) // 2
                img = get_card_image(card)
                img = pygame.transform.smoothscale(img, (card_width, card_height))
                card_rect = pygame.Rect(x, y, card_width, card_height)
                screen.blit(img, card_rect.topleft)

        # Dibuja la última carta descartada en el cuadro "Tomar descarte"
        # Dibuja el fondo del cuadro "Tomar descarte"
        rect = cuadros_interactivos.get("Tomar descarte")
        if rect:
            plantilla_img_path = os.path.join(ASSETS_PATH, "plantilla.png")
            if os.path.exists(plantilla_img_path):
                plantilla_img = pygame.image.load(plantilla_img_path).convert_alpha()
                img = pygame.transform.smoothscale(plantilla_img, (rect.width - 8, rect.height - 8))
                img_rect = img.get_rect(center=rect.center)
                screen.blit(img, img_rect.topleft)

            # Dibuja la última carta descartada encima
            if mazo_descarte:
                card = mazo_descarte[-1]
                card_width = rect.width - 8
                card_height = int(card_width / 0.68)
                x = rect.x + (rect.width - card_width) // 2
                y = rect.y + (rect.height - card_height) // 2
                img = get_card_image(card)
                img = pygame.transform.smoothscale(img, (card_width, card_height))
                card_rect = pygame.Rect(x, y, card_width, card_height)
                screen.blit(img, card_rect.topleft)

        # for idx, nombre in enumerate(["Seguidilla", "Trio", "Descarte"]):
        #     if zona_cartas[idx]:
        #         rect = cuadros_interactivos.get(nombre)
        #         if rect:
        #             n = len(zona_cartas[idx])
        #             card_width = rect.width - 8
        #             card_height = int(card_width / 0.68)
        #             if n > 1:
        #                 solapamiento = (rect.height - card_height) // (n - 1)
        #                 if solapamiento > card_height * 0.7:
        #                     solapamiento = int(card_height * 0.7)
        #             else:
        #                 solapamiento = 0
        #             x = rect.x + (rect.width - card_width) // 2
        #             start_y = rect.y
        #             for i in range(n):
        #                 card = zona_cartas[idx][i]
        #                 img = get_card_image(card)
        #                 img = pygame.transform.smoothscale(img, (card_width, card_height))
        #                 card_rect = pygame.Rect(x, start_y + i * solapamiento, card_width, card_height)
        #                 screen.blit(img, card_rect.topleft)

        # Al final del while running, antes de pygame.display.flip(), agrega:
        if mensaje_temporal and time.time() - mensaje_tiempo < 5:
            font_videojuego = pygame.font.SysFont("PressStart2P", 28)  # O el nombre de tu fuente de videojuego
            texto = font_videojuego.render(mensaje_temporal, True, (255, 255, 0))
            rect = texto.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 180))
            screen.blit(texto, rect)
        elif mensaje_temporal and time.time() - mensaje_tiempo >= 5:
            mensaje_temporal = ""

        # --- Botón "Ronda" ---
        ronda_img_path = os.path.join(ASSETS_PATH, "ronda.png")
        if os.path.exists(ronda_img_path):
            ronda_img = pygame.image.load(ronda_img_path).convert_alpha()
            img = pygame.transform.smoothscale(ronda_img, (ronda_rect.width, ronda_rect.height))
            screen.blit(img, ronda_rect.topleft)
        cuadros_interactivos["Ronda"] = ronda_rect

        # --- Botón "Turno" ---
        turno_img_path = os.path.join(ASSETS_PATH, "turno.png")
        if os.path.exists(turno_img_path):
            turno_img = pygame.image.load(turno_img_path).convert_alpha()
            img = pygame.transform.smoothscale(turno_img, (turno_rect.width, turno_rect.height))
            screen.blit(img, turno_rect.topleft)
        cuadros_interactivos["Turno"] = turno_rect

        # --- Botón "Menú" ---
        menu_img_path = os.path.join(ASSETS_PATH, "menu.png")
        if os.path.exists(menu_img_path):
            menu_img = pygame.image.load(menu_img_path).convert_alpha()
            img = pygame.transform.smoothscale(menu_img, (menu_rect.width, menu_rect.height))
            screen.blit(img, menu_rect.topleft)
        cuadros_interactivos["Menú"] = menu_rect

        # Mostrar jugadas bajadas en los bloques de bajada de todos los jugadores
        from Card import Card

        # Ejemplo: crea jugadas de prueba si no existen
        #for idx in range(len(players)):
            #if not hasattr(players[idx], "jugadas_bajadas"):
                # Crea jugadas de ejemplo para cada jugador
                #players[idx].jugadas_bajadas = [
                    #[Card("A", "♠"), Card("2", "♠"), Card("3", "♠")],
                    #[Card("K", "♥"), Card("K", "♦"), Card("K", "♣")]
                #]

        # Diccionario para asociar cada bloque de bajada con el jugador correspondiente
        bloques_bajada = {
            0: "baj1",
            1: "baj2",
            2: "baj3",
            3: "baj4",
            4: "baj5",
            5: "baj6",
            6: "baj7"
        }
        # Diccionario para guardar referencias de rectángulos de jugadas
        rects_jugadas = {}

        for idx, jugador in enumerate(players):
            bloque_nombre = bloques_bajada.get(idx)
            if not bloque_nombre:
                continue
            bloque_rect = boxes.get(bloque_nombre)
            if not bloque_rect:
                continue
            # Usa las jugadas reales del jugador
            if hasattr(jugador, "playMade") and jugador.playMade:
                rects_jugadas[jugador.playerName] = []
                # --- Laterales: cartas pequeñas, verticales y rotadas ---
                if bloque_nombre in ["baj2", "baj3", "baj6", "baj7"]:
                    margen_jugada = 1 
                    card_width = int(bloque_rect.width * 0.45)
                    card_height = int(card_width / 0.68)
                    x = bloque_rect.x + (bloque_rect.width - card_height) // 2
                    y_actual = bloque_rect.y + 6
                    # Aquí usamos enumerate para conocer el índice real en playMade
                    #for play_index, jugada in enumerate(jugador.playMade):
                        #print(f"jugada: {[str(c) for c in jugada]}")
                    # preferir jugadas_bajadas (objetos Card) si existen, sino usar playMade
                    plays_source = getattr(jugador, "jugadas_bajadas", None) or getattr(jugador, "playMade", [])
                    for play_index, jugada in enumerate(plays_source):
                        string_to_card(jugada[0])
                        string_to_card(jugada[1])
                        # Si la entrada es una lista de strings (p.ej. ['trio','straight']), intenta resolver
                        if isinstance(jugada, list) and jugada and isinstance(jugada[0], str):
                            string_to_card(jugada[0])
                            resolved = None
                            if hasattr(jugador, "jugadas_bajadas") and len(jugador.jugadas_bajadas) > play_index:
                                resolved = jugador.jugadas_bajadas[play_index]
                            if resolved is None:
                                print(f"Advertencia: jugada en play_index {play_index} parece contener strings y no hay jugadas_bajadas para resolverla. Saltando.")
                                continue
                            jugada = resolved
                         # Si la jugada es un dict, extrae trío y seguidilla
                        jugadas_a_dibujar = []
                        if isinstance(jugada, dict):
                             if "trio" in jugada and jugada["trio"]:
                                 jugadas_a_dibujar.append(jugada["trio"])
                             if "straight" in jugada and jugada["straight"]:
                                 jugadas_a_dibujar.append(jugada["straight"])
                        else:
                             jugadas_a_dibujar = [jugada]
                        for cartas_jugada in jugadas_a_dibujar:
                            string_to_card([cartas_jugada])
                            #print(f"jugada (DEBE SER OBJETOS DE CARTAS): {[str(c) for c in cartas_jugada]}")
                            n = len(cartas_jugada)
                            if n == 0:
                                continue
                            solapamiento = int(card_height * 0.20) if n > 1 else 0
                            # Guarda la posición inicial y final de la jugada
                            inicio_rect = pygame.Rect(x, y_actual, card_height, card_width)
                            final_rect = pygame.Rect(x, y_actual + (n-1)*solapamiento, card_height, card_width)
                            # Guardamos también el índice original en playMade (play_index)
                            rects_jugadas[jugador.playerName].append({
                                "inicio": inicio_rect,
                                "final": final_rect,
                                "tipo": "trio" if n == 3 else "straight",
                                "play_index": play_index,
                                "cartas": cartas_jugada
                            })
                            # Dibuja la jugada
                            for i, carta in enumerate(cartas_jugada):
                                string_to_card([cartas_jugada])
                                img = get_card_image(carta)
                                img = pygame.transform.smoothscale(img, (card_width, card_height))
                                img = pygame.transform.rotate(img, 90)
                                card_rect = pygame.Rect(x, y_actual + i * solapamiento, card_height, card_width)
                                if card_rect.bottom <= bloque_rect.bottom:
                                    screen.blit(img, card_rect.topleft)
                            # Mueve y_actual para la siguiente jugada
                            y_actual += n * solapamiento + card_width + margen_jugada
                else:
                    # El resto de bloques como antes
                    card_height = bloque_rect.height - 8
                    card_width = int(card_height * 0.68)
                    margen_jugada = 1  
                    x_actual = bloque_rect.x + 6
                    y = bloque_rect.y + (bloque_rect.height - card_height) // 2 - 18
                    # Usamos enumerate también aquí para mantener play_index correcto
                    plays_source = getattr(jugador, "jugadas_bajadas", None) or getattr(jugador, "playMade", [])
                    for play_index, jugada in enumerate(plays_source):
                        if isinstance(jugada, list) and jugada and isinstance(jugada[0], str):
                            resolved = None
                            if hasattr(jugador, "jugadas_bajadas") and len(jugador.jugadas_bajadas) > play_index:
                                resolved = jugador.jugadas_bajadas[play_index]
                            if resolved is None:
                                print(f"Advertencia: jugada en play_index {play_index} parece contener strings y no hay jugadas_bajadas para resolverla. Saltando.")
                                continue
                            jugada = resolved
                        jugadas_a_dibujar = []
                        if isinstance(jugada, dict):
                            if "trio" in jugada and jugada["trio"]:
                                jugadas_a_dibujar.append(jugada["trio"])
                            if "straight" in jugada and jugada["straight"]:
                                jugadas_a_dibujar.append(jugada["straight"])
                        else:
                            jugadas_a_dibujar = [jugada]
                        for cartas_jugada in jugadas_a_dibujar:
                            n = len(cartas_jugada)
                            if n == 0:
                                continue
                            solapamiento = int(card_width * 0.35) if n > 1 else 0  
                            inicio_rect = pygame.Rect(x_actual, y, card_width, card_height)
                            final_rect = pygame.Rect(x_actual + (n-1)*solapamiento, y, card_width, card_height)
                            # Guardar el índice original en playMade
                            rects_jugadas[jugador.playerName].append({
                                "inicio": inicio_rect,
                                "final": final_rect,
                                "tipo": "trio" if n == 3 else "straight",
                                "play_index": play_index,
                                "cartas": cartas_jugada
                            })
                            # Dibuja la jugada
                            for i, carta in enumerate(cartas_jugada):
                                img = get_card_image(carta)
                                img = pygame.transform.smoothscale(img, (card_width, card_height))
                                card_rect = pygame.Rect(x_actual + i * solapamiento, y, card_width, card_height)
                                screen.blit(img, card_rect.topleft)
                            x_actual += n * solapamiento + card_width + margen_jugada
        # --- FASE DE MOSTRAR ORDEN ---
        if fase == "mostrar_orden":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            screen.blit(fondo_img, (0, 0))

            # --- RECTÁNGULO DE FONDO GRIS ---
            ancho_rect = 420
            alto_rect = 60 + 40 * len(mensaje_orden.split("\n"))
            x_rect = (WIDTH - ancho_rect) // 2
            y_rect = HEIGHT // 2 - 180  # Más arriba

            # --- Usa la fuente personalizada desde assets ---
            font_path = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
            font_orden = pygame.font.Font(font_path, 25)  # Fuente de videojuego

            rect_fondo = pygame.Rect(x_rect, y_rect, ancho_rect, alto_rect)
            pygame.draw.rect(screen, (60, 60, 60), rect_fondo, border_radius=18)
            pygame.draw.rect(screen, (180, 180, 180), rect_fondo, 2, border_radius=18)

            lineas = mensaje_orden.split("\n")
            for i, linea in enumerate(lineas):
                texto = font_orden.render(linea, True, (255, 255, 255))  # Color blanco
                rect = texto.get_rect(center=(WIDTH // 2, y_rect + 36 + i * 40))
                screen.blit(texto, rect)
            pygame.display.flip()
            # Espera 5 segundos y pasa a la fase de juego
            if time.time() - tiempo_inicio_orden >= 5:
                fase = "juego"
                #Aquí voy a inicializar la ronda
                #round = startRound(players, screen)[0]
                #for c in round.discards:
                #    mazo_descarte.append(c)
                #deckForRound = [c for c in round.deck.cards if c!= round.discards]
                #print(str(round.discards))

                #mainGameLoop(screen, players, deck, mazo_descarte, nombre, zona_cartas)
                pass
            continue

        # --- DETECTAR FIN DE RONDA ---
        if fase == "juego":
            for jugador in players:
                if hasattr(jugador, "playerHand") and len(jugador.playerHand) == 0:
                    # Calcular puntos de todos los jugadores
                    for p in players:
                        p.calculatePoints()
                    fase = "fin"
                    fase_fin_tiempo = time.time()
                    break

        # --- FASE DE FIN ---
        if fase == "fin":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            screen.blit(fondo_img, (0, 0))
            mostrar_puntuaciones_final(screen, fondo_img, players, WIDTH, HEIGHT, ASSETS_PATH)
            pygame.display.flip()
            # Espera 7 segundos y termina el juego (puedes cambiar el tiempo)
            if time.time() - fase_fin_tiempo >= 7:
                running = False
            continue

        pygame.display.flip()
    return

def mostrar_puntuaciones_final(screen, fondo_img, players, WIDTH, HEIGHT, ASSETS_PATH):
    # Ordenar jugadores por puntos de menor a mayor
    jugadores_ordenados = sorted(players, key=lambda j: getattr(j, "playerPoints", 0))

    ancho_rect = 550
    alto_rect = 60 + 40 * len(jugadores_ordenados)
    x_rect = (WIDTH - ancho_rect) // 2
    y_rect = HEIGHT // 2 - 180

    font_path = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
    if os.path.exists(font_path):
        font_orden = pygame.font.Font(font_path, 25)
    else:
        font_orden = pygame.font.SysFont("arial", 25, bold=True)

    rect_fondo = pygame.Rect(x_rect, y_rect, ancho_rect, alto_rect)
    pygame.draw.rect(screen, (60, 60, 60), rect_fondo, border_radius=18)
    pygame.draw.rect(screen, (180, 180, 180), rect_fondo, 2, border_radius=18)

    titulo = font_orden.render("Puntuaciones Finales", True, (255, 255, 255))
    rect_titulo = titulo.get_rect(center=(WIDTH // 2, y_rect + 36))
    screen.blit(titulo, rect_titulo)

    for i, jugador in enumerate(jugadores_ordenados):
        nombre = getattr(jugador, "playerName", f"Jugador {i+1}")
        puntos = getattr(jugador, "playerPoints", 0)
        linea = f"{nombre}: {puntos} puntos"
        texto = font_orden.render(linea, True, (255, 255, 255))
        rect = texto.get_rect(center=(WIDTH // 2, y_rect + 80 + i * 40))
        screen.blit(texto, rect)

def actualizar_indices_visual_hand(visual_hand):
    """
    Reasigna el índice visual (id_visual) a cada carta en visual_hand.
    """
    for idx, carta in enumerate(visual_hand):
        carta.id_visual = idx

def compactar_visual_hand(visual_hand):
    """
    Si falta una carta (None o eliminada), mueve las cartas hacia la izquierda
    y reasigna los índices visuales para que no queden huecos.
    """
    # Elimina cualquier carta None o inexistente
    visual_hand = [c for c in visual_hand if c is not None]

    # Reasigna los índices visuales
    for idx, carta in enumerate(visual_hand):
        carta.id_visual = idx

    return visual_hand

def reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref):
    global dragging, carta_arrastrada, drag_rect, drag_offset_x, organizar_habilitado
    """
    Borra todo lo visual y reconstruye la mano visual y sus ubicaciones
    """
    visual_hand.clear()
    cuadros_interactivos.clear()
    cartas_ref.clear()

    # Reconstruye visual_hand con las cartas actuales del jugador
    for idx, carta in enumerate(jugador_local.playerHand):
        visual_hand.append(carta)
        carta.id_visual = idx  # Si usas id_visual

    # Reinicia variables de arrastre
    global dragging, carta_arrastrada, drag_rect, drag_offset_x
    dragging = False
    carta_arrastrada = None
    drag_rect = None
    drag_offset_x = 0

    organizar_habilitado = True  # Así puedes modificarla aquí también

def ocultar_elementos_visual(screen, fondo_img):
    """
    Oculta todo lo visual del juego excepto el fondo.
    """
    screen.blit(fondo_img, (0, 0))
    pygame.display.flip()

def mostrar_cartas_eleccion(screen, cartas_eleccion):
    for carta in cartas_eleccion:
        # Siempre muestra la carta de reverso
        img = get_card_image("PT")
        img = pygame.transform.smoothscale(img, (60, 90))
        screen.blit(img, carta.rect.topleft)
        
        # NUEVO PARA PRUEBAS
        # Dibuja el rectángulo de colisión para diagnóstico (QUITAR DESPUÉS)
        pygame.draw.rect(screen, (255, 0, 0), carta.rect, 2) # Rojo, 2px de grosor
        
        screen.blit(img, carta.rect.topleft)

def process_received_messagesUi2():
        """Procesa los mensajes recividos de la red"""
        if hasattr(network_manager,'received_data') and network_manager.received_data:
            with network_manager.lock:
                data = network_manager.received_data
                network_manager.received_data = None  # Limpiar despues de procesar

            print(f"Procesando mensaje recibido en Ui2.py: {data}")
            
            if network_manager.is_host:
                #with threading.Lock:
                # Si es un mensaje de ESTADO (como el que contiene cartas_disponibles, elecciones, etc.) en ui2
                if isinstance(data, dict) and data.get("type") in ["ELECTION_CARDS","SELECTION_UPDATE", "ESTADO_CARTAS", "ORDEN_COMPLETO"]:
                    network_manager.game_state.update(data)
                    print(f"Estado del juego actualizado: {network_manager.game_state}")
                elif isinstance(data, dict) and data.get("type") in ["BAJARSE","TOMAR_DESCARTE", "TOMAR_CARTA", "DESCARTE"]:
                    network_manager.moves_gameServer.append(data)
                    print(f" Jugada del jugador recibida:{data.get("type"),network_manager.moves_gameServer}")
                # Si es otro tipo de estructura/mensaje no clasificado
                else:
                    network_manager.incoming_messages.append(("raw", data)) # Opcional: para mensajes no clasificados
                    print(f"Mensaje guardado en incoming_messages... raw {network_manager.incoming_messages}")

def recalcular_posiciones_eleccion(cartas_eleccion, WIDTH, HEIGHT):
    """Calcula y asigna el atributo .rect a todas las cartas de elección."""
    if not cartas_eleccion:
        return

    # Parámetros de diseño (ajustar según tu UI)
    CARD_WIDTH = 60
    CARD_HEIGHT = 90
    espacio = 120 # separación horizontal entre cartas

    centro_x = WIDTH // 2
    centro_y = HEIGHT // 2
    
    total_cartas = len(cartas_eleccion)
    total_ancho = espacio * (total_cartas - 1)
    inicio_x = centro_x - total_ancho // 2 # Punto de inicio para centrar

    for i, carta in enumerate(cartas_eleccion):
        # La línea clave: asigna el rect a la carta
        carta.rect = pygame.Rect(
            inicio_x + i * espacio, 
            centro_y - CARD_HEIGHT // 2, 
            CARD_WIDTH, 
            CARD_HEIGHT
        )

if __name__ == "__main__":
    #ocultar_elementos_visual(screen, fondo_img)  # Solo muestra el fondo al inicio
    main()