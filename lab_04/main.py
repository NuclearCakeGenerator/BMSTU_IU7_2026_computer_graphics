import math
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import colorchooser, messagebox, ttk
from typing import Callable

from PIL import Image, ImageDraw

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 920
CANVAS_WIDTH = 920
CANVAS_HEIGHT = 860


@dataclass(frozen=True)
class Pixel:
    x: int
    y: int


def normalize_hex(color: str) -> str:
    value = color.strip()
    if not value.startswith("#"):
        raise ValueError("Color must be in #RRGGBB format")
    if len(value) != 7:
        raise ValueError("Color must be in #RRGGBB format")
    int(value[1:], 16)
    return value.upper()


def deduplicate(pixels: list[Pixel]) -> list[Pixel]:
    return list(set(pixels))


def _plot_circle_points(cx: int, cy: int, x: int, y: int) -> list[Pixel]:
    return [
        Pixel(cx + x, cy + y),
        Pixel(cx + x, cy - y),
        Pixel(cx - x, cy + y),
        Pixel(cx - x, cy - y),
        Pixel(cx + y, cy + x),
        Pixel(cx + y, cy - x),
        Pixel(cx - y, cy + x),
        Pixel(cx - y, cy - x),
    ]


def _plot_ellipse_points(cx: int, cy: int, x: int, y: int) -> list[Pixel]:
    return [
        Pixel(cx + x, cy + y),
        Pixel(cx + x, cy - y),
        Pixel(cx - x, cy + y),
        Pixel(cx - x, cy - y),
    ]


def circle_canonical(cx: int, cy: int, r: int) -> list[Pixel]:
    if r < 0:
        return []
    if r == 0:
        return [Pixel(cx, cy)]

    pixels: list[Pixel] = []
    edge = int(round(r / math.sqrt(2)))
    r_sq = r * r

    for x in range(0, edge + 1):
        y = int(round(math.sqrt(max(0.0, r_sq - x * x))))
        pixels.extend(_plot_circle_points(cx, cy, x, y))
    return deduplicate(pixels)


def circle_parametric(cx: int, cy: int, r: int) -> list[Pixel]:
    if r < 0:
        return []
    if r == 0:
        return [Pixel(cx, cy)]

    pixels: list[Pixel] = []
    step = 1.0 / max(1, r)
    t = 0.0
    limit = math.pi / 4
    while t <= limit + 1e-9:
        x = int(round(r * math.cos(t)))
        y = int(round(r * math.sin(t)))
        pixels.extend(_plot_circle_points(cx, cy, x, y))
        t += step
    return deduplicate(pixels)


def circle_bresenham(cx: int, cy: int, r: int) -> list[Pixel]:
    if r < 0:
        return []
    if r == 0:
        return [Pixel(cx, cy)]

    x = 0
    y = r
    d = 2 * (1 - r)
    pixels: list[Pixel] = []

    while y >= x:
        pixels.extend(_plot_circle_points(cx, cy, x, y))
        if d < 0:
            d1 = 2 * d + 2 * y - 1
            x += 1
            if d1 <= 0:
                d += 2 * x + 1
            else:
                y -= 1
                d += 2 * (x - y + 1)
        elif d > 0:
            d2 = 2 * d - 2 * x - 1
            y -= 1
            if d2 > 0:
                d += -2 * y + 1
            else:
                x += 1
                d += 2 * (x - y + 1)
        else:
            x += 1
            y -= 1
            d += 2 * (x - y + 1)

    return deduplicate(pixels)


def circle_midpoint(cx: int, cy: int, r: int) -> list[Pixel]:
    if r < 0:
        return []
    if r == 0:
        return [Pixel(cx, cy)]

    x = 0
    y = r
    d = 1 - r
    pixels: list[Pixel] = []

    while x <= y:
        pixels.extend(_plot_circle_points(cx, cy, x, y))
        x += 1
        if d < 0:
            d += 2 * x + 1
        else:
            y -= 1
            d += 2 * (x - y) + 1

    return deduplicate(pixels)


def circle_library(cx: int, cy: int, r: int) -> list[Pixel]:
    if r < 0:
        return []
    size = 2 * r + 3
    image = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(image)
    draw.ellipse((1, 1, size - 2, size - 2), outline=255)
    pixels: list[Pixel] = []
    for y in range(size):
        for x in range(size):
            if image.getpixel((x, y)) > 0:
                px = cx + x - (r + 1)
                py = cy + y - (r + 1)
                pixels.append(Pixel(px, py))
    return pixels


