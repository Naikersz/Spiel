import json
import os
import pygame

from core.constants import SAVE_ROOT, SAVE_SLOTS, WIDTH, HEIGHT
from ui.button import Button
from ui.fonts import FONT, FONT_SMALL, FONT_BIG


# Zuordnung von Item-Typen zu Equipment-Slots
SLOT_MAP = {
    "weapon": "weapon",
    "helmet": "helmet",
    "chest": "chest",
    "pants": "pants",
    "boot": "boots",      # Item-Daten verwenden "boot", Slots verwenden "boots"
    "boots": "boots",     # Fallback für beide Varianten
    "glove": "gloves",    # Item-Daten verwenden "glove", Slots verwenden "gloves"
    "gloves": "gloves",   # Fallback für beide Varianten
    "shield": "shield",
}


class InventoryScene:
    """
    Einfache Inventar-Ansicht.
    Zeigt die aktuell ausgerüsteten Items und alle Items aus dem globalen Inventar.
    """

    def __init__(self, slot_index: int):
        self.slot_index = slot_index
        self.buttons = []
        self.player_name = "Unbekannt"
        self.player_level = 1
        self.equipped_items = {}
        self.inventory_items = []
        self.error_message = ""
        self.info_message = ""
        self.selected_inventory_index = None
        self.selected_equipped_slot = None
        self._equipped_hitboxes = []
        self._inventory_hitboxes = []

        self.player_path = None
        self.inventory_path = None
        self._player_data = None

        self._load_data()
        self._create_buttons()

    # ------------------------------------------------------------------ #
    # Daten laden
    # ------------------------------------------------------------------ #
    def _load_data(self):
        save_dir = os.path.join(SAVE_ROOT, SAVE_SLOTS[self.slot_index])
        self.player_path = os.path.join(save_dir, "player.json")
        self.inventory_path = os.path.join(save_dir, "global_inventory.json")

        # Player laden
        try:
            with open(self.player_path, "r", encoding="utf-8") as f:
                player_data = json.load(f)
        except FileNotFoundError:
            self.error_message = f"Spielerdatei fehlt: {self.player_path}"
            self.equipped_items = {}
            return
        except json.JSONDecodeError:
            self.error_message = "Spielerdatei ist beschädigt."
            self.equipped_items = {}
            return

        self._player_data = player_data
        self.player_name = player_data.get("name", "Unbekannt")
        self.player_level = player_data.get("level", player_data.get("stats", {}).get("level", 1))
        self.equipped_items = player_data.get("equipped", {})

        # Inventar laden
        try:
            with open(self.inventory_path, "r", encoding="utf-8") as f:
                self.inventory_items = json.load(f)
        except FileNotFoundError:
            self.inventory_items = []
        except json.JSONDecodeError:
            self.inventory_items = []
            self.error_message = "Inventardatei ist beschädigt."

    # ------------------------------------------------------------------ #
    def _create_buttons(self):
        w, h = 200, 60
        margin = 30
        right = WIDTH - w - margin
        base_y = HEIGHT - h * 4 - margin
        self.buttons = [
            Button("Anlegen", right, base_y, w, h, self._equip_selected_inventory),
            Button("Ablegen", right, base_y + h + 10, w, h, self._unequip_selected_slot),
            Button("Aktualisieren", right, base_y + (h + 10) * 2, w, h, self._reload_data),
            Button("Zurück", right, base_y + (h + 10) * 3, w, h, self._back_to_town),
        ]

    # ------------------------------------------------------------------ #
    def _reload_data(self):
        self.selected_equipped_slot = None
        self.selected_inventory_index = None
        self.info_message = ""
        self._load_data()

    def _back_to_town(self):
        from scenes.town_scene import TownScene

        return TownScene(self.slot_index)

    # ------------------------------------------------------------------ #
    # Update / Draw
    # ------------------------------------------------------------------ #
    def update(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self._handle_click(e.pos)

            for btn in self.buttons:
                result = btn.handle_event(e)
                if result:
                    return result

    def draw(self, screen):
        screen.fill((22, 24, 32))

        title = FONT_BIG.render("Inventar", True, (255, 255, 255))
        subtitle = FONT.render(
            f"{self.player_name}  |  Level {self.player_level}", True, (200, 200, 200)
        )
        screen.blit(title, (40, 40))
        screen.blit(subtitle, (40, 120))

        y_error_start = 180
        if self.error_message:
            err = FONT.render(self.error_message, True, (255, 80, 80))
            screen.blit(err, (40, y_error_start))
            y_error_start += 50

        if self.info_message:
            info = FONT_SMALL.render(self.info_message, True, (160, 220, 160))
            screen.blit(info, (40, HEIGHT - 100))

        self._draw_equipped(screen, start_x=40, start_y=200)
        self._draw_inventory(screen, start_x=WIDTH // 2, start_y=200)

        for btn in self.buttons:
            btn.draw(screen)

    # ------------------------------------------------------------------ #
    def _draw_equipped(self, screen, start_x: int, start_y: int):
        header = FONT.render("Ausgerüstet", True, (255, 255, 255))
        screen.blit(header, (start_x, start_y))

        y = start_y + 50
        if not self.equipped_items:
            txt = FONT_SMALL.render("Keine Ausrüstung gefunden.", True, (200, 200, 200))
            screen.blit(txt, (start_x, y))
            return

        self._equipped_hitboxes = []
        max_width = (WIDTH // 2) - 80

        for slot, item in sorted(self.equipped_items.items()):
            label = self._format_item_line(item)
            row_rect = pygame.Rect(start_x - 10, y - 6, max_width, 36)

            if slot == self.selected_equipped_slot:
                pygame.draw.rect(screen, (60, 70, 110), row_rect, border_radius=6)

            slot_txt = FONT.render(f"{slot.capitalize()}:", True, (180, 200, 255))
            screen.blit(slot_txt, (start_x, y))

            item_txt = FONT_SMALL.render(label, True, (220, 220, 220))
            screen.blit(item_txt, (start_x + 220, y + 6))

            self._equipped_hitboxes.append((slot, row_rect))
            y += 40

    def _draw_inventory(self, screen, start_x: int, start_y: int):
        header = FONT.render("Inventar", True, (255, 255, 255))
        screen.blit(header, (start_x, start_y))

        y = start_y + 50
        if not self.inventory_items:
            txt = FONT_SMALL.render("Inventar ist leer.", True, (200, 200, 200))
            screen.blit(txt, (start_x, y))
            return

        self._inventory_hitboxes = []
        max_visible = 20
        for idx, item in enumerate(self.inventory_items[:max_visible]):
            label = self._format_item_line(item)
            row_rect = pygame.Rect(start_x - 10, y - 4, (WIDTH // 2) - 80, 30)

            if idx == self.selected_inventory_index:
                pygame.draw.rect(screen, (50, 90, 70), row_rect, border_radius=4)

            bullet = FONT_SMALL.render(f"- {label}", True, (220, 220, 220))
            screen.blit(bullet, (start_x, y))

            self._inventory_hitboxes.append((idx, row_rect))
            y += 30

        if len(self.inventory_items) > max_visible:
            more = FONT_SMALL.render(f"... (+{len(self.inventory_items) - max_visible} weitere)", True, (180, 180, 180))
            screen.blit(more, (start_x, y))

    # ------------------------------------------------------------------ #
    @staticmethod
    def _format_item_line(item):
        if not item:
            return "leer"

        name = item.get("name") or item.get("id", "Unbekannt")
        level = item.get("item_level") or item.get("item_level_min")
        slot = item.get("item_type", "?")
        return f"{name} (Slot: {slot}, Level: {level or '?'})"

    # ------------------------------------------------------------------ #
    def _handle_click(self, pos):
        for slot, rect in self._equipped_hitboxes:
            if rect.collidepoint(pos):
                self.selected_equipped_slot = slot
                self.info_message = f"Slot '{slot}' ausgewählt."
                return

        for idx, rect in self._inventory_hitboxes:
            if rect.collidepoint(pos):
                if idx < len(self.inventory_items):
                    self.selected_inventory_index = idx
                    name = self.inventory_items[idx].get("name") or self.inventory_items[idx].get("id", "Item")
                    self.info_message = f"Inventar-Item '{name}' ausgewählt."
                return

    def _equip_selected_inventory(self):
        if self.selected_inventory_index is None:
            self.info_message = "Kein Inventar-Item ausgewählt."
            return

        if self.selected_inventory_index >= len(self.inventory_items):
            self.info_message = "Auswahl ist ungültig."
            self.selected_inventory_index = None
            return

        item = self.inventory_items[self.selected_inventory_index]
        target_slot = self._resolve_slot(item.get("item_type"))
        if not target_slot:
            self.info_message = "Für diesen Item-Typ existiert kein Slot."
            return

        # Entferne Item aus Inventar
        item = self.inventory_items.pop(self.selected_inventory_index)
        prev_item = self.equipped_items.get(target_slot)
        self.equipped_items[target_slot] = item
        if prev_item:
            self.inventory_items.append(prev_item)

        self.selected_inventory_index = None
        self._persist_changes()
        name = item.get("name") or item.get("id", "Item")
        self.info_message = f"{name} wurde ausgerüstet."

    def _unequip_selected_slot(self):
        if not self.selected_equipped_slot:
            self.info_message = "Kein Ausrüstungs-Slot ausgewählt."
            return

        item = self.equipped_items.get(self.selected_equipped_slot)
        if not item:
            self.info_message = "Dieser Slot ist leer."
            return

        self.inventory_items.append(item)
        self.equipped_items[self.selected_equipped_slot] = None
        self._persist_changes()
        self.info_message = f"{item.get('name', item.get('id', 'Item'))} abgelegt."

    def _persist_changes(self):
        if self._player_data is not None and self.player_path:
            self._player_data["equipped"] = self.equipped_items
            with open(self.player_path, "w", encoding="utf-8") as f:
                json.dump(self._player_data, f, ensure_ascii=False, indent=4)

        if self.inventory_path:
            with open(self.inventory_path, "w", encoding="utf-8") as f:
                json.dump(self.inventory_items, f, ensure_ascii=False, indent=4)

    @staticmethod
    def _resolve_slot(item_type: str):
        if not item_type:
            return None
        item_type = item_type.lower()
        return SLOT_MAP.get(item_type)

