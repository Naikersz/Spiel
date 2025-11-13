import pygame
import json
import os
from typing import Dict, List, Optional

# Инициализация Pygame
pygame.init()

class CharacterLayer:
    """Класс для одного слоя персонажа (тело, голова, одежда и т.д.)"""
    
    def __init__(self, layer_data: dict, base_url: str):
        self.file_name = layer_data["fileName"]
        self.z_pos = layer_data["zPos"]
        self.parent_name = layer_data["parentName"]
        self.name = layer_data["name"]
        self.variant = layer_data.get("variant", "")
        self.supported_animations = layer_data["supportedAnimations"].split(",")
        
        # Загружаем спрайт
        self.sprite_sheet = self.load_image(base_url + self.file_name)
        self.frame_width = 64  # Стандартный размер для LPC
        self.frame_height = 64
        
    def load_image(self, path: str) -> pygame.Surface:
        """Загрузка изображения с обработкой ошибок"""
        try:
            # Если файл локальный
            if os.path.exists(path):
                image = pygame.image.load(path).convert_alpha()
            else:
                # Для веб-загрузки нужно добавить requests
                print(f"Файл не найден: {path}")
                # Создаём временный поверхность
                image = pygame.Surface((512, 832), pygame.SRCALPHA)  # Размер LPC спрайт-листа
        except Exception as e:
            print(f"Ошибка загрузки {path}: {e}")
            image = pygame.Surface((512, 832), pygame.SRCALPHA)
            
        return image
        
    def supports_animation(self, animation_name: str) -> bool:
        """Проверяет, поддерживает ли слой данную анимацию"""
        return animation_name in self.supported_animations
    
    def get_frame_rect(self, frame_index: int) -> pygame.Rect:
        """Получает прямоугольник кадра в спрайт-листе"""
        frame_x = (frame_index % 8) * self.frame_width
        frame_y = (frame_index // 8) * self.frame_height
        return pygame.Rect(frame_x, frame_y, self.frame_width, self.frame_height)


class LPCCharacter:
    """Основной класс персонажа с системой слоёв"""
    
    # Стандартные анимации LPC
    ANIMATION_ROWS = {
        "spellcast": 0, "thrust": 1, "walk": 2, "slash": 3,
        "shoot": 4, "hurt": 5, "idle": 6, "jump": 7, "run": 8,
        "sit": 9, "emote": 10, "climb": 11, "combat": 12,
        "1h_slash": 13, "1h_backslash": 14, "1h_halfslash": 15,
        "watering": 16
    }
    
    def __init__(self, json_data: dict, x: int = 100, y: int = 100):
        self.body_type = json_data["bodyTypeName"]
        self.base_url = json_data.get("spritesheets", "")
        
        # Позиция на экране
        self.x = x
        self.y = y
        
        # Словари слоёв
        self.available_layers: Dict[str, List[CharacterLayer]] = {}
        self.equipped_layers: Dict[str, CharacterLayer] = {}
        
        # Анимация
        self.current_animation = "idle"
        self.current_frame = 0
        self.animation_speed = 0.15  # секунды между кадрами
        self.frame_timer = 0
        self.facing_right = True
        
        # Загружаем слои из JSON
        self.load_layers_from_json(json_data)
        
    def load_layers_from_json(self, json_data: dict):
        """Загружает все слои из JSON данных"""
        for layer_data in json_data["layers"]:
            layer = CharacterLayer(layer_data, self.base_url)
            layer_type = self._get_layer_type(layer.name)
            
            # Добавляем в доступные слои
            if layer_type not in self.available_layers:
                self.available_layers[layer_type] = []
            self.available_layers[layer_type].append(layer)
            
            # Автоматически экипируем первый слой каждого типа
            if layer_type not in self.equipped_layers:
                self.equipped_layers[layer_type] = layer
    
    def _get_layer_type(self, layer_name: str) -> str:
        """Определяет тип слоя для категоризации"""
        name_lower = layer_name.lower()
        if "body" in name_lower:
            return "body"
        elif "head" in name_lower:
            return "head"
        elif "hair" in name_lower:
            return "hair"
        elif "chest" in name_lower or "torso" in name_lower:
            return "chest"
        elif "legs" in name_lower or "pants" in name_lower:
            return "legs"
        elif "feet" in name_lower or "shoes" in name_lower:
            return "feet"
        elif "hand" in name_lower:
            return "hands"
        else:
            return "accessory"
    
    def equip_layer(self, layer_type: str, variant: str = "") -> bool:
        """Экипирует слой определённого типа и варианта"""
        if layer_type not in self.available_layers:
            print(f"Тип слоя '{layer_type}' не найден")
            return False
            
        # Ищем слой по варианту
        target_layer = None
        for layer in self.available_layers[layer_type]:
            if not variant or layer.variant == variant:
                target_layer = layer
                break
                
        if target_layer:
            self.equipped_layers[layer_type] = target_layer
            print(f"Экипирован: {layer_type} - {target_layer.name}")
            return True
        else:
            print(f"Слой '{layer_type}' с вариантом '{variant}' не найден")
            return False
    
    def unequip_layer(self, layer_type: str) -> bool:
        """Снимает слой (кроме обязательных как body и head)"""
        if layer_type in ["body", "head"]:
            print(f"Нельзя снять обязательный слой: {layer_type}")
            return False
            
        if layer_type in self.equipped_layers:
            del self.equipped_layers[layer_type]
            print(f"Снят слой: {layer_type}")
            return True
        return False
    
    def add_new_layer(self, layer_data: dict):
        """Добавляет новый слой в доступные"""
        layer = CharacterLayer(layer_data, self.base_url)
        layer_type = self._get_layer_type(layer.name)
        
        if layer_type not in self.available_layers:
            self.available_layers[layer_type] = []
        self.available_layers[layer_type].append(layer)
    
    def set_animation(self, animation_name: str):
        """Устанавливает текущую анимацию"""
        if animation_name in self.ANIMATION_ROWS:
            if self.current_animation != animation_name:
                self.current_animation = animation_name
                self.current_frame = 0
                self.frame_timer = 0
        else:
            print(f"Анимация '{animation_name}' не найдена. Используется 'idle'")
            self.current_animation = "idle"
    
    def update(self, dt: float):
        """Обновляет анимацию персонажа"""
        self.frame_timer += dt
        
        if self.frame_timer >= self.animation_speed:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % 8  # 8 кадров на анимацию
    
    def get_frame_index(self) -> int:
        """Получает индекс кадра в спрайт-листе LPC"""
        row = self.ANIMATION_ROWS.get(self.current_animation, 6)  # По умолчанию idle
        return row * 8 + self.current_frame  # 8 кадров в строке
    
    def draw(self, screen: pygame.Surface):
        """Отрисовывает персонажа со всеми слоями"""
        # Сортируем слои по zPos для правильного порядка отрисовки
        sorted_layers = sorted(
            self.equipped_layers.values(), 
            key=lambda layer: layer.z_pos
        )
        
        frame_index = self.get_frame_index()
        
        # Отрисовываем каждый слой
        for layer in sorted_layers:
            if layer.supports_animation(self.current_animation):
                frame_rect = layer.get_frame_rect(frame_index)
                sprite_to_draw = layer.sprite_sheet.subsurface(frame_rect)
                
                # Отражаем спрайт если смотрит влево
                if not self.facing_right:
                    sprite_to_draw = pygame.transform.flip(sprite_to_draw, True, False)
                
                screen.blit(sprite_to_draw, (self.x, self.y))
    
    def move(self, dx: int, dy: int):
        """Перемещает персонажа"""
        self.x += dx
        self.y += dy
        
        # Автоматически устанавливаем направление взгляда
        if dx > 0:
            self.facing_right = True
        elif dx < 0:
            self.facing_right = False
        
        # Автоматически переключаем анимацию при движении
        if dx != 0 or dy != 0:
            self.set_animation("walk")
        else:
            self.set_animation("idle")
    
    def get_equipped_items(self) -> Dict[str, str]:
        """Возвращает словарь экипированных предметов"""
        return {layer_type: layer.name for layer_type, layer in self.equipped_layers.items()}


# Пример использования
def main():
    # Настройки экрана
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("LPC Character System")
    clock = pygame.time.Clock()
    
    # Пример JSON данных (можно загрузить из файла)
    example_json = {
        "bodyTypeName": "male",
        "spritesheets": "assets/sprites/",
        "layers": [
            {
                "fileName": "body/bodies/male/light.png",
                "zPos": 10,
                "parentName": "body",
                "name": "Body_color",
                "variant": "light",
                "supportedAnimations": "spellcast,thrust,walk,slash,shoot,hurt,watering,idle,jump,run,sit,emote,climb,combat,1h_slash,1h_backslash,1h_halfslash"
            },
            {
                "fileName": "head/heads/human/male/light.png",
                "zPos": 100,
                "parentName": "head",
                "name": "Human_male",
                "variant": "light",
                "supportedAnimations": "spellcast,thrust,walk,slash,shoot,hurt,watering,idle,jump,run,sit,emote,climb,combat,1h_slash,1h_backslash,1h_halfslash"
            }
        ]
    }
    
    # Создаём персонажа
    player = LPCCharacter(example_json, 400, 300)
    
    # Добавляем дополнительные слои (пример)
    hair_layer_data = {
        "fileName": "hair/hairs/male/black.png",
        "zPos": 90,
        "parentName": "head", 
        "name": "Hair_male",
        "variant": "black",
        "supportedAnimations": "spellcast,thrust,walk,slash,shoot,hurt,watering,idle,jump,run,sit,emote,climb,combat,1h_slash,1h_backslash,1h_halfslash"
    }
    player.add_new_layer(hair_layer_data)
    player.equip_layer("hair", "black")
    
    # Главный игровой цикл
    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time в секундах
        
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Смена анимаций по клавишам
                if event.key == pygame.K_1:
                    player.set_animation("idle")
                elif event.key == pygame.K_2:
                    player.set_animation("walk") 
                elif event.key == pygame.K_3:
                    player.set_animation("jump")
                elif event.key == pygame.K_4:
                    player.set_animation("slash")
                elif event.key == pygame.K_5:
                    player.set_animation("spellcast")
                # Смена одежды
                elif event.key == pygame.K_h:
                    if "hair" in player.equipped_layers:
                        player.unequip_layer("hair")
                    else:
                        player.equip_layer("hair", "black")
        
        # Управление движением
        keys = pygame.key.get_pressed()
        move_x, move_y = 0, 0
        if keys[pygame.K_LEFT]:
            move_x = -3
        if keys[pygame.K_RIGHT]:
            move_x = 3
        if keys[pygame.K_UP]:
            move_y = -3
        if keys[pygame.K_DOWN]:
            move_y = 3
            
        player.move(move_x, move_y)
        player.update(dt)
        
        # Отрисовка
        screen.fill((50, 50, 80))  # Темно-синий фон
        player.draw(screen)
        
        # Отладочная информация
        font = pygame.font.Font(None, 36)
        anim_text = font.render(f"Animation: {player.current_animation}", True, (255, 255, 255))
        items_text = font.render(f"Items: {len(player.equipped_layers)}", True, (255, 255, 255))
        screen.blit(anim_text, (10, 10))
        screen.blit(items_text, (10, 50))
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()