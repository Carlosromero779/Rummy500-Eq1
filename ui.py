import pygame
import os
import sys
import threading
import pickle
import time
from network import NetworkManager

class Button:
    def __init__(self, image, pos, text_input, font, base_color, hovering_color, size=(250, 100), scale_factor=1.1):
        self.image = image         # Guarda la imagen del botón (puede ser una Surface de Pygame o None si solo es texto)
        self.original_image = image             # Guarda la imagen del botón (puede ser una Surface de Pygame o None si solo es texto)
        self.x_pos = pos[0]         # Coordenada X en la pantalla donde se dibujará el botón
        self.y_pos = pos[1]         # Coordenada Y en la pantalla donde se dibujará el botón
        self.font = font          # Fuente que se usará para dibujar el texto del botón
        self.base_color = base_color      # Color del texto o botón cuando no hay interacción (estado normal)
        self.hovering_color = hovering_color         # Color del texto o botón cuando el ratón está encima (hover)
        self.text_input = text_input          # Color del texto o botón cuando el ratón está encima (hover)
        self.base_size = size         # Color del texto o botón cuando el ratón está encima (hover)
        self.scale_factor = scale_factor         # Factor por el cual crecerá el botón cuando el ratón esté encima (1.1 = 10% más grande)
        self.current_size = list(size)         # Tamaño actual del botón, empieza igual al tamaño base pero cambia si hay hover
        self.is_hovering = False         # Estado booleano que indica si el ratón está sobre el botón
        self.text = self.font.render(self.text_input, False, self.base_color) # Renderiza el texto en una superficie con el color base, AntialisinG False
        # Si hay imagen, escalarla al tamaño actual y obtener el rectángulo centrado
        if self.image is not None:
            self.image = pygame.transform.scale(self.original_image, self.current_size)
            self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        else:
        # Si no hay imagen, crear un rectángulo con el tamaño actual y centrarlo
            self.rect = pygame.Rect(0, 0, *self.current_size)
            self.rect.center = (self.x_pos, self.y_pos)
        # Rectángulo del texto centrado sobre el botón
        self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))

    def update(self, screen):

        # Calcular tamaño objetivo según si el cursor está sobre el botón

        target_size = [int(self.base_size[0] * (self.scale_factor if self.is_hovering else 1)),
                      int(self.base_size[1] * (self.scale_factor if self.is_hovering else 1))]
        
        # Interpolación suave del tamaño actual hacia el tamaño objetivo

        for i in range(2):
            if abs(self.current_size[i] - target_size[i]) > 1:
                self.current_size[i] += (target_size[i] - self.current_size[i]) * 0.2
            else:
                self.current_size[i] = target_size[i]
        
        # Dibujar la imagen escalada si existe

        if self.image is not None:
            scaled_image = pygame.transform.scale(self.original_image, [int(x) for x in self.current_size])
            scaled_rect = scaled_image.get_rect(center=(self.x_pos, self.y_pos))
            screen.blit(scaled_image, scaled_rect)
            self.rect = scaled_rect
        else:
            # Si no hay imagen, aseguro que el rect tenga el tamaño y centro actuales
            self.rect.size = (int(self.current_size[0]), int(self.current_size[1]))
            self.rect.center = (self.x_pos, self.y_pos)

        # Asegurar que el texto siempre se centre respecto al rect (evita que quede en la posición inicial)
        self.text_rect = self.text.get_rect(center=self.rect.center)

        # Dibujar siempre el texto centrado
        screen.blit(self.text, self.text_rect)

    def checkForInput(self, position):

        # Devuelve True si la posición del mouse está dentro del rectángulo del botón

        return self.rect.collidepoint(position)

    def changeColor(self, position):
        if self.rect.collidepoint(position):

        # Si el mouse está sobre el botón, usar color de hover

            self.text = self.font.render(self.text_input, True, self.hovering_color)
        else:

        # Si no está sobre el botón, usar color base

            self.text = self.font.render(self.text_input, True, self.base_color)

    def check_hover(self, position):
        # Guardar estado anterior de hover
        was_hovering = self.is_hovering

        # Actualizar estado actual de hover
        self.is_hovering = self.rect.collidepoint(position)
        
        # Si hubo un cambio (entró o salió del hover), actualizar el color del texto
        if was_hovering != self.is_hovering:
            self.changeColor(position)

# ===========================
# Clase para cajas de texto
# ===========================

class InputBox:
    def __init__(self, x, y, w, h, font, text=''):
        # Rectángulo que define la posición y tamaño de la caja
        self.rect = pygame.Rect(x, y, w, h)
        # Colores de la caja: inactivo y activo (cuando el usuario hace click)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        # Texto que contiene la caja
        self.text = text
        # Fuente para renderizar el texto
        self.font = font
        # Surface que dibuja el texto en la pantalla
        self.txt_surface = font.render(text, True, self.color)
        # Estado de la caja: activa o no
        self.active = False

    # Manejar eventos del teclado y mouse
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Si se hace click dentro del rectángulo, alternar activo/inactivo
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
                # Cambiar color según estado
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN:
            # Solo escribir si la caja está activa
            if self.active:
                if event.key == pygame.K_RETURN:
                # Enter imprime el texto y lo limpia
                    print(self.text)
                    #self.text = ''
                    return self.text
                elif event.key == pygame.K_BACKSPACE:
                # Borrar última letra
                    self.text = self.text[:-1]
                else:
                # Agregar letra presionada
                    self.text += event.unicode
                # Actualizar surface del texto
                self.txt_surface = self.font.render(self.text, True, self.color)

    # Actualizar tamaño de la caja según longitud del texto
    def update(self):
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width


    # Dibujar la caja y el texto en pantalla
    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        pygame.draw.rect(screen, self.color, self.rect, 2)



