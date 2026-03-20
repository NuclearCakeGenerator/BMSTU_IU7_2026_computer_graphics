import math
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk, messagebox, colorchooser
from typing import Callable

from PIL import Image, ImageDraw

WINDOW_WIDTH = 1350
WINDOW_HEIGHT = 900
CANVAS_SIZE = 860
DEFAULT_BG_COLOR = "#000000"


@dataclass
class Pixel:
    x: int
    y: int
    intensity: float = 1.0


class PseudoPixelCanvas:
    def __init__(self, parent: tk.Widget, width: int, height: int):
        self.canvas = tk.Canvas(
            parent,
            width=width,
            height=height,
            bg="#111111",
            highlightthickness=1,
            highlightbackground="#444444",
        )
        self.canvas.pack(fill="both", expand=True)

        self.width_px = width
        self.height_px = height

        self.grid_w = 100
        self.grid_h = 100
        self.cell_size = 8
        self.offset_x = 0
        self.offset_y = 0
        self.bg_hex = DEFAULT_BG_COLOR
        self.bg_rgb = (0, 0, 0)
        self.grid_line_color = "#494949"

        self.update_grid(self.grid_w, self.grid_h)

    def update_grid(self, grid_w: int, grid_h: int):
        self.grid_w = max(10, grid_w)
        self.grid_h = max(10, grid_h)

        self.cell_size = max(
            1,
            int(min(self.width_px / self.grid_w, self.height_px / self.grid_h)),
        )
        drawable_w = self.grid_w * self.cell_size
        drawable_h = self.grid_h * self.cell_size
        self.offset_x = (self.width_px - drawable_w) // 2
        self.offset_y = (self.height_px - drawable_h) // 2

        self.clear(self.bg_hex)

    def clear(self, bg_hex: str = DEFAULT_BG_COLOR):
        self.bg_hex = bg_hex
        self.bg_rgb = hex_to_rgb(bg_hex)
        self.canvas.delete("all")
        self.canvas.create_rectangle(
            self.offset_x,
            self.offset_y,
            self.offset_x + self.grid_w * self.cell_size,
            self.offset_y + self.grid_h * self.cell_size,
            fill=self.bg_hex,
            outline="#333333",
        )
        self._draw_grid_lines()

    def _draw_grid_lines(self):
        x_start = self.offset_x
        y_start = self.offset_y
        x_end = self.offset_x + self.grid_w * self.cell_size
        y_end = self.offset_y + self.grid_h * self.cell_size

        for col in range(self.grid_w + 1):
            x = x_start + col * self.cell_size
            self.canvas.create_line(
                x,
                y_start,
                x,
                y_end,
                fill=self.grid_line_color,
            )

        for row in range(self.grid_h + 1):
            y = y_start + row * self.cell_size
            self.canvas.create_line(
                x_start,
                y,
                x_end,
                y,
                fill=self.grid_line_color,
            )

    def draw_pixels(self, pixels: list[Pixel], color_hex: str):
        color_rgb = hex_to_rgb(color_hex)
        for pixel in pixels:
            self.draw_pixel(pixel.x, pixel.y, color_rgb, pixel.intensity)

    def draw_pixel(
        self,
        x: int,
        y: int,
        color_rgb: tuple[int, int, int],
        intensity: float = 1.0,
    ):
        px, py = self._logical_to_grid(x, y)
        if not (0 <= px < self.grid_w and 0 <= py < self.grid_h):
            return

        blend = blend_color(self.bg_rgb, color_rgb, max(0.0, min(1.0, intensity)))
        color_hex = rgb_to_hex(blend)

        x0 = self.offset_x + px * self.cell_size
        y0 = self.offset_y + py * self.cell_size
        x1 = x0 + self.cell_size
        y1 = y0 + self.cell_size
        self.canvas.create_rectangle(
            x0,
            y0,
            x1,
            y1,
            fill=color_hex,
            outline=self.grid_line_color,
        )

    def _logical_to_grid(self, x: int, y: int) -> tuple[int, int]:
        gx = int(round(x)) + self.grid_w // 2
        gy = self.grid_h // 2 - int(round(y))
        return gx, gy


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def hex_to_rgb(color_hex: str) -> tuple[int, int, int]:
    value = color_hex.strip()
    if value.startswith("#"):
        value = value[1:]
    if len(value) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in value):
        raise ValueError("Color must be in #RRGGBB format")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def blend_color(
    bg: tuple[int, int, int], fg: tuple[int, int, int], alpha: float
) -> tuple[int, int, int]:
    return (
        int(bg[0] * (1.0 - alpha) + fg[0] * alpha),
        int(bg[1] * (1.0 - alpha) + fg[1] * alpha),
        int(bg[2] * (1.0 - alpha) + fg[2] * alpha),
    )


