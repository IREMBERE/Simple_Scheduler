import sys, json, os, uuid, math, random
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QScrollArea,
    QFrame, QDialog, QTimeEdit, QDateEdit, QComboBox,
    QMessageBox, QStackedWidget, QGraphicsOpacityEffect, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, QTime, QDate, pyqtSignal, pyqtSlot, QThread, QMutex, QMutexLocker,
    QPropertyAnimation, QEasingCurve, QAbstractAnimation, QObject
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QPainter, QBrush, QLinearGradient, 
    QRadialGradient, QPainterPath, QCursor, QIcon, QPixmap
)

# ── Resource path ─────────────────────────────────────────────────────────────
def resource_path(p):
    base = sys._MEIPASS if getattr(sys,'frozen',False) else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, p)

# ── Storage ───────────────────────────────────────────────────────────────────
DATA_FILE = os.path.join(os.path.expanduser("~"), ".olisched_tahoe.json")
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f: return json.load(f)
        except: pass
    return {"tasks":[], "daily_notes":{}}
def save_data(data):
    with open(DATA_FILE,"w") as f: json.dump(data,f,indent=2)

# ── Liquid Glass Palette ──────────────────────────────────────────────────────
BG_GRAD_TOP    = "#1a1a2e"
BG_GRAD_MID    = "#16213e"
BG_GRAD_BOT    = "#0f3460"
GLASS          = "rgba(255,255,255,0.08)"
GLASS_BORDER   = "rgba(255,255,255,0.18)"
GLASS_HOVER    = "rgba(255,255,255,0.14)"
GLASS_PRESS    = "rgba(255,255,255,0.06)"
TEXT1          = "#f5f5f7"
TEXT2          = "rgba(245,245,247,0.65)"
TEXT3          = "rgba(245,245,247,0.35)"
ACCENT         = "#0a84ff"
ACCENT2        = "#30d158"
AMBER          = "#ff9f0a"
CORAL          = "#ff453a"
PURPLE         = "#bf5af2"
TEAL           = "#5ac8fa"
MINT           = "#63e6be"

PRIORITY_COLORS = {
    "LOW":    (ACCENT2, "rgba(48,209,88,0.15)"),
    "MEDIUM": (ACCENT,  "rgba(10,132,255,0.15)"),
    "HIGH":   (CORAL,   "rgba(255,69,58,0.15)"),
}
STATUS_COLORS = {
    "planned":     ACCENT,
    "in_progress": AMBER,
    "completed":   ACCENT2,
}

# ── SF Pro Typography ─────────────────────────────────────────────────────────
def sf(size, weight=QFont.Weight.Normal, italic=False):
    f = QFont()
    f.setFamilies(["SF Pro Display","SF Pro Text","SF Pro Rounded",
                   "Helvetica Neue",".AppleSystemUIFont",
                   "Segoe UI Variable Display","Segoe UI","Arial"])
    f.setPointSize(size)
    f.setWeight(weight)
    f.setItalic(italic)
    if size >= 14:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, -0.4)
    elif size >= 11:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, -0.2)
    return f

# ── Animated Glass Button ─────────────────────────────────────────────────────
class GlassButton(QPushButton):
    def __init__(self, text, accent=None, filled=False, parent=None):
        super().__init__(text, parent)
        self._accent = accent or ACCENT
        self._filled = filled
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._apply_style()

    def _darken(self, hex_color):
        c = QColor(hex_color)
        c.setHsv(c.hsvHue(), c.hsvSaturation(), max(0, c.value()-30))
        return c.name()

    def _lighten(self, hex_color):
        c = QColor(hex_color)
        c.setHsv(c.hsvHue(), max(0, c.hsvSaturation()-20), min(255, c.value()+20))
        return c.name()

    def _apply_style(self):
        a = self._accent
        if self._filled:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 {a}, stop:1 {self._darken(a)});
                    color: white; border: none;
                    border-radius: 10px; padding: 0 20px; font-weight: 600;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 {self._lighten(a)}, stop:1 {a});
                }}
                QPushButton:pressed {{
                    background: {self._darken(a)};
                    padding-top: 2px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.08);
                    color: {a}; border: 1px solid rgba(255,255,255,0.20);
                    border-radius: 10px; padding: 0 16px; font-weight: 500;
                }}
                QPushButton:hover {{
                    background: rgba(255,255,255,0.14); border-color: {a};
                }}
                QPushButton:pressed {{
                    background: rgba(255,255,255,0.05);
                    padding-top: 2px;
                }}
            """)

# ── Glass Card ───────────────────────────────────────────────────────────────
class GlassCard(QFrame):
    def __init__(self, radius=18, tint=None, border_accent=None, parent=None):
        super().__init__(parent)
        self._radius = radius
        self._tint = tint
        self._border_accent = border_accent
        self.setObjectName("gc")
        self._apply()

    def _apply(self):
        ba = self._border_accent
        if ba:
            border = f"border: 1px solid {ba}55;"
            border_left = f"border-left: 3px solid {ba};"
        else:
            border = f"border: 1px solid {GLASS_BORDER};"
            border_left = ""
        tint_bg = self._tint if self._tint else "rgba(255,255,255,0.07)"
        self.setStyleSheet(f"""
            #gc {{
                background: {tint_bg};
                {border}
                {border_left}
                border-radius: {self._radius}px;
            }}
            #gc:hover {{
                background: rgba(255,255,255,0.11);
            }}
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self._radius
        W, H = self.width(), self.height()
        grad = QLinearGradient(0, 0, 0, H * 0.4)
        grad.setColorAt(0, QColor(255,255,255,28))
        grad.setColorAt(1, QColor(255,255,255,0))
        path = QPainterPath()
        path.addRoundedRect(1, 1, W-2, H*0.4, r, r)
        p.fillPath(path, QBrush(grad))

