import pygame
from Round import Round
from Turn import drawCard
from Card import Card
from itertools import combinations
class Player:

    def __init__(self, id, name):
        self.playerId = id
        self.playerName = name
        self.playerPoints = 0 #Nos contiene los puntos del jugador a lo largo de la partida
        self.isHand = False #Esto nos indica si el jugador es mano o no, o en otras palabras, si está en turno
        self.playerTurn = False #Este turno se utilizará para determinar si el jugador está en su turno para comprar la carta
        self.playerHand = [] #Lista que contendrá las cartas del jugador.
        self.playerCardsPos = {} #Atributo experimental, para conocer la posición de cada carta lógica.
        self.playerCardsSelect = [] #Atributo experimental, para guardar las cartas selecc. para un movimiento.
        self.playerCardsToEx = []   # Atrib. exp., para guardar cartas para intercambiar posiciones.
        self.playMade = [] #Este array nos guarda la jugada hecha al momento de bajarse. Esta se actualiza en getOff()
        self.jugadas_bajadas = []
        #self.cardTakend = []
        self.downHand = False #Este atributo nos indica si el jugador ya se bajó o no, mostrando True o False respectivamente
        self.playerBuy = False #Este atributo nos indica si el jugador decidió comprar la carta o no
        self.playerPass = False #Atrib. experimental, para saber si el jugador en turno pasó de la carta descartada.
        self.winner = False #Nos permitirá saber si el jugador fue el ganador
        self.cardDrawn = False #Nos permitirá saber si el jugador tomó una carta en su turno (definido por isHand)
        self.connected = False #Nos permitirá saber si el jugador está conectado al servidor o no
        self.carta_elegida = False  #NUEVO PARA PRUEBA
        self.discarded = False
        self.canDiscard = True # Atrib. que permite bloquear o desbloquear el descarte (para compra de cartas)

    def __str__(self):
        return f"({self.playerId}, {self.playerName})"
    
    def __repr__(self):
        return self.__str__()

    # Mét. para permitir que el jugador seleccione cartas para jugar.
    def chooseCard(self, clickPos):
        
        # Para cada carta en la mano del jugador, verificamos si se hace click en el rectángulo asociado
        # a una carta específica y si dicha carta ha sido previamente seleccionada.
        # Si la carta no está en la lista de seleccionadas, la incluimos; si resulta que está entre las
        # seleccionadas y se vuelve a hacer click en ella, la eliminamos de la lista.
        # NOTA: Con la inclusión de un ID a cada carta este proceso se simplifica, ya que las coincidencias
        #       sólo pueden darse entre cartas con un mismo valor para todos sus atributos.
        for card in self.playerHand:
            if self.playerCardsPos[card].collidepoint(clickPos) and card not in self.playerCardsSelect:
                print(f"Carta marcada: {card}{card.id}")
                self.playerCardsSelect.append(card)
            elif self.playerCardsPos[card].collidepoint(clickPos) and card in self.playerCardsSelect:
                print(f"Carta desmarcada: {card}{card.id}")
                self.playerCardsSelect.remove(card)

    # Mét. para permitir al jugador intercambiar el lugar de sus cartas para que pueda ordenarlas.
    # Trabaja casi igual que chooseCard(), pero almacena dos cartas a lo mucho.
    def exchangeCard(self, clickPos):
        for card in self.playerHand:
            if self.playerCardsPos[card].collidepoint(clickPos) and card not in self.playerCardsToEx:
                print(f"Carta marcada para intercambiar: {card}{card.id}")
                self.playerCardsToEx.append(card)
            elif self.playerCardsPos[card].collidepoint(clickPos) and card in self.playerCardsToEx:
                print(f"Carta desmarcada para intercambiar: {card}{card.id}")
                self.playerCardsToEx.remove(card)

        # Si el jugador marca dos cartas para intercambiar (con el click derecho)...
        if len(self.playerCardsToEx) == 2:
                
                # Tomamos la posición de cada carta en la mano del jugador.
                IndexFirstCard = self.playerHand.index(self.playerCardsToEx[0])
                IndexSecondCard = self.playerHand.index(self.playerCardsToEx[1])

                # Tomamos las cartas asociadas a cada posición.
                firstCard = self.playerHand[IndexFirstCard]
                secondCard = self.playerHand[IndexSecondCard]

                # Intercambiamos posiciones en la mano del jugador.
                self.playerHand[IndexFirstCard] = secondCard
                self.playerHand[IndexSecondCard] = firstCard

                # Limpiamos la lista de intercambio para reiniciar el proceso.
                self.playerCardsToEx.clear()    
                
    #empiezan cambios por aqui
    '''def canExtendTrio(self, card, plays):
        """
        Verifica si la carta puede extender algún trío en la lista de jugadas 'plays'.
        Incluye validación interna de si cada jugada es un trío válido.
        similar a la logica de ins
        """
        for play in plays:
            # Validación interna: verificar si 'play' es un trío válido
            if len(play) < 3:
                continue
            noJokers = [c.value for c in play if not c.joker]
            if len(set(noJokers)) != 1:  # No todos los valores no-Joker son iguales
                continue
            
            # Verificar si la carta puede extender este trío
            common_value = noJokers[0]
            if card.joker:
                jokersInTrio = sum(1 for c in play if c.joker)
                if jokersInTrio < 1:
                    return True
            else:
                if card.value == common_value:
                    return True
        return False
        
    def canExtendStraight(self, card, plays):
        """
        Verifica si la carta puede extender alguna seguidilla en la lista de jugadas 'plays'.
        Incluye validación interna de si cada jugada es una seguidilla válida.
        """
        valueToRank = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
                       "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13}
        
        def rank(c, highAs=False):
            if getattr(c, "joker", False):
                return -1
            if c.value == "A" and highAs:
                return 14
            return valueToRank.get(c.value, -1)
        
        for play in plays:
            # Validación interna: verificar si 'play' es una seguidilla válida
            if len(play) < 4:
                continue
            noJokerSuit = [c.type for c in play if not c.joker]
            if len(set(noJokerSuit)) != 1:  # Todos los palos no-Joker deben ser iguales
                continue
            
            # Verificar secuencia con ranks
            common_suit = noJokerSuit[0]
            isValidStraight = False
            for highAs in (False, True):
                ranks = [rank(c, highAs) for c in play if rank(c, highAs) != -1]
                if len(ranks) < len(play) - 1:  # Demasiados Jokers
                    continue
                ranks.sort()
                if all(ranks[i] + 1 == ranks[i+1] for i in range(len(ranks)-1)):
                    isValidStraight = True
                    break
            if not isValidStraight:
                continue
            
            # Verificar si la carta puede extender esta seguidilla
            if card.joker:
                suit = common_suit
            else:
                if card.type != common_suit:
                    continue
            
            for highAs in (False, True):
                sorted_straight = sorted([c for c in play if rank(c, highAs) != -1], key=lambda c: rank(c, highAs))
                if not sorted_straight:
                    continue
                firstRank = rank(sorted_straight[0], highAs)
                lastRank = rank(sorted_straight[-1], highAs)
                cardRank = rank(card, highAs)
                
                if cardRank == firstRank - 1 or cardRank == lastRank + 1:
                    return True
        return False'''
        
    #Mét. para descartar una carta de la playerHand del jugador. Sólo se ejecuta si el jugador tiene una única
    #carta seleccionada previamente.
    def discardCard(self, selectedDiscards, round):#def discardCard(self, selectedDiscards, round, otherPlayers): asi para lo de ana
        """
        Modificado para verificar si alguna carta seleccionada puede extender una jugada en la mesa.
        - otherPlayers: Lista de otros jugadores (excluyendo al actual) para acceder a sus jugadas bajadas.
        """
        # Verificar si alguna carta puede extender jugadas propias
        '''for card in selectedDiscards:
            if self.downHand and self.playMade and not card.joker:  # Solo si el jugador se ha bajado
                if self.canExtendTrio(card, self.playMade):
                    print(f"No se puede descartar {card}: puede extender tu trio.")
                    return None
                if self.canExtendStraight(card, self.playMade) and not card.joker:
                    print(f"No se puede descartar {card}: puede extender tu seguidilla.")
                    return None
        # Verificar si alguna carta puede extender una jugada bajada de otros jugadores
        for card in selectedDiscards:
            for player in otherPlayers:
                
                if player.downHand and player.playMade and not card.joker:  # Solo si se ha bajado y tiene jugadas
                    if self.canExtendTrio(card, player.playMade):
                        print(f"No se puede descartar {card}: puede extender un trío en la jugada de {player.playerName}.")
                        return None
                    elif self.canExtendStraight(card, player.playMade) and not card.joker:
                        print(f"No se puede descartar {card}: puede extender una seguidilla en la jugada de {player.playerName}.")
                        return None'''
        # hasta aqui los cambios :))))
        if len(selectedDiscards) == 2 and self.isHand and self.cardDrawn and self.downHand:

            #Si seleccionaron dos y la primera es un Joker, se retorna una lista con ambas cartas.
            if selectedDiscards[0].joker:

                cardDiscarded = selectedDiscards[1]
                jokerDiscarded = selectedDiscards[0]
                self.playerHand.remove(cardDiscarded)
                self.playerHand.remove(jokerDiscarded)
                selectedDiscards.remove(cardDiscarded)
                selectedDiscards.remove(jokerDiscarded)
                selectedDiscards = []
                round.discards.append(jokerDiscarded)
                round.discards.append(cardDiscarded)
                self.discarded = True
                # self.isHand = False

                return [jokerDiscarded, cardDiscarded]
            #Si seleccionó dos y la segunda es un Joker, volvemos a retornar ambas cartas.
            elif selectedDiscards[1].joker:

                jokerDiscarded = selectedDiscards[1]
                cardDiscarded = selectedDiscards[0]
                self.playerHand.remove(jokerDiscarded)
                self.playerHand.remove(cardDiscarded)
                selectedDiscards.remove(cardDiscarded)
                selectedDiscards.remove(jokerDiscarded)
                selectedDiscards = []
                round.discards.append(jokerDiscarded)
                round.discards.append(cardDiscarded)
                self.discarded = True
                # self.isHand = False

                return [cardDiscarded, jokerDiscarded]
        #Si el jugador sólo seleccionó una carta para descartar, retornamos dicha carta.
        elif len(selectedDiscards) == 1 and not selectedDiscards[0].joker and self.isHand and self.cardDrawn:

            cardDiscarded = selectedDiscards[0]
            try:
                self.playerHand.remove(cardDiscarded)
                round.discards.append(cardDiscarded)
                selectedDiscards.remove(cardDiscarded)
                selectedDiscards = []
                self.discarded = True
                # self.isHand = False

                return [cardDiscarded]
            except ValueError:
                print("La carta que intenta descartar no pertenece a la mano del jugador")
                return []
        #Si el jugador no seleccionó ninguna carta, retornamos None.
        else:
            if len(selectedDiscards) == 2 and (not any(c.joker for c in selectedDiscards) or all(c.joker for c in selectedDiscards)) and self.downHand:
                return '001'#print("Solo puedes bajar 2 cartas si *una* de ellas es un Joker")
            elif len(selectedDiscards) == 1 and selectedDiscards[0].joker:
                return '002'#print("Para poder descartar un joker, debes descartar también otra carta normal")
            elif len(selectedDiscards)==2 and ( any(c.joker for c in selectedDiscards) or all(c.joker for c in selectedDiscards)) and not self.downHand:
                return '003' #print("No puedes quemar el mono sino te has bajado")
            elif not self.cardDrawn:
                return '004' #print("Debes tomar una carta antes de descartar")
            else:
                return []
    def isValidTrioF(self,lista):
        """
        Valida si una lista específica de cartas (propuesta) es un grupo válido.
        Un grupo válido (trío, cuarteto, etc.) debe:
        1. Tener 3 o más cartas.
        2. Tener un máximo de 1 joker.
        3. Todas las cartas normales deben tener el mismo valor.
        """
        
        # 1. Verificar el tamaño (mínimo 3 cartas)
        # Tu código original buscaba de 3 en adelante.
        if not lista or len(lista) < 3:
            print(f"Error: La propuesta debe tener al menos 3 cartas. (Tiene {len(lista)})")
            return False

        # 2. Separar jokers y cartas normales de la propuesta
        jokers_en_propuesta = []
        cartas_normales = []
        for card in lista:
            # Asumiendo que tu objeto Card tiene un booleano 'joker'
            if card.joker:
                jokers_en_propuesta.append(card)
            else:
                cartas_normales.append(card)

        # 3. Verificar la regla del Joker (máximo 1)
        if len(jokers_en_propuesta) > 1:
            print(f"Error: La propuesta tiene más de 1 joker. (Tiene {len(jokers_en_propuesta)})")
            return False

        # 4. Verificar los valores de las cartas normales
        # Si hay 0 o 1 carta normal, es válido (ej: [Joker, 5, 5])
        # Si hay 2 o más cartas normales, TODAS deben ser iguales.
        if len(cartas_normales) >= 2:
            # Tomamos el valor de la primera carta normal como referencia
            # Asumiendo que tu objeto Card tiene un atributo 'value'
            valor_referencia = cartas_normales[0].value
            
            # Iteramos sobre el RESTO de cartas normales
            for i in range(1, len(cartas_normales)):
                if cartas_normales[i].value != valor_referencia:
                    print(f"Error: Las cartas normales no tienen el mismo valor.")
                    print(f"Se esperaba '{valor_referencia}', pero se encontró '{cartas_normales[i].value}'")
                    return False
                    
        # 5. Caso especial: ¿Propuesta de solo Jokers?
        # Ej: [Joker, Joker, Joker]. Esto fallaría en el paso 3 (len > 1).
        if not cartas_normales and len(jokers_en_propuesta) >= 3:
             # Esto solo puede pasar si la regla de jokers es > 1, pero
             # nuestro paso 3 ya lo habría bloqueado. Es una doble seguridad.
             print("Error: No se pueden formar grupos solo de Jokers (o la regla de max 1 joker lo impide).")
             return False

        # Si llegamos hasta aquí, la propuesta es válida.
        print(f"¡Propuesta válida!: {[str(c) for c in lista]}")
        return True
    
    def isValidStraightF(self, cards):
        """
        Verifica si una lista de objetos Card forma una seguidilla válida (Rummy).
        NO requiere que las cartas vengan ordenadas.
        Retorna True o False.
        """
        if not cards or len(cards) < 4:
            return False

        # 1. Separar Jokers y Cartas normales
        jokers = [c for c in cards if c.joker]
        non_jokers = [c for c in cards if not c.joker]
        
        num_jokers = len(jokers)

        # Regla: Máximo 2 Jokers
        if num_jokers > 2:
            return False

        # Si todo son jokers no es válido sin referencia de palo
        if not non_jokers:
            return False 

        # 2. Verificar Palo (Suit)
        first_suit = non_jokers[0].type
        if any(c.type != first_suit for c in non_jokers):
            return False

        # Función auxiliar interna para verificar la secuencia numérica
        def check_sequence(values_list):
            # Ordenamos los valores numéricos de menor a mayor
            sorted_values = sorted(values_list)
            
            # Verificamos duplicados numéricos exactos
            if len(sorted_values) != len(set(sorted_values)):
                return False
            
            gaps_needed = 0
            
            # Recorremos la lista ordenada comparando pares
            for i in range(len(sorted_values) - 1):
                current_val = sorted_values[i]
                next_val = sorted_values[i+1]
                
                diff = next_val - current_val
                
                # Si diff es 1, son consecutivas (perfecto)
                # Si diff es 2, falta 1 carta (necesita 1 joker)
                # Si diff es > 2, faltan 2+ cartas (necesita 2+ jokers seguidos -> invalido)
                
                missing_cards = diff - 1
                
                if missing_cards > 1: 
                    return False 
                
                gaps_needed += missing_cards

            # Si la cantidad de jokers que tenemos cubre los huecos
            return gaps_needed <= num_jokers

        # 3. Construcción de listas de valores (Low, High, Mixed)
        
        values_low = []   # Todos los Ases valen 1
        values_high = []  # Todos los Ases valen 14
        values_mixed = [] # Un As vale 1, el otro 14 (Solo si hay 2+ Ases)
        
        # Contamos cuantos Ases hay para saber si activar el modo mixto
        ace_count = sum(1 for c in non_jokers if c.value == "A")
        aces_processed = 0

        for c in non_jokers:
            val = c.numValue() # Asumimos 2-13. Si tu numValue da 1 para As, no importa, lo sobreescribimos abajo.
            
            if c.value == "A":
                # Llenamos listas básicas
                values_low.append(1)
                values_high.append(14)
                
                # Llenamos lista mixta (si aplica)
                if ace_count >= 2:
                    aces_processed += 1
                    # El primer As que procesamos será el 1, el segundo será el 14
                    if aces_processed == 1:
                        values_mixed.append(1)
                    else:
                        values_mixed.append(14)
            else:
                values_low.append(val)
                values_high.append(val)
                if ace_count >= 2:
                    values_mixed.append(val)

        # 4. Verificaciones
        
        # Caso 1: As Bajo (A, 2, 3...)
        if check_sequence(values_low):
            return True
        
        # Caso 2: As Alto (...Q, K, A)
        if check_sequence(values_high):
            return True
            
        # Caso 3: As Mixto / Vuelta al mundo (A, 2 ... K, A)
        if ace_count >= 2:
            if check_sequence(values_mixed):
                return True
                
        return False
        
    def sortedStraight(self, cards):
        """
        Valida y ordena una seguidilla (Straight).
        Soporta:
        - As Bajo (A, 2, 3...)
        - As Alto (...Q, K, A)
        - As Mixto/Vuelta al mundo (A, 2, ... K, A) si hay 2 Ases.
        """
        if not cards or len(cards) < 4:
            return False

        jokers = [c for c in cards if c.joker]
        naturals = [c for c in cards if not c.joker]

        if len(jokers) > 2: return False
        if not naturals: return False 

        # 1. Validar Palo
        first_suit = naturals[0].type
        if any(c.type != first_suit for c in naturals):
            return False

        # --- Función para construir la secuencia ---
        def try_build(mode):
            # modes: "LOW" (A=1), "HIGH" (A=14), "MIXED" (Un A=1, otro A=14)
            
            temp_naturals = []
            aces_seen = 0
            
            for c in naturals:
                val = c.numValue()
                if c.value == "A":
                    aces_seen += 1
                    if mode == "LOW":
                        val = 1
                    elif mode == "HIGH":
                        val = 14
                    elif mode == "MIXED":
                        # El primer As que veamos será 1, el segundo será 14
                        # Si hay más de 2 Ases, serán duplicados y fallará luego (correcto)
                        val = 1 if aces_seen == 1 else 14
                
                temp_naturals.append((val, c))
            
            # Ordenamos por valor numérico
            temp_naturals.sort(key=lambda x: x[0])
            
            # Verificar duplicados numéricos
            # Esto evita tener dos "5" o dos Ases asignados al mismo valor
            for i in range(len(temp_naturals) - 1):
                if temp_naturals[i][0] == temp_naturals[i+1][0]: 
                    return None

            built_sequence = []
            available_jokers = list(jokers)
            
            # Construcción de huecos internos
            curr_rank, curr_card = temp_naturals[0]
            built_sequence.append(curr_card)
            
            for i in range(len(temp_naturals) - 1):
                next_rank, next_card = temp_naturals[i+1]
                diff = next_rank - curr_rank
                
                if diff == 1:
                    built_sequence.append(next_card)
                elif diff == 2:
                    if not available_jokers: return None
                    built_sequence.append(available_jokers.pop(0))
                    built_sequence.append(next_card)
                else:
                    return None # Hueco > 1 carta requiere > 1 joker consecutivo
                
                curr_rank = next_rank

            # Gestión de extremos (Punta y Cola) para jokers sobrantes
            
            # Helper para obtener rango lógico ya asignado en la lista
            def get_rank(c, index_in_seq):
                if c.joker: return None
                if c.value == "A":
                    # Si estamos en modo MIXED, deducimos por posición
                    if mode == "MIXED":
                         # Si el As está al principio es 1, si está al final es 14
                         # Pero cuidado con el sort. Mejor miramos el vecino.
                         pass
                    return 14 if mode == "HIGH" else 1
                return c.numValue()
            
            # Nota: En modo MIXED con el sort hecho, el As(1) está al principio 
            # y el As(14) al final. Los numValue() simples funcionan para los límites.

            # 1. Rellenar COLA (Derecha)
            while available_jokers:
                last_card = built_sequence[-1]
                # Logica simplificada para saber el valor del ultimo
                last_val = None
                if not last_card.joker:
                    if last_card.value == "A":
                        last_val = 14 if (mode == "HIGH" or (mode == "MIXED" and built_sequence.index(last_card) > 0)) else 1
                    else:
                        last_val = last_card.numValue()
                else:
                    # Inferir del penultimo
                    prev_card = built_sequence[-2]
                    # Recursividad simple o hardcodeo seguro
                    if not prev_card.joker:
                        if prev_card.value == "A":
                             p_val = 14 if (mode == "HIGH" or mode=="MIXED") else 1 # Asumiendo As al final
                        else:
                             p_val = prev_card.numValue()
                        last_val = p_val + 1
                    else:
                        return None # Demasiados jokers al final sin referencia

                limit = 14 # Siempre 14 como maximo teorico
                if last_val < limit:
                     built_sequence.append(available_jokers.pop(0))
                else:
                    break

            # 2. Rellenar PUNTA (Izquierda)
            while available_jokers:
                first_card = built_sequence[0]
                first_val = None
                
                if not first_card.joker:
                     if first_card.value == "A":
                         first_val = 1 if (mode == "LOW" or mode == "MIXED") else 14
                     else:
                         first_val = first_card.numValue()
                else:
                     # Inferir del segundo
                     next_card = built_sequence[1]
                     if not next_card.joker:
                         if next_card.value == "A":
                             n_val = 14 # Raro caso Joker-As(High)
                         else:
                             n_val = next_card.numValue()
                         first_val = n_val - 1
                     else:
                         return None
                
                limit_low = 1
                if first_val > limit_low:
                    built_sequence.insert(0, available_jokers.pop(0))
                else:
                    return None 

            return built_sequence

        # --- Ejecución de Modos ---
        candidates = []

        # 1. Probar As Bajo
        s1 = try_build("LOW")
        if s1: candidates.append(s1)

        # 2. Probar As Alto
        s2 = try_build("HIGH")
        if s2: candidates.append(s2)
        
        # 3. Probar Mixto (Solo si hay más de 1 As)
        ace_count = sum(1 for c in naturals if c.value == "A")
        if ace_count >= 2:
            s3 = try_build("MIXED")
            if s3: candidates.append(s3)

        if not candidates:
            return False

        # --- Selección del Mejor Candidato ---
        best = candidates[0]
        for seq in candidates:
            if seq == cards: return True # Orden original perfecto
            
            # Preferencia: Joker al final
            if seq[-1].joker and not best[-1].joker:
                best = seq
            # Preferencia secundaria: Secuencia más larga (en caso de logicas raras)
            elif len(seq) > len(best):
                best = seq
                
        return best



    def insertCard(self, targetPlayer, targetPlayIndex, cardToInsert, position=None):
        """
        Inserta una carta en targetPlayer.playMade[targetPlayIndex].
        position: 'start', 'end' o None para sustitución de Joker.
        Requisitos: self.downHand == True y cardToInsert in self.playerHand
        """

        # 1) Validaciones básicas
        if not self.downHand:
            print(f"❌ {self.playerName} no puede insertar cartas: aún no se ha bajado.")
            return False
        
        if not self.isHand:
            print(f"❌ {self.playerName} no puede insertar cartas aún porque no es su turno.")

        if cardToInsert not in self.playerHand:
            print(f"❌ {self.playerName} no tiene la carta {cardToInsert} en su mano.")
            return False

        if targetPlayIndex < 0 or targetPlayIndex >= len(targetPlayer.playMade):
            print("❌ El índice dado para la jugada objetivo es inválido.")
            return False

        targetPlay = targetPlayer.playMade[targetPlayIndex]
        temporalPlay = targetPlay.copy()



        # Mapa para ranks (A tratado luego según modo)
        valueToRank = {
            "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
            "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13
        }
        def string_to_card(c):
            if isinstance(c,str):
                if c == "Joker":
                    return Card("Joker", "", joker=True)
                else:
                    value = c[:-1]    # todo menos el último carácter (valor)
                    suit = c[-1]      # último carácter (palo)
                    return Card(value, suit)
            else:
                return c
        def isJoker(c):
            return getattr(c, "joker", False)

        # ---------- Validación TRÍO ----------
        def isValidTrio(play1):
            # Un trío debe tener exactamente 3 cartas (o 3 con 1 Joker)
            play = [c for c in play1["trio"]] if isinstance(play1,dict) else play1
            if len(play) < 3:
                return False
            jokers = [c for c in play if isJoker(c)]
            nonJokers = [c for c in play if not isJoker(c)]
            # Regla: no más de 1 joker en trío
            if len(jokers) > 1:
                return False
            if len(nonJokers) == 0:
                return False
            values = [c.value for c in nonJokers]
            return len(set(values)) == 1

        # ---------- Validación SEGUIDILLA ----------
        def isValidStraight(play):
            # Debe tener al menos 4 cartas totales
            if len(play) < 4:
                return False

            # No permitir jokers adyacentes
            for i in range(len(play) - 1):
                if isJoker(play[i]) and isJoker(play[i + 1]):
                    return False

            # Validar palos (los no-jokers deben pertenecer al mismo palo)
            suits = [c.type for c in play if not isJoker(c)]
            if len(suits) == 0:
                return False
            if len(set(suits)) > 1:
                return False

            # Intentaremos ambos modos: As como bajo (A=1) y As como alto (A=14)
            for highAs in (False, True):
                # Construir lista de ranks (None para jokers)
                ranks = []
                okMode = True #
                for c in play:
                    if isJoker(c):
                        ranks.append(None)
                    else:
                        if c.value == "A":
                            r = 14 if highAs else 1
                        else:
                            if c.value not in valueToRank:
                                okMode = False
                                break
                            r = valueToRank[c.value]
                        ranks.append(r)
                if not okMode:
                    continue

                # Debe haber al menos un non-joker para fijar la base
                nonIndex = [i for i, r in enumerate(ranks) if r is not None]
                if not nonIndex:
                    continue

                # Calcular el "base" candidato: r - pos para cada non-joker
                baseSet = set(ranks[i] - i for i in nonIndex)
                if len(baseSet) != 1:
                    continue
                base = baseSet.pop()

                # Comprobar que los expected ranks estén en 1..14 y coincidan con non-jokers
                expectedOk = True
                for pos, r in enumerate(ranks):
                    expected = base + pos
                    if expected < 1 or expected > 14:
                        expectedOk = False
                        break
                    if r is not None and r != expected:
                        expectedOk = False
                        break
                if not expectedOk:
                    continue

                # Reglas específicas con As:
                # Si hay un As en play:
                for i, c in enumerate(play):
                    if not isJoker(c) and c.value == "A":
                        # As como bajo: no debe haber ningún Joker antes de esa A
                        if not highAs:
                            if any(isJoker(play[j]) for j in range(0, i)):
                                expectedOk = False
                                break
                        # As como alto: no debe haber ningún Joker después de esa A
                        else:
                            if any(isJoker(play[j]) for j in range(i + 1, len(play))):
                                expectedOk = False
                                break
                if not expectedOk:
                    continue

                # Si llegamos hasta aquí, el modo es válido => la secuencia es válida
                return True

            # Ningún modo válido
            return False

    # ---------- Detectar si la jugada objetivo "parece" trío ----------
        def isTrioLike(play):
            # heurística: si la mayoría de cartas no-joker comparten valor y longitud <= 4
            nonJokers = [c for c in play if not isJoker(c)]
            if not nonJokers:
                return False
            values = [string_to_card(c).value if isinstance(c,str) else c.value for c in nonJokers]
            return len(play) <= 4 and len(set(values)) == 1

        isTrioTarget = isTrioLike(targetPlay)

        # Helper: extrae la lista interna (y su clave en caso de dict) de una jugada
        def _extract_play_list(play):
            """Devuelve (lista, key) donde key es 'trio'|'straight' o None si play es lista.
            Si play es dict y no contiene las claves esperadas, devuelve el primer valor encontrado."""
            if isinstance(play, dict):
                if "trio" in play:
                    return play["trio"], "trio"
                if "straight" in play:
                    return play["straight"], "straight"
                # fallback: devolver primer valor
                for k, v in play.items():
                    return v, k
            return play, None

        # ---------- Simular la operación ----------
        temporal_list, temporal_key = _extract_play_list(temporalPlay)

        if position is None:
            # sustitución: buscar primer Joker en la lista interna
            jokerIndex = next((i for i, c in enumerate(temporal_list) if isJoker(c)), None)
            if jokerIndex is None:
                print("❌ No hay Joker para sustituir en esta jugada.")
                return False
            temporal_list[jokerIndex] = cardToInsert
        elif position == "start":
            temporal_list.insert(0, cardToInsert)
        elif position == "end":
            temporal_list.append(cardToInsert)
        else:
            print("❌ Posición inválida. Usa 'start', 'end' o None.")
            return False

        # ---------- Validar la jugada simulada (sin depender de findStraight/findTrios) ----------
        # Validar la jugada simulada (trabajando sobre la lista interna extraída)
        if isTrioTarget:
            valid = isValidTrio(temporal_list)
        else:
            valid = isValidStraight(temporal_list)

        if not valid:
            if isTrioTarget:
                print("❌ La sustitución/inserción rompe el trío: operación rechazada.")
                print(f"Trío si se agregase dicha carta: {[str(c) for c in temporal_list]}")
            else:
                print("❌ La carta no puede insertarse: la seguidilla resultante no es válida.")
                print(f"Seguidilla si se agregase dicha carta: {[str(c) for c in temporal_list]}")
            return False

        # ---------- Aplicar cambios reales ----------
        # ---------- Aplicar cambios reales ----------
        target_list, target_key = _extract_play_list(targetPlay)
        if position is None:
            # Reemplazar el Joker real y devolver esa instancia de Joker a la mano del que inserta
            jokerIndexReal = next((i for i, c in enumerate(target_list) if isJoker(c)), None)
            if jokerIndexReal is None:
                print("❌ (race) No hay Joker real para sustituir.")
                return False
            replacedJoker = target_list[jokerIndexReal]
            target_list[jokerIndexReal] = cardToInsert
            # quitar carta del que inserta y devolver el Joker real a su mano
            self.playerHand.remove(cardToInsert)
            self.playerHand.append(replacedJoker)
            print(f"🔄 {self.playerName} sustituyó un Joker con {cardToInsert} (Joker -> mano).")
            return True
        else:
            # Insert real al inicio o final (trabajando sobre la lista interna)
            if position == "start":
                target_list.insert(0, cardToInsert)
            else:
                target_list.append(cardToInsert)
            print(f"⬅️ {self.playerName} agregó {cardToInsert} al inicio de la jugada." if position == 'start' else f"➡️ {self.playerName} agregó {cardToInsert} al final de la jugada.")
            self.playerHand.remove(cardToInsert)
            return True

    # Mét. para cambiar el valor de "playerPass" para saber si, en un turno dado, pasó de la carta del
    # descarte y agarró del mazo de disponibles. Servirá para la compra de cartas de los siguientes
    # jugadores.
    def passCard(self):
        self.playerPass = not self.playerPass

    def buyCard(self, round):
        """Este método debe recibir como parámetro el objeto de la ronda actual.
        Eso se hará desde el ciclo principal del juego.
        Este método se utilizará en el botón de comprar carta, que solo se mostrará
        cuando isHand es False"""
        discardedCard = round.discards.pop()
        #Si el jugador decidió comprar la carta del descarte, se le entrega dicha carta y además se le da una del mazo como castigo
        if self.playerBuy and not self.isHand:
            extraCard = round.pile.pop()  #Sacamos la última carta del mazo
            round.hands[self.playerId].append(extraCard)  #Añadimos la carta a la mano del jugador
            # self.playerHand.append(discardedCard)
            round.hands[self.playerId].append(discardedCard)
            self.playerHand = round.hands[self.playerId]
            print(f"El jugador {self.playerName} compró la carta {discardedCard} y recibió una carta: {extraCard}, del mazo como castigo")
            return [discardedCard, extraCard]
            # return round
        else:
            print(f"El jugador {self.playerName} no compró la carta del descarte")
            return None
        
    def calculatePoints(self):
        """Esto añade los puntos al jugador. Se debe llamar este método al finalizar cada ronda.
        Los puntos van de la siguiente manera:
        -Cartas del 2 al 9: 5 puntos cada una
        -Cartas 10, J, Q, K: 10 puntos cada una
        -Cartas de Ases: 20 puntos
        -Cartas Joker: 25 puntos"""
        totalPoints = 0
        for card in self.playerHand:
            if card.joker:
                totalPoints += 25
            elif card.value in ["K", "Q", "J", "10"]:
                totalPoints += 10
            elif card.value == "A":
                totalPoints += 20
            else:
                totalPoints += 5
        self.playerPoints += totalPoints
        return totalPoints
