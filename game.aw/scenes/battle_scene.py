"""
Battle Scene - Kampfszene mit Gegnern
"""
import json
import os
import random
from typing import Any, Dict

import pygame
from ui.button import Button
from ui.fonts import FONT, FONT_SMALL
from core.constants import WIDTH, HEIGHT
from core.enemy_generator import generate_enemies_for_field
from core.dev_settings import load_dev_settings
from core.player_stats_calculator import PlayerStatsCalculator
from core.level_data import load_level_settings, save_level_settings
from core.loot_generator import LootGenerator
from core.constants import SAVE_ROOT, SAVE_SLOTS




class BattleScene:
    def __init__(self, slot_index, level_type, level_number):
        """
        Initialisiert die Battle Scene
        
        Args:
            slot_index: Speicher-Slot Index
            level_type: Art des Levels ("Feld" oder "Cave")
            level_number: Nummer des Levels
        """
        self.slot_index = slot_index
        self.level_type = level_type
        self.level_number = level_number
        
        # Eindeutiger Key pro Level/Feld
        self.level_key = f"{self.level_type}_{self.level_number}"

        # Dev-Level-Settings für dieses Feld
        self.level_config = load_level_settings(self.level_key)

        # Globaler Dev-Status (aus Optionen)
        self.dev_settings = load_dev_settings()
        self.dev_enabled = self.dev_settings.get("dev_mode", False)

        # Flag & Buttons für Dev-Overlay
        self.show_dev_overlay = False
        self.dev_buttons = []
        
        # Lade Hintergrundbild
        # Berechne Pfad: game.aw/scenes/ -> game.aw/ -> root/ -> assets/battle/
        base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))  # game.aw
        root_path = os.path.dirname(base_path)  # root
        battle_bg_path = os.path.join(root_path, "assets", "battle", "2D_test_battle.png")
        
        try:
            self.background = pygame.image.load(battle_bg_path)
            # Skaliere Hintergrund auf Bildschirmgröße falls nötig
            bg_width, bg_height = self.background.get_size()
            if bg_width != WIDTH or bg_height != HEIGHT:
                self.background = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
        except Exception as e:
            print(f"Fehler beim Laden des Hintergrundbildes: {e}")
            self.background = None
        
        # Generiere Gegner nur für "Feld" Level
        self.enemies = []
        if level_type == "Feld":
            # Nutzt die Config für dieses Feld
            self.enemies = generate_enemies_for_field(level_number, config=self.level_config)
            self._place_enemies_randomly()
        
        # Loot-Generator
        self.loot_generator = LootGenerator()

        # Buttons
        self.buttons = []
        self.create_buttons()      # Zurück (+ ggf. Dev-Button)
        if self.dev_enabled:
            self._create_dev_buttons()  # Buttons IM Overlay
        
        # Hover und Click Tracking
        self.hovered_enemy = None  # Index des gehoverten Gegners
        self.enemy_size = 50  # Größe des Gegner-Rechtecks (Radius 25)
        
        # Lade Spieler-Stats
        self.stats_calculator = PlayerStatsCalculator()
        self.player_stats = self.stats_calculator.get_player_stats(slot_index)
        
        # Schadensanzeigen (für visuelles Feedback)
        self.damage_texts = []  # Liste von (x, y, timer, damage, enemy_index)
    
    def _place_enemies_randomly(self):
        """
        Platziert Gegner zufällig auf der Map
        """
        # Definiere Bereiche für zufällige Platzierung
        # Lasse einen Rand frei (z.B. 100 Pixel von den Rändern)
        margin = 100
        min_x = margin
        max_x = WIDTH - margin
        min_y = margin
        max_y = HEIGHT - margin
        
        # Stelle sicher, dass Gegner nicht zu nah beieinander sind
        min_distance = 80
        placed_positions = []
        
        for enemy in self.enemies:
            max_attempts = 50
            placed = False
            
            for attempt in range(max_attempts):
                x = random.randint(min_x, max_x)
                y = random.randint(min_y, max_y)
                
                # Prüfe Abstand zu bereits platzierten Gegnern
                too_close = False
                for px, py in placed_positions:
                    distance = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
                    if distance < min_distance:
                        too_close = True
                        break
                
                if not too_close:
                    # Füge Position zur enemy-Datenstruktur hinzu
                    enemy["x"] = x
                    enemy["y"] = y
                    placed_positions.append((x, y))
                    placed = True
                    break
            
            # Falls kein passender Platz gefunden wurde, platziere trotzdem
            if not placed:
                x = random.randint(min_x, max_x)
                y = random.randint(min_y, max_y)
                enemy["x"] = x
                enemy["y"] = y
                placed_positions.append((x, y))
    
    def create_buttons(self):
        """Erstellt Buttons für die Battle Scene"""
        # Zurück-Button
        back_w, back_h = 150, 40
        back_x = 20
        back_y = 20
        self.buttons.append(
            Button("Zurück", back_x, back_y, back_w, back_h, self.back_to_level_selection)
        )

        # Dev-Button (rechts oben) nur wenn Dev global aktiviert ist
        if self.dev_enabled:
            dev_w, dev_h = 120, 40
            dev_x = WIDTH - dev_w - 20
            dev_y = 20
            self.buttons.append(
                Button("Dev", dev_x, dev_y, dev_w, dev_h, self.toggle_dev_overlay)
            )
    
    def toggle_dev_overlay(self):
        self.show_dev_overlay = not self.show_dev_overlay

    def _create_dev_buttons(self):
        """
        Kleine +/- Buttons im Overlay (werden nur benutzt, wenn Overlay offen ist).
        """
        self.dev_buttons = []

        panel_width = int(WIDTH * 0.6)
        panel_height = int(HEIGHT * 0.6)
        panel_x = (WIDTH - panel_width) // 2
        panel_y = (HEIGHT - panel_height) // 2

        btn_w, btn_h = 40, 30
        row_h = 40

        # Startposition der Zeilen
        base_x = panel_x + panel_width - 160
        base_y = panel_y + 80

        def add_pair(row_index, minus_cb, plus_cb):
            y = base_y + row_index * row_h
            self.dev_buttons.append(Button("-", base_x, y, btn_w, btn_h, minus_cb))
            self.dev_buttons.append(Button("+", base_x + btn_w + 10, y, btn_w, btn_h, plus_cb))

        add_pair(0,
                 lambda: self._change_enemy_count(-1),
                 lambda: self._change_enemy_count(+1))
        add_pair(1,
                 lambda: self._change_enchantment_min(-1),
                 lambda: self._change_enchantment_min(+1))
        add_pair(2,
                 lambda: self._change_enchantment_max(-1),
                 lambda: self._change_enchantment_max(+1))
        add_pair(3,
                 lambda: self._change_level_min(-1),
                 lambda: self._change_level_min(+1))
        add_pair(4,
                 lambda: self._change_level_max(-1),
                 lambda: self._change_level_max(+1))

    # --- Hilfsfunktionen zum Ändern + Speichern ---

    def _save_level_config(self):
        save_level_settings(self.level_key, self.level_config)

    def _change_enemy_count(self, delta):
        v = int(self.level_config.get("enemy_count", 5)) + delta
        v = max(1, min(50, v))
        self.level_config["enemy_count"] = v
        self._save_level_config()

    def _change_enchantment_min(self, delta):
        min_v = int(self.level_config.get("enchantment_min", 0)) + delta
        max_v = int(self.level_config.get("enchantment_max", 0))
        min_v = max(0, min(min_v, max_v))
        self.level_config["enchantment_min"] = min_v
        self._save_level_config()

    def _change_enchantment_max(self, delta):
        min_v = int(self.level_config.get("enchantment_min", 0))
        max_v = int(self.level_config.get("enchantment_max", 0)) + delta
        max_v = max(min_v, min(10, max_v))
        self.level_config["enchantment_max"] = max_v
        self._save_level_config()

    def _change_level_min(self, delta):
        min_v = int(self.level_config.get("monster_level_min", 1)) + delta
        max_v = int(self.level_config.get("monster_level_max", 10))
        min_v = max(1, min(min_v, max_v))
        self.level_config["monster_level_min"] = min_v
        self._save_level_config()

    def _change_level_max(self, delta):
        min_v = int(self.level_config.get("monster_level_min", 1))
        max_v = int(self.level_config.get("monster_level_max", 10)) + delta
        max_v = max(min_v, min(200, max_v))
        self.level_config["monster_level_max"] = max_v
        self._save_level_config()

    
    def back_to_level_selection(self):
        """Zurück zur Level-Auswahl"""
        from scenes.level_selection_scene import LevelSelectionScene
        return LevelSelectionScene(self.slot_index)
    
    def _get_enemy_rect(self, enemy: Dict) -> pygame.Rect:
        """
        Gibt das Rechteck eines Gegners zurück
        
        Args:
            enemy: Gegner-Dictionary
            
        Returns:
            pygame.Rect des Gegners
        """
        x = enemy.get("x", 0)
        y = enemy.get("y", 0)
        size = self.enemy_size
        return pygame.Rect(x - size // 2, y - size // 2, size, size)
    
    def _get_enemy_at_position(self, pos: tuple) -> int:
        """
        Gibt den Index des Gegners an der gegebenen Position zurück
        
        Args:
            pos: (x, y) Mausposition
            
        Returns:
            Index des Gegners oder -1 wenn keiner gefunden
        """
        mouse_x, mouse_y = pos
        
        # Prüfe von hinten nach vorne (zuerst sichtbare Gegner)
        for i in range(len(self.enemies) - 1, -1, -1):
            enemy = self.enemies[i]
            enemy_rect = self._get_enemy_rect(enemy)
            if enemy_rect.collidepoint(mouse_x, mouse_y):
                return i
        
        return -1
    
    def update(self, events):
        """
        Update-Logik für die Battle Scene
        
        Args:
            events: Liste von pygame Events
            
        Returns:
            Neue Scene oder None
        """
        mouse_pos = pygame.mouse.get_pos()
        
        # Prüfe Hover über Gegnern
        hovered_index = self._get_enemy_at_position(mouse_pos)
        self.hovered_enemy = hovered_index
        
        for e in events:
            # Buttons (Zurück + Dev)
            for btn in self.buttons:
                result = btn.handle_event(e)
                if result:
                    return result

            # Dev-Overlay aktiv? Dann nur Dev-Buttons verarbeiten, kein Kampf
            if self.show_dev_overlay:
                for btn in self.dev_buttons:
                    btn.handle_event(e)
                continue

            # Click auf Gegner - Starte Kampf
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                clicked_enemy_index = self._get_enemy_at_position(e.pos)
                if clicked_enemy_index >= 0 and clicked_enemy_index < len(self.enemies):
                    # Simuliere Kampf
                    enemy_died = self._simulate_combat(clicked_enemy_index)
                    
                    # Entferne Gegner wenn tot
                    if enemy_died:
                        self.enemies.pop(clicked_enemy_index)
                        # Setze hover zurück falls der entfernte Gegner gehover wurde
                        if self.hovered_enemy == clicked_enemy_index:
                            self.hovered_enemy = None
                        elif self.hovered_enemy > clicked_enemy_index:
                            # Anpassen des Hover-Index wenn ein vorheriger Gegner entfernt wurde
                            self.hovered_enemy -= 1
        
        # Aktualisiere Schadensanzeigen
        dt = 0.016  # ~60 FPS (wird später durch tatsächliches dt ersetzt wenn nötig)
        self._update_damage_texts(dt)
        
        return None

        
    
    def _update_damage_texts(self, dt: float):
        """
        Aktualisiert Schadensanzeigen
        
        Args:
            dt: Delta-Zeit
        """
        # Entferne abgelaufene Schadensanzeigen und aktualisiere Timer
        updated_texts = []
        for dmg in self.damage_texts:
            # Prüfe ob Gegner noch existiert
            if 0 <= dmg["enemy_index"] < len(self.enemies):
                dmg["timer"] -= dt
                if dmg["timer"] > 0:
                    # Aktualisiere Position (bewegt sich nach oben)
                    dmg["y"] -= 50 * dt
                    updated_texts.append(dmg)
        
        self.damage_texts = updated_texts
    
    def _simulate_combat(self, enemy_index: int) -> bool:
        """
        Simuliert einen Kampf zwischen Spieler und Gegner
        
        Args:
            enemy_index: Index des angegriffenen Gegners
            
        Returns:
            True wenn Gegner gestorben ist, False sonst
        """
        if enemy_index < 0 or enemy_index >= len(self.enemies):
            return False
        
        enemy = self.enemies[enemy_index]
        
        # Prüfe ob Spieler-Stats verfügbar sind
        if not self.player_stats:
            print("Keine Spieler-Stats verfügbar!")
            return False
        
        player_stats = self.player_stats.get("stats", {})
        final_stats = enemy.get("final_stats", enemy.get("generated_stats", {}))
        
        # Hole Spieler-Schaden
        player_damage = player_stats.get("damage", 0)
        
        # Wenn kein direkter Schaden vorhanden, berechne aus Stärke/Intelligenz
        if player_damage <= 0:
            strength = player_stats.get("strength", 0)
            intelligence = player_stats.get("intelligence", 0)
            # Verwende den höheren Wert als Basis-Schaden
            player_damage = max(strength, intelligence) if max(strength, intelligence) > 0 else 5
        
        # Hole Gegner-Verteidigung
        enemy_defense = final_stats.get("defense", 0)
        enemy_armour = final_stats.get("armour", 0)
        total_defense = enemy_defense + enemy_armour
        
        # Berechne tatsächlichen Schaden
        # Schaden = Spieler-Schaden - Gegner-Verteidigung (Minimum 1)
        actual_damage = max(1, player_damage - total_defense)
        
        # Reduziere Gegner-HP
        current_hp = final_stats.get("hp", 0)
        new_hp = max(0, current_hp - actual_damage)
        final_stats["hp"] = new_hp
        
        # Aktualisiere Gegner-Stats
        enemy["final_stats"] = final_stats
        
        # Füge Schadensanzeige hinzu
        enemy_x = enemy.get("x", 0)
        enemy_y = enemy.get("y", 0)
        self.damage_texts.append({
            "x": enemy_x,
            "y": enemy_y - 30,
            "timer": 1.5,  # 1.5 Sekunden sichtbar
            "damage": actual_damage,
            "enemy_index": enemy_index
        })
        
        print(f"⚔️ Kampf: {player_damage} Schaden - {total_defense} Verteidigung = {actual_damage} Schaden")
        print(f"   Gegner HP: {current_hp} -> {new_hp}")
        
        # Prüfe ob Gegner tot ist
        if new_hp <= 0:
            print(f"   ✝️ Gegner '{enemy.get('name', 'Unbekannt')}' ist gestorben!")
            self._handle_enemy_death(enemy)
            return True
        
        return False

    def _handle_enemy_death(self, enemy: Dict[str, Any]):
        """
        Versucht einen Itemdrop zu generieren und speichert ihn im Inventar.
        """
        monster_level = enemy.get("level", 1)
        loot_item = self.loot_generator.generate_loot(monster_level)

        if not loot_item:
            return

        self._add_item_to_inventory(loot_item)
        item_name = loot_item.get("name", loot_item.get("id", "Item"))
        print(f"💰 Loot erhalten: {item_name}")

    def _add_item_to_inventory(self, item: Dict[str, Any]):
        """
        Speichert ein Item im globalen Inventar des aktuellen Slots.
        """
        save_dir = os.path.join(SAVE_ROOT, SAVE_SLOTS[self.slot_index])
        os.makedirs(save_dir, exist_ok=True)
        inventory_path = os.path.join(save_dir, "global_inventory.json")

        try:
            with open(inventory_path, "r", encoding="utf-8") as f:
                inventory = json.load(f)
        except FileNotFoundError:
            inventory = []
        except json.JSONDecodeError:
            inventory = []

        inventory.append(item)

        with open(inventory_path, "w", encoding="utf-8") as f:
            json.dump(inventory, f, ensure_ascii=False, indent=4)
    
    def draw(self, screen):
        """
        Zeichnet die Battle Scene
        
        Args:
            screen: pygame Screen Surface
        """
        # Hintergrund zeichnen
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((30, 50, 30))  # Fallback-Hintergrund
        
        # Titel
        title_text = f"{self.level_type} {self.level_number}"
        title = FONT.render(title_text, True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))
        
        # Zeichne Gegner
        self._draw_enemies(screen)
        
        # Zeichne Tooltip wenn über einem Gegner gehover wird
        if self.hovered_enemy is not None and 0 <= self.hovered_enemy < len(self.enemies):
            self._draw_enemy_tooltip(screen, self.enemies[self.hovered_enemy], mouse_pos=pygame.mouse.get_pos())
        
        # Zeichne Schadensanzeigen
        self._draw_damage_texts(screen)
        
        # Zeichne Spieler-Stats
        if self.player_stats:
            self._draw_player_stats(screen)
        
        # Buttons zeichnen
        for btn in self.buttons:
            btn.draw(screen)
        
        # Dev-Overlay zeichnen, falls aktiv
        if self.show_dev_overlay:
            self._draw_dev_overlay(screen)
    
    def _draw_enemies(self, screen):
        """
        Zeichnet die Gegner auf dem Bildschirm
        
        Args:
            screen: pygame Screen Surface
        """
        for i, enemy in enumerate(self.enemies):
            x = enemy.get("x", 100 + i * 100)
            y = enemy.get("y", 200 + i * 50)
            
            # Zeichne Gegner als Rechteck (später kann dies durch Sprites ersetzt werden)
            # Hover-Effekt: Heller wenn gehover
            is_hovered = (i == self.hovered_enemy)
            color = (255, 100, 100) if is_hovered else (200, 50, 50)  # Helleres Rot wenn gehover
            border_color = (255, 255, 0) if is_hovered else (255, 255, 255)  # Gelber Rand wenn gehover
            
            # Größeres Rechteck für bessere Sichtbarkeit
            enemy_rect = pygame.Rect(x - self.enemy_size // 2, y - self.enemy_size // 2, 
                                   self.enemy_size, self.enemy_size)
            pygame.draw.rect(screen, color, enemy_rect)
            pygame.draw.rect(screen, border_color, enemy_rect, 3 if is_hovered else 2)
            
            # Zeichne Monster-Name mit Farbe je nach "Stufe"
            monster_name = enemy.get("name", "Gegner")

            # Anzahl der Verzauberungen
            enchantments = enemy.get("enchantments", [])
            enchant_count = len(enchantments)

            # Optional: Unique-Info aus Daten
            loot_quality = str(enemy.get("loot_quality", "")).lower()
            is_unique = enemy.get("is_unique", False) or loot_quality == "unique"

            # Farben definieren
            WHITE       = (255, 255, 255)
            BLUE        = (100, 149, 237)   # 1–2 Enchants
            PURPLE      = (186, 85, 211)    # 3–4 Enchants
            GOLD        = (255, 215, 0)     # 5–6 Enchants
            DARK_ORANGE = (210, 120, 0)     # Unique

            # Farbe nach Regel bestimmen
            if is_unique:
                name_color = DARK_ORANGE
            elif enchant_count >= 5:
                name_color = GOLD
            elif enchant_count >= 3:
                name_color = PURPLE
            elif enchant_count >= 1:
                name_color = BLUE
            else:
                name_color = WHITE

            name_text = FONT_SMALL.render(monster_name, True, name_color)
            screen.blit(name_text, (x - name_text.get_width() // 2, y - 40))
            
            # Zeichne HP-Balken (verwende finale Stats mit Verzauberungen)
            final_stats = enemy.get("final_stats", enemy.get("generated_stats", {}))
            hp = final_stats.get("hp", 0)
            max_hp = final_stats.get("max_hp", hp)
            
            if max_hp > 0:
                hp_bar_width = 60
                hp_bar_height = 6
                hp_percent = hp / max_hp
                
                # Hintergrund (schwarz)
                bar_x = x - hp_bar_width // 2
                bar_y = y + 30
                pygame.draw.rect(screen, (0, 0, 0), 
                               (bar_x, bar_y, hp_bar_width, hp_bar_height))
                
                # HP (grün zu rot basierend auf HP%)
                hp_color = (
                    int(255 * (1 - hp_percent)),
                    int(255 * hp_percent),
                    0
                )
                hp_width = int(hp_bar_width * hp_percent)
                pygame.draw.rect(screen, hp_color,
                               (bar_x, bar_y, hp_width, hp_bar_height))
            
            # Zeichne Verzauberungs-Anzahl wenn vorhanden
            enchantments = enemy.get("enchantments", [])
            if enchantments:
                enchant_text = FONT_SMALL.render(
                    f"{len(enchantments)} Verz.", True, (255, 215, 0)
                )
                screen.blit(enchant_text, (x - enchant_text.get_width() // 2, y + 40))
    
    def _draw_enemy_tooltip(self, screen: pygame.Surface, enemy: Dict, mouse_pos: tuple):
        """
        Zeichnet ein Tooltip mit Stats und Verzauberungen des Gegners
        
        Args:
            screen: pygame Screen Surface
            enemy: Gegner-Dictionary
            mouse_pos: (x, y) Mausposition
        """
        mouse_x, mouse_y = mouse_pos
        
        # Sammle alle Tooltip-Informationen
        lines = []
        
        # Name
        monster_name = enemy.get("name", "Unbekannter Gegner")
        monster_level = enemy.get("level", 1)
        lines.append(f"{monster_name} (Level {monster_level})")
        lines.append("")  # Leerzeile
        
        # Stats (mit Verzauberungen berechnet)
        final_stats = enemy.get("final_stats", enemy.get("generated_stats", {}))
        enchantment_bonuses = enemy.get("enchantment_bonuses", {})
        
        if final_stats:
            lines.append("Stats:")
            
            # HP mit Verzauberungsbonus
            hp = final_stats.get("hp", 0)
            max_hp = final_stats.get("max_hp", hp)
            hp_bonus = enchantment_bonuses.get("hp", 0)
            if hp_bonus > 0:
                lines.append(f"  HP: {hp}/{max_hp} ({hp_bonus:+d} von Verzauberung)")
            else:
                lines.append(f"  HP: {hp}/{max_hp}")
            
            # Schaden mit Verzauberungsbonus
            damage = final_stats.get("damage", 0)
            damage_bonus = enchantment_bonuses.get("damage", 0)
            if damage_bonus > 0:
                lines.append(f"  Schaden: {damage} ({damage_bonus:+d} von Verzauberung)")
            else:
                lines.append(f"  Schaden: {damage}")
            
            # Verteidigung mit Verzauberungsbonus
            defense = final_stats.get("defense", 0)
            defense_bonus = enchantment_bonuses.get("defense", 0)
            if defense_bonus > 0:
                lines.append(f"  Verteidigung: {defense} ({defense_bonus:+d} von Verzauberung)")
            else:
                lines.append(f"  Verteidigung: {defense}")
            
            # Angriffsgeschwindigkeit mit Verzauberungsbonus
            attack_speed = final_stats.get("attack_speed", 1.0)
            attack_speed_bonus = enchantment_bonuses.get("attack_speed", 0.0)
            if attack_speed_bonus > 0:
                lines.append(f"  Angriffsgeschw.: {attack_speed:.1f} ({attack_speed_bonus:+.2f} von Verzauberung)")
            else:
                lines.append(f"  Angriffsgeschw.: {attack_speed:.1f}")
            
            # Ausweichen
            evasion = final_stats.get("evasion", 0)
            lines.append(f"  Ausweichen: {evasion}")
        
        # Verzauberungen
        enchantments = enemy.get("enchantments", [])
        if enchantments:
            lines.append("")  # Leerzeile
            lines.append(f"Verzauberungen ({len(enchantments)}):")
            for enchant in enchantments:
                name = enchant.get("name", "Unbekannt")
                value = enchant.get("value", 0)
                value_type = enchant.get("type", "")
                
                # Formatiere Wert je nach Typ
                if "%" in value_type or "percent" in value_type.lower():
                    display_value = f"+{value}%"
                else:
                    display_value = f"+{value}"
                
                lines.append(f"  • {name}: {display_value}")
        else:
            lines.append("")  # Leerzeile
            lines.append("Keine Verzauberungen")
        
        # Berechne Tooltip-Größe
        padding = 10
        line_height = 20
        max_width = 0
        line_surfaces = []
        
        for line in lines:
            if line:  # Nicht-leere Zeile
                surf = FONT_SMALL.render(line, True, (255, 255, 255))
                line_surfaces.append((surf, line))
                max_width = max(max_width, surf.get_width())
            else:  # Leerzeile
                line_surfaces.append((None, ""))
        
        tooltip_width = max_width + padding * 2
        tooltip_height = len(lines) * line_height + padding * 2
        
        # Positioniere Tooltip (rechts und unterhalb der Maus, aber nicht außerhalb des Bildschirms)
        tooltip_x = mouse_x + 15
        tooltip_y = mouse_y + 15
        
        # Prüfe ob Tooltip außerhalb des Bildschirms wäre
        if tooltip_x + tooltip_width > WIDTH:
            tooltip_x = mouse_x - tooltip_width - 15  # Links von der Maus
        if tooltip_y + tooltip_height > HEIGHT:
            tooltip_y = mouse_y - tooltip_height - 15  # Oberhalb der Maus
        
        # Zeichne Tooltip-Hintergrund
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        
        # Dunkler Hintergrund mit Transparenz-Effekt
        tooltip_surface = pygame.Surface((tooltip_width, tooltip_height))
        tooltip_surface.set_alpha(240)
        tooltip_surface.fill((20, 20, 30))
        screen.blit(tooltip_surface, (tooltip_x, tooltip_y))
        
        # Rand
        pygame.draw.rect(screen, (100, 150, 255), tooltip_rect, 2)
        
        # Zeichne Text
        current_y = tooltip_y + padding
        for surf, line in line_surfaces:
            if surf:
                screen.blit(surf, (tooltip_x + padding, current_y))
            current_y += line_height
    
    def _draw_player_stats(self, screen: pygame.Surface):
        """
        Zeichnet Spieler-Stats auf dem Bildschirm
        
        Args:
            screen: pygame Screen Surface
        """
        if not self.player_stats:
            return
        
        stats = self.player_stats.get("stats", {})
        player_name = self.player_stats.get("name", "Unbekannt")
        class_name = self.player_stats.get("class_name", "Unbekannt")
        level = self.player_stats.get("level", 1)
        
        # Position des Stats-Panels (links unten)
        panel_x = 20
        panel_y = HEIGHT - 240
        panel_width = 280
        panel_height = 220
        padding = 10
        
        # Zeichne Panel-Hintergrund
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(220)
        panel_surface.fill((20, 20, 40))
        screen.blit(panel_surface, (panel_x, panel_y))
        
        # Rand
        pygame.draw.rect(screen, (100, 150, 255), panel_rect, 2)
        
        # Titel
        title_text = f"{player_name} ({class_name})"
        title_surf = FONT.render(title_text, True, (255, 255, 255))
        screen.blit(title_surf, (panel_x + padding, panel_y + padding))
        
        level_text = f"Level {level}"
        level_surf = FONT_SMALL.render(level_text, True, (200, 200, 255))
        screen.blit(level_surf, (panel_x + padding, panel_y + padding + 25))
        
        # Stats
        current_y = panel_y + padding + 50
        line_height = 20
        
        # Grundwerte
        stat_lines = [
            ("HP", stats.get("health", 0), stats.get("max_health", 0), True),
            ("Stärke", stats.get("strength", 0), None, False),
            ("Intelligenz", stats.get("intelligence", 0), None, False),
            ("Geschick", stats.get("dexterity", 0), None, False),
            ("Geschwindigkeit", stats.get("speed", 0), None, False),
        ]
        
        for label, value, max_value, is_hp in stat_lines:
            if is_hp and max_value:
                text = f"{label}: {value}/{max_value}"
            else:
                text = f"{label}: {value}"
            
            stat_surf = FONT_SMALL.render(text, True, (255, 255, 255))
            screen.blit(stat_surf, (panel_x + padding, current_y))
            current_y += line_height
        
        # Kampf-Stats
        current_y += 5  # Kleiner Abstand
        
        combat_stats = [
            ("Schaden", stats.get("damage", 0)),
            ("Verteidigung", stats.get("defense", 0) + stats.get("magic_defense", 0)),
            ("Rüstung", stats.get("armour", 0)),
            ("Ausweichen", stats.get("evasion", 0)),
        ]
        
        for label, value in combat_stats:
            if value > 0:  # Nur anzeigen wenn > 0
                text = f"{label}: {value}"
                stat_surf = FONT_SMALL.render(text, True, (200, 255, 200))
                screen.blit(stat_surf, (panel_x + padding, current_y))
                current_y += line_height
        
        # Attack Speed
        attack_speed = stats.get("attack_speed", 1.0)
        if attack_speed != 1.0:
            text = f"Angriffsgeschw.: {attack_speed:.2f}"
            stat_surf = FONT_SMALL.render(text, True, (200, 255, 200))
            screen.blit(stat_surf, (panel_x + padding, current_y))
    
    def _draw_damage_texts(self, screen: pygame.Surface):
        """
        Zeichnet Schadensanzeigen über Gegnern
        
        Args:
            screen: pygame Screen Surface
        """
        for dmg in self.damage_texts:
            if dmg["timer"] > 0:
                # Berechne Alpha (Transparenz) basierend auf verbleibender Zeit
                alpha = int(255 * min(1.0, dmg["timer"] / 1.5))
                
                # Erstelle Schadens-Text
                damage_text = f"-{dmg['damage']}"
                damage_surf = FONT_SMALL.render(damage_text, True, (255, 100, 100))
                damage_surf.set_alpha(alpha)
                
                # Zeichne Text
                text_x = dmg["x"] - damage_surf.get_width() // 2
                text_y = int(dmg["y"])
                screen.blit(damage_surf, (text_x, text_y))

    def _draw_dev_overlay(self, screen):
        import pygame as pg

        panel_width = int(WIDTH * 0.6)
        panel_height = int(HEIGHT * 0.6)
        panel_x = (WIDTH - panel_width) // 2
        panel_y = (HEIGHT - panel_height) // 2

        # halbtransparentes Overlay
        overlay = pg.Surface((panel_width, panel_height))
        overlay.set_alpha(220)
        overlay.fill((20, 20, 40))
        screen.blit(overlay, (panel_x, panel_y))

        pg.draw.rect(screen, (150, 180, 255), (panel_x, panel_y, panel_width, panel_height), 3)

        title = FONT.render(f"Dev Level-Settings: {self.level_key}", True, (255, 255, 255))
        screen.blit(title, (panel_x + 20, panel_y + 20))

        s = self.level_config
        lines = [
            f"Gegneranzahl: {s.get('enemy_count', 5)}",
            f"Verzauberungen pro Gegner: {s.get('enchantment_min', 0)} - {s.get('enchantment_max', 0)}",
            f"Monster-Levelbereich: {s.get('monster_level_min', 1)} - {s.get('monster_level_max', 10)}",
        ]

        y = panel_y + 80
        for line in lines:
            txt = FONT.render(line, True, (230, 230, 230))
            screen.blit(txt, (panel_x + 20, y))
            y += 40

        # Dev-Buttons zeichnen
        for btn in self.dev_buttons:
            btn.draw(screen)