# ── Animated Tab Button ───────────────────────────────────────────────────────
class TabButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFont(sf(10, QFont.Weight.Medium))
        self.setFixedHeight(32)
        self._update_style()
        self.toggled.connect(lambda _: self._update_style())

    def _update_style(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 rgba(255,255,255,0.22),
                        stop:1 rgba(255,255,255,0.12));
                    color: {TEXT1};
                    border: 1px solid rgba(255,255,255,0.30);
                    border-radius: 10px;
                    padding: 0 18px;
                    font-weight: 600;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {TEXT2};
                    border: 1px solid transparent;
                    border-radius: 10px;
                    padding: 0 18px;
                }}
                QPushButton:hover {{
                    background: rgba(255,255,255,0.08);
                    color: {TEXT1};
                }}
            """)

# ── Helper label ──────────────────────────────────────────────────────────────
def lbl(text, size=10, color=TEXT1, bold=False, italic=False, wrap=False):
    l = QLabel(text)
    l.setFont(sf(size, QFont.Weight.Bold if bold else QFont.Weight.Normal, italic))
    l.setStyleSheet(f"color:{color}; background:transparent;")
    if wrap: l.setWordWrap(True)
    return l

def divider():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("background:rgba(255,255,255,0.10); max-height:1px;")
    return f

# ── Background Gradient Widget ───────────────────────────────────────────────
class GradientBG(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self._update_gradient()
    
    def _update_gradient(self):
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BG_GRAD_TOP},
                    stop:0.5 {BG_GRAD_MID},
                    stop:1 {BG_GRAD_BOT});
            }}
        """)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)

# ── Custom Logo Widget (Replaces the star) ────────────────────────────────────
class LogoWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self.setObjectName("logo")
        
        # Try to load custom icon from file
        icon_paths = [
            resource_path("OliSchedIcon.ico"),
        ]
        
        self.icon_label = QLabel(self)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_loaded = False
        for path in icon_paths:
            if os.path.exists(path):
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    # Scale the icon to fit the button
                    scaled_pixmap = pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.icon_label.setPixmap(scaled_pixmap)
                    icon_loaded = True
                    break
        
        if not icon_loaded:
            # Fallback to a nice gradient circle with text instead of star
            self.icon_label.setText("📋")
            self.icon_label.setFont(sf(24, QFont.Weight.Bold))
            self.icon_label.setStyleSheet("color: white; background: transparent;")
        
        # Set up the layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.icon_label)
        
        # Style the logo container
        self.setStyleSheet(f"""
            #logo {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {ACCENT}, stop:1 {PURPLE});
                border: none;
                border-radius: 13px;
            }}
        """)