def line_library(x0: int, y0: int, x1: int, y1: int) -> list[Pixel]:
    min_x = min(x0, x1)
    max_x = max(x0, x1)
    min_y = min(y0, y1)
    max_y = max(y0, y1)

    width = max(1, max_x - min_x + 1)
    height = max(1, max_y - min_y + 1)

    image = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(image)
    draw.line((x0 - min_x, y0 - min_y, x1 - min_x, y1 - min_y), fill=255, width=1)

    pixels: list[Pixel] = []
    for y in range(height):
        for x in range(width):
            if image.getpixel((x, y)) > 0:
                pixels.append(Pixel(x + min_x, y + min_y, 1.0))
    return pixels


def line_dda(x0: int, y0: int, x1: int, y1: int) -> list[Pixel]:
    dx = x1 - x0
    dy = y1 - y0
    steps = int(max(abs(dx), abs(dy)))

    if steps == 0:
        return [Pixel(x0, y0, 1.0)]

    x_inc = dx / steps
    y_inc = dy / steps
    x = x0
    y = y0

    pixels = []
    for _ in range(steps + 1):
        pixels.append(Pixel(round(x), round(y), 1.0))
        x += x_inc
        y += y_inc
    return deduplicate(pixels)


def line_bres_float(x0: int, y0: int, x1: int, y1: int) -> list[Pixel]:
    dx = x1 - x0
    dy = y1 - y0
    sx = sign(dx)
    sy = sign(dy)

    dx = abs(dx)
    dy = abs(dy)
    swapped = False

    if dy > dx:
        dx, dy = dy, dx
        swapped = True

    if dx == 0:
        return [Pixel(x0, y0, 1.0)]

    m = dy / dx
    error = m - 0.5

    x = x0
    y = y0
    pixels = [Pixel(x, y, 1.0)]

    for _ in range(dx):
        if error >= 0:
            if swapped:
                x += sx
            else:
                y += sy
            error -= 1.0

        if swapped:
            y += sy
        else:
            x += sx
        error += m

        pixels.append(Pixel(x, y, 1.0))

    return deduplicate(pixels)


def line_bres_int(x0: int, y0: int, x1: int, y1: int) -> list[Pixel]:
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1

    x = x0
    y = y0
    pixels = [Pixel(x, y, 1.0)]

    if dx >= dy:
        err = 2 * dy - dx
        for _ in range(dx):
            if err >= 0:
                y += sy
                err -= 2 * dx
            x += sx
            err += 2 * dy
            pixels.append(Pixel(x, y, 1.0))
    else:
        err = 2 * dx - dy
        for _ in range(dy):
            if err >= 0:
                x += sx
                err -= 2 * dy
            y += sy
            err += 2 * dx
            pixels.append(Pixel(x, y, 1.0))

    return pixels


