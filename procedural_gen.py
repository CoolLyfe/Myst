import random
from PIL import Image, ImageDraw
import os

def procedural_gen ():
    map = []
    for i in range(5):
        ligne = []
        for j in range (8):
            ligne.append([0, [], random.randint(1,3)])
        map.append(ligne) 

    directions = {"N": (0, -1),"S": (0, 1),"E": (1, 0),"O": (-1, 0)}
    direction_opposite = {"N": "S","S": "N","E": "O","O": "E"}
    
    start = (random.randint(1,6), random.randint(1,3))
    map[start[1]][start[0]][0] = 2      # 0 = salle non existante ; 1 = salle active ; 2 = salle de depart/spawn ; 3 = salle de boss

    rooms = [start]
    nbroom = random.randint(15,20)

    while len(rooms) < nbroom + 1 :
        x, y = random.choice(rooms)
        next_direction_random , (dx, dy) = random.choice(list(directions.items()))
        next_x, next_y = x+dx, y+dy
        if 0 <= x + dx < 8 and 0 <= y + dy < 5:
            if len(map[y][x][1]) <= 2 :
                if map[next_y][next_x][0] == 0:
                    if len(rooms) < nbroom :
                        map[next_y][next_x][0] = 1
                    else :
                        map[next_y][next_x][0] = 3
                    rooms.append((next_x, next_y))
                    map[y][x][1].append(next_direction_random)
                    map[next_y][next_x][1].append(direction_opposite[next_direction_random])
    
    #for i in range (5):
    #    print(map[i])
    
    return map

def create_map_image(map, cell_size=1500):
    
    largeur_y = len(map)
    longeur_z = len(map[0]) 
    
    img_width = longeur_z * cell_size
    img_height = largeur_y * cell_size
    image = Image.new('RGB', (img_width, img_height), color='black')
    draw = ImageDraw.Draw(image)
    
    colors = {
        0: (0, 0, 0),      # salle inexistante - noir
        1: (100, 100, 150),   # salle existante - bleu
        2: (200, 200, 100),    # spawn - vert
        3: (200, 100, 100)     # salle de boss - rouge
    }
    # en vrai il faudrai rajouter une salle "shop" ou salle "pnj encounter" (pour rencontrer 'igrek koi tegal')
    
    for y in range(largeur_y):
        for x in range(longeur_z):
            if map[y][x][0] > 0: 
                connections = map[y][x][1]
                directions = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "O": (-1, 0)}
                
                for new_direction in connections:
                    dx, dy = directions[new_direction]
                    next_x, next_y = x + dx, y + dy
                    
                    #div_x, div_y = random.randint(1,3), random.randint(1,3)      c'est pour le style mais ca marche pas 
                    x1 = x * cell_size + cell_size // 2
                    y1 = y * cell_size + cell_size // 2
                    x2 = next_x * cell_size + cell_size // 2
                    y2 = next_y * cell_size + cell_size // 2
                    if (map[y][x][0] == 1) or  (map[y][x][0] == 2):
                        draw.line([x1, y1, x2, y2], fill=(255, 255, 0), width=300)
                    elif map[y][x][0] == 3:
                        draw.line([x1, y1, x2, y2], fill=(255, 0, 0), width=300) 
    
    for y in range(largeur_y):
        for x in range(longeur_z):
            room_type = map[y][x][0]
            color = colors.get(room_type, (0, 0, 0))
            x1 = x * cell_size + 50
            y1 = y * cell_size + 50
            x2 = (x + 1) * cell_size - 50
            y2 = (y + 1) * cell_size - 50
            
            draw.rectangle([x1, y1, x2, y2], fill=color, outline=(0, 0, 0), width=10)
    

    # je sais pas comment mettre de chemin non-absolut
    image.save('C:/Users/loule/Desktop/game/asset/map_game.png')
    return image
