# Интеграция систем из папки Andreas

## Структура созданных систем

### Core Systems (`game/core/`)
- **`game_state_manager.py`** - Управление глобальным состоянием игры (настройки, сохранения)
- **`game_initializer.py`** - Основная точка входа инициализации всех систем
- **`game_launcher.py`** - Управление процессом запуска игры

### Player Systems (`game/player/`)
- **`player_manager.py`** - Центральный класс управления игроком
- **`player_initializer.py`** - Создание нового персонажа (интеграция с hero_creator)
- **`player_loader.py`** - Загрузка сохранений (интеграция с hero_loader)
- **`player_data_validator.py`** - Валидация данных персонажа (обратная совместимость)

### Setup Systems (`game/setup/`)
- **`new_game_setup.py`** - Настройка новой игры (квесты, мир, NPC)
- **`starter_gear_distributor.py`** - Умная выдача стартовой экипировки
- **`progression_manager.py`** - Система уровней, опыта, прокачки

## Интеграционные точки

### 1. Создание персонажа
```python
from game.player.player_manager import PlayerManager

player_manager = PlayerManager(base_path)
hero = player_manager.create_character("warrior", "PlayerName")
```

### 2. Загрузка персонажа
```python
hero = player_manager.load_character("PlayerName")
```

### 3. Запуск игры
```python
from game.core.game_launcher import GameLauncher

launcher = GameLauncher(base_path)
launcher.run()
```

### 4. Интеграция с меню
Меню создания персонажа (`CharacterCreationMenu`) автоматически интегрировано с `PlayerManager` через `MenuManager.handle_action("create_character")`.

## Использование существующих систем

### Hero System
- Использует структуру данных из `game/data/hero_classes.json`
- Совместим с существующими сохранениями из `save/heroes/`

### Inventory System
- Интегрируется с глобальным инвентарем через `GameStateManager.get_global_inventory_path()`
- Использует существующую структуру JSON предметов

### JSON Database
- Классы: `game/data/hero_classes.json`
- Предметы: `game/data/items/weapons.json`, `game/data/items/armor/*.json`

## Обратная совместимость

Все системы обеспечивают обратную совместимость:
- Старые сохранения автоматически валидируются и исправляются
- Отсутствующие поля дополняются значениями по умолчанию
- Структура данных совместима с существующими системами

## Запуск игры

```bash
python main.py
```

Игра автоматически:
1. Инициализирует все системы через `GameInitializer`
2. Загружает настройки через `GameStateManager`
3. Запускает меню через `MenuManager`
4. Интегрируется с созданием персонажа через `PlayerManager`

