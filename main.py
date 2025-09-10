import pygame
import sys
import json
import os
import win32gui  # Для манипуляций окном, специфичных для Windows
import win32con  # Для констант Windows
import keyboard  # Для глобальных горячих клавиш
import math
import re  # Импортируем регулярные выражения для поиска чисел в имени пресета
import urllib.request
import threading
import webbrowser

from layer_manager import LayerManager, LAYER_COLORS_FOR_BUTTONS
# Импортируем VolumeSliderManager и константы размеров ползунка напрямую
from volume_slider_manager import (
    VolumeSliderManager,
    SLIDER_TRACK_FIXED_WIDTH,
    SLIDER_TRACK_FIXED_HEIGHT,
    RIGHT_RECT_WIDTH,  # Импортируем из volume_slider_manager
    RIGHT_RECT_HEIGHT_CUSTOM  # Импортируем из volume_slider_manager
)

# --- КОНСТАНТЫ ---
CURRENT_VERSION = "1.0"
# ЗАМЕНИТЕ ЭТУ ССЫЛКУ на свою. Это должна быть RAW ссылка на version.json в вашем репозитории
VERSION_URL = "https://raw.githubusercontent.com/olegsamsonenko2019-cloud/soundpad-app/refs/heads/main/version.json"

# Настройки экрана
SCREEN_WIDTH = 540
SCREEN_HEIGHT = 600
CAPTION = "Настраиваемый саундпад"

# Цвета
DARK_GRAY = (30, 30, 30)
ORANGE = (255, 165, 0)
LIGHT_GRAY = (200, 200, 200)
BLACK = (0, 0, 0)
BORDER_COLOR = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
TRANSPARENT_BLACK = (0, 0, 0, 150)
SLIGHTLY_LIGHTER_ORANGE = (255, 180, 20)
SLIGHTLY_DARKER_WHITE = (220, 220, 220)

# Длительность анимации нажатия кнопки в миллисекундах
ANIMATION_DURATION_MS = 150
# Интервал между кадрами анимации для неназначенных кнопок (в миллисекундах)
FRAME_ANIMATION_INTERVAL_MS = 500
# Минимальный интервал между срабатываниями горячих клавиш для предотвращения двойных срабатываний (в миллисекундах)
HOTKEY_DEBOUNCE_INTERVAL_MS = 100
# Длительность отображения предупреждающего сообщения (в миллисекундах)
WARNING_DURATION_MS = 2000

# Размеры и отступы для кнопок саундпада
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 95
BUTTON_SPACING_X = 20
BUTTON_SPACING_Y = 20
GRID_COLUMNS = 3
GRID_ROWS = 4

# --- КОНСТАНТЫ РАЗМЕЩЕНИЯ ЭЛЕМЕНТОВ ---
# Константы для логотипа
LOGO_IMAGE_PATH = 'assets/logo.png'
LOGO_TARGET_WIDTH = 80
LOGO_TARGET_HEIGHT = 50
LOGO_POS_X = 20
LOGO_POS_Y = 10

# Константы для кнопок управления (Сохранить, Загрузить, Назначить, Сброс)
CONTROL_BUTTON_WIDTH = 110
CONTROL_BUTTON_HEIGHT = 45

MESSAGE_CONFIGURING_Y = 45

# Константы для позиционирования оранжевого фона и ползунка
RIGHT_RECT_POS_X = SCREEN_WIDTH - RIGHT_RECT_WIDTH - 5
RIGHT_RECT_POS_Y = (SCREEN_HEIGHT - RIGHT_RECT_HEIGHT_CUSTOM) // 5

