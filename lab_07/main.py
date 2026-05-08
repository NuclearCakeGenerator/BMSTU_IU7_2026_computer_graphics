import tkinter as tk
from enum import Enum, auto
from tkinter import colorchooser, messagebox

from utils import (
    BACKGROUND_COLOR,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    DEFAULT_CLIPPER_COLOR,
    DEFAULT_RESULT_COLOR,
    DEFAULT_SEGMENT_COLOR,
    LEFT_PANEL_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    Point,
    Rect,
    Segment,
    normalize_rect,
)


OUT_LEFT = 1
OUT_RIGHT = 2
OUT_BOTTOM = 4
OUT_TOP = 8


class MouseMode(Enum):
    NONE = auto()
    SEGMENT = auto()
    CLIPPER = auto()


class Lab07App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Lab 07 - Отсечение отрезков методом Сазерленда-Коэна")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        self.clipper_color = DEFAULT_CLIPPER_COLOR
        self.segment_color = DEFAULT_SEGMENT_COLOR
        self.result_color = DEFAULT_RESULT_COLOR

        self.clipper_rect: Rect | None = None
        self.segments: list[Segment] = []
        self.clipped_segments: list[Segment] = []

        self.mouse_mode = MouseMode.NONE
        self.pending_segment_start: Point | None = None
        self.clipper_drag_start: Point | None = None
        self.preview_segment: Segment | None = None
        self.preview_rect: Rect | None = None

        self.clipper_vars = [
            tk.StringVar(value="120"),
            tk.StringVar(value="120"),
            tk.StringVar(value="560"),
            tk.StringVar(value="420"),
        ]
        self.segment_vars = [
            tk.StringVar(value="80"),
            tk.StringVar(value="80"),
            tk.StringVar(value="650"),
            tk.StringVar(value="340"),
        ]

        self._build_layout()
        self._bind_events()
        self._redraw_all()
        self._update_status(
            "Задайте отсекатель и отрезки мышью или через координаты, затем нажмите 'Отсечь'."
        )

    def _build_layout(self):
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        self.left_frame = tk.Frame(
            self.container,
            width=LEFT_PANEL_WIDTH,
            padx=10,
            pady=10,
            relief="ridge",
            borderwidth=1,
        )
        self.left_frame.pack(side="left", fill="y")
        self.left_frame.pack_propagate(False)

        self.right_frame = tk.Frame(self.container, padx=10, pady=10)
        self.right_frame.pack(side="left", fill="both", expand=True)

        self._build_color_section()
        self._build_clipper_section()
        self._build_segment_section()
        self._build_action_section()

        tk.Label(self.right_frame, text="Статус:").pack(anchor="w")
        self.status_var = tk.StringVar(value="")
        self.status_entry = tk.Entry(
            self.right_frame,
            textvariable=self.status_var,
            state="readonly",
            readonlybackground="#FFFFFF",
        )
        self.status_entry.pack(fill="x", pady=(0, 8))

        self.canvas = tk.Canvas(
            self.right_frame,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg=BACKGROUND_COLOR,
            highlightthickness=1,
            highlightbackground="#555555",
            cursor="crosshair",
        )
        self.canvas.pack(fill="both", expand=True)

    def _build_color_section(self):
        color_frame = tk.LabelFrame(self.left_frame, text="Цвета", padx=8, pady=8)
        color_frame.pack(fill="x", pady=(0, 10))

        self._build_color_picker(
            color_frame,
            "Отсекатель",
            self.clipper_color,
            self._choose_clipper_color,
        )
        self._build_color_picker(
            color_frame,
            "Отрезки",
            self.segment_color,
            self._choose_segment_color,
        )
        self._build_color_picker(
            color_frame,
            "Результат",
            self.result_color,
            self._choose_result_color,
        )

    def _build_color_picker(
        self,
        parent: tk.Widget,
        label: str,
        color: str,
        command,
    ):
        row = tk.Frame(parent)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label, width=12, anchor="w").pack(side="left")
        preview = tk.Label(row, text="      ", bg=color, relief="sunken", borderwidth=1)
        preview.pack(side="left")
        button = tk.Button(row, text="Выбрать", command=command, cursor="hand2")
        button.pack(side="left", padx=8)
        if label == "Отсекатель":
            self.clipper_color_preview = preview
        elif label == "Отрезки":
            self.segment_color_preview = preview
        else:
            self.result_color_preview = preview

    def _build_clipper_section(self):
        clipper_frame = tk.LabelFrame(
            self.left_frame, text="Отсекатель", padx=8, pady=8
        )
        clipper_frame.pack(fill="x", pady=(0, 10))

        self._build_entry_grid(
            clipper_frame,
            self.clipper_vars,
            labels=("x1", "y1", "x2", "y2"),
        )

        button_row = tk.Frame(clipper_frame)
        button_row.pack(fill="x", pady=(8, 0))

        tk.Button(
            button_row,
            text="Задать",
            command=self._set_clipper_from_entries,
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            button_row,
            text="Задать мышью",
            command=self._start_clipper_mouse_mode,
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            button_row,
            text="Очистить отсекатель",
            command=self._clear_clipper,
            cursor="hand2",
        ).pack(fill="x")

        tk.Label(
            clipper_frame,
            text="Мышь: нажмите и протяните прямоугольник.",
            anchor="w",
            wraplength=280,
            justify="left",
        ).pack(fill="x", pady=(6, 0))

    def _build_segment_section(self):
        segment_frame = tk.LabelFrame(
            self.left_frame, text="Отрезки", padx=8, pady=8
        )
        segment_frame.pack(fill="x", pady=(0, 10))

        self._build_entry_grid(
            segment_frame,
            self.segment_vars,
            labels=("x1", "y1", "x2", "y2"),
        )

        tk.Button(
            segment_frame,
            text="Добавить",
            command=self._add_segment_from_entries,
            cursor="hand2",
        ).pack(fill="x", pady=(8, 4))
        tk.Button(
            segment_frame,
            text="Горизонтальный",
            command=self._add_horizontal_segment,
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            segment_frame,
            text="Вертикальный",
            command=self._add_vertical_segment,
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            segment_frame,
            text="Добавить мышью",
            command=self._start_segment_mouse_mode,
            cursor="hand2",
        ).pack(fill="x")

        tk.Label(
            segment_frame,
            text="Мышь: первый клик задает начало, второй - конец.",
            anchor="w",
            wraplength=280,
            justify="left",
        ).pack(fill="x", pady=(6, 0))

    def _build_action_section(self):
        action_frame = tk.LabelFrame(
            self.left_frame, text="Действия", padx=8, pady=8
        )
        action_frame.pack(fill="x", pady=(0, 10))

        tk.Button(
            action_frame,
            text="Отсечь все",
            command=self._clip_all_segments,
            bg="#FFD8A8",
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            action_frame,
            text="Очистить результат",
            command=self._clear_result,
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            action_frame,
            text="Очистить все",
            command=self._clear_all,
            bg="#FFCCCC",
            cursor="hand2",
        ).pack(fill="x")

        tk.Label(
            action_frame,
            text="Если меняете геометрию, результат отсечения сбрасывается.",
            anchor="w",
            wraplength=280,
            justify="left",
        ).pack(fill="x", pady=(6, 0))

    def _build_entry_grid(
        self,
        parent: tk.Widget,
        variables: list[tk.StringVar],
        labels: tuple[str, str, str, str],
    ):
        grid = tk.Frame(parent)
        grid.pack(fill="x")

        for column, label in enumerate(labels):
            tk.Label(grid, text=label).grid(row=0, column=column, padx=4, sticky="w")
        for column, variable in enumerate(variables):
            entry = tk.Entry(grid, textvariable=variable, width=8, justify="right")
            entry.grid(row=1, column=column, padx=4, pady=(2, 0))

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self._on_canvas_left_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_left_release)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)

    def _update_status(self, text: str):
        self.status_var.set(text)

    def _choose_clipper_color(self):
        color = colorchooser.askcolor(
            title="Выберите цвет отсекателя",
            color=self.clipper_color,
        )[1]
        if color is None:
            return
        self.clipper_color = color.upper()
        self.clipper_color_preview.config(bg=self.clipper_color)
        self._redraw_all()

    def _choose_segment_color(self):
        color = colorchooser.askcolor(
            title="Выберите цвет отрезков",
            color=self.segment_color,
        )[1]
        if color is None:
            return
        self.segment_color = color.upper()
        self.segment_color_preview.config(bg=self.segment_color)
        self._redraw_all()

    def _choose_result_color(self):
        color = colorchooser.askcolor(
            title="Выберите цвет результата",
            color=self.result_color,
        )[1]
        if color is None:
            return
        self.result_color = color.upper()
        self.result_color_preview.config(bg=self.result_color)
        self._redraw_all()

    def _parse_float(self, value: str, field_name: str) -> float:
        try:
            return float(value)
        except ValueError as exc:
            raise ValueError(f"Поле {field_name} должно содержать число.") from exc

    def _point_from_vars(self, variables: list[tk.StringVar], prefix: str) -> tuple[Point, Point]:
        x1 = self._parse_float(variables[0].get(), f"{prefix} x1")
        y1 = self._parse_float(variables[1].get(), f"{prefix} y1")
        x2 = self._parse_float(variables[2].get(), f"{prefix} x2")
        y2 = self._parse_float(variables[3].get(), f"{prefix} y2")
        return Point(x1, y1), Point(x2, y2)

    def _set_clipper_from_entries(self):
        try:
            first, second = self._point_from_vars(self.clipper_vars, "отсекатель")
        except ValueError as exc:
            messagebox.showwarning("Неверные координаты", str(exc))
            return

        rect = normalize_rect(first, second)
        if rect.left == rect.right or rect.top == rect.bottom:
            messagebox.showwarning(
                "Некорректный отсекатель",
                "Отсекатель должен иметь ненулевую ширину и высоту.",
            )
            return

        self.clipper_rect = rect
        self._clear_result()
        self._update_status(
            f"Отсекатель задан: ({rect.left:.0f}, {rect.top:.0f}) - ({rect.right:.0f}, {rect.bottom:.0f})."
        )
        self._redraw_all()

    def _add_segment(self, first: Point, second: Point):
        if first.x == second.x and first.y == second.y:
            messagebox.showwarning(
                "Некорректный отрезок",
                "Концы отрезка не должны совпадать.",
            )
            return

        self.segments.append(Segment(first, second))
        self._clear_result()
        self._update_status(
            f"Добавлен отрезок: ({first.x:.0f}, {first.y:.0f}) - ({second.x:.0f}, {second.y:.0f})."
        )
        self._redraw_all()

    def _add_segment_from_entries(self):
        try:
            first, second = self._point_from_vars(self.segment_vars, "отрезок")
        except ValueError as exc:
            messagebox.showwarning("Неверные координаты", str(exc))
            return

        self._add_segment(first, second)

    def _add_horizontal_segment(self):
        try:
            first, second = self._point_from_vars(self.segment_vars, "отрезок")
        except ValueError as exc:
            messagebox.showwarning("Неверные координаты", str(exc))
            return

        horizontal = Segment(Point(first.x, first.y), Point(second.x, first.y))
        self._add_segment(horizontal.start, horizontal.end)

    def _add_vertical_segment(self):
        try:
            first, second = self._point_from_vars(self.segment_vars, "отрезок")
        except ValueError as exc:
            messagebox.showwarning("Неверные координаты", str(exc))
            return

        vertical = Segment(Point(first.x, first.y), Point(first.x, second.y))
        self._add_segment(vertical.start, vertical.end)

    def _start_segment_mouse_mode(self):
        self.mouse_mode = MouseMode.SEGMENT
        self.pending_segment_start = None
        self.clipper_drag_start = None
        self.preview_segment = None
        self.preview_rect = None
        self._redraw_all()
        self._update_status("Режим мыши для отрезков: нажмите начало, затем конец.")

    def _start_clipper_mouse_mode(self):
        self.mouse_mode = MouseMode.CLIPPER
        self.pending_segment_start = None
        self.clipper_drag_start = None
        self.preview_segment = None
        self.preview_rect = None
        self._redraw_all()
        self._update_status("Режим мыши для отсекателя: нажмите и протяните прямоугольник.")

    def _clear_mouse_state(self):
        self.mouse_mode = MouseMode.NONE
        self.pending_segment_start = None
        self.clipper_drag_start = None
        self.preview_segment = None
        self.preview_rect = None

    def _point_from_event(self, event: tk.Event) -> Point | None:
        if not (0 <= event.x < CANVAS_WIDTH and 0 <= event.y < CANVAS_HEIGHT):
            return None
        return Point(float(event.x), float(event.y))

    def _on_canvas_left_click(self, event: tk.Event):
        point = self._point_from_event(event)
        if point is None:
            return

        if self.mouse_mode is MouseMode.CLIPPER:
            self.clipper_drag_start = point
            self.preview_rect = Rect(point.x, point.y, point.x, point.y)
            self._redraw_all()
            return

        if self.mouse_mode is MouseMode.SEGMENT:
            if self.pending_segment_start is None:
                self.pending_segment_start = point
                self.preview_segment = Segment(point, point)
                self._redraw_all()
                self._update_status(
                    f"Начало отрезка: ({point.x:.0f}, {point.y:.0f}). Нажмите конец."
                )
                return

            self._add_segment(self.pending_segment_start, point)
            self.pending_segment_start = None
            self.preview_segment = None
            self._clear_mouse_state()
            return

    def _on_canvas_mouse_move(self, event: tk.Event):
        point = self._point_from_event(event)
        if point is None:
            return

        if self.mouse_mode is MouseMode.CLIPPER and self.clipper_drag_start is not None:
            self.preview_rect = normalize_rect(self.clipper_drag_start, point)
            self._redraw_all()
            return

        if self.mouse_mode is MouseMode.SEGMENT and self.pending_segment_start is not None:
            self.preview_segment = Segment(self.pending_segment_start, point)
            self._redraw_all()

    def _on_canvas_left_release(self, event: tk.Event):
        if self.mouse_mode is not MouseMode.CLIPPER or self.clipper_drag_start is None:
            return

        point = self._point_from_event(event)
        if point is None:
            self.preview_rect = None
            self.clipper_drag_start = None
            self._redraw_all()
            return

        rect = normalize_rect(self.clipper_drag_start, point)
        self.clipper_drag_start = None
        self.preview_rect = None

        if rect.left == rect.right or rect.top == rect.bottom:
            self._redraw_all()
            self._update_status("Отсекатель не задан: прямоугольник слишком мал.")
            return

        self.clipper_rect = rect
        self._clear_result()
        self._clear_mouse_state()
        self._redraw_all()
        self._update_status(
            f"Отсекатель задан мышью: ({rect.left:.0f}, {rect.top:.0f}) - ({rect.right:.0f}, {rect.bottom:.0f})."
        )

    def _on_canvas_right_click(self, event: tk.Event):
        self._clear_mouse_state()
        self._redraw_all()
        self._update_status("Режим мыши отменен.")

    def _region_code(self, point: Point, rect: Rect) -> int:
        code = 0
        if point.x < rect.left:
            code |= OUT_LEFT
        elif point.x > rect.right:
            code |= OUT_RIGHT

        if point.y < rect.top:
            code |= OUT_TOP
        elif point.y > rect.bottom:
            code |= OUT_BOTTOM

        return code

    def _clip_segment(self, segment: Segment) -> Segment | None:
        if self.clipper_rect is None:
            return None

        rect = self.clipper_rect
        x0 = segment.start.x
        y0 = segment.start.y
        x1 = segment.end.x
        y1 = segment.end.y

        code0 = self._region_code(segment.start, rect)
        code1 = self._region_code(segment.end, rect)

        while True:
            if not (code0 | code1):
                return Segment(Point(x0, y0), Point(x1, y1))

            if code0 & code1:
                return None

            out_code = code0 or code1

            if out_code & OUT_TOP:
                if y1 == y0:
                    return None
                x = x0 + (x1 - x0) * (rect.top - y0) / (y1 - y0)
                y = rect.top
            elif out_code & OUT_BOTTOM:
                if y1 == y0:
                    return None
                x = x0 + (x1 - x0) * (rect.bottom - y0) / (y1 - y0)
                y = rect.bottom
            elif out_code & OUT_RIGHT:
                if x1 == x0:
                    return None
                y = y0 + (y1 - y0) * (rect.right - x0) / (x1 - x0)
                x = rect.right
            else:
                if x1 == x0:
                    return None
                y = y0 + (y1 - y0) * (rect.left - x0) / (x1 - x0)
                x = rect.left

            if out_code == code0:
                x0, y0 = x, y
                code0 = self._region_code(Point(x0, y0), rect)
            else:
                x1, y1 = x, y
                code1 = self._region_code(Point(x1, y1), rect)

    def _clip_all_segments(self):
        if self.clipper_rect is None:
            messagebox.showwarning("Невозможно отсечь", "Сначала задайте отсекатель.")
            return

        if not self.segments:
            messagebox.showwarning("Невозможно отсечь", "Сначала добавьте отрезки.")
            return

        self.clipped_segments = []
        for segment in self.segments:
            clipped = self._clip_segment(segment)
            if clipped is not None:
                self.clipped_segments.append(clipped)

        self._redraw_all()
        self._update_status(
            f"Отсечение выполнено: {len(self.clipped_segments)} из {len(self.segments)} отрезков попали внутрь."
        )

    def _draw_segment(self, segment: Segment, color: str, width: int = 2, dash=None):
        kwargs = {
            "fill": color,
            "width": width,
        }
        if dash is not None:
            kwargs["dash"] = dash
        self.canvas.create_line(
            segment.start.x,
            segment.start.y,
            segment.end.x,
            segment.end.y,
            **kwargs,
        )

    def _draw_rect(self, rect: Rect, color: str, width: int = 2, dash=None):
        kwargs = {
            "outline": color,
            "width": width,
        }
        if dash is not None:
            kwargs["dash"] = dash
        self.canvas.create_rectangle(rect.left, rect.top, rect.right, rect.bottom, **kwargs)

    def _redraw_all(self):
        self.canvas.delete("all")

        for segment in self.segments:
            self._draw_segment(segment, self.segment_color, width=2)

        if self.clipper_rect is not None:
            self._draw_rect(self.clipper_rect, self.clipper_color, width=2)

        for segment in self.clipped_segments:
            self._draw_segment(segment, self.result_color, width=4)

        if self.preview_segment is not None:
            self._draw_segment(self.preview_segment, "#7DD3FC", width=2, dash=(6, 3))

        if self.preview_rect is not None:
            self._draw_rect(self.preview_rect, "#7DD3FC", width=2, dash=(6, 3))

    def _clear_result(self):
        self.clipped_segments.clear()
        self._redraw_all()

    def _clear_clipper(self):
        self.clipper_rect = None
        self._clear_result()
        self._redraw_all()
        self._update_status("Отсекатель очищен.")

    def _clear_all(self):
        self.clipper_rect = None
        self.segments.clear()
        self.clipped_segments.clear()
        self._clear_mouse_state()
        self._redraw_all()
        self._update_status("Холст очищен. Начните заново.")


if __name__ == "__main__":
    root = tk.Tk()
    app = Lab07App(root)
    root.mainloop()