def ellipse_canonical(cx: int, cy: int, a: int, b: int) -> list[Pixel]:
    if a < 0 or b < 0:
        return []
    if a == 0 and b == 0:
        return [Pixel(cx, cy)]

    if a == 0:
        return [Pixel(cx, cy + y) for y in range(-b, b + 1)]
    if b == 0:
        return [Pixel(cx + x, cy) for x in range(-a, a + 1)]

    pixels: list[Pixel] = []
    a_sq = a * a
    b_sq = b * b

    edge_x = int(round(a_sq / math.sqrt(a_sq + b_sq)))
    for x in range(0, edge_x + 1):
        y = int(round(math.sqrt(max(0.0, (1 - x * x / a_sq) * b_sq))))
        pixels.extend(_plot_ellipse_points(cx, cy, x, y))

    edge_y = int(round(b_sq / math.sqrt(a_sq + b_sq)))
    for y in range(edge_y, -1, -1):
        x = int(round(math.sqrt(max(0.0, (1 - y * y / b_sq) * a_sq))))
        pixels.extend(_plot_ellipse_points(cx, cy, x, y))

    return deduplicate(pixels)


def ellipse_parametric(cx: int, cy: int, a: int, b: int) -> list[Pixel]:
    if a < 0 or b < 0:
        return []
    if a == 0 and b == 0:
        return [Pixel(cx, cy)]

    if a == 0:
        return [Pixel(cx, cy + y) for y in range(-b, b + 1)]
    if b == 0:
        return [Pixel(cx + x, cy) for x in range(-a, a + 1)]

    pixels: list[Pixel] = []
    step = 1.0 / max(a, b)
    t = 0.0
    limit = math.pi / 2
    while t <= limit + 1e-9:
        x = int(round(a * math.cos(t)))
        y = int(round(b * math.sin(t)))
        pixels.extend(_plot_ellipse_points(cx, cy, x, y))
        t += step
    return deduplicate(pixels)


def ellipse_bresenham(cx: int, cy: int, a: int, b: int) -> list[Pixel]:
    if a < 0 or b < 0:
        return []
    if a == 0 and b == 0:
        return [Pixel(cx, cy)]

    if a == 0:
        return [Pixel(cx, cy + y) for y in range(-b, b + 1)]
    if b == 0:
        return [Pixel(cx + x, cy) for x in range(-a, a + 1)]

    x = 0
    y = b
    a_sq = a * a
    b_sq = b * b
    d = b_sq - a_sq * (2 * b - 1)

    pixels: list[Pixel] = []
    while y >= 0:
        pixels.extend(_plot_ellipse_points(cx, cy, x, y))

        if d < 0:
            d1 = 2 * d + a_sq * (2 * y - 1)
            x += 1
            if d1 <= 0:
                d += b_sq * (2 * x + 1)
            else:
                y -= 1
                d += b_sq * (2 * x + 1) + a_sq * (1 - 2 * y)
        elif d > 0:
            d2 = 2 * d + b_sq * (-2 * x - 1)
            y -= 1
            if d2 > 0:
                d += a_sq * (1 - 2 * y)
            else:
                x += 1
                d += b_sq * (2 * x + 1) + a_sq * (1 - 2 * y)
        else:
            x += 1
            y -= 1
            d += b_sq * (2 * x + 1) + a_sq * (1 - 2 * y)

    return deduplicate(pixels)


def ellipse_midpoint(cx: int, cy: int, a: int, b: int) -> list[Pixel]:
    if a < 0 or b < 0:
        return []
    if a == 0 and b == 0:
        return [Pixel(cx, cy)]

    if a == 0:
        return [Pixel(cx, cy + y) for y in range(-b, b + 1)]
    if b == 0:
        return [Pixel(cx + x, cy) for x in range(-a, a + 1)]

    pixels: list[Pixel] = []
    x = 0
    y = b
    a_sq = float(a * a)
    b_sq = float(b * b)

    d1 = b_sq - a_sq * b + 0.25 * a_sq
    dx = 2 * b_sq * x
    dy = 2 * a_sq * y

    while dx < dy:
        pixels.extend(_plot_ellipse_points(cx, cy, x, y))
        x += 1
        dx = 2 * b_sq * x
        if d1 < 0:
            d1 += dx + b_sq
        else:
            y -= 1
            dy = 2 * a_sq * y
            d1 += dx - dy + b_sq

    d2 = b_sq * (x + 0.5) * (x + 0.5) + a_sq * (y - 1) * (y - 1) - a_sq * b_sq
    while y >= 0:
        pixels.extend(_plot_ellipse_points(cx, cy, x, y))
        y -= 1
        dy = 2 * a_sq * y
        if d2 > 0:
            d2 += a_sq - dy
        else:
            x += 1
            dx = 2 * b_sq * x
            d2 += dx - dy + a_sq

    return deduplicate(pixels)


def ellipse_library(cx: int, cy: int, a: int, b: int) -> list[Pixel]:
    if a < 0 or b < 0:
        return []
    w = 2 * a + 3
    h = 2 * b + 3
    image = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(image)
    draw.ellipse((1, 1, w - 2, h - 2), outline=255)
    pixels: list[Pixel] = []
    for y in range(h):
        for x in range(w):
            if image.getpixel((x, y)) > 0:
                px = cx + x - (a + 1)
                py = cy + y - (b + 1)
                pixels.append(Pixel(px, py))
    return pixels