SLIDER_TRACK_POS_X = RIGHT_RECT_POS_X + (RIGHT_RECT_WIDTH // 2) - (SLIDER_TRACK_FIXED_WIDTH // 2)
SLIDER_TRACK_POS_Y = RIGHT_RECT_POS_Y + (RIGHT_RECT_HEIGHT_CUSTOM // 2) - (SLIDER_TRACK_FIXED_HEIGHT // 2)

# Константы для прямого управления позицией всего блока интерактивных элементов (кнопок управления и сетки)
INTERACTIVE_AREA_START_X = 5
INTERACTIVE_AREA_START_Y = (SCREEN_HEIGHT - (
        4 * (CONTROL_BUTTON_HEIGHT + BUTTON_SPACING_Y) - BUTTON_SPACING_Y)) // 5

# Константы для курсора и моргания
CURSOR_BLINK_RATE = 500
CONFIG_BUTTON_BLINK_RATE = 400  # Скорость моргания кнопки при назначении
DOUBLE_CLICK_INTERVAL = 500  # Интервал для двойного клика в миллисекундах

# Путь к файлу звука по умолчанию
DEFAULT_SOUND_FILE_PATH = "sound.wav"
BACKGROUND_IMAGE_PATH = 'assets/fon.jpg'
UNASSIGNED_KEY_IMAGE_PATHS = ['assets/skull.png', 'assets/skull2.png']
TRASH_ICON_PATH = 'assets/tash_can_pixel_icon.ico'  # Путь к иконке корзины
EDIT_ICON_PATH = 'assets/edit_text_icon.ico'  # Путь к иконке редактирования

# Новые константы для управления файлами конфигурации
CONFIGS_DIR = "configs"
INTERNAL_DEFAULT_CONFIG_NAME = "internal_default_blank"  # Скрытое имя пресета по умолчанию


def get_bundle_path(relative_path):
    """
    Возвращает абсолютный путь к файлу ресурса для упакованных ресурсов (только для чтения).
    Используется для изображений, звуков и т.д.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def get_app_base_path():
    """
    Возвращает базовый путь, где запущено приложение.
    Важно для определения места хранения пользовательских данных.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")


def get_config_folder_path():
    """
    Возвращает абсолютный путь к папке, где будут храниться все конфигурации.
    """
    app_base_path = get_app_base_path()
    return os.path.join(app_base_path, CONFIGS_DIR)


def get_config_file_path(config_name):
    """
    Возвращает полный путь к файлу конфигурации по заданному имени.
    """
    config_folder = get_config_folder_path()
    return os.path.join(config_folder, f"{config_name}.json")


class SoundpadApp:
    def __init__(self):
        """Инициализирует приложение Soundpad."""
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(CAPTION)

        self.pygame_window_hwnd = None
        self._setup_window_always_on_top()

        self._cached_font_path = None
        self.font = self._load_font(24)
        self.font_small = self._load_font(18)
        self.font_message = self._load_font(24)

        # Создаем жирные версии шрифтов
        self.font_bold = self._load_font(24)
        self.font_bold.set_bold(True)
        self.font_small_bold = self._load_font(18)
        self.font_small_bold.set_bold(True)

        self.GRID_ROWS = GRID_ROWS
        self.GRID_COLUMNS = GRID_COLUMNS
        self.BUTTON_WIDTH = BUTTON_WIDTH
        self.BUTTON_HEIGHT = BUTTON_HEIGHT
        self.BUTTON_SPACING_X = BUTTON_SPACING_X
        self.BUTTON_SPACING_Y = BUTTON_SPACING_Y
        self.CONTROL_BUTTON_HEIGHT = CONTROL_BUTTON_HEIGHT
        self.BLACK = BLACK
        self.WHITE = WHITE
        self.LIGHT_GRAY = LIGHT_GRAY
        self.ORANGE = ORANGE

        self.unassigned_key_frames = self._load_unassigned_key_frames()
        self.current_frame_index = 0
        self.last_frame_switch_time = pygame.time.get_ticks()

        self.background_image = self._load_background_image(get_bundle_path(BACKGROUND_IMAGE_PATH))
        self.logo_image = self._load_logo_image(get_bundle_path(LOGO_IMAGE_PATH))
        self.trash_icon_image = self._load_scaled_icon(get_bundle_path(TRASH_ICON_PATH), (16, 16))
        self.edit_icon_image = self._load_scaled_icon(get_bundle_path(EDIT_ICON_PATH), (16, 16))

        self.grid_total_width = self.GRID_COLUMNS * self.BUTTON_WIDTH + (self.GRID_COLUMNS - 1) * BUTTON_SPACING_X
        self.grid_total_height = self.GRID_ROWS * self.BUTTON_HEIGHT + (self.GRID_ROWS - 1) * self.BUTTON_SPACING_Y

        LEFT_CONTROL_PANE_SPACING = BUTTON_SPACING_X * 0.5

        # Теперь используем INTERACTIVE_AREA_START_X для начальной X-позиции
        start_x_for_interactive_area = INTERACTIVE_AREA_START_X

        self.control_buttons_start_x = start_x_for_interactive_area
        self.grid_start_x = self.control_buttons_start_x + CONTROL_BUTTON_WIDTH + LEFT_CONTROL_PANE_SPACING

        # Теперь используем INTERACTIVE_AREA_START_Y для начальной Y-позиции кнопок управления
        self.interactive_area_top_y = INTERACTIVE_AREA_START_Y

        # Используем константы для позиционирования оранжевого фона, определенные выше
        self.right_rectangle_rect = pygame.Rect(
            RIGHT_RECT_POS_X,
            RIGHT_RECT_POS_Y,
            RIGHT_RECT_WIDTH,
            RIGHT_RECT_HEIGHT_CUSTOM
        )

        # Используем константы для позиционирования дорожки ползунка, определенные выше
        self.volume_track_rect = pygame.Rect(
            SLIDER_TRACK_POS_X,
            SLIDER_TRACK_POS_Y,
            SLIDER_TRACK_FIXED_WIDTH,
            SLIDER_TRACK_FIXED_HEIGHT
        )

        self.config_folder_path = get_config_folder_path()
        os.makedirs(self.config_folder_path, exist_ok=True)
        print(f"Папка конфигураций: {self.config_folder_path}")

        # Инициализируем layers_data перед LayerManager
        self.layers_data = [[] for _ in range(max(3, len(LAYER_COLORS_FOR_BUTTONS)))]
        self.current_layer_index = 0

        self.layer_manager = LayerManager(self, self.font_small)
        self.volume_manager = VolumeSliderManager(self)  # Инициализация VolumeSliderManager

        self.config_data = self._load_config(INTERNAL_DEFAULT_CONFIG_NAME)  # Загружаем внутренний дефолт
        self.volume = self.config_data.get('volume', 1.0)
        self.current_active_config_name = INTERNAL_DEFAULT_CONFIG_NAME  # Активный пресет - внутренний дефолт

        self._update_layer_button_rects()

        self.layer_manager._initialize_layer_dots()

        self.sound_file_path = get_bundle_path(DEFAULT_SOUND_FILE_PATH)
        self._check_sound_file()

        self.sound = None
        self._load_sound_for_mixer()

        if self.sound:
            self.sound.set_volume(self.volume)

        # Создаем кнопки управления
        self.save_button_data = self._create_control_button(
            text="Сохранить", x=self.control_buttons_start_x, y=self.interactive_area_top_y,
            width=CONTROL_BUTTON_WIDTH, height=CONTROL_BUTTON_HEIGHT
        )
        self.load_button_data = self._create_control_button(
            text="Загрузить", x=self.control_buttons_start_x,
            y=self.interactive_area_top_y + CONTROL_BUTTON_HEIGHT + self.BUTTON_SPACING_Y,
            width=CONTROL_BUTTON_WIDTH, height=CONTROL_BUTTON_HEIGHT
        )
        self.config_button_data = self._create_control_button(
            text="Назначить", x=self.control_buttons_start_x,
            y=self.interactive_area_top_y + 2 * (CONTROL_BUTTON_HEIGHT + self.BUTTON_SPACING_Y),
            width=CONTROL_BUTTON_WIDTH, height=CONTROL_BUTTON_HEIGHT
        )
        self.reset_button_data = self._create_control_button(
            text="Сброс", x=self.control_buttons_start_x,
            y=self.interactive_area_top_y + 3 * (CONTROL_BUTTON_HEIGHT + self.BUTTON_SPACING_Y),
            width=CONTROL_BUTTON_WIDTH, height=CONTROL_BUTTON_HEIGHT
        )

        # Кэшируем поверхности кнопок после их создания
        self._cache_all_button_surfaces()

        self.global_hotkey_map = {}
        self._register_all_assigned_hotkeys()

        self.program_state = 'normal'
        self.button_to_configure = None
        self.unsaved_changes = False

        self.warning_message = ""
        self.warning_message_display_time = 0

        self.current_input_text = ""
        self.input_prompt_message = ""
        self.input_box_rect = None

        self.prompt_context = None

        self.pending_action_after_prompt = None
        self.pending_overwrite_config_name = None
        self.previous_program_state = 'normal'

        self.load_config_file_list = []
        self.load_config_buttons_rects = []
        self.scroll_offset_load_configs = 0

        # New attributes for the save prompt dropdown animation
        self.save_dropdown_active = False  # Target state (True = opening, False = closing)
        self.save_dropdown_rects = []
        self.save_dropdown_scroll_offset = 0
        self.dropdown_arrow_rect = None
        self.dropdown_anim_progress = 0.0  # Current state (0.0 = closed, 1.0 = open)
        self.dropdown_anim_speed = 8.0  # Animation speed
        self.is_dragging_save_scrollbar = False
        self.save_scrollbar_rect = None
        self.save_scrollbar_handle_rect = None

        # New attributes for the load list scrollbar
        self.is_dragging_load_scrollbar = False
        self.load_scrollbar_rect = None
        self.load_scrollbar_handle_rect = None
        self.scrollbar_drag_details = {}

        self.running = True
        self.last_hotkey_trigger_time = 0
        self.cursor_visible = True
        self.cursor_blink_timer = pygame.time.get_ticks()

        # Для анимации черепов
        self.needs_unassigned_redraw = False

        self.last_load_click_time = 0
        self.last_clicked_config_name = None

        self.volume_knob_rect = pygame.Rect(0, 0, 0, 0)
        self.is_dragging_volume_knob = False

        # Атрибуты для переименования и удаления
        self.config_to_rename = None
        self.config_to_delete = None
        self.confirm_delete_yes_rect = None
        self.confirm_delete_no_rect = None

        # Атрибуты для отслеживания двойных кликов по иконкам
        self.last_edit_icon_click = {'name': None, 'time': 0}
        self.last_delete_icon_click = {'name': None, 'time': 0}

        # Атрибуты для системы обновлений
        self.update_info = None
        self.update_prompt_yes_rect = None
        self.update_prompt_no_rect = None

        self.clock = pygame.time.Clock()
        self._check_for_updates()

    def _check_for_updates(self):
        """Запускает проверку обновлений в отдельном потоке, чтобы не блокировать GUI."""
        thread = threading.Thread(target=self._update_worker)
        thread.daemon = True
        thread.start()

    def _update_worker(self):
        """Скачивает и сравнивает версии."""
        try:
            with urllib.request.urlopen(VERSION_URL, timeout=5) as url:
                data = json.loads(url.read().decode())
                latest_version_str = data.get('latest_version', '0')

                # Сравниваем версии как кортежи чисел
                current_v = tuple(map(int, (CURRENT_VERSION.split("."))))
                latest_v = tuple(map(int, (latest_version_str.split("."))))

                if latest_v > current_v:
                    print(f"Доступна новая версия: {latest_version_str}")
                    self.update_info = data
                    # Переключаем состояние в основном потоке через post event
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'action': 'show_update_prompt'}))
                else:
                    print("У вас последняя версия программы.")
        except Exception as e:
            print(f"Не удалось проверить обновления: {e}")

    def _setup_window_always_on_top(self):
        """Пытается установить окно Pygame в режим 'поверх всех окон' в Windows."""
        try:
            self.pygame_window_hwnd = pygame.display.get_wm_info()['window']
            win32gui.SetWindowPos(self.pygame_window_hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            print("Окно Soundpad установлено в режим 'поверх всех окон'.")
        except Exception as e:
            print(f"Ошибка при попытке установить окно 'поверх всех окон': {e}")
            print("Возможные причины:")
            print("1. Библиотека pywin32 не установлена (попробуйте 'pip install pywin32').")
            print("2. Если pywin32 установлен, скрипт пост-установки мог не быть запущен.")
            print("   Попробуйте запустить: python -m pywin32_postinstall -install")
            print("3. Программа не запущена в Windows (режим 'поверх всех окон' специфичен для Windows).")

    def _load_font(self, size):
        """Загружает шрифт с поддержкой кириллицы, с опциями запасных шрифтов."""
        if not self._cached_font_path:
            try_fonts = ["dejavusans", "notosans", "arial", "freesansbold", None]
            actual_font_path = None
            for f_name in try_fonts:
                if f_name is None:
                    actual_font_path = None
                    break
                temp_path = pygame.font.match_font(f_name)
                if temp_path:
                    actual_font_path = temp_path
                    break
            self._cached_font_path = actual_font_path
        return pygame.font.Font(self._cached_font_path, size)

    def _load_unassigned_key_frames(self):
        """Загружает и масштабирует изображения для неназначенных клавиш (кадры анимации)."""
        frames = []
        scaled_width = int(self.BUTTON_WIDTH * 0.8)
        scaled_height = int(self.BUTTON_HEIGHT * 0.8)

        for path in UNASSIGNED_KEY_IMAGE_PATHS:
            full_path = get_bundle_path(path)
            if os.path.exists(full_path):
                try:
                    image = pygame.image.load(full_path).convert_alpha()
                    frames.append(pygame.transform.smoothscale(image, (scaled_width, scaled_height)))
                except pygame.error as e:
                    print(f"Ошибка загрузки или масштабирования изображения '{full_path}': {e}")
            else:
                print(f"Предупреждение: изображение '{full_path}' не найдено.")
        if not frames:
            print(
                "Предупреждение: Не найдено изображений для неназначенных клавиш. Кнопки без назначенного текста будут пустыми.")
        return frames

    def _load_background_image(self, path):
        """Загружает и масштабирует фоновое изображение под размер экрана."""
        if os.path.exists(path):
            try:
                image = pygame.image.load(path).convert()
                return pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except pygame.error as e:
                print(f"Ошибка загрузки или масштабирования фонового изображения '{path}': {e}")
        else:
            print(f"Предупреждение: фоновое изображение '{path}' не найдено.")
        return None

    def _load_logo_image(self, path):
        """Загружает и масштабирует изображение логотипа."""
        if os.path.exists(path):
            try:
                image = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(image, (LOGO_TARGET_WIDTH, LOGO_TARGET_HEIGHT))
            except pygame.error as e:
                print(f"Ошибка загрузки или масштабирования изображения логотипа '{path}': {e}")
        else:
            print(f"Предупреждение: изображение логотипа '{path}' не найдено.")
        return None

    def _load_scaled_icon(self, path, size):
        """Загружает и масштабирует изображение иконки."""
        if os.path.exists(path):
            try:
                image = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(image, size)
            except pygame.error as e:
                print(f"Ошибка загрузки или масштабирования иконки '{path}': {e}")
        else:
            print(f"Предупреждение: файл иконки '{path}' не найден.")
        return None

    def _create_initial_default_layer_data(self):
        """
        Возвращает базовую структуру данных для нового слоя по умолчанию.
        Используется для начальной инициализации layers_data.
        Возвращает данные в JSON-совместимом формате (список для 'rect').
        """
        return [
            {'text': '', 'rect': [0, 0, self.BUTTON_WIDTH, self.BUTTON_HEIGHT], 'last_pressed_time': 0}
            for _ in range(self.GRID_ROWS * self.GRID_COLUMNS)
        ]

    def _update_layer_button_rects(self):
        """
        Обновляет прямоугольники (Rect-ы) всех кнопок в self.layers_data
        в соответствии с текущими параметрами позиционирования.
        Этот метод следует вызывать после любой операции, которая может изменить расположение слоев
        (например, загрузка новой конфигурации, инициализация).
        """
        interactive_area_top_y_for_grid = INTERACTIVE_AREA_START_Y

        for layer_index, layer in enumerate(self.layers_data):
            for row in range(self.GRID_ROWS):
                for col in range(self.GRID_COLUMNS):
                    idx = row * self.GRID_COLUMNS + col
                    x = self.grid_start_x + col * (self.BUTTON_WIDTH + BUTTON_SPACING_X)
                    y = interactive_area_top_y_for_grid + row * (self.BUTTON_HEIGHT + self.BUTTON_SPACING_Y)
                    if idx < len(layer):
                        # Всегда устанавливаем rect в новый объект pygame.Rect, используя рассчитанные координаты
                        layer[idx]['rect'] = pygame.Rect(x, y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
                    else:
                        # Если в загруженном слое меньше кнопок, чем ожидается, добавляем новые с правильными Rect
                        new_rect = pygame.Rect(x, y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
                        layer.append({'text': '', 'rect': new_rect, 'last_pressed_time': 0})

    def _check_sound_file(self):
        """Проверяет существование звукового файла и выходит, если он не найден."""
        if not os.path.exists(self.sound_file_path):
            print(f"Ошибка: Звуковой файл '{self.sound_file_path}' не найден.")
            print("Убедитесь, что файл находится в той же папке, что и программа.")
            self.running = False
            return False
        return True

    def _load_sound_for_mixer(self):
        """Загружает звуковой файл с помощью pygame.mixer.Sound."""
        try:
            self.sound = pygame.mixer.Sound(self.sound_file_path)
            print(f"Звуковой файл '{self.sound_file_path}' загружен в pygame.mixer.")
        except pygame.error as e:
            print(f"Ошибка загрузки звукового файла '{self.sound_file_path}' в pygame.mixer: {e}")
            self.sound = None
            print("Внимание: Звуковой файл не был загружен. Воспроизведение звука будет невозможно.")

    def _create_control_button(self, text, x, y, width, height):
        """Создает структуру данных для кнопки управления."""
        return {
            'rect': pygame.Rect(x, y, width, height),
            'text': text,
            'last_pressed_time': 0
        }

    def _play_sound_global_callback(self, key_char):
        """
        Функция, вызываемая глобальными горячими клавишами.
        Воспроизводит звук, имитирует нажатие клавиши и обновляет анимацию, если окно Pygame активно.
        Добавлена логика "антидребезга" для предотвращения двойных срабатываний.
        """
        current_time = pygame.time.get_ticks()
        if current_time - self.last_hotkey_trigger_time < HOTKEY_DEBOUNCE_INTERVAL_MS:
            return

        self.last_hotkey_trigger_time = current_time

        if self.sound:
            self.sound.play()
        else:
            print(f"Ошибка: Звуковой файл не загружен. Невозможно воспроизвести '{key_char}' (через горячую клавишу).")

        if self.pygame_window_hwnd and win32gui.GetForegroundWindow() == self.pygame_window_hwnd:
            for button in self.layers_data[self.current_layer_index]:
                if button['text'].lower() == key_char.lower():
                    button['last_pressed_time'] = pygame.time.get_ticks()
                    break

    def _register_all_assigned_hotkeys(self):
        """
        Отключает все существующие горячие клавиши и регистрирует все горячие клавиши для всех назначенных кнопок
        во всех слоях. Это обеспечивает глобальную функциональность горячих клавиш независимо от активного слоя.
        """
        keyboard.unhook_all()
        self.global_hotkey_map = {}
        print("Все предыдущие горячие клавиши отключены.")

        for layer_idx, layer_buttons in enumerate(self.layers_data):
            for button in layer_buttons:
                key_char = button['text']  # Используем без .lower() для корректной регистрации символов
                if key_char:
                    try:
                        hotkey_obj = keyboard.add_hotkey(key_char,
                                                         lambda kc=key_char: self._play_sound_global_callback(kc))
                        self.global_hotkey_map[key_char] = hotkey_obj
                    except Exception as e:
                        print(f"Ошибка при регистрации горячей клавиши '{key_char}' на слое {layer_idx + 1}: {e}")

    def is_config_blank(self):
        """Проверяет, является ли вся конфигурация пустой (нет назначенных клавиш)."""
        for layer in self.layers_data:
            for button in layer:
                if button['text'] != '':
                    return False
        return True

    def _is_key_already_assigned(self, key_name_to_check):
        """Проверяет, назначена ли уже клавиша на любую другую кнопку на любом слое."""
        for layer in self.layers_data:
            for button in layer:
                # Если мы проверяем кнопку, которую сейчас настраиваем, пропускаем ее.
                # Сравниваем по `is`, чтобы убедиться, что это тот же самый объект в памяти,
                # а не просто кнопка с такими же координатами на другом слое.
                if self.button_to_configure is button:
                    continue
                if button['text'].lower() == key_name_to_check.lower():
                    return True
        return False

    def _read_available_configs(self):
        """Читает имена всех доступных файлов конфигурации из папки 'configs', исключая внутренний дефолт."""
        config_names = []
        config_folder = get_config_folder_path()
        if os.path.exists(config_folder):
            for filename in os.listdir(config_folder):
                if filename.endswith(".json"):
                    config_name = os.path.splitext(filename)[0]
                    if config_name != INTERNAL_DEFAULT_CONFIG_NAME:  # Исключаем внутренний дефолт
                        config_names.append(config_name)
        return sorted(config_names)

    def _get_next_preset_name(self, base_name="Preset"):
        """
        Генерирует следующее доступное имя пресета, добавляя (N) при необходимости.
        Например: "Preset", "Preset (1)", "Preset (2)".
        """
        config_names = self._read_available_configs()

        # New logic to handle names like "Preset (5)" -> "Preset (6)"
        match = re.match(r'^(.*?) \((\d+)\)$', base_name)
        if match:
            prefix = match.group(1)
            num = int(match.group(2))
            i = num + 1
            while True:
                new_name = f"{prefix} ({i})"
                if new_name not in config_names:
                    return new_name
                i += 1

        # Original logic for base names like "Preset"
        if base_name not in config_names:
            return base_name

        i = 1
        while True:
            new_name = f"{base_name} ({i})"
            if new_name not in config_names:
                return new_name
            i += 1

    def _load_config(self, config_name):
        """
        Загружает конфигурацию (слои и громкость) из файла или возвращает конфигурацию по умолчанию.
        Создает файл внутреннего дефолта, если он отсутствует.
        """
        print(f"[DEBUG] Попытка загрузить конфигурацию: '{config_name}.json'")  # Отладочное сообщение
        config_path = get_config_file_path(config_name)

        # Создаем пустую конфигурацию для нового слоя
        empty_layer_data_json_compatible = self._create_initial_default_layer_data()  # Получаем JSON-совместимые данные

        # Инициализируем default_config для внутреннего дефолта с JSON-совместимыми данными
        default_config_data = {
            'layers': [empty_layer_data_json_compatible for _ in range(max(3, len(LAYER_COLORS_FOR_BUTTONS)))],
            'volume': 1.0,
        }

        if not os.path.exists(config_path) and config_name == INTERNAL_DEFAULT_CONFIG_NAME:
            # Если internal_default не существует, создаем его как пустой
            try:
                os.makedirs(self.config_folder_path, exist_ok=True)
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config_data, f, indent=4)
                print(
                    f"[DEBUG] Создан внутренний файл конфигурации по умолчанию: '{INTERNAL_DEFAULT_CONFIG_NAME}.json'.")  # Отладочное сообщение
            except IOError as e:
                print(
                    f"[DEBUG] Ошибка при создании внутреннего файла конфигурации по умолчанию: {e}")  # Отладочное сообщение
                # Если не удалось создать, все равно используем пустые данные

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config_raw = json.load(f)

                if 'layers' not in loaded_config_raw or not isinstance(loaded_config_raw['layers'], list):
                    print(
                        f"[DEBUG] Предупреждение: Неверный формат 'layers' в файле конфигурации '{config_name}'. Используется конфигурация слоев по умолчанию.")  # Отладочное сообщение
                    self.layers_data = [list(layer) for layer in default_config_data['layers']]
                else:
                    self.layers_data = []
                    for layer_raw in loaded_config_raw['layers']:
                        current_layer_buttons = []
                        for item_raw in layer_raw:
                            item_rect_data = item_raw.get('rect', [0, 0, self.BUTTON_WIDTH, self.BUTTON_HEIGHT])
                            # Создаем pygame.Rect из списка при загрузке
                            if isinstance(item_rect_data, (list, tuple)) and len(item_rect_data) == 4:
                                rect_obj = pygame.Rect(item_rect_data)
                            else:
                                rect_obj = pygame.Rect(0, 0, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)  # Fallback

                            current_layer_buttons.append({
                                'key': item_raw.get('key', ''),
                                'rect': rect_obj,  # Теперь это объект Rect
                                'text': item_raw.get('text', ''),
                                'last_pressed_time': 0
                            })
                        self.layers_data.append(current_layer_buttons)

                initial_num_layers = max(3, len(LAYER_COLORS_FOR_BUTTONS))
                while len(self.layers_data) < initial_num_layers:
                    self.layers_data.append([list(item) for item in self._create_initial_default_layer_data()])

                if 'volume' in loaded_config_raw and isinstance(loaded_config_raw['volume'], (int, float)):
                    self.volume = max(0.0, min(1.0, loaded_config_raw['volume']))
                else:
                    print(
                        f"[DEBUG] Предупреждение: Неверное значение 'volume' в файле конфигурации '{config_name}'. Используется громкость по умолчанию.")  # Отладочное сообщение
                    self.volume = 1.0

                self.unsaved_changes = False
                print(
                    f"[DEBUG] Конфигурация '{config_name}.json' успешно загружена. Активная конфигурация: {config_name}")  # Отладочное сообщение
                self.current_active_config_name = config_name

                return loaded_config_raw
            except (IOError, json.JSONDecodeError) as e:
                print(
                    f"[DEBUG] Ошибка чтения файла конфигурации '{config_name}': {e}. Загружена конфигурация по умолчанию.")  # Отладочное сообщение
                self.unsaved_changes = False
                self.layers_data = [list(layer) for layer in default_config_data['layers']]
                self.volume = default_config_data['volume']
                self.current_active_config_name = INTERNAL_DEFAULT_CONFIG_NAME
                return default_config_data

        self.unsaved_changes = False
        print(
            f"[DEBUG] Файл конфигурации '{config_name}.json' не найден. Загружена конфигурация по умолчанию. Активная конфигурация: {self.current_active_config_name}")  # Отладочное сообщение
        self.layers_data = [list(layer) for layer in default_config_data['layers']]
        self.volume = default_config_data['volume']
        self.current_active_config_name = INTERNAL_DEFAULT_CONFIG_NAME
        return default_config_data

    def _sanitize_filename(self, filename):
        """
        Очищает строку, чтобы она была безопасна для использования в качестве имени файла.
        Удаляет символы, которые являются недопустимыми в большинстве файловых систем.
        Сохраняет остальные печатные символы.
        """
        # Символы, которые критически запрещены в именах файлов Windows (Python's os.path.basename on Windows)
        # Linux более снисходителен, но для кроссплатформенной совместимости лучше придерживаться Windows-безопасных правил.
        forbidden_filename_chars_os = r'/\:*?"<>|'  # Эти символы не могут быть в именах файлов в Windows

        sanitized_filename = ""
        for char in filename:
            # Оставляем любой печатный символ, который НЕ находится в списке запрещенных ОС
            if char.isprintable() and char not in forbidden_filename_chars_os:
                sanitized_filename += char
        return sanitized_filename.strip()

    def _save_config(self, config_name, overwrite=False):
        """Сохраняет текущую конфигурацию (слои и громкость) в файл с заданным именем."""
        if not config_name:
            print("Ошибка сохранения: Имя конфигурации не может быть пустым.")
            return False

        # Санитизируем имя файла, чтобы оно было безопасно для файловой системы
        sanitized_config_name = self._sanitize_filename(config_name)

        if not sanitized_config_name:
            print(
                f"Ошибка сохранения: Имя конфигурации '{config_name}' после очистки стало пустым или содержит только недопустимые символы. Попробуйте другое имя.")
            return False

        # Используем санитизированное имя для файла
        config_path = get_config_file_path(sanitized_config_name)

        # Проверка на существование файла.
        # Если файл с таким санитизированным именем уже существует и мы не указали перезапись, то запрашиваем подтверждение.
        if os.path.exists(config_path) and not overwrite:
            print(f"Файл '{sanitized_config_name}.json' уже существует. Запросите перезапись.")
            return False

        save_data_layers = []
        for layer in self.layers_data:
            layer_data = []
            for item in layer:
                # Преобразуем pygame.Rect в список [x, y, w, h] для сохранения
                rect_representation = list(item['rect']) if isinstance(item['rect'], pygame.Rect) else item['rect']
                layer_data.append({
                    'key': item['text'],
                    'rect': rect_representation,
                    'text': item['text']
                })
            save_data_layers.append(layer_data)

        full_config_to_save = {
            'layers': save_data_layers,
            'volume': self.volume,
        }

        try:
            os.makedirs(self.config_folder_path, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(full_config_to_save, f, indent=4)
            print(f"Конфигурация '{sanitized_config_name}.json' успешно сохранена.")
            self.unsaved_changes = False
            self.current_active_config_name = sanitized_config_name  # Устанавливаем санитизированное имя как активное
            return True
        except IOError as e:
            print(f"Ошибка при записи файла конфигурации '{sanitized_config_name}.json': {e}")
            return False

    def _reset_current_layer_assignments(self):
        """Сбрасывает все назначения клавиш для кнопок в текущем слое."""
        for button in self.layers_data[self.current_layer_index]:
            button['text'] = ''
        self._register_all_assigned_hotkeys()

        # Если после сброса слоя вся конфигурация стала пустой,
        # то считать, что несохраненных изменений нет.
        if self.is_config_blank():
            self.unsaved_changes = False
        else:
            self.unsaved_changes = True

        print(f"Назначения клавиш для слоя {self.current_layer_index + 1} сброшены.")
        # Обновляем кэш для измененных кнопок
        self._cache_all_button_surfaces()

    def _create_button_surface(self, rect, base_color, border_radius, border_color, border_thickness,
                               text_content, original_font_object, text_color, is_pressed=False):
        """
        Создает и возвращает поверхность (Surface) для кнопки с заданными параметрами.
        """
        draw_color = list(base_color)

        if is_pressed:
            # Затемняем цвет для эффекта нажатия
            draw_color = [int(c * 0.7) for c in draw_color]
            draw_color = tuple(draw_color)

        # Отрисовка основной кнопки
        scale = 4  # Уменьшенный масштаб для производительности
        temp_surface_size = (rect.width * scale, rect.height * scale)
        temp_surface = pygame.Surface(temp_surface_size, pygame.SRCALPHA)

        scaled_border_radius = border_radius * scale
        scaled_border_thickness = border_thickness * scale

        # Внешний прямоугольник (цвет рамки)
        pygame.draw.rect(temp_surface, border_color, (0, 0, temp_surface_size[0], temp_surface_size[1]),
                         border_radius=int(scaled_border_radius))

        # Внутренний прямоугольник (цвет заливки)
        inner_rect_scaled = pygame.Rect(scaled_border_thickness, scaled_border_thickness,
                                        temp_surface_size[0] - 2 * scaled_border_thickness,
                                        temp_surface_size[1] - 2 * scaled_border_thickness)
        pygame.draw.rect(temp_surface, draw_color, inner_rect_scaled,
                         border_radius=int(scaled_border_radius - scaled_border_thickness))

        # Масштабируем и выводим на основной экран
        final_button_surface = pygame.transform.smoothscale(temp_surface, rect.size)

        # Отрисовка текста
        if text_content:
            font_to_use = original_font_object
            if len(text_content) > 3:
                if original_font_object.get_bold():
                    font_to_use = self.font_small_bold
                else:
                    font_to_use = self.font_small

            text_surface = font_to_use.render(text_content, True, text_color)
            text_rect = text_surface.get_rect(center=final_button_surface.get_rect().center)
            final_button_surface.blit(text_surface, text_rect)
        elif not text_content and base_color == self.ORANGE and self.unassigned_key_frames:
            current_frame = self.unassigned_key_frames[self.current_frame_index % len(self.unassigned_key_frames)]
            image_rect = current_frame.get_rect(center=final_button_surface.get_rect().center)
            final_button_surface.blit(current_frame, image_rect)

        return final_button_surface

    def _cache_all_button_surfaces(self):
        """
        Предварительно рендерит и кэширует поверхности для всех кнопок во всех состояниях.
        """
        for layer in self.layers_data:
            for button in layer:
                self._update_cached_surfaces_for_button(button)
        # Кэшируем также и для контрольных кнопок
        for btn_data in [self.save_button_data, self.load_button_data, self.config_button_data, self.reset_button_data]:
            btn_data['surface_normal'] = self._create_button_surface(
                btn_data['rect'], self.LIGHT_GRAY, 25, BORDER_COLOR, 2, btn_data['text'], self.font_small, self.BLACK)
            btn_data['surface_pressed'] = self._create_button_surface(
                btn_data['rect'], self.LIGHT_GRAY, 25, BORDER_COLOR, 2, btn_data['text'], self.font_small, self.BLACK,
                is_pressed=True)

    def _update_cached_surfaces_for_button(self, button):
        """Обновляет кэшированные поверхности для одной конкретной кнопки."""
        button['surface_normal'] = self._create_button_surface(
            button['rect'], self.ORANGE, 25, BORDER_COLOR, 2, button['text'], self.font_bold, self.BLACK)
        button['surface_pressed'] = self._create_button_surface(
            button['rect'], self.ORANGE, 25, BORDER_COLOR, 2, button['text'], self.font_bold, self.BLACK,
            is_pressed=True)

    def _draw_buttons(self):
        """Рисует основные кнопки саундпада, используя кэшированные поверхности."""
        current_time = pygame.time.get_ticks()
        current_button_backlight_color = LAYER_COLORS_FOR_BUTTONS[self.current_layer_index]

        # Обновляем поверхности для анимированных черепов, если необходимо
        if self.needs_unassigned_redraw:
            for button in self.layers_data[self.current_layer_index]:
                if not button['text']:  # Обновляем только неназначенные кнопки
                    self._update_cached_surfaces_for_button(button)
            self.needs_unassigned_redraw = False

        for button in self.layers_data[self.current_layer_index]:
            # Рисуем подсветку (это быстрая операция)
            backlight_padding = 4
            backlight_rect = button['rect'].inflate(backlight_padding * 2, backlight_padding * 2)
            pygame.draw.rect(self.screen, current_button_backlight_color, backlight_rect,
                             border_radius=25 + backlight_padding)

            is_configuring_this_button = (self.program_state == 'configuring' and self.button_to_configure is button)
            is_pressed = (0 < current_time - button['last_pressed_time'] < ANIMATION_DURATION_MS)

            if is_configuring_this_button:
                surface_to_draw = button['surface_pressed']
            else:
                surface_to_draw = button['surface_pressed'] if is_pressed else button['surface_normal']

            self.screen.blit(surface_to_draw, button['rect'].topleft)

    def _draw_control_buttons(self):
        """Рисует кнопки управления, используя кэшированные поверхности."""
        current_time = pygame.time.get_ticks()
        for btn_data in [self.save_button_data, self.load_button_data, self.config_button_data, self.reset_button_data]:
            is_pressed = (0 < current_time - btn_data['last_pressed_time'] < ANIMATION_DURATION_MS)
            surface_to_draw = btn_data['surface_pressed'] if is_pressed else btn_data['surface_normal']
            self.screen.blit(surface_to_draw, btn_data['rect'].topleft)

    def _draw_right_rectangle(self):
        """Рисует прямоугольник справа от сетки кнопок с двумя границами."""
        outer_border_thickness = 2
        inner_border_thickness = 2

        pygame.draw.rect(self.screen, self.ORANGE, self.right_rectangle_rect, width=outer_border_thickness,
                         border_radius=10)

        black_border_rect = pygame.Rect(
            self.right_rectangle_rect.x + outer_border_thickness,
            self.right_rectangle_rect.y + outer_border_thickness,
            self.right_rectangle_rect.width - (2 * outer_border_thickness),
            self.right_rectangle_rect.height - (2 * outer_border_thickness)
        )
        pygame.draw.rect(self.screen, self.BLACK, black_border_rect, width=inner_border_thickness, border_radius=8)

        orange_fill_rect = pygame.Rect(
            black_border_rect.x + inner_border_thickness,
            black_border_rect.y + inner_border_thickness,
            black_border_rect.width - (2 * inner_border_thickness),
            black_border_rect.height - (2 * inner_border_thickness)
        )
        pygame.draw.rect(self.screen, self.ORANGE, orange_fill_rect, border_radius=6)

    def _draw_unsaved_changes_prompt(self):
        """Рисует запрос о несохраненных изменениях в зависимости от контекста (выход или загрузка)."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(TRANSPARENT_BLACK)
        self.screen.blit(overlay, (0, 0))

        prompt_width = 450
        prompt_height = 200
        prompt_x = (SCREEN_WIDTH - prompt_width) // 2
        prompt_y = (SCREEN_HEIGHT - prompt_height) // 2
        prompt_rect = pygame.Rect(prompt_x, prompt_y, prompt_width, prompt_height)

        self.screen.blit(
            self._create_button_surface(prompt_rect, DARK_GRAY, 20, BORDER_COLOR, 2, "", self.font_message, self.WHITE),
            prompt_rect.topleft)

        message_line1_text = "Есть несохраненные изменения."
        message_line2_text = "Сохранить?"
        message_line1_surface = self.font_message.render(message_line1_text, True, self.WHITE)
        message_line2_surface = self.font_message.render(message_line2_text, True, self.WHITE)
        message_line1_rect = message_line1_surface.get_rect(center=(prompt_rect.centerx, prompt_rect.y + 60))
        message_line2_rect = message_line2_surface.get_rect(center=(prompt_rect.centerx, prompt_rect.y + 95))
        self.screen.blit(message_line1_surface, message_line1_rect)
        self.screen.blit(message_line2_surface, message_line2_rect)

        button_width = 120
        button_height = 40
        button_spacing = 20
        total_buttons_width = (3 * button_width) + (2 * button_spacing)
        start_x = prompt_x + (prompt_width - total_buttons_width) // 2
        button_y = prompt_y + 130

        if self.prompt_context == 'exit':
            save_button_rect = pygame.Rect(start_x, button_y, button_width, button_height)
            back_button_rect = pygame.Rect(start_x + button_width + button_spacing, button_y, button_width,
                                           button_height)
            exit_button_rect = pygame.Rect(start_x + 2 * (button_width + button_spacing), button_y, button_width,
                                           button_height)

            self.screen.blit(
                self._create_button_surface(save_button_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Сохранить",
                                            self.font_small, self.BLACK), save_button_rect.topleft)
            self.screen.blit(self._create_button_surface(back_button_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Назад",
                                                         self.font_small, self.BLACK), back_button_rect.topleft)
            self.screen.blit(self._create_button_surface(exit_button_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Выход",
                                                         self.font_small, self.BLACK), exit_button_rect.topleft)

        elif self.prompt_context == 'load':
            save_button_rect = pygame.Rect(start_x, button_y, button_width, button_height)
            dont_save_button_rect = pygame.Rect(start_x + button_width + button_spacing, button_y, button_width,
                                                button_height)
            back_button_rect = pygame.Rect(start_x + 2 * (button_width + button_spacing), button_y, button_width,
                                           button_height)

            self.screen.blit(
                self._create_button_surface(save_button_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Сохранить",
                                            self.font_small, self.BLACK), save_button_rect.topleft)
            self.screen.blit(
                self._create_button_surface(dont_save_button_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Не сохранять",
                                            self.font_small, self.BLACK), dont_save_button_rect.topleft)
            self.screen.blit(self._create_button_surface(back_button_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Назад",
                                                         self.font_small, self.BLACK), back_button_rect.topleft)

    def _draw_update_prompt(self):
        """Рисует окно с предложением обновиться."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(TRANSPARENT_BLACK)
        self.screen.blit(overlay, (0, 0))

        prompt_width = 450
        prompt_height = 200
        prompt_x = (SCREEN_WIDTH - prompt_width) // 2
        prompt_y = (SCREEN_HEIGHT - prompt_height) // 2
        prompt_rect = pygame.Rect(prompt_x, prompt_y, prompt_width, prompt_height)

        self.screen.blit(
            self._create_button_surface(prompt_rect, DARK_GRAY, 20, BORDER_COLOR, 2, "", self.font_message, self.WHITE),
            prompt_rect.topleft)

        line1_text = f"Доступна новая версия: {self.update_info['latest_version']}"
        line2_text = "Хотите скачать?"

        line1_surface = self.font_message.render(line1_text, True, self.WHITE)
        line2_surface = self.font_message.render(line2_text, True, self.WHITE)

        line1_rect = line1_surface.get_rect(center=(prompt_rect.centerx, prompt_rect.y + 60))
        line2_rect = line2_surface.get_rect(center=(prompt_rect.centerx, prompt_rect.y + 95))

        self.screen.blit(line1_surface, line1_rect)
        self.screen.blit(line2_surface, line2_rect)

        button_width = 120
        button_height = 40
        button_spacing = 20
        total_buttons_width = 2 * button_width + button_spacing
        start_x = prompt_x + (prompt_width - total_buttons_width) // 2
        button_y = prompt_y + 130

        self.update_prompt_yes_rect = pygame.Rect(start_x, button_y, button_width, button_height)
        self.update_prompt_no_rect = pygame.Rect(start_x + button_width + button_spacing, button_y, button_width,
                                                 button_height)

        self.screen.blit(
            self._create_button_surface(self.update_prompt_yes_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Да",
                                        self.font_small, self.BLACK),
            self.update_prompt_yes_rect.topleft)
        self.screen.blit(
            self._create_button_surface(self.update_prompt_no_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Нет",
                                        self.font_small, self.BLACK),
            self.update_prompt_no_rect.topleft)

    def _prepare_save_dropdown_buttons(self):
        """Подготавливает Rect'ы для выпадающего списка пресетов в окне сохранения."""
        self.save_dropdown_rects = []
        config_names = self._read_available_configs()

        if not self.input_box_rect:
            return

        list_area_y = self.input_box_rect.bottom + 2
        button_height = 35
        button_spacing = 2

        max_visible_items = 4

        start_index = self.save_dropdown_scroll_offset
        end_index = min(start_index + max_visible_items, len(config_names))

        for i in range(start_index, end_index):
            config_name = config_names[i]
            y_pos = list_area_y + (i - start_index) * (button_height + button_spacing)
            config_button_rect = pygame.Rect(
                self.input_box_rect.x,
                y_pos,
                self.input_box_rect.width,
                button_height
            )
            self.save_dropdown_rects.append({'name': config_name, 'rect': config_button_rect})

    def _draw_config_name_prompt(self):
        """Рисует всплывающее окно для ввода имени конфигурации."""
        # 1. Draw the background overlay first
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(TRANSPARENT_BLACK)
        self.screen.blit(overlay, (0, 0))

        # 2. Draw the main prompt window on top of the overlay
        prompt_width = 450
        prompt_height = 200
        prompt_x = (SCREEN_WIDTH - prompt_width) // 2
        prompt_y = (SCREEN_HEIGHT - prompt_height) // 2
        self.input_box_rect = pygame.Rect(prompt_x + 50, prompt_y + 90, prompt_width - 100, 40)

        prompt_rect = pygame.Rect(prompt_x, prompt_y, prompt_width, prompt_height)
        self.screen.blit(
            self._create_button_surface(prompt_rect, DARK_GRAY, 20, BORDER_COLOR, 2, "", self.font_message, self.WHITE),
            prompt_rect.topleft)

        message_surface = self.font_message.render(self.input_prompt_message, True, self.WHITE)
        message_rect = message_surface.get_rect(center=(prompt_x + prompt_width // 2, prompt_y + 50))
        self.screen.blit(message_surface, message_rect)

        pygame.draw.rect(self.screen, self.WHITE, self.input_box_rect, border_radius=5)
        pygame.draw.rect(self.screen, self.BLACK, self.input_box_rect, 2, border_radius=5)

        text_surface = self.font_small.render(self.current_input_text, True, self.BLACK)
        self.screen.blit(text_surface, (self.input_box_rect.x + 5, self.input_box_rect.y + 10))

        arrow_size = 10
        arrow_padding = 10
        self.dropdown_arrow_rect = pygame.Rect(
            self.input_box_rect.right - arrow_size - arrow_padding,
            self.input_box_rect.centery - arrow_size // 2,
            arrow_size,
            arrow_size
        )
        pygame.draw.polygon(self.screen, BLACK, [
            (self.dropdown_arrow_rect.left, self.dropdown_arrow_rect.top),
            (self.dropdown_arrow_rect.right, self.dropdown_arrow_rect.top),
            (self.dropdown_arrow_rect.centerx, self.dropdown_arrow_rect.bottom)
        ])

        if self.cursor_visible:
            cursor_x = self.input_box_rect.x + 5 + text_surface.get_width()
            if cursor_x < self.dropdown_arrow_rect.left - 5:
                cursor_y_start = self.input_box_rect.y + 10
                cursor_y_end = self.input_box_rect.y + self.input_box_rect.height - 10
                pygame.draw.line(self.screen, self.BLACK, (cursor_x, cursor_y_start), (cursor_x, cursor_y_end), 2)

        save_button_rect = pygame.Rect(prompt_x + 80, prompt_y + 140, 120, 40)
        cancel_button_rect = pygame.Rect(prompt_x + prompt_width - 80 - 120, prompt_y + 140, 120, 40)
        self.screen.blit(self._create_button_surface(save_button_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Сохранить",
                                                     self.font_small, self.BLACK), save_button_rect.topleft)
        self.screen.blit(self._create_button_surface(cancel_button_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Назад",
                                                     self.font_small, self.BLACK), cancel_button_rect.topleft)

        # 3. Draw the animated dropdown on top of everything
        if self.dropdown_anim_progress > 0:
            self._prepare_save_dropdown_buttons()
            if self.save_dropdown_rects:
                first_rect = self.save_dropdown_rects[0]['rect']
                last_rect = self.save_dropdown_rects[-1]['rect']

                # The surface for the dropdown content needs to be larger to include the scrollbar
                scrollbar_width = 15
                dropdown_content_width = first_rect.width
                full_dropdown_width = dropdown_content_width

                full_height = last_rect.bottom - first_rect.top

                dropdown_surf = pygame.Surface((full_dropdown_width, full_height), pygame.SRCALPHA)

                # Draw main background for the list
                list_bg_rect = pygame.Rect(0, 0, dropdown_content_width, full_height)
                pygame.draw.rect(dropdown_surf, DARK_GRAY, list_bg_rect, border_radius=8)
                pygame.draw.rect(dropdown_surf, BORDER_COLOR, list_bg_rect, 2, border_radius=8)

                # Draw items onto the temp surface
                for item in self.save_dropdown_rects:
                    relative_rect = item['rect'].copy()
                    relative_rect.top -= first_rect.top
                    relative_rect.left -= first_rect.left

                    pygame.draw.rect(dropdown_surf, LIGHT_GRAY, relative_rect.inflate(-4, -4), border_radius=5)
                    text_surf = self.font_small.render(item['name'], True, BLACK)
                    text_rect = text_surf.get_rect(midleft=(relative_rect.left + 10, relative_rect.centery))
                    dropdown_surf.blit(text_surf, text_rect)

                current_height = int(full_height * self.dropdown_anim_progress)
                if current_height > 0:
                    clip_rect = pygame.Rect(0, 0, full_dropdown_width, current_height)

                    # Scrollbar for save dropdown
                    config_names_count = len(self._read_available_configs())
                    max_visible_items = 4
                    if config_names_count > max_visible_items:
                        self.save_scrollbar_rect = pygame.Rect(
                            self.input_box_rect.right + 4,
                            self.input_box_rect.bottom + 2,
                            scrollbar_width,
                            current_height
                        )
                        pygame.draw.rect(self.screen, (50, 50, 50), self.save_scrollbar_rect)

                        handle_height = max(20,
                                            self.save_scrollbar_rect.height * (max_visible_items / config_names_count))
                        scrollable_items = config_names_count - max_visible_items
                        scroll_progress = self.save_dropdown_scroll_offset / scrollable_items if scrollable_items > 0 else 0
                        handle_y_pos = self.save_scrollbar_rect.top + (
                                self.save_scrollbar_rect.height - handle_height) * scroll_progress

                        self.save_scrollbar_handle_rect = pygame.Rect(
                            self.save_scrollbar_rect.left, handle_y_pos,
                            scrollbar_width, handle_height
                        )
                        pygame.draw.rect(self.screen, LIGHT_GRAY, self.save_scrollbar_handle_rect)
                    else:
                        self.save_scrollbar_rect = None
                        self.save_scrollbar_handle_rect = None

                    dropdown_surf.set_alpha(int(255 * self.dropdown_anim_progress))
                    self.screen.blit(dropdown_surf, (first_rect.x, first_rect.y), area=clip_rect)

    def _draw_overwrite_prompt(self):
        """Рисует всплывающее окно для запроса перезаписи существующего файла."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(TRANSPARENT_BLACK)
        self.screen.blit(overlay, (0, 0))

        prompt_width = 500
        prompt_height = 200
        prompt_x = (SCREEN_WIDTH - prompt_width) // 2
        prompt_y = (SCREEN_HEIGHT - prompt_height) // 2
        prompt_rect = pygame.Rect(prompt_x, prompt_y, prompt_width, prompt_height)

        self.screen.blit(
            self._create_button_surface(prompt_rect, DARK_GRAY, 20, BORDER_COLOR, 2, "", self.font_message, self.WHITE),
            prompt_rect.topleft)

        message_line1_text = f"Файл '{self.pending_overwrite_config_name}' уже существует."
        message_line2_text = "Перезаписать?"

        message_line1_surface = self.font_message.render(message_line1_text, True, self.WHITE)
        message_line2_surface = self.font_message.render(message_line2_text, True, self.WHITE)

        message_line1_rect = message_line1_surface.get_rect(
            center=(prompt_rect.centerx, prompt_rect.y + 60))
        message_line2_rect = message_line2_surface.get_rect(
            center=(prompt_rect.centerx, prompt_rect.y + 95))

        self.screen.blit(message_line1_surface, message_line1_rect)
        self.screen.blit(message_line2_surface, message_line2_rect)

        button_width = 130
        button_height = 40
        button_spacing = 20
        total_buttons_width = 2 * button_width + button_spacing
        start_x_buttons = prompt_x + (prompt_width - total_buttons_width) // 2

        overwrite_button_rect = pygame.Rect(start_x_buttons, prompt_y + 140, button_width, button_height)
        rename_button_rect = pygame.Rect(start_x_buttons + button_width + button_spacing, prompt_y + 140, button_width,
                                         button_height)

        self.screen.blit(
            self._create_button_surface(overwrite_button_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Перезаписать",
                                        self.font_small, self.BLACK), overwrite_button_rect.topleft)
        self.screen.blit(
            self._create_button_surface(rename_button_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Переименовать",
                                        self.font_small, self.BLACK), rename_button_rect.topleft)

    def _draw_confirm_delete_prompt(self):
        """Рисует всплывающее окно для подтверждения удаления пресета."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(TRANSPARENT_BLACK)
        self.screen.blit(overlay, (0, 0))

        prompt_width = 450
        prompt_height = 200
        prompt_x = (SCREEN_WIDTH - prompt_width) // 2
        prompt_y = (SCREEN_HEIGHT - prompt_height) // 2
        prompt_rect = pygame.Rect(prompt_x, prompt_y, prompt_width, prompt_height)

        # Фон
        self.screen.blit(
            self._create_button_surface(prompt_rect, DARK_GRAY, 20, BORDER_COLOR, 2, "", self.font_message, self.WHITE),
            prompt_rect.topleft)

        # Текст
        message_text = f"Удалить пресет '{self.config_to_delete}'?"
        message_surface = self.font_message.render(message_text, True, self.WHITE)
        message_rect = message_surface.get_rect(center=(prompt_rect.centerx, prompt_rect.y + 80))
        self.screen.blit(message_surface, message_rect)

        # Кнопки
        button_width = 120
        button_height = 40
        button_spacing = 20
        total_buttons_width = 2 * button_width + button_spacing
        start_x = prompt_x + (prompt_width - total_buttons_width) // 2
        button_y = prompt_y + 130

        self.confirm_delete_yes_rect = pygame.Rect(start_x, button_y, button_width, button_height)
        self.confirm_delete_no_rect = pygame.Rect(start_x + button_width + button_spacing, button_y, button_width,
                                                  button_height)

        self.screen.blit(
            self._create_button_surface(self.confirm_delete_yes_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Да",
                                        self.font_small, self.BLACK),
            self.confirm_delete_yes_rect.topleft)
        self.screen.blit(
            self._create_button_surface(self.confirm_delete_no_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Нет",
                                        self.font_small, self.BLACK),
            self.confirm_delete_no_rect.topleft)

    def _prepare_load_config_buttons(self):
        """
        Подготавливает список Rect-ов для кнопок загрузки конфигураций.
        Этот метод вызывается при входе в режим 'load_config_list'.
        """
        self.load_config_buttons_rects = []
        config_names = self._read_available_configs()

        prompt_width = 450
        prompt_height = 400
        prompt_x = (SCREEN_WIDTH - prompt_width) // 2
        prompt_y = (SCREEN_HEIGHT - prompt_height) // 2
        list_area_rect = pygame.Rect(prompt_x + 30, prompt_y + 70, prompt_width - 60, prompt_height - 150)

        button_height = 35
        button_spacing = 5

        max_visible_items = (list_area_rect.height - button_spacing) // (button_height + button_spacing)
        if max_visible_items <= 0:
            max_visible_items = 1

        start_index = self.scroll_offset_load_configs
        end_index = min(start_index + max_visible_items, len(config_names))

        for i in range(start_index, end_index):
            config_name = config_names[i]
            y_pos = list_area_rect.y + button_spacing + (i - start_index) * (button_height + button_spacing)
            config_button_rect = pygame.Rect(
                list_area_rect.x + button_spacing,
                y_pos,
                list_area_rect.width - 2 * button_spacing,
                button_height
            )

            # Добавляем rect'ы для круглых кнопок
            circle_radius = 8
            circle_diameter = circle_radius * 2
            spacing_from_edge = 15
            spacing_between_circles = 5

            # Кнопка удаления (справа)
            delete_button_rect = pygame.Rect(
                config_button_rect.right - spacing_from_edge - circle_diameter,
                config_button_rect.centery - circle_radius,
                circle_diameter,
                circle_diameter
            )
            # Кнопка редактирования (слева от кнопки удаления)
            edit_button_rect = pygame.Rect(
                delete_button_rect.left - spacing_between_circles - circle_diameter,
                config_button_rect.centery - circle_radius,
                circle_diameter,
                circle_diameter
            )

            self.load_config_buttons_rects.append({
                'name': config_name,
                'rect': config_button_rect,
                'delete_rect': delete_button_rect,
                'edit_rect': edit_button_rect
            })
        print(f"[DEBUG] Кнопки загрузки конфигураций подготовлены: {len(self.load_config_buttons_rects)} кнопок.")

    def _draw_load_config_list(self):
        """Рисует всплывающее окно со списком доступных конфигураций для загрузки."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(TRANSPARENT_BLACK)
        self.screen.blit(overlay, (0, 0))

        prompt_width = 450
        prompt_height = 400
        prompt_x = (SCREEN_WIDTH - prompt_width) // 2
        prompt_y = (SCREEN_HEIGHT - prompt_height) // 2
        prompt_rect = pygame.Rect(prompt_x, prompt_y, prompt_width, prompt_height)

        self.screen.blit(
            self._create_button_surface(prompt_rect, DARK_GRAY, 20, BORDER_COLOR, 2, "", self.font_message, self.WHITE),
            prompt_rect.topleft)

        title_surface = self.font_message.render("Выберите конфигурацию для загрузки:", True, self.WHITE)
        title_rect = title_surface.get_rect(center=(prompt_rect.centerx, prompt_rect.y + 30))
        self.screen.blit(title_surface, title_rect)

        list_area_rect = pygame.Rect(prompt_x + 30, prompt_y + 70, prompt_width - 60, prompt_height - 150)
        pygame.draw.rect(self.screen, SLIGHTLY_DARKER_WHITE, list_area_rect, border_radius=5)
        pygame.draw.rect(self.screen, self.BLACK, list_area_rect, 2, border_radius=5)

        button_height = 35
        button_spacing = 5
        max_visible_items = (list_area_rect.height - button_spacing) // (button_height + button_spacing)
        if max_visible_items <= 0: max_visible_items = 1

        # --- New Scrollbar Drawing ---
        config_names_count = len(self._read_available_configs())
        if config_names_count > max_visible_items:
            scrollbar_width = 15
            self.load_scrollbar_rect = pygame.Rect(
                list_area_rect.right + 5,
                list_area_rect.top,
                scrollbar_width,
                list_area_rect.height
            )
            pygame.draw.rect(self.screen, DARK_GRAY, self.load_scrollbar_rect)

            handle_height = max(20, self.load_scrollbar_rect.height * (max_visible_items / config_names_count))

            scrollable_items = config_names_count - max_visible_items
            scroll_progress = self.scroll_offset_load_configs / scrollable_items if scrollable_items > 0 else 0

            handle_y_pos = self.load_scrollbar_rect.top + (
                    self.load_scrollbar_rect.height - handle_height) * scroll_progress

            self.load_scrollbar_handle_rect = pygame.Rect(
                self.load_scrollbar_rect.left,
                handle_y_pos,
                scrollbar_width,
                handle_height
            )
            pygame.draw.rect(self.screen, LIGHT_GRAY, self.load_scrollbar_handle_rect)
        else:
            self.load_scrollbar_rect = None
            self.load_scrollbar_handle_rect = None

        # Отрисовываем кнопки из уже подготовленного списка
        for config_btn_data in self.load_config_buttons_rects:
            config_name = config_btn_data['name']
            config_button_rect = config_btn_data['rect']
            delete_rect = config_btn_data['delete_rect']
            edit_rect = config_btn_data['edit_rect']

            bg_color = self.LIGHT_GRAY
            if config_name == self.last_clicked_config_name:
                bg_color = self.ORANGE

            # Рисуем фон кнопки без текста
            self.screen.blit(
                self._create_button_surface(config_button_rect, bg_color, 8, self.BLACK, 1, "", self.font_small,
                                            self.BLACK), config_button_rect.topleft)

            # Рисуем текст отдельно, с выравниванием по левому краю
            text_surface = self.font_small.render(config_name, True, self.BLACK)
            text_rect = text_surface.get_rect(midleft=(config_button_rect.left + 10, config_button_rect.centery))
            self.screen.blit(text_surface, text_rect)

            # Рисуем иконки
            if self.edit_icon_image:
                self.screen.blit(self.edit_icon_image, edit_rect.topleft)
            else:
                # Fallback
                pygame.draw.circle(self.screen, RED, edit_rect.center, edit_rect.width // 2)
                pygame.draw.circle(self.screen, BLACK, edit_rect.center, edit_rect.width // 2, 1)

            if self.trash_icon_image:
                self.screen.blit(self.trash_icon_image, delete_rect.topleft)
            else:
                # Fallback
                pygame.draw.circle(self.screen, RED, delete_rect.center, delete_rect.width // 2)
                pygame.draw.circle(self.screen, BLACK, delete_rect.center, delete_rect.width // 2, 1)

        cancel_button_rect = pygame.Rect(prompt_x + prompt_width // 2 - 60, prompt_y + prompt_height - 60, 120, 40)
        self.screen.blit(self._create_button_surface(cancel_button_rect, self.LIGHT_GRAY, 10, self.BLACK, 1, "Назад",
                                                     self.font_small, self.BLACK), cancel_button_rect.topleft)

    def _handle_mouse_click(self, pos):
        """Обрабатывает клики мыши."""
        # Блокируем другие клики, если есть активное модальное окно
        if self.program_state not in ['normal', 'configuring', 'load_config_list']:
            return

        if self.program_state == 'load_config_list':
            self._handle_load_config_list_click(pos)
            return

        # Остальная логика кликов для 'normal' и 'configuring' состояний
        if self.save_button_data['rect'].collidepoint(pos):
            self.save_button_data['last_pressed_time'] = pygame.time.get_ticks()
            if self.unsaved_changes:
                self.previous_program_state = 'normal'
                self.program_state = 'prompt_config_name'
                self.current_input_text = self._get_next_preset_name()
                self.input_prompt_message = "Введите имя для нового пресета:"
            else:
                self.program_state = 'normal'
        elif self.load_button_data['rect'].collidepoint(pos):
            self.load_button_data['last_pressed_time'] = pygame.time.get_ticks()
            if self.unsaved_changes:
                self.previous_program_state = 'normal'
                self.program_state = 'unsaved_changes_prompt'
                self.prompt_context = 'load'
            else:
                self.program_state = 'load_config_list'
                self.scroll_offset_load_configs = 0
                self._prepare_load_config_buttons()
        elif self.config_button_data['rect'].collidepoint(pos):
            self.config_button_data['last_pressed_time'] = pygame.time.get_ticks()
            self.program_state = 'configuring'
            self.button_to_configure = None
        elif self.reset_button_data['rect'].collidepoint(pos):
            self.reset_button_data['last_pressed_time'] = pygame.time.get_ticks()
            self._reset_current_layer_assignments()

        if self.layer_manager.handle_mouse_click(pos):
            return

        if self.volume_manager.handle_mouse_button_down(pos):
            self.is_dragging_volume_knob = self.volume_manager.is_dragging_volume_knob
            return

        if self.program_state == 'normal':
            for button in self.layers_data[self.current_layer_index]:
                if button['rect'].collidepoint(pos):
                    button['last_pressed_time'] = pygame.time.get_ticks()
                    if self.sound:
                        self.sound.play()
                    break
        elif self.program_state == 'configuring' and self.button_to_configure is None:
            for button in self.layers_data[self.current_layer_index]:
                if button['rect'].collidepoint(pos):
                    self.button_to_configure = button
                    button['last_pressed_time'] = 0
                    break

    def _handle_prompt_click(self, pos):
        """Обрабатывает клики мыши в состоянии 'prompt_config_name'."""
        prompt_width = 450
        prompt_height = 200
        prompt_x = (SCREEN_WIDTH - prompt_width) // 2
        prompt_y = (SCREEN_HEIGHT - prompt_height) // 2

        save_button_rect = pygame.Rect(prompt_x + 80, prompt_y + 140, 120, 40)
        cancel_button_rect = pygame.Rect(prompt_x + prompt_width - 80 - 120, prompt_y + 140, 120, 40)

        # 1. Проверяем клик по стрелке выпадающего списка
        if self.dropdown_arrow_rect and self.dropdown_arrow_rect.collidepoint(pos):
            self.save_dropdown_active = not self.save_dropdown_active
            if self.save_dropdown_active:
                self.save_dropdown_scroll_offset = 0
                self._prepare_save_dropdown_buttons()
            return

        # 2. Проверяем взаимодействие с ползунком прокрутки
        if self.save_scrollbar_handle_rect and self.save_scrollbar_handle_rect.collidepoint(pos):
            self.is_dragging_save_scrollbar = True
            self.scrollbar_drag_details = {'start_y': pos[1], 'start_offset': self.save_dropdown_scroll_offset}
            return

        if self.save_scrollbar_rect and self.save_scrollbar_rect.collidepoint(pos):
            max_visible_items = 4
            if pos[1] < self.save_scrollbar_handle_rect.top:
                self.save_dropdown_scroll_offset = max(0, self.save_dropdown_scroll_offset - max_visible_items)
            else:
                total_items = len(self._read_available_configs())
                if total_items > max_visible_items:
                    self.save_dropdown_scroll_offset = min(total_items - max_visible_items,
                                                           self.save_dropdown_scroll_offset + max_visible_items)
            self._prepare_save_dropdown_buttons()
            return

        # 3. Проверяем клики по элементам в выпадающем списке
        if self.save_dropdown_active:
            for item in self.save_dropdown_rects:
                if item['rect'].collidepoint(pos):
                    self.current_input_text = item['name']
                    self.save_dropdown_active = False
                    return

        # 4. Проверяем клики по кнопкам "Сохранить" и "Назад"
        if save_button_rect.collidepoint(pos):
            self.save_dropdown_active = False
            self._save_config_from_prompt()
            return

        if cancel_button_rect.collidepoint(pos):
            self.save_dropdown_active = False
            self.program_state = 'normal'
            self.unsaved_changes = True
            self.current_input_text = ""
            self.input_prompt_message = ""
            self.pending_action_after_prompt = None
            print("[DEBUG] Ввод имени конфигурации отменен, возврат к интерфейсу.")
            return

        # 5. Если клик был за пределами всех активных элементов, закрываем выпадающий список
        prompt_rect = pygame.Rect(prompt_x, prompt_y, prompt_width, prompt_height)
        is_click_outside = not prompt_rect.collidepoint(pos)

        dropdown_area = None
        if self.dropdown_anim_progress > 0 and self.save_dropdown_rects:
            first_rect = self.save_dropdown_rects[0]['rect']
            last_rect = self.save_dropdown_rects[-1]['rect']
            dropdown_area = pygame.Rect(first_rect.left, first_rect.top, first_rect.width,
                                        last_rect.bottom - first_rect.top)
            if self.save_scrollbar_rect:
                dropdown_area.union_ip(self.save_scrollbar_rect)

        if dropdown_area and dropdown_area.collidepoint(pos):
            is_click_outside = False

        if is_click_outside:
            self.save_dropdown_active = False

    def _handle_update_prompt_click(self, pos):
        """Обрабатывает клики в окне обновления."""
        if self.update_prompt_yes_rect and self.update_prompt_yes_rect.collidepoint(pos):
            print("Открытие ссылки для скачивания...")
            webbrowser.open(self.update_info['download_url'])
            self.running = False  # Закрываем приложение
        elif self.update_prompt_no_rect and self.update_prompt_no_rect.collidepoint(pos):
            self.program_state = 'normal'
            self.update_info = None  # Сбрасываем информацию об обновлении

    def _handle_overwrite_prompt_click(self, pos):
        """Обрабатывает клики в окне запроса перезаписи."""
        prompt_width = 500
        prompt_height = 200
        prompt_x = (SCREEN_WIDTH - prompt_width) // 2
        prompt_y = (SCREEN_HEIGHT - prompt_height) // 2

        button_width = 130
        button_height = 40
        button_spacing = 20
        total_buttons_width = 2 * button_width + button_spacing
        start_x_buttons = prompt_x + (prompt_width - total_buttons_width) // 2

        overwrite_button_rect = pygame.Rect(start_x_buttons, prompt_y + 140, button_width, button_height)
        rename_button_rect = pygame.Rect(start_x_buttons + button_width + button_spacing, prompt_y + 140, button_width,
                                         button_height)

        if overwrite_button_rect.collidepoint(pos):
            if self._save_config(self.pending_overwrite_config_name, overwrite=True):
                print(f"[DEBUG] Файл '{self.pending_overwrite_config_name}' перезаписан.")
                self._handle_post_save_actions()
            else:
                print("[DEBUG] Ошибка при перезаписи файла.")
                self.program_state = self.previous_program_state
            self.pending_overwrite_config_name = None
        elif rename_button_rect.collidepoint(pos):
            self.previous_program_state = 'overwrite_prompt'
            self.program_state = 'prompt_config_name'
            self.current_input_text = self._get_next_preset_name(
                self.pending_overwrite_config_name)  # Suggest a new name
            self.input_prompt_message = "Введите новое имя:"
            self.pending_overwrite_config_name = None
            print("[DEBUG] Пользователь решил переименовать файл.")

    def _handle_confirm_delete_click(self, pos):
        """Обрабатывает клики в окне подтверждения удаления."""
        if self.confirm_delete_yes_rect and self.confirm_delete_yes_rect.collidepoint(pos):
            config_to_delete_path = get_config_file_path(self.config_to_delete)
            try:
                if os.path.exists(config_to_delete_path):
                    os.remove(config_to_delete_path)
                    print(f"Пресет '{self.config_to_delete}' успешно удален.")
                else:
                    print(f"Предупреждение: Файл для пресета '{self.config_to_delete}' не найден.")
            except OSError as e:
                print(f"Ошибка при удалении файла '{config_to_delete_path}': {e}")

            # Возвращаемся к списку и обновляем его
            self.program_state = 'load_config_list'
            self.config_to_delete = None
            self._prepare_load_config_buttons()

        elif self.confirm_delete_no_rect and self.confirm_delete_no_rect.collidepoint(pos):
            # Просто возвращаемся к списку
            self.program_state = 'load_config_list'
            self.config_to_delete = None

    def _handle_load_config_list_click(self, pos):
        """Обрабатывает клики в окне выбора конфигурации."""
        prompt_width = 450
        prompt_height = 400
        prompt_x = (SCREEN_WIDTH - prompt_width) // 2
        prompt_y = (SCREEN_HEIGHT - prompt_height) // 2
        cancel_button_rect = pygame.Rect(prompt_x + prompt_width // 2 - 60, prompt_y + prompt_height - 60, 120, 40)

        # --- Scrollbar Interaction ---
        if self.load_scrollbar_handle_rect and self.load_scrollbar_handle_rect.collidepoint(pos):
            self.is_dragging_load_scrollbar = True
            self.scrollbar_drag_details = {'start_y': pos[1], 'start_offset': self.scroll_offset_load_configs}
            return

        if self.load_scrollbar_rect and self.load_scrollbar_rect.collidepoint(pos):
            list_area_rect = pygame.Rect(prompt_x + 30, prompt_y + 70, prompt_width - 60, prompt_height - 150)
            button_height = 35;
            button_spacing = 5
            max_visible_items = (list_area_rect.height - button_spacing) // (button_height + button_spacing)
            if pos[1] < self.load_scrollbar_handle_rect.top:
                self.scroll_offset_load_configs = max(0, self.scroll_offset_load_configs - max_visible_items)
            else:
                total_items = len(self._read_available_configs())
                self.scroll_offset_load_configs = min(total_items - max_visible_items,
                                                      self.scroll_offset_load_configs + max_visible_items)
            self._prepare_load_config_buttons()
            return

        if cancel_button_rect.collidepoint(pos):
            self.program_state = 'normal'
            self.scroll_offset_load_configs = 0
            self.load_config_buttons_rects = []
            self.last_clicked_config_name = None
            print("[DEBUG] Загрузка конфигурации отменена.")
            return

        for config_btn in self.load_config_buttons_rects:
            current_time = pygame.time.get_ticks()

            # Логика двойного клика по иконке редактирования
            if config_btn['edit_rect'].collidepoint(pos):
                if current_time - self.last_edit_icon_click['time'] < DOUBLE_CLICK_INTERVAL and \
                        self.last_edit_icon_click['name'] == config_btn['name']:
                    self.last_edit_icon_click = {'name': None, 'time': 0}  # Сброс
                    print(f"Двойной клик по иконке редактирования для '{config_btn['name']}'")
                    self.program_state = 'prompt_config_name'
                    self.prompt_context = 'rename'
                    self.config_to_rename = config_btn['name']
                    self.current_input_text = config_btn['name']
                    self.input_prompt_message = "Введите новое имя:"
                else:
                    self.last_edit_icon_click = {'name': config_btn['name'], 'time': current_time}
                return

            # Логика двойного клика по иконке удаления
            if config_btn['delete_rect'].collidepoint(pos):
                if current_time - self.last_delete_icon_click['time'] < DOUBLE_CLICK_INTERVAL and \
                        self.last_delete_icon_click['name'] == config_btn['name']:
                    self.last_delete_icon_click = {'name': None, 'time': 0}  # Сброс
                    print(f"Двойной клик по иконке удаления для '{config_btn['name']}'")
                    self.program_state = 'confirm_delete'
                    self.config_to_delete = config_btn['name']
                else:
                    self.last_delete_icon_click = {'name': config_btn['name'], 'time': current_time}
                return

            # Логика двойного клика по основной кнопке пресета
            if config_btn['rect'].collidepoint(pos):
                selected_config_name = config_btn['name']
                if current_time - self.last_load_click_time < DOUBLE_CLICK_INTERVAL and selected_config_name == self.last_clicked_config_name:
                    self.last_load_click_time = 0
                    self.last_clicked_config_name = None
                    print(f"[DEBUG] Двойной клик на '{selected_config_name}'. Загрузка...")
                    self._load_and_apply_config(selected_config_name)
                else:
                    self.last_load_click_time = current_time
                    self.last_clicked_config_name = selected_config_name
                    print(f"[DEBUG] Одиночный клик на '{selected_config_name}'.")
                return

    def _load_and_apply_config(self, config_name):
        """Загружает и применяет указанную конфигурацию."""
        print(f"[DEBUG] Вызов _load_and_apply_config для '{config_name}'")
        self._load_config(config_name)
        self._update_layer_button_rects()
        self._cache_all_button_surfaces()
        self.current_layer_index = 0
        if self.sound:
            self.sound.set_volume(self.volume)
        self._register_all_assigned_hotkeys()
        self.layer_manager._initialize_layer_dots()
        self.program_state = 'normal'
        print(
            f"[DEBUG] _load_and_apply_config завершено. Активная конфигурация: {self.current_active_config_name}")

    def _handle_key_input(self, event):
        """Обрабатывает ввод с клавиатуры."""
        if self.program_state == 'prompt_config_name':
            if event.key == pygame.K_RETURN:
                self.save_dropdown_active = False
                self._save_config_from_prompt()
            elif event.key == pygame.K_BACKSPACE:
                self.current_input_text = self.current_input_text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.save_dropdown_active = False
                self.program_state = 'normal'  # Always return to main interface
                self.unsaved_changes = True  # Keep changes marked as unsaved
                self.current_input_text = ""
                self.input_prompt_message = ""
                self.pending_action_after_prompt = None
                print("[DEBUG] Ввод имени конфигурации отменен, возврат к интерфейсу.")
            else:
                typed_char = None
                if pygame.K_a <= event.key <= pygame.K_z:
                    typed_char = chr(event.key)
                    if event.mod & (pygame.KMOD_LSHIFT | pygame.KMOD_RSHIFT | pygame.KMOD_CAPS):
                        typed_char = typed_char.upper()
                elif pygame.K_0 <= event.key <= pygame.K_9:
                    typed_char = chr(event.key)
                elif event.key == pygame.K_SPACE:
                    typed_char = ' '
                elif event.key == pygame.K_MINUS:
                    typed_char = '-'
                elif event.key == pygame.K_EQUALS:
                    typed_char = '='
                elif event.key == pygame.K_LEFTBRACKET:
                    typed_char = '['
                elif event.key == pygame.K_RIGHTBRACKET:
                    typed_char = ']'
                elif event.key == pygame.K_BACKSLASH:
                    typed_char = '\\'
                elif event.key == pygame.K_SEMICOLON:
                    typed_char = ';'
                elif event.key == pygame.K_QUOTE:
                    typed_char = '\''
                elif event.key == pygame.K_COMMA:
                    typed_char = ','
                elif event.key == pygame.K_PERIOD:
                    typed_char = '.'
                elif event.key == pygame.K_SLASH:
                    typed_char = '/'
                elif event.key == pygame.K_BACKQUOTE:
                    typed_char = '`'

                if typed_char is None and event.unicode and event.unicode.isprintable():
                    allowed_general_symbols = "~!@#$%^&*()_+-=[]{};'\\:\"|,./<>?"
                    if event.unicode in allowed_general_symbols:
                        typed_char = event.unicode

                if typed_char:
                    self.current_input_text += typed_char
            self.cursor_blink_timer = pygame.time.get_ticks()
            self.cursor_visible = True
            return

        if self.program_state == 'configuring' and self.button_to_configure:
            FORBIDDEN_KEYS = {
                pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_BACKSPACE,
                pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LCTRL, pygame.K_RCTRL,
                pygame.K_LALT, pygame.K_RALT, pygame.K_CAPSLOCK, pygame.K_TAB,
                pygame.K_LGUI, pygame.K_RGUI
            }

            if event.key in FORBIDDEN_KEYS:
                self.warning_message = "Эту клавишу нельзя назначить."
                self.warning_message_display_time = pygame.time.get_ticks()
                print("[DEBUG] Попытка назначить запрещенную клавишу.")
                return

            key_name_to_assign = pygame.key.name(event.key).upper()

            if self._is_key_already_assigned(key_name_to_assign):
                self.warning_message = f"Клавиша '{key_name_to_assign}' занята."
                self.warning_message_display_time = pygame.time.get_ticks()
                print(f"[DEBUG] Попытка назначить уже используемую клавишу: {key_name_to_assign}")
                return

            self.button_to_configure['text'] = key_name_to_assign
            self._update_cached_surfaces_for_button(self.button_to_configure)

            self.unsaved_changes = True
            self.warning_message = ""
            print(f"[DEBUG] Кнопке назначена клавиша: {key_name_to_assign}")
            self.program_state = 'normal'
            self.button_to_configure = None
            self._register_all_assigned_hotkeys()

    def _handle_post_save_actions(self):
        """
        Выполняет действия, отложенные после успешного сохранения конфигурации,
        затем загружает внутреннюю конфигурацию по умолчанию.
        """
        print("[DEBUG] После сохранения: загружаем внутреннюю конфигурацию по умолчанию.")

        if self.pending_action_after_prompt == 'show_load_list':
            self.program_state = 'load_config_list'
            self.scroll_offset_load_configs = 0
            self._prepare_load_config_buttons()
        else:
            self._load_and_apply_config(INTERNAL_DEFAULT_CONFIG_NAME)

        self.pending_action_after_prompt = None

    def _save_config_from_prompt(self):
        """Сохраняет или переименовывает конфигурацию, используя имя, введенное в поле ввода."""
        new_name = self.current_input_text.strip()
        if not new_name:
            print("[DEBUG] Имя конфигурации не может быть пустым.")
            return

        sanitized_new_name = self._sanitize_filename(new_name)
        if not sanitized_new_name:
            print(f"[DEBUG] Имя конфигурации '{new_name}' после очистки стало пустым.")
            return

        # --- Логика переименования ---
        if self.prompt_context == 'rename':
            old_name = self.config_to_rename
            if old_name == sanitized_new_name:
                self.program_state = 'load_config_list'  # Просто выходим
                return

            old_path = get_config_file_path(old_name)
            new_path = get_config_file_path(sanitized_new_name)

            if os.path.exists(new_path):
                print(f"[DEBUG] Имя '{sanitized_new_name}' уже занято.")
                self.warning_message = f"Имя '{sanitized_new_name}' уже занято."
                self.warning_message_display_time = pygame.time.get_ticks()
                return  # Остаемся в окне переименования

            try:
                os.rename(old_path, new_path)
                print(f"Пресет '{old_name}' переименован в '{sanitized_new_name}'.")
                self.program_state = 'load_config_list'
                self.config_to_rename = None
                self._prepare_load_config_buttons()  # Обновляем список файлов
            except OSError as e:
                print(f"Ошибка переименования файла: {e}")
                self.program_state = 'load_config_list'
            return

        # --- Логика сохранения (старая) ---
        config_path = get_config_file_path(sanitized_new_name)
        if os.path.exists(config_path):
            self.previous_program_state = 'prompt_config_name'
            self.pending_overwrite_config_name = sanitized_new_name
            self.program_state = 'overwrite_prompt'
            return

        if self._save_config(sanitized_new_name, overwrite=True):
            self._handle_post_save_actions()
        else:
            print("[DEBUG] Ошибка при сохранении конфигурации.")
            self.program_state = self.previous_program_state
            self.current_input_text = ""
            self.input_prompt_message = ""

    def _handle_unsaved_changes_prompt(self, pos):
        """Обрабатывает клики в окне запроса о несохраненных изменениях."""
        prompt_width = 450
        prompt_height = 200
        prompt_x = (SCREEN_WIDTH - prompt_width) // 2
        prompt_y = (SCREEN_HEIGHT - prompt_height) // 2

        button_width = 120
        button_height = 40
        button_spacing = 20
        total_buttons_width = (3 * button_width) + (2 * button_spacing)
        start_x = prompt_x + (prompt_width - total_buttons_width) // 2
        button_y = prompt_y + 130

        if self.prompt_context == 'exit':
            save_button_rect = pygame.Rect(start_x, button_y, button_width, button_height)
            back_button_rect = pygame.Rect(start_x + button_width + button_spacing, button_y, button_width,
                                           button_height)
            exit_button_rect = pygame.Rect(start_x + 2 * (button_width + button_spacing), button_y, button_width,
                                           button_height)

            if save_button_rect.collidepoint(pos):
                self.previous_program_state = 'unsaved_changes_prompt'
                self.program_state = 'prompt_config_name'
                self.current_input_text = self._get_next_preset_name()
                self.input_prompt_message = "Введите имя для нового пресета:"
            elif back_button_rect.collidepoint(pos):
                self.program_state = 'normal'
                self.prompt_context = None
            elif exit_button_rect.collidepoint(pos):
                self.running = False

        elif self.prompt_context == 'load':
            save_button_rect = pygame.Rect(start_x, button_y, button_width, button_height)
            dont_save_button_rect = pygame.Rect(start_x + button_width + button_spacing, button_y, button_width,
                                                button_height)
            back_button_rect = pygame.Rect(start_x + 2 * (button_width + button_spacing), button_y, button_width,
                                           button_height)

            if save_button_rect.collidepoint(pos):
                self.previous_program_state = 'unsaved_changes_prompt'
                self.program_state = 'prompt_config_name'
                self.current_input_text = self._get_next_preset_name()
                self.input_prompt_message = "Введите имя для нового пресета:"
                self.pending_action_after_prompt = 'show_load_list'
            elif dont_save_button_rect.collidepoint(pos):
                self.unsaved_changes = False
                self._load_and_apply_config(INTERNAL_DEFAULT_CONFIG_NAME)
                self.program_state = 'load_config_list'
                self.scroll_offset_load_configs = 0
                self._prepare_load_config_buttons()
                self.prompt_context = None
            elif back_button_rect.collidepoint(pos):
                self.program_state = 'normal'
                self.prompt_context = None

    def run(self):
        """Основной цикл приложения."""
        while self.running:
            delta_time = self.clock.tick(60) / 1000.0

            # --- Animation Update ---
            if self.save_dropdown_active and self.dropdown_anim_progress < 1.0:
                self.dropdown_anim_progress += self.dropdown_anim_speed * delta_time
                self.dropdown_anim_progress = min(1.0, self.dropdown_anim_progress)
            elif not self.save_dropdown_active and self.dropdown_anim_progress > 0.0:
                self.dropdown_anim_progress -= self.dropdown_anim_speed * delta_time
                self.dropdown_anim_progress = max(0.0, self.dropdown_anim_progress)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.unsaved_changes:
                        if self.program_state != 'unsaved_changes_prompt':
                            self.previous_program_state = 'normal'
                            self.program_state = 'unsaved_changes_prompt'
                            self.prompt_context = 'exit'
                    else:
                        self.running = False

                elif event.type == pygame.USEREVENT and event.action == 'show_update_prompt':
                    self.program_state = 'update_prompt'

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.program_state == 'update_prompt':
                            self._handle_update_prompt_click(event.pos)
                        elif self.program_state == 'unsaved_changes_prompt':
                            self._handle_unsaved_changes_prompt(event.pos)
                        elif self.program_state == 'confirm_delete':
                            self._handle_confirm_delete_click(event.pos)
                        elif self.volume_manager.handle_mouse_button_down(event.pos):
                            self.is_dragging_volume_knob = self.volume_manager.is_dragging_volume_knob
                            pass
                        elif self.program_state == 'prompt_config_name':
                            self._handle_prompt_click(event.pos)
                        elif self.program_state == 'load_config_list':
                            self._handle_load_config_list_click(event.pos)
                        elif self.program_state == 'overwrite_prompt':
                            self._handle_overwrite_prompt_click(event.pos)
                        elif self.program_state == 'normal' or (
                                self.program_state == 'configuring' and self.button_to_configure is None):
                            self._handle_mouse_click(event.pos)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.is_dragging_load_scrollbar = False
                        self.is_dragging_save_scrollbar = False
                        self.volume_manager.handle_mouse_button_up()
                        self.is_dragging_volume_knob = self.volume_manager.is_dragging_volume_knob
                elif event.type == pygame.MOUSEMOTION:
                    if self.is_dragging_load_scrollbar:
                        mouse_y = event.pos[1]
                        delta_y = mouse_y - self.scrollbar_drag_details['start_y']

                        track_height = self.load_scrollbar_rect.height
                        handle_height = self.load_scrollbar_handle_rect.height
                        scrollable_track_space = track_height - handle_height

                        total_items = len(self._read_available_configs())
                        list_area_rect = pygame.Rect(0, 0, 450 - 60, 400 - 150)
                        button_height = 35;
                        button_spacing = 5
                        max_visible_items = (list_area_rect.height - button_spacing) // (button_height + button_spacing)

                        scrollable_items = total_items - max_visible_items

                        if scrollable_track_space > 0:
                            scroll_per_pixel = scrollable_items / scrollable_track_space
                            new_offset = self.scrollbar_drag_details['start_offset'] + delta_y * scroll_per_pixel
                            self.scroll_offset_load_configs = max(0, min(scrollable_items, int(round(new_offset))))
                            self._prepare_load_config_buttons()

                    elif self.is_dragging_save_scrollbar:
                        mouse_y = event.pos[1]
                        delta_y = mouse_y - self.scrollbar_drag_details['start_y']

                        track_height = self.save_scrollbar_rect.height
                        handle_height = self.save_scrollbar_handle_rect.height
                        scrollable_track_space = track_height - handle_height

                        total_items = len(self._read_available_configs())
                        max_visible_items = 4

                        scrollable_items = total_items - max_visible_items

                        if scrollable_track_space > 0:
                            scroll_per_pixel = scrollable_items / scrollable_track_space
                            new_offset = self.scrollbar_drag_details['start_offset'] + delta_y * scroll_per_pixel
                            self.save_dropdown_scroll_offset = max(0, min(scrollable_items, int(round(new_offset))))
                            self._prepare_save_dropdown_buttons()

                    if self.volume_manager.handle_mouse_motion(event.pos):
                        pass
                elif event.type == pygame.KEYDOWN:
                    self._handle_key_input(event)
                elif event.type == pygame.MOUSEWHEEL:
                    if self.program_state == 'load_config_list':
                        config_names_count = len(self._read_available_configs())
                        list_area_height = 400 - 150
                        button_height = 35
                        button_spacing = 5
                        max_visible_items = (list_area_height - button_spacing) // (button_height + button_spacing)
                        if max_visible_items <= 0: max_visible_items = 1

                        if event.y > 0:
                            if self.scroll_offset_load_configs > 0:
                                self.scroll_offset_load_configs -= 1
                                self._prepare_load_config_buttons()
                        elif event.y < 0:
                            if self.scroll_offset_load_configs + max_visible_items < config_names_count:
                                self.scroll_offset_load_configs += 1
                                self._prepare_load_config_buttons()
                    elif self.program_state == 'prompt_config_name' and self.dropdown_anim_progress > 0.5:
                        config_names_count = len(self._read_available_configs())
                        max_visible_items = 4
                        if event.y > 0:
                            if self.save_dropdown_scroll_offset > 0:
                                self.save_dropdown_scroll_offset -= 1
                                self._prepare_save_dropdown_buttons()
                        elif event.y < 0:
                            if self.save_dropdown_scroll_offset + max_visible_items < config_names_count:
                                self.save_dropdown_scroll_offset += 1
                                self._prepare_save_dropdown_buttons()
                    else:
                        self.layer_manager.handle_mouse_wheel(event.y)

            current_time = pygame.time.get_ticks()

            if self.warning_message and current_time - self.warning_message_display_time > WARNING_DURATION_MS:
                self.warning_message = ""

            if current_time - self.last_frame_switch_time > FRAME_ANIMATION_INTERVAL_MS:
                if self.unassigned_key_frames:
                    self.current_frame_index = (self.current_frame_index + 1) % len(self.unassigned_key_frames)
                    self.needs_unassigned_redraw = True
                self.last_frame_switch_time = current_time

            if current_time - self.cursor_blink_timer > CURSOR_BLINK_RATE:
                self.cursor_visible = not self.cursor_visible
                self.cursor_blink_timer = current_time

            if self.background_image:
                self.screen.blit(self.background_image, (0, 0))
            else:
                self.screen.fill(DARK_GRAY)

            if self.logo_image:
                self.screen.blit(self.logo_image, (LOGO_POS_X, LOGO_POS_Y))

            self._draw_buttons()
            self._draw_control_buttons()
            self.layer_manager.draw_layer_switcher()
            self._draw_right_rectangle()
            self.volume_manager.draw_volume_slider()

            # --- Drawing prompts on top of everything ---
            if self.program_state == 'update_prompt':
                self._draw_update_prompt()
            elif self.program_state == 'unsaved_changes_prompt':
                self._draw_unsaved_changes_prompt()
            elif self.program_state == 'prompt_config_name':
                self._draw_config_name_prompt()
            elif self.program_state == 'load_config_list':
                self._draw_load_config_list()
            elif self.program_state == 'overwrite_prompt':
                self._draw_overwrite_prompt()
            elif self.program_state == 'confirm_delete':
                self._draw_confirm_delete_prompt()

            # --- Warning message on top of all prompts except update ---
            if self.program_state not in ['update_prompt']:
                if self.warning_message:
                    message = self.font_message.render(self.warning_message, True, self.WHITE)
                    message_rect = message.get_rect(center=(SCREEN_WIDTH // 1.8, MESSAGE_CONFIGURING_Y))
                    self.screen.blit(message, message_rect)
                elif self.program_state == 'configuring':
                    message_text = "Нажмите на кнопку для назначения..." if self.button_to_configure is None else "Нажмите новую клавишу..."
                    message = self.font_message.render(message_text, True, self.WHITE)
                    message_rect = message.get_rect(center=(SCREEN_WIDTH // 1.8, MESSAGE_CONFIGURING_Y))
                    self.screen.blit(message, message_rect)

            pygame.display.flip()

        keyboard.unhook_all()
        pygame.quit()
        sys.exit()


def main():
    app = SoundpadApp()
    if app.running:
        app.run()


if __name__ == '__main__':
    main()