"""
番茄钟悬浮计时器 - Pomodoro Timer

透明悬浮置顶窗口，自定义圆角右键菜单。
零外部依赖，单文件实现。

功能：
- 透明悬浮窗口，始终置顶
- 标准番茄周期：25min 专注 + 5min 短休息 + 15min 长休息
- 右键圆角菜单控制：开始/暂停/重置/跳过/统计/通知开关/自动切换
- 阶段切换时弹出通知提醒
- 每日完成番茄数自动统计
"""

import tkinter as tk
import json
import os
import ctypes
import ctypes.wintypes
from datetime import datetime
from enum import Enum


# ==================== 配置 ====================

class TimerState(Enum):
    IDLE = "idle"
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


STATE_CONFIG = {
    TimerState.WORK: {
        "duration": 25 * 60,
        "label": "专注",
        "color": "#FF6B35",
        "notify_msg": "专注时间结束，休息一下吧！"
    },
    TimerState.SHORT_BREAK: {
        "duration": 5 * 60,
        "label": "短休息",
        "color": "#4CAF50",
        "notify_msg": "休息结束，继续专注！"
    },
    TimerState.LONG_BREAK: {
        "duration": 15 * 60,
        "label": "长休息",
        "color": "#2196F3",
        "notify_msg": "长休息结束，开始新一轮专注！"
    },
}


# ==================== 统计管理 ====================