def line_bres_smooth(x0: int, y0: int, x1: int, y1: int) -> list[Pixel]:
    dx = x1 - x0
    dy = y1 - y0
    sx = sign(dx)
    sy = sign(dy)

    dx = abs(dx)
    dy = abs(dy)
    swapped = False

    if dy > dx:
        dx, dy = dy, dx
        swapped = True

    if dx == 0:
        return [Pixel(x0, y0, 1.0)]

    intensity_max = 255.0
    m = dy / dx
    e = intensity_max / 2.0

    x = x0
    y = y0
    pixels: list[Pixel] = []

    for _ in range(dx + 1):
        main_intensity = 1.0 - (e / intensity_max)
        side_intensity = e / intensity_max

        pixels.append(Pixel(x, y, main_intensity))
        if swapped:
            pixels.append(Pixel(x + sx, y, side_intensity))
        else:
            pixels.append(Pixel(x, y + sy, side_intensity))

        e += m * intensity_max
        if e < intensity_max:
            if swapped:
                y += sy
            else:
                x += sx
        else:
            x += sx
            y += sy
            e -= intensity_max

    return deduplicate_max_intensity(pixels)


def line_wu(x0: int, y0: int, x1: int, y1: int) -> list[Pixel]:
    def fpart(val: float) -> float:
        return val - math.floor(val)

    def rfpart(val: float) -> float:
        return 1.0 - fpart(val)

    pixels: list[Pixel] = []

    steep = abs(y1 - y0) > abs(x1 - x0)
    if steep:
        x0, y0 = y0, x0
        x1, y1 = y1, x1

    if x0 > x1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0

    dx = x1 - x0
    dy = y1 - y0
    gradient = dy / dx if dx != 0 else 0.0

    x_end = round(x0)
    y_end = y0 + gradient * (x_end - x0)
    x_gap = rfpart(x0 + 0.5)
    xpxl1 = x_end
    ypxl1 = math.floor(y_end)

    if steep:
        pixels.append(Pixel(ypxl1, xpxl1, rfpart(y_end) * x_gap))
        pixels.append(Pixel(ypxl1 + 1, xpxl1, fpart(y_end) * x_gap))
    else:
        pixels.append(Pixel(xpxl1, ypxl1, rfpart(y_end) * x_gap))
        pixels.append(Pixel(xpxl1, ypxl1 + 1, fpart(y_end) * x_gap))

    intery = y_end + gradient

    x_end = round(x1)
    y_end = y1 + gradient * (x_end - x1)
    x_gap = fpart(x1 + 0.5)
    xpxl2 = x_end
    ypxl2 = math.floor(y_end)

    if steep:
        pixels.append(Pixel(ypxl2, xpxl2, rfpart(y_end) * x_gap))
        pixels.append(Pixel(ypxl2 + 1, xpxl2, fpart(y_end) * x_gap))
    else:
        pixels.append(Pixel(xpxl2, ypxl2, rfpart(y_end) * x_gap))
        pixels.append(Pixel(xpxl2, ypxl2 + 1, fpart(y_end) * x_gap))

    for x in range(xpxl1 + 1, xpxl2):
        if steep:
            pixels.append(Pixel(math.floor(intery), x, rfpart(intery)))
            pixels.append(Pixel(math.floor(intery) + 1, x, fpart(intery)))
        else:
            pixels.append(Pixel(x, math.floor(intery), rfpart(intery)))
            pixels.append(Pixel(x, math.floor(intery) + 1, fpart(intery)))
        intery += gradient

    return deduplicate_max_intensity(pixels)


def deduplicate(pixels: list[Pixel]) -> list[Pixel]:
    result = []
    used = set()
    for pixel in pixels:
        key = (pixel.x, pixel.y)
        if key in used:
            continue
        used.add(key)
        result.append(pixel)
    return result


def deduplicate_max_intensity(pixels: list[Pixel]) -> list[Pixel]:
    max_map: dict[tuple[int, int], float] = {}
    for pixel in pixels:
        key = (pixel.x, pixel.y)
        max_map[key] = max(max_map.get(key, 0.0), pixel.intensity)
    return [Pixel(x, y, intensity) for (x, y), intensity in max_map.items()]


