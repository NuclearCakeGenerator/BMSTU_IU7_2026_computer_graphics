import time
import tkinter as tk
from tkinter import colorchooser, messagebox

from utils import (
    BACKGROUND_COLOR,
    BOUNDARY_COLOR,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    DEFAULT_DELAY_MS,
    LEFT_PANEL_WIDTH,
    MAX_DELAY_MS,
    Point,
    SEED_MARKER_COLOR,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


class Lab06App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Lab 06 - Построчное затравочное заполнение")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        self.fill_color = "#FF0000"

        self.contours: list[list[Point]] = []
        self.current_contour: list[Point] = []

        self.boundary_pixels: set[tuple[int, int]] = set()
        self.filled_pixels: set[tuple[int, int]] = set()

        self.seed_point: Point | None = None
        self.seed_marker_id: int | None = None

        self.segment_ids: list[int] = []
        self.vertex_ids: list[int] = []

        self._build_layout()
        self._bind_events()
        self._update_status(
            "ЛКМ: вершины. ПКМ: затравка. Затем замкните контур и запустите заливку."
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

        tk.Label(self.left_frame, text="Цвет заливки:").pack(anchor="w")

        self.color_row = tk.Frame(self.left_frame)
        self.color_row.pack(fill="x", pady=(4, 10))

        self.color_preview = tk.Label(
            self.color_row,
            text="      ",
            bg=self.fill_color,
            relief="sunken",
            borderwidth=1,
        )
        self.color_preview.pack(side="left")

        self.color_label = tk.Label(self.color_row, text=self.fill_color)
        self.color_label.pack(side="left", padx=8)

        self.btn_choose_color = tk.Button(
            self.left_frame,
            text="Выбрать цвет",
            command=self._choose_fill_color,
            cursor="hand2",
        )
        self.btn_choose_color.pack(fill="x", pady=(0, 12))

        self.hint_frame = tk.LabelFrame(
            self.left_frame,
            text="Подсказки",
            padx=8,
            pady=8,
        )
        self.hint_frame.pack(fill="x", pady=(0, 10))

        hints = [
            "ЛКМ: добавить вершину",
            "Shift + клик: горизонталь",
            "Ctrl + клик: вертикаль",
            "Shift + Ctrl: авто H/V",
            "ПКМ: установить затравку",
            "Кнопка 'Замкнуть': закрыть контур",
        ]
        for text in hints:
            tk.Label(self.hint_frame, text=text, anchor="w").pack(fill="x")

        self.btn_close = tk.Button(
            self.left_frame,
            text="Замкнуть",
            command=self._close_current_contour,
            bg="#CBF2C6",
            cursor="hand2",
        )
        self.btn_close.pack(fill="x", pady=(0, 8))

        self.btn_fill_fast = tk.Button(
            self.left_frame,
            text="Закрасить без задержки",
            command=self._fill_without_delay,
            bg="#FFD8A8",
            cursor="hand2",
        )
        self.btn_fill_fast.pack(fill="x", pady=(0, 8))

        self.delay_row = tk.Frame(self.left_frame)
        self.delay_row.pack(fill="x", pady=(0, 6))

        tk.Label(self.delay_row, text="Задержка, мс:").pack(side="left")
        self.delay_var = tk.IntVar(value=DEFAULT_DELAY_MS)
        self.delay_spin = tk.Spinbox(
            self.delay_row,
            from_=1,
            to=MAX_DELAY_MS,
            width=6,
            textvariable=self.delay_var,
            justify="right",
        )
        self.delay_spin.pack(side="right")

        self.btn_fill_delay = tk.Button(
            self.left_frame,
            text="Закрасить с задержкой",
            command=self._fill_with_delay,
            bg="#FFD8A8",
            cursor="hand2",
        )
        self.btn_fill_delay.pack(fill="x", pady=(0, 8))

        self.btn_clear_fill = tk.Button(
            self.left_frame,
            text="Стереть только заливку",
            command=self._reset_fill_layer,
            cursor="hand2",
        )
        self.btn_clear_fill.pack(fill="x", pady=(0, 8))

        self.btn_clear = tk.Button(
            self.left_frame,
            text="Очистить все",
            command=self._clear_canvas,
            bg="#FFCCCC",
            cursor="hand2",
        )
        self.btn_clear.pack(fill="x")

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

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self._on_canvas_left_click)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)

    def _update_status(self, text: str):
        self.status_var.set(text)

    def _choose_fill_color(self):
        color = colorchooser.askcolor(
            title="Выберите цвет заливки",
            color=self.fill_color,
        )[1]
        if color is None:
            return

        self.fill_color = color.upper()
        self.color_preview.config(bg=self.fill_color)
        self.color_label.config(text=self.fill_color)
        self._update_status(f"Цвет заливки: {self.fill_color}")

    def _draw_vertex(self, point: Point):
        radius = 3
        vertex_id = self.canvas.create_oval(
            point.x - radius,
            point.y - radius,
            point.x + radius,
            point.y + radius,
            fill="#F5F5F5",
            outline="#F5F5F5",
            tags=("geometry",),
        )
        self.vertex_ids.append(vertex_id)

    def _rasterize_segment(self, start: Point, end: Point) -> list[tuple[int, int]]:
        x0 = start.x
        y0 = start.y
        x1 = end.x
        y1 = end.y

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1

        points: list[tuple[int, int]] = []
        err = dx - dy

        while True:
            points.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

        return points

    def _draw_segment(self, start: Point, end: Point):
        segment_id = self.canvas.create_line(
            start.x,
            start.y,
            end.x,
            end.y,
            fill=BOUNDARY_COLOR,
            width=1,
            tags=("geometry",),
        )
        self.segment_ids.append(segment_id)

        for px, py in self._rasterize_segment(start, end):
            if 0 <= px < CANVAS_WIDTH and 0 <= py < CANVAS_HEIGHT:
                self.boundary_pixels.add((px, py))

    def _on_canvas_left_click(self, event: tk.Event):
        if not (0 <= event.x < CANVAS_WIDTH and 0 <= event.y < CANVAS_HEIGHT):
            return

        new_point = Point(event.x, event.y)
        if self.current_contour:
            new_point = self._apply_snap(
                self.current_contour[-1],
                new_point,
                event.state,
            )
            self._draw_segment(self.current_contour[-1], new_point)

        self.current_contour.append(new_point)
        self._draw_vertex(new_point)
        self._update_status(
            f"Текущий контур: {len(self.current_contour)} вершин. "
            f"Замкнутых контуров: {len(self.contours)}."
        )

    def _on_canvas_right_click(self, event: tk.Event):
        if not (0 <= event.x < CANVAS_WIDTH and 0 <= event.y < CANVAS_HEIGHT):
            return

        self.seed_point = Point(event.x, event.y)
        self._draw_seed_marker()
        self._update_status(f"Затравка установлена: ({event.x}, {event.y}).")

    def _draw_seed_marker(self):
        if self.seed_marker_id is not None:
            self.canvas.delete(self.seed_marker_id)

        if self.seed_point is None:
            return

        marker_size = 4
        x = self.seed_point.x
        y = self.seed_point.y
        self.seed_marker_id = self.canvas.create_line(
            x - marker_size,
            y,
            x + marker_size,
            y,
            x,
            y - marker_size,
            x,
            y + marker_size,
            fill=SEED_MARKER_COLOR,
            width=2,
            tags=("seed", "geometry"),
        )

    def _apply_snap(self, previous: Point, current: Point, state: int) -> Point:
        shift_pressed = bool(state & 0x0001)
        ctrl_pressed = bool(state & 0x0004)

        if shift_pressed and ctrl_pressed:
            if abs(current.x - previous.x) >= abs(current.y - previous.y):
                return Point(current.x, previous.y)
            return Point(previous.x, current.y)

        if shift_pressed:
            return Point(current.x, previous.y)

        if ctrl_pressed:
            return Point(previous.x, current.y)

        return current

    def _close_current_contour(self):
        if len(self.current_contour) < 3:
            messagebox.showwarning(
                "Недостаточно вершин",
                "Нужно минимум 3 вершины для замыкания контура.",
            )
            return

        self._draw_segment(self.current_contour[-1], self.current_contour[0])
        self.contours.append(self.current_contour.copy())
        self.current_contour.clear()
        self._update_status(
            f"Контур замкнут. Всего замкнутых контуров: {len(self.contours)}."
        )

    def _reset_fill_layer(self):
        self.canvas.delete("fill")
        self.filled_pixels.clear()
        self.canvas.tag_raise("geometry")
        if self.seed_point is not None:
            self._draw_seed_marker()

    def _is_fillable(self, x: int, y: int) -> bool:
        if not (0 <= x < CANVAS_WIDTH and 0 <= y < CANVAS_HEIGHT):
            return False
        if (x, y) in self.boundary_pixels:
            return False
        if (x, y) in self.filled_pixels:
            return False
        return True

    def _paint_span(self, left: int, right: int, y: int):
        if right < left:
            return

        self.canvas.create_line(
            left,
            y,
            right,
            y,
            fill=self.fill_color,
            width=1,
            tags=("fill",),
        )

        for x in range(left, right + 1):
            self.filled_pixels.add((x, y))

    def _find_new_seeds_in_row(
        self,
        left: int,
        right: int,
        y: int,
        stack: list[tuple[int, int]],
    ):
        x = left
        while x <= right:
            while x <= right and not self._is_fillable(x, y):
                x += 1

            if x > right:
                break

            start_x = x
            while x <= right and self._is_fillable(x, y):
                x += 1

            seed_x = (start_x + (x - 1)) // 2
            stack.append((seed_x, y))

    def _scanline_seed_fill(self, delay_ms: int = 0) -> tuple[float, int]:
        if self.seed_point is None:
            raise ValueError("Сначала установите затравку (ПКМ по холсту).")

        if not self.contours:
            raise ValueError("Сначала задайте и замкните хотя бы один контур.")

        seed = (self.seed_point.x, self.seed_point.y)
        if seed in self.boundary_pixels:
            raise ValueError("Затравка не должна лежать на границе контура.")

        self._reset_fill_layer()

        stack: list[tuple[int, int]] = [seed]
        filled_scanlines = 0
        start_time = time.perf_counter()

        while stack:
            x, y = stack.pop()
            if not self._is_fillable(x, y):
                continue

            xl = x
            while self._is_fillable(xl - 1, y):
                xl -= 1

            xr = x
            while self._is_fillable(xr + 1, y):
                xr += 1

            self._paint_span(xl, xr, y)
            filled_scanlines += 1

            up_y = y - 1
            down_y = y + 1
            if up_y >= 0:
                self._find_new_seeds_in_row(xl, xr, up_y, stack)
            if down_y < CANVAS_HEIGHT:
                self._find_new_seeds_in_row(xl, xr, down_y, stack)

            if delay_ms > 0:
                self.canvas.update()
                time.sleep(delay_ms / 1000.0)

        self.canvas.update_idletasks()
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return elapsed_ms, filled_scanlines

    def _fill_without_delay(self):
        try:
            elapsed_ms, filled_scanlines = self._scanline_seed_fill(delay_ms=0)
        except ValueError as exc:
            messagebox.showwarning("Невозможно выполнить заливку", str(exc))
            return

        self._update_status(
            f"Заливка без задержки завершена. Строк: {filled_scanlines}."
        )
        messagebox.showinfo(
            "Результат заливки",
            f"Заливка завершена. Время выполнения: {elapsed_ms:.2f} мс",
        )

    def _fill_with_delay(self):
        try:
            delay_ms = int(self.delay_var.get())
        except (tk.TclError, ValueError):
            messagebox.showwarning(
                "Неверная задержка",
                f"Введите число от 1 до {MAX_DELAY_MS} мс.",
            )
            return

        if delay_ms < 1 or delay_ms > MAX_DELAY_MS:
            messagebox.showwarning(
                "Неверная задержка",
                f"Введите число от 1 до {MAX_DELAY_MS} мс.",
            )
            return

        try:
            elapsed_ms, filled_scanlines = self._scanline_seed_fill(delay_ms=delay_ms)
        except ValueError as exc:
            messagebox.showwarning("Невозможно выполнить заливку", str(exc))
            return

        self._update_status(
            f"Заливка с задержкой {delay_ms} мс завершена. Строк: {filled_scanlines}."
        )

    def _clear_canvas(self):
        self.canvas.delete("all")

        self.contours.clear()
        self.current_contour.clear()

        self.boundary_pixels.clear()
        self.filled_pixels.clear()

        self.seed_point = None
        self.seed_marker_id = None

        self.segment_ids.clear()
        self.vertex_ids.clear()

        self._update_status("Холст очищен. Начните ввод заново.")


if __name__ == "__main__":
    root = tk.Tk()
    app = Lab06App(root)
    root.mainloop()
