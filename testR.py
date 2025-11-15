import random

def generate_room(width, height):
    room = []
    for y in range(height):
        row = []
        for x in range(width):
            if x == 0 or y == 0 or x == width-1 or y == height-1:
                row.append('#')  # стены по краям
            else:
                row.append('.')  # пол внутри
        room.append(''.join(row))
    
    # Добавляем случайную дверь
    wall = random.choice(['top', 'bottom', 'left', 'right'])
    if wall == 'top':
        room[0][width//2] = '-'
    elif wall == 'bottom':
        room[height-1][width//2] = '-'
    
    return room