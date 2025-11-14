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
import sys


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
# --- Iniciar fuente centralizada del juego ---
FONT_FILE = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
_fonts_cache = {}
def get_game_font(size):
    """Devuelve pygame.font.Font cargada desde assets o SysFont si falla; cachea por tamaño."""
    if size in _fonts_cache:
        return _fonts_cache[size]
    try:
        if os.path.exists(FONT_FILE):
            f = pygame.font.Font(FONT_FILE, size)
        else:
            f = pygame.font.SysFont("arial", size)
    except Exception:
        f = pygame.font.SysFont("arial", size)
    _fonts_cache[size] = f
    return f
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
mostrar_boton_descartar = False
mostrar_boton_bajarse = False
mostrar_boton_comprar = False

# guarda la última carta tomada y por quién (para impedir descartarla en el mismo turno)
last_taken_card = None
last_taken_player = None
#Cambio Boton Menu / Salir




def show_menu_modal(screen, WIDTH, HEIGHT, ASSETS_PATH):
    import pygame
    import os
    clock = pygame.time.Clock()
    img_reanudar = pygame.image.load(os.path.join(ASSETS_PATH, "reanudar.png")).convert_alpha()
    img_ajustes = pygame.image.load(os.path.join(ASSETS_PATH, "ajustes.png")).convert_alpha()
    img_salir = pygame.image.load(os.path.join(ASSETS_PATH, "salir.png")).convert_alpha()
    btn_w, btn_h = 220, 70
    img_reanudar = pygame.transform.smoothscale(img_reanudar, (btn_w, btn_h))
    img_ajustes = pygame.transform.smoothscale(img_ajustes, (btn_w, btn_h))
    img_salir = pygame.transform.smoothscale(img_salir, (btn_w, btn_h))
    try:
        background_snapshot = screen.copy()
    except Exception:
        background_snapshot = pygame.Surface((WIDTH, HEIGHT))
        background_snapshot.blit(screen, (0, 0))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))

    w, h = 330, 300
    x = (WIDTH - w) // 2
    y = (HEIGHT - h) // 2
    modal_rect = pygame.Rect(x, y, w, h)
    padding = 16

    btn_w, btn_h = 220, 44
    espacio_vertical = 35
    inicio_y = y + 40
    btn_resume = pygame.Rect(x + (w - btn_w) // 2, inicio_y, btn_w, btn_h)
    btn_config = pygame.Rect(x + (w - btn_w) // 2, inicio_y + btn_h + espacio_vertical, btn_w, btn_h)
    btn_exit   = pygame.Rect(x + (w - btn_w) // 2, inicio_y + 2 * (btn_h + espacio_vertical), btn_w, btn_h)
    font_path = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
    title_font = pygame.font.Font(font_path, 16)

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return "exit"
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return "resume"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if btn_resume.collidepoint(mx, my):
                    return "resume"
                if btn_config.collidepoint(mx, my):
                    return "config"
                if btn_exit.collidepoint(mx, my):
                    pygame.quit()

        if pygame.display.get_init():
            screen.blit(background_snapshot, (0, 0))
            screen.blit(overlay, (0, 0))

            pygame.draw.rect(screen, (40, 40, 40), modal_rect, border_radius=12)
            pygame.draw.rect(screen, (150, 150, 150), modal_rect, 2, border_radius=12)

            title = title_font.render("Menú de Pausa", True, (230, 230, 230))
            screen.blit(title, (x + padding + 50, y + padding))

            screen.blit(img_reanudar, btn_resume.topleft)
            screen.blit(img_ajustes, btn_config.topleft)
            screen.blit(img_salir, btn_exit.topleft)
            pygame.display.flip()
            clock.tick(60)
        else:
            return "exit"
#Cambio Boton Menu / Salir

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
            if (c is last_taken_card or c == last_taken_card) and len(items) >= 1:
                return False
        except Exception:
            if str(c) == str(last_taken_card):
                return False
    return True

# ---------------------- Helpers robustos para UI ----------------------
from Card import Card

def string_to_card(card_string_or_object):
    """
    Si recibe string como 'A♥' o 'Joker', devuelve Card(...).
    Si recibe lista con strings, intenta convertir cada elemento.
    Si recibe ya un Card, lo devuelve.
    """
    if isinstance(card_string_or_object, Card):
        return card_string_or_object
    if isinstance(card_string_or_object, list):
        # retorna lista de Card o lista original si ya son Card
        return [string_to_card(c) for c in card_string_or_object]
    if not isinstance(card_string_or_object, str):
        return card_string_or_object

    # es str
    if card_string_or_object == "Joker":
        return Card("Joker", "", joker=True)
    # valor == todo menos último char, palo == último char
    value = card_string_or_object[:-1]
    suit = card_string_or_object[-1]
    
    return Card(value, suit)

def resolve_play(jugador, raw_play, play_index=None):
    """
    raw_play puede ser:
      - una lista de Card (ok) -> devuelve la misma lista
      - una lista de str -> si jugador tiene 'jugadas_bajadas' usa esa para resolver
      - un dict -> devolver dict convertida con Card objects
    Devuelve la estructura con cartas como objetos Card (no strings). Si no puede resolver,
    devuelve None.
    """
    # caso ya resuelto
    if isinstance(raw_play, dict):
        resolved = {}
        if "trio" in raw_play and raw_play["trio"]:
            resolved["trio"] = [string_to_card(c) for c in raw_play["trio"]]
        if "straight" in raw_play and raw_play["straight"]:
            resolved["straight"] = [string_to_card(c) for c in raw_play["straight"]]
        return resolved

    if isinstance(raw_play, list) and raw_play and isinstance(raw_play[0], str):
        # busca en jugadas_bajadas si existe
        if hasattr(jugador, "jugadas_bajadas") and play_index is not None and len(jugador.jugadas_bajadas) > play_index:
            return jugador.jugadas_bajadas[play_index]
        # no hay resolved, intentar convertir strings a Card
        try:
            return [string_to_card(s) for s in raw_play]
        except Exception:
            return None

    # si es lista de Card o mezcla:
    if isinstance(raw_play, list):
        return [string_to_card(c) for c in raw_play]

    # fallback
    return raw_play
# --------------------------------------------------------------------


# Nueva función: valida tipos y llama insertCard solo si todo está correcto
def safe_insert_card(jugador, target_player, idx_jugada, card_to_insert, position, target_subtype=None):
    """
    Valida tipos y que la jugada objetivo tenga objetos Card.
    target_subtype: "trio" | "straight" | None (None -> intenta inferir)
    """
    from Card import Card
    objeto_carta = string_to_card(card_to_insert)
    print(f"Objeto de carta: {objeto_carta}")
    print(f"String de carta: {card_to_insert}")
    # normaliza carta
    if not isinstance(card_to_insert, Card):
        print("safe_insert_card: card_to_insert NO es Card:", type(card_to_insert), repr(card_to_insert))
        return False

    plays = getattr(target_player, "playMade", [])
    if idx_jugada < 0 or idx_jugada >= len(plays):
        print("safe_insert_card: idx_jugada fuera de rango:", idx_jugada, "len(playMade)=", len(plays))
        return False

    target_play = plays[idx_jugada]

    # si target_play es dict, elegimos la sublista correcta
    if isinstance(target_play, dict):
        if target_subtype == "trio":
            cartas_jugada = target_play.get("trio", [])
        elif target_subtype == "straight":
            cartas_jugada = target_play.get("straight", [])
        else:
            # intentar inferir: preferir straight si existe no vacío
            cartas_jugada = target_play.get("straight") or target_play.get("trio") or []
    else:
        cartas_jugada = target_play or []

    # Validar que cartas_jugada sean objetos Card
    for c in cartas_jugada:
        string_to_card(c)
        if not isinstance(c, Card):
            print("safe_insert_card: elemento en la jugada objetivo NO es Card:", type(c), repr(c))
            print("target_player.playMade[{}] = {}".format(idx_jugada, target_play))
            return False

    # Todo bien: llamar al método real. Importante: aquí llamamos con idx_jugada (índice en playMade).
    try:
        # Si tu Player.insertCard espera trabajar con dict y asume 'straight' por defecto,
        # esto funcionará. Si insertCard necesita un subtype explícito, habría que pasarlo.
        result = jugador.insertCard(targetPlayer=target_player, targetPlayIndex=idx_jugada, cardToInsert=card_to_insert, position=position)
        if result:
            return True
        else:
            return False
    except Exception as e:
        print("safe_insert_card: excepción al llamar insertCard:", e)
        return False

def render_text_with_border(text, font, color, border_color, pos, surface):
    # Dibuja el texto en 8 posiciones alrededor (borde)
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
        border = font.render(text, True, border_color)
        surface.blit(border, (pos[0]+dx, pos[1]+dy))
    # Dibuja el texto principal encima
    txt = font.render(text, True, color)
    surface.blit(txt, pos)

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

#CAMBIO 1
# --- Añadir en ui2.py (zona de utilidades/UI) ---
def draw_simple_button(surface, rect, text, font, bg=(70,70,70), fg=(255,255,255)):
    pygame.draw.rect(surface, bg, rect, border_radius=8)
    pygame.draw.rect(surface, (180,180,180), rect, 2, border_radius=8)
    txt = font.render(text, True, fg)
    tr = txt.get_rect(center=rect.center)
    surface.blit(txt, tr)


#COMPRAR CARTA

def confirm_buy_card(screen, card, WIDTH, HEIGHT, ASSETS_PATH, font):
    #def confirm_replace_joker(screen, WIDTH, HEIGHT, ASSETS_PATH):
    """
    Muestra una ventana modal que pregunta si el jugador quiere comprar la carta.
    - card: objeto Card (puede ser None para mostrar reverso).
    - Devuelve True si pulsa SI, False si pulsa NO o cierra.
    Bloqueante: procesa su propio loop hasta respuesta.
    """
    clock = pygame.time.Clock()
    # Captura del fondo actual para mostrarlo detrás del modal (asegura transparencia visual)
    try:
        background_snapshot = screen.copy()
    except Exception:
        background_snapshot = pygame.Surface((WIDTH, HEIGHT))
        background_snapshot.blit(screen, (0, 0))

    # Overlay semi-transparente (creado una vez)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))  # ajuste alpha aquí (0=totalmente transparente, 255=opaco)


    #Cambio 3 (Tamaño del Rectángulo de 420,240 a 330,320)
    # Tamaños y rects
    w, h = 330, 320
    #Cambio 3

    x = (WIDTH - w)//2
    y = (HEIGHT - h)//2
    modal_rect = pygame.Rect(x, y, w, h)
    padding = 16


    #Cambio 4 (Centrar Carta)
    # Rect para imagen de carta
    card_w, card_h = 100, 150
    card_rect = pygame.Rect(x + (w - card_w)//2, y + (h - card_h)//2, card_w, card_h)
    #Cambio 4


    # Botones SI / NO
    btn_w, btn_h = 120, 44
    btn_yes = pygame.Rect(x + w - padding - btn_w, y + h - padding - btn_h, btn_w, btn_h)
    btn_no = pygame.Rect(x + w - padding - 2*btn_w - 12, y + h - padding - btn_h, btn_w, btn_h)

    # Preparar imagen de carta (usar get_card_image existente)
    try:
        if card is None:
            card_img = get_card_image("back")
        else:
            card_img = get_card_image(card)
    except Exception:
        card_img = pygame.Surface((card_w, card_h))
        card_img.fill((200,200,200))
    card_img = pygame.transform.smoothscale(card_img, (card_w, card_h))

    #Cambio 5 (Tipografía)
    #Descartamos: title_font = pygame.font.SysFont("arial", 20, bold=True)
    font_path = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
    title_font = pygame.font.Font(font_path, 16)
    info_font = pygame.font.Font(font_path, 12)
    #Cambio 5


    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return False
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if btn_yes.collidepoint(mx, my):
                    return True
                if btn_no.collidepoint(mx, my):
                    return False

        # Dibujo del modal: primero el fondo capturado, luego overlay semi-transparente
        screen.blit(background_snapshot, (0, 0))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (40,40,40), modal_rect, border_radius=12)
        pygame.draw.rect(screen, (150,150,150), modal_rect, 2, border_radius=12)

        # Texto
        title = title_font.render("Comprar carta", True, (230,230,230))
        screen.blit(title, (x + padding, y + padding))

        
        #Cambio 6 (Separar Texto)
        info = info_font.render("¿Deseas comprar esta carta", True, (200,200,200))
        screen.blit(info, (x + padding, y + padding + 30))
        info2 = info_font.render("del descarte?", True, (200,200,200))
        screen.blit(info2, (x + padding, y + padding + 50))
        #Cambio 6


        # Dibuja la carta
        screen.blit(card_img, card_rect.topleft)
        # Mostrar nombre de carta debajo
        name_txt = info_font.render(str(card) if card is not None else "?", True, (230,230,230))
        nt = name_txt.get_rect(midtop=(card_rect.centerx, card_rect.bottom + 6))
        screen.blit(name_txt, nt)

        # Botones
        draw_simple_button(screen, btn_no, "No", info_font, bg=(120,40,40))
        draw_simple_button(screen, btn_yes, "Si", info_font, bg=(40,120,40))

        pygame.display.flip()
        clock.tick(60)
#COMPRAR CARTA'''




def choose_insert_target_modal(screen, WIDTH, HEIGHT, ASSETS_PATH, fase):
    """
    Modal: Pregunta "Dónde deseas insertar la carta?"
    Botones según fase:
        Ronda 1: Trio / Seguidilla
        Ronda 2: Seguidilla 2 / Seguidilla 1
        Ronda 3: Trio 1 / Trio 2 / Trio 3
        Ronda 4: Trio 1 / Trio 2 / Seguidilla
    Devuelve: nombre del botón elegido o None si se cierra.
    """
    jugador_local = globals().get("jugador_local", None)
    # Mostrar modal SOLO si el jugador local existe, se ha bajado y está en su turno (isHand True)
    if jugador_local is None or not getattr(jugador_local, "downHand", False) or not getattr(jugador_local, "isHand", False):
        return None
    # ------------------------------------------------------------------------

    clock = pygame.time.Clock()
    try:
        background_snapshot = screen.copy()
    except Exception:
        background_snapshot = pygame.Surface((WIDTH, HEIGHT))
        background_snapshot.blit(screen, (0, 0))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))

    w, h = 380, 180
    x = (WIDTH - w) // 2
    y = (HEIGHT - h) // 2
    modal_rect = pygame.Rect(x, y, w, h)
    padding = 14

    # botón de cierre (X) en la esquina superior derecha del modal
    close_btn_size = 28
    close_btn_rect = pygame.Rect(x + w - close_btn_size - 8, y + 8, close_btn_size, close_btn_size)

    # botones principales
    btn_w, btn_h = 100, 44
    buttons = []

    font_path = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
    title_font = pygame.font.Font(font_path, 16)
    info_font = pygame.font.Font(font_path, 12)

    # Crear botones según ronda
    if fase == "ronda1":
        buttons = [("Trio", pygame.Rect(x + padding, y + h - padding - btn_h, btn_w + 40, btn_h)),
                   ("Seguidilla", pygame.Rect(x + w - padding - btn_w - 40, y + h - padding - btn_h, btn_w + 40, btn_h))]
    elif fase == "ronda2":
        buttons = [("Seguidilla 2", pygame.Rect(x + padding, y + h - padding - btn_h, btn_w + 55, btn_h)),
                   ("Seguidilla 1", pygame.Rect(x + w - padding - btn_w - 50, y + h - padding - btn_h, btn_w + 55, btn_h))]
    elif fase == "ronda3":
        spacing = (w - 3 * btn_w) // 4
        buttons = [("Trio 1", pygame.Rect(x + spacing, y + h - padding - btn_h, btn_w, btn_h)),
                   ("Trio 2", pygame.Rect(x + 2*spacing + btn_w, y + h - padding - btn_h, btn_w, btn_h)),
                   ("Trio 3", pygame.Rect(x + 3*spacing + 2*btn_w, y + h - padding - btn_h, btn_w, btn_h))]
    elif fase == "ronda4":
        spacing = (w - 3 * btn_w) // 4
        buttons = [("Trio 1", pygame.Rect(x + spacing, y + h - padding - btn_h, btn_w, btn_h)),
                   ("Trio 2", pygame.Rect(x + 2*spacing + btn_w, y + h - padding - btn_h, btn_w, btn_h)),
                   ("Seguidilla", pygame.Rect(x + 3*spacing + 2*btn_w, y + h - padding - btn_h, btn_w, btn_h))]

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return None
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return None
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                # clic en X -> cancelar
                if close_btn_rect.collidepoint(mx, my):
                    return None
                for name, rect in buttons:
                    if rect.collidepoint(mx, my):
                        return name

        screen.blit(background_snapshot, (0, 0))
        screen.blit(overlay, (0, 0))

        # modal
        pygame.draw.rect(screen, (40, 40, 40), modal_rect, border_radius=12)
        pygame.draw.rect(screen, (150, 150, 150), modal_rect, 2, border_radius=12)

        # título
        title = title_font.render("¿Dónde deseas", True, (230, 230, 230))
        screen.blit(title, (x + padding, y + padding))
        subtitle = title_font.render("insertar la carta?", True, (230, 230, 230))
        screen.blit(subtitle, (x + padding, y + padding + 28))

        # dibujar botón X
        pygame.draw.rect(screen, (200, 60, 60), close_btn_rect, border_radius=6)
        x_txt = title_font.render("X", True, (255, 255, 255))
        xt = x_txt.get_rect(center=close_btn_rect.center)
        screen.blit(x_txt, xt)

        # botones de elección
        for name, rect in buttons:
            draw_simple_button(screen, rect, name, info_font, bg=(40, 120, 40))

        pygame.display.flip()
        clock.tick(60)

#Pantallitas el infierno del Joker

def trio_choice_modal(screen, WIDTH, HEIGHT, ASSETS_PATH):
    """
    Modal mostrado cuando el jugador eligió 'Trio' como destino.
    Botones: Insertar Trio / Sustituir Joker
    Devuelve: "insert_trio", "replace_joker" o None si se cierra.
    """
    clock = pygame.time.Clock()
    try:
        background_snapshot = screen.copy()
    except Exception:
        background_snapshot = pygame.Surface((WIDTH, HEIGHT))
        background_snapshot.blit(screen, (0, 0))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))

    w, h = 510, 140
    x = (WIDTH - w) // 2
    y = (HEIGHT - h) // 2
    modal_rect = pygame.Rect(x, y, w, h)
    padding = 14

    btn_w, btn_h = 200, 44
    btn_insert = pygame.Rect(x + padding, y + h - padding - btn_h, btn_w, btn_h)
    btn_replace = pygame.Rect(x + w - padding - btn_w, y + h - padding - btn_h, btn_w, btn_h)

    font_path = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
    title_font = pygame.font.Font(font_path, 16)
    info_font = pygame.font.Font(font_path, 12)
    info_font_small = pygame.font.Font(font_path, 8)

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return None
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return None
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if btn_insert.collidepoint(mx, my):
                    return "insert_trio"
                if btn_replace.collidepoint(mx, my):
                    return "replace_joker"

        screen.blit(background_snapshot, (0, 0))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (40, 40, 40), modal_rect, border_radius=12)
        pygame.draw.rect(screen, (150, 150, 150), modal_rect, 2, border_radius=12)

        title = title_font.render("Trio", True, (230, 230, 230))
        screen.blit(title, (x + padding, y + padding))

        info = info_font.render("Elige acción para insertar en el trío", True, (200, 200, 200))
        screen.blit(info, (x + padding, y + padding + 28))

        draw_simple_button(screen, btn_insert, "Insertar Normalmente", info_font_small, bg=(241, 196, 15))
        draw_simple_button(screen, btn_replace, "Sustituir Joker", info_font, bg=(241, 196, 15))

        pygame.display.flip()
        clock.tick(60)


