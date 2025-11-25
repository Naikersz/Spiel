import pygame
from ui.button import Button
from ui.fonts import FONT, FONT_BIG
from core.constants import WIDTH, HEIGHT
from core.dev_settings import load_dev_settings, save_dev_settings, set_dev_mode


class OptionsScene:
    def __init__(self):
        self.settings = load_dev_settings()
        self.buttons = []
        self.create_buttons()

    def create_buttons(self):
        center_x = WIDTH // 2
        w, h = 300, 60
        start_y = 180
        gap = 80

        # Dev-Modus Button
        self.dev_button = Button(
            self._dev_button_text(),
            center_x - w // 2,
            start_y,
            w,
            h,
            self.toggle_dev_mode
        )
        self.buttons.append(self.dev_button)

        # Zurück
        self.buttons.append(
            Button(
                "Zurück",
                center_x - w // 2,
                start_y + gap,
                w,
                h,
                self.back_to_main_menu
            )
        )

    def _dev_button_text(self):
        return f"Dev-Modus: {'AN' if self.settings.get('dev_mode') else 'AUS'}"

    def toggle_dev_mode(self):
        self.settings["dev_mode"] = not self.settings.get("dev_mode", False)
        save_dev_settings(self.settings)           # globalen Zustand aktualisieren
        set_dev_mode(self.settings["dev_mode"])    # explizit setzen (optional, aber klar)
        # Button-Text aktualisieren
        self.dev_button.text = self._dev_button_text()
        print(f"Dev-Modus ist jetzt: {self.settings['dev_mode']}")


    def back_to_main_menu(self):
        from scenes.main_menu import MainMenu
        return MainMenu()

    def update(self, events):
        for e in events:
            for b in self.buttons:
                result = b.handle_event(e)
                if result:
                    return result

    def draw(self, screen):
        screen.fill((20, 20, 30))

        title = FONT_BIG.render("Optionen", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))

        info = FONT.render(
            "Dev-Modus: zeigt extra Balancing-Panel in der Level Auswahl",
            True,
            (200, 200, 200)
        )
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, 120))

        for b in self.buttons:
            b.draw(screen)