# ===========================
# Clase que maneja la interfaz
# ===========================
class   UIManager:
    def __init__(self, screen_width, screen_height, network_manager):
        
        # Dimensiones de la pantalla
        self.SCREEN_WIDTH = screen_width
        self.SCREEN_HEIGHT = screen_height
        
        # Manager de red (para conectar con el servidor, enviar/recibir datos)
        self.network_manager = network_manager
        
        # Crear ventana de Pygame con las dimensiones dadas
        self.SCREEN = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.RESIZABLE)
        
        # Título de la ventana        
        pygame.display.set_caption("Menu Principal")
        
        # Cargar todos los assets (imágenes, botones, etc.)
        self.load_assets()
        
        # Pantalla actual (puede ser "main", "settings", etc.)
        self.current_screen = "main"
        
        # Reloj para controlar FPS y timing
        self.clock = pygame.time.Clock()
        
        # Guardar tiempo actual para calcular deltas
        self.last_time = pygame.time.get_ticks()
        
        # Inicializar componentes de la UI (botones, cajas de texto, etc.)
        self.init_components()

        self.servers = []      #Lista de servidores encontrados
        self.selectedServer = None  #ALmacena el servidor selecionado
        self.isSeletedServer = False #Fija el servidor seleccionado
        self.response = None #Resuesta de conexion para el jugador
        self.is_hovered = None
        self.messages = []    #Mensajes para el Chat
        self.chatLock = threading.Lock() 
        self.playGamePlayer = False
        #-----------------------------------
        self.wrong_password_until = 0
        self.fullserver_until = 0         
        self.no_server_until = 0  

        click_path = os.path.join("assets", "sonido", "click.wav")
        self.click_sound = pygame.mixer.Sound(click_path)      
        #------------------------------------



    def load_assets(self):
        assets_path = os.path.join(os.getcwd(), "assets")  # Ruta a la carpeta de assets

        # Guardar las imágenes originales para poder re-escalarlas al cambiar el tamaño de la ventana
        self.titulo_img_original = pygame.image.load(os.path.join(assets_path, "titulo.png")).convert_alpha()
        self.fondo_img_original = pygame.image.load(os.path.join(assets_path, "fondo.png")).convert()

        self.jugar_img = pygame.image.load(os.path.join(assets_path, "jugar_button.png")).convert_alpha()  # Botón Jugar
        self.reglas_img = pygame.image.load(os.path.join(assets_path, "reglas_button.png")).convert_alpha()  # Botón Reglas
        self.salir_img = pygame.image.load(os.path.join(assets_path, "salir_button.png")).convert_alpha()  # Botón Salir
        self.unirse_img = pygame.image.load(os.path.join(assets_path, "unirse_button.png")).convert_alpha()  # Botón Unirse
        self.actualizar_img = pygame.image.load(os.path.join(assets_path, "refreshButtom.png")).convert_alpha()  # Botón Actualizar
        self.crear_img = pygame.image.load(os.path.join(assets_path, "crear_button.png")).convert_alpha()  # Botón Crear
        self.volver_img = pygame.image.load(os.path.join(assets_path, "volver_button.png")).convert_alpha()  # Botón Volver
        self.iniciar_juego_img = pygame.image.load(os.path.join(assets_path, "iniciar_juego_button.png")).convert_alpha()  # Botón iniciar juego

        self.animacion_fondo_img = pygame.image.load(os.path.join(assets_path, "animacion_fondo.png")).convert_alpha()  # Fondo animado
        self.animacion_fondo_img = pygame.transform.scale(self.animacion_fondo_img, (1000, 800))  # Escalar animación
        self.pos_izquierda = (40, 120)  # Posición animación izquierda
        self.pos_derecha = (1230, 120)  # Posición animación derecha
        self.angulo_izquierda = 0  # Ángulo inicial izquierda
        self.angulo_derecha = 0  # Ángulo inicial derecha

        # Intentar cargar una fuente pixelada personalizada desde la carpeta "assets"
        try:
            self.pixel_font = pygame.font.Font(
                os.path.join("assets", "PressStart2P-Regular.ttf"),  # Ruta del archivo de fuente
                30  # Tamaño de la fuente
            )
        # Si falla (por ejemplo, si no encuentra el archivo), usar una fuente del sistema
        except:
            print("Advertencia: No se pudo cargar la fuente pixelada. Usando fuente por defecto.")
            self.pixel_font = pygame.font.SysFont("Arial", 30)  # Fuente de respaldo (Arial tamaño 30)

        # Crear una superficie (imagen) con el texto de los créditos usando la fuente cargada
        self.credits_surface = self.pixel_font.render(
            "Proyecto realizado por el Equipo 1",  # Texto que se dibuja
            True,  # Activar suavizado de bordes (antialiasing)
            "#d7fcd4"  # Color del texto en formato hexadecimal
        )

    # Función para obtener una fuente personalizada o de respaldo
    def get_font(self, size):
        try:
            # Intenta cargar la fuente pixelada desde la carpeta assets
            return pygame.font.Font(os.path.join("assets", "PressStart2P-Regular.ttf"), size)
        except:
            # Si falla, usa la fuente Arial como respaldo
            print("Advertencia: No se pudo cargar la fuente personalizada. Usando fuente por defecto.")
            return pygame.font.SysFont("Arial", size)

    # Función para inicializar todos los botones y elementos de la interfaz
    def init_components(self):
        # Se escalan las imágenes originales basándose en la resolusión actual de la pantalla
        self.titulo_img = pygame.transform.scale(self.titulo_img_original, (int(self.SCREEN_WIDTH * 0.5), int(self.SCREEN_HEIGHT * 0.35)))
        self.fondo_img = pygame.transform.scale(self.fondo_img_original, (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))

        # Botón "JUGAR"
        self.JUGAR_BUTTON = Button(
            image=self.jugar_img,  # Imagen del botón
            pos=(self.SCREEN_WIDTH//2, int(self.SCREEN_HEIGHT*0.55)),  # Posición centrada horizontal y 55% de alto
            text_input="",  # Sin texto
            font=self.get_font(75),  # Fuente grande
            base_color="#d7fcd4",  # Color base
            hovering_color="White",  # Color al pasar el mouse
            size=(400, 110)  # Tamaño del botón
        )

        # Botón "REGLAS"
        self.REGLAS_BUTTON = Button(
            image=self.reglas_img,
            pos=(self.SCREEN_WIDTH//2 - 180, int(self.SCREEN_HEIGHT*0.75)),  # Más a la izquierda
            text_input="",
            font=self.get_font(75),
            base_color="#d7fcd4",
            hovering_color="White",
            size=(300, 90)
        )

        # Botón "SALIR"
        self.SALIR_BUTTON = Button(
            image=self.salir_img,
            pos=(self.SCREEN_WIDTH//2 + 180, int(self.SCREEN_HEIGHT*0.75)),  # Más a la derecha
            text_input="",
            font=self.get_font(75),
            base_color="#d7fcd4",
            hovering_color="White",
            size=(300, 90)
        )

        # Botón "UNIRSE"
        self.UNIRSE_BUTTON = Button(
            image=self.unirse_img,
            pos=(self.SCREEN_WIDTH//2 - 150, 420),  # Izquierda
            text_input="",
            font=self.get_font(50),
            base_color="#d7fcd4",
            hovering_color="White",
            size=(250, 100)
        )

        # Botón "CREAR"
        self.CREAR_BUTTON = Button(
            image=self.crear_img,
            pos=(self.SCREEN_WIDTH//2 + 150, 420),  # Derecha
            text_input="",
            font=self.get_font(50),
            base_color="#d7fcd4",
            hovering_color="White",
            size=(250, 100)
        )
        
        # Botón "VOLVER" en pantalla de juego
        self.PLAY_BACK = Button(
            image=self.volver_img,
            pos=(self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT * 0.75),
            text_input="",
            font=self.get_font(75),
            base_color="White",
            hovering_color="Green"
        )

        # Fuente pequeña para botones secundarios
        small_font = self.get_font(30)

        # Botón "Unirse por IP"-> Conectar
        self.JOIN_IP_BUTTON = Button(
            image=None,
            pos=(self.SCREEN_WIDTH//2, 490),
            text_input="Conectar",
            font=small_font,
            base_color="#d7fcd4",
            hovering_color="White",
            size=(200, 50)
        )

        # Botón "VOLVER" en menú de unirse
        self.JOIN_BACK_BUTTON = Button(
            image=self.volver_img,
            pos=(self.SCREEN_WIDTH//2 + 150, self.SCREEN_HEIGHT * 0.85),
            text_input="",
            font=self.get_font(75),
            base_color="White",
            hovering_color="Green"
        )

        # Botón "ACTUALIZAR" en menú de unirse
        self.JOIN_REFREHS_BUTTON = Button(
            image=self.actualizar_img,
            pos=(self.SCREEN_WIDTH//2 - 150, self.SCREEN_HEIGHT * 0.85),
            text_input="",
            font=self.get_font(75),
            base_color="White",
            hovering_color="Green"
        )

        # Botón "Crear Partida"
        self.CREATE_GAME_BUTTON = Button(
            image=None,
            pos=(self.SCREEN_WIDTH//2, 490),
            text_input="Crear Partida",
            font=small_font,
            base_color="#d7fcd4",
            hovering_color="White",
            size=(200, 50)
        )

        # Botón "VOLVER" en menú de crear partida
        self.CREATE_BACK_BUTTON = Button(
            image=self.volver_img,
            pos=(self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT * 0.85),
            text_input="",
            font=self.get_font(75),
            base_color="White",
            hovering_color="Green"
        )

        # Botón "INICIAR PARTIDA" en pantalla de Lobby
        self.PLAY_GAME_BUTTON = Button(
            image=self.iniciar_juego_img,
            pos=(self.SCREEN_WIDTH//2 - 150, self.SCREEN_HEIGHT * 0.85),
            text_input="",
            font=self.get_font(75),
            base_color="White",
            hovering_color="Green"
        )

        # Botón "VOLVER" en menú lobby
        self.LOBBY_BACK_BUTTON = Button(
            image=self.volver_img,
            pos=(self.SCREEN_WIDTH//2 + 150, self.SCREEN_HEIGHT * 0.85),
            text_input="",
            font=self.get_font(75),
            base_color="White",
            hovering_color="Green"
        )

        # Botón "enviar mensaje" en menu lobby
        self.SEND_MS_BUTTON = Button(
            image=None,
            pos=(self.SCREEN_WIDTH//2, 530),
            text_input="Enviar Mensaje",
            font=small_font,
            base_color="#d7fcd4",
            hovering_color="White",
            size=(200, 50)
        )
        # Ajustar la posicion de los creditos
        self.credits_x_pos = self.SCREEN_WIDTH
        self.credits_y_pos = int(self.SCREEN_HEIGHT * 0.95)

        # Nota: La posición de los créditos ya no se define aquí. Ahora se hace en init_components() para que se reajuste si se cambia el tamaño de la ventana.


        self.init_input_boxes()

    def init_input_boxes(self):
        small_font = self.get_font(30)   # Fuente un poco más grande para los cuadros de texto
        smaller_font = self.get_font(20) # Fuente más pequeña para las etiquetas (Nombre, Contraseña, etc.)

        # Cuadro de texto para ingresar IP (Unirse a partida)
        ####self.ip_input_box = InputBox(self.SCREEN_WIDTH//2 - 30, 340, 300, 40, small_font)
        #       self.ip_input_box = pygame.Rect(100, 340, 300, 40)
        #pygame.draw.rect(screen, self.color, server_rect)
        #pygame.draw.rect(screen, self.color, server_rect, 2)
        #self.rect         = pygame.Rect(0, 0, *self.current_size)
        #self.ip_input_box.center  = (110, 350, 300, 40)
        
        # Cuadro de texto para ingresar contraseña al unirse
        self.join_password_input_box = InputBox(self.SCREEN_WIDTH//2 - 30, 390, 300, 40, small_font)
        # Input para nombre de jugador al unirse (nuevo)
        self.join_player_input_box = InputBox(self.SCREEN_WIDTH//2 - 30, 340, 300, 40, small_font)

        # Cuadro de texto para crear partida → Nombre de la sala
        self.name_input_box = InputBox(self.SCREEN_WIDTH//2 + 100, 240, 300, 40, small_font)
        # Cuadro de texto para crear partida → Contraseña
        self.password_input_box = InputBox(self.SCREEN_WIDTH//2 + 100, 280, 300, 40, small_font)
        # Cuadro de texto para crear partida → Máximo de jugadores
        self.max_players_input_box = InputBox(self.SCREEN_WIDTH//2 + 100, 320, 300, 40, small_font)

        # Texto que acompaña a los cuadros (como etiquetas al lado)
        self.name_text = smaller_font.render("Nombre:", True, "#d7fcd4")
        self.password_text = smaller_font.render("Contraseña:", True, "#d7fcd4")
        self.max_players_text = smaller_font.render("Jugadores:", True, "#d7fcd4")

        # Cuadro de texto para lobby → Nombre de la sala
        #self.messages_input_box = InputBox(self.SCREEN_WIDTH//2 + 100, 240, 300, 40, small_font)
        # Cuadro de texto para lobby → Mensaje
        self.message_input_box = InputBox(self.SCREEN_WIDTH//2 + 100, 320, 300, 40, small_font)

        # Texto que acompaña a los cuadros (como etiquetas al lado)
        self.messages_text = smaller_font.render("CHAT", True, "#d7fcd4")
        self.message_text = smaller_font.render("Mensaje:", True, "#d7fcd4")

        # Lista de partidas disponibles (ejemplo para mostrar en pantalla)
        self.available_games = ["Partida 1 - 192.168.1.1", "Partida 2 - 192.168.1.2", "Partida 3 - 192.168.1.3"]

    def update_animation(self, delta_time):
        # Aumenta el ángulo de las imágenes giratorias (animación de los lados)
        self.angulo_izquierda = (self.angulo_izquierda + 50 * delta_time) % 360
        self.angulo_derecha = (self.angulo_derecha + 50 * delta_time) % 360

        # Mueve los créditos hacia la izquierda
        self.credits_x_pos -= 100 * delta_time
        # Si los créditos salen de la pantalla, reinicia la posición (efecto bucle infinito)
        if self.credits_x_pos < -self.credits_surface.get_width():
            self.credits_x_pos = self.SCREEN_WIDTH


    def draw_background(self):
        # Dibuja la imagen de fondo en toda la pantalla
        self.SCREEN.blit(self.fondo_img, (0, 0))

        # Rota la animación de la izquierda según el ángulo actual
        rotada_izquierda = pygame.transform.rotate(self.animacion_fondo_img, self.angulo_izquierda)
        rect_izquierda = rotada_izquierda.get_rect(center=self.pos_izquierda)  # Mantiene centrada la animación
        self.SCREEN.blit(rotada_izquierda, rect_izquierda)  # Dibuja la animación girada en la pantalla

        # Rota la animación de la derecha según el ángulo actual
        rotada_derecha = pygame.transform.rotate(self.animacion_fondo_img, self.angulo_derecha)
        rect_derecha = rotada_derecha.get_rect(center=self.pos_derecha)  # Mantiene centrada la animación
        self.SCREEN.blit(rotada_derecha, rect_derecha)  # Dibuja la animación girada en la pantalla

        # Dibuja los créditos que se mueven en la parte inferior
        self.SCREEN.blit(self.credits_surface, (self.credits_x_pos, self.credits_y_pos))


    def draw_main_menu(self):
        # Calcula la posición del título (centrado arriba de la pantalla)
        title_rect = self.titulo_img.get_rect(center=(self.SCREEN_WIDTH//2, int(self.SCREEN_HEIGHT*0.25)))
        self.SCREEN.blit(self.titulo_img, title_rect)  # Dibuja la imagen del título

        # Obtiene la posición actual del mouse
        MENU_MOUSE_POS = pygame.mouse.get_pos()

        # Actualiza los botones principales (Jugar, Reglas, Salir)
        for button in [self.JUGAR_BUTTON, self.REGLAS_BUTTON, self.SALIR_BUTTON]:
            button.check_hover(MENU_MOUSE_POS)  # Revisa si el mouse está encima (hover)
            button.update(self.SCREEN)  # Dibuja el botón en pantalla
        
        return MENU_MOUSE_POS  # Devuelve la posición del mouse para detectar clicks

    def draw_play_menu(self):
        # Obtiene la posición actual del mouse
        MENU_MOUSE_POS = pygame.mouse.get_pos()

        # Actualiza los botones del menú "Jugar" (Unirse, Crear, Volver)
        for button in [self.UNIRSE_BUTTON, self.CREAR_BUTTON, self.PLAY_BACK]:
            button.check_hover(MENU_MOUSE_POS)  # Revisa si el mouse está encima (hover)
            button.update(self.SCREEN)  # Dibuja el botón en pantalla

        return MENU_MOUSE_POS  # Devuelve la posición del mouse para detectar clicks

    def draw_join_menu(self):
        self.servers = self.network_manager.servers
        MENU_MOUSE_POS = pygame.mouse.get_pos()
        smaller_font = self.get_font(20)
        
        # Usamos exactamente el mismo recuadro y posición que draw_create_menu
        box_width = 800
        box_height = 250
        box_x = self.SCREEN_WIDTH // 2 - box_width // 2
        box_y = self.SCREEN_HEIGHT // 2 - box_height // 2 + 50
    
       # Dibuja el mismo rectángulo gris oscuro (igual que Crear Partida)
        pygame.draw.rect(self.SCREEN, (50, 50, 50), (box_x, box_y, box_width, box_height))

        # Coordenadas base iguales a Crear Partida (etiquetas a la izquierda, inputs a la derecha)
        input_x = box_x + 260  # Posición horizontal de los input
        input_req_x = box_x  # Posición horizontal de las etiquetas de los inputs

        # Dibuja el rectángulo para el campo de IP
        rectNameServer = pygame.draw.rect(self.SCREEN, (255, 255, 254), (input_x + 100, box_y + 35, 420, 48), 2)
        self.is_hovered = rectNameServer.collidepoint(MENU_MOUSE_POS)

        # Lista de servidores
        """
        if self.network.servers:
            y_offset = 160
            for i, server in enumerate(self.network.servers):
                server_rect = pygame.Rect(100, y_offset, 600, 60)
                is_hovered = server_rect.collidepoint(mouse_pos)
                
                color = LIGHT_BLUE if is_hovered else GRAY
                pygame.draw.rect(screen, color, server_rect)
                pygame.draw.rect(screen, BLACK, server_rect, 2)
                
                # Información del servidor
                server_text = font_small.render(
                    f"{server['name']} - {server['ip']} - Jugadores: {server['current_players']}/{server['max_players']} - Creado: {server['created_at']}",
                    True, BLACK
                )
                screen.blit(server_text, (110, y_offset + 20))
                
                # Selección del servidor
                for event in pygame.event.get():
                    if event.type == MOUSEBUTTONDOWN and event.button == 1 and is_hovered:
                        self.selected_server = server
                        if self.network.connect_to_server(server):
                            self.current_screen = "game_lobby"
                
                y_offset += 70
        else:
            no_servers = font_medium.render("No se encontraron servidores", True, BLACK)
            screen.blit(no_servers, (SCREEN_WIDTH//2 - no_servers.get_width()//2, 300))
        
        """

        # Dibujar el rectángulo de Nombre del servidor
        color = (0, 0, 255) if self.isSeletedServer else (100,0,150) if self.is_hovered else (90, 90, 90)
        pygame.draw.rect(self.SCREEN, color, rectNameServer)
        pygame.draw.rect(self.SCREEN, (0, 0, 0), rectNameServer, 2)

        if self.servers:
            # Información del servidor
            server_text = smaller_font.render(f"{self.servers[0]['name']}: Jugadores {self.servers[0]['currentPlayers']}/{self.servers[0]['max_players']}", True, (0, 0, 0))
            self.SCREEN.blit(server_text, (input_req_x + 370, box_y + 50))
                       
        else:
            noServers = smaller_font.render("No hay servidores :( ", True, (0,0,0))
            self.SCREEN.blit(noServers, (input_req_x + 370, box_y + 50))
        
        if self.response == "No ha seleccionado un servidor":
            ####noSelectServer = smaller_font.render("No ha seleccionado un servidor", True, (0,0,0))
            ####self.SCREEN.blit(noSelectServer, (input_req_x + 100, box_y + 70)) 
            #-------------------------------
            if pygame.time.get_ticks() < self.no_server_until:
                noSelectServer = smaller_font.render("Seleccione", True, (255,255,255))
                self.SCREEN.blit(noSelectServer, (input_req_x + 575, box_y + 150)) 
                noSelectServer2 = smaller_font.render("un servidor", True, (255,255,255))
                self.SCREEN.blit(noSelectServer2, (input_req_x + 575, box_y + 175)) 
            else:
                self.response = None
            #-------------------------------
            
        # Contraseña incorrecta
        elif self.response == "wrongPassword":
            ####wrongPassword = smaller_font.render("Contraseña incorrecta", True, (0,0,0))
            ####self.SCREEN.blit(wrongPassword, (input_req_x + 100, box_y + 150)) 
            #-------------------------------
            if pygame.time.get_ticks() < self.wrong_password_until:
                wrongPassword = smaller_font.render("Contraseña", True, (255,255,255))
                self.SCREEN.blit(wrongPassword, (input_req_x + 575, box_y + 150))
                wrongPassword2 = smaller_font.render("Incorrecta", True, (255,255,255))
                self.SCREEN.blit(wrongPassword2, (input_req_x + 575, box_y + 175))
            else:
                self.response = None
            #----------------------------------

        # Servidor lleno
        elif self.response == "fullserver":
            ####fullserver = smaller_font.render("servidor lleno", True, (0,0,0))
            ####self.SCREEN.blit(fullserver, (input_req_x + 100, box_y + 150))
            #-------------------------------
            if pygame.time.get_ticks() < self.fullserver_until:
                fullserver = smaller_font.render("Servidor", True, (255,255,255))
                self.SCREEN.blit(fullserver, (input_req_x + 575, box_y + 150))
                fullserver2 = smaller_font.render("Lleno", True, (255,255,255))
                self.SCREEN.blit(fullserver2, (input_req_x + 575, box_y + 175))
            else:
                self.response = None
            #-------------------------------
        # Etiqueta para el campo de IP
        ip_label = smaller_font.render("Nombre Servidor:", True, "#d7fcd4")
        self.SCREEN.blit(ip_label, (input_req_x + 40 , box_y + 50))
    
        """#### Caja de texto para contraseña
        self.join_password_input_box.draw(self.SCREEN)
        self.join_password_input_box.rect.topleft = (input_x + 100 , box_y + 120)

        # Etiqueta para el campo de contraseña
        pw_label = smaller_font.render("Contraseña:", True, "#d7fcd4")
        self.SCREEN.blit(pw_label, (input_req_x + 140, box_y + 130))
        ####"""
        #------------------------------------
       
        # Etiqueta y caja para Nombre Jugador (nuevo)
        player_label = smaller_font.render("Nombre Jugador:", True, "#d7fcd4")
        self.SCREEN.blit(player_label, (input_req_x + 60, box_y + 100))
        self.join_player_input_box.draw(self.SCREEN)
        self.join_player_input_box.rect.topleft = (input_x + 100, box_y + 90)

        # Etiqueta y caja para Contraseña
        pw_label = smaller_font.render("Contraseña:", True, "#d7fcd4")
        self.SCREEN.blit(pw_label, (input_req_x + 140, box_y + 150))
        self.join_password_input_box.draw(self.SCREEN)
        self.join_password_input_box.rect.topleft = (input_x + 100 , box_y + 140)
        #-------------------------------------

        # Ajustar posición del botón para que quede debajo del segundo input
        self.JOIN_IP_BUTTON.check_hover(MENU_MOUSE_POS)
        self.JOIN_IP_BUTTON.update(self.SCREEN)
        self.JOIN_IP_BUTTON.rect.center = (self.SCREEN_WIDTH//2, box_y + 200)  # 90-> 170
    
        # Botón actualizar
        self.JOIN_REFREHS_BUTTON.check_hover(MENU_MOUSE_POS)
        self.JOIN_REFREHS_BUTTON.update(self.SCREEN)

        # Botón volver
        self.JOIN_BACK_BUTTON.check_hover(MENU_MOUSE_POS)
        self.JOIN_BACK_BUTTON.update(self.SCREEN)
    
        return MENU_MOUSE_POS

    def draw_create_menu(self):
        MENU_MOUSE_POS = pygame.mouse.get_pos()
        smaller_font = self.get_font(20)  # Fuente más pequeña para los textos en el menú de crear partida

        box_width = 700  # Ancho de la caja donde se configuran los datos de la partida
        box_height = 200  # Alto de la caja
        # Centrar la caja horizontalmente y posicionarla verticalmente
        box_x = self.SCREEN_WIDTH // 2 - box_width // 2
        box_y = self.SCREEN_HEIGHT // 2 - box_height // 2 + 50

        # Dibuja un rectángulo gris oscuro como fondo del menú "Crear Partida"
        pygame.draw.rect(self.SCREEN, (50, 50, 50), (box_x, box_y, box_width, box_height))

        # Título "Crear Partida" en la parte superior de la caja
        text_surface = smaller_font.render("Crear Partida", True, "#d7fcd4")
        text_rect = text_surface.get_rect(center=(self.SCREEN_WIDTH//2, box_y + 20))
        self.SCREEN.blit(text_surface, text_rect)

        # Coordenadas base para ubicar los campos de entrada
        input_x = box_x + 250  # Posición horizontal de los input (nombre, contraseña, jugadores)
        input_req_x = box_x + 20  # Posición horizontal de las etiquetas de los inputs

        # Caja de texto para el nombre de la partida
        self.name_input_box.draw(self.SCREEN)
        self.name_input_box.rect.topleft = (input_x, box_y + 40)

        # Caja de texto para la contraseña
        self.password_input_box.draw(self.SCREEN)
        self.password_input_box.rect.topleft = (input_x, box_y + 80)

        # Caja de texto para cantidad máxima de jugadores
        self.max_players_input_box.draw(self.SCREEN)
        self.max_players_input_box.rect.topleft = (input_x, box_y + 120)

        # Botón para confirmar y crear la partida
        self.CREATE_GAME_BUTTON.check_hover(MENU_MOUSE_POS)  # Revisa si el mouse está encima
        self.CREATE_GAME_BUTTON.update(self.SCREEN)  # Dibuja el botón
        self.CREATE_GAME_BUTTON.rect.center = (self.SCREEN_WIDTH//2, box_y + 170)  # Lo centra abajo en la caja

        # Botón para volver atrás
        self.CREATE_BACK_BUTTON.check_hover(MENU_MOUSE_POS)
        self.CREATE_BACK_BUTTON.update(self.SCREEN)

        # Etiquetas a la izquierda de cada input
        self.SCREEN.blit(self.name_text, (input_req_x, box_y + 40))       # "Nombre:"
        self.SCREEN.blit(self.password_text, (input_req_x, box_y + 80))   # "Contraseña:"
        self.SCREEN.blit(self.max_players_text, (input_req_x, box_y + 120))  # "Jugadores:"

        return MENU_MOUSE_POS  # Devuelve la posición del mouse

    def draw_lobby(self):
        MENU_MOUSE_POS = pygame.mouse.get_pos()
        smaller_font = self.get_font(20)  # Fuente más pequeña para los textos en el menú de crear partida

        box_width = 700  # Ancho de la caja donde se configuran los datos de la partida
        box_height = 200  # Alto de la caja
        # Centrar la caja horizontalmente y posicionarla verticalmente
        box_x = self.SCREEN_WIDTH // 2 - box_width // 2
        box_y = self.SCREEN_HEIGHT // 2 - box_height // 2 + 50

        # Dibuja un rectángulo gris oscuro como fondo del menú "Crear Partida"
        pygame.draw.rect(self.SCREEN, (50, 50, 50), (box_x, box_y - 20, box_width, box_height + 75))

        #Mostrar información del servidor
        if self.network_manager.currentServer:
            # Título "Lobby" en la parte superior de la caja del CREADOR
            text_surface = smaller_font.render(f"Servidor:{self.network_manager.currentServer['name']} Jugadores:{self.network_manager.currentServer['currentPlayers']}/{self.network_manager.currentServer['max_players']}", True,  "#d7fcd4")
        elif self.selectedServer:
            # Título "Lobby" en la parte superior de la caja del JUGADOR
            text_surface = smaller_font.render(f"Conectado a:{self.selectedServer['name']} Jugadores:{self.selectedServer['currentPlayers']}/{self.selectedServer['max_players']}", True,  "#d7fcd4")
        
        text_rect = text_surface.get_rect(center=(self.SCREEN_WIDTH//2, box_y)) #+20 en y
        self.SCREEN.blit(text_surface, text_rect)

        # Coordenadas base para ubicar los campos de entrada
        input_x = box_x + 250  # Posición horizontal de los input (nombre, contraseña, jugadores)
        input_req_x = box_x + 20  # Posición horizontal de las etiquetas de los inputs

        # Caja de texto para mensajes
        # Área de chat
        pygame.draw.rect(self.SCREEN, (50,50,50), (box_x + 200, box_y + 10, box_x + 150, box_y - 165))
        pygame.draw.rect(self.SCREEN, (255,255,255), (box_x + 200, box_y + 10, box_x + 150, box_y - 165), 2)
        
        # Mostrar mensajes
        y_offset = box_y + 20
        with self.chatLock:
            #recentMsg = self.messages[-5:]
            recentMsg = self.network_manager.messagesServer[-5:]

        for msg in recentMsg:  # Mostrar solo los últimos 5 mensajes
            msg_surface = smaller_font.render(msg, True, (0,0,0))
            # Mensaje muy largo, lo recorta...
            if msg_surface.get_width() > box_x + 200 -10:
                msg = msg[:17]+"..."
                msg_surface = smaller_font.render(msg, True, (0,0,0))
            self.SCREEN.blit(msg_surface, (input_x - 30, y_offset))
            y_offset += 25

        # Caja de texto para escribir mensajes
        self.message_input_box.draw(self.SCREEN)
        self.message_input_box.rect.topleft = (input_x - 50, box_y + 160)   #+120

        # Botón para enviar mensaje al chat
        self.SEND_MS_BUTTON.check_hover(MENU_MOUSE_POS)  # Revisa si el mouse está encima
        self.SEND_MS_BUTTON.update(self.SCREEN)  # Dibuja el botón
        self.SEND_MS_BUTTON.rect.center = (self.SCREEN_WIDTH//2, box_y + 220)  # Lo centra abajo en la caja +170

        # Botón iniciar partida (Solo para el Host)
        if self.network_manager.is_host:
            canStart = self.network_manager.canStartGame()
            self.PLAY_GAME_BUTTON.check_hover(MENU_MOUSE_POS)
            if canStart:
                self.PLAY_GAME_BUTTON.check_hover(MENU_MOUSE_POS)
                self.PLAY_GAME_BUTTON.update(self.SCREEN)
        elif self.playGamePlayer:
            self.PLAY_GAME_BUTTON.check_hover(MENU_MOUSE_POS)
            self.PLAY_GAME_BUTTON.update(self.SCREEN)
        
        if self.process_received_messages()=="launch_ui2":
            self.playGamePlayer = True

        # Botón para volver atrás
        self.LOBBY_BACK_BUTTON.check_hover(MENU_MOUSE_POS)
        self.LOBBY_BACK_BUTTON.update(self.SCREEN)

        # Etiquetas a la izquierda de cada input
        self.SCREEN.blit(self.messages_text, (input_req_x, box_y + 20 ))       # "CHAT:"   +40
        self.SCREEN.blit(self.message_text, (input_req_x, box_y + 170))  # "Mensaje:" +120

        return MENU_MOUSE_POS  # Devuelve la posición del mouse
    
    # ===========================
    # Clase para mostrar las reglas del juego (con scroll, clip y word-wrap)
    # ===========================
    class RulesTextBox:
        def __init__(self, x, y, w, h, font, text_lines, extra_bottom_space=50):
            self.rect = pygame.Rect(x, y, w, h)
            self.font = font
            # acepta lista de líneas o string multilínea
            if isinstance(text_lines, list):
                raw = "\n".join(text_lines)
            else:
                raw = str(text_lines)
            # separar en líneas base por saltos de línea
            self.lines = raw.splitlines()
            # medidas y estilos
            self.padding = 16  # margen interior (espacio a izquierda/derecha)
            self.line_height = self.font.size("Tg")[1] + 6
            self.offset = 0  # desplazamiento vertical (0 = tope)
            self.extra_bottom_space = extra_bottom_space
            # genera las líneas envueltas al ancho del cuadro
            self._wrap_lines()
            # calcula máximo desplazamiento teniendo en cuenta espacio extra
            total_height = len(self.wrapped_lines) * self.line_height + self.padding * 2 + self.extra_bottom_space
            self.max_offset = max(0, total_height - self.rect.h)

        def _wrap_lines(self):
            max_w = max(10, self.rect.w - self.padding * 2)
            wrapped = []
            for line in self.lines:
                if line.strip() == "":
                    wrapped.append("")  # línea vacía preservada
                    continue
                words = line.split(" ")
                cur = ""
                for word in words:
                    test = (cur + " " + word) if cur else word
                    if self.font.size(test)[0] <= max_w:
                        cur = test
                    else:
                        if cur:
                            wrapped.append(cur)
                        # si la palabra individual es más larga que el ancho, partir por caracteres
                        if self.font.size(word)[0] > max_w:
                            part = ""
                            for ch in word:
                                tp = part + ch
                                if self.font.size(tp)[0] <= max_w:
                                    part = tp
                                else:
                                    if part:
                                        wrapped.append(part)
                                    part = ch
                            if part:
                                cur = part
                            else:
                                cur = ""
                        else:
                            cur = word
                if cur:
                    wrapped.append(cur)
            self.wrapped_lines = wrapped

        def draw(self, screen):
            # fondo del contenedor (sólido)
            pygame.draw.rect(screen, (35, 35, 35), self.rect)
            # guardar clip anterior y establecer clip para que el texto no desborde
            old_clip = screen.get_clip()
            screen.set_clip(self.rect)
            start_y = self.rect.y + self.padding + int(self.offset)
            # dibuja cada línea con fondo sólido detrás y respeta padding
            for i, line in enumerate(self.wrapped_lines):
                line_y = start_y + i * self.line_height
                # sólo dibujar si intersecta la zona visible
                if line_y + self.line_height < self.rect.y or line_y > self.rect.y + self.rect.h:
                    continue
                # fondo sólido detrás de la línea (con margen a los lados)
                bg_rect = pygame.Rect(self.rect.x + 4, line_y - 4, self.rect.w - 8, self.line_height + 8)
                pygame.draw.rect(screen, (45, 50, 45), bg_rect)
                # render del texto encima con margen izquierdo
                text_surf = self.font.render(line, True, "#d7fcd4")
                screen.blit(text_surf, (self.rect.x + self.padding, line_y))
            # restaura clip anterior
            screen.set_clip(old_clip)
            # borde
            pygame.draw.rect(screen, (90, 90, 90), self.rect, 2)

        def update(self, events):
            # procesa eventos para scroll (MOUSEWHEEL y botones 4/5)
            for event in events:
                if event.type == pygame.MOUSEWHEEL:
                    # event.y positivo = rueda arriba
                    self.offset += event.y * 30
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:  # rueda arriba
                        self.offset += 30
                    elif event.button == 5:  # rueda abajo
                        self.offset -= 30
            # recalcula límites y clamp (incluye espacio extra)
            total_height = len(self.wrapped_lines) * self.line_height + self.padding * 2 + self.extra_bottom_space
            self.max_offset = max(0, total_height - self.rect.h)
            if self.offset > 0:
                self.offset = 0
            if self.offset < -self.max_offset:
                self.offset = -self.max_offset

    def options(self):
        pygame.display.set_caption("Opciones")
        # Texto completo de reglas (se puede ajustar)
        game_rules = """Rummy 500
Objetivo: Ser el último jugador con menos de 500 puntos.

Jugadores: 2 - 13

Mazo: 52 cartas + 1 Joker.

Cómo ganar: El último jugador en acumular menos de 500 puntos gana la partida.
Cómo perder: El primer jugador en alcanzar o superar los 500 puntos es eliminado.
Combinaciones:
• Trío: Tres cartas del mismo valor (ej: Q♥, Q♦, Q♠).
• Seguidilla: Cuatro cartas consecutivas del mismo palo (ej: ♣7, ♣8, ♣9, ♣10).

Rondas de Juego:
1. Trío y Seguidilla
2. Dos Seguidillas
3. Tres Tríos
4. Una Seguidilla y Dos Tríos (Ronda Completa): Para finalizar esta ronda, el jugador debe descartar las diez cartas (la seguidilla de cuatro y los dos tríos) en un solo turno.

Puntuación:
• Cartas 2 - 9: 5 puntos
• Cartas 10 - K: 10 puntos
• As: 15 puntos
• Joker: 25 puntos

Desarrollo del Juego:
1. Inicio: Cada jugador recibe 10 cartas. Se coloca una carta boca arriba del mazo en el centro de la mesa para iniciar el descarte. Se designa un jugador como MANO.
2. Turno del MANO: Para la siguiente ronda, el rol de MANO pasa al jugador a la izquierda del MANO actual.
3. Primera Toma de la Carta Central: Solo el jugador MANO tiene la primera oportunidad de tomar la carta boca arriba del centro. Si decide tomarla, debe descartar una carta de su mano para mantener un total de 10 cartas. Si el MANO no toma la carta central, se pasa a la siguiente fase de toma.
4. Segunda Oportunidad de Toma de la Carta Central: Si el MANO no tomó la carta central, los demás jugadores, en orden hacia la izquierda del MANO, tienen la oportunidad de tomarla. El primer jugador que la tome debe robar una carta adicional del mazo como penalización, quedando con 12 cartas. Si nadie toma la carta central en esta segunda oportunidad, la carta se QUEMA y se descarta, quedando fuera de juego.
5. Turno Regular del Jugador: Después de la fase de toma de la carta central (haya sido tomada o quemada), y durante el resto de su turno, cada jugador puede realizar una de las siguientes acciones:
o Tomar la carta superior del mazo boca abajo (solo si no agarró la carta boca arriba o si agarra como penalización).
o Bajarse: Mostrar sobre la mesa las combinaciones de cartas requeridas para la ronda actual (tríos o seguidillas). Se puede usar un Joker para completar una combinación. Un Joker ya bajado puede ser reemplazado por la carta que representa y utilizado en otra combinación propia.
o Agregar cartas: Añadir cartas válidas a sus propias combinaciones ya bajadas (antes de descartar).
o Descartar: Colocar una carta boca arriba en el centro de la mesa para finalizar su turno.
6. Fin de la Ronda: Una ronda termina cuando un jugador se queda sin cartas al bajar todas sus combinaciones requeridas (y descartar si es necesario). El jugador que se quedó sin cartas será el primero en actuar en la siguiente ronda.
7. Puntuación de la Ronda: Los jugadores que no lograron bajarse suman los puntos de las cartas que aún tienen en su mano.
8. Fin de la Partida: El juego continúa a lo largo de las cuatro rondas. El ganador es el jugador con la menor puntuación total al final de las cuatro rondas, o el último jugador que no haya alcanzado o superado los 500 puntos."""
        # crear la caja de reglas dentro de Options (usa la clase anidada)
        box_w, box_h = 760, 400
        box_x = self.SCREEN_WIDTH // 2 - box_w // 2
        box_y = 140
        rules_box = self.RulesTextBox(box_x + 20, box_y + 20, box_w - 40, box_h - 40, self.get_font(18), game_rules)

        # Crear botón VOLVER una sola vez y posicionarlo dentro del contenedor
        options_back = Button(
            image=self.volver_img,                    # usar asset de botón "volver"
            pos=(self.SCREEN_WIDTH//2, box_y + box_h + 40),
            text_input="",                            # sin texto (solo imagen)
            font=self.get_font(50),
            base_color="White",
            hovering_color="Green",
            size=(250, 110)                            # tamaño del botón (ajusta si es necesario)
        )

        while True:  # Bucle principal de la pantalla de opciones
            delta_time = self.clock.tick(60) / 1000.0  # Controla FPS y calcula delta_time
            self.update_animation(delta_time)  # Actualiza la animación de fondo

            # Captura eventos una sola vez y pásalos a la caja de reglas
            events = pygame.event.get()

            # Manejo eventos globales
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                #Cuando la ventana cambia de tamaño, volvemos a calcular la posición y el tamaño de la caja de reglas y del botón "volver" para que todo se adapte.
                elif event.type == pygame.VIDEORESIZE:
                    self.SCREEN_WIDTH, self.SCREEN_HEIGHT = event.size
                    self.SCREEN = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.RESIZABLE)
                    # Reajustamos las posiciones y tamaños
                    box_w, box_h = int(self.SCREEN_WIDTH * 0.7), int(self.SCREEN_HEIGHT * 0.6)
                    box_x = self.SCREEN_WIDTH // 2 - box_w // 2
                    box_y = self.SCREEN_HEIGHT // 2 - box_h // 2
                    rules_box.rect.topleft = (box_x + 20, box_y + 20)
                    rules_box._wrap_lines()
                    options_back.x_pos = self.SCREEN_WIDTH // 2
                    options_back.y_pos = box_y + box_h + 40

            # Dibuja fondo y contenedor
            self.draw_background()
            # Contenedor centrado (fondo oscuro)
            self.SCREEN.fill((50, 50, 50), (self.SCREEN_WIDTH//2 - box_w//2, box_y, box_w, box_h))

            # Título
            options_text = self.get_font(45).render("Reglas de Rummy 500", True, "White")
            options_rect = options_text.get_rect(center=(self.SCREEN_WIDTH//2, 100))
            # Fondo gris detrás del texto (margen horizontal y vertical)
            bg_rect = options_rect.inflate(40, 18)  # ajusta el padding si quieres más/menos espacio
            pygame.draw.rect(self.SCREEN, (80, 80, 80), bg_rect, border_radius=6)
            
            self.SCREEN.blit(options_text, options_rect)

            # Actualizar y dibujar la caja de reglas (usa clipping para que el texto no salga)
            rules_box.update(events)
            rules_box.draw(self.SCREEN)

            # Botón VOLVER
            mouse_pos = pygame.mouse.get_pos()
            options_back.check_hover(mouse_pos)
            options_back.update(self.SCREEN)

            # detectar click en VOLVER
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if options_back.checkForInput(mouse_pos):
                        return

            pygame.display.update()

    def lanzar_juego_ui2(self):
        import ui2
        pygame.quit()  # Cierra la ventana actual de Pygame
        ui2.main()     # Lanza el juego principal de ui2.py
    
    def play_click(self):
        self.click_sound.play()
    

    def handle_events(self):
        for event in pygame.event.get():  # Recorre todos los eventos de Pygame
            if event.type == pygame.QUIT:  # Si se cierra la ventana
                return False  # Finaliza el programa
            # Cada vez que el usuario cambia el tamaño de la ventana, ajustamos la interfaz completa para que se adapte.
            elif event.type == pygame.VIDEORESIZE:
                self.SCREEN_WIDTH, self.SCREEN_HEIGHT = event.size
                self.SCREEN = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.RESIZABLE)
                self.init_components()
            

            if event.type == pygame.MOUSEBUTTONDOWN:  # Si se hace clic con el mouse
                if self.current_screen == "main":  # Si estamos en el menú principal
                    if self.JUGAR_BUTTON.checkForInput(event.pos):  # Clic en "JUGAR"
                        self.play_click()
                        self.current_screen = "play"  # Cambia a la pantalla de jugar
                    elif self.REGLAS_BUTTON.checkForInput(event.pos):  # Clic en "REGLAS"
                        self.play_click()
                        self.options()  # Abre la pantalla de opciones/reglas
                    elif self.SALIR_BUTTON.checkForInput(event.pos):  # Clic en "SALIR"
                        self.play_click()
                        return False  # Sale del juego

                elif self.current_screen == "play":  # Si estamos en el menú de "jugar"
                    if self.PLAY_BACK.checkForInput(event.pos):  # Botón "volver"
                        self.play_click()
                        self.current_screen = "main"  # Regresa al menú principal
                    elif self.UNIRSE_BUTTON.checkForInput(event.pos):  # Botón "unirse"
                        self.play_click()
                        self.servers = self.network_manager.discoverServers()
                        self.response = ''
                        self.current_screen = "join"  # Cambia a la pantalla de unirse
                    elif self.CREAR_BUTTON.checkForInput(event.pos):  # Botón "crear"
                        self.play_click()
                        self.current_screen = "create"  # Cambia a la pantalla de crear partida

                elif self.current_screen == "join":  # Si estamos en la pantalla de unirse
                    if event.button == 1 and self.is_hovered:
                        if self.servers:
                            self.selectedServer = self.servers[0]
                            self.isSeletedServer = True  # Activar el estado de selección
                            print(f"Acabo de seleccionar este servidor")#  {self.selectedServer}")
                    if self.JOIN_BACK_BUTTON.checkForInput(event.pos):  # Botón "volver"
                        self.play_click()
                        self.current_screen = "play"  # Regresa al menú de jugar
                        self.response = ''
                    elif self.JOIN_REFREHS_BUTTON.checkForInput(event.pos): # Botón Actualizar
                        self.play_click()
                        self.servers = self.network_manager.discoverServers()
                        self.response = ''
                    elif self.JOIN_IP_BUTTON.checkForInput(event.pos):  # Botón "conectar"
                        password = self.join_password_input_box.text  # Obtiene la contraseña
                        if self.servers:
                            self.servers[0]['password'] = password
                            if self.join_player_input_box.text != "":
                                playerName = self.join_player_input_box.text  # Convierte jugadores a número
                            else:  # Si no se escribe un número válido
                                playerName = f"Jugador {self.servers[0]['currentPlayers']}"  # Valor por defecto
                            
                            self.servers[0]['playerName'] = playerName
                            pygame.display.update()
                            
                            print(f"Esto esta en el Server {self.servers}")
                        if self.selectedServer:
                            acep, resp = self.network_manager.connectToServer(self.selectedServer)
                            if acep:
                                self.selectedServer['currentPlayers'] += 1 
                                print(f"Info de connectToServer  {(acep,resp)}")
                                print("ClaveCorrecta.... Probando")
                                self.current_screen = "lobby"
                            elif acep==False:
                                if resp=="Contraseña incorrecta":
                                    self.response = "wrongPassword"
                                    self.wrong_password_until = pygame.time.get_ticks() + 2000
                                    print("Contraseña incorrecta")
                                elif resp=="El servidor está lleno":
                                    self.response = "fullserver"
                                    self.fullserver_until = pygame.time.get_ticks() + 2000
                                    print("El servidor está lleno")
                        else:
                            self.response = "No ha seleccionado un servidor"
                            self.no_server_until = pygame.time.get_ticks() + 2000
                            print("No ha seleccionado un servidor")

                elif self.current_screen == "create":  # Si estamos en la pantalla de crear
                    if self.CREATE_BACK_BUTTON.checkForInput(event.pos):  # Botón "volver"
                        self.current_screen = "play"  # Regresa al menú de jugar
                    elif self.CREATE_GAME_BUTTON.checkForInput(event.pos):  # Botón "crear partida"
                        nombre = self.name_input_box.text  # Nombre de la partida
                        password = self.password_input_box.text  # Contraseña
                        try:
                            max_players = int(self.max_players_input_box.text)  # Convierte jugadores a número
                        except:  # Si no se escribe un número válido
                            max_players = 7  # Valor por defecto
                        # Intenta crear el servidor
                        exito = self.network_manager.start_server(nombre, password, max_players)
                        print("Servidor creado" if exito else "Error al crear servidor")
                        print(self.network_manager.host,self.network_manager.gameName)
                        self.current_screen = "lobby"  # Cambia a la pantalla lobby
                
                elif self.current_screen == "lobby":  # Si estamos en la pantalla de lobby
                    if self.LOBBY_BACK_BUTTON.checkForInput(event.pos):
                        self.current_screen = "play"
                        self.network_manager.connected_players.clear()
                        self.network_manager.stop()
                        if self.selectedServer:
                            self.selectedServer['currentPlayers'] = len(self.network_manager.connected_players)
                        print(f"Servidor cerrado...")
                    elif self.PLAY_GAME_BUTTON.checkForInput(event.pos):
                        #++++++++++++++++++++++++++++++++++++++++
                        if self.network_manager.is_host:
                            if self.network_manager.canStartGame():
                                # Hay minimo 2 jugadores conectados

                                # Envía la señal a todos los clientes game_started = True
                                self.network_manager.startGame()
                            else:
                                print("Se necesitan al menos dos jugadores")
                        else:
                            msg = self.network_manager.get_msgStartGame() #self.process_received_messages()
                            print(f"Lo que esta en el msg del lobby PLAY_BUTTON {msg}")
                            if msg == "launch_ui2":

                                return "launch_ui2"
                        #+++++++++++++++++++++++++++++++++++++++++
                        return "launch_ui2"  # <-- Indica al main que debe lanzar ui2.py
                    elif self.SEND_MS_BUTTON.checkForInput(event.pos):  # Botón "enviar mensaje"
                        msg = self.message_input_box.text.strip()
                        if msg:
                            # Enviando mensajes del servidor/jugador
                            if self.network_manager.server:
                                formattedMsg = f"Host: {msg}"
                                with self.chatLock:
                                    self.network_manager.messagesServer.append(formattedMsg)
                                    print(f"en la lista de mensajes: {self.messages}")
                                
                                # Transmitiendo a todos los jugadores
                                self.network_manager.broadcast_message(formattedMsg)

                            if self.network_manager.player:
                                success = self.network_manager.sendData(("chat_messages",msg))
                                if success:
                                    formattedMsg = f"Tú: {msg}"
                                    with self.chatLock:
                                        self.network_manager.messagesServer.append(formattedMsg)

                            # Limpiar caja de texto
                            self.message_input_box.text = ""
                            self.message_input_box.txt_surface = self.get_font(20).render("", True, (0,0,0))
                                
                        #self.messages.append(self.message_input_box.text)  # mensaje 
                        print(f" Mensajes: {self.messages}")

            # Manejo de inputs de texto dependiendo de la pantalla
            if self.current_screen == "join":  
                self.join_player_input_box.handle_event(event)  # Maneja el nuevo input
                self.join_password_input_box.handle_event(event)  # Campo de contraseña
            elif self.current_screen == "create":
                self.name_input_box.handle_event(event)  # Campo de nombre
                self.password_input_box.handle_event(event)  # Campo de contraseña
                self.max_players_input_box.handle_event(event)  # Campo de jugadores
            elif self.current_screen == "lobby":
                self.message_input_box.handle_event(event)  # Mensaje

        self.process_received_messages()
        return True  # Si nada fuerza salida, el loop sigue
    
    def process_received_messages(self):
        """Procesa los mensajes recividos de la red"""
        if hasattr(self.network_manager,'receivedData') and self.network_manager.receivedData:
            with self.network_manager.lock:
                data = self.network_manager.receivedData
                self.network_manager.receivedData = None  # Limpiar despues de procesar

            print(f"Procesando mensaje recibido en Ui.py: {data}")
            
            # Si es un mensaje para iniciar partida
            if isinstance(data,dict) and data.get("type") == "START_GAME":
                print("Comenzando el juego")
                return "launch_ui2"
                        
            # Si es la lista de jugadores
            if isinstance(data,dict) and data.get("players"):
                print("Recibiendo lista de jugadores")
                players = data.get("players")
                return players

            # Si es un mensaje de chat (string que empieza con "Host:" o "Jugador")
            if isinstance(data, str) and (data.startswith("Host:") or data.startswith("Jugador")):
                with self.chatLock:
                    # Solo agregar si no es un mensaje duplicado del propio usuario
                    if not (data.startswith("Tú:") or (self.network_manager.is_host and data.startswith("Host:"))):
                        #self.messages.append(data)
                        self.network_manager.messagesServer.append(data)
                        # Mantener solo los últimos mensajes
                        if len(self.network_manager.messagesServer) > 20:
                            self.network_manager.messagesServer = self.network_manager.messagesServer[-20:]            
            
            elif isinstance(data, tuple):
                # Procesar otros tipos de mensajes estructurados
                pass


    def update(self):
        delta_time = self.clock.tick(60) / 1000.0  
        self.update_animation(delta_time)

        # Dibuja fondo y animaciones
        self.draw_background()

        # Dibuja el título siempre, sin importar el menú
        title_rect = self.titulo_img.get_rect(center=(self.SCREEN_WIDTH//2, int(self.SCREEN_HEIGHT*0.25)))
        self.SCREEN.blit(self.titulo_img, title_rect)

        # --- ACTUALIZAR INPUT BOXES SEGÚN LA PANTALLA ---
        if self.current_screen == "join":  
            #self.ip_input_box.update()
            #-----------------------------
            self.join_player_input_box.update()  # Actualiza el nuevo input
            #-------------------------------
            self.join_password_input_box.update()
        elif self.current_screen == "create":  
            self.name_input_box.update()
            self.password_input_box.update()
            self.max_players_input_box.update()
        elif self.current_screen == "lobby":  
            #self.messages_input_box.update()
            self.message_input_box.update()

        # --- MANEJO DE CADA PANTALLA ---
        if self.current_screen == "main":  
            mouse_pos = self.draw_main_menu()
            for button in [self.JUGAR_BUTTON, self.REGLAS_BUTTON, self.SALIR_BUTTON]:
                button.check_hover(mouse_pos)

        elif self.current_screen == "play":  
            mouse_pos = self.draw_play_menu()
            for button in [self.UNIRSE_BUTTON, self.CREAR_BUTTON, self.PLAY_BACK]:
                button.check_hover(mouse_pos)

        elif self.current_screen == "join":  
            mouse_pos = self.draw_join_menu()
            for button in [self.JOIN_IP_BUTTON, self.JOIN_REFREHS_BUTTON, self.JOIN_BACK_BUTTON]:
                button.check_hover(mouse_pos)

        elif self.current_screen == "create":  
            mouse_pos = self.draw_create_menu()
            for button in [self.CREATE_GAME_BUTTON, self.CREATE_BACK_BUTTON]:
                button.check_hover(mouse_pos)
        
        elif self.current_screen == "lobby":  
            mouse_pos = self.draw_lobby()
            for button in [self.SEND_MS_BUTTON, self.PLAY_GAME_BUTTON, self.LOBBY_BACK_BUTTON]:
                button.check_hover(mouse_pos)

        elif self.current_screen == "play_game":  
            mouse_pos = self.draw_play_game()
            #for button in [self.SEND_MS_BUTTON, self.PLAY_GAME_BUTTON, self.LOBBY_BACK_BUTTON]:
            #    button.check_hover(mouse_pos)

        pygame.display.update()
        return True