def straight_choice_modal(screen, WIDTH, HEIGHT, ASSETS_PATH):
    """
    Modal mostrado cuando el jugador eligió 'Seguidilla' como destino.
    Botones: Inicio / Final / Sustituir Joker
    Devuelve: "start", "end", "replace_joker" o None si se cierra.
    """
    clock = pygame.time.Clock()
    try:
        background_snapshot = screen.copy()
    except Exception:
        background_snapshot = pygame.Surface((WIDTH, HEIGHT))
        background_snapshot.blit(screen, (0, 0))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))

    w, h = 500, 180
    x = (WIDTH - w) // 2
    y = (HEIGHT - h) // 2
    modal_rect = pygame.Rect(x, y, w, h)
    padding = 14

    btn_w, btn_h = 150, 40
    btn_start = pygame.Rect(x + padding, y + h - padding - btn_h, btn_w, btn_h)
    btn_end = pygame.Rect(x + (w // 2 - btn_w // 2), y + h - padding - btn_h, btn_w, btn_h)
    btn_replace = pygame.Rect(x + w - padding - btn_w, y + h - padding - btn_h, btn_w, btn_h)

    font_path = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
    title_font = pygame.font.Font(font_path, 16)
    info_font = pygame.font.Font(font_path, 12)
    info_font_small = pygame.font.Font(font_path, 9)

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return None
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return None
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if btn_start.collidepoint(mx, my):
                    return "start"
                if btn_end.collidepoint(mx, my):
                    return "end"
                if btn_replace.collidepoint(mx, my):
                    return "replace_joker"

        screen.blit(background_snapshot, (0, 0))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (40, 40, 40), modal_rect, border_radius=12)
        pygame.draw.rect(screen, (150, 150, 150), modal_rect, 2, border_radius=12)

        title = title_font.render("Seguidilla", True, (230, 230, 230))
        screen.blit(title, (x + padding, y + padding))

        info = info_font.render("¿Dónde deseas insertar la carta", True, (200, 200, 200))
        screen.blit(info, (x + padding, y + padding + 28))

        info = info_font.render("en la seguidilla?", True, (200, 200, 200))
        screen.blit(info, (x + padding, y + padding + 56))

        draw_simple_button(screen, btn_start, "Inicio", info_font, bg=(52, 152, 219))
        draw_simple_button(screen, btn_end, "Final", info_font, bg=(52, 152, 219))
        draw_simple_button(screen, btn_replace, "Sustituir Joker", info_font_small, bg=(52, 152, 219))

        pygame.display.flip()
        clock.tick(60)

#Pantallitas el infierno del Joker




def confirm_buy_card(screen, card, WIDTH, HEIGHT, ASSETS_PATH, font):
    clock = pygame.time.Clock()
    #La papa de las pantallas
    # 1) Primera pantalla: ¿Dónde deseas insertar la carta?
    first_choice = choose_insert_target_modal(screen, WIDTH, HEIGHT, ASSETS_PATH)
    if first_choice is None:
        # usuario cerró la pantalla sin elegir
        pass
    elif first_choice == "trio":
        # 2) Si eligió Trio, abrir las opciones de trio
        trio_action = trio_choice_modal(screen, WIDTH, HEIGHT, ASSETS_PATH)
        if trio_action == "insert_trio":
            # Aquí llamas la lógica para insertar en trío (inicio/final no aplica)
            # ejemplo: safe_insert_card(..., position=None) o la que uses
            print("Acción elegida: Insertar en Trío")
            # TODO: llamar safe_insert_card / insertCard con los parámetros adecuados
            return None
        elif trio_action == "replace_joker":
            print("Acción elegida: Sustituir Joker en Trío")
            # TODO: llamar a la lógica que sustituye joker (position=None en insertCard)
            return None
    
    elif first_choice == "straight":
        # 3) Si eligió Seguidilla, abrir las opciones de seguidilla (Inicio/Final/Sustituir Joker)
        straight_action = straight_choice_modal(screen, WIDTH, HEIGHT, ASSETS_PATH)
        if straight_action == "start":
            print("Acción elegida: Insertar al Inicio de la Seguidilla")
            # TODO: llamar safe_insert_card(..., position="start")
            return None
        elif straight_action == "end":
            print("Acción elegida: Insertar al Final de la Seguidilla")
            # TODO: llamar safe_insert_card(..., position="end")
            return None
        elif straight_action == "replace_joker":
            print("Acción elegida: Sustituir Joker en Seguidilla")
            # TODO: llamar safe_insert_card(..., position=None)
            return None
    #La papa de las pantallas
        pygame.display.flip()
        clock.tick(60)



#CambioJoker #WhySoSerious

def confirm_joker(screen, card, WIDTH, HEIGHT, ASSETS_PATH, font):
    #def confirm_replace_joker(screen, WIDTH, HEIGHT, ASSETS_PATH):
    """
    Muestra una ventana modal que pregunta si el jugador quiere comprar la carta.
    - card: objeto Card (puede ser None para mostrar reverso).
    - font: pygame.font.Font ya creado para renderizar texto.
    Devuelve True si pulsa Si, False si pulsa No o cierra.
    Bloqueante: procesa su propio loop hasta respuesta.
    """
    clock = pygame.time.Clock()
    try:
        background_snapshot = screen.copy()
    except Exception:
        background_snapshot = pygame.Surface((WIDTH, HEIGHT))
        background_snapshot.blit(screen, (0, 0))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))

    w, h = 330, 370
    x = (WIDTH - w)//2
    y = (HEIGHT - h)//2
    modal_rect = pygame.Rect(x, y, w, h)
    padding = 16

    card_w, card_h = 100, 150
    card_rect = pygame.Rect(x + (w - card_w)//2, y + (h - card_h)//2, card_w, card_h)

    btn_w, btn_h = 140, 44
    btn_replace = pygame.Rect(x + w - padding - btn_w, y + h - padding - btn_h, btn_w, btn_h)
    btn_continue = pygame.Rect(x + w - padding - 2*btn_w - 12, y + h - padding - btn_h, btn_w, btn_h)

    # Mostrar siempre la imagen del Joker
    try:
        card_img = get_card_image(Card("Joker", "", joker=True))
    except Exception:
        card_img = pygame.Surface((card_w, card_h))
        card_img.fill((200,200,200))
    card_img = pygame.transform.smoothscale(card_img, (card_w, card_h))
    font_path = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
    title_font = pygame.font.Font(font_path, 16)
    info_font = pygame.font.Font(font_path, 12)

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return False
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if btn_replace.collidepoint(mx, my):
                    return True
                if btn_continue.collidepoint(mx, my):
                    return False

        screen.blit(background_snapshot, (0, 0))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (40,40,40), modal_rect, border_radius=12)
        pygame.draw.rect(screen, (150,150,150), modal_rect, 2, border_radius=12)

        title = title_font.render("Jugada con Joker", True, (230,230,230))
        screen.blit(title, (x + padding, y + padding))

        info1 = info_font.render("¿Deseas continuar la", True, (200,200,200))
        info2 = info_font.render("secuencia o reemplazar", True, (200,200,200))
        info3 = info_font.render("al Joker?", True, (200,200,200))
        screen.blit(info1, (x + padding, y + padding + 30))
        screen.blit(info2, (x + padding, y + padding + 50))
        screen.blit(info3, (x + padding, y + padding + 70))

        screen.blit(card_img, card_rect.topleft)
        name_txt = info_font.render("Joker", True, (230,230,230))
        nt = name_txt.get_rect(midtop=(card_rect.centerx, card_rect.bottom + 6))
        screen.blit(name_txt, nt)

        draw_simple_button(screen, btn_continue, "Seguir", info_font, bg=(120,40,40))
        draw_simple_button(screen, btn_replace, "Reemplazar", info_font, bg=(40,120,40))

        pygame.display.flip()
        clock.tick(60)
#CambioJoker #WhySoSerious
    '''"""
    Muestra una ventana modal que pregunta si el jugador quiere comprar la carta.
    - card: objeto Card (puede ser None para mostrar reverso).
    - Devuelve True si pulsa SI, False si pulsa NO o cierra.
    Bloqueante: procesa su propio loop hasta respuesta.
    """
    clock = pygame.time.Clock()
    # Captura del fondo actual para mostrarlo detrás del modal (asegura transparencia visual)
    try:
        background_snapshot = screen.copy()
    except Exception:
        background_snapshot = pygame.Surface((WIDTH, HEIGHT))
        background_snapshot.blit(screen, (0, 0))

    # Overlay semi-transparente (creado una vez)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))  # ajuste alpha aquí (0=totalmente transparente, 255=opaco)


    #Cambio 3 (Tamaño del Rectángulo de 420,240 a 330,320)
    # Tamaños y rects
    w, h = 330, 320
    #Cambio 3

    x = (WIDTH - w)//2
    y = (HEIGHT - h)//2
    modal_rect = pygame.Rect(x, y, w, h)
    padding = 16


    #Cambio 4 (Centrar Carta)
    # Rect para imagen de carta
    card_w, card_h = 100, 150
    ''' '''Descartamos: card_rect = pygame.Rect(x + padding, y + (h - card_h)//2, card_w, card_h)''' '''
    card_rect = pygame.Rect(x + (w - card_w)//2, y + (h - card_h)//2, card_w, card_h)
    #Cambio 4


    # Botones SI / NO
    btn_w, btn_h = 120, 44
    btn_yes = pygame.Rect(x + w - padding - btn_w, y + h - padding - btn_h, btn_w, btn_h)
    btn_no = pygame.Rect(x + w - padding - 2*btn_w - 12, y + h - padding - btn_h, btn_w, btn_h)

    # Preparar imagen de carta (usar get_card_image existente)
    try:
        if card is None:
            card_img = get_card_image("back")
        else:
            card_img = get_card_image(card)
    except Exception:
        card_img = pygame.Surface((card_w, card_h))
        card_img.fill((200,200,200))
    card_img = pygame.transform.smoothscale(card_img, (card_w, card_h))

    #Cambio 5 (Tipografía)
    ''' '''Descartamos: title_font = pygame.font.SysFont("arial", 20, bold=True)
    info_font = font_small''' '''
    font_path = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
    title_font = pygame.font.Font(font_path, 16)
    info_font = pygame.font.Font(font_path, 12)
    #Cambio 5


    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return False
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if btn_yes.collidepoint(mx, my):
                    return True
                if btn_no.collidepoint(mx, my):
                    return False

        # Dibujo del modal: primero el fondo capturado, luego overlay semi-transparente
        screen.blit(background_snapshot, (0, 0))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (40,40,40), modal_rect, border_radius=12)
        pygame.draw.rect(screen, (150,150,150), modal_rect, 2, border_radius=12)

        # Texto
        title = title_font.render("Comprar carta", True, (230,230,230))
        screen.blit(title, (x + padding, y + padding))

        
        #Cambio 6 (Separar Texto)
        ''' '''info = info_font.render("¿Deseas comprar esta carta del descarte?", True, (200,200,200))
        screen.blit(info, (x + padding, y + padding + 30))''' '''
        info = info_font.render("¿Deseas comprar esta", True, (200,200,200))
        info2 = info_font.render("carta del descarte?", True, (200,200,200))
        screen.blit(info, (x + padding, y + padding + 30))
        screen.blit(info2, (x + padding, y + padding + 50))
        #Cambio 6


        # Dibuja la carta
        screen.blit(card_img, card_rect.topleft)
        # Mostrar nombre de carta debajo
        name_txt = info_font.render(str(card) if card is not None else "?", True, (230,230,230))
        nt = name_txt.get_rect(midtop=(card_rect.centerx, card_rect.bottom + 6))
        screen.blit(name_txt, nt)

        # Botones
        draw_simple_button(screen, btn_no, "No", info_font, bg=(120,40,40))
        draw_simple_button(screen, btn_yes, "Si", info_font, bg=(40,120,40))

        pygame.display.flip()
        clock.tick(60)'''
#CAMBIO 1 

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

def update_descartar_visibility(zona_cartas, roundThree, roundFour):
    """
    Botón 'Descartar':
    - Rondas 1/2 → visible si zona_cartas[2] tiene al menos 1 carta.
    - Rondas 3/4 → visible si zona_cartas[3] tiene al menos 1 carta.
    """
    global mostrar_boton_descartar

    try:
        if zona_cartas is None:
            mostrar_boton_descartar = False
            return

        if roundThree or roundFour:
            # revisar zona 3
            mostrar_boton_descartar = len(zona_cartas) > 3 and len(zona_cartas[3]) > 0
        else:
            # revisar zona 2
            mostrar_boton_descartar = len(zona_cartas) > 2 and len(zona_cartas[2]) > 0

    except Exception:
        mostrar_boton_descartar = False
def update_bajarse_visibility(zona_cartas, roundThree, roundFour):
    """
    Reglas:
    - En rondas 1/2 → zonas 0 y 1 deben tener al menos 1 carta.
    - En rondas 3/4 → zonas 0, 1 y 2 deben tener al menos 1 carta.
    """
    global mostrar_boton_bajarse
    try:
        # Validar existencia de zona_cartas
        if 'zona_cartas' not in globals() or zona_cartas is None:
            mostrar_boton_bajarse = False
            return

        # Rondas 3 o 4 → revisar zonas 0,1,2
        if roundThree or roundFour:
            if len(zona_cartas) > 2:
                mostrar_boton_bajarse = (
                    len(zona_cartas[0]) > 0 and
                    len(zona_cartas[1]) > 0 and
                    len(zona_cartas[2]) > 0
                )
            else:
                mostrar_boton_bajarse = False
            return

        # Rondas 1 o 2 → solo revisar zonas 0 y 1
        if len(zona_cartas) > 1:
            mostrar_boton_bajarse = (
                len(zona_cartas[0]) > 0 and
                len(zona_cartas[1]) > 0
            )
        else:
            mostrar_boton_bajarse = False

    except Exception:
        mostrar_boton_bajarse = False
def update_comprar_visibility():
    """
    El botón 'Comprar carta' será visible solo mientras la flag mostrar_boton_comprar sea True.
    """
    global mostrar_boton_comprar
    # Simplemente devolvemos la flag, no hay validación de zona ni ronda
    return mostrar_boton_comprar


