import pygame

# --- КОНСТАНТЫ ДЛЯ ПОЛЗУНКА ГРОМКОСТИ (ПЕРЕМЕЩЕНЫ ИЗ main.py) ---
SLIDER_TRACK_COLOR = (120, 120, 120)  # Средний серый для дорожки ползунка
SLIDER_INNER_TRACK_COLOR = (80, 80, 80)  # Темно-серый для внутренней части дорожки
SLIDER_KNOB_COLOR = (200, 200, 200)  # Светло-серый для ручки ползунка
SLIDER_KNOB_BORDER_COLOR = (0, 0, 0)  # Черный для границ ручки ползунка
SLIDER_MARK_COLOR = (0, 0, 0)  # Черный для меток громкости

SLIDER_MARKS_COUNT = 8
SLIDER_MARK_LENGTH = 15
SLIDER_MARK_THICKNESS = 2

SLIDER_BORDER_COLOR = (0, 0, 0)
SLIDER_TRACK_BORDER_THICKNESS = 2

MOSAIC_BLOCK_COUNT_WIDTH = 5
MOSAIC_BLOCK_COUNT_HEIGHT = 15
MOSAIC_COLOR_1 = (0, 0, 0)
MOSAIC_COLOR_2 = (145, 145, 145)

SLIDER_TRACK_FIXED_WIDTH = 20
SLIDER_TRACK_FIXED_HEIGHT = 200

# Константы для оранжевого фона ползунка (перемещены из main.py)
RIGHT_RECT_WIDTH = 60
RIGHT_RECT_HEIGHT_CUSTOM = 250
RIGHT_RECT_POS_X = 660  # Фиксированная X-позиция для оранжевого фона
RIGHT_RECT_POS_Y = 80  # Фиксированная Y-позиция для оранжевого фона