class PlotCanvas:
    def __init__(self, parent: tk.Widget):
        self.canvas = tk.Canvas(
            parent,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg="#0F1115",
            highlightthickness=1,
            highlightbackground="#3A3A3A",
        )
        self.canvas.pack(fill="both", expand=True)
        self.image = tk.PhotoImage(width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
        self.canvas.create_image((0, 0), image=self.image, anchor="nw")
        self.bg_color = "#000000"
        self.clear(self.bg_color)

    def clear(self, bg_color: str):
        self.bg_color = bg_color
        self.image.put(bg_color, to=(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT))
        self.canvas.delete("overlay")
        self._draw_axes()

    def _draw_axes(self):
        cx = CANVAS_WIDTH // 2
        cy = CANVAS_HEIGHT // 2
        self.canvas.create_line(0, cy, CANVAS_WIDTH, cy, fill="#444444", tags="overlay")
        self.canvas.create_line(
            cx,
            0,
            cx,
            CANVAS_HEIGHT,
            fill="#444444",
            tags="overlay",
        )

    def put_pixel(self, x: int, y: int, color: str):
        sx = x + CANVAS_WIDTH // 2
        sy = CANVAS_HEIGHT // 2 - y
        if 0 <= sx < CANVAS_WIDTH and 0 <= sy < CANVAS_HEIGHT:
            self.image.put(color, (sx, sy))

    def draw_pixels(self, pixels: list[Pixel], color: str):
        for pixel in pixels:
            self.put_pixel(pixel.x, pixel.y, color)


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Computer Graphics Lab 4")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        self.circle_algorithms: dict[str, Callable[[int, int, int], list[Pixel]]] = {
            "Canonical": circle_canonical,
            "Parametric": circle_parametric,
            "Bresenham": circle_bresenham,
            "Midpoint": circle_midpoint,
            "Library (Pillow)": circle_library,
        }
        self.ellipse_algorithms: dict[
            str, Callable[[int, int, int, int], list[Pixel]]
        ] = {
            "Canonical": ellipse_canonical,
            "Parametric": ellipse_parametric,
            "Bresenham": ellipse_bresenham,
            "Midpoint": ellipse_midpoint,
            "Library (Pillow)": ellipse_library,
        }

        self.draw_color = "#00FF66"
        self.bg_color = "#000000"

        self._build_ui()

    def _build_ui(self):
        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True)

        controls = tk.Frame(main, width=450, padx=10, pady=10)
        controls.pack(side="left", fill="y")
        controls.pack_propagate(False)

        canvas_frame = tk.Frame(main, padx=10, pady=10)
        canvas_frame.pack(side="left", fill="both", expand=True)

        self.plot = PlotCanvas(canvas_frame)

        ttk.Label(controls, text="Colors", font=("Arial", 10, "bold")).pack(anchor="w")
        color_row = tk.Frame(controls)
        color_row.pack(fill="x", pady=4)

        tk.Button(color_row, text="Pick draw color", command=self.pick_draw_color).pack(
            side="left"
        )
        self.draw_color_preview = tk.Label(
            color_row, width=10, text=self.draw_color, bg=self.draw_color
        )
        self.draw_color_preview.pack(side="left", padx=6)

        tk.Button(color_row, text="Pick bg color", command=self.pick_bg_color).pack(
            side="left"
        )

        action_row = tk.Frame(controls)
        action_row.pack(fill="x", pady=6)
        tk.Button(
            action_row,
            text="Clear",
            command=self.clear_canvas,
            bg="#E8E8E8",
        ).pack(side="left", expand=True, fill="x", padx=2)

        notebook = ttk.Notebook(controls)
        notebook.pack(fill="both", expand=True, pady=(8, 0))

        self.tab_circle = tk.Frame(notebook, padx=8, pady=8)
        self.tab_ellipse = tk.Frame(notebook, padx=8, pady=8)
        self.tab_circle_spectrum = tk.Frame(notebook, padx=8, pady=8)
        self.tab_ellipse_spectrum = tk.Frame(notebook, padx=8, pady=8)
        self.tab_timing = tk.Frame(notebook, padx=8, pady=8)

        notebook.add(self.tab_circle, text="Single circle")
        notebook.add(self.tab_ellipse, text="Single ellipse")
        notebook.add(self.tab_circle_spectrum, text="Circle spectrum")
        notebook.add(self.tab_ellipse_spectrum, text="Ellipse spectrum")
        notebook.add(self.tab_timing, text="Timing")

        self._build_circle_tab()
        self._build_ellipse_tab()
        self._build_circle_spectrum_tab()
        self._build_ellipse_spectrum_tab()
        self._build_timing_tab()

        self.status = tk.StringVar(value="Ready")
        ttk.Label(
            controls,
            textvariable=self.status,
            wraplength=420,
            foreground="#003E99",
        ).pack(anchor="w", pady=(8, 0))

    def _pair_entries(
        self,
        parent: tk.Widget,
        left_label: str,
        left_default: str,
        right_label: str,
        right_default: str,
    ) -> tuple[tk.Entry, tk.Entry]:
        row = tk.Frame(parent)
        row.pack(fill="x", pady=3)
        left = tk.Frame(row)
        left.pack(side="left", fill="x", expand=True, padx=2)
        right = tk.Frame(row)
        right.pack(side="left", fill="x", expand=True, padx=2)

        ttk.Label(left, text=left_label).pack(anchor="w")
        e1 = tk.Entry(left)
        e1.insert(0, left_default)
        e1.pack(fill="x")

        ttk.Label(right, text=right_label).pack(anchor="w")
        e2 = tk.Entry(right)
        e2.insert(0, right_default)
        e2.pack(fill="x")
        return e1, e2

    def _single_entry(
        self, parent: tk.Widget, label: str, default: str = ""
    ) -> tk.Entry:
        frame = tk.Frame(parent)
        frame.pack(fill="x", pady=3)
        ttk.Label(frame, text=label).pack(anchor="w")
        entry = tk.Entry(frame)
        if default:
            entry.insert(0, default)
        entry.pack(fill="x")
        return entry

    def _build_circle_tab(self):
        ttk.Label(
            self.tab_circle,
            text="Circle params",
            font=("Arial", 10, "bold"),
        ).pack(anchor="w")
        self.circle_cx, self.circle_cy = self._pair_entries(
            self.tab_circle, "Center X", "0", "Center Y", "0"
        )
        self.circle_r = self._single_entry(self.tab_circle, "Radius", "120")

        ttk.Label(self.tab_circle, text="Algorithm").pack(anchor="w", pady=(6, 0))
        self.circle_algo = ttk.Combobox(
            self.tab_circle,
            state="readonly",
            values=list(self.circle_algorithms.keys()),
        )
        self.circle_algo.current(0)
        self.circle_algo.pack(fill="x")

        ttk.Label(self.tab_circle, text="Overlay algorithm (optional)").pack(
            anchor="w", pady=(6, 0)
        )
        self.circle_overlay = ttk.Combobox(
            self.tab_circle,
            state="readonly",
            values=["None"] + list(self.circle_algorithms.keys()),
        )
        self.circle_overlay.current(0)
        self.circle_overlay.pack(fill="x")

        tk.Button(
            self.tab_circle,
            text="Draw circle",
            command=self.draw_single_circle,
            bg="#A6FFBF",
        ).pack(fill="x", pady=8)

    def _build_ellipse_tab(self):
        ttk.Label(
            self.tab_ellipse, text="Ellipse params", font=("Arial", 10, "bold")
        ).pack(anchor="w")
        self.ellipse_cx, self.ellipse_cy = self._pair_entries(
            self.tab_ellipse, "Center X", "0", "Center Y", "0"
        )
        self.ellipse_a, self.ellipse_b = self._pair_entries(
            self.tab_ellipse, "Semi-axis a", "180", "Semi-axis b", "90"
        )

        ttk.Label(self.tab_ellipse, text="Algorithm").pack(anchor="w", pady=(6, 0))
        self.ellipse_algo = ttk.Combobox(
            self.tab_ellipse,
            state="readonly",
            values=list(self.ellipse_algorithms.keys()),
        )
        self.ellipse_algo.current(0)
        self.ellipse_algo.pack(fill="x")

        ttk.Label(self.tab_ellipse, text="Overlay algorithm (optional)").pack(
            anchor="w", pady=(6, 0)
        )
        self.ellipse_overlay = ttk.Combobox(
            self.tab_ellipse,
            state="readonly",
            values=["None"] + list(self.ellipse_algorithms.keys()),
        )
        self.ellipse_overlay.current(0)
        self.ellipse_overlay.pack(fill="x")

        tk.Button(
            self.tab_ellipse,
            text="Draw ellipse",
            command=self.draw_single_ellipse,
            bg="#A6FFBF",
        ).pack(fill="x", pady=8)

    def _build_circle_spectrum_tab(self):
        ttk.Label(
            self.tab_circle_spectrum,
            text="Three params required, leave one empty",
            font=("Arial", 9),
        ).pack(anchor="w")

        self.spec_circle_cx, self.spec_circle_cy = self._pair_entries(
            self.tab_circle_spectrum, "Center X", "0", "Center Y", "0"
        )

        self.spec_r_start, self.spec_r_end = self._pair_entries(
            self.tab_circle_spectrum, "Start radius", "20", "End radius", "220"
        )
        self.spec_r_step, self.spec_count = self._pair_entries(
            self.tab_circle_spectrum, "Radius step", "20", "Count", ""
        )

        ttk.Label(self.tab_circle_spectrum, text="Algorithm").pack(
            anchor="w", pady=(6, 0)
        )
        self.spec_circle_algo = ttk.Combobox(
            self.tab_circle_spectrum,
            state="readonly",
            values=list(self.circle_algorithms.keys()),
        )
        self.spec_circle_algo.current(2)
        self.spec_circle_algo.pack(fill="x")

        ttk.Label(self.tab_circle_spectrum, text="Overlay algorithm (optional)").pack(
            anchor="w", pady=(6, 0)
        )
        self.spec_circle_overlay = ttk.Combobox(
            self.tab_circle_spectrum,
            state="readonly",
            values=["None"] + list(self.circle_algorithms.keys()),
        )
        self.spec_circle_overlay.current(0)
        self.spec_circle_overlay.pack(fill="x")

        tk.Button(
            self.tab_circle_spectrum,
            text="Draw circle spectrum",
            command=self.draw_circle_spectrum,
            bg="#B6E3FF",
        ).pack(fill="x", pady=8)

    def _build_ellipse_spectrum_tab(self):
        ttk.Label(
            self.tab_ellipse_spectrum,
            text="Second axis scales with the first while drawing spectrum",
            font=("Arial", 9),
        ).pack(anchor="w")

        self.spec_ellipse_cx, self.spec_ellipse_cy = self._pair_entries(
            self.tab_ellipse_spectrum, "Center X", "0", "Center Y", "0"
        )
        self.spec_ellipse_a0, self.spec_ellipse_b0 = self._pair_entries(
            self.tab_ellipse_spectrum, "Start a", "40", "Start b", "20"
        )
        self.spec_ellipse_step, self.spec_ellipse_count = self._pair_entries(
            self.tab_ellipse_spectrum, "Step", "15", "Count", "12"
        )

        axis_frame = tk.Frame(self.tab_ellipse_spectrum)
        axis_frame.pack(fill="x", pady=4)
        ttk.Label(axis_frame, text="Primary axis").pack(anchor="w")
        self.spec_primary_axis = ttk.Combobox(
            axis_frame,
            state="readonly",
            values=["a", "b"],
        )
        self.spec_primary_axis.current(0)
        self.spec_primary_axis.pack(fill="x")

        ttk.Label(self.tab_ellipse_spectrum, text="Algorithm").pack(
            anchor="w", pady=(6, 0)
        )
        self.spec_ellipse_algo = ttk.Combobox(
            self.tab_ellipse_spectrum,
            state="readonly",
            values=list(self.ellipse_algorithms.keys()),
        )
        self.spec_ellipse_algo.current(2)
        self.spec_ellipse_algo.pack(fill="x")

        ttk.Label(self.tab_ellipse_spectrum, text="Overlay algorithm (optional)").pack(
            anchor="w", pady=(6, 0)
        )
        self.spec_ellipse_overlay = ttk.Combobox(
            self.tab_ellipse_spectrum,
            state="readonly",
            values=["None"] + list(self.ellipse_algorithms.keys()),
        )
        self.spec_ellipse_overlay.current(0)
        self.spec_ellipse_overlay.pack(fill="x")

        tk.Button(
            self.tab_ellipse_spectrum,
            text="Draw ellipse spectrum",
            command=self.draw_ellipse_spectrum,
            bg="#B6E3FF",
        ).pack(fill="x", pady=8)

    def _build_timing_tab(self):
        ttk.Label(
            self.tab_timing,
            text="Benchmark params",
            font=("Arial", 10, "bold"),
        ).pack(anchor="w")

        self.time_r_start, self.time_r_end = self._pair_entries(
            self.tab_timing, "Circle start R", "10", "Circle end R", "260"
        )
        self.time_r_step, self.time_repeats = self._pair_entries(
            self.tab_timing, "Radius step", "10", "Repeats", "80"
        )

        self.time_e_a0, self.time_e_b0 = self._pair_entries(
            self.tab_timing, "Ellipse start a", "20", "Ellipse start b", "12"
        )
        self.time_e_step, self.time_e_count = self._pair_entries(
            self.tab_timing, "Ellipse step", "8", "Ellipse count", "26"
        )

        axis_frame = tk.Frame(self.tab_timing)
        axis_frame.pack(fill="x", pady=4)
        ttk.Label(axis_frame, text="Ellipse varying axis").pack(anchor="w")
        self.time_primary_axis = ttk.Combobox(
            axis_frame,
            state="readonly",
            values=["a", "b"],
        )
        self.time_primary_axis.current(0)
        self.time_primary_axis.pack(fill="x")

        tk.Button(
            self.tab_timing,
            text="Timing: circle algorithms",
            command=self.research_timing_circles,
            bg="#FFE2A8",
        ).pack(fill="x", pady=4)
        tk.Button(
            self.tab_timing,
            text="Timing: ellipse algorithms",
            command=self.research_timing_ellipses,
            bg="#FFE2A8",
        ).pack(fill="x", pady=4)

    def pick_draw_color(self):
        selected = colorchooser.askcolor(
            color=self.draw_color,
            title="Choose draw color",
        )
        if selected[1]:
            self.draw_color = normalize_hex(selected[1])
            self.draw_color_preview.config(text=self.draw_color, bg=self.draw_color)

    def pick_bg_color(self):
        selected = colorchooser.askcolor(
            color=self.bg_color,
            title="Choose background color",
        )
        if selected[1]:
            self.bg_color = normalize_hex(selected[1])
            self.plot.clear(self.bg_color)

    def clear_canvas(self):
        self.plot.clear(self.bg_color)
        self.status.set("Canvas cleared")

    @staticmethod
    def _parse_int(value: str, title: str) -> int:
        try:
            return int(float(value))
        except ValueError as exc:
            raise ValueError(f"{title} must be numeric") from exc

    def _draw_circle_with_algo(
        self,
        algo_name: str,
        cx: int,
        cy: int,
        r: int,
        color: str,
    ):
        algo = self.circle_algorithms[algo_name]
        pixels = algo(cx, cy, r)
        self.plot.draw_pixels(pixels, color)

    def _draw_ellipse_with_algo(
        self, algo_name: str, cx: int, cy: int, a: int, b: int, color: str
    ):
        algo = self.ellipse_algorithms[algo_name]
        pixels = algo(cx, cy, a, b)
        self.plot.draw_pixels(pixels, color)

    def draw_single_circle(self):
        try:
            cx = self._parse_int(self.circle_cx.get(), "Center X")
            cy = self._parse_int(self.circle_cy.get(), "Center Y")
            r = self._parse_int(self.circle_r.get(), "Radius")
            if r < 0:
                raise ValueError("Radius must be >= 0")

            algo_name = self.circle_algo.get()
            overlay_name = self.circle_overlay.get()

            self._draw_circle_with_algo(algo_name, cx, cy, r, self.draw_color)
            if overlay_name != "None":
                self._draw_circle_with_algo(overlay_name, cx, cy, r, self.bg_color)

            self.status.set(
                f"Circle drawn by {algo_name}"
                + (" with overlay" if overlay_name != "None" else "")
            )
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc))

    def draw_single_ellipse(self):
        try:
            cx = self._parse_int(self.ellipse_cx.get(), "Center X")
            cy = self._parse_int(self.ellipse_cy.get(), "Center Y")
            a = self._parse_int(self.ellipse_a.get(), "Semi-axis a")
            b = self._parse_int(self.ellipse_b.get(), "Semi-axis b")
            if a < 0 or b < 0:
                raise ValueError("Semi-axes must be >= 0")

            algo_name = self.ellipse_algo.get()
            overlay_name = self.ellipse_overlay.get()

            self._draw_ellipse_with_algo(algo_name, cx, cy, a, b, self.draw_color)
            if overlay_name != "None":
                self._draw_ellipse_with_algo(overlay_name, cx, cy, a, b, self.bg_color)

            self.status.set(
                f"Ellipse drawn by {algo_name}"
                + (" with overlay" if overlay_name != "None" else "")
            )
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc))

    def _resolve_circle_spectrum_params(self) -> tuple[int, int, int, int]:
        values_raw = {
            "start": self.spec_r_start.get().strip(),
            "end": self.spec_r_end.get().strip(),
            "step": self.spec_r_step.get().strip(),
            "count": self.spec_count.get().strip(),
        }

        missing = [key for key, value in values_raw.items() if value == ""]
        if len(missing) > 1:
            raise ValueError("Leave at most one spectrum parameter empty")

        values: dict[str, int] = {}
        for key, value in values_raw.items():
            if value == "":
                continue
            values[key] = self._parse_int(value, key)

        if "start" in values and values["start"] < 0:
            raise ValueError("start radius must be >= 0")
        if "end" in values and values["end"] < 0:
            raise ValueError("end radius must be >= 0")
        if "step" in values and values["step"] <= 0:
            raise ValueError("step must be > 0")
        if "count" in values and values["count"] <= 0:
            raise ValueError("count must be > 0")

        if not missing:
            start = values["start"]
            end = values["end"]
            step = values["step"]
            count = values["count"]
            expected = start + step * (count - 1)
            if expected != end:
                raise ValueError("Provided parameters are inconsistent")
            return start, end, step, count

        miss = missing[0]
        start = values.get("start")
        end = values.get("end")
        step = values.get("step")
        count = values.get("count")

        if miss == "start":
            start = end - step * (count - 1)
        elif miss == "end":
            end = start + step * (count - 1)
        elif miss == "step":
            if count <= 1:
                step = 1
            else:
                diff = end - start
                if diff % (count - 1) != 0:
                    raise ValueError("(end - start) must be divisible by (count - 1)")
                step = diff // (count - 1)
        elif miss == "count":
            if step <= 0:
                raise ValueError("step must be > 0")
            diff = end - start
            if diff < 0 or diff % step != 0:
                raise ValueError(
                    "(end - start) must be non-negative and divisible by step"
                )
            count = diff // step + 1

        if start < 0 or end < 0 or step <= 0 or count <= 0:
            raise ValueError("Resolved spectrum parameters are invalid")
        if start > end:
            raise ValueError("start must be <= end")
        return start, end, step, count

    def draw_circle_spectrum(self):
        try:
            cx = self._parse_int(self.spec_circle_cx.get(), "Center X")
            cy = self._parse_int(self.spec_circle_cy.get(), "Center Y")
            start, end, step, count = self._resolve_circle_spectrum_params()

            algo_name = self.spec_circle_algo.get()
            overlay_name = self.spec_circle_overlay.get()

            radius = start
            for _ in range(count):
                self._draw_circle_with_algo(algo_name, cx, cy, radius, self.draw_color)
                if overlay_name != "None":
                    self._draw_circle_with_algo(
                        overlay_name,
                        cx,
                        cy,
                        radius,
                        self.bg_color,
                    )
                radius += step

            self.status.set(
                "Circle spectrum drawn "
                f"({algo_name}): start={start}, end={end}, count={count}"
            )
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc))

    def _ellipse_spectrum_sizes(
        self, a0: int, b0: int, step: int, count: int, primary_axis: str
    ) -> list[tuple[int, int]]:
        if a0 < 0 or b0 < 0:
            raise ValueError("Start semi-axes must be >= 0")
        if step <= 0:
            raise ValueError("Step must be > 0")
        if count <= 0:
            raise ValueError("Count must be > 0")
        if a0 == 0 and b0 == 0:
            return [(0, 0) for _ in range(count)]

        sizes: list[tuple[int, int]] = []
        for i in range(count):
            if primary_axis == "a":
                a = a0 + i * step
                scale = a / max(1, a0)
                b = int(round(b0 * scale)) if a0 > 0 else b0 + i * step
            else:
                b = b0 + i * step
                scale = b / max(1, b0)
                a = int(round(a0 * scale)) if b0 > 0 else a0 + i * step
            sizes.append((max(0, a), max(0, b)))
        return sizes

    def draw_ellipse_spectrum(self):
        try:
            cx = self._parse_int(self.spec_ellipse_cx.get(), "Center X")
            cy = self._parse_int(self.spec_ellipse_cy.get(), "Center Y")
            a0 = self._parse_int(self.spec_ellipse_a0.get(), "Start a")
            b0 = self._parse_int(self.spec_ellipse_b0.get(), "Start b")
            step = self._parse_int(self.spec_ellipse_step.get(), "Step")
            count = self._parse_int(self.spec_ellipse_count.get(), "Count")
            axis = self.spec_primary_axis.get()

            algo_name = self.spec_ellipse_algo.get()
            overlay_name = self.spec_ellipse_overlay.get()
            sizes = self._ellipse_spectrum_sizes(a0, b0, step, count, axis)

            for a, b in sizes:
                self._draw_ellipse_with_algo(algo_name, cx, cy, a, b, self.draw_color)
                if overlay_name != "None":
                    self._draw_ellipse_with_algo(
                        overlay_name,
                        cx,
                        cy,
                        a,
                        b,
                        self.bg_color,
                    )

            self.status.set(
                "Ellipse spectrum drawn "
                f"({algo_name}), count={count}, primary axis={axis}"
            )
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc))

    def _show_time_graph(
        self,
        title: str,
        x_label: str,
        y_label: str,
        series: dict[str, list[tuple[float, float]]],
    ):
        window = tk.Toplevel(self.root)
        window.title(title)
        chart = tk.Canvas(window, width=980, height=620, bg="#FFFFFF")
        chart.pack(fill="both", expand=True)

        margin_left = 80
        margin_right = 30
        margin_top = 45
        margin_bottom = 70

        plot_w = 980 - margin_left - margin_right
        plot_h = 620 - margin_top - margin_bottom

        chart.create_text(490, 20, text=title, font=("Arial", 12, "bold"))
        chart.create_line(
            margin_left,
            margin_top,
            margin_left,
            margin_top + plot_h,
            width=2,
            fill="#111111",
        )
        chart.create_line(
            margin_left,
            margin_top + plot_h,
            margin_left + plot_w,
            margin_top + plot_h,
            width=2,
            fill="#111111",
        )

        all_points = [point for points in series.values() for point in points]
        if not all_points:
            chart.create_text(490, 310, text="No data")
            return

        x_min = min(point[0] for point in all_points)
        x_max = max(point[0] for point in all_points)
        y_min = 0.0
        y_max = max(point[1] for point in all_points)
        if y_max == 0:
            y_max = 1.0

        def map_x(x: float) -> float:
            if x_max == x_min:
                return margin_left + plot_w / 2
            return margin_left + (x - x_min) / (x_max - x_min) * plot_w

        def map_y(y: float) -> float:
            return margin_top + plot_h - (y - y_min) / (y_max - y_min) * plot_h

        palette = ["#DC2626", "#2563EB", "#16A34A", "#CA8A04", "#9333EA"]
        for idx, (name, points) in enumerate(series.items()):
            color = palette[idx % len(palette)]
            line_points: list[float] = []
            for x, y in points:
                sx = map_x(x)
                sy = map_y(y)
                line_points.extend([sx, sy])
                chart.create_oval(
                    sx - 2,
                    sy - 2,
                    sx + 2,
                    sy + 2,
                    fill=color,
                    outline=color,
                )
            if len(line_points) >= 4:
                chart.create_line(*line_points, fill=color, width=2)

        for tick in range(6):
            xv = x_min + (x_max - x_min) * tick / 5 if x_max != x_min else x_min
            sx = map_x(xv)
            chart.create_line(sx, margin_top + plot_h, sx, margin_top + plot_h + 5)
            chart.create_text(sx, margin_top + plot_h + 18, text=f"{xv:.0f}")

            yv = y_min + (y_max - y_min) * tick / 5
            sy = map_y(yv)
            chart.create_line(margin_left - 5, sy, margin_left, sy)
            chart.create_text(margin_left - 36, sy, text=f"{yv:.1f}")

        chart.create_text(490, 590, text=x_label)
        chart.create_text(22, 310, text=y_label, angle=90)

        legend_x = margin_left + plot_w - 180
        legend_y = margin_top + 10
        for idx, name in enumerate(series.keys()):
            color = palette[idx % len(palette)]
            y = legend_y + idx * 22
            chart.create_line(legend_x, y, legend_x + 18, y, fill=color, width=3)
            chart.create_text(legend_x + 24, y, text=name, anchor="w")

    def research_timing_circles(self):
        try:
            r_start = self._parse_int(self.time_r_start.get(), "Circle start R")
            r_end = self._parse_int(self.time_r_end.get(), "Circle end R")
            r_step = self._parse_int(self.time_r_step.get(), "Radius step")
            repeats = self._parse_int(self.time_repeats.get(), "Repeats")
            if r_start < 0 or r_end < 0 or r_step <= 0 or repeats <= 0:
                raise ValueError(
                    "Timing params must be positive, with non-negative radii"
                )
            if r_end < r_start:
                raise ValueError("Circle end R must be >= start R")
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc))
            return

        radii = list(range(r_start, r_end + 1, r_step))
        series: dict[str, list[tuple[float, float]]] = {}
        for algo_name, algo in self.circle_algorithms.items():
            points: list[tuple[float, float]] = []
            for radius in radii:
                start = time.perf_counter_ns()
                for _ in range(repeats):
                    algo(0, 0, radius)
                elapsed_us = (time.perf_counter_ns() - start) / repeats / 1000.0
                points.append((float(radius), elapsed_us))
            series[algo_name] = points

        self._show_time_graph(
            title=f"Circle timing vs radius (repeats={repeats})",
            x_label="Radius",
            y_label="Time (microseconds)",
            series=series,
        )
        self.status.set("Circle timing research complete")

    def research_timing_ellipses(self):
        try:
            a0 = self._parse_int(self.time_e_a0.get(), "Ellipse start a")
            b0 = self._parse_int(self.time_e_b0.get(), "Ellipse start b")
            step = self._parse_int(self.time_e_step.get(), "Ellipse step")
            count = self._parse_int(self.time_e_count.get(), "Ellipse count")
            repeats = self._parse_int(self.time_repeats.get(), "Repeats")
            axis = self.time_primary_axis.get()
            sizes = self._ellipse_spectrum_sizes(a0, b0, step, count, axis)
            if repeats <= 0:
                raise ValueError("Repeats must be > 0")
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc))
            return

        series: dict[str, list[tuple[float, float]]] = {}
        for algo_name, algo in self.ellipse_algorithms.items():
            points: list[tuple[float, float]] = []
            for a, b in sizes:
                x_value = float(a if axis == "a" else b)
                start = time.perf_counter_ns()
                for _ in range(repeats):
                    algo(0, 0, a, b)
                elapsed_us = (time.perf_counter_ns() - start) / repeats / 1000.0
                points.append((x_value, elapsed_us))
            series[algo_name] = points

        self._show_time_graph(
            title=f"Ellipse timing vs varying {axis} (repeats={repeats})",
            x_label=f"Semi-axis {axis}",
            y_label="Time (microseconds)",
            series=series,
        )
        self.status.set("Ellipse timing research complete")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