# ── Task Card ────────────────────────────────────────────────────────────────
class TaskCard(GlassCard):
    sig_delete = pyqtSignal(str)
    sig_status = pyqtSignal(str, str)

    def __init__(self, task, parent=None):
        bcol = STATUS_COLORS.get(task["status"], ACCENT)
        super().__init__(radius=14, border_accent=bcol, parent=parent)
        self.task = task
        self._build()

    def _build(self):
        task = self.task
        done = task["status"] == "completed"
        pc, pbg = PRIORITY_COLORS.get(task.get("priority","MEDIUM"), PRIORITY_COLORS["MEDIUM"])

        lay = QVBoxLayout(self); lay.setContentsMargins(16,13,16,13); lay.setSpacing(7)

        r1 = QHBoxLayout(); r1.setSpacing(8)
        if task.get("time"):
            r1.addWidget(lbl(f"🕐  {task['time']}", 8, TEXT2))
        if task.get("duration"):
            r1.addWidget(lbl(f"·  {task['duration']}m", 8, TEXT3))
        r1.addStretch()
        pri = task.get("priority","MEDIUM")
        pb = QLabel(f" {pri} ")
        pb.setFont(sf(7, QFont.Weight.Bold))
        pb.setStyleSheet(f"color:{pc}; background:{pbg}; border:1px solid {pc}44; border-radius:6px; padding:2px 6px;")
        r1.addWidget(pb)
        lay.addLayout(r1)

        tl = QLabel(task.get("title",""))
        tl.setFont(sf(13, QFont.Weight.Bold))
        tl.setWordWrap(True)
        if done:
            tl.setStyleSheet("color:rgba(245,245,247,0.30); text-decoration:line-through; background:transparent;")
        else:
            tl.setStyleSheet(f"color:{TEXT1}; background:transparent;")
        lay.addWidget(tl)

        if task.get("notes"):
            nl = QLabel(task["notes"][:100]+("…" if len(task["notes"])>100 else ""))
            nl.setFont(sf(9, italic=True)); nl.setWordWrap(True)
            nl.setStyleSheet(f"color:{TEXT3}; background:transparent;")
            lay.addWidget(nl)

        if task.get("reminder") and task["reminder"] != "None":
            lay.addWidget(lbl(f"🔔  {task['reminder']}", 8, AMBER, italic=True))

        lay.addWidget(divider())

        br = QHBoxLayout(); br.setSpacing(10)

        db = QPushButton("🗑️  Delete")
        db.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        db.setFont(sf(10, QFont.Weight.Medium))
        db.setFixedSize(90, 32)
        db.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,69,58,0.15);
                color: {CORAL};
                border: 1px solid {CORAL}88;
                border-radius: 8px;
                padding: 5px 12px;
            }}
            QPushButton:hover {{
                background: rgba(255,69,58,0.30);
                border-color: {CORAL};
            }}
            QPushButton:pressed {{
                background: rgba(255,69,58,0.50);
                padding-top: 6px;
            }}
        """)
        db.clicked.connect(lambda checked, tid=task["id"]: self.sig_delete.emit(tid))
        br.addWidget(db)
        br.addStretch()

        if task["status"] == "planned":
            sb = GlassButton("⚡ Start", AMBER)
            sb.setFont(sf(9, QFont.Weight.Medium)); sb.setFixedHeight(32)
            sb.clicked.connect(lambda checked, tid=task["id"]: self.sig_status.emit(tid, "in_progress"))
            br.addWidget(sb)
            cb = GlassButton("✓ Done", ACCENT2, filled=True)
            cb.setFont(sf(9, QFont.Weight.DemiBold)); cb.setFixedHeight(32)
            cb.clicked.connect(lambda checked, tid=task["id"]: self.sig_status.emit(tid, "completed"))
            br.addWidget(cb)
        elif task["status"] == "in_progress":
            cb = GlassButton("✓ Done", ACCENT2, filled=True)
            cb.setFont(sf(9, QFont.Weight.DemiBold)); cb.setFixedHeight(32)
            cb.clicked.connect(lambda checked, tid=task["id"]: self.sig_status.emit(tid, "completed"))
            br.addWidget(cb)
        else:
            mb = GlassButton("↩ Revert", ACCENT)
            mb.setFont(sf(9, QFont.Weight.Medium)); mb.setFixedHeight(32)
            mb.clicked.connect(lambda checked, tid=task["id"]: self.sig_status.emit(tid, "planned"))
            br.addWidget(mb)
        lay.addLayout(br)

# ── Column ────────────────────────────────────────────────────────────────────
class Column(GlassCard):
    changed = pyqtSignal()
    HEADERS = {
        "planned":     ("PLANNED",         ACCENT,  "Ready"),
        "in_progress": ("ACTIVE WORKFLOW",  AMBER,  "In Progress"),
        "completed":   ("COMPLETED",        ACCENT2,"Crossed Out"),
    }
    def __init__(self, status, data, parent=None):
        super().__init__(radius=20, parent=parent)
        self.status = status; self._data = data
        title, color, sub = self.HEADERS[status]
        self._color = color

        lay = QVBoxLayout(self); lay.setContentsMargins(16,16,16,16); lay.setSpacing(10)

        hr = QHBoxLayout(); hr.setSpacing(8)
        dot = QLabel("●"); dot.setFont(sf(10)); dot.setStyleSheet(f"color:{color};background:transparent;")
        tl = QLabel(title); tl.setFont(sf(11,QFont.Weight.Bold))
        tl.setStyleSheet(f"color:{TEXT1};letter-spacing:-0.2px;background:transparent;")
        self._badge = QLabel("0"); self._badge.setFont(sf(9,QFont.Weight.Bold))
        self._badge.setStyleSheet(f"color:{color};background:{color}22;border:1px solid {color}44;border-radius:9px;padding:1px 9px;")
        sl = QLabel(sub); sl.setFont(sf(8,italic=True)); sl.setStyleSheet(f"color:{TEXT3};background:transparent;")
        hr.addWidget(dot); hr.addWidget(tl); hr.addWidget(self._badge); hr.addStretch(); hr.addWidget(sl)
        lay.addLayout(hr); lay.addWidget(divider())

        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True); self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet("""
            QScrollArea{background:transparent;border:none;}
            QScrollBar:vertical{background:transparent;width:4px;}
            QScrollBar::handle:vertical{background:rgba(255,255,255,0.25);border-radius:2px;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}
        """)
        self._inner = QWidget(); self._inner.setStyleSheet("background:transparent;")
        self._il = QVBoxLayout(self._inner); self._il.setContentsMargins(0,0,4,0); self._il.setSpacing(8); self._il.addStretch()
        self._scroll.setWidget(self._inner); lay.addWidget(self._scroll,1)
        self.refresh()

    def refresh(self):
        while self._il.count()>1:
            it=self._il.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        tasks=sorted([t for t in self._data["tasks"] if t["status"]==self.status],
                     key=lambda t:(t.get("date",""),t.get("time","")))
        for t in tasks:
            c=TaskCard(t); c.sig_delete.connect(self._del); c.sig_status.connect(self._chg)
            self._il.insertWidget(self._il.count()-1,c)
        self._badge.setText(str(len(tasks)))

    def _del(self,tid):
        self._data["tasks"]=[t for t in self._data["tasks"] if t["id"]!=tid]
        save_data(self._data); self.changed.emit()
    def _chg(self,tid,ns):
        for t in self._data["tasks"]:
            if t["id"]==tid: t["status"]=ns; break
        save_data(self._data); self.changed.emit()

# ── New Plan Dialog ───────────────────────────────────────────────────────────
class NewPlanDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.task = task or {}
        self.setWindowTitle("New Plan")
        self.setFixedSize(500, 520)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        card = GlassCard(radius=22)
        card.setStyleSheet("""
            #gc{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 rgba(30,40,70,0.97),
                    stop:1 rgba(15,25,50,0.97));
                border:1px solid rgba(255,255,255,0.22);
                border-radius:22px;
            }
        """)
        outer.addWidget(card)

        lay = QVBoxLayout(card); lay.setContentsMargins(28,26,28,26); lay.setSpacing(13)

        close_row = QHBoxLayout()
        close_row.addStretch()
        xb = QPushButton("✕"); xb.setFont(sf(11)); xb.setFixedSize(28,28)
        xb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        xb.setStyleSheet(f"QPushButton{{background:rgba(255,69,58,0.25);color:{CORAL};border:none;border-radius:14px;}}QPushButton:hover{{background:rgba(255,69,58,0.50);}}")
        xb.clicked.connect(self.reject)
        close_row.addWidget(xb)
        lay.addLayout(close_row)

        lay.addWidget(lbl("New Plan", 19, TEXT1, bold=True))
        lay.addSpacing(2)

        field_style = f"""
            background:rgba(255,255,255,0.08);
            color:{TEXT1};
            border:1px solid rgba(255,255,255,0.18);
            border-radius:10px;
            padding:8px 12px;
            font-family:'Segoe UI'; font-size:10pt;
            selection-background-color:rgba(10,132,255,0.40);
        """
        focus_style = f"border:1px solid {ACCENT}; background:rgba(10,132,255,0.10);"

        lay.addWidget(lbl("Title", 9, TEXT2))
        self.e_title = QLineEdit(self.task.get("title",""))
        self.e_title.setPlaceholderText("What do you need to do?")
        self.e_title.setStyleSheet(f"QLineEdit{{{field_style}}} QLineEdit:focus{{{focus_style}}}")
        lay.addWidget(self.e_title)

        r1 = QHBoxLayout(); r1.setSpacing(12)
        def col(t, w):
            c = QVBoxLayout(); c.setSpacing(4)
            c.addWidget(lbl(t,9,TEXT2)); c.addWidget(w); return c

        self.e_date = QDateEdit(); self.e_date.setCalendarPopup(True)
        self.e_date.setDate(QDate.fromString(self.task.get("date",date.today().isoformat()),"yyyy-MM-dd"))
        self.e_date.setDisplayFormat("yyyy-MM-dd")
        self.e_date.setStyleSheet(f"QDateEdit{{{field_style}}}QDateEdit::drop-down{{border:none;width:20px;}}")
        r1.addLayout(col("Date", self.e_date))

        self.e_time = QTimeEdit()
        self.e_time.setTime(QTime.fromString(self.task["time"],"HH:mm") if self.task.get("time") else QTime.currentTime())
        self.e_time.setDisplayFormat("HH:mm")
        self.e_time.setStyleSheet(f"QTimeEdit{{{field_style}}}")
        r1.addLayout(col("Time", self.e_time))

        self.e_dur = QLineEdit(str(self.task.get("duration","")))
        self.e_dur.setPlaceholderText("mins")
        self.e_dur.setStyleSheet(f"QLineEdit{{{field_style}}} QLineEdit:focus{{{focus_style}}}")
        r1.addLayout(col("Duration", self.e_dur))
        lay.addLayout(r1)

        r2 = QHBoxLayout(); r2.setSpacing(12)
        cb_style = f"""
            QComboBox{{{field_style}}}
            QComboBox::drop-down{{border:none;width:22px;}}
            QComboBox QAbstractItemView{{
                background:rgba(20,30,55,0.98);color:{TEXT1};
                selection-background-color:rgba(10,132,255,0.35);
                border:1px solid rgba(255,255,255,0.20);border-radius:10px;
            }}
        """
        self.e_pri = QComboBox(); [self.e_pri.addItem(p) for p in ["LOW","MEDIUM","HIGH"]]
        self.e_pri.setCurrentText(self.task.get("priority","MEDIUM"))
        self.e_pri.setStyleSheet(cb_style)
        r2.addLayout(col("Priority", self.e_pri))

        self.e_rem = QComboBox()
        [self.e_rem.addItem(o) for o in ["None","At time","5 min before","15 min before","30 min before","1 hr before","1 day before"]]
        self.e_rem.setCurrentText(self.task.get("reminder","None"))
        self.e_rem.setStyleSheet(cb_style)
        r2.addLayout(col("Reminder", self.e_rem))

        self.e_status = QComboBox()
        for v,t in [("planned","Planned"),("in_progress","In Progress"),("completed","Completed")]:
            self.e_status.addItem(t,v)
        cur = self.task.get("status","planned")
        for i in range(self.e_status.count()):
            if self.e_status.itemData(i)==cur: self.e_status.setCurrentIndex(i); break
        self.e_status.setStyleSheet(cb_style)
        r2.addLayout(col("Status", self.e_status))
        lay.addLayout(r2)

        lay.addWidget(lbl("Notes", 9, TEXT2))
        self.e_notes = QTextEdit(self.task.get("notes",""))
        self.e_notes.setPlaceholderText("Add details, context, overview…")
        self.e_notes.setFixedHeight(80)
        self.e_notes.setStyleSheet(f"QTextEdit{{background:rgba(255,255,255,0.08);color:{TEXT1};border:1px solid rgba(255,255,255,0.18);border-radius:10px;padding:10px;}}QTextEdit:focus{{border-color:{ACCENT};}}")
        lay.addWidget(self.e_notes)

        lay.addStretch()
        br = QHBoxLayout(); br.setSpacing(12)
        cancel = GlassButton("Cancel", CORAL)
        cancel.setFont(sf(10,QFont.Weight.Medium)); cancel.setFixedHeight(40)
        cancel.clicked.connect(self.reject)
        save = GlassButton("Save Plan", ACCENT, filled=True)
        save.setFont(sf(11,QFont.Weight.DemiBold)); save.setFixedHeight(40)
        save.clicked.connect(self.accept)
        br.addWidget(cancel); br.addStretch(); br.addWidget(save)
        lay.addLayout(br)

    def mousePressEvent(self, e):
        self._drag_pos = e.globalPosition().toPoint()
    def mouseMoveEvent(self, e):
        if hasattr(self,'_drag_pos'):
            delta = e.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = e.globalPosition().toPoint()

    def result_task(self):
        return {
            "id":       self.task.get("id", str(uuid.uuid4())),
            "title":    self.e_title.text().strip(),
            "date":     self.e_date.date().toString("yyyy-MM-dd"),
            "time":     self.e_time.time().toString("HH:mm"),
            "duration": self.e_dur.text().strip(),
            "priority": self.e_pri.currentText(),
            "reminder": self.e_rem.currentText(),
            "status":   self.e_status.currentData(),
            "notes":    self.e_notes.toPlainText().strip(),
            "created":  self.task.get("created", datetime.now().isoformat()),
        }

# ── Search Panel ──────────────────────────────────────────────────────────────
class SearchPanel(QWidget):
    jump_to = pyqtSignal(str)
    STATUS_LABEL = {"planned":"📋 Planned","in_progress":"⚡ In Progress","completed":"✅ Completed"}

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data
        self.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(self); lay.setContentsMargins(0,12,0,0); lay.setSpacing(14)

        hcard = GlassCard(14)
        hl = QVBoxLayout(hcard); hl.setContentsMargins(20,18,20,18); hl.setSpacing(10)
        hl.addWidget(lbl("🔍 Search Tasks", 15, TEXT1, bold=True))
        hl.addWidget(lbl("Search by title, notes, date, or priority", 9, TEXT3, italic=True))

        bar = QHBoxLayout(); bar.setSpacing(10)
        self._inp = QLineEdit()
        self._inp.setFont(sf(11))
        self._inp.setPlaceholderText("Search anything…")
        self._inp.setFixedHeight(42)
        self._inp.setStyleSheet(f"""
            QLineEdit{{
                background:rgba(255,255,255,0.08);
                color:{TEXT1};
                border:1px solid rgba(255,255,255,0.20);
                border-radius:12px; padding:0 16px;
            }}
            QLineEdit:focus{{
                border-color:{ACCENT};
                background:rgba(10,132,255,0.10);
            }}
        """)
        self._inp.textChanged.connect(self._search)
        bar.addWidget(self._inp, 1)

        clr = GlassButton("✕", CORAL)
        clr.setFont(sf(10)); clr.setFixedSize(42,42)
        clr.clicked.connect(lambda: self._inp.clear())
        bar.addWidget(clr)
        hl.addLayout(bar)
        lay.addWidget(hcard)

        self._count_lbl = lbl("", 9, TEXT3, italic=True)
        lay.addWidget(self._count_lbl)

        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True); self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}QScrollBar:vertical{background:transparent;width:4px;}QScrollBar::handle:vertical{background:rgba(255,255,255,0.25);border-radius:2px;}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        self._inner = QWidget(); self._inner.setStyleSheet("background:transparent;")
        self._il = QVBoxLayout(self._inner); self._il.setContentsMargins(0,0,4,0); self._il.setSpacing(10); self._il.addStretch()
        self._scroll.setWidget(self._inner); lay.addWidget(self._scroll,1)

    def _search(self, query):
        while self._il.count()>1:
            it=self._il.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        q = query.strip().lower()
        if not q: self._count_lbl.setText(""); return

        results = [t for t in self._data["tasks"]
                   if q in t.get("title","").lower()
                   or q in t.get("notes","").lower()
                   or q in t.get("date","").lower()
                   or q in t.get("priority","").lower()]
        self._count_lbl.setText(f"{len(results)} result{'s' if len(results)!=1 else ''} found")

        for t in results:
            sc = STATUS_COLORS.get(t["status"], ACCENT)
            row = GlassCard(12, border_accent=sc)
            rl = QVBoxLayout(row); rl.setContentsMargins(16,12,16,12); rl.setSpacing(5)

            top = QHBoxLayout()
            done = t["status"]=="completed"
            tl2 = QLabel(t.get("title",""))
            tl2.setFont(sf(12,QFont.Weight.Bold))
            if done:
                tl2.setStyleSheet("color:rgba(245,245,247,0.30);text-decoration:line-through;background:transparent;")
            else:
                tl2.setStyleSheet(f"color:{TEXT1};background:transparent;")
            top.addWidget(tl2); top.addStretch()
            sp = QLabel(self.STATUS_LABEL.get(t["status"],""))
            sp.setFont(sf(8,QFont.Weight.Bold))
            sp.setStyleSheet(f"color:{sc};background:{sc}22;border:1px solid {sc}44;border-radius:8px;padding:2px 9px;")
            top.addWidget(sp); rl.addLayout(top)

            meta = QHBoxLayout(); meta.setSpacing(14)
            if t.get("date"): meta.addWidget(lbl(f"📅 {t['date']}",8,TEXT2))
            if t.get("time"): meta.addWidget(lbl(f"🕐 {t['time']}",8,TEXT2))
            if t.get("priority"):
                pc,_ = PRIORITY_COLORS.get(t["priority"],PRIORITY_COLORS["MEDIUM"])
                meta.addWidget(lbl(t["priority"],8,pc))
            meta.addStretch(); rl.addLayout(meta)

            if t.get("notes"):
                rl.addWidget(lbl(t["notes"][:80]+("…" if len(t["notes"])>80 else ""),8,TEXT3,wrap=True))

            col_name = "Planned" if t["status"]=="planned" else "Active Workflow" if t["status"]=="in_progress" else "Completed"
            jb = GlassButton(f"→ Go to {col_name}", sc)
            jb.setFont(sf(9,QFont.Weight.Medium)); jb.setFixedHeight(28)
            jb.clicked.connect(lambda checked, s=t["status"]: self.jump_to.emit(s))
            rl.addWidget(jb, alignment=Qt.AlignmentFlag.AlignRight)
            self._il.insertWidget(self._il.count()-1, row)

    def refresh(self): self._search(self._inp.text())

# ── Reflections Tab ───────────────────────────────────────────────────────────
class ReflectionsTab(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data
        self._today = date.today().isoformat()
        self.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(self); lay.setContentsMargins(0,12,0,0); lay.setSpacing(16)

        wcard = GlassCard(18)
        wl = QVBoxLayout(wcard); wl.setContentsMargins(24,20,24,20); wl.setSpacing(12)
        wl.addWidget(lbl("📓 Daily Reflection", 15, TEXT1, bold=True))
        wl.addWidget(lbl(date.today().strftime("%A, %d %B %Y"), 10, TEXT2))
        wl.addWidget(lbl("How did today go? Write your overview, wins, thoughts…", 9, TEXT3, italic=True))

        self.editor = QTextEdit()
        self.editor.setFont(sf(10))
        self.editor.setPlaceholderText("Start writing…")
        self.editor.setPlainText(self._data.get("daily_notes",{}).get(self._today,""))
        self.editor.setMinimumHeight(150)
        self.editor.setStyleSheet(f"""
            QTextEdit{{
                background:rgba(255,255,255,0.07);
                color:{TEXT1};
                border:1px solid rgba(255,255,255,0.15);
                border-radius:12px; padding:12px;
            }}
            QTextEdit:focus{{border-color:{ACCENT};background:rgba(10,132,255,0.08);}}
        """)
        wl.addWidget(self.editor)

        sb = GlassButton("Save Reflection", ACCENT2, filled=True)
        sb.setFont(sf(10,QFont.Weight.DemiBold)); sb.setFixedHeight(38)
        sb.clicked.connect(self._save)
        wl.addWidget(sb, alignment=Qt.AlignmentFlag.AlignRight)
        lay.addWidget(wcard)

        lay.addWidget(lbl("Previous Entries", 12, TEXT1, bold=True))

        self._ps = QScrollArea(); self._ps.setWidgetResizable(True); self._ps.setFrameShape(QFrame.Shape.NoFrame)
        self._ps.setStyleSheet("QScrollArea{background:transparent;border:none;}QScrollBar:vertical{background:transparent;width:4px;}QScrollBar::handle:vertical{background:rgba(255,255,255,0.25);border-radius:2px;}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        self._pi = QWidget(); self._pi.setStyleSheet("background:transparent;")
        self._pl = QVBoxLayout(self._pi); self._pl.setContentsMargins(0,0,0,0); self._pl.setSpacing(10); self._pl.addStretch()
        self._ps.setWidget(self._pi); lay.addWidget(self._ps,1)
        self._load_past()

    def _save(self):
        self._data.setdefault("daily_notes",{})[self._today] = self.editor.toPlainText()
        save_data(self._data); self._load_past()

    def _load_past(self):
        while self._pl.count()>1:
            it=self._pl.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        for dk in sorted(self._data.get("daily_notes",{}).keys(), reverse=True):
            txt = self._data["daily_notes"][dk]
            if not txt.strip(): continue
            c = GlassCard(12)
            cl = QVBoxLayout(c); cl.setContentsMargins(18,14,18,14); cl.setSpacing(5)
            top = QHBoxLayout()
            try: dfmt = datetime.strptime(dk,"%Y-%m-%d").strftime("%A, %d %b %Y")
            except: dfmt = dk
            top.addWidget(lbl(dfmt,9,TEAL,bold=True))
            top.addStretch()
            
            db = QPushButton("🗑️  Delete Entry")
            db.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            db.setFont(sf(10, QFont.Weight.Medium))
            db.setFixedSize(130, 32)
            db.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,69,58,0.15);
                    color: {CORAL};
                    border: 1px solid {CORAL}88;
                    border-radius: 8px;
                    padding: 5px 12px;
                }}
                QPushButton:hover {{
                    background: rgba(255,69,58,0.30);
                    border-color: {CORAL};
                }}
                QPushButton:pressed {{
                    background: rgba(255,69,58,0.50);
                    padding-top: 6px;
                }}
            """)
            db.clicked.connect(lambda checked, key=dk: self._delete_entry(key))
            top.addWidget(db)
            cl.addLayout(top)
            
            tl2 = QLabel(txt[:200]+("…" if len(txt)>200 else ""))
            tl2.setFont(sf(9)); tl2.setWordWrap(True)
            tl2.setStyleSheet(f"color:{TEXT2};background:transparent;")
            cl.addWidget(tl2)
            self._pl.insertWidget(self._pl.count()-1, c)

    def _delete_entry(self, key):
        d = QMessageBox(self); d.setWindowTitle("Delete Entry")
        d.setText(f"Delete reflection for {key}?")
        d.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        d.setStyleSheet(f"QMessageBox{{background:{BG_GRAD_MID};}}QLabel{{color:{TEXT1};}}")
        if d.exec() == QMessageBox.StandardButton.Yes:
            self._data["daily_notes"].pop(key,None)
            save_data(self._data); self._load_past()

# ── Boards Tab ────────────────────────────────────────────────────────────────
class BoardsTab(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data
        self.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(self); lay.setContentsMargins(0,10,0,0); lay.setSpacing(14)

        sr = QHBoxLayout(); sr.setSpacing(12)
        self._stat_nums = {}
        for t,c,k in [("Planned",ACCENT,"planned"),("In Progress",AMBER,"in_progress"),("Completed",ACCENT2,"completed"),("Total",PURPLE,"total")]:
            cf = GlassCard(14); cf.setFixedHeight(62)
            cl = QVBoxLayout(cf); cl.setContentsMargins(12,8,12,8); cl.setSpacing(1)
            n = QLabel("0"); n.setFont(sf(20,QFont.Weight.Bold))
            n.setStyleSheet(f"color:{c};background:transparent;"); n.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l = QLabel(t); l.setFont(sf(8)); l.setStyleSheet(f"color:{TEXT3};background:transparent;"); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(n); cl.addWidget(l); sr.addWidget(cf,1); self._stat_nums[k]=n
        lay.addLayout(sr)

        cols = QHBoxLayout(); cols.setSpacing(14)
        self._cp = Column("planned",data); self._cw = Column("in_progress",data); self._cd = Column("completed",data)
        for c in [self._cp,self._cw,self._cd]: c.changed.connect(self.refresh); cols.addWidget(c,1)
        lay.addLayout(cols,1)

    def refresh(self):
        self._cp.refresh(); self._cw.refresh(); self._cd.refresh()
        t = self._data["tasks"]
        self._stat_nums["planned"].setText(str(sum(1 for x in t if x["status"]=="planned")))
        self._stat_nums["in_progress"].setText(str(sum(1 for x in t if x["status"]=="in_progress")))
        self._stat_nums["completed"].setText(str(sum(1 for x in t if x["status"]=="completed")))
        self._stat_nums["total"].setText(str(len(t)))

# ── Reminder Worker ──────────────────────────────────────────────────────────
class ReminderWorker(QObject):
    remind = pyqtSignal(str, str)
    
    def __init__(self, data):
        super().__init__()
        self._data = data
        self._fired = set()
        self._running = True
        self._mutex = QMutex()
    
    def stop(self):
        with QMutexLocker(self._mutex):
            self._running = False
    
    @pyqtSlot()
    def check_reminders(self):
        with QMutexLocker(self._mutex):
            if not self._running:
                return
            tasks_copy = self._data.get("tasks", []).copy()
        
        offs = {"At time": 0, "5 min before": 5, "15 min before": 15,
                "30 min before": 30, "1 hr before": 60, "1 day before": 1440}
        now = datetime.now()
        
        for t in tasks_copy:
            if t["status"] == "completed":
                continue
            rem = t.get("reminder", "None")
            if rem == "None" or not t.get("date") or not t.get("time"):
                continue
            try:
                dt = datetime.strptime(f"{t['date']} {t['time']}", "%Y-%m-%d %H:%M")
            except:
                continue
            rat = dt - timedelta(minutes=offs.get(rem, 0))
            fid = f"{t['id']}-{rem}"
            if abs((now - rat).total_seconds()) < 45 and fid not in self._fired:
                self._fired.add(fid)
                self.remind.emit(t["title"], f"Reminder: {t['title']} at {t['time']}")

# ── Main Window ───────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._data = load_data()
        self.setWindowTitle("OliSched")
        self.resize(1320, 880)
        self.setMinimumSize(980, 660)
        self._reminder_timer = None
        self._reminder_worker = None
        self._reminder_thread = None

        icon_path = resource_path("OliSchedIcon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._build()
        self._start_rem()
        self._boards.refresh()

    def closeEvent(self, event):
        if hasattr(self, '_reminder_worker') and self._reminder_worker:
            self._reminder_worker.stop()
        if hasattr(self, '_reminder_timer') and self._reminder_timer:
            self._reminder_timer.stop()
        if hasattr(self, '_reminder_thread') and self._reminder_thread and self._reminder_thread.isRunning():
            self._reminder_thread.quit()
            self._reminder_thread.wait(2000)
        event.accept()

    def _build(self):
        self._bg = GradientBG()
        self.setCentralWidget(self._bg)
        rl = QVBoxLayout(self._bg); rl.setContentsMargins(0,0,0,0); rl.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("hdr"); hdr.setFixedHeight(70)
        hdr.setStyleSheet("""
            #hdr{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 rgba(255,255,255,0.12),
                    stop:1 rgba(255,255,255,0.06));
                border-bottom: 1px solid rgba(255,255,255,0.15);
            }
        """)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(26,0,26,0); hl.setSpacing(0)

        # REPLACED: Custom Logo Widget instead of star
        logo_widget = LogoWidget()
        hl.addWidget(logo_widget)
        hl.addSpacing(14)

        nc = QVBoxLayout(); nc.setSpacing(1)
        nc.addWidget(lbl("OliSched", 17, TEXT1, bold=True))
        nc.addWidget(lbl("Personal Command Center", 8, TEXT3))
        hl.addLayout(nc); hl.addStretch()

        self._clock = QLabel()
        self._clock.setFont(sf(19, QFont.Weight.Bold))
        self._clock.setStyleSheet(f"color:{TEXT1};background:transparent;")
        self._clock.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._date_lbl = QLabel()
        self._date_lbl.setFont(sf(8))
        self._date_lbl.setStyleSheet(f"color:{TEXT2};background:transparent;")
        self._date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        cc = QVBoxLayout(); cc.setSpacing(1)
        cc.addWidget(self._clock); cc.addWidget(self._date_lbl)
        hl.addLayout(cc)
        self._tick()
        ct = QTimer(self); ct.timeout.connect(self._tick); ct.start(1000)
        rl.addWidget(hdr)

        tb = QFrame(); tb.setObjectName("tb"); tb.setFixedHeight(54)
        tb.setStyleSheet("""
            #tb{
                background:rgba(255,255,255,0.06);
                border-bottom:1px solid rgba(255,255,255,0.12);
            }
        """)
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(26,0,26,0); tbl.setSpacing(6)

        self._tab_btns = []
        for txt,idx in [("📋 Schedule Boards",0),("🔍 Search",1),("📓 Reflections",2)]:
            b = TabButton(txt); b.setChecked(idx==0)
            b.clicked.connect(lambda checked, i=idx: self._switch(i))
            self._tab_btns.append(b); tbl.addWidget(b)

        tbl.addStretch()
        tbl.addWidget(lbl("Active Day:", 9, TEXT3))
        day_lbl = QLabel(date.today().strftime("%d/%m/%Y"))
        day_lbl.setFont(sf(9,QFont.Weight.Bold))
        day_lbl.setStyleSheet(f"""
            color:{TEXT1};
            background:rgba(255,255,255,0.10);
            border:1px solid rgba(255,255,255,0.20);
            border-radius:8px; padding:4px 12px;
        """)
        tbl.addWidget(day_lbl); tbl.addSpacing(14)

        np_btn = GlassButton("＋ New Plan", ACCENT, filled=True)
        np_btn.setFont(sf(10,QFont.Weight.DemiBold)); np_btn.setFixedHeight(36)
        np_btn.clicked.connect(self._on_new); tbl.addWidget(np_btn)
        rl.addWidget(tb)

        self._stack = QStackedWidget(); self._stack.setStyleSheet("background:transparent;")

        def wrap(w, pad=(26,14,26,0)):
            sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.Shape.NoFrame)
            sc.setStyleSheet("QScrollArea{background:transparent;border:none;}QScrollBar:vertical{background:transparent;width:5px;}QScrollBar::handle:vertical{background:rgba(255,255,255,0.25);border-radius:2px;}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
            inner = QWidget(); inner.setStyleSheet("background:transparent;")
            il = QVBoxLayout(inner); il.setContentsMargins(*pad); il.setSpacing(0)
            il.addWidget(w,1); inner.setMinimumHeight(1)
            sc.setWidget(inner); return sc

        self._boards  = BoardsTab(self._data)
        self._search  = SearchPanel(self._data)
        self._search.jump_to.connect(lambda s: self._switch(0))
        self._reflect = ReflectionsTab(self._data)

        self._stack.addWidget(wrap(self._boards))
        self._stack.addWidget(wrap(self._search))
        self._stack.addWidget(wrap(self._reflect))
        rl.addWidget(self._stack,1)

        ft = QFrame(); ft.setObjectName("ft"); ft.setFixedHeight(28)
        ft.setStyleSheet("QFrame{background:rgba(255,255,255,0.05);border-top:1px solid rgba(255,255,255,0.10);}")
        fl = QHBoxLayout(ft); fl.setContentsMargins(26,0,26,0)
        fl.addWidget(lbl("OliSched · Liquid Glass · macOS Tahoe Style", 8, TEXT3))
        fl.addStretch()
        fl.addWidget(lbl("Offline · Secure · Local Storage", 8, TEXT3))
        rl.addWidget(ft)

    def _switch(self, idx):
        self._stack.setCurrentIndex(idx)
        for i,b in enumerate(self._tab_btns): b.setChecked(i==idx)

    def _on_new(self):
        dlg = NewPlanDialog(self)
        dlg.move(self.x() + (self.width()-dlg.width())//2,
                 self.y() + (self.height()-dlg.height())//2)
        if dlg.exec():
            t = dlg.result_task()
            if t["title"]:
                self._data["tasks"].append(t)
                save_data(self._data)
                self._boards.refresh()
                self._search.refresh()
                self._switch(0)

    def _tick(self):
        now = datetime.now()
        self._clock.setText(now.strftime("%I:%M:%S %p"))
        self._date_lbl.setText(now.strftime("%a, %b %d, %Y"))

    def _start_rem(self):
        self._reminder_worker = ReminderWorker(self._data)
        self._reminder_thread = QThread()
        self._reminder_worker.moveToThread(self._reminder_thread)
        
        self._reminder_worker.remind.connect(self._show_remind)
        self._reminder_thread.finished.connect(self._reminder_worker.deleteLater)
        
        self._reminder_timer = QTimer()
        self._reminder_timer.moveToThread(self._reminder_thread)
        self._reminder_timer.timeout.connect(self._reminder_worker.check_reminders)
        
        self._reminder_thread.started.connect(lambda: self._reminder_timer.start(30000))
        self._reminder_thread.start()
        self._reminder_worker.check_reminders()

    def _show_remind(self, title, msg):
        m = QMessageBox(self); m.setWindowTitle("🔔 Reminder")
        m.setText(f"<b style='color:{ACCENT2};font-size:13pt;'>{title}</b>")
        m.setInformativeText(msg)
        m.setStyleSheet(f"""
            QMessageBox{{background:{BG_GRAD_MID};border-radius:16px;}}
            QLabel{{color:{TEXT1};}}
            QPushButton{{
                background:rgba(255,255,255,0.12);color:{TEXT1};
                border:1px solid rgba(255,255,255,0.22);border-radius:9px;
                padding:7px 22px;
            }}
            QPushButton:hover{{background:rgba(255,255,255,0.22);}}
        """)
        m.exec()

# ── Entry ─────────────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("OliSched")
    app.setStyle("Fusion")

    icon_path = resource_path("OliSchedIcon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,          QColor(BG_GRAD_TOP))
    p.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT1))
    p.setColor(QPalette.ColorRole.Base,            QColor(BG_GRAD_MID))
    p.setColor(QPalette.ColorRole.Text,            QColor(TEXT1))
    p.setColor(QPalette.ColorRole.Button,          QColor(BG_GRAD_MID))
    p.setColor(QPalette.ColorRole.ButtonText,      QColor(TEXT1))
    p.setColor(QPalette.ColorRole.Highlight,       QColor(ACCENT))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(p)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()