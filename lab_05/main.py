import math
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import colorchooser, messagebox

from utils import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    FILL_STEP_MESSAGES,
    FillStep,
    InteractionMode,
    LEFT_PANEL_WIDTH,
    Point,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


@dataclass(frozen=True)
class Edge:
    x0: int
    y0: int
    x1: int
    y1: int


@dataclass
class FillRuntime:
    edges: list[Edge]
    min_y: int
    max_y: int
    current_y: int


class Lab05App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Lab 05 - Заполнение со списком ребер и флагом")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        self.fill_color = "#FF0000"
        self.mode = InteractionMode.EDITING
        self.step_index = 0
        self.step_plan: list[FillStep] = []
        self.fill_runtime: FillRuntime | None = None

        self.contours: list[list[Point]] = []
        self.current_contour: list[Point] = []
        self.segment_ids: list[int] = []
        self.vertex_ids: list[int] = []

        self._build_layout()
        self._bind_events()
        self._update_status("Кликайте по холсту для ввода вершин.")

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

        self.btn_fill = tk.Button(
            self.left_frame,
            text="Закрасить",
            command=self._fill_immediately,
            bg="#FFD8A8",
            cursor="hand2",
        )
        self.btn_fill.pack(fill="x", pady=(0, 8))

        self.btn_fill_step = tk.Button(
            self.left_frame,
            text="Закрасить по шагам",
            command=self._start_step_mode,
            bg="#FFD8A8",
            cursor="hand2",
        )
        self.btn_fill_step.pack(fill="x", pady=(0, 8))

        self.btn_clear = tk.Button(
            self.left_frame,
            text="Очистить",
            command=self._clear_canvas,
            bg="#FFCCCC",
            cursor="hand2",
        )
        self.btn_clear.pack(fill="x")

        self.step_frame = tk.LabelFrame(
            self.left_frame,
            text="Пошаговая заливка",
            padx=8,
            pady=8,
        )
        self.btn_next_step = tk.Button(
            self.step_frame,
            text="Дальше",
            command=self._next_step,
            cursor="hand2",
        )
        self.btn_exit_step = tk.Button(
            self.step_frame,
            text="Выход",
            command=self._exit_step_mode,
            cursor="hand2",
        )
        self.btn_next_step.pack(fill="x", pady=(0, 6))
        self.btn_exit_step.pack(fill="x")

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
            bg="#111111",
            highlightthickness=1,
            highlightbackground="#555555",
            cursor="crosshair",
        )
        self.canvas.pack(fill="both", expand=True)

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self._on_canvas_click)

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

    def _draw_segment(self, start: Point, end: Point):
        segment_id = self.canvas.create_line(
            start.x,
            start.y,
            end.x,
            end.y,
            fill="#FFFFFF",
            width=2,
            tags=("geometry",),
        )
        self.segment_ids.append(segment_id)

    def _on_canvas_click(self, event: tk.Event):
        if self.mode is InteractionMode.STEP_FILL:
            self._update_status(
                "Пошаговый режим активен. Нажмите 'Выход', чтобы редактировать контуры."
            )
            return

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
        if self.mode is InteractionMode.STEP_FILL:
            self._update_status("Нельзя замкнуть контур в пошаговом режиме.")
            return

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

    def _all_closed_contours(self) -> list[list[Point]]:
        return self.contours.copy()

    def _build_edges(self) -> list[Edge]:
        edges: list[Edge] = []
        for contour in self.contours:
            if len(contour) < 2:
                continue

            for index, start in enumerate(contour):
                end = contour[(index + 1) % len(contour)]
                if start.y == end.y:
                    continue

                if start.y < end.y:
                    edges.append(Edge(start.x, start.y, end.x, end.y))
                else:
                    edges.append(Edge(end.x, end.y, start.x, start.y))

        return edges

    def _scanline_intersections(self, y: int, edges: list[Edge]) -> list[float]:
        intersections: list[float] = []
        for edge in edges:
            if not (edge.y0 <= y < edge.y1):
                continue

            dy = edge.y1 - edge.y0
            if dy == 0:
                continue

            x = edge.x0 + (y - edge.y0) * (edge.x1 - edge.x0) / dy
            intersections.append(x)

        intersections.sort()
        return intersections

    def _paint_fill_pixel(self, x: int, y: int):
        self.canvas.create_rectangle(
            x,
            y,
            x + 1,
            y + 1,
            fill=self.fill_color,
            outline=self.fill_color,
            width=0,
            tags=("fill",),
        )

    def _paint_scanline(self, y: int) -> tuple[list[float], list[tuple[int, int]]]:
        if self.fill_runtime is None:
            return [], []

        intersections = self._scanline_intersections(y, self.fill_runtime.edges)
        painted_ranges: list[tuple[int, int]] = []

        for index in range(0, len(intersections) - 1, 2):
            left = intersections[index]
            right = intersections[index + 1]
            start_x = math.ceil(left)
            end_x = math.floor(right)

            if end_x < start_x:
                continue

            painted_ranges.append((start_x, end_x))
            for x in range(start_x, end_x + 1):
                self._paint_fill_pixel(x, y)

        self.canvas.tag_raise("geometry")
        return intersections, painted_ranges

    def _format_ranges(self, ranges: list[tuple[int, int]]) -> str:
        if not ranges:
            return "нет интервалов"

        parts = [f"[{start}, {end}]" for start, end in ranges]
        return ", ".join(parts)

    def _prepare_fill_runtime(self):
        edges = self._build_edges()
        if not edges:
            self.fill_runtime = None
            return

        ys = [point.y for contour in self.contours for point in contour]
        min_y = min(ys)
        max_y = max(ys)
        self.fill_runtime = FillRuntime(
            edges=edges,
            min_y=min_y,
            max_y=max_y,
            current_y=min_y,
        )

    def _reset_fill_layer(self):
        self.canvas.delete("fill")

    def _fill_all_scanlines(self) -> float:
        self._reset_fill_layer()
        self._prepare_fill_runtime()
        if self.fill_runtime is None:
            return 0.0

        start_time = time.perf_counter()
        for y in range(self.fill_runtime.min_y, self.fill_runtime.max_y):
            self._paint_scanline(y)
        self.canvas.update_idletasks()
        return (time.perf_counter() - start_time) * 1000.0

    def _fill_immediately(self):
        if self.current_contour:
            messagebox.showwarning(
                "Контур не замкнут",
                "Сначала замкните текущий контур кнопкой 'Замкнуть'.",
            )
            return

        if not self._all_closed_contours():
            messagebox.showwarning(
                "Нет данных",
                "Сначала задайте хотя бы один замкнутый контур.",
            )
            return

        self.mode = InteractionMode.EDITING
        self.step_frame.pack_forget()
        self._set_edit_controls_state("normal")

        duration_ms = self._fill_all_scanlines()
        if self.fill_runtime is None:
            messagebox.showwarning(
                "Нечего закрашивать",
                "Не удалось построить список ребер для заливки.",
            )
            return

        messagebox.showinfo(
            "Результат заливки",
            f"Заливка завершена. Время выполнения: {duration_ms:.2f} мс",
        )
        self._update_status("Инстантная заливка выполнена.")

    def _build_step_plan(self):
        self.step_plan = [
            FillStep.BUILD_EDGE_LIST,
            FillStep.FIND_SCANLINE_RANGE,
        ]
        self.step_index = 0

    def _start_step_mode(self):
        if self.current_contour:
            messagebox.showwarning(
                "Контур не замкнут",
                "Сначала замкните текущий контур кнопкой 'Замкнуть'.",
            )
            return

        if not self.contours:
            messagebox.showwarning(
                "Нет данных",
                "Сначала задайте хотя бы один замкнутый контур.",
            )
            return

        self._reset_fill_layer()
        self._prepare_fill_runtime()
        if self.fill_runtime is None:
            messagebox.showwarning(
                "Нечего закрашивать",
                "Не удалось построить список ребер для заливки.",
            )
            return

        self.mode = InteractionMode.STEP_FILL
        self._set_edit_controls_state("disabled")
        self.step_frame.pack(fill="x", pady=(10, 0))
        self._build_step_plan()
        self.fill_runtime.current_y = self.fill_runtime.min_y
        self._update_status("Пошаговый режим включен. Нажмите 'Дальше'.")

    def _next_step(self):
        if self.mode is not InteractionMode.STEP_FILL:
            return

        if self.fill_runtime is None:
            self._update_status("Заливка не подготовлена.")
            return

        if self.step_index < len(self.step_plan):
            step = self.step_plan[self.step_index]
            if step is FillStep.BUILD_EDGE_LIST:
                self._update_status(
                    f"{FILL_STEP_MESSAGES[step]} Ребер: {len(self.fill_runtime.edges)}."
                )
            else:
                self._update_status(
                    f"{FILL_STEP_MESSAGES[step]} Диапазон: {self.fill_runtime.min_y}.."
                    f"{self.fill_runtime.max_y - 1}."
                )

            self.step_index += 1
            return

        if self.fill_runtime.current_y >= self.fill_runtime.max_y:
            self._update_status("Пошаговая заливка завершена.")
            return

        intersections, ranges = self._paint_scanline(self.fill_runtime.current_y)
        self._update_status(
            f"{FILL_STEP_MESSAGES[FillStep.NEXT_SCANLINE]} "
            f"y={self.fill_runtime.current_y}, "
            f"пересечений: {len(intersections)}, "
            f"интервалы: {self._format_ranges(ranges)}."
        )
        self.fill_runtime.current_y += 1

        self.canvas.update_idletasks()
        self.step_index += 1

    def _exit_step_mode(self):
        if self.mode is not InteractionMode.STEP_FILL:
            return

        self.mode = InteractionMode.EDITING
        self.step_frame.pack_forget()
        self._set_edit_controls_state("normal")
        self._reset_fill_layer()
        self.fill_runtime = None
        self._update_status(
            "Выход из пошагового режима. Можно продолжать ввод контуров."
        )

    def _set_edit_controls_state(self, state: str):
        self.btn_close.config(state=state)
        self.btn_fill.config(state=state)
        self.btn_fill_step.config(state=state)
        self.btn_clear.config(state=state)
        self.btn_choose_color.config(state=state)

    def _clear_canvas(self):
        if self.mode is InteractionMode.STEP_FILL:
            self._exit_step_mode()

        self.canvas.delete("all")
        self.contours.clear()
        self.current_contour.clear()
        self.segment_ids.clear()
        self.vertex_ids.clear()
        self.fill_runtime = None
        self._update_status("Холст очищен. Начните ввод вершин заново.")


if __name__ == "__main__":
    root = tk.Tk()
    app = Lab05App(root)
    root.mainloop()
