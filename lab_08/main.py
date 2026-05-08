import tkinter as tk
from enum import Enum, auto
from math import isclose
from tkinter import colorchooser, messagebox

from utils import (
    BACKGROUND_COLOR,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    DEFAULT_CLIPPER_COLOR,
    DEFAULT_RESULT_COLOR,
    DEFAULT_SEGMENT_COLOR,
    EPS,
    LEFT_PANEL_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    Point,
    Segment,
    cross,
    dot,
    length,
    vec_mul,
    vec_sub,
)


class MouseMode(Enum):
    NONE = auto()
    SEGMENT = auto()
    CLIPPER = auto()


class Lab08App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Lab 08 - Отсечение отрезков методом Кируса-Бэка")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        self.clipper_color = DEFAULT_CLIPPER_COLOR
        self.segment_color = DEFAULT_SEGMENT_COLOR
        self.result_color = DEFAULT_RESULT_COLOR

        self.clipper_vertices: list[Point] = []
        self.clipper_closed = False
        self.segments: list[Segment] = []
        self.clipped_segments: list[Segment] = []

        self.mouse_mode = MouseMode.NONE
        self.pending_segment_start: Point | None = None
        self.preview_segment: Segment | None = None
        self.preview_poly_point: Point | None = None

        self.vertex_vars = [
            tk.StringVar(value="200"),
            tk.StringVar(value="180"),
        ]
        self.segment_vars = [
            tk.StringVar(value="120"),
            tk.StringVar(value="120"),
            tk.StringVar(value="720"),
            tk.StringVar(value="460"),
        ]
        self.parallel_side_var = tk.StringVar(value="1")

        self._build_layout()
        self._bind_events()
        self._redraw_all()
        self._update_status(
            "Задайте выпуклый отсекатель и отрезки, затем нажмите 'Отсечь все'."
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
        clipper_frame = tk.LabelFrame(self.left_frame, text="Отсекатель", padx=8, pady=8)
        clipper_frame.pack(fill="x", pady=(0, 10))

        grid = tk.Frame(clipper_frame)
        grid.pack(fill="x")
        tk.Label(grid, text="x").grid(row=0, column=0, padx=4, sticky="w")
        tk.Label(grid, text="y").grid(row=0, column=1, padx=4, sticky="w")
        tk.Entry(grid, textvariable=self.vertex_vars[0], width=10, justify="right").grid(
            row=1,
            column=0,
            padx=4,
            pady=(2, 0),
        )
        tk.Entry(grid, textvariable=self.vertex_vars[1], width=10, justify="right").grid(
            row=1,
            column=1,
            padx=4,
            pady=(2, 0),
        )

        tk.Button(
            clipper_frame,
            text="Добавить вершину",
            command=self._add_vertex_from_entries,
            cursor="hand2",
        ).pack(fill="x", pady=(8, 4))
        tk.Button(
            clipper_frame,
            text="Замкнуть отсекатель",
            command=self._close_clipper,
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            clipper_frame,
            text="Ввод мышью",
            command=self._start_clipper_mouse_mode,
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            clipper_frame,
            text="Очистить отсекатель",
            command=self._clear_clipper,
            cursor="hand2",
        ).pack(fill="x")

        tk.Label(
            clipper_frame,
            text=(
                "Мышь: левый клик добавляет вершину, правый клик замыкает многоугольник."
            ),
            anchor="w",
            wraplength=340,
            justify="left",
        ).pack(fill="x", pady=(6, 0))

        self.clipper_info_var = tk.StringVar(value="Вершин: 0")
        tk.Label(
            clipper_frame,
            textvariable=self.clipper_info_var,
            anchor="w",
            fg="#0B5",
        ).pack(fill="x", pady=(6, 0))

    def _build_segment_section(self):
        segment_frame = tk.LabelFrame(self.left_frame, text="Отрезки", padx=8, pady=8)
        segment_frame.pack(fill="x", pady=(0, 10))

        grid = tk.Frame(segment_frame)
        grid.pack(fill="x")
        for column, label in enumerate(("x1", "y1", "x2", "y2")):
            tk.Label(grid, text=label).grid(row=0, column=column, padx=4, sticky="w")
        for column, variable in enumerate(self.segment_vars):
            tk.Entry(grid, textvariable=variable, width=7, justify="right").grid(
                row=1,
                column=column,
                padx=4,
                pady=(2, 0),
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

        parallel_row = tk.Frame(segment_frame)
        parallel_row.pack(fill="x", pady=(0, 4))
        tk.Label(parallel_row, text="Сторона №", width=10, anchor="w").pack(side="left")
        tk.Entry(
            parallel_row,
            textvariable=self.parallel_side_var,
            width=6,
            justify="right",
        ).pack(side="left")
        tk.Button(
            parallel_row,
            text="Параллельный",
            command=self._add_parallel_segment,
            cursor="hand2",
        ).pack(side="left", padx=(8, 0))

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
            wraplength=340,
            justify="left",
        ).pack(fill="x", pady=(6, 0))

    def _build_action_section(self):
        action_frame = tk.LabelFrame(self.left_frame, text="Действия", padx=8, pady=8)
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

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self._on_canvas_left_click)
        self.canvas.bind("<Motion>", self._on_canvas_mouse_move)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)

    def _update_status(self, text: str):
        self.status_var.set(text)

    def _update_clipper_info(self):
        closed_text = "замкнут" if self.clipper_closed else "не замкнут"
        self.clipper_info_var.set(f"Вершин: {len(self.clipper_vertices)}, {closed_text}.")

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

    def _point_from_event(self, event: tk.Event) -> Point | None:
        if not (0 <= event.x < CANVAS_WIDTH and 0 <= event.y < CANVAS_HEIGHT):
            return None
        return Point(float(event.x), float(event.y))

    def _segment_from_vars(self) -> tuple[Point, Point]:
        x1 = self._parse_float(self.segment_vars[0].get(), "x1")
        y1 = self._parse_float(self.segment_vars[1].get(), "y1")
        x2 = self._parse_float(self.segment_vars[2].get(), "x2")
        y2 = self._parse_float(self.segment_vars[3].get(), "y2")
        return Point(x1, y1), Point(x2, y2)

    def _add_vertex(self, point: Point):
        if self.clipper_closed:
            self.clipper_vertices.clear()
            self.clipper_closed = False

        if self.clipper_vertices:
            prev = self.clipper_vertices[-1]
            if isclose(prev.x, point.x, abs_tol=EPS) and isclose(prev.y, point.y, abs_tol=EPS):
                self._update_status("Вершина совпадает с предыдущей и была пропущена.")
                return

        self.clipper_vertices.append(point)
        self._clear_result()
        self._update_clipper_info()
        self._redraw_all()
        self._update_status(
            f"Добавлена вершина: ({point.x:.0f}, {point.y:.0f})."
        )

    def _add_vertex_from_entries(self):
        try:
            x = self._parse_float(self.vertex_vars[0].get(), "x")
            y = self._parse_float(self.vertex_vars[1].get(), "y")
        except ValueError as exc:
            messagebox.showwarning("Неверные координаты", str(exc))
            return

        self._add_vertex(Point(x, y))

    def _polygon_orientation(self, vertices: list[Point]) -> float:
        area2 = 0.0
        for i in range(len(vertices)):
            a = vertices[i]
            b = vertices[(i + 1) % len(vertices)]
            area2 += a.x * b.y - b.x * a.y
        return area2

    def _is_convex_polygon(self, vertices: list[Point]) -> bool:
        n = len(vertices)
        if n < 3:
            return False

        sign = 0
        for i in range(n):
            a = vertices[i]
            b = vertices[(i + 1) % n]
            c = vertices[(i + 2) % n]
            ab = vec_sub(b, a)
            bc = vec_sub(c, b)
            z = cross(ab, bc)
            if abs(z) < EPS:
                continue
            current_sign = 1 if z > 0 else -1
            if sign == 0:
                sign = current_sign
            elif sign != current_sign:
                return False

        return sign != 0

    def _close_clipper(self):
        if len(self.clipper_vertices) < 3:
            messagebox.showwarning(
                "Некорректный отсекатель",
                "Для замыкания нужно минимум 3 вершины.",
            )
            return

        if not self._is_convex_polygon(self.clipper_vertices):
            messagebox.showwarning(
                "Некорректный отсекатель",
                "Отсекатель должен быть выпуклым и без вырожденных сторон.",
            )
            return

        self.clipper_closed = True
        self._clear_result()
        self._clear_mouse_state()
        self._update_clipper_info()
        self._redraw_all()
        self._update_status(
            f"Отсекатель замкнут. Вершин: {len(self.clipper_vertices)}."
        )

    def _start_clipper_mouse_mode(self):
        self.mouse_mode = MouseMode.CLIPPER
        self.pending_segment_start = None
        self.preview_segment = None
        self.preview_poly_point = None
        self._redraw_all()
        self._update_status(
            "Режим отсекателя: левый клик добавляет вершину, правый - замыкает."
        )

    def _start_segment_mouse_mode(self):
        self.mouse_mode = MouseMode.SEGMENT
        self.pending_segment_start = None
        self.preview_segment = None
        self.preview_poly_point = None
        self._redraw_all()
        self._update_status("Режим отрезков: выберите начало и конец отрезка.")

    def _clear_mouse_state(self):
        self.mouse_mode = MouseMode.NONE
        self.pending_segment_start = None
        self.preview_segment = None
        self.preview_poly_point = None

    def _on_canvas_left_click(self, event: tk.Event):
        point = self._point_from_event(event)
        if point is None:
            return

        if self.mouse_mode is MouseMode.CLIPPER:
            self._add_vertex(point)
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

    def _on_canvas_mouse_move(self, event: tk.Event):
        point = self._point_from_event(event)
        if point is None:
            return

        if self.mouse_mode is MouseMode.SEGMENT and self.pending_segment_start is not None:
            self.preview_segment = Segment(self.pending_segment_start, point)
            self._redraw_all()
            return

        if self.mouse_mode is MouseMode.CLIPPER and self.clipper_vertices:
            self.preview_poly_point = point
            self._redraw_all()

    def _on_canvas_right_click(self, event: tk.Event):
        if self.mouse_mode is MouseMode.CLIPPER:
            self._close_clipper()
            return

        self._clear_mouse_state()
        self._redraw_all()
        self._update_status("Режим мыши отменен.")

    def _add_segment(self, first: Point, second: Point):
        if isclose(first.x, second.x, abs_tol=EPS) and isclose(first.y, second.y, abs_tol=EPS):
            messagebox.showwarning(
                "Некорректный отрезок",
                "Концы отрезка не должны совпадать.",
            )
            return

        self.segments.append(Segment(first, second))
        self._clear_result()
        self._redraw_all()
        self._update_status(
            f"Добавлен отрезок: ({first.x:.0f}, {first.y:.0f}) - ({second.x:.0f}, {second.y:.0f})."
        )

    def _add_segment_from_entries(self):
        try:
            first, second = self._segment_from_vars()
        except ValueError as exc:
            messagebox.showwarning("Неверные координаты", str(exc))
            return

        self._add_segment(first, second)

    def _add_horizontal_segment(self):
        try:
            first, second = self._segment_from_vars()
        except ValueError as exc:
            messagebox.showwarning("Неверные координаты", str(exc))
            return

        self._add_segment(first, Point(second.x, first.y))

    def _add_vertical_segment(self):
        try:
            first, second = self._segment_from_vars()
        except ValueError as exc:
            messagebox.showwarning("Неверные координаты", str(exc))
            return

        self._add_segment(first, Point(first.x, second.y))

    def _add_parallel_segment(self):
        if not self.clipper_closed:
            messagebox.showwarning(
                "Невозможно добавить",
                "Сначала задайте и замкните отсекатель.",
            )
            return

        try:
            first, second = self._segment_from_vars()
            side_index = int(self.parallel_side_var.get()) - 1
        except ValueError:
            messagebox.showwarning(
                "Неверные данные",
                "Сторона должна быть целым числом, координаты - числами.",
            )
            return

        n = len(self.clipper_vertices)
        if side_index < 0 or side_index >= n:
            messagebox.showwarning(
                "Неверная сторона",
                f"Введите номер стороны от 1 до {n}.",
            )
            return

        side_start = self.clipper_vertices[side_index]
        side_end = self.clipper_vertices[(side_index + 1) % n]
        direction = vec_sub(side_end, side_start)
        side_len = length(direction)
        req_len = length(vec_sub(second, first))

        if side_len < EPS or req_len < EPS:
            messagebox.showwarning(
                "Некорректный отрезок",
                "Нулевая длина не поддерживается.",
            )
            return

        unit = vec_mul(direction, 1.0 / side_len)
        new_end = Point(first.x + unit.x * req_len, first.y + unit.y * req_len)
        self._add_segment(first, new_end)

    def _clip_segment_cyrus_beck(self, segment: Segment) -> Segment | None:
        if not self.clipper_closed:
            return None

        vertices = self.clipper_vertices
        d = vec_sub(segment.end, segment.start)

        orientation = self._polygon_orientation(vertices)
        ccw = orientation > 0

        t_enter = 0.0
        t_leave = 1.0

        for i in range(len(vertices)):
            p_i = vertices[i]
            p_j = vertices[(i + 1) % len(vertices)]
            edge = vec_sub(p_j, p_i)

            if ccw:
                normal = Point(edge.y, -edge.x)
            else:
                normal = Point(-edge.y, edge.x)

            w = vec_sub(segment.start, p_i)
            d_dot_n = dot(d, normal)
            w_dot_n = dot(w, normal)

            if abs(d_dot_n) < EPS:
                if w_dot_n > EPS:
                    return None
                continue

            t = -w_dot_n / d_dot_n
            if d_dot_n < 0:
                if t > t_enter:
                    t_enter = t
            else:
                if t < t_leave:
                    t_leave = t

            if t_enter - t_leave > EPS:
                return None

        start = Point(
            segment.start.x + d.x * t_enter,
            segment.start.y + d.y * t_enter,
        )
        end = Point(
            segment.start.x + d.x * t_leave,
            segment.start.y + d.y * t_leave,
        )
        return Segment(start, end)

    def _clip_all_segments(self):
        if not self.clipper_closed:
            messagebox.showwarning(
                "Невозможно отсечь",
                "Сначала задайте и замкните выпуклый отсекатель.",
            )
            return

        if not self.segments:
            messagebox.showwarning("Невозможно отсечь", "Сначала добавьте отрезки.")
            return

        self.clipped_segments.clear()
        for segment in self.segments:
            clipped = self._clip_segment_cyrus_beck(segment)
            if clipped is not None:
                self.clipped_segments.append(clipped)

        self._redraw_all()
        self._update_status(
            f"Отсечение выполнено: {len(self.clipped_segments)} из {len(self.segments)} отрезков внутри."
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

    def _draw_clipper(self):
        if not self.clipper_vertices:
            return

        points = []
        for v in self.clipper_vertices:
            points.extend((v.x, v.y))

        if len(self.clipper_vertices) == 1:
            v = self.clipper_vertices[0]
            self.canvas.create_oval(v.x - 2, v.y - 2, v.x + 2, v.y + 2, fill=self.clipper_color)
            return

        if self.clipper_closed:
            self.canvas.create_polygon(
                points,
                outline=self.clipper_color,
                fill="",
                width=2,
            )
        else:
            self.canvas.create_line(*points, fill=self.clipper_color, width=2)

        for idx, v in enumerate(self.clipper_vertices, start=1):
            self.canvas.create_oval(v.x - 3, v.y - 3, v.x + 3, v.y + 3, fill=self.clipper_color)
            self.canvas.create_text(v.x + 10, v.y - 10, text=str(idx), fill=self.clipper_color)

        if (
            self.mouse_mode is MouseMode.CLIPPER
            and self.preview_poly_point is not None
            and self.clipper_vertices
            and not self.clipper_closed
        ):
            last = self.clipper_vertices[-1]
            self.canvas.create_line(
                last.x,
                last.y,
                self.preview_poly_point.x,
                self.preview_poly_point.y,
                fill="#7DD3FC",
                width=2,
                dash=(6, 3),
            )

    def _redraw_all(self):
        self.canvas.delete("all")

        for segment in self.segments:
            self._draw_segment(segment, self.segment_color, width=2)

        self._draw_clipper()

        for segment in self.clipped_segments:
            self._draw_segment(segment, self.result_color, width=4)

        if self.preview_segment is not None:
            self._draw_segment(self.preview_segment, "#7DD3FC", width=2, dash=(6, 3))

    def _clear_result(self):
        self.clipped_segments.clear()
        self._redraw_all()

    def _clear_clipper(self):
        self.clipper_vertices.clear()
        self.clipper_closed = False
        self._clear_result()
        self._clear_mouse_state()
        self._update_clipper_info()
        self._redraw_all()
        self._update_status("Отсекатель очищен.")

    def _clear_all(self):
        self.clipper_vertices.clear()
        self.clipper_closed = False
        self.segments.clear()
        self.clipped_segments.clear()
        self._clear_mouse_state()
        self._update_clipper_info()
        self._redraw_all()
        self._update_status("Холст очищен.")


if __name__ == "__main__":
    root = tk.Tk()
    app = Lab08App(root)
    root.mainloop()