# Новые константы для прямого управления позицией дорожки ползунка
# Эти позиции теперь рассчитываются относительно RIGHT_RECT_POS_X и RIGHT_RECT_POS_Y,
# но вы можете изменить их на абсолютно фиксированные значения, если хотите полностью
# отвязать ползунок от его фона.
SLIDER_TRACK_POS_X = RIGHT_RECT_POS_X + (RIGHT_RECT_WIDTH // 2) - (SLIDER_TRACK_FIXED_WIDTH // 2)
SLIDER_TRACK_POS_Y = RIGHT_RECT_POS_Y + (RIGHT_RECT_HEIGHT_CUSTOM // 2) - (SLIDER_TRACK_FIXED_HEIGHT // 2)

KNOB_VISUAL_WIDTH = 35
KNOB_VISUAL_HEIGHT = 10
KNOB_CAP_HEIGHT = 6
KNOB_CAP_WIDTH_FACTOR = 0.8
KNOB_VERTICAL_SPACING = -2
KNOB_BORDER_THICKNESS = 2
KNOB_RADIUS = 1

KNOB_TOTAL_VERTICAL_PADDING_TOP = 6
KNOB_TOTAL_VERTICAL_PADDING_BOTTOM = 6

TOTAL_KNOB_VISUAL_HEIGHT = KNOB_VISUAL_HEIGHT + (2 * KNOB_CAP_HEIGHT) + (2 * KNOB_VERTICAL_SPACING)


class VolumeSliderManager:
    """
    Управляет логикой ползунка громкости, его отображением и взаимодействием.
    """

    def __init__(self, app_instance):
        """
        Инициализирует VolumeSliderManager.

        Args:
            app_instance: Экземпляр SoundpadApp для доступа к его атрибутам
                          (экран, громкость, позиции).
        """
        self.app = app_instance
        self.is_dragging_volume_knob = False
        # Здесь мы не создаем self.app.volume_track_rect и self.app.right_rectangle_rect
        # вместо этого, SoundpadApp будет создавать их, используя константы,
        # которые мы определили в этом файле.

    def draw_volume_slider(self):
        """
        Рисует элементы ползунка громкости.
        """
        surface = self.app.screen
        volume_track_rect = self.app.volume_track_rect # Используем rect из app_instance
        volume = self.app.volume

        pygame.draw.rect(surface, SLIDER_BORDER_COLOR, volume_track_rect, border_radius=10)
        pygame.draw.rect(surface, SLIDER_TRACK_COLOR, volume_track_rect.inflate(-2 * SLIDER_TRACK_BORDER_THICKNESS,
                                                                                 -2 * SLIDER_TRACK_BORDER_THICKNESS),
                         border_radius=8)

        inner_texture_rect = volume_track_rect.inflate(-2 * SLIDER_TRACK_BORDER_THICKNESS,
                                                        -2 * SLIDER_TRACK_BORDER_THICKNESS)

        # Рисование мозаичного узора
        if MOSAIC_BLOCK_COUNT_WIDTH <= 0 or MOSAIC_BLOCK_COUNT_HEIGHT <= 0:
            pygame.draw.rect(surface, MOSAIC_COLOR_1, inner_texture_rect)
        else:
            potential_block_side_w = inner_texture_rect.width / MOSAIC_BLOCK_COUNT_WIDTH
            potential_block_side_h = inner_texture_rect.height / MOSAIC_BLOCK_COUNT_HEIGHT

            block_side = max(1, int(min(potential_block_side_w, potential_block_side_h)))

            actual_blocks_width = int(inner_texture_rect.width / block_side) + (
                1 if inner_texture_rect.width % block_side > 0 else 0)
            actual_blocks_height = int(inner_texture_rect.height / block_side) + (
                1 if inner_texture_rect.height % block_side > 0 else 0)

            for row_idx in range(actual_blocks_height):
                for col_idx in range(actual_blocks_width):
                    x = inner_texture_rect.left + col_idx * block_side
                    y = inner_texture_rect.top + row_idx * block_side

                    draw_color = MOSAIC_COLOR_1 if (row_idx + col_idx) % 2 == 0 else MOSAIC_COLOR_2

                    block_rect = pygame.Rect(x, y, block_side, block_side)

                    clipped_rect = block_rect.clip(inner_texture_rect)

                    if clipped_rect.width > 0 and clipped_rect.height > 0:
                        pygame.draw.rect(surface, draw_color, clipped_rect)

        # Расчет позиции ручки ползунка
        if TOTAL_KNOB_VISUAL_HEIGHT > volume_track_rect.height:
            TOTAL_KNOB_VISUAL_HEIGHT_ADJUSTED = volume_track_rect.height
        else:
            TOTAL_KNOB_VISUAL_HEIGHT_ADJUSTED = TOTAL_KNOB_VISUAL_HEIGHT

        knob_visual_top_at_highest_pos = volume_track_rect.top + KNOB_TOTAL_VERTICAL_PADDING_TOP
        knob_visual_top_at_lowest_pos = volume_track_rect.bottom - KNOB_TOTAL_VERTICAL_PADDING_BOTTOM - TOTAL_KNOB_VISUAL_HEIGHT_ADJUSTED

        knob_y_pos_for_rect = knob_visual_top_at_highest_pos + (1 - volume) * \
                              (knob_visual_top_at_lowest_pos - knob_visual_top_at_highest_pos)

        # Обновляем rect ручки ползунка в app_instance, чтобы его можно было использовать для обработки событий
        self.app.volume_knob_rect = pygame.Rect(
            volume_track_rect.centerx - (KNOB_VISUAL_WIDTH / 2),
            knob_y_pos_for_rect,
            KNOB_VISUAL_WIDTH,
            TOTAL_KNOB_VISUAL_HEIGHT_ADJUSTED
        )

        # Рисование меток громкости
        knob_main_body_top_at_highest_pos = volume_track_rect.top + KNOB_TOTAL_VERTICAL_PADDING_TOP + KNOB_CAP_HEIGHT + KNOB_VERTICAL_SPACING
        knob_main_body_top_at_lowest_pos = volume_track_rect.bottom - KNOB_TOTAL_VERTICAL_PADDING_BOTTOM - KNOB_CAP_HEIGHT - KNOB_VERTICAL_SPACING - KNOB_VISUAL_HEIGHT

        mark_y_center_at_max_volume = knob_main_body_top_at_highest_pos + (KNOB_VISUAL_HEIGHT / 2)
        mark_y_center_at_min_volume = knob_main_body_top_at_lowest_pos + (KNOB_VISUAL_HEIGHT / 2)

        total_mark_span_height = mark_y_center_at_min_volume - mark_y_center_at_max_volume

        if SLIDER_MARKS_COUNT > 1:
            vertical_spacing = total_mark_span_height / (SLIDER_MARKS_COUNT - 1)
        else:
            vertical_spacing = 0

        for i in range(SLIDER_MARKS_COUNT):
            mark_y = mark_y_center_at_min_volume - (i * vertical_spacing)

            mark_end_x = volume_track_rect.left
            mark_start_x = mark_end_x - SLIDER_MARK_LENGTH

            pygame.draw.line(surface, SLIDER_MARK_COLOR, (mark_start_x, mark_y), (mark_end_x, mark_y),
                             SLIDER_MARK_THICKNESS)

        # Рисование ручки ползунка (три части: верхнее крыло, тело, нижнее крыло)
        top_cap_width = KNOB_VISUAL_WIDTH * KNOB_CAP_WIDTH_FACTOR
        wing_top_rect = pygame.Rect(
            volume_track_rect.centerx - (top_cap_width / 2),
            self.app.volume_knob_rect.y,
            top_cap_width,
            KNOB_CAP_HEIGHT
        )
        pygame.draw.rect(surface, SLIDER_KNOB_BORDER_COLOR, wing_top_rect, width=KNOB_BORDER_THICKNESS,
                         border_radius=KNOB_RADIUS)
        pygame.draw.rect(surface, SLIDER_KNOB_COLOR,
                         wing_top_rect.inflate(-2 * KNOB_BORDER_THICKNESS, -2 * KNOB_BORDER_THICKNESS),
                         border_radius=KNOB_RADIUS)

        main_body_rect = pygame.Rect(
            volume_track_rect.centerx - (KNOB_VISUAL_WIDTH / 2),
            wing_top_rect.bottom + KNOB_VERTICAL_SPACING,
            KNOB_VISUAL_WIDTH,
            KNOB_VISUAL_HEIGHT
        )
        pygame.draw.rect(surface, SLIDER_KNOB_BORDER_COLOR, main_body_rect, width=KNOB_BORDER_THICKNESS,
                         border_radius=KNOB_RADIUS)
        pygame.draw.rect(surface, SLIDER_KNOB_COLOR,
                         main_body_rect.inflate(-2 * KNOB_BORDER_THICKNESS, -2 * KNOB_BORDER_THICKNESS),
                         border_radius=KNOB_RADIUS)

        bottom_cap_width = KNOB_VISUAL_WIDTH * KNOB_CAP_WIDTH_FACTOR
        wing_bottom_rect = pygame.Rect(
            volume_track_rect.centerx - (bottom_cap_width / 2),
            main_body_rect.bottom + KNOB_VERTICAL_SPACING,
            bottom_cap_width,
            KNOB_CAP_HEIGHT
        )
        pygame.draw.rect(surface, SLIDER_KNOB_BORDER_COLOR, wing_bottom_rect, width=KNOB_BORDER_THICKNESS,
                         border_radius=KNOB_RADIUS)
        pygame.draw.rect(surface, SLIDER_KNOB_COLOR,
                         wing_bottom_rect.inflate(-2 * KNOB_BORDER_THICKNESS, -2 * KNOB_BORDER_THICKNESS),
                         border_radius=KNOB_RADIUS)

    def handle_mouse_button_down(self, pos):
        """
        Обрабатывает событие нажатия кнопки мыши для ползунка.
        """
        if self.app.volume_knob_rect.collidepoint(pos):
            self.is_dragging_volume_knob = True
            return True
        return False

    def handle_mouse_button_up(self):
        """
        Обрабатывает событие отпускания кнопки мыши для ползунка.
        """
        self.is_dragging_volume_knob = False

    def handle_mouse_motion(self, event_pos):
        """
        Обрабатывает событие движения мыши для ползунка.
        """
        if self.is_dragging_volume_knob:
            knob_visual_top_at_highest_pos = self.app.volume_track_rect.top + KNOB_TOTAL_VERTICAL_PADDING_TOP
            knob_visual_top_at_lowest_pos = self.app.volume_track_rect.bottom - KNOB_TOTAL_VERTICAL_PADDING_BOTTOM - TOTAL_KNOB_VISUAL_HEIGHT

            clamped_knob_top_y = max(knob_visual_top_at_highest_pos,
                                     min(knob_visual_top_at_lowest_pos, event_pos[1]))

            knob_y_travel_range = knob_visual_top_at_lowest_pos - knob_visual_top_at_highest_pos

            if knob_y_travel_range > 0:
                self.app.volume = 1.0 - (
                        (clamped_knob_top_y - knob_visual_top_at_highest_pos) / knob_y_travel_range)
            else:
                self.app.volume = 1.0

            self.app.volume = max(0.0, min(1.0, self.app.volume))

            if self.app.sound:
                self.app.sound.set_volume(self.app.volume)
            return True
        return False