class StatsManager:
    """管理每日番茄完成统计（含坏番茄）"""

    BAD_PREFIX = "_bad_"

    def __init__(self, filepath: str = "stats.json"):
        self.filepath = filepath
        self.data: dict[str, int] = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def add_pomodoro(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self.data[today] = self.data.get(today, 0) + 1
        self._save()

    def add_bad_pomodoro(self):
        today = datetime.now().strftime("%Y-%m-%d")
        key = f"{self.BAD_PREFIX}{today}"
        self.data[key] = self.data.get(key, 0) + 1
        self._save()

    def get_today(self) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.data.get(today, 0)

    def get_bad_today(self) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.data.get(f"{self.BAD_PREFIX}{today}", 0)

    def get_summary(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        today_good = self.data.get(today, 0)
        today_bad = self.data.get(f"{self.BAD_PREFIX}{today}", 0)
        total_good = sum(v for k, v in self.data.items()
                         if not k.startswith(self.BAD_PREFIX))
        total_bad = sum(v for k, v in self.data.items()
                        if k.startswith(self.BAD_PREFIX))
        return (f"今日完成: {today_good}  今日中断: {today_bad}\n"
                f"累计完成: {total_good}  累计中断: {total_bad}")

    def get_recent(self, days: int = 7) -> list[tuple[str, int]]:
        good = {k: v for k, v in self.data.items()
                if not k.startswith(self.BAD_PREFIX)}
        return sorted(good.items(), reverse=True)[:days]


# ==================== 通知窗口 ====================

class Notification:
    """自定义弹出通知，从屏幕上方居中滑入，3秒自动关闭"""

    DURATION = 5000
    WIDTH, HEIGHT = 320, 80
    TARGET_TOP = 24
    SLIDE_STEP = 10
    SLIDE_INTERVAL = 16
    CORNER_RADIUS = 10
    TITLE_Y = 22
    MESSAGE_Y = 50
    MESSAGE_WIDTH = 205

    def __init__(self, parent: tk.Tk, message: str, color: str):
        self.win = tk.Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.92)

        screen_w = self.win.winfo_screenwidth()
        self._x = (screen_w - self.WIDTH) // 2
        y = -self.HEIGHT
        self.win.geometry(f"{self.WIDTH}x{self.HEIGHT}+{self._x}+{y}")

        canvas = tk.Canvas(self.win, width=self.WIDTH, height=self.HEIGHT,
                           bg="#18272F", highlightthickness=0)
        canvas.pack()

        _draw_rounded_rect(canvas, 1, 1, self.WIDTH - 1, self.HEIGHT - 1,
                           self.CORNER_RADIUS,
                           fill="#18272F", outline="#3A3A5C", width=1)

        canvas.create_rectangle(0, 1, 6, self.HEIGHT - 1,
                                fill=color, outline="")

        canvas.create_text(self.WIDTH // 2, self.TITLE_Y,
                           text="番茄钟提醒",
                           font=("Microsoft YaHei UI", 12, "bold"),
                           fill="#B0B0B0")

        canvas.create_text(self.WIDTH // 2, self.MESSAGE_Y,
                           text=message,
                           width=self.MESSAGE_WIDTH,
                           justify="center",
                           font=("Microsoft YaHei UI", 12),
                           fill="#FFFFFF")

        self._closing = False
        canvas.bind("<Button-1>", self._close)

        self._slide_down()
        self.win.after(self.DURATION, self._close)

    def _slide_down(self):
        def move(y_pos: int):
            try:
                if self._closing:
                    return
                if y_pos < self.TARGET_TOP:
                    y_pos = min(y_pos + self.SLIDE_STEP, self.TARGET_TOP)
                    self.win.geometry(f"{self.WIDTH}x{self.HEIGHT}+{self._x}+{y_pos}")
                    self.win.after(self.SLIDE_INTERVAL, lambda: move(y_pos))
            except tk.TclError:
                pass

        move(-self.HEIGHT)

    def _slide_up(self):
        def move(y_pos: int, alpha: float):
            try:
                if y_pos > -self.HEIGHT or alpha > 0:
                    y_pos = max(-self.HEIGHT, y_pos - self.SLIDE_STEP)
                    alpha = max(0, alpha - 0.06)
                    self.win.geometry(f"{self.WIDTH}x{self.HEIGHT}+{self._x}+{y_pos}")
                    self.win.attributes("-alpha", alpha)
                    self.win.after(self.SLIDE_INTERVAL, lambda: move(y_pos, alpha))
                else:
                    self.win.destroy()
            except tk.TclError:
                pass

        try:
            cur_y = self.win.winfo_y()
            cur_alpha = float(self.win.attributes("-alpha"))
            move(cur_y, cur_alpha)
        except tk.TclError:
            pass

    def _close(self):
        if self._closing:
            return
        self._closing = True
        self._slide_up()


# ==================== 工具函数 ====================

def _draw_rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    """在 Canvas 上绘制圆角矩形"""
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# ==================== 自定义圆角菜单 ====================

class RoundMenu:
    """自定义圆角右键菜单，替代 tk.Menu"""

    MENU_WIDTH = 155
    ITEM_HEIGHT = 26
    SEPARATOR_HEIGHT = 8
    PADDING = 6
    CORNER_RADIUS = 8

    def __init__(self, parent: tk.Tk, callbacks: dict):
        self.parent = parent
        self.callbacks = callbacks
        self.win = None
        self._shown = False
        self._items = [
            ("\u25b6 开始", "start"),
            ("\u23f8 暂停", "pause"),
            ("\u23f9 重置", "reset"),
            ("\u23ed 跳过", "skip"),
            ("---", None),
            ("\U0001f4ca 查看统计", "stats"),
            ("\U0001f514 通知: 开", "toggle_notification"),
            ("\U0001f504 自动切换: 开", "toggle_auto_mode"),
            ("---", None),
            ("\u274c 退出", "quit"),
        ]

    def _calc_height(self) -> int:
        n_items = len(self._items)
        n_separators = sum(1 for item in self._items if item[0] == "---")
        return (self.PADDING * 2
                + (n_items - n_separators) * self.ITEM_HEIGHT
                + n_separators * self.SEPARATOR_HEIGHT)

    def show(self, x: int, y: int):
        self._close()

        height = self._calc_height()
        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()

        if x + self.MENU_WIDTH > sw:
            x = max(0, x - self.MENU_WIDTH)
        if y + height > sh:
            y = max(0, y - height)

        self.win = tk.Toplevel(self.parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.95)
        self.win.geometry(f"{self.MENU_WIDTH}x{height}+{x}+{y}")

        canvas = tk.Canvas(self.win, width=self.MENU_WIDTH, height=height,
                           bg="#18272F", highlightthickness=0)
        canvas.pack()

        r = self.CORNER_RADIUS
        _draw_rounded_rect(canvas, 1, 1, self.MENU_WIDTH - 1, height - 1, r,
                           fill="#18272F", outline="#3A3A5C", width=1)

        y_pos = self.PADDING
        for item_text, item_id in self._items:
            if item_text == "---":
                y_pos += self.SEPARATOR_HEIGHT // 2
                canvas.create_line(
                    self.PADDING + 8, y_pos,
                    self.MENU_WIDTH - self.PADDING - 8, y_pos,
                    fill="#3A3A5C", width=1
                )
                y_pos += self.SEPARATOR_HEIGHT // 2
                continue

            tid = canvas.create_text(
                self.MENU_WIDTH // 2, y_pos + self.ITEM_HEIGHT // 2,
                text=item_text, anchor="center",
                font=("Microsoft YaHei UI", 10),
                fill="#FFFFFF"
            )

            canvas.tag_bind(tid, "<Enter>",
                            lambda e, t=tid, c=canvas: c.itemconfig(t, fill="#FF6B35"))
            canvas.tag_bind(tid, "<Leave>",
                            lambda e, t=tid, c=canvas: c.itemconfig(t, fill="#FFFFFF"))
            canvas.tag_bind(tid, "<Button-1>",
                            lambda e, i=item_id: self._on_click(i))

            y_pos += self.ITEM_HEIGHT

        canvas.bind("<Button-1>", lambda e: self._close())

        self._shown = True
        self.parent.bind("<Button-1>", self._on_root_click, add="+")

    def _on_root_click(self, event):
        if self._shown:
            self._close()

    def _on_click(self, item_id: str):
        self._close()
        if item_id in self.callbacks:
            self.callbacks[item_id]()

    def _close(self):
        self._shown = False
        if self.win:
            try:
                self.win.destroy()
            except tk.TclError:
                pass
            self.win = None

    def update_notification_label(self, enabled: bool):
        label = "\U0001f514 通知: 开" if enabled else "\U0001f515 通知: 关"
        self._items[6] = (label, "toggle_notification")

    def update_auto_mode_label(self, enabled: bool):
        label = "\U0001f504 自动切换: 开" if enabled else "\U0001f504 自动切换: 关"
        self._items[7] = (label, "toggle_auto_mode")


# ==================== 主应用 ====================

class TomatoApp:
    """番茄钟主程序"""

    WIDTH, HEIGHT = 100, 60

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("番茄钟")

        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.55)

        work_area = ctypes.wintypes.RECT()
        ctypes.windll.user32.SystemParametersInfoW(
            0x0030, 0, ctypes.byref(work_area), 0)
        x = work_area.right - self.WIDTH
        y = work_area.bottom - self.HEIGHT
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        self.state = TimerState.IDLE
        self.remaining = 0
        self.pomodoro_count = 0
        self.running = False
        self.notification_enabled = True
        self.auto_mode = False


        self.stats = StatsManager()

        self._drag_x = 0
        self._drag_y = 0
        self._timer_id = None

        self.round_menu = RoundMenu(self.root, {
            "start": self._start,
            "pause": self._pause,
            "reset": self._reset,
            "skip": self._skip,
            "stats": self._show_stats_window,
            "toggle_notification": self._toggle_notification,
            "toggle_auto_mode": self._toggle_auto_mode,
            "quit": self.root.quit,
        })

        self._build_ui()
        self._bind_events()
        self._update_display()

    def _build_ui(self):
        self.canvas = tk.Canvas(self.root, width=self.WIDTH, height=self.HEIGHT,
                                bg="#18272F", highlightthickness=0)
        self.canvas.pack()

        self.state_text = self.canvas.create_text(
            self.WIDTH // 2, 10, text="就绪",
            font=("Microsoft YaHei UI", 9, "bold"),
            fill="#B0B0B0"
        )

        self.timer_text = self.canvas.create_text(
            self.WIDTH // 2, 32, text="25:00",
            font=("Consolas", 18, "bold"),
            fill="#FFFFFF"
        )

        self.progress_text = self.canvas.create_text(
            self.WIDTH // 2, 50, text="\u756a\u8304\u00d70",
            font=("Microsoft YaHei UI", 8),
            fill="#B0B0B0"
        )

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_move)

        self.canvas.bind("<Enter>", lambda e: self.root.attributes("-alpha", 0.95))
        self.canvas.bind("<Leave>", lambda e: self.root.attributes("-alpha", 0.55))

        self.canvas.bind("<Double-Button-1>", lambda e: self._toggle())

        self.root.bind("<Button-3>", self._on_right_click)

    # ---- 鼠标事件 ----

    def _on_drag_start(self, event: tk.Event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag_move(self, event: tk.Event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _on_right_click(self, event: tk.Event):
        self.round_menu.update_notification_label(self.notification_enabled)
        self.round_menu.update_auto_mode_label(self.auto_mode)
        self.round_menu.show(event.x_root, event.y_root)

    # ---- 控制方法 ----

    def _start(self):
        if self.running:
            return
        if self.state == TimerState.IDLE:
            self.state = TimerState.WORK
            self.remaining = STATE_CONFIG[TimerState.WORK]["duration"]
            self.pomodoro_count = 0
        self.running = True
        self._update_display()
        self._tick()

    def _toggle(self):
        if self.running:
            self._pause()
        else:
            self._start()

    def _pause(self):
        self.running = False

    def _reset(self):
        if self.state == TimerState.WORK:
            self.stats.add_bad_pomodoro()
        self.running = False
        self.state = TimerState.IDLE
        self.remaining = 0
        self.pomodoro_count = 0
        self._update_display()

    def _skip(self):
        if self.state == TimerState.IDLE:
            return
        self.running = False
        if self.state == TimerState.WORK:
            self.stats.add_bad_pomodoro()
            if self.pomodoro_count % 4 == 0:
                self.state = TimerState.LONG_BREAK
            else:
                self.state = TimerState.SHORT_BREAK
            if self.notification_enabled:
                Notification(self.root,
                             STATE_CONFIG[self.state]["notify_msg"],
                             STATE_CONFIG[self.state]["color"])
        else:
            self._on_phase_end()
            return
        self.remaining = STATE_CONFIG[self.state]["duration"]
        self._update_display()
        if self._timer_id:
            self.root.after_cancel(self._timer_id)
        if self.auto_mode:
            self.running = True
            self._timer_id = self.root.after(1000, self._tick)

    def _toggle_notification(self):
        self.notification_enabled = not self.notification_enabled

    def _toggle_auto_mode(self):
        self.auto_mode = not self.auto_mode

    # ---- 计时逻辑 ----

    def _tick(self):
        if not self.running:
            return
        if self.remaining > 0:
            self.remaining -= 1
            self._update_display()
            self._timer_id = self.root.after(1000, self._tick)
        else:
            self._on_phase_end()

    def _on_phase_end(self):
        if self.state == TimerState.WORK:
            self.pomodoro_count += 1
            self.stats.add_pomodoro()

            if self.notification_enabled:
                Notification(self.root,
                             STATE_CONFIG[TimerState.WORK]["notify_msg"],
                             STATE_CONFIG[TimerState.WORK]["color"])

            if self.pomodoro_count % 4 == 0:
                self.state = TimerState.LONG_BREAK
            else:
                self.state = TimerState.SHORT_BREAK

        elif self.state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            if self.notification_enabled:
                Notification(self.root,
                             STATE_CONFIG[self.state]["notify_msg"],
                             STATE_CONFIG[self.state]["color"])
            self.state = TimerState.WORK
        else:
            return

        self.remaining = STATE_CONFIG[self.state]["duration"]
        self._update_display()

        if self._timer_id:
            self.root.after_cancel(self._timer_id)

        if self.auto_mode:
            self.running = True
            self._timer_id = self.root.after(1000, self._tick)
        else:
            self.running = False

    def _update_display(self):
        if self.state == TimerState.IDLE:
            self.canvas.itemconfig(self.timer_text, text="25:00")
            self.canvas.itemconfig(self.state_text, text="就绪", fill="#B0B0B0")
        else:
            mins = self.remaining // 60
            secs = self.remaining % 60
            self.canvas.itemconfig(self.timer_text, text=f"{mins:02d}:{secs:02d}")
            config = STATE_CONFIG[self.state]
            self.canvas.itemconfig(self.state_text, text=config["label"],
                                   fill=config["color"])

        self.canvas.itemconfig(
            self.progress_text,
            text=f"\u756a\u8304\u00d7{self.stats.get_today()}")

    def _show_stats_window(self):
        win = tk.Toplevel(self.root)
        win.title("番茄统计")
        win.geometry("260x260")
        win.resizable(False, False)
        win.attributes("-topmost", True)

        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - 260) // 2
        y = (sh - 260) // 2
        win.geometry(f"+{x}+{y}")

        win.configure(bg="#18272F")

        tk.Label(win, text="\U0001f4ca 番茄统计",
                 font=("Microsoft YaHei UI", 14, "bold"),
                 bg="#18272F", fg="#FFFFFF").pack(pady=(14, 4))

        tk.Frame(win, height=1, bg="#333355").pack(fill="x", padx=25, pady=4)

        summary = self.stats.get_summary()
        tk.Label(win, text=summary,
                 font=("Microsoft YaHei UI", 10),
                 bg="#18272F", fg="#E0E0E0", justify="center").pack(pady=6)

        tk.Frame(win, height=1, bg="#333355").pack(fill="x", padx=25, pady=4)

        recent = self.stats.get_recent(4)
        if recent:
            tk.Label(win, text="最近完成:",
                     font=("Microsoft YaHei UI", 10),
                     bg="#18272F", fg="#888888").pack(pady=(3, 1))
            for date, count in recent:
                tk.Label(win, text=f"  {date}    {count} 个番茄",
                         font=("Consolas", 10),
                         bg="#18272F", fg="#AAAAAA").pack()
        else:
            tk.Label(win, text="暂无记录",
                     font=("Microsoft YaHei UI", 10),
                     bg="#18272F", fg="#666666").pack(pady=6)
        tk.Frame(win, height=14, bg="#18272F").pack()

    def run(self):
        self.root.mainloop()


# ==================== 入口 ====================

if __name__ == "__main__":
    app = TomatoApp()
    app.run()