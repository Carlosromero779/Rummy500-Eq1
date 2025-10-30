mi_lista = [10, 20, 30, 40]
mi_iterador = iter(mi_lista)


print(type(mi_iterador))
print(next(mi_iterador))  # Salida: 10
print(next(mi_iterador))  # Salida: 20
print(next(mi_iterador, "Fin"))  # Salida: Fin
#print(next(mi_iterador[1]))  # Salida: 10


def pasar_turno(players):
    """
    Busca el jugador con isHand=True, lo pone en False, 
    y pone en True el isHand del siguiente jugador.
    """
    
    # 1. Encontrar el índice del jugador actual
    indice_actual = -1
    for i, player in enumerate(players):
        if player.isHand:
            indice_actual = i
            break  # Detenemos la búsqueda una vez encontrado
            
    # Si no se encuentra un jugador con isHand=True, se podría manejar el error o terminar.
    if indice_actual == -1:
        print("Error: No se encontró ningún jugador con isHand = True.")
        return players # Retorna la lista sin cambios

    # 2. Desactivar el 'isHand' del jugador actual
    players[indice_actual].isHand = False
    
    # 3. Calcular el índice del siguiente jugador
    # Usamos el operador módulo (%) para manejar el "wrap-around" (vuelta al inicio)
    # Es decir, si el actual es el último, el siguiente será el primero (índice 0).
    indice_siguiente = (indice_actual + 1) % len(players)
    
    # 4. Activar el 'isHand' del siguiente jugador
    players[indice_siguiente].isHand = True
    
    return players

# --- EJEMPLO DE USO CON CLASES SIMULADAS ---

# Clase de ejemplo para simular tus elementos de la lista
class Player:
    def __init__(self, name, isHand=False):
        self.name = name
        self.isHand = isHand
    
    def __repr__(self):
        return f"<{self.name}: isHand={self.isHand}>"

# Lista inicial de jugadores
players = [
    Player("Alice", isHand=False),
    Player("Bob", isHand=True),  # Bob tiene el turno (isHand=True)
    Player("Charlie", isHand=False),
    Player("David", isHand=False)
]

print("Estado Inicial:")
print(players)

# Pasar el turno
players = pasar_turno(players)

print("\nEstado Después del 1er Turno:")
print(players) 
# Resultado esperado: Bob es False, Charlie es True

# Pasar el turno otra vez (para ver el "wrap-around" de Charlie a David)
players = pasar_turno(players)

print("\nEstado Después del 2do Turno:")
print(players) 
# Resultado esperado: Charlie es False, David es True

# Pasar el turno otra vez (para ver el "wrap-around" de David a Alice)
players = pasar_turno(players)

print("\nEstado Después del 3er Turno (Vuelta al inicio):")
print(players) 
# Resultado esperado: David es False, Alice es True