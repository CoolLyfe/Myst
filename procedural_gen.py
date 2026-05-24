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
    
    start = (random.randint(2,5), random.randint(1,3))
    map[start[1]][start[0]][0] = 1      # 0 = salle non existante ; 1 = salle de spawn ; 2 = salle de boss ; 3 = salle classique ; 4 = salle de loot ; 5 = salle de baston harr

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
                        map[next_y][next_x][0] = random.randint(3,3)
                    else :
                        map[next_y][next_x][0] = 2
                    rooms.append((next_x, next_y))
                    map[y][x][1].append(next_direction_random)
                    map[next_y][next_x][1].append(direction_opposite[next_direction_random])
    
    #for i in range (5):
    #   print(map[i])
    return map, start

def create_map_image(map, cell_size=2500):
    
    largeur_y = len(map)
    longeur_z = len(map[0]) 
    
    img_width = longeur_z * cell_size
    img_height = largeur_y * cell_size
    # fond transparent pour les zones sans salle/corridor
    image = Image.new('RGBA', (img_width, img_height), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    room_images = {
        1: Image.open("assets/grassy_map.png"), #spawn room
        2: Image.open("assets/snowy_map.png"), #boss room
        3: Image.open("assets/base_map_good.png"), #classic room
        4: Image.open("assets/loot_room.png"), #loot room
        5: Image.open("assets/fight_room.png"), #fight room
        }
    couloir_image = Image.open("assets/couloir.png").convert("RGBA")

    # en vrai il faudrai rajouter une salle "shop" ou salle "pnj encounter" (pour rencontrer 'igrek koi tegal')
    #reponse de louis.l : ntm trop dure on vera

    #j'ai fais ca pour de la transparence

    for y in range(largeur_y):
        for x in range(longeur_z):
            draw.rectangle([x*cell_size, y*cell_size, (x+1)*cell_size, (y+1)*cell_size], (0, 0, 0, 0), (0,0,0,0), width=2)

    for y in range(largeur_y):
        for x in range(longeur_z):
            room_type = map[y][x][0]
            # Remplace le rectangle par l'image de la salle
            room_img = room_images.get(room_type)
            gap = 400
            if room_img:
                resized = room_img.resize((cell_size-gap, cell_size-gap))
                image.paste(resized, (x*cell_size+gap//2, y*cell_size+gap//2))

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

                    start_x = x1 + (dx * (cell_size / 2)) - (gap / 1.11 * dx)
                    start_y = y1 + (dy * (cell_size / 2)) - (gap / 1.11 * dy)
                    end_x = x2 - (dx * (cell_size / 2)) + (gap / 1.11 * dx)
                    end_y = y2 - (dy * (cell_size / 2)) + (gap / 1.11 * dy)

                    if dx != 0:
                        length = int(abs(end_x - start_x))
                        thickness = int(cell_size // 12)
                        couloir = couloir_image.resize((max(1, length), thickness), Image.LANCZOS)
                        paste_x = int(min(start_x, end_x))
                        paste_y = int(start_y - thickness / 2)
                    else:
                        length = int(abs(end_y - start_y))
                        thickness = int(cell_size // 12)
                        couloir = couloir_image.resize((max(1, length), thickness), Image.LANCZOS).rotate(90, expand=True)
                        paste_x = int(start_x - thickness / 2)
                        paste_y = int(min(start_y, end_y))

                    image.paste(couloir, (paste_x, paste_y), couloir)
    

    image.save('assets/map_game.png')
    return image