def main(manager_de_red): # <-- Acepta el manager de red
    global mostrar_boton_comprar
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

    global ronudOne, roundTwo   # Para prueba
    # variables de espera / temporizador usadas en el loop (evitan UnboundLocalError)
    global waiting, time_waiting, noBuy


    roundOne = True
    roundTwo = False
    roundThree = False
    roundFour = False
    # inicializar flags de espera/temporizador
    waiting = False
    time_waiting = 0.0
    noBuy = False
# ...existing code..

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
        player1 = Player(host_port, network_manager.playerName)

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

    zona_cartas = [[], [], [], []]  # [0]=segunda casilla, [1]=primera casilla, [2]=tercera casilla o descarte  ///o cuando son 4 [0]=segunda casilla, [1]=primera casilla, [2]=tercera casilla, [3]=cuarta casilla o descarte

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

    # Variables para manejar el ciclo de compra. 
    noBuy = True        # Indica que no hay compras activas.
    bought = False      # Indica que ya hubo ciclo de compras en el turno actual.
    waiting = False     # Indica que el MANO esta esperando alguna decision de compra.
    time_waiting = None # Variable para manejar el tiempo de espera.

    while running:
        # --- SOLO FASE DE ELECCIÓN ---
        update_descartar_visibility(zona_cartas, roundThree, roundFour)
        update_comprar_visibility()
        update_bajarse_visibility(zona_cartas, roundThree, roundFour)
        if fase == "eleccion":
            screen.blit(fondo_img, (0, 0))  # Nuevo pero se puede quedar :)

            # Procesando mensaje con datos de seleccion de cartas y la lista de jugadores...
            if not network_manager.is_host:
                # Recuperar los mensajes recibidos del buffer de red
                if roundOne:
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
                            print("Jugador: Recibido orden de jugadores")
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
                                print("Jugador: creado Round local con pile/discards recibidos.NO DEBERIA...")
                            # Buscar y actualizar jugador local
                            puerto_local = network_manager.player.getsockname()[1]
                            for p in players:
                                if p.playerId == puerto_local:
                                    jugador_local = p
                                    break

                            jugador_local.playerHand = hands[jugador_local.playerId] 
                            visual_hand = list(jugador_local.playerHand)  # Copia inicial para el orden visual
                            # Limpiar zonas de cartas para todas las rondas
                            zona_cartas[0] = []
                            zona_cartas[0].clear()
                            zona_cartas[1] = []
                            zona_cartas[1].clear()
                            if roundThree or roundFour:
                                zona_cartas[2] = []
                                zona_cartas[2].clear()
                            for idx, carta in enumerate(visual_hand):
                                if not hasattr(carta, "id_visual"):
                                    carta.id_visual = id(carta)  # O usa idx para algo más simple

                            # Cambiar fase
                            mensaje_orden = msg[1].get("orden_str", "")
                            tiempo_inicio_orden = time.time()
                            
                            if roundOne:
                                fase = "mostrar_orden"
                            elif roundTwo:
                                fase = "ronda2" 
                            elif roundThree:
                                fase = "ronda3"
                            elif roundFour:
                                fase = "ronda4"
                            
                # Fin procesar Mensajes de INICIO----  Cargar Mazos, Mano, e isHand... PARA EL JUGADOR...       

            if network_manager.is_host:
                if roundOne:
                    from Game import electionPhase
                    playerOrder = electionPhase(players, deck)
                    # Lista de jugadores Ordenada
                    players[:] = playerOrder
                    players[0].isHand = True    # El primer jugador es mano
                    player1 = None
                elif roundTwo or roundThree or roundFour:
                    # Rotar la lista: el primero pasa al final
                    players.append(players.pop(0))

                    # Reiniciar la bandera de 'isHand' para todos
                    for player in players:
                        player.isHand = False

                    # El nuevo primer jugador es la nueva mano
                    players[0].isHand = True
                #for p in players:
                if players[0].playerId == host_port:
                    jugador_local = players[0]
                    print(f"nombre del jugador_local   {jugador_local.playerName}")  

                # Construir mensaje de orden
                orden_str = "Orden de juego:\n"
                for idx, jugador in enumerate(players):
                    orden_str += f"{idx+1}. {jugador.playerName}\n"
                
                # Limpiar bajadas/parametros de los jagadores para cada ronda
                for p in players:
                    p.jugadas_bajadas = []
                    p.playMade = []
                    p.playerHand = []
                    p.downHand = False
                    p.cardDrawn = False
                # Inicializacion del mazo...
                round = startRound(players, screen)[0]
                print(f"deck para la ronda: {[str(c) for c in round.pile]}")
                print(f"descartes de la ronda: {[str(c) for c in round.discards]}")
                for c in round.discards:
                    mazo_descarte.append(c)
                deckForRound = round.pile
                print(f"Las manos a repartir ...... {round.hands}")
                # Enviar orden a todos
                
                # PARA PRUEBA...
                print(f" Mano del jugador... {jugador_local.playerHand}")
                '''if roundOne:
                    jugador_local.playerHand = [Card("2","♥"), Card("3","♥"), Card("4","♥"), 
                                                Card("5","♥"), Card("9","♦"), Card("9","♠"), 
                                                Card("9","♠")]  # Solo una carta para prueba
                    round.hands[jugador_local.playerId] = jugador_local.playerHand

                if roundTwo:
                    jugador_local.playerHand = [Card("2","♥"), Card("3","♥"), Card("4","♥"), 
                                                Card("5","♥"),
                                                Card("2","♠"), Card("3","♠"), Card("4","♠"), 
                                                Card("5","♠")]  # Solo una carta para prueba
                    round.hands[jugador_local.playerId] = jugador_local.playerHand'''
                # --------------''''
                '''if roundThree:
                    jugador_local.playerHand = [Card("9","♥"), Card("9","♠"), Card("9","♦"), 
                                                Card("8","♥"), Card("8","♠"), Card("8","♦"), 
                                                Card("7","♥"),Card("7","♦"),Card("7","♠")]  # Solo una carta para prueba
                    round.hands[jugador_local.playerId] = jugador_local.playerHand
                if roundFour:
                    jugador_local.playerHand = [Card("9","♥"), Card("9","♠"), Card("9","♦"), 
                                                Card("8","♥"), Card("8","♠"), Card("8","♦"), 
                                                Card("2","♥"), Card("3","♥"), Card("4","♥"), 
                                                Card("5","♥")]  # Solo una carta para prueba
                    round.hands[jugador_local.playerId] = jugador_local.playerHand'''
                # Limpiar zonas de cartas para todas las rondas
                zona_cartas[0] = []
                zona_cartas[0].clear()
                zona_cartas[1] = []
                zona_cartas[1].clear()
                if roundThree or roundFour:
                    zona_cartas[2] = []
                    zona_cartas[2].clear()

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
                if roundOne:
                    fase = "mostrar_orden"
                elif roundTwo:
                    fase = "ronda2"
                elif roundThree:
                    fase = "ronda3"
                elif roundFour:
                    fase = "ronda4"

                print(f" fase del juego>>> Ronda en realidad :)   {fase}")

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
                mano_restante = msg.get("playerHand")  # Lista de objetos Card
                jugadas_en_mesa = msg.get("jugadas_bajadas")  # Lista con las combinaciones (tríos/escaleras)
                Jugadas_en_mesa2 = msg.get("playMade")    ## Lista con las combinaciones (tríos/escaleras) en INGLES :D
                round = msg.get("round")

                print(f"Mensaje de BAJARSE recibido del Player ID: {player_id_que_se_bajo}")
                for p in players:
                    if p.playerId == player_id_que_se_bajo:
                        p.playerHand = mano_restante
                        p.jugadas_bajadas = jugadas_en_mesa
                        p.playMade = Jugadas_en_mesa2
                        try:
                            bajarse_sound.play()
                        except Exception as e:
                            print("Error al reproducir bajarse_sound:", e)
            
            elif isinstance(msg,dict) and msg.get("type")=="TOMAR_DESCARTE":
                player_id_que_tomoD = msg.get("playerId")
                mano_restante = msg.get("playerHand")  # Lista de objetos Card
                carta_tomada = msg.get("cardTakenD")  # Lista con las combinaciones (tríos/escaleras)
                mazo_de_descarte = msg.get("mazo_descarte")
                round = msg.get("round")
                
                bought = True

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
                
                # bought = True

                print(f"Mensaje de TOMAR CARTA recibido del Player ID: {player_id_que_tomoC}")
                for p in players:
                    if p.playerId == player_id_que_tomoC:
                        p.playerHand = mano_restante
                        p.playerPass = False
                        #pass
                cardTaken = carta_tomada
                deckForRound = mazoBocaAbajo #round.pile

            elif isinstance(msg,dict) and msg.get("type")=="PASAR_DESCARTE":
                mostrar_boton_comprar = True  

                player_id_que_pasoD = msg.get("playerId")
                player_name_que_pasoD = msg.get("playerName")

                waiting = True
                time_waiting = time.time()
                print(f"Waiting y time_waiting: ({waiting}, {time_waiting})")
                mostrar_boton_comprar = True  

                
                print(f"Mensaje de PASAR DESCARTE recibido del Player ID: {player_id_que_pasoD}")
                for p in players:
                    if p.playerId == player_id_que_pasoD:
                        p.playerPass = True

                if not jugador_local.isHand:
                    mostrar_boton_comprar = True  
                    mensaje_temporal = f"{player_name_que_pasoD} pasó del descarte. Compra habilitada temporalmente."
                    mensaje_tiempo = time.time()

            elif isinstance(msg,dict) and msg.get("type")=="INICIAR_COMPRA":
                player_id_que_compraC = msg.get("playerId")
                player_name_que_compraC = msg.get("playerName")
                next_idx_player_isHand = msg.get("next_idx_player_isHand")
                idx_player_jugador_local = msg.get("idx_player_jugador_local")
                print(f"Mensaje de INICIAR COMPRA recibido del Player ID: {player_id_que_compraC}")


                noBuy = False

                """ for i in range(next_idx_player_isHand, idx_player_jugador_local):
                    players[i].playerTurn = True """
                mensaje_temporal = f"{player_name_que_compraC} quiere comprar la carta."
                mensaje_tiempo = time.time()

            elif isinstance(msg,dict) and msg.get("type")=="FIN_CICLO_COMPRA":
                player_id_que_finalizoC = msg.get("playerId")
                
                print(f"Mensaje de FIN CICLO COMPRA recibido del Player ID: {player_id_que_finalizoC}")
                mostrar_boton_comprar = False  

                bought = True
                waiting = False
                time_waiting = None
                print(f"Waiting y time_waiting: ({waiting}, {time_waiting})")

                mensaje_temporal = "Tiempo de espera finalizado."
                mensaje_tiempo = time.time()

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
                
                noBuy = True
                bought = False
                waiting = False
                time_waiting = None
                print(f"Valor de bought: {bought}")

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
                mano_actualizada = msg.get("playerHand")
                player_id_que_compro = msg.get("playerId")
                player_name_que_compro = msg.get("playerName")
                mazo_de_descarte = msg.get("mazo_descarte")
                deck_for_round = msg.get("deckForRound")
                # mano_restante = msg.get("playerHand")  # Lista de objetos Card
                # cartasDescartadas = msg.get("cartas_descartadas")
                # players[:] = msg.get("players")
                received_round = msg.get("round")

                noBuy = True
                bought = True

                print(f"Mensaje de COMPRAR CARTA recibido del Player ID: {player_id_que_compro}")
                for p in players:
                    if p.playerId == player_id_que_compro:
                        p.playerHand = mano_actualizada
                        #p.playerHand = mano_restante
                        #???cartas_descartadas = cartasDescartadas
                        #mazo_descarte = mazo_de_descarte
                        #zona_cartas = zonaCartas
                
                if received_round:
                    round = received_round
                    deckForRound = round.pile
                    mazo_descarte = round.discards
                else:
                    print("Algo salio mal con la transmision de la compra, Houston...")

                mensaje_temporal = f"{player_name_que_compro} compro la carta."
                mensaje_tiempo = time.time()
            
            elif isinstance(msg, dict) and msg.get("type") == "INSERTAR_CARTA":
                mano_restante = msg.get("playerHand")
                jugadas_visuales = msg.get("jugadas_bajadas")
                jugadas_logicas = msg.get("playMade")
                id_target_player = msg.get("playerId")
                id_jugador_que_inserto = msg.get("playerId2")
                received_round = msg.get("round")

                for p in players:
                    if p.playerId == id_target_player:
                        p.jugadas_bajadas = jugadas_visuales
                        p.playMade = jugadas_logicas
                    if p.playerId == id_jugador_que_inserto:
                        p.playerHand = mano_restante


                
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
                        # Reproducir sonido al iniciar el arrastre
                        try:
                            carta_sound.play()
                        except Exception as e:
                            # Si falla la reproducción, no interrumpe el juego; registra en consola.
                            print("Error al reproducir carta_sound:", e)



                #Cambio Menu
                elif nombre == "Menú":
                    resultado = show_menu_modal(screen, WIDTH, HEIGHT, ASSETS_PATH)
                    if resultado == "resume":
                        pass  # simplemente se cierra el modal
                    elif resultado == "config":
                        print("Abrir configuración (modal futuro)")
                    elif resultado == "exit":
                        pygame.quit()
                #Cambio Menu



                elif nombre:
                    if nombre == "Tomar carta":

                        if not bought and jugador_local.isHand and not jugador_local.cardDrawn:

                            msgPasarD = {
                                    "type": "PASAR_DESCARTE",
                                    "playerId": jugador_local.playerId,
                                    "playerName": jugador_local.playerName
                            }

                            waiting = True
                            time_waiting = time.time()

                            mensaje_temporal = "Esperando decision de compra de los otros jugadores."
                            mensaje_tiempo = time.time()

                            if network_manager.is_host:
                                network_manager.broadcast_message(msgPasarD)
                            elif network_manager.player:
                                network_manager.sendData(msgPasarD)

                            # time.sleep(3)
                            # bought = True
                            break
                        elif jugador_local.cardDrawn and noBuy:
                            mensaje_temporal = "Ya tomaste una carta en este turno."
                            mensaje_tiempo = time.time()
                        elif not jugador_local.isHand and noBuy:
                            mensaje_temporal = "No puedes tomar cartas porque no es tu turno."
                            mensaje_tiempo = time.time()
                        elif noBuy and not waiting:
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
                            
                            jugador_local.playerPass = False

                            if network_manager.is_host:
                                network_manager.broadcast_message(msgTomarC)
                            elif network_manager.player:
                                network_manager.sendData(msgTomarC)
                        else:
                            mensaje_temporal = "Hay una compra activa en este momento. Toma del mazo cuando culmine."
                            mensaje_tiempo = time.time()
                    elif nombre == "Tomar descarte":
                        if jugador_local.cardDrawn:
                            mensaje_temporal = "Ya tomaste una carta."
                            mensaje_tiempo = time.time()
                        elif not jugador_local.isHand:
                            mensaje_temporal = "No puedes tomar cartas porque no es tu turno."
                            mensaje_tiempo = time.time()
                        elif bought:
                            mensaje_temporal = "No puedes tomar del mazo de descarte porque la carta se ha quemado."
                            mensaje_tiempo = time.time()
                        elif not waiting and round.discards and noBuy:
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
                            #cartas_ocultas.clear()


                            msgTomarDescarte = {
                                "type": "TOMAR_DESCARTE",
                                "cardTakenD": cardTakenD,
                                "playerHand": jugador_local.playerHand,
                                "playerId": jugador_local.playerId,
                                "mazo_descarte": mazo_descarte,
                                "round": round
                                }
                            
                            bought = True

                            if network_manager.is_host:
                                network_manager.broadcast_message(msgTomarDescarte)
                            elif network_manager.player:
                                network_manager.sendData(msgTomarDescarte)
                        else:
                            mensaje_temporal = "No puedes tomar el descarte mientras el ciclo de compra este activo."
                            mensaje_tiempo = time.time()

                    elif nombre == "Bajarse":
                        send = False # Para controlar el envío del mensaje de "BAJARSE"
                        resultado1 = []
                        resultado2 = []
                        resultado3 = []
                        if jugador_local.cardDrawn:
                            if roundOne:
                                resultado1 = jugador_local.isValidStraightF(zona_cartas[0])
                                resultado2 = jugador_local.isValidTrioF(zona_cartas[1])
                            elif roundTwo:
                                resultado1 = jugador_local.isValidStraightF(zona_cartas[0])
                                resultado2 = jugador_local.isValidStraightF(zona_cartas[1])

                            elif roundThree:
                                #resultado = jugador_local.getOff2(zona_cartas[0], zona_cartas[1])
                                resultado1 = jugador_local.isValidTrioF(zona_cartas[1])
                                resultado2 = jugador_local.isValidTrioF(zona_cartas[0])
                                resultado3 = jugador_local.isValidTrioF(zona_cartas[2])
                            elif roundFour:
                                resultado1 = jugador_local.isValidTrioF(zona_cartas[1])
                                resultado2 = jugador_local.isValidTrioF(zona_cartas[0])
                                resultado3 = jugador_local.isValidStraightF(zona_cartas[2])
                                '''SeguidillaRoundFour = [Card("2","♥"), Card("3","♥"), Card("4","♥"), 
                                                        Card("5","♥")]
                                SeguidillaRoundFour2 = SeguidillaRoundFour.copy()
                                TrioRoundFour = [Card("2","♦"), Card("2","♠"),Card("2","♠")] 

                                for c in SeguidillaRoundFour:
                                    jugador_local.playerHand.append(c) # Anexando Seguidilla para usar getOff
                                # Esperar nuevas zonas de cartas
                                print(f"zona[1]{zona_cartas[1]}")
                                resultado1 = jugador_local.getOff(SeguidillaRoundFour,zona_cartas[1])   # Solo valida la seguidilla Zona[0]
                                print(f"resultado1 {resultado1}")
                                if resultado1:
                                    jugador_local.downHand = False  # Para volver a usar el getOff
                                else: ##############
                                    for c in SeguidillaRoundFour:
                                        jugador_local.playerHand.remove(c)
                                
                                for c in SeguidillaRoundFour2:
                                    jugador_local.playerHand.append(c) # Anexando Trio para usar getOff
                                print(f"zona[0]{zona_cartas[0]}")
                                resultado2 = jugador_local.getOff(SeguidillaRoundFour2,zona_cartas[0])   # Solo valida la seguidilla Zona[1]        
                                print(f"resultado2 {resultado2}")
                                if resultado2:
                                    jugador_local.downHand = False  # Para volver a usar el getOff
                                else:
                                    for c in SeguidillaRoundFour2:
                                        jugador_local.playerHand.remove(c) # Anexando Trio para usar getOff
                                for c in TrioRoundFour:
                                    jugador_local.playerHand.append(c) # Anexando Trio para usar getOff
                                print(f"zona[2]{zona_cartas[2]}")
                                resultado3 = jugador_local.getOff( zona_cartas[2],TrioRoundFour)   # Solo valida la seguidilla Zona[1] 
                                print(f"resultado3 {resultado3}")       
                                if not resultado3:
                                    for c in TrioRoundFour:
                                        jugador_local.playerHand.remove(c) # Anexando Trio para usar getOff
                            cartas_ocultas.clear()'''
                            if resultado1 and resultado2 and roundOne:  #Para la primera ronda 
                                send = True
                                #trios_bajados, seguidillas_bajadas = resultado
                                # Guarda las jugadas bajadas en jugador_local.jugadas_bajadas
                                if not hasattr(jugador_local, "jugadas_bajadas"):
                                    jugador_local.jugadas_bajadas = []
                                if resultado1:
                                    jugador_local.jugadas_bajadas.append(zona_cartas[0])
                                if resultado2:
                                    jugador_local.jugadas_bajadas.append(zona_cartas[1])
                                for carta in zona_cartas[0]+ zona_cartas[1]:
                                    if carta in visual_hand:
                                        visual_hand.remove(carta)
                                        jugador_local.playerHand.remove(carta)
                                jugador_local.playMade.append(zona_cartas[0])
                                jugador_local.playMade.append(zona_cartas[1])
                                jugador_local.downHand =True
                                cartas_ocultas.clear()
                                zona_cartas[0] = []
                                zona_cartas[0].clear()
                                zona_cartas[1] = []
                                zona_cartas[1].clear()
                                #Eliminamos las cartas de los espacios visuales, para que desaparezcan al pulsar el botón de bajarse
                            
                            elif resultado1 and resultado2 and roundTwo:
                            #elif resultado1 and resultado2 and roundTwo:  #Para la segunda ronda 
                                send = True
                                #seguidillas_bajadas, seguidillas2_bajadas = resultado
                                #NoUsar , seguidillas_bajadas = resultado1
                                #NoUsar , seguidillas2_bajadas = resultado2 
                                
                                # Guarda las jugadas bajadas en jugador_local.jugadas_bajadas
                                if not hasattr(jugador_local, "jugadas_bajadas"):
                                    jugador_local.jugadas_bajadas = []
                                if resultado1:
                                    jugador_local.jugadas_bajadas.append(zona_cartas[0])
                                if resultado2:
                                    jugador_local.jugadas_bajadas.append(zona_cartas[1])
                                for carta in zona_cartas[0]+ zona_cartas[1]:
                                    if carta in visual_hand:
                                        visual_hand.remove(carta)
                                        jugador_local.playerHand.remove(carta)
                                jugador_local.playMade.append(zona_cartas[0])
                                jugador_local.playMade.append(zona_cartas[1])
                                jugador_local.downHand =True
                                cartas_ocultas.clear()
                                zona_cartas[0] = []
                                zona_cartas[0].clear()
                                zona_cartas[1] = []
                                zona_cartas[1].clear()
                            
                            elif resultado1 and resultado2 and resultado3 and roundThree:  #Para la tercera ronda 
                                send = True
                                if not hasattr(jugador_local, "jugadas_bajadas"):
                                    jugador_local.jugadas_bajadas = []
                                if resultado1:
                                    jugador_local.jugadas_bajadas.append(zona_cartas[1])
                                if resultado2:
                                    jugador_local.jugadas_bajadas.append(zona_cartas[0])
                                if resultado3:
                                    jugador_local.jugadas_bajadas.append(zona_cartas[2])
                                for carta in zona_cartas[1]+ zona_cartas[0] + zona_cartas[2]:
                                    if carta in visual_hand:
                                        visual_hand.remove(carta)
                                        jugador_local.playerHand.remove(carta)
                                jugador_local.playMade.append(zona_cartas[1])
                                jugador_local.playMade.append(zona_cartas[0])
                                jugador_local.playMade.append(zona_cartas[2])
                                jugador_local.downHand =True
                                cartas_ocultas.clear()
                                zona_cartas[0] = []
                                zona_cartas[0].clear()
                                zona_cartas[1] = []
                                zona_cartas[1].clear()
                                zona_cartas[2] = []
                                zona_cartas[2].clear()
                                
                                
                            elif resultado1 and resultado2 and resultado3 and roundFour and (len(zona_cartas[0])+len(zona_cartas[1])+len(zona_cartas[2]))==len(jugador_local.playerHand): 
                                send = True
                                if not hasattr(jugador_local, "jugadas_bajadas"):
                                    jugador_local.jugadas_bajadas = []
                                if resultado1:
                                    jugador_local.jugadas_bajadas.append(zona_cartas[1])
                                if resultado2:
                                    jugador_local.jugadas_bajadas.append(zona_cartas[0])
                                if resultado3:
                                    jugador_local.jugadas_bajadas.append(zona_cartas[2])
                                for carta in zona_cartas[1]+ zona_cartas[0] + zona_cartas[2]:
                                    if carta in visual_hand:
                                        visual_hand.remove(carta)
                                        jugador_local.playerHand.remove(carta)
                                jugador_local.playMade.append(zona_cartas[1])
                                jugador_local.playMade.append(zona_cartas[0])
                                jugador_local.playMade.append(zona_cartas[2])
                                jugador_local.downHand =True
                                cartas_ocultas.clear()
                                zona_cartas[0] = []
                                zona_cartas[0].clear()
                                zona_cartas[1] = []
                                zona_cartas[1].clear()
                                zona_cartas[2] = []
                                zona_cartas[2].clear()
                            else:
                                cartas_ocultas.clear()
                                zona_cartas[0] = []
                                zona_cartas[0].clear()
                                zona_cartas[1] = []
                                zona_cartas[1].clear()
                                if roundThree or roundFour:
                                    zona_cartas[2] = []
                                    zona_cartas[2].clear()
                            if not send and roundFour and jugador_local.cardDrawn:
                                mensaje_temporal = "En la Ronda 4 No te puedes bajar y quedar con cartas en la mano"
                                mensaje_tiempo = time.time()

                            # Actualiza visual_hand y permite organizar
                            visual_hand.clear()
                            for carta in jugador_local.playerHand:
                                visual_hand.append(carta)
                            reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                            organizar_habilitado = True
                            # Actualiza visual_hand y permite organizar
                            visual_hand.clear()
                            for carta in jugador_local.playerHand:
                                visual_hand.append(carta)
                            reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                            organizar_habilitado = True
                            #cartas_ocultas.clear()

                            msgBajarse = {
                                "type":"BAJARSE",
                                "playerHand": jugador_local.playerHand,
                                "jugadas_bajadas": jugador_local.jugadas_bajadas,
                                "playMade": jugador_local.playMade,
                                "playerId": jugador_local.playerId,
                                "round": round
                                }
                            if network_manager.is_host:
                                if msgBajarse and send:
                                    network_manager.broadcast_message(msgBajarse)
                                else: 
                                    print("Mensaje vacio... No enviado")
                            else:
                                if msgBajarse and send:
                                    network_manager.sendData(msgBajarse)
                                else: 
                                    print("Mensaje vacio... No enviado")
                        else:
                            mensaje_temporal = "Debes tomar una carta antes de bajarte."
                            mensaje_tiempo = time.time()
                            cartas_ocultas.clear()
                            zona_cartas[0] = []
                            zona_cartas[0].clear()
                            zona_cartas[1] = []
                            zona_cartas[1].clear()
                            if roundThree or roundFour:
                                    zona_cartas[2] = []
                                    zona_cartas[2].clear()
                    elif nombre in ("Descarte", "Descartar"):
                            # Determinar la carta seleccionada (click sobre Carta_x) o usar la zona de arrastre (zona_cartas[2])
                            selected_card = None
                            for key, rect in cuadros_interactivos.items():
                                if key.startswith("Carta_") and rect.collidepoint(event.pos):
                                    selected_card = cartas_ref.get(key)
                                    break
                            numero = 0
                            if roundOne or roundTwo:
                                numero = 2
                            elif roundThree or roundFour:
                                numero = 3
                            if len(zona_cartas[numero]) >= 1:
                                # si hay cartas arrastradas al área de descarte, úsalas
                                selected_cards = list(zona_cartas[numero])
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
                                zona_cartas[numero] = []
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
                                zona_cartas[numero] = []
                            elif not can_discard(jugador_local, cartas_descartadas) and len(jugador_local.playerHand) > 1:
                                mensaje_temporal = "No puedes descartar la carta que acabas de tomar."
                                mensaje_tiempo = time.time()
                                # devolver cartas a la mano si fue necesario
                                for c in cartas_descartadas:
                                    if c not in jugador_local.playerHand:
                                        jugador_local.playerHand.append(c)
                                cartas_ocultas.clear()
                                zona_cartas[numero] = []
                                # jugador_local.isHand = True
                            elif (jugador_local.isHand and jugador_local.canDiscard) or (not can_discard(jugador_local, cartas_descartadas) and len(jugador_local.playerHand) == 1):
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
                                cartas_ocultas.clear()

                                # Guarda la carta descartada en el mazo de descarte
                                for carta in cartas_descartadas:
                                    if len(cartas_descartadas) == 2 and hasattr(cartas_descartadas[1], "joker") and cartas_descartadas[1].joker:
                                        mazo_descarte.append(cartas_descartadas[1])
                                        mazo_descarte.append(cartas_descartadas[0])
                                        #break
                                    else:
                                        #mazo_descarte.append(carta)
                                        mazo_descarte = round.discards  #Luego de reiniciado el mazo, se duplicaron las cartas
                                zona_cartas[numero] = []
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

                                bought = False
                                noBuy = True

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
                        #CAMBIO 2
                        if not jugador_local.isHand: # El jugador MANO no puede comprar cartas...

                            if not bought:

                                jugador_mano_actual = [p for p in players if p.isHand][0] # Encontramos al jugador MANO actualmente
                            
                                print(f"MANO actual: {jugador_mano_actual}")
                                print(f"Valor de playerPass del MANO: {jugador_mano_actual.playerPass}")
                                if jugador_mano_actual.playerPass: # Verificamos el valor de "playerPass", para saber si la compra esta permitida.

                                    print(f"Valor de jugador_local: {jugador_local}")
                                    # Encontramos la posicion del jugador local en la lista de jugadores (el que activo la compra de cartas)
                                    indice_jugador_local = None
                                    for idx, player in enumerate(players):
                                        if player.playerId == jugador_local.playerId:
                                            indice_jugador_local = idx
                                            break
                                    
                                    # Buscamos la posicion del jugador MANO en la lista de jugadores y calculamos el indice que le sigue.
                                    indice_mano_actual = None
                                    siguiente_idx = None
                                    for idx, player in enumerate(players):
                                        if player.playerId == jugador_mano_actual.playerId:
                                            indice_mano_actual = idx
                                            siguiente_idx = (idx + 1) % len(players)
                                            break

                                    msgIniciarCompra = {
                                        "type": "INICIAR_COMPRA",
                                        "playerId": jugador_local.playerId,
                                        "playerName": jugador_local.playerName,
                                        "next_idx_player_isHand": siguiente_idx,
                                        "idx_player_jugador_local": indice_jugador_local
                                    }

                                    noBuy = False
                                    jugador_local.playerTurn = True

                                    if network_manager.is_host:
                                        network_manager.broadcast_message(msgIniciarCompra)
                                    else:
                                        network_manager.sendData(msgIniciarCompra)
                                    
                                    # Si no hay cartas en la pila de descartes, no se puede comprar nada.
                                    if not round.discards:
                                        mensaje_temporal = "No hay cartas para comprar en este momento."
                                        mensaje_tiempo = time.time()
                                        continue
                                    # Si el indice del jugador que viene luego del MANO coincide con el indice del jugador local, 
                                    # se sigue el proceso de compra sin mostrar la pantalla de confirmacion (tiene la maxima prioridad).
                                    elif siguiente_idx == indice_jugador_local and jugador_local.playerTurn:
                                        
                                        # Indicamos que el jugador compra la carta.
                                        jugador_local.playerBuy = True
                                        print(f"Pila antes de compra: {[c for c in round.pile]}")
                                        cards_bought = jugador_local.buyCard(round)
                                        print(f"Pila despues de compra: {[c for c in round.pile]}")
                                        # jugador_local.playerHand = round.hands[jugador_local.playerId]
                                        cartas_ocultas.clear()
                                        zona_cartas[2] = [] # Limpiamos la zona de descartes.
                                        print(f"Mano del jugador que compro: {jugador_local.playerHand}")
                                        
                                        # players[indice_mano_actual].playerPass = False
                                        players[indice_mano_actual].isHand = True
                                        players[indice_jugador_local].isHand = False
                                        print("Se reseteo el valor de playerPass del MANO a False.")

                                        for idx, carta in enumerate(jugador_local.playerHand):
                                            carta.id_visual = idx
                                            visual_hand.append(carta)

                                        reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                                        mazo_descarte = round.discards
                                        deckForRound = round.pile

                                        msgComprarC = {
                                                "type": "COMPRAR_CARTA",
                                                # "cartas_descartadas": cartas_descartadas,
                                                "playerHand": jugador_local.playerHand,
                                                "playerId": jugador_local.playerId,
                                                "playerName": jugador_local.playerName,
                                                "mazo_descarte": mazo_descarte,#  El mazo se debe actualizar
                                                "deckForRound": deckForRound,
                                                "zona_cartas": zona_cartas,
                                                # "players": players,
                                                "round": round
                                        }

                                        noBuy = True
                                        bought = True

                                        if network_manager.is_host:
                                            network_manager.broadcast_message(msgComprarC)
                                        else:
                                            network_manager.sendData(msgComprarC)
                                    elif jugador_local.playerTurn:
                                        pass
                                        """ for i in range(1, len(players)):
                                            pass

                                        card_to_show = mazo_descarte[-1] if mazo_descarte else None
                                        wants = confirm_buy_card(screen, card_to_show, WIDTH, HEIGHT, ASSETS_PATH, font) """
                                    else:
                                        mensaje_temporal = "Un jugador mas cercano al MANO quiere comprar."
                                        mensaje_tiempo = time.time()
                                        continue
                                else:
                                    mensaje_temporal = "El jugador MANO aún no ha elegido una carta."
                                    mensaje_tiempo = time.time()
                                    continue
                            else:
                                mensaje_temporal = "El ciclo de compra ha finalizado."
                                mensaje_tiempo = time.time()
                                continue
                        else:
                            mensaje_temporal = "Botón inhabilitado: eres el jugador MANO."
                            mensaje_tiempo = time.time()
                            continue

                        wants = False
                        if wants:                        
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

                                """ # Creo que no está la lógica para comprar la Carta... para comprar, No debe ser su turno... 
                                msgComprarC = {
                                    "type": "COMPRAR_CARTA",
                                    #?    "cartas_descartadas": cartas_descartadas,
                                        "playerHand": jugador_local.playerHand,
                                        "playerId": jugador_local.playerId,
                                        "mazo_descarte": mazo_descarte,#  El mazo se debe actualizar
                                        "zona_cartas": zona_cartas,
                                        "round": round
                                    }
                                if network_manager.is_host:
                                    network_manager.broadcast_message(msgComprarC)
                                else:
                                    network_manager.sendData(msgComprarC) """
                            else: 
                            # El jugador eligió no comprar: no hacemos nada
                                pass
                    #CAMBIO 2
            
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

                    # Detectar si se soltó sobre una caja de "bajada" (baj1..baj7)
                    drop_bajada = None
                    for nombre_box, rect_box in boxes.items():
                        if nombre_box.startswith("baj") and rect_box.collidepoint(mouse_x, mouse_y):
                            drop_bajada = nombre_box
                            break

                    # Resolver jugador objetivo consultando el mapeo baj_box_to_player (construido arriba)
                    def player_for_bajada(baj_name):
                        if not baj_name:
                            return None, None
                        target_player = baj_box_to_player.get(baj_name)
                        if target_player:
                            try:
                                idx = players.index(target_player)
                                return target_player, idx
                            except ValueError:
                                return target_player, None
                        # fallback por índice si no está en el mapa
                        try:
                            idx = int(baj_name[3:]) - 1
                            if 0 <= idx < len(players):
                                return players[idx], idx
                        except Exception:
                            pass
                        return None, None


                    # Normalizar carta a objeto Card
                    carta_obj = string_to_card(carta_arrastrada)
                    send = False

                    if drop_bajada:
                        eleccion = choose_insert_target_modal(screen, WIDTH, HEIGHT, ASSETS_PATH, fase)
                        if eleccion is None:
                            mensaje_temporal = ""
                            mensaje_tiempo = time.time()
                        else:
                            target_player, target_idx = player_for_bajada(drop_bajada)
                            if not target_player:
                                mensaje_temporal = "Jugador objetivo no encontrado."
                                mensaje_tiempo = time.time()
                            else:
                                # --- TRIOS ---
                                if "Trio" in eleccion:  # cualquier trio seleccionado
                                    target_subtype = "trio"
                                    # elegir índice según el número de trío seleccionado y la ronda
                                    plays = getattr(target_player, "playMade", [])
                                    if plays:
                                        if fase == "ronda3":
                                            if eleccion == "Trio 1":
                                                play_index = 0
                                            elif eleccion == "Trio 2":
                                                play_index = 1
                                            elif eleccion == "Trio 3":
                                                play_index = 2
                                        elif fase == "ronda4":
                                            if eleccion == "Trio 1":
                                                play_index = 0
                                            elif eleccion == "Trio 2":
                                                play_index = 1
                                        else:
                                            play_index = len(plays) - 1
                                    else:
                                        play_index = 0

                                    ok = safe_insert_card(jugador_local, target_player, play_index, carta_obj, "end", target_subtype)
                                    if ok:
                                        send = True
                                        #if carta_arrastrada in visual_hand:
                                        #   visual_hand.remove(carta_arrastrada)
                                        reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                                        mensaje_temporal = f"Carta insertada en {eleccion}."
                                        msgInsertar = {
                                        "type":"INSERTAR_CARTA",
                                        "playerHand": jugador_local.playerHand,
                                        "jugadas_bajadas": target_player.jugadas_bajadas,
                                        "playMade": target_player.playMade,
                                        "playerId": target_player.playerId,
                                        "playerId2": jugador_local.playerId,
                                        "round": round
                                        }
                                        if network_manager.is_host:
                                            if msgInsertar and send:
                                                network_manager.broadcast_message(msgInsertar)
                                            else: 
                                                print("Mensaje vacio... No enviado")
                                        else:
                                            if msgInsertar and send:
                                                network_manager.sendData(msgInsertar)
                                            else: 
                                                print("Mensaje vacio... No enviado")
                                    else:
                                        mensaje_temporal = f"No se pudo insertar en {eleccion}."
                                    mensaje_tiempo = time.time()

                                # --- SEGUIDILLAS ---
                                elif "Seguidilla" in eleccion:
                                    target_subtype = "straight"
                                    straight_accion = straight_choice_modal(screen, WIDTH, HEIGHT, ASSETS_PATH)
                                    
                                    plays = getattr(target_player, "playMade", [])
                                    # elegir índice según la seguidilla seleccionada (si hay más de una)
                                    if plays:
                                        if fase == "ronda2" and eleccion == "Seguidilla 1":
                                            play_index = 1
                                        elif fase == "ronda2" and eleccion == "Seguidilla 2":
                                            play_index = 0
                                        elif fase == "ronda1":
                                            play_index = 0
                                        else:
                                            play_index = len(plays) - 1
                                    else:
                                        play_index = 0

                                    if straight_accion == "start":
                                        ok = safe_insert_card(jugador_local, target_player, play_index, carta_obj, "start", target_subtype)
                                        if ok:
                                            send = True
                                            if carta_arrastrada in visual_hand:
                                                visual_hand.remove(carta_arrastrada)
                                            reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                                            mensaje_tiempo = time.time()
                                            mensaje_temporal = "Insertado al Inicio de la seguidilla."
                                            msgInsertar = {
                                            "type":"INSERTAR_CARTA",
                                            "playerHand": jugador_local.playerHand,
                                            "jugadas_bajadas": target_player.jugadas_bajadas,
                                            "playMade": target_player.playMade,
                                            "playerId": target_player.playerId,
                                            "playerId2": jugador_local.playerId,
                                            "round": round
                                            }
                                            if network_manager.is_host:
                                                if msgInsertar and send:
                                                    network_manager.broadcast_message(msgInsertar)
                                                else: 
                                                    print("Mensaje vacio... No enviado")
                                            else:
                                                if msgInsertar and send:
                                                    network_manager.sendData(msgInsertar)
                                                else: 
                                                    print("Mensaje vacio... No enviado")
                                        else:
                                            mensaje_tiempo = time.time()
                                            mensaje_temporal = "No se pudo insertar al Inicio de la seguidilla."
                                    elif straight_accion == "end":
                                        ok = safe_insert_card(jugador_local, target_player, play_index, carta_obj, "end", target_subtype)
                                        if ok:
                                            send = True
                                            if carta_arrastrada in visual_hand:
                                                visual_hand.remove(carta_arrastrada)
                                            reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                                            mensaje_tiempo = time.time()
                                            mensaje_temporal = "Insertado al Final de la seguidilla."
                                            msgInsertar = {
                                            "type":"INSERTAR_CARTA",
                                            "playerHand": jugador_local.playerHand,
                                            "jugadas_bajadas": target_player.jugadas_bajadas,
                                            "playMade": target_player.playMade,
                                            "playerId": target_player.playerId,
                                            "playerId2": jugador_local.playerId,
                                            "round": round
                                            }
                                            if network_manager.is_host:
                                                if msgInsertar and send:
                                                    network_manager.broadcast_message(msgInsertar)
                                                else: 
                                                    print("Mensaje vacio... No enviado")
                                            else:
                                                if msgInsertar and send:
                                                    network_manager.sendData(msgInsertar)
                                                else: 
                                                    print("Mensaje vacio... No enviado")
                                        else:
                                            mensaje_tiempo = time.time()
                                            mensaje_temporal = "No se pudo insertar al Final de la seguidilla."
                                    elif straight_accion == "replace_joker":
                                        ok = safe_insert_card(jugador_local, target_player, play_index, carta_obj, None, target_subtype)
                                        if ok:
                                            send = True
                                            if carta_arrastrada in visual_hand:
                                                visual_hand.remove(carta_arrastrada)
                                            reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                                            mensaje_tiempo = time.time()
                                            mensaje_temporal = "Sustitución de Joker en seguidilla realizada."
                                            msgInsertar = {
                                            "type":"INSERTAR_CARTA",
                                            "playerHand": jugador_local.playerHand,
                                            "jugadas_bajadas": target_player.jugadas_bajadas,
                                            "playMade": target_player.playMade,
                                            "playerId": target_player.playerId,
                                            "playerId2": jugador_local.playerId,
                                            "round": round
                                            }
                                            if network_manager.is_host:
                                                if msgInsertar and send:
                                                    network_manager.broadcast_message(msgInsertar)
                                                else: 
                                                    print("Mensaje vacio... No enviado")
                                            else:
                                                if msgInsertar and send:
                                                    network_manager.sendData(msgInsertar)
                                                else: 
                                                    print("Mensaje vacio... No enviado")
                                        else:
                                            mensaje_tiempo = time.time()
                                            mensaje_temporal = "No se pudo sustituir el Joker de la seguidilla."
                                    else:
                                        mensaje_tiempo = time.time()
                                        mensaje_temporal = "Operación Seguidilla cancelada."
                                        ok = False

                                    if ok:
                                        #if carta_arrastrada in visual_hand:
                                         #   visual_hand.remove(carta_arrastrada)
                                        reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)

                                    mensaje_tiempo = time.time()
                        # No tocar zona_cartas ni cartas_ocultas aquí; safe_insert_card ya maneja lógica real
                    else:
                        # Mantener la lógica previa para mesa/insert en jugadas (sin cambios)
                        trio_rect = cuadros_interactivos.get("Trio")
                        seguidilla_rect = cuadros_interactivos.get("Seguidilla")
                        descarte_rect = cuadros_interactivos.get("Descarte")

                        insertado_en_jugada = False
                        # Intentar insertar en jugadas de cada jugador (inicio/final o reemplazo de Joker)
                        for jugador, jugadas in rects_jugadas.items():
                            if insertado_en_jugada:
                                break
                            for idx_jugada, jugada in enumerate(jugadas):
                                if jugada["inicio"].collidepoint(mouse_x, mouse_y):
                                    target_player = next((p for p in players if p.playerName == jugador), None)
                                    if target_player:
                                        ok = safe_insert_card(jugador_local, target_player, jugada.get("play_index", idx_jugada), string_to_card(carta_arrastrada), "start")
                                        if ok:
                                            if carta_arrastrada in visual_hand:
                                                visual_hand.remove(carta_arrastrada)
                                            reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                                        else:
                                            mensaje_temporal = "Error al insertar en inicio. ."
                                            mensaje_tiempo = time.time()
                                    insertado_en_jugada = True
                                    break
                                elif jugada["final"].collidepoint(mouse_x, mouse_y):
                                    target_player = next((p for p in players if p.playerName == jugador), None)
                                    if target_player:
                                        ok = safe_insert_card(jugador_local, target_player, jugada.get("play_index", idx_jugada), string_to_card(carta_arrastrada), "end")
                                        if ok:
                                            if carta_arrastrada in visual_hand:
                                                visual_hand.remove(carta_arrastrada)
                                            reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                                        else:
                                            mensaje_temporal = "Error al insertar en final. ."
                                            mensaje_tiempo = time.time()
                                    insertado_en_jugada = True
                                    break
                                else:
                                    # detección de sustitución de Joker (igual que antes)
                                    cartas_jugada = jugada.get("cartas", [])
                                    if not cartas_jugada:
                                        continue
                                    bloque_nombre = None
                                    for idx_p, p in enumerate(players):
                                        if p.playerName == jugador:
                                            bloque_nombre = {0:"baj1",1:"baj2",2:"baj3",3:"baj4",4:"baj5",5:"baj6",6:"baj7"}.get(idx_p)
                                            break
                                    bloque_rect = boxes.get(bloque_nombre)
                                    if not bloque_rect:
                                        continue
                                    if bloque_nombre in ["baj2","baj3","baj6","baj7"]:
                                        # vertical / rotada
                                        card_width = int(bloque_rect.width * 0.45)
                                        card_height = int(card_width / 0.68)
                                        solapamiento = int(card_height * 0.55) if len(cartas_jugada) > 1 else 0
                                        x = bloque_rect.x + (bloque_rect.width - card_height) // 2
                                        y = jugada["inicio"].y
                                        for i, carta in enumerate(cartas_jugada):
                                            card_rect = pygame.Rect(x, y + i * solapamiento, card_height, card_width)
                                            if hasattr(carta, "joker") and carta.joker and card_rect.collidepoint(mouse_x, mouse_y):
                                                target_player = next((p for p in players if p.playerName == jugador), None)
                                                if target_player:
                                                    ok = safe_insert_card(jugador_local, target_player, jugada.get("play_index", idx_jugada), string_to_card(carta_arrastrada), None)
                                                    if ok:
                                                        if carta_arrastrada in visual_hand:
                                                            visual_hand.remove(carta_arrastrada)
                                                        reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                                                    else:
                                                        mensaje_temporal = "Error al sustituir Joker. ."
                                                        mensaje_tiempo = time.time()
                                                insertado_en_jugada = True
                                                break
                                    else:
                                        # horizontal
                                        card_height = bloque_rect.height - 8
                                        card_width = int(card_height * 0.68)
                                        solapamiento = int(card_width * 0.65) if len(cartas_jugada) > 1 else 0
                                        x = jugada["inicio"].x
                                        y = bloque_rect.y + (bloque_rect.height - card_height) // 2 - 18
                                        for i, carta in enumerate(cartas_jugada):
                                            card_rect = pygame.Rect(x + i * solapamiento, y, card_width, card_height)
                                            if hasattr(carta, "joker") and carta.joker and card_rect.collidepoint(mouse_x, mouse_y):
                                                target_player = next((p for p in players if p.playerName == jugador), None)
                                                if target_player:
                                                    ok = safe_insert_card(jugador_local, target_player, jugada.get("play_index", idx_jugada), string_to_card(carta_arrastrada), None)
                                                    if ok:
                                                        if carta_arrastrada in visual_hand:
                                                            visual_hand.remove(carta_arrastrada)
                                                        reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref)
                                                    else:
                                                        mensaje_temporal = "Error al sustituir Joker. ."
                                                        mensaje_tiempo = time.time()
                                                insertado_en_jugada = True
                                                break
                                if insertado_en_jugada:
                                    break

                        # 3) Si no se insertó en jugada, chequear zonas Trio/Seguidilla/Descarte centrales
                        if not insertado_en_jugada:
                            # PRIORIDAD: zona central interactiva (cuadro que creaste)
                            zona_central = cuadros_interactivos.get("ZonaCentralInteractiva")
                            if zona_central and zona_central.collidepoint(mouse_x, mouse_y):
                                # asegurar al menos 4 ranuras
                                while len(zona_cartas) < 4:
                                    zona_cartas.append([])
                                zona_cartas[-1].append(carta_arrastrada)
                                if carta_arrastrada in visual_hand:
                                    cartas_ocultas.add(visual_hand.index(carta_arrastrada))
                                organizar_habilitado = False
                                print("DEBUG after drop -> zona_cartas (zona central):", [[str(c) for c in z] for z in zona_cartas])
                            else:
                                if trio_rect and trio_rect.collidepoint(mouse_x, mouse_y):
                                    zona_cartas[1].append(carta_arrastrada)
                                    if carta_arrastrada in visual_hand:
                                        cartas_ocultas.add(visual_hand.index(carta_arrastrada))
                                    organizar_habilitado = False
                                elif seguidilla_rect and seguidilla_rect.collidepoint(mouse_x, mouse_y):
                                    zona_cartas[0].append(carta_arrastrada)
                                    if carta_arrastrada in visual_hand:
                                        cartas_ocultas.add(visual_hand.index(carta_arrastrada))
                                    organizar_habilitado = False
                                elif descarte_rect and descarte_rect.collidepoint(mouse_x, mouse_y):
                                    zona_cartas[2].append(carta_arrastrada)
                                    if carta_arrastrada in visual_hand:
                                        cartas_ocultas.add(visual_hand.index(carta_arrastrada))
                                    organizar_habilitado = False
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
                                

                # siempre limpiar arrastre
                dragging = False
                carta_arrastrada = None
                drag_rect = None
                try:
                    print("DEBUG drag end -> zona_cartas:", [[str(c) for c in z] for z in zona_cartas])
                except Exception:
                    print("DEBUG drag end -> zona_cartas (raw):", zona_cartas)
            elif event.type == pygame.MOUSEMOTION and dragging:
                pass  # El dibujo se maneja abajo
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Click derecho
                for zona in zona_cartas:
                    for carta in zona:
                        if carta not in visual_hand:
                            visual_hand.append(carta)
                zona_cartas = [[], [], [],[]]
                cartas_ocultas.clear()
                organizar_habilitado = True  # Vuelve a habilitar organización
        # Fin evento de pygame...
        if waiting and (time.time() - time_waiting) > 4 and noBuy:
            print(f"Temporizador, waiting, time_waiting, noBuy: ({waiting}, {time_waiting}, {noBuy})")

            if jugador_local.isHand:

                msgFinCicloCompra = {
                                    "type": "FIN_CICLO_COMPRA",
                                    "playerId": jugador_local.playerId,
                }

                print("FINALIZO EL TIEMPO, VALEEEEE!")

                bought = True
                waiting = False
                time_waiting = None

                if network_manager.is_host:
                    network_manager.broadcast_message(msgFinCicloCompra)
                elif network_manager.player:
                    network_manager.sendData(msgFinCicloCompra)

                mensaje_temporal = "Espera finalizada. Vuelve a hacer click en el mazo para tomar una carta."
                mensaje_tiempo = time.time()

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
        #screen.blit(fondo_img, (0, 0))

        # Fondo Joker temporal
        if mostrar_joker_fondo and pygame.time.get_ticks() - tiempo_joker_fondo < 3000:
            screen.blit(joker_fondo_img, (0, 0))
        else:
            mostrar_joker_fondo = False
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
        start_x = (WIDTH - total_width) // 2 - 30
        cuadro_y = (HEIGHT - cuadro_h) // 2

        # Usar exactamente el mismo tamaño que las casillas (cuadro_w_carta, cuadro_h_carta)
        card_w = cuadro_w_carta
        card_h = cuadro_h_carta
        # Ajusta este valor para mover más/menos a la derecha
        despl_x = 120
        # Crear rect central del mismo tamaño que una casilla (sin overlay visible)
        # Habilitar la zona central SOLO en Ronda 3 o Ronda 4
        enabled_zone = False
        if 'roundThree' in globals() or 'roundFour' in globals():
            enabled_zone = bool(globals().get('roundThree')) or bool(globals().get('roundFour'))
        else:
            enabled_zone = (globals().get('fase') in ("ronda3", "ronda4"))

        if enabled_zone:
            zona_central_rect = pygame.Rect(
                start_x + (total_width - cuadro_w_carta) // 2 + despl_x,
                cuadro_y + (cuadro_h - cuadro_h_carta) // 2,
                cuadro_w_carta,
                cuadro_h_carta
            )
            cuadros_interactivos["ZonaCentralInteractiva"] = zona_central_rect
        else:
            # asegurar que no quede definida si no está habilitada
            cuadros_interactivos.pop("ZonaCentralInteractiva", None)
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
        bajarse_visible = mostrar_boton_bajarse  
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
            x_descarte,   # posición X del botón
            boton_y,      # posición Y del botón
            boton_w_fino, # ancho
            boton_h       # alto
        )
        descartar_visible = mostrar_boton_descartar
        if descartar_visible:
            descartar_img_path = os.path.join(ASSETS_PATH, "descartar.png")
            if os.path.exists(descartar_img_path):
                descartar_img = pygame.image.load(descartar_img_path).convert_alpha()
                img = pygame.transform.smoothscale(descartar_img, (boton_w_fino, boton_h))
                screen.blit(img, descartar_rect.topleft)
            else:
                draw_transparent_rect(screen, (180, 180, 220, 110), descartar_rect, border=1)
                draw_label(descartar_rect, "Descartar")
            cuadros_interactivos["Descartar"] = descartar_rect
        else:
            cuadros_interactivos.pop("Descartar", None)
        
        if mostrar_boton_comprar:
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
        else:
            # Si la flag es False, removemos el botón de los interactivos
            cuadros_interactivos.pop("Comprar carta", None)
        # --- Cuadros: Trio, Seguidilla, Descarte, Tomar descarte, Tomar carta (todos alineados y centrados verticalmente) ---
        combinaciones_requeridas = []
        if fase == "ronda1":
            combinaciones_requeridas = ["Trio", "Seguidilla"]
        if fase == "ronda2":
            combinaciones_requeridas = ["Seguidilla", "Seguidilla"]
        if fase == "ronda3":
            combinaciones_requeridas = ["Trio","Trio","Trio"]
        if fase == "ronda4":
            combinaciones_requeridas = ["Trio","Trio", "Seguidilla"]

        textos = combinaciones_requeridas + ["Descarte", "Tomar descarte", "Tomar carta"]
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
        cuadros_interactivos["Trio"] = pygame.Rect(x_trio, cuadro_y, cuadro_w_carta, cuadro_h)
        cuadros_interactivos["Seguidilla"] = pygame.Rect(x_seguidilla, cuadro_y, cuadro_w_carta, cuadro_h)
        cuadros_interactivos["Descarte"] = pygame.Rect(x_descarte, cuadro_y, cuadro_w_carta, cuadro_h)

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
        # --- Izquierda (Jugadores 2 y 3) ---
        # --- Derecha (Jugadores 6 y 7) ---
        # --- Arriba (Jugadores 4 y 5) ---

        if len(players) == 2:
            if jugador_local == players[0]:
                jugadores_laterales.append((players[1], jug2))
            elif jugador_local == players[1]:
                jugadores_laterales.append((players[0], jug7))
        if len(players) == 3:
            if jugador_local == players[0]:
                jugadores_laterales.append((players[1], jug2))
                jugadores_laterales.append((players[2], jug3))
            elif jugador_local == players[1]:
                jugadores_laterales.append((players[2], jug2))
                jugadores_laterales.append((players[0], jug7))
            elif jugador_local == players[2]:
                jugadores_laterales.append((players[0], jug6))
                jugadores_laterales.append((players[1], jug7))
        if len(players) == 4:
            if jugador_local == players[0]:
                jugadores_laterales.append((players[1], jug2))
                jugadores_laterales.append((players[2], jug3))
                jugadores_superiores.append((players[3], jug4))
            elif jugador_local == players[1]:
                jugadores_laterales.append((players[2], jug2))
                jugadores_laterales.append((players[3], jug3))
                jugadores_laterales.append((players[0], jug7))
            elif jugador_local == players[2]:
                jugadores_laterales.append((players[3], jug2))
                jugadores_laterales.append((players[0], jug6))
                jugadores_laterales.append((players[1], jug7))
            elif jugador_local == players[3]:
                jugadores_superiores.append((players[0], jug5))
                jugadores_laterales.append((players[1], jug6))
                jugadores_laterales.append((players[2], jug7))
        if len(players) == 5:
            if jugador_local == players[0]:
                jugadores_laterales.append((players[1], jug2))
                jugadores_laterales.append((players[2], jug3))
                jugadores_superiores.append((players[3], jug4))
                jugadores_superiores.append((players[4], jug5))
            elif jugador_local == players[1]:
                jugadores_laterales.append((players[2], jug2))
                jugadores_laterales.append((players[3], jug3))
                jugadores_superiores.append((players[4], jug4))
                jugadores_laterales.append((players[0], jug7))
            elif jugador_local == players[2]:
                jugadores_laterales.append((players[3], jug2))
                jugadores_laterales.append((players[4], jug3))
                jugadores_laterales.append((players[0], jug6))
                jugadores_laterales.append((players[1], jug7))
            elif jugador_local == players[3]:
                jugadores_laterales.append((players[4], jug2))
                jugadores_superiores.append((players[0], jug5))
                jugadores_laterales.append((players[1], jug6))
                jugadores_laterales.append((players[2], jug7))
            elif jugador_local == players[4]:
                jugadores_superiores.append((players[0], jug4))
                jugadores_superiores.append((players[1], jug5))
                jugadores_laterales.append((players[2], jug6))
                jugadores_laterales.append((players[3], jug7))
        if len(players) == 6:
            if jugador_local == players[0]:
                jugadores_laterales.append((players[1], jug2))
                jugadores_laterales.append((players[2], jug3))
                jugadores_superiores.append((players[3], jug4))
                jugadores_superiores.append((players[4], jug5))
                jugadores_laterales.append((players[5], jug6))
            elif jugador_local == players[1]:
                jugadores_laterales.append((players[2], jug2))
                jugadores_laterales.append((players[3], jug3))
                jugadores_superiores.append((players[4], jug4))
                jugadores_superiores.append((players[5], jug5))
                jugadores_laterales.append((players[0], jug7))
            elif jugador_local == players[2]:
                jugadores_laterales.append((players[3], jug2))
                jugadores_laterales.append((players[4], jug3))
                jugadores_superiores.append((players[5], jug4))
                jugadores_laterales.append((players[0], jug6))
                jugadores_laterales.append((players[1], jug7))
            elif jugador_local == players[3]:
                jugadores_laterales.append((players[4], jug2))
                jugadores_laterales.append((players[5], jug3))
                jugadores_superiores.append((players[0], jug5))
                jugadores_laterales.append((players[1], jug6))
                jugadores_laterales.append((players[2], jug7))
            elif jugador_local == players[4]:
                jugadores_laterales.append((players[5], jug2))
                jugadores_superiores.append((players[0], jug4))
                jugadores_superiores.append((players[1], jug5))
                jugadores_laterales.append((players[2], jug6))
                jugadores_laterales.append((players[3], jug7))
            elif jugador_local == players[5]:
                jugadores_laterales.append((players[0], jug3))
                jugadores_superiores.append((players[1], jug4))
                jugadores_superiores.append((players[2], jug5))
                jugadores_laterales.append((players[3], jug6))
                jugadores_laterales.append((players[4], jug7))
        if len(players) == 7:
            if jugador_local == players[0]:
                jugadores_laterales.append((players[1], jug2))
                jugadores_laterales.append((players[2], jug3))
                jugadores_superiores.append((players[3], jug4))
                jugadores_superiores.append((players[4], jug5))
                jugadores_laterales.append((players[5], jug6))
                jugadores_laterales.append((players[6], jug7))
            elif jugador_local == players[1]:
                jugadores_laterales.append((players[2], jug2))
                jugadores_laterales.append((players[3], jug3))
                jugadores_superiores.append((players[4], jug4))
                jugadores_superiores.append((players[5], jug5))
                jugadores_laterales.append((players[6], jug6))
                jugadores_laterales.append((players[0], jug7))
            elif jugador_local == players[2]:
                jugadores_laterales.append((players[3], jug2))
                jugadores_laterales.append((players[4], jug3))
                jugadores_superiores.append((players[5], jug4))
                jugadores_superiores.append((players[6], jug5))
                jugadores_laterales.append((players[0], jug6))
                jugadores_laterales.append((players[1], jug7))
            elif jugador_local == players[3]:
                jugadores_laterales.append((players[4], jug2))
                jugadores_laterales.append((players[5], jug3))
                jugadores_superiores.append((players[6], jug4))
                jugadores_superiores.append((players[0], jug5))
                jugadores_laterales.append((players[1], jug6))
                jugadores_laterales.append((players[2], jug7))
            elif jugador_local == players[4]:
                jugadores_laterales.append((players[5], jug2))
                jugadores_laterales.append((players[6], jug3))
                jugadores_superiores.append((players[0], jug4))
                jugadores_superiores.append((players[1], jug5))
                jugadores_laterales.append((players[2], jug6))
                jugadores_laterales.append((players[3], jug7))
            elif jugador_local == players[5]:
                jugadores_laterales.append((players[6], jug2))
                jugadores_laterales.append((players[0], jug3))
                jugadores_superiores.append((players[1], jug4))
                jugadores_superiores.append((players[2], jug5))
                jugadores_laterales.append((players[3], jug6))
                jugadores_laterales.append((players[4], jug7))
            elif jugador_local == players[6]:
                jugadores_laterales.append((players[0], jug2))
                jugadores_laterales.append((players[1], jug3))
                jugadores_superiores.append((players[2], jug4))
                jugadores_superiores.append((players[3], jug5))
                jugadores_laterales.append((players[4], jug6))
                jugadores_laterales.append((players[5], jug7))
        

        # Dibuja solo los jugadores activos en los recuadros correspondientes
        # Dibuja solo los jugadores activos en los recuadros correspondientes
        for jugador, recuadro in jugadores_laterales:
            draw_horizontal_rain_hand_rotated(jugador, recuadro)

        for jugador, recuadro in jugadores_superiores:
            draw_horizontal_pt_hand(jugador, recuadro)
        # ===== Construir mapeo caja_de_bajada -> jugador =====
        # Esto asegura que la zona de arrastre (bajN) esté vinculada al jugador correcto
        baj_box_to_player = {}
        # jugador_local siempre a baj1 si existe
        if jugador_local:
            baj_box_to_player["baj1"] = jugador_local
        # Buscar por rects asociados (jugX -> bajX)
        for p, r in jugadores_laterales + jugadores_superiores:
            # encontrar clave 'jugN' en boxes cuyo rect sea r
            jug_key = next((k for k, v in boxes.items() if v == r and k.startswith("jug")), None)
            if jug_key:
                baj_key = jug_key.replace("jug", "baj")
                baj_box_to_player[baj_key] = p
        # fallback: mapear por índice en players si alguna bajX no mapeó
        for idx, p in enumerate(players):
            key = f"baj{idx+1}"
            if key not in baj_box_to_player and key in boxes:
                baj_box_to_player[key] = p

        BASE_NOMBRE_SIZE = 14
        BASE_PUNTOS_SIZE = 11

        def get_fitting_font(text, max_width, base_size, min_size=8):
            """
            Devuelve una pygame.font.Font cuyo tamaño se va reduciendo desde base_size
            hasta que el ancho del texto cabe en max_width (o llega a min_size).
            """
            size = base_size
            font = get_game_font(size)
            # medir con render (color cualquiera)
            width = font.render(text, True, (0,0,0)).get_width()
            while width > max_width and size > min_size:
                size -= 1
                font = get_game_font(size)
                width = font.render(text, True, (0,0,0)).get_width()
            return font

        # font por defecto para casos donde no se aplique ajuste directo
        # --- Después de dibujar manos, cartas y elementos (justo antes de dibujar nombres) ---
        # Tomar snapshot del screen tal y como están las cartas / UI detrás de los nombres
        try:
            pre_names_snapshot = screen.copy()
        except Exception:
            pre_names_snapshot = None

        BASE_NOMBRE_SIZE = 14
        BASE_PUNTOS_SIZE = 11

        def get_fitting_font(text, max_width, base_size, min_size=8):
            """Devuelve pygame.font.Font cuyo tamaño se reduce pixel a pixel hasta caber."""
            size = base_size
            font = get_game_font(size)
            width = font.render(text, True, (0,0,0)).get_width()
            while width > max_width and size > min_size:
                size -= 1
                font = get_game_font(size)
                width = font.render(text, True, (0,0,0)).get_width()
            return font

        # font por defecto
        font_nombre = get_game_font(BASE_NOMBRE_SIZE)
        font_puntos = get_game_font(BASE_PUNTOS_SIZE)

        def draw_text_with_border(surface, text, font, pos, color=(255,255,255), border_color=(0,0,0)):
            """Dibuja texto con borde (8 direcciones)."""
            x, y = pos
            # render de borde una sola vez por dirección para ahorrar
            for ox, oy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
                surface.blit(font.render(text, True, border_color), (x+ox, y+oy))
            surface.blit(font.render(text, True, color), (x, y))

        def restore_region(rect, inflate_x=12, inflate_y=10):
            """
            Restaura la región desde la instantánea pre_names_snapshot (que contiene
            las cartas ya dibujadas). Si no existe snapshot, usa fondo_img como fallback.
            Esto evita borrar las cartas debajo de los nombres al actualizar texto.
            """
            try:
                bg_rect = rect.inflate(inflate_x, inflate_y).clip(pygame.Rect(0,0,WIDTH,HEIGHT))
                if bg_rect.width <= 0 or bg_rect.height <= 0:
                    return
                if pre_names_snapshot:
                    # copiar desde la snapshot que contiene cartas y UI previas
                    screen.blit(pre_names_snapshot, bg_rect.topleft, bg_rect)
                else:
                    # fallback: reponer desde fondo estático (pierde cartas)
                    screen.blit(fondo_img, bg_rect.topleft, bg_rect)
            except Exception:
                pygame.draw.rect(screen, (0,0,0), rect.inflate(inflate_x, inflate_y))

        # --- Jugador local (parte inferior) ---
        if jugador_local:
            jug_rect = boxes.get("jug1")
            if jug_rect:
                borde_color = (255,0,0) if getattr(jugador_local, "isHand", False) else (0,0,0)
                nombre_txt = str(getattr(jugador_local, "playerName", "Jugador"))
                max_w_nombre = max(40, jug_rect.width - 8)
                font_nombre_used = get_fitting_font(nombre_txt, max_w_nombre, BASE_NOMBRE_SIZE)
                nombre_rect = font_nombre_used.render(nombre_txt, True, (255,255,255)).get_rect(
                    center=(jug_rect.centerx, jug_rect.bottom + 15)
                )
                # restaurar sólo la zona previa desde la snapshot (no el fondo completo)
                restore_region(nombre_rect, 14, 12)
                draw_text_with_border(screen, nombre_txt, font_nombre_used, nombre_rect.topleft,
                                     (255,255,255), borde_color)

                # Puntos debajo del nombre: NO borrar el fondo (solo dibujar sobre lo que haya)
                puntos_txt = f"{getattr(jugador_local, 'playerPoints', 0)} pts"
                max_w_puntos = max(30, jug_rect.width - 8)
                font_puntos_used = get_fitting_font(puntos_txt, max_w_puntos, BASE_PUNTOS_SIZE)
                puntos_rect = font_puntos_used.render(puntos_txt, True, (220,220,120)).get_rect(
                    center=(jug_rect.centerx, nombre_rect.bottom + 12)
                )
                # no restaurar (para no borrar cartas); si quieres limpiar sólo texto viejo, restaura desde snapshot:
                restore_region(puntos_rect, 12, 10)
                draw_text_with_border(screen, puntos_txt, font_puntos_used, puntos_rect.topleft,
                                     (220,220,120), (0,0,0))

        # --- Jugadores laterales ---
        for jugador, recuadro in jugadores_laterales:
            borde_color = (255,0,0) if getattr(jugador, "isHand", False) else (0,0,0)
            nombre_txt = str(getattr(jugador, "playerName", "Jugador"))
            max_w_nombre = max(30, recuadro.width - 8)
            font_nombre_used = get_fitting_font(nombre_txt, max_w_nombre, BASE_NOMBRE_SIZE)
            nombre_rect = font_nombre_used.render(nombre_txt, True, (255,255,255)).get_rect(
                center=(recuadro.centerx, recuadro.top - 12)
            )
            restore_region(nombre_rect, 12, 10)
            draw_text_with_border(screen, nombre_txt, font_nombre_used, nombre_rect.topleft,
                                 (255,255,255), borde_color)

            puntos_txt = f"{getattr(jugador, 'playerPoints', 0)} pts"
            max_w_puntos = max(30, recuadro.width - 8)
            font_puntos_used = get_fitting_font(puntos_txt, max_w_puntos, BASE_PUNTOS_SIZE)
            puntos_rect = font_puntos_used.render(puntos_txt, True, (220,220,120)).get_rect(
                center=(recuadro.centerx, nombre_rect.bottom + 10)
            )
            restore_region(puntos_rect, 10, 8)
            draw_text_with_border(screen, puntos_txt, font_puntos_used, puntos_rect.topleft,
                                 (220,220,120), (0,0,0))

        # --- Jugadores superiores ---
        for jugador, recuadro in jugadores_superiores:
            borde_color = (255,0,0) if getattr(jugador, "isHand", False) else (0,0,0)
            nombre_txt = str(getattr(jugador, "playerName", "Jugador"))
            max_w_nombre = max(30, recuadro.width - 8)
            font_nombre_used = get_fitting_font(nombre_txt, max_w_nombre, BASE_NOMBRE_SIZE)
            nombre_rect = font_nombre_used.render(nombre_txt, True, (255,255,255)).get_rect(
                center=(recuadro.centerx, recuadro.bottom + 15)
            )
            restore_region(nombre_rect, 12, 10)
            draw_text_with_border(screen, nombre_txt, font_nombre_used, nombre_rect.topleft,
                                 (255,255,255), borde_color)

            puntos_txt = f"{getattr(jugador, 'playerPoints', 0)} pts"
            max_w_puntos = max(30, recuadro.width - 8)
            font_puntos_used = get_fitting_font(puntos_txt, max_w_puntos, BASE_PUNTOS_SIZE)
            puntos_rect = font_puntos_used.render(puntos_txt, True, (220,220,120)).get_rect(
                center=(recuadro.centerx, nombre_rect.bottom + 12)
            )
            restore_region(puntos_rect, 10, 8)
            draw_text_with_border(screen, puntos_txt, font_puntos_used, puntos_rect.topleft,
                                 (220,220,120), (0,0,0))
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

        # Dibuja cartas en Trio (zona_cartas[1]) ##### Prueba no se para ver que pasa 
        '''if zona_cartas[1] and roundOne:
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
                    screen.blit(img, card_rect.topleft)'''

        if zona_cartas[1]:
            rect = cuadros_interactivos.get("Trio")    # Seguidilla2 en la zona[1]
            if rect:
                n = len(zona_cartas[1])
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
        #        # Dibuja de atrás hacia adelante (la última encima)
                for i in range(n):
                    idx = i  # Si quieres la última encima, usa el orden normal
                    card = zona_cartas[1][idx]
                    img = get_card_image(card)
                    img = pygame.transform.smoothscale(img, (card_width, card_height))
                    card_rect = pygame.Rect(x, start_y + i * solapamiento, card_width, card_height)
                    screen.blit(img, card_rect.topleft)


        # Dibuja cartas en Descarte (zona_cartas[2])
        # Deben haber como mucho 2 cartas
        rect = cuadros_interactivos.get("Descarte")
        if rect and len(zona_cartas) > 2 and zona_cartas[2]:
            stack = zona_cartas[2]
            # usar mismas medidas que casillas
            card_w = rect.width - 8
            card_h = int(card_w / 0.68)
            overlap_y = max(6, card_h // 3)
            # limitar visibilidad para no desbordar el rect
            max_visible = max(1, (rect.height - 8) // overlap_y)
            start_index = max(0, len(stack) - max_visible)
            # tomar referencia Y igual que otras casillas para empezar la lluvia alineada
            ref_rect = cuadros_interactivos.get("Trio") or cuadros_interactivos.get("Seguidilla") or cuadros_interactivos.get("ZonaCentralInteractiva") or rect
            base_y = ref_rect.y + 70
            for i, carta in enumerate(stack[start_index:], start=0):
                try:
                    img = get_card_image(carta)
                    img = pygame.transform.smoothscale(img, (card_w, card_h))
                except Exception:
                    img = pygame.Surface((card_w, card_h))
                    img.fill((200, 200, 200))
                x = rect.x + (rect.width - card_w) // 2
                y = base_y + i * overlap_y
                screen.blit(img, (x, y))
        # --- Dibuja la Zona CentralInteractiva como las demás casillas (lluvia / solapada) ---
        zona_rect = cuadros_interactivos.get("ZonaCentralInteractiva")
        try:
            zona_central = zona_cartas[3] if len(zona_cartas) > 3 else (zona_cartas[-1] if zona_cartas else [])
        except Exception:
            zona_central = []
        # Dibujar en solapamiento vertical (hacia abajo), sin overlay ni borde
        if zona_rect is not None and zona_central:
            card_w = zona_rect.width - 8
            card_h = int(card_w / 0.68)
            # solapamiento vertical (espacio entre cartas)
            overlap_y = max(6, card_h // 3)
            # calcular cuántas caben verticalmente
            max_visible = max(1, (zona_rect.height - 8) // overlap_y)
            start_index = max(0, len(zona_central) - max_visible)
            for i, carta in enumerate(zona_central[start_index:], start=0):
                try:
                    img = get_card_image(carta)
                    img = pygame.transform.smoothscale(img, (card_w, card_h))
                except Exception:
                    img = pygame.Surface((card_w, card_h))
                    img.fill((180, 180, 180))
                x = zona_rect.x + (zona_rect.width - card_w) // 2  # centrar horizontalmente
                y = zona_rect.y + 4 + i * overlap_y
                screen.blit(img, (x, y))       
        if zona_cartas[3] and roundTwo:
            rect = cuadros_interactivos.get("Trio") 
            if rect:
                n = len(zona_cartas[3])
                card_width = rect.width - 8
                card_height = int(card_width / 0.68)
        if zona_cartas[3] and roundFour:
            rect = cuadros_interactivos.get("Seguidilla") 
            if rect:
                n = len(zona_cartas[3])
                card_width = rect.width - 8
                card_height = int(card_width / 0.68)

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

            # DIBUJA OVERLAY SEMI‑INVISIBLE (solo visual, la detección de click usa cuadros_interactivos)
            ov = cuadros_interactivos.get("DescarteOverlay")
            if ov:
                surf = pygame.Surface((ov.width, ov.height), pygame.SRCALPHA)
                surf.fill((255, 255, 255, 20))  # muy translúcido
                screen.blit(surf, ov.topleft)

        # for idx, nombre in enumerate(["Seguidilla", "Trio", "Descarte"]):
        #     if zona_cartas[idx]:
        #         rect = cuadros_interactivos.get(nombre)
        #         if rect:
                img = get_card_image(card)
                img = pygame.transform.smoothscale(img, (card_width, card_height))
                card_rect = pygame.Rect(x, y, card_width, card_height)
                screen.blit(img, card_rect.topleft)
        if zona_cartas[3] and roundTwo:
            rect = cuadros_interactivos.get("Trio") 
            if rect:
                n = len(zona_cartas[3])
                card_width = rect.width - 8
                card_height = int(card_width / 0.68)
        if zona_cartas[3] and roundFour:
            rect = cuadros_interactivos.get("Seguidilla") 
            if rect:
                n = len(zona_cartas[3])
                card_width = rect.width - 8
                card_height = int(card_width / 0.68)

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
        # Mensaje temporal: blanco, más grande, wrap por palabra cada 35 caracteres y un poco más abajo
        if mensaje_temporal and time.time() - mensaje_tiempo < 5:
            def wrap_preserve_words(text, max_chars=35):
                words = text.split()
                if not words:
                    return []
                lines = []
                cur = words[0]
                for w in words[1:]:
                    if len(cur) + 1 + len(w) <= max_chars:
                        cur += " " + w
                    else:
                        lines.append(cur)
                        cur = w
                lines.append(cur)
                return lines

            font_msg = get_game_font(18) 
            lines = wrap_preserve_words(mensaje_temporal, 35)
            line_h = font_msg.get_linesize()
            base_x = WIDTH // 2
            base_y = HEIGHT // 2 + 160  
            total_h = line_h * len(lines)
            start_y = base_y - total_h // 2

            for i, line in enumerate(lines):
                surf = font_msg.render(line, True, (255, 255, 255))
                rect = surf.get_rect(center=(base_x, start_y + i * line_h))
                # borde negro alrededor (8 direcciones)
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
                    screen.blit(font_msg.render(line, True, ( (165, 42, 42))), (rect.x + dx, rect.y + dy))
                screen.blit(surf, rect)
        elif mensaje_temporal and time.time() - mensaje_tiempo >= 5:
            mensaje_temporal = ""
        # Dibujar siempre los botones Ronda / Turno / Menú con las imágenes cacheadas (evita parpadeo)
        try:
            ronda_rect = cuadros_interactivos.get("Ronda")
            if ronda_rect:
                img = pygame.transform.smoothscale(ronda_rect.width, ronda_rect.height)
                screen.blit(img, ronda_rect.topleft)

            turno_rect = cuadros_interactivos.get("Turno")
            if turno_rect:
                img = pygame.transform.smoothscale(turno_rect.width, turno_rect.height)
                screen.blit(img, turno_rect.topleft)

            menu_rect = cuadros_interactivos.get("Menú") or cuadros_interactivos.get("Menu")
            if menu_rect:
                img = pygame.transform.smoothscale(menu_rect.width, menu_rect.height)
                screen.blit(img, menu_rect.topleft)
        except Exception:
            pass
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

        # --- Mostrar solo el nombre del jugador en turno con sangría ---
        try:
            current_player_name = next((getattr(p, "playerName", "?") for p in players if getattr(p, "isHand", False)), None)
            if current_player_name is None:
                current_player_name = getattr(players[0], "playerName", "—") if players else "—"
        except Exception:
            current_player_name = "—"

        font_path = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
        turno_font = pygame.font.Font(font_path, 20)
        turn_text = turno_font.render(str(current_player_name), True, (255, 255, 255))
        turn_text_rect = turn_text.get_rect(left=turno_rect.left + 155, centery=turno_rect.centery)
        render_text_with_border(str(current_player_name), turno_font, (255,255,255), (0,0,0), (turn_text_rect.x, turn_text_rect.y), screen)
        screen.blit(turn_text, turn_text_rect)

        # --- Mostrar "Ronda 1" o "Ronda 2" al lado del nombre ---
        if fase == "ronda1":
            ronda_text = "1"
        elif fase == "ronda2":
            ronda_text = "2"
        elif fase == "ronda3": #####################
            ronda_text = "3"
        elif fase == "ronda4":
            ronda_text = "4"
        else:
            ronda_text = ""
        if ronda_text:
            ronda_font = pygame.font.Font(font_path, 35)
            # Calcula la posición centrada encima del nombre
            ronda_render = ronda_font.render(ronda_text, True, (255,255,255))
            ronda_rect = ronda_render.get_rect(left=turn_text_rect.left + 30, bottom=turn_text_rect.top - 25)
            render_text_with_border(ronda_text, ronda_font, (255,255,255), (200,0,0), (ronda_rect.x, ronda_rect.y), screen)            # Dibuja texto blanco con borde rojo
        # --- Botón "Menú" ---
            menu_img_path = os.path.join(ASSETS_PATH, "menu.png")
            if os.path.exists(menu_img_path):
                menu_img = pygame.image.load(menu_img_path).convert_alpha()
                img = pygame.transform.smoothscale(menu_img, (menu_rect.width, menu_rect.height))
                screen.blit(img, menu_rect.topleft)
            cuadros_interactivos["Menú"] = menu_rect

        # Mostrar jugadas bajadas en los bloques de bajada de todos los jugadores

        # Mostrar jugadas bajadas: ubicar cada bajada junto a la caja del jugador (misma lógica que nombres/manos)
        rects_jugadas = {}

        # Construir mapping playerName -> rect de "bajada" usando la misma perspectiva que ya usamos
        player_baj_rect = {}

        # jugador local -> baj1
        if jugador_local:
            player_baj_rect[getattr(jugador_local, "playerName", None)] = boxes.get("baj1")

        # Para laterales/superiores ya tenemos listas (jugadores_laterales, jugadores_superiores)
        all_side_players = jugadores_laterales + jugadores_superiores
        for p, jug_rect in all_side_players:
            # buscar la clave de 'jugX' dentro de boxes que coincida con el rect actual
            jug_key = next((k for k, v in boxes.items() if v == jug_rect and k.startswith("jug")), None)
            if jug_key:
                baj_key = jug_key.replace("jug", "baj")
                player_baj_rect[getattr(p, "playerName", None)] = boxes.get(baj_key)

        # También cubrir casos si hay players no listados (por si layout cambió)
        for p in players:
            if p.playerName not in player_baj_rect:
                # intentar mapear por índice relativo (0->baj1,1->baj2,...)
                try:
                    idx = players.index(p)
                    key = f"baj{idx+1}"
                    if key in boxes:
                        player_baj_rect[p.playerName] = boxes.get(key)
                except Exception:
                    pass

        # función helper que dibuja jugadas dentro de un rect (vertical u horizontal según caja)
        def draw_plays_in_bajada(jugador, bloque_rect):
            if not bloque_rect:
                return
            plays_source = getattr(jugador, "playMade", []) or getattr(jugador, "jugadas_bajadas", [])
            if not plays_source:
                return
            rects_jugadas[jugador.playerName] = []

            vertical_boxes = {"baj2", "baj3", "baj6", "baj7"}
            # averiguar nombre de la caja para orientación
            box_name = next((k for k, v in boxes.items() if v == bloque_rect), None)

            if box_name in vertical_boxes:
                margen_jugada = 1
                card_width = int(bloque_rect.width * 0.45)
                card_height = int(card_width / 0.68)
                x = bloque_rect.x + (bloque_rect.width - card_height) // 2
                y_actual = bloque_rect.y + 6

                for play_index, jugada in enumerate(plays_source):
                    string_to_card(jugada[0])
                    string_to_card(jugada[1])
                    if isinstance(jugada, list) and jugada and isinstance(jugada[0], str):
                        resolved = None
                        if hasattr(jugador, "jugadas_bajadas") and len(jugador.jugadas_bajadas) > play_index:
                            resolved = jugador.jugadas_bajadas[play_index]
                        if resolved is None:
                            continue
                        jugada = resolved

                    resolved_jugada = resolve_play(jugador, jugada, play_index)
                    if not resolved_jugada:
                        continue

                    jugadas_a_dibujar = []
                    if isinstance(resolved_jugada, dict):
                        if "trio" in resolved_jugada and resolved_jugada["trio"]:
                            jugadas_a_dibujar.append(("trio", resolved_jugada["trio"]))
                        if "straight" in resolved_jugada and resolved_jugada["straight"]:
                            jugadas_a_dibujar.append(("straight", resolved_jugada["straight"]))
                    elif isinstance(resolved_jugada, list):
                        inferred_type = "trio" if len(resolved_jugada) == 3 else "straight"
                        jugadas_a_dibujar.append((inferred_type, resolved_jugada))
                    else:
                        continue

                    for subtype, cartas_jugada in jugadas_a_dibujar:
                        n = len(cartas_jugada)
                        if n == 0:
                            continue
                        solapamiento = int(card_width * 0.20) if n > 1 else 0
                        inicio_rect = pygame.Rect(x, y_actual, card_width, card_height)
                        final_rect = pygame.Rect(x + (n - 1) * solapamiento, y_actual, card_width, card_height)
                        rects_jugadas[jugador.playerName].append({
                            "inicio": inicio_rect,
                            "final": final_rect,
                            "tipo": "trio" if subtype == "trio" else "straight",
                            "play_index": play_index,
                            "subtype": subtype,
                            "cartas": cartas_jugada
                        })
                        for i, carta in enumerate(cartas_jugada):
                            string_to_card([cartas_jugada])
                            img = get_card_image(carta)
                            img = pygame.transform.smoothscale(img, (card_width, card_height))
                            img = pygame.transform.rotate(img, 90)
                            card_rect = pygame.Rect(x, y_actual + i * solapamiento, card_height, card_width)
                            if card_rect.bottom <= bloque_rect.bottom:
                                screen.blit(img, card_rect.topleft)
                        y_actual += n * solapamiento + card_width + margen_jugada
            else:
                card_height = bloque_rect.height - 8
                card_width = int(card_height * 0.68)
                margen_jugada = 1
                x_actual = bloque_rect.x + 6
                y = bloque_rect.y + (bloque_rect.height - card_height) // 2 - 18

                for play_index, jugada in enumerate(plays_source):
                    if isinstance(jugada, list) and jugada and isinstance(jugada[0], str):
                        resolved = None
                        if hasattr(jugador, "jugadas_bajadas") and len(jugador.jugadas_bajadas) > play_index:
                            resolved = jugador.jugadas_bajadas[play_index]
                        if resolved is None:
                            continue
                        jugada = resolved

                    resolved_jugada = resolve_play(jugador, jugada, play_index)
                    if not resolved_jugada:
                        continue

                    jugadas_a_dibujar = []
                    if isinstance(resolved_jugada, dict):
                        if "trio" in resolved_jugada and resolved_jugada["trio"]:
                            jugadas_a_dibujar.append(("trio", resolved_jugada["trio"]))
                        if "straight" in resolved_jugada and resolved_jugada["straight"]:
                            jugadas_a_dibujar.append(("straight", resolved_jugada["straight"]))
                    elif isinstance(resolved_jugada, list):
                        inferred_type = "trio" if len(resolved_jugada) == 3 else "straight"
                        jugadas_a_dibujar.append((inferred_type, resolved_jugada))
                    else:
                        continue

                    for subtype, cartas_jugada in jugadas_a_dibujar:
                        n = len(cartas_jugada)
                        if n == 0:
                            continue
                        solapamiento = int(card_width * 0.20) if n > 1 else 0
                        inicio_rect = pygame.Rect(x_actual, y, card_width, card_height)
                        final_rect = pygame.Rect(x_actual + (n - 1) * solapamiento, y, card_width, card_height)
                        rects_jugadas[jugador.playerName].append({
                            "inicio": inicio_rect,
                            "final": final_rect,
                            "tipo": "trio" if subtype == "trio" else "straight",
                            "play_index": play_index,
                            "subtype": subtype,
                            "cartas": cartas_jugada
                        })
                        for i, carta in enumerate(cartas_jugada):
                            img = get_card_image(carta)
                            img = pygame.transform.smoothscale(img, (card_width, card_height))
                            card_rect = pygame.Rect(x_actual + i * solapamiento, y, card_width, card_height)
                            screen.blit(img, card_rect.topleft)
                        x_actual += n * solapamiento + card_width + margen_jugada

        # Dibujar todas las jugadas usando el mapping construido
        for p in players:
            p_name = getattr(p, "playerName", None)
            baj_rect = player_baj_rect.get(p_name)
            if baj_rect:
                draw_plays_in_bajada(p, baj_rect)

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
                
                #Cambiar aqui juego1 para ronda 1 y juego2 para ronda 2 para hacer test
                fase = "ronda1"
                #-------------------------


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
        if fase == "ronda1":    # Puede quedarse "juego"  :)
            for jugador in players:
                if hasattr(jugador, "playerHand") and len(jugador.playerHand) == 0:
                    # Calcular puntos de todos los jugadores
                    for p in players:
                        p.calculatePoints()
                    aplausos_sound_path = os.path.join(ASSETS_PATH, "sonido", "aplauso.wav")
                    aplausos_sound = pygame.mixer.Sound(aplausos_sound_path)
                    aplausos_sound.play()
                    fase = "fin1"
                    fase_fin_tiempo = time.time()
                    break

        # --- FASE DE FIN ---
        if fase == "fin1":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            screen.blit(fondo_img, (0, 0))
            mostrar_puntuaciones_final(screen, fondo_img, players, WIDTH, HEIGHT, ASSETS_PATH, round_number=1)
            pygame.display.flip()
            # Espera 7 segundos y termina el juego (puedes cambiar el tiempo)
            if time.time() - fase_fin_tiempo >= 7:
                fase = "eleccion" #"ronda2"   # "eleccion" <--- Ahí se reinicia y se distribuye el mazo y las manos
                roundOne = False
                roundTwo = True   # Para Prueba
            continue
        
        if fase == "ronda2":
            for jugador in players:
                if hasattr(jugador, "playerHand") and len(jugador.playerHand) == 0:
                    # Calcular puntos de todos los jugadores
                    for p in players:
                        p.calculatePoints()
                    aplausos_sound_path = os.path.join(ASSETS_PATH, "sonido", "aplauso.wav")
                    aplausos_sound = pygame.mixer.Sound(aplausos_sound_path)
                    aplausos_sound.play()
                    fase = "fin2"
                    fase_fin_tiempo = time.time()
                    break
        
        if fase == "fin2":
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                screen.blit(fondo_img, (0, 0))
                mostrar_puntuaciones_final(screen, fondo_img, players, WIDTH, HEIGHT, ASSETS_PATH, round_number=2)
                pygame.display.flip()
                # Espera 7 segundos y termina el juego (puedes cambiar el tiempo)
                if time.time() - fase_fin_tiempo >= 7:
                    fase = "eleccion"
                    roundTwo = False
                    roundThree = True
                continue

        if fase == "ronda3":
            for jugador in players:
                if hasattr(jugador, "playerHand") and len(jugador.playerHand) == 0:
                    # Calcular puntos de todos los jugadores
                    for p in players:
                        p.calculatePoints()
                    aplausos_sound_path = os.path.join(ASSETS_PATH, "sonido", "aplauso.wav")
                    aplausos_sound = pygame.mixer.Sound(aplausos_sound_path)
                    aplausos_sound.play()                    
                    fase = "fin3"
                    fase_fin_tiempo = time.time()
                    break

        if fase == "fin3":
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                screen.blit(fondo_img, (0, 0))
                mostrar_puntuaciones_final(screen, fondo_img, players, WIDTH, HEIGHT, ASSETS_PATH, round_number=3)
                pygame.display.flip()
                # Espera 7 segundos y termina el juego (puedes cambiar el tiempo)
                if time.time() - fase_fin_tiempo >= 7:
                    fase = "eleccion"
                    roundThree = False
                    roundFour = True
                continue

        if fase == "ronda4":
            for jugador in players:
                if hasattr(jugador, "playerHand") and len(jugador.playerHand) == 0:
                    # Calcular puntos de todos los jugadores
                    for p in players:
                        p.calculatePoints()
                    aplausos_sound_path = os.path.join(ASSETS_PATH, "sonido", "aplauso.wav")
                    aplausos_sound = pygame.mixer.Sound(aplausos_sound_path)
                    aplausos_sound.play()
                    fase = "fin4"
                    fase_fin_tiempo = time.time()
                    break
        if fase == "fin4":
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                screen.blit(fondo_img, (0, 0))
                mostrar_puntuacion_final_detallada(screen, fondo_img, players, WIDTH, HEIGHT, ASSETS_PATH, round_number=4)
                pygame.display.flip()
                # Espera 7 segundos y termina el juego (puedes cambiar el tiempo)
                if time.time() - fase_fin_tiempo >= 7:
                    running = False
                continue
        pygame.display.flip()
    return


def mostrar_puntuaciones_final(screen, fondo_img, players, WIDTH, HEIGHT, ASSETS_PATH, round_number=None):
    """
    Muestra un panel centrado que diga:
      PUNTUACIONES FINALES
      Ronda: <n>        (si round_number no es None)
    y debajo, la lista de jugadores en el orden dado.
    Ajustes: mayor espaciado y mejor centrado para que no se corte abajo.
    """
    jugadores = list(players)  # respetar orden de juego

    filas = max(1, len(jugadores))
    espacio_entre = 52        # un poco más de separación entre filas
    top_padding = 36
    bottom_padding = 40
    header_h = 120            # más espacio para título + subtítulo

    alto_rect = header_h + filas * espacio_entre + top_padding + bottom_padding
    ancho_rect = min(WIDTH - 140, 820)

    # evitar que el rect se salga de la pantalla; reducir si es necesario
    if alto_rect + 80 > HEIGHT:
        alto_rect = HEIGHT - 80
        espacio_entre = max(36, (alto_rect - header_h - top_padding - bottom_padding) // max(1, filas))

    x_rect = (WIDTH - ancho_rect) // 2
    y_rect = max(40, (HEIGHT - alto_rect) // 2)

    rect_fondo = pygame.Rect(x_rect, y_rect, ancho_rect, alto_rect)

    # Fondo semitransparente + borde
    overlay = pygame.Surface((rect_fondo.width, rect_fondo.height), pygame.SRCALPHA)
    overlay.fill((18, 18, 18, 200))
    screen.blit(overlay, rect_fondo.topleft)
    pygame.draw.rect(screen, (180, 180, 180), rect_fondo, 2, border_radius=12)

    # Fuentes (usar la fuente del juego si existe)
    title_font = get_game_font(34)
    subtitle_font = get_game_font(18)
    player_font = get_game_font(22)
    info_font = get_game_font(12)

    center_x = x_rect + ancho_rect // 2

    # Título grande centrado (con borde para legibilidad)
    title_txt = "Puntuaciones Finales"
    title_surf = title_font.render(title_txt, True, (255, 255, 255))
    title_pos = (center_x - title_surf.get_width() // 2, y_rect + 18)
    # borde simple
    for ox, oy in [(-1,0),(1,0),(0,-1),(0,1)]:
        screen.blit(title_font.render(title_txt, True, (0,0,0)), (title_pos[0] + ox, title_pos[1] + oy))
    screen.blit(title_surf, title_pos)

    # Subtítulo Ronda (si aplica) — centrado, con margen extra debajo
    players_start_y = title_pos[1] + title_surf.get_height() + 12
    if round_number is not None:
        sub_txt = f"Ronda: {round_number}"
        sub_surf = subtitle_font.render(sub_txt, True, (220, 220, 220))
        sub_pos = (center_x - sub_surf.get_width() // 2, players_start_y)
        screen.blit(sub_surf, sub_pos)
        players_start_y = sub_pos[1] + sub_surf.get_height() + 18
    else:
        players_start_y += 8

    # Lista de jugadores (centrada horizontalmente, más abajo)
    max_players_display = (alto_rect - (players_start_y - y_rect) - bottom_padding) // espacio_entre
    # si hay demasiados jugadores, ajustar espacio para que entren
    if filas > max_players_display and max_players_display > 0:
        espacio_entre = max(32, (alto_rect - (players_start_y - y_rect) - bottom_padding) // filas)

    for i, jugador in enumerate(jugadores):
        nombre = getattr(jugador, "playerName", f"Jugador {i+1}")
        puntos = getattr(jugador, "playerPoints", 0)
        linea = f"{i+1}. {nombre}  —  {puntos} pts"
        y_line = players_start_y + i * espacio_entre
        # centrar la línea
        surf = player_font.render(linea, True, (240, 240, 220))
        x_line = center_x - surf.get_width() // 2
        # borde ligero para contraste sin tapar fondo
        for ox, oy in [(-1,0),(1,0),(0,-1),(0,1)]:
            screen.blit(player_font.render(linea, True, (0,0,0)), (x_line + ox, y_line + oy))
        screen.blit(surf, (x_line, y_line))

    # Mensaje de instrucción al final (más abajo con margen)
    info_txt = "Iniciando Siguiente Ronda..."
    info_surf = info_font.render(info_txt, True, (190,190,190))
    info_rect = info_surf.get_rect(center=(center_x, y_rect + alto_rect - 22))
    screen.blit(info_surf, info_rect.topleft)


def mostrar_puntuacion_final_detallada(screen, fondo_img, players, WIDTH, HEIGHT, ASSETS_PATH, round_number=None):
    """
    Muestra pantalla de 'Puntuación final' con:
      1er Lugar, 2do Lugar, ...
    Ahora el 1er lugar será el jugador con MENOS puntos (orden ascendente).
    round_number: opcional, muestra "Ronda: <n>" debajo del título si se pasa.
    """
    if not players:
        return

    # ordenar por puntos ASCENDENTE => primero = menor puntaje
    jugadores_ordenados = sorted(players, key=lambda j: getattr(j, "playerPoints", 0))

    # Helper para ordinales simples en español
    def ordinal_es(n):
        if n == 1:
            return "1er"
        if n == 2:
            return "2do"
        if n == 3:
            return "3er"
        return f"{n}º"

    filas = len(jugadores_ordenados)
    padding_y = 28
    espacio_linea = 44
    header_h = 84
    alto_rect = header_h + filas * espacio_linea + padding_y * 2
    ancho_rect = min(WIDTH - 120, 720 + max(0, (filas - 4) * 24))

    x_rect = (WIDTH - ancho_rect) // 2
    y_rect = max(40, (HEIGHT - alto_rect) // 2)

    rect_fondo = pygame.Rect(x_rect, y_rect, ancho_rect, alto_rect)

    # Fondo semitransparente + borde
    overlay = pygame.Surface((rect_fondo.width, rect_fondo.height), pygame.SRCALPHA)
    overlay.fill((16, 16, 16, 220))
    screen.blit(overlay, rect_fondo.topleft)
    pygame.draw.rect(screen, (200, 200, 200), rect_fondo, 2, border_radius=10)

    # Fuentes (usar la fuente del juego)
    title_font = get_game_font(28)
    place_font = get_game_font(20)
    info_font = get_game_font(12)

    # Dibuja título con borde simple
    title_txt = "Puntuación final"
    title_surf = title_font.render(title_txt, True, (255, 255, 255))
    tx, ty = x_rect + ancho_rect // 2, y_rect + 20
    # borde
    for ox, oy in [(-1,0),(1,0),(0,-1),(0,1)]:
        screen.blit(title_font.render(title_txt, True, (0,0,0)), (tx - title_surf.get_width()//2 + ox, ty + oy))
    screen.blit(title_surf, (tx - title_surf.get_width()//2, ty))

    # Subtítulo: Ronda si se pasó
    players_start_y = ty + title_surf.get_height() + 10
    if round_number is not None:
        sub_txt = f"Ronda: {round_number}"
        sub_surf = info_font.render(sub_txt, True, (220, 220, 220))
        sub_x = x_rect + ancho_rect // 2 - sub_surf.get_width() // 2
        sub_y = players_start_y
        screen.blit(sub_surf, (sub_x, sub_y))
        players_start_y = sub_y + sub_surf.get_height() + 12

    # Listado de lugares (primero = menor puntaje)
    for i, jugador in enumerate(jugadores_ordenados):
        lugar = i + 1
        nombre = getattr(jugador, "playerName", f"Jugador {lugar}")
        puntos = getattr(jugador, "playerPoints", 0)
        linea = f"{ordinal_es(lugar)} Lugar: {nombre} — {puntos} pts"
        y_line = players_start_y + i * espacio_linea

        surf = place_font.render(linea, True, (240, 240, 200))
        rx = x_rect + ancho_rect // 2 - surf.get_width() // 2
        ry = y_line
        # borde ligero
        for ox, oy in [(-1,0),(1,0),(0,-1),(0,1)]:
            screen.blit(place_font.render(linea, True, (0,0,0)), (rx+ox, ry+oy))
        screen.blit(surf, (rx, ry))

    # Info para continuar (vacío o personalizado)
    info_txt = ""
    info_surf = info_font.render(info_txt, True, (200,200,200))
    info_rect = info_surf.get_rect(center=(x_rect + ancho_rect//2, y_rect + alto_rect - 18))
    screen.blit(info_surf, info_rect.topleft)

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
                elif isinstance(data, dict) and data.get("type") in ["BAJARSE","TOMAR_DESCARTE", "TOMAR_CARTA", "DESCARTE", "COMPRAR_CARTA", "PASAR_DESCARTE", "INICIAR_COMPRA", "FIN_CICLO_COMPRA", "INSERTAR_CARTA"]:
                    network_manager.moves_gameServer.append(data)
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


def play_risa_if_joker(cartas):
    global mostrar_joker_fondo, tiempo_joker_fondo
    risa_sound_path = os.path.join(ASSETS_PATH, "sonido", "risa.wav")
    risa_sound = pygame.mixer.Sound(risa_sound_path)
    for carta in cartas:
        if hasattr(carta, "joker") and carta.joker:
            risa_sound.play()
            mostrar_joker_fondo = True
            tiempo_joker_fondo = pygame.time.get_ticks()
            break

joker_fondo_img = pygame.image.load(os.path.join(ASSETS_PATH, "joker_fondo.png")).convert()
joker_fondo_img = pygame.transform.scale(joker_fondo_img, (WIDTH, HEIGHT))
mostrar_joker_fondo = False
tiempo_joker_fondo = 0

if __name__ == "__main__":
    #ocultar_elementos_visual(screen, fondo_img)  # Solo muestra el fondo al inicio
    main()