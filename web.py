#!/usr/bin/env python3
"""
GeoClone minimal — single-file Python app using Tkinter + Matplotlib.

Funcionalidades:
 - Ferramentas: Point, Move, Line, Circle, Plot function
 - Clique para adicionar ponto. Arraste para mover (Move).
 - Selecionar 2 pontos para criar linha.
 - Clicar centro + arrastar para definir raio do círculo.
 - Entrar função em Python (x como variável) e clicar Plot.
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import numpy as np
import math
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import models 
# ---- Model classes ----

# ---- Main app ----
class GeoCloneApp:
    def __init__(self, root):
        self.root = root
        root.title("GeoClone - Python")
        self.tool = tk.StringVar(value="point")  # point, move, line, circle, plot
        self.status = tk.StringVar(value="Tool: Point")
        self.objects_points = []  # list of Point
        self.objects_lines = []   # list of Line
        self.objects_circles = [] # list of Circle
        self.objects_plots = []   # list of PlotFunc

        # temp state
        self.selected_point = None
        self.dragging_point = None
        self.line_selection = []  # two points selected to create line
        self.circle_center = None
        self.circle_preview_radius = None

        # UI layout
        self.setup_ui()
        self.redraw()

    def setup_ui(self):
        # Left toolbar
        toolbar = ttk.Frame(self.root, padding=(6,6))
        toolbar.pack(side="left", fill="y")

        ttk.Label(toolbar, text="Tools", font=("Segoe UI", 10, "bold")).pack(pady=(0,6))
        for t, label in [("point","Point"), ("move","Move"), ("line","Line"), ("circle","Circle"), ("plot","Plot")]:
            rb = ttk.Radiobutton(toolbar, text=label, variable=self.tool, value=t, command=self.on_tool_change)
            rb.pack(anchor="w", pady=2)

        ttk.Separator(toolbar, orient="horizontal").pack(fill="x", pady=8)
        ttk.Button(toolbar, text="Clear All", command=self.clear_all).pack(fill="x", pady=4)
        ttk.Button(toolbar, text="List Objects", command=self.list_objects).pack(fill="x", pady=4)

        ttk.Label(toolbar, text="Function (py):", padding=(0,8)).pack(anchor="w")
        self.func_entry = ttk.Entry(toolbar, width=20)
        self.func_entry.insert(0, "sin(x)")
        self.func_entry.pack(pady=(0,4))
        ttk.Button(toolbar, text="Plot function", command=self.plot_function).pack(fill="x", pady=2)

        ttk.Separator(toolbar, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(toolbar, textvariable=self.status, foreground="#333").pack(anchor="w", pady=(6,0))

        # Matplotlib figure
        self.fig = Figure(figsize=(7,5))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.grid(True, which='both', linestyle='--', linewidth=0.6)
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-7, 7)

        canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(side="right", fill="both", expand=True)

        # Bind events
        canvas.mpl_connect("button_press_event", self.on_mouse_down)
        canvas.mpl_connect("button_release_event", self.on_mouse_up)
        canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.canvas = canvas

    # ---- object management ----
    def clear_all(self):
        self.objects_points.clear()
        self.objects_lines.clear()
        self.objects_circles.clear()
        self.objects_plots.clear()
        self.line_selection.clear()
        self.circle_center = None
        self.dragging_point = None
        self.redraw()

    def list_objects(self):
        s = []
        for i,p in enumerate(self.objects_points,1):
            s.append(f"P{i}: ({p.x:.3f}, {p.y:.3f})")
        for i,l in enumerate(self.objects_lines,1):
            s.append(f"L{i}: through P {self.objects_points.index(l.p1)+1} and P {self.objects_points.index(l.p2)+1}")
        for i,c in enumerate(self.objects_circles,1):
            s.append(f"C{i}: center ({c.center.x:.3f},{c.center.y:.3f}), r={c.radius:.3f}")
        for i,f in enumerate(self.objects_plots,1):
            s.append(f"F{i}: {f.expr}")
        if not s:
            messagebox.showinfo("Objects", "Nenhum objeto presente.")
        else:
            messagebox.showinfo("Objects", "\n".join(s))

    # ---- interaction handlers ----
    def on_tool_change(self):
        tool = self.tool.get()
        self.status.set(f"Tool: {tool.capitalize()}")
        # reset temporary state
        self.line_selection.clear()
        self.circle_center = None
        self.dragging_point = None

    def find_point_near(self, xdata, ydata, tol=0.3):
        """Procura um ponto existente perto do clique (em coordenadas do gráfico)."""
        best = None
        bestd = tol
        for p in self.objects_points:
            d = math.hypot(p.x - xdata, p.y - ydata)
            if d < bestd:
                best = p
                bestd = d
        return best

    def on_mouse_down(self, event):
        if event.xdata is None or event.ydata is None:
            return
        t = self.tool.get()
        x, y = event.xdata, event.ydata

        if t == "point":
            # adicionar ponto
            name = f"P{len(self.objects_points)+1}"
            p = Point(x, y, name=name)
            self.objects_points.append(p)
            self.status.set(f"Added point {name} at ({x:.2f}, {y:.2f})")
            self.redraw()

        elif t == "move":
            p = self.find_point_near(x, y, tol=0.4)
            if p:
                self.dragging_point = p
                self.status.set(f"Dragging {p.name}")
            else:
                self.status.set("Move: clique num ponto para arrastar")

        elif t == "line":
            p = self.find_point_near(x, y, tol=0.4)
            if p is None:
                # criar ponto automático se não existir
                p = Point(x, y, name=f"P{len(self.objects_points)+1}")
                self.objects_points.append(p)
            self.line_selection.append(p)
            self.status.set(f"Selected {p.name} for line ({len(self.line_selection)}/2)")
            if len(self.line_selection) == 2:
                a, b = self.line_selection
                if a is b:
                    messagebox.showwarning("Line", "Selecione dois pontos diferentes.")
                else:
                    self.objects_lines.append(Line(a, b))
                    self.status.set(f"Line created through {a.name} and {b.name}")
                self.line_selection.clear()
                self.redraw()

        elif t == "circle":
            # first click: center (if near point, choose it)
            p = self.find_point_near(x, y, tol=0.4)
            if p is None:
                p = Point(x, y, name=f"P{len(self.objects_points)+1}")
                self.objects_points.append(p)
            self.circle_center = p
            self.circle_preview_radius = 0.0
            self.status.set(f"Circle center set to {p.name}. Arraste para ajustar raio.")

        elif t == "plot":
            self.status.set("Use o botão 'Plot function' na barra para inserir expressão e plotar.")

    def on_mouse_up(self, event):
        if event.xdata is None or event.ydata is None:
            return
        t = self.tool.get()
        x, y = event.xdata, event.ydata

        if t == "move" and self.dragging_point:
            # drop point
            p = self.dragging_point
            p.x, p.y = x, y
            self.status.set(f"Moved {p.name} to ({x:.2f}, {y:.2f})")
            self.dragging_point = None
            self.redraw()

        if t == "circle" and self.circle_center is not None:
            # on release, fix circle with radius from center to release pos
            r = math.hypot(x - self.circle_center.x, y - self.circle_center.y)
            if r < 1e-6:
                self.status.set("Circle radius muito pequeno, cancelado.")
            else:
                self.objects_circles.append(Circle(self.circle_center, r))
                self.status.set(f"Circle created center {self.circle_center.name}, r={r:.3f}")
            self.circle_center = None
            self.circle_preview_radius = None
            self.redraw()

    def on_mouse_move(self, event):
        if event.xdata is None or event.ydata is None:
            return
        x, y = event.xdata, event.ydata
        t = self.tool.get()

        if t == "move" and self.dragging_point:
            # live drag
            p = self.dragging_point
            p.x, p.y = x, y
            self.redraw(live=True)

        if t == "circle" and self.circle_center is not None:
            r = math.hypot(x - self.circle_center.x, y - self.circle_center.y)
            self.circle_preview_radius = r
            self.redraw(live=True)

    # ---- drawing ----
    def redraw(self, live=False):
        self.ax.clear()
        self.ax.grid(True, which='both', linestyle='--', linewidth=0.6)
        self.ax.set_aspect('equal', adjustable='box')
        # keep limits or autoscale? keep fixed for simplicity
        # draw plots
        for pf in self.objects_plots:
            self._draw_plotfunc(pf)
        # draw lines (infinite visualized within limits)
        for l in self.objects_lines:
            self._draw_line(l)

        # draw circles
        for c in self.objects_circles:
            self._draw_circle(c, style='-')

        # preview circle
        if self.circle_center is not None and self.circle_preview_radius is not None:
            self._draw_circle(Circle(self.circle_center, self.circle_preview_radius), style='--', alpha=0.7)

        # draw points on top
        for p in self.objects_points:
            self._draw_point(p)

        # draw axes
        self._draw_axes()

        self.canvas.draw_idle()

    def _draw_point(self, p: Point):
        self.ax.plot(p.x, p.y, marker='o', markersize=6, color='#1f77b4')
        self.ax.text(p.x + 0.1, p.y + 0.1, p.name or "", fontsize=9)

    def _draw_line(self, l: Line):
        # compute two far points along the line to span axes limits
        x1, y1 = l.p1.x, l.p1.y
        x2, y2 = l.p2.x, l.p2.y
        if abs(x2 - x1) < 1e-9 and abs(y2 - y1) < 1e-9:
            return
        # param t; get axis limits
        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()
        # compute line paramization
        dx = x2 - x1
        dy = y2 - y1
        # choose two points by intersecting with box extremes
        tvals = []
        # intersect with x = xmin/xmax
        if abs(dx) > 1e-9:
            t1 = (xmin - x1) / dx
            t2 = (xmax - x1) / dx
            tvals.extend([t1,t2])
        if abs(dy) > 1e-9:
            t3 = (ymin - y1) / dy
            t4 = (ymax - y1) / dy
            tvals.extend([t3,t4])
        if not tvals:
            return
        tmin = min(tvals) - 1.0
        tmax = max(tvals) + 1.0
        xs = np.linspace(tmin, tmax, 2)
        X = x1 + dx*xs
        Y = y1 + dy*xs
        self.ax.plot(X, Y, linestyle='-', linewidth=1.6, color='#2ca02c')

    def _draw_circle(self, c: Circle, style='-.', alpha=1.0):
        theta = np.linspace(0, 2*np.pi, 240)
        xs = c.center.x + c.radius * np.cos(theta)
        ys = c.center.y + c.radius * np.sin(theta)
        self.ax.plot(xs, ys, linestyle=style, linewidth=1.6, color='#d62728', alpha=alpha)
        # center marker
        self.ax.plot(c.center.x, c.center.y, marker='x', markersize=6, color='#d62728')

    def _draw_plotfunc(self, pf: PlotFunc):
        expr = pf.expr
        xmin, xmax = self.ax.get_xlim()
        xs = np.linspace(xmin, xmax, 800)
        ys = np.full_like(xs, np.nan)
        # safe eval: provide math and numpy, x variable
        safe_env = {"math": math, "np": np, "sin": np.sin, "cos": np.cos,
                    "tan": np.tan, "exp": np.exp, "log": np.log, "sqrt": np.sqrt, "pi": math.pi}
        for i, xv in enumerate(xs):
            try:
                # evaluate expression; x available as float
                x = float(xv)
                y = eval(expr, safe_env, {"x": x})
                y = float(y)
                ys[i] = y
            except Exception:
                ys[i] = np.nan
        self.ax.plot(xs, ys, linewidth=1.6, color='#000000')

    def _draw_axes(self):
        self.ax.axhline(0, color='#444', linewidth=0.9)
        self.ax.axvline(0, color='#444', linewidth=0.9)

    # ---- actions ----
    def plot_function(self):
        expr = self.func_entry.get().strip()
        if not expr:
            messagebox.showwarning("Plot", "Insira uma expressão.")
            return
        # quick check evaluate at 0
        try:
            safe_env = {"math": math, "np": np, "sin": np.sin, "cos": np.cos,
                        "tan": np.tan, "exp": np.exp, "log": np.log, "sqrt": np.sqrt, "pi": math.pi}
            test = eval(expr, safe_env, {"x": 0.0})
        except Exception as e:
            messagebox.showerror("Erro na expressão", f"Erro ao avaliar expressão:\n{e}")
            return
        pf = PlotFunc(expr)
        self.objects_plots.append(pf)
        self.status.set(f"Function plotted: {expr}")
        self.redraw()

# ---- run ----
def main():
    root = tk.Tk()
    app = GeoCloneApp(root)
    root.geometry("1000x650")
    root.mainloop()

if __name__ == "__main__":
    main()
  