def sign(value: int) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def stair_count(pixels: list[Pixel], major_x: bool) -> int:
    if not pixels:
        return 0

    ordered = sorted(
        {(p.x, p.y) for p in pixels},
        key=lambda point: ((point[0], point[1]) if major_x else (point[1], point[0])),
    )
    minor_index = 1 if major_x else 0

    count = 1
    prev_minor = ordered[0][minor_index]
    for point in ordered[1:]:
        if point[minor_index] != prev_minor:
            count += 1
            prev_minor = point[minor_index]
    return count


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Computer Graphics Lab 3")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        self.algorithms: dict[str, Callable[[int, int, int, int], list[Pixel]]] = {
            "Library (Pillow)": line_library,
            "DDA": line_dda,
            "Bresenham (float)": line_bres_float,
            "Bresenham (int)": line_bres_int,
            "Bresenham (smooth)": line_bres_smooth,
            "Wu": line_wu,
        }

        self._build_ui()
        self.apply_grid()

    def _build_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        controls = tk.Frame(main_frame, width=420, padx=10, pady=10)
        controls.pack(side="left", fill="y")
        controls.pack_propagate(False)

        canvas_frame = tk.Frame(main_frame, padx=10, pady=10)
        canvas_frame.pack(side="left", fill="both", expand=True)

        self.pp_canvas = PseudoPixelCanvas(canvas_frame, CANVAS_SIZE, CANVAS_SIZE)

        ttk.Label(
            controls, text="Segment coordinates", font=("Arial", 10, "bold")
        ).pack(anchor="w")
        coords_row1 = tk.Frame(controls)
        coords_row1.pack(fill="x", pady=4)
        coords_row2 = tk.Frame(controls)
        coords_row2.pack(fill="x", pady=4)

        self.entry_x0 = self._labeled_entry(coords_row1, "x0", "-30")
        self.entry_y0 = self._labeled_entry(coords_row1, "y0", "-10")
        self.entry_x1 = self._labeled_entry(coords_row2, "x1", "45")
        self.entry_y1 = self._labeled_entry(coords_row2, "y1", "30")

        ttk.Label(controls, text="Algorithm", font=("Arial", 10, "bold")).pack(
            anchor="w", pady=(8, 0)
        )
        self.primary_algo = ttk.Combobox(
            controls, state="readonly", values=list(self.algorithms.keys())
        )
        self.primary_algo.current(1)
        self.primary_algo.pack(fill="x", pady=4)

        self.line_color_hex = "#00FF66"
        color_row = tk.Frame(controls)
        color_row.pack(fill="x", pady=4)
        ttk.Label(
            color_row,
            text="Line color",
            font=("Arial", 10, "bold"),
        ).pack(side="left")
        picker_row = tk.Frame(controls)
        picker_row.pack(fill="x", pady=(0, 6))
        tk.Button(
            picker_row,
            text="Pick color",
            command=self.pick_line_color,
            cursor="hand2",
        ).pack(side="left")
        self.color_preview = tk.Label(
            picker_row,
            width=10,
            text=self.line_color_hex,
            relief="sunken",
            bg=self.line_color_hex,
            fg="#000000",
        )
        self.color_preview.pack(side="left", padx=8)

        grid_row = tk.Frame(controls)
        grid_row.pack(fill="x", pady=4)
        self.entry_grid_w = self._labeled_entry(grid_row, "pseudo W", "120")
        self.entry_grid_h = self._labeled_entry(grid_row, "pseudo H", "120")

        buttons_row = tk.Frame(controls)
        buttons_row.pack(fill="x", pady=(8, 4))
        tk.Button(
            buttons_row,
            text="Apply grid",
            command=self.apply_grid,
            cursor="hand2",
            bg="#A8FFA8",
        ).pack(side="left", expand=True, fill="x", padx=2)
        tk.Button(
            buttons_row,
            text="Clear",
            command=self.clear_canvas,
            cursor="hand2",
        ).pack(side="left", expand=True, fill="x", padx=2)

        tk.Button(
            controls,
            text="Draw segment",
            command=self.draw_segment,
            cursor="hand2",
            bg="#6BFFA4",
        ).pack(fill="x", pady=4)

        ttk.Separator(controls).pack(fill="x", pady=8)
        ttk.Label(controls, text="Research setup", font=("Arial", 10, "bold")).pack(
            anchor="w"
        )

        research_params_1 = tk.Frame(controls)
        research_params_1.pack(fill="x", pady=4)
        self.entry_length = self._labeled_entry(research_params_1, "length", "50")
        self.entry_ang_start = self._labeled_entry(research_params_1, "ang start", "0")

        research_params_2 = tk.Frame(controls)
        research_params_2.pack(fill="x", pady=4)
        self.entry_ang_end = self._labeled_entry(research_params_2, "ang end", "360")
        self.entry_ang_step = self._labeled_entry(research_params_2, "ang step", "5")

        self.entry_repeats = self._single_entry(
            controls,
            "timing repeats (benchmark loops)",
            "300",
        )

        tk.Button(
            controls,
            text="Research visual overlay",
            command=self.research_visual,
            cursor="hand2",
        ).pack(fill="x", pady=3)
        tk.Button(
            controls,
            text="Research timing (histogram)",
            command=self.research_timing,
            cursor="hand2",
        ).pack(fill="x", pady=3)
        tk.Button(
            controls,
            text="Research staircase (graph)",
            command=self.research_staircase,
            cursor="hand2",
        ).pack(fill="x", pady=3)

        self.status = tk.StringVar(value="Ready")
        ttk.Label(
            controls,
            textvariable=self.status,
            wraplength=380,
            foreground="#0044AA",
        ).pack(anchor="w", pady=(8, 0))
        self.update_color_preview()

    def _labeled_entry(self, parent: tk.Widget, label: str, default: str) -> tk.Entry:
        frame = tk.Frame(parent)
        frame.pack(side="left", fill="x", expand=True, padx=2)
        ttk.Label(frame, text=label).pack(anchor="w")
        entry = tk.Entry(frame)
        entry.insert(0, default)
        entry.pack(fill="x")
        return entry

    def _single_entry(self, parent: tk.Widget, label: str, default: str) -> tk.Entry:
        frame = tk.Frame(parent)
        frame.pack(fill="x", pady=4)
        ttk.Label(frame, text=label).pack(anchor="w")
        entry = tk.Entry(frame)
        entry.insert(0, default)
        entry.pack(fill="x")
        return entry

    def apply_grid(self):
        try:
            grid_w = int(self.entry_grid_w.get())
            grid_h = int(self.entry_grid_h.get())
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc))
            return

        self.pp_canvas.update_grid(grid_w, grid_h)
        self.pp_canvas.clear(DEFAULT_BG_COLOR)
        self.status.set(f"Grid applied: {grid_w}x{grid_h}")

    def clear_canvas(self):
        self.pp_canvas.clear(DEFAULT_BG_COLOR)
        self.status.set("Canvas cleared")

    def parse_segment(
        self,
    ) -> tuple[
        int,
        int,
        int,
        int,
        str,
        Callable[[int, int, int, int], list[Pixel]],
    ]:
        try:
            x0 = int(float(self.entry_x0.get()))
            y0 = int(float(self.entry_y0.get()))
            x1 = int(float(self.entry_x1.get()))
            y1 = int(float(self.entry_y1.get()))
        except ValueError:
            raise ValueError("Coordinates must be numeric")

        line_color = self.line_color_hex

        algo_name = self.primary_algo.get()
        if algo_name not in self.algorithms:
            raise ValueError("Select a valid primary algorithm")

        return x0, y0, x1, y1, line_color, self.algorithms[algo_name]

    def normalize_hex(self, color_value: str) -> str:
        rgb = hex_to_rgb(color_value)
        return rgb_to_hex(rgb)

    def pick_line_color(self):
        selected = colorchooser.askcolor(
            color=self.line_color_hex,
            title="Choose line color",
        )
        color_hex = selected[1]
        if not color_hex:
            return
        self.line_color_hex = self.normalize_hex(color_hex)
        self.update_color_preview()

    def update_color_preview(self):
        self.color_preview.config(
            text=self.line_color_hex,
            bg=self.line_color_hex,
            fg="#000000",
        )

    def draw_segment(self):
        try:
            x0, y0, x1, y1, line_color, algorithm = self.parse_segment()
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc))
            return

        pixels = algorithm(x0, y0, x1, y1)
        self.pp_canvas.draw_pixels(pixels, line_color)
        self.status.set(
            f"Added segment with {self.primary_algo.get()}: {len(pixels)} pseudo-pixels"
        )

    def parse_research_common(
        self,
    ) -> tuple[float, float, float, float, str]:
        try:
            length = float(self.entry_length.get())
            ang_start = float(self.entry_ang_start.get())
            ang_end = float(self.entry_ang_end.get())
            ang_step = float(self.entry_ang_step.get())
        except ValueError:
            raise ValueError("Research parameters must be numeric")

        if length <= 0:
            raise ValueError("Length must be positive")
        if ang_step <= 0:
            raise ValueError("Angle step must be positive")
        if ang_end < ang_start:
            raise ValueError("ang end must be >= ang start")

        line_color = self.line_color_hex
        return length, ang_start, ang_end, ang_step, line_color

    def research_visual(self):
        try:
            length, ang_start, ang_end, ang_step, line_color = (
                self.parse_research_common()
            )
            primary_name = self.primary_algo.get()
            if primary_name not in self.algorithms:
                raise ValueError("Select a valid algorithm")

            algorithm = self.algorithms[primary_name]
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc))
            return

        angle = ang_start
        rays = 0
        while angle <= ang_end + 1e-9:
            radians = math.radians(angle)
            x1 = int(round(length * math.cos(radians)))
            y1 = int(round(length * math.sin(radians)))

            self.pp_canvas.draw_pixels(algorithm(0, 0, x1, y1), line_color)

            rays += 1
            angle += ang_step

        self.status.set(f"Visual overlay added: {primary_name}, rays={rays}")

    def research_timing(self):
        try:
            length, ang_start, ang_end, ang_step, _ = self.parse_research_common()
            repeats = int(float(self.entry_repeats.get()))
            if repeats <= 0:
                raise ValueError("timing repeats must be positive")
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc))
            return

        vectors = []
        angle = ang_start
        while angle <= ang_end + 1e-9:
            radians = math.radians(angle)
            vectors.append(
                (
                    0,
                    0,
                    int(round(length * math.cos(radians))),
                    int(round(length * math.sin(radians))),
                )
            )
            angle += ang_step

        times: dict[str, float] = {}
        for algo_name, algo in self.algorithms.items():
            start = time.perf_counter()
            for _ in range(repeats):
                for x0, y0, x1, y1 in vectors:
                    algo(x0, y0, x1, y1)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            times[algo_name] = elapsed_ms

        self.show_histogram(
            times,
            title=f"Timing histogram (length={length:g}, repeats={repeats})",
        )
        self.status.set("Timing research complete")

    def research_staircase(self):
        try:
            length, ang_start, ang_end, ang_step, _ = self.parse_research_common()
            algo_name = self.primary_algo.get()
            if algo_name not in self.algorithms:
                raise ValueError("Select a valid algorithm")
            algo = self.algorithms[algo_name]
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc))
            return

        data: list[tuple[float, int]] = []
        angle = ang_start
        while angle <= ang_end + 1e-9:
            radians = math.radians(angle)
            x1 = int(round(length * math.cos(radians)))
            y1 = int(round(length * math.sin(radians)))
            pixels = algo(0, 0, x1, y1)
            major_x = abs(x1) >= abs(y1)
            steps = stair_count(pixels, major_x=major_x)
            data.append((angle, steps))
            angle += ang_step

        self.show_line_graph(
            data,
            title=f"Staircase graph for {algo_name} (line length={length:g})",
            x_label="Angle (degrees)",
            y_label="Step count",
        )
        self.status.set(f"Staircase research complete for {algo_name}")

    def show_histogram(self, data: dict[str, float], title: str):
        window = tk.Toplevel(self.root)
        window.title(title)
        chart = tk.Canvas(window, width=920, height=520, bg="#FFFFFF")
        chart.pack(fill="both", expand=True)

        margin_left = 70
        margin_bottom = 60
        margin_top = 40
        margin_right = 30
        plot_w = 920 - margin_left - margin_right
        plot_h = 520 - margin_top - margin_bottom

        chart.create_text(460, 20, text=title, font=("Arial", 12, "bold"))
        chart.create_line(
            margin_left, margin_top, margin_left, margin_top + plot_h, width=2
        )
        chart.create_line(
            margin_left,
            margin_top + plot_h,
            margin_left + plot_w,
            margin_top + plot_h,
            width=2,
        )

        items = list(data.items())
        max_value = max(data.values()) if data else 1.0
        bar_w = plot_w / max(1, len(items))

        for i, (name, value) in enumerate(items):
            x0 = margin_left + i * bar_w + 8
            x1 = margin_left + (i + 1) * bar_w - 8
            bar_h = 0 if max_value == 0 else (value / max_value) * (plot_h - 20)
            y0 = margin_top + plot_h - bar_h
            y1 = margin_top + plot_h
            chart.create_rectangle(x0, y0, x1, y1, fill="#3C82F6", outline="#2E5FA8")
            chart.create_text((x0 + x1) / 2, y0 - 10, text=f"{value:.1f}")
            chart.create_text(
                (x0 + x1) / 2,
                margin_top + plot_h + 18,
                text=name,
                angle=30,
                anchor="w",
            )

        chart.create_text(20, margin_top + plot_h / 2, text="ms", angle=90)

    def show_line_graph(
        self,
        points: list[tuple[float, int]],
        title: str,
        x_label: str,
        y_label: str,
    ):
        window = tk.Toplevel(self.root)
        window.title(title)
        chart = tk.Canvas(window, width=920, height=520, bg="#FFFFFF")
        chart.pack(fill="both", expand=True)

        margin_left = 70
        margin_bottom = 60
        margin_top = 40
        margin_right = 30
        plot_w = 920 - margin_left - margin_right
        plot_h = 520 - margin_top - margin_bottom

        chart.create_text(460, 20, text=title, font=("Arial", 12, "bold"))
        chart.create_line(
            margin_left, margin_top, margin_left, margin_top + plot_h, width=2
        )
        chart.create_line(
            margin_left,
            margin_top + plot_h,
            margin_left + plot_w,
            margin_top + plot_h,
            width=2,
        )

        x_min = min(point[0] for point in points)
        x_max = max(point[0] for point in points)
        y_min = 0
        y_max = max(point[1] for point in points) if points else 1

        def map_x(value: float) -> float:
            if x_max == x_min:
                return margin_left + plot_w / 2
            return margin_left + (value - x_min) / (x_max - x_min) * plot_w

        def map_y(value: float) -> float:
            if y_max == y_min:
                return margin_top + plot_h / 2
            return margin_top + plot_h - (value - y_min) / (y_max - y_min) * plot_h

        screen_points = []
        for angle, step_count in points:
            sx = map_x(angle)
            sy = map_y(step_count)
            screen_points.extend([sx, sy])
            chart.create_oval(
                sx - 2,
                sy - 2,
                sx + 2,
                sy + 2,
                fill="#EF4444",
                outline="#EF4444",
            )

        if len(screen_points) >= 4:
            chart.create_line(*screen_points, fill="#EF4444", width=2)

        for t in range(6):
            x_tick_value = x_min + (x_max - x_min) * t / 5 if x_max != x_min else x_min
            x_tick = map_x(x_tick_value)
            chart.create_line(
                x_tick, margin_top + plot_h, x_tick, margin_top + plot_h + 5
            )
            chart.create_text(
                x_tick, margin_top + plot_h + 20, text=f"{x_tick_value:.1f}"
            )

            y_tick_value = y_min + (y_max - y_min) * t / 5 if y_max != y_min else y_min
            y_tick = map_y(y_tick_value)
            chart.create_line(margin_left - 5, y_tick, margin_left, y_tick)
            chart.create_text(margin_left - 30, y_tick, text=f"{y_tick_value:.0f}")

        chart.create_text(460, 500, text=x_label)
        chart.create_text(20, 260, text=y_label, angle=90)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
