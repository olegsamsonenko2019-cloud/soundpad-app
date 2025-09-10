import pygame

# --- КОНСТАНТЫ ДЛЯ СЛОЕВ ---
# Цвета для точек слоев и для подсветки отдельных кнопок
# Эти цвета являются специфичными для менеджера слоев
LAYER_COLORS_FOR_BUTTONS = [(255, 0, 0), (0, 255, 0), (255, 255, 255)]  # RED, GREEN, WHITE

# Константы для отрисовки точек слоев
DOT_SIZE = 20
DOT_SPACING = 25  # Горизонтальный интервал между точками (УВЕЛИЧЕНО)

# КОНСТАНТЫ ДЛЯ РАСПОЛОЖЕНИЯ СЛОЕВ ВНИЗУ ПОД СЕТКОЙ КНОПОК (ВОССТАНОВЛЕНО)
LAYER_SWITCHER_START_X_OFFSET = 180  # Горизонтальное смещение для всего блока переключателей слоев
LAYER_SWITCHER_VERTICAL_OFFSET = 15  # Вертикальное смещение блока переключателей слоев от нижней части сетки кнопок (УМЕНЬШЕНО)

# Факторы для изменения яркости слоев
BRIGHTEN_FACTOR = 1.3  # Увеличиваем яркость активного слоя
DARKEN_FACTOR = 0.3  # Уменьшаем яркость неактивных слоев


def adjust_brightness(color, factor):
    """
    Регулирует яркость цвета.
    Factor > 1 для осветления, Factor < 1 для затемнения.
    Каждый компонент цвета (R, G, B) корректируется и ограничивается диапазоном [0, 255].
    """
    return tuple(max(0, min(255, int(c * factor))) for c in color)


class LayerManager:
    """
    Управляет логикой слоев, их отображением и переключением.
    """

    def __init__(self, app_instance, font_small):
        """
        Инициализирует LayerManager.

        Args:
            app_instance: Экземпляр SoundpadApp для доступа к его атрибутам
                          (экран, позиции, данные слоев, константы кнопок).
            font_small: Объект шрифта для отрисовки текста.
        """
        self.app = app_instance
        self.font_small = font_small

        # Переменные, которые будут обновляться из SoundpadApp
        # Фактические данные слоев (self.app.layers_data) и текущий индекс слоя
        # (self.app.current_layer_index) будут доступны через self.app.
        self.layer_dot_rects = []  # Список Rect'ов для каждой точки слоя
        # Вызов _initialize_layer_dots теперь происходит в SoundpadApp.__init__ после инициализации layers_data

    def _initialize_layer_dots(self):
        """
        Инициализирует позиции и размеры точек для переключения слоев,
        позиционируя их внизу под сеткой кнопок, как на вашем изображении.
        Этот метод теперь должен быть вызван явно из SoundpadApp после загрузки конфигурации.
        """
        # Расчет позиции центра сетки кнопок
        grid_center_x = self.app.grid_start_x + self.app.grid_total_width // 2
        # Расчет Y-позиции для текста "Слой: N/M"
        layer_text_y = self.app.interactive_area_top_y + self.app.grid_total_height + LAYER_SWITCHER_VERTICAL_OFFSET

        # Расчет начальной X-позиции для точек, чтобы они были выровнены по центру под текстом
        total_dots_width = len(self.app.layers_data) * DOT_SIZE + (len(self.app.layers_data) - 1) * DOT_SPACING
        start_x = grid_center_x - total_dots_width // 2

        # Y-позиция для точек, располагается ниже текста "Слой: N/M"
        # Для простоты, пока будем считать, что текст занимает около 20-30 пикселей в высоту.
        # Поэтому добавим небольшой отступ к layer_text_y
        start_y_dots = layer_text_y + 17  # Примерное смещение от нижней части текста

        self.layer_dot_rects = []
        for i in range(len(self.app.layers_data)):
            dot_x = start_x + (i * (DOT_SIZE + DOT_SPACING))
            dot_rect = pygame.Rect(dot_x, start_y_dots, DOT_SIZE, DOT_SIZE)
            self.layer_dot_rects.append(dot_rect)

    def draw_layer_switcher(self):
        """
        Отрисовывает индикаторы слоев (точки), текущий активный слой
        и текст "Слой: N/M".
        """
        # Расчет позиции для текста "Слой: N/M"
        grid_center_x = self.app.grid_start_x + self.app.grid_total_width // 2
        layer_text_y = self.app.interactive_area_top_y + self.app.grid_total_height + LAYER_SWITCHER_VERTICAL_OFFSET

        layer_text = self.font_small.render(
            f"Слой: {self.app.current_layer_index + 1}/{len(self.app.layers_data)}",
            True, self.app.WHITE
        )
        layer_text_rect = layer_text.get_rect(center=(grid_center_x, layer_text_y))
        self.app.screen.blit(layer_text, layer_text_rect)

        # Отрисовка точек слоев
        for i, dot_rect in enumerate(self.layer_dot_rects):
            base_color = LAYER_COLORS_FOR_BUTTONS[i % len(LAYER_COLORS_FOR_BUTTONS)]

            draw_color = base_color
            if i == self.app.current_layer_index:
                # Если это активный слой, осветляем его
                draw_color = adjust_brightness(base_color, BRIGHTEN_FACTOR)
            else:
                # Если это неактивный слой, затемняем его
                draw_color = adjust_brightness(base_color, DARKEN_FACTOR)

            # Рисуем контур точки
            pygame.draw.circle(self.app.screen, self.app.BLACK, dot_rect.center, DOT_SIZE // 2 + 2, 2)
            # Рисуем саму точку с измененной яркостью
            pygame.draw.circle(self.app.screen, draw_color, dot_rect.center, DOT_SIZE // 2)

    def handle_mouse_click(self, pos):
        """
        Обрабатывает клики мыши для переключения слоев.
        """
        # Блокируем переключение, если идет назначение клавиши
        if self.app.program_state == 'configuring' and self.app.button_to_configure is not None:
            return False

        for i, dot_rect in enumerate(self.layer_dot_rects):
            if dot_rect.collidepoint(pos):
                if self.app.current_layer_index != i:
                    self.app.current_layer_index = i
                    print(f"Переключено на слой {self.app.current_layer_index + 1}.")
                return True  # Обработано
        return False  # Не обработано

    def handle_mouse_wheel(self, event_y):
        """
        Обрабатывает прокрутку колеса мыши для переключения слоев.
        """
        # Блокируем переключение, если идет назначение клавиши
        if self.app.program_state == 'configuring' and self.app.button_to_configure is not None:
            return False

        layers_count = len(self.app.layers_data)
        if event_y > 0:  # Прокрутка вверх
            new_layer_index = (self.app.current_layer_index - 1 + layers_count) % layers_count
        elif event_y < 0:  # Прокрутка вниз
            new_layer_index = (self.app.current_layer_index + 1) % layers_count
        else:
            new_layer_index = self.app.current_layer_index

        if new_layer_index != self.app.current_layer_index:
            self.app.current_layer_index = new_layer_index
            print(f"Переключено на слой {self.app.current_layer_index + 1}.")
            return True  # Обработано
        return False  # Не обработано