import sys, json, os, uuid
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QScrollArea,
    QFrame, QDialog, QTimeEdit, QDateEdit, QComboBox,
    QMessageBox, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QTime, QDate, pyqtSignal
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QPainter, QBrush,
    QLinearGradient, QRadialGradient, QCursor, QIcon, QPixmap
)

# ── Resource path ─────────────────────────────────────────────────────────────
def resource_path(p):
    base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, p)

# ── Storage ───────────────────────────────────────────────────────────────────
DATA_FILE = os.path.join(os.path.expanduser("~"), ".olisched_tahoe.json")

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"tasks": [], "daily_notes": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── Palette ───────────────────────────────────────────────────────────────────
BG_TOP    = "#1a1a2e"
BG_MID    = "#16213e"
BG_BOT    = "#0f3460"
TEXT1     = "#f5f5f7"
TEXT2     = "#a0b4c8"
TEXT3     = "#5a7a8a"
ACCENT    = "#0a84ff"
GREEN     = "#30d158"
AMBER     = "#ff9f0a"
CORAL     = "#ff453a"
PURPLE    = "#bf5af2"
TEAL      = "#5ac8fa"

PRIORITY_COLORS = {
    "LOW":    (GREEN,  "#0d3320"),
    "MEDIUM": (ACCENT, "#0a2040"),
    "HIGH":   (CORAL,  "#3a1010"),
}
STATUS_COLORS = {
    "planned":     ACCENT,
    "in_progress": AMBER,
    "completed":   GREEN,
}

# ── Font ──────────────────────────────────────────────────────────────────────
def sf(size, weight=QFont.Weight.Normal, italic=False):
    f = QFont()
    f.setFamilies(["SF Pro Display", "SF Pro Text", "Helvetica Neue",
                   "Segoe UI Variable Display", "Segoe UI", "Arial"])
    f.setPointSize(size)
    f.setWeight(weight)
    f.setItalic(italic)
    if size >= 13:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, -0.3)
    return f

# ── Helpers ───────────────────────────────────────────────────────────────────
def lbl(text, size=10, color=TEXT1, bold=False, italic=False, wrap=False):
    l = QLabel(text)
    l.setFont(sf(size, QFont.Weight.Bold if bold else QFont.Weight.Normal, italic))
    l.setStyleSheet(f"color:{color}; background:transparent;")
    if wrap:
        l.setWordWrap(True)
    return l

def divider():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("background:rgba(255,255,255,0.12); max-height:1px;")
    return f

def glass_btn(text, color, filled=False, h=30):
    b = QPushButton(text)
    b.setFont(sf(9, QFont.Weight.Medium))
    b.setFixedHeight(h)
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    if filled:
        b.setStyleSheet(f"""
            QPushButton {{
                background:{color}; color:#fff;
                border:none; border-radius:9px; padding:0 18px; font-weight:600;
            }}
            QPushButton:hover {{ background:{color}dd; }}
            QPushButton:pressed {{ background:{color}aa; padding-top:1px; }}
        """)
    else:
        b.setStyleSheet(f"""
            QPushButton {{
                background:rgba(255,255,255,0.09); color:{color};
                border:1px solid rgba(255,255,255,0.22); border-radius:9px; padding:0 14px;
            }}
            QPushButton:hover {{ background:rgba(255,255,255,0.16); border-color:{color}; }}
            QPushButton:pressed {{ background:rgba(255,255,255,0.05); padding-top:1px; }}
        """)
    return b

def glass_card(radius=16, accent=None):
    f = QFrame()
    f.setObjectName("gc")
    if accent:
        f.setStyleSheet(f"""
            #gc {{
                background:rgba(255,255,255,0.07);
                border:1px solid rgba(255,255,255,0.14);
                border-left:3px solid {accent};
                border-radius:{radius}px;
            }}
            #gc:hover {{ background:rgba(255,255,255,0.11); }}
        """)
    else:
        f.setStyleSheet(f"""
            #gc {{
                background:rgba(255,255,255,0.07);
                border:1px solid rgba(255,255,255,0.14);
                border-radius:{radius}px;
            }}
            #gc:hover {{ background:rgba(255,255,255,0.10); }}
        """)
    return f

# ── Static gradient background ────────────────────────────────────────────────
class GradientBG(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._px = None

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._px = None  # invalidate cache

    def paintEvent(self, e):
        W, H = self.width(), self.height()
        if W <= 0 or H <= 0:
            return
        if self._px is None or self._px.width() != W or self._px.height() != H:
            self._px = QPixmap(W, H)
            p = QPainter(self._px)
            g = QLinearGradient(0, 0, 0, H)
            g.setColorAt(0,   QColor(BG_TOP))
            g.setColorAt(0.5, QColor(BG_MID))
            g.setColorAt(1,   QColor(BG_BOT))
            p.fillRect(0, 0, W, H, QBrush(g))
            for ox, oy, or_, col in [
                (0.15, 0.12, 0.32, QColor(10, 132, 255, 20)),
                (0.80, 0.55, 0.28, QColor(191, 90, 242, 16)),
                (0.50, 0.88, 0.25, QColor(10, 132, 255, 14)),
            ]:
                rg = QRadialGradient(ox * W, oy * H, or_ * W)
                rg.setColorAt(0, col)
                rg.setColorAt(1, QColor(0, 0, 0, 0))
                p.fillRect(0, 0, W, H, QBrush(rg))
            p.end()
        QPainter(self).drawPixmap(0, 0, self._px)

# ── Task Card ─────────────────────────────────────────────────────────────────
class TaskCard(QFrame):
    sig_delete = pyqtSignal(str)
    sig_status = pyqtSignal(str, str)

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        tid = task["id"]
        status = task["status"]
        done = status == "completed"
        ac = STATUS_COLORS.get(status, ACCENT)
        pc, pbg = PRIORITY_COLORS.get(task.get("priority", "MEDIUM"), PRIORITY_COLORS["MEDIUM"])

        self.setObjectName("tc")
        self.setStyleSheet(f"""
            #tc {{
                background:rgba(255,255,255,0.07);
                border:1px solid rgba(255,255,255,0.13);
                border-left:3px solid {ac};
                border-radius:13px;
            }}
            #tc:hover {{ background:rgba(255,255,255,0.11); }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(15, 12, 15, 12)
        lay.setSpacing(7)

        # Row 1: time · duration · priority
        r1 = QHBoxLayout(); r1.setSpacing(8)
        if task.get("time"):
            r1.addWidget(lbl(f"🕐  {task['time']}", 8, TEXT2))
        if task.get("duration"):
            r1.addWidget(lbl(f"·  {task['duration']}m", 8, TEXT3))
        r1.addStretch()
        pri = task.get("priority", "MEDIUM")
        pb = QLabel(f"  {pri}  ")
        pb.setFont(sf(7, QFont.Weight.Bold))
        pb.setStyleSheet(f"color:{pc}; background:{pbg}; border:1px solid {pc}55; border-radius:5px;")
        r1.addWidget(pb)
        lay.addLayout(r1)

        # Title
        tl = QLabel(task.get("title", ""))
        tl.setFont(sf(12, QFont.Weight.Bold))
        tl.setWordWrap(True)
        if done:
            tl.setStyleSheet("color:rgba(245,245,247,0.28); text-decoration:line-through; background:transparent;")
        else:
            tl.setStyleSheet(f"color:{TEXT1}; background:transparent;")
        lay.addWidget(tl)

        if task.get("notes"):
            nl = QLabel(task["notes"][:95] + ("…" if len(task["notes"]) > 95 else ""))
            nl.setFont(sf(9, italic=True))
            nl.setWordWrap(True)
            nl.setStyleSheet(f"color:{TEXT3}; background:transparent;")
            lay.addWidget(nl)

        if task.get("reminder") and task["reminder"] != "None":
            lay.addWidget(lbl(f"🔔  {task['reminder']}", 8, AMBER, italic=True))

        lay.addWidget(divider())

        # Buttons — capture tid by value with default arg
        br = QHBoxLayout(); br.setSpacing(8)
        db = glass_btn("🗑", CORAL, h=28)
        db.setFixedHeight(28)
        db.clicked.connect(self._confirm_del)
        br.addWidget(db)
        br.addStretch()

        if status == "planned":
            sb = glass_btn("⚡  Start", AMBER, h=28)
            sb.clicked.connect(lambda checked=False, t=tid: self.sig_status.emit(t, "in_progress"))
            br.addWidget(sb)
            cb = glass_btn("✓  Done", GREEN, filled=True, h=28)
            cb.clicked.connect(lambda checked=False, t=tid: self.sig_status.emit(t, "completed"))
            br.addWidget(cb)
        elif status == "in_progress":
            cb = glass_btn("✓  Done", GREEN, filled=True, h=28)
            cb.clicked.connect(lambda checked=False, t=tid: self.sig_status.emit(t, "completed"))
            br.addWidget(cb)
        else:
            mb = glass_btn("↩  Revert", ACCENT, h=28)
            mb.clicked.connect(lambda checked=False, t=tid: self.sig_status.emit(t, "planned"))
            br.addWidget(mb)

        lay.addLayout(br)

    def _confirm_del(self):
        d = QMessageBox(self)
        d.setWindowTitle("Delete Task")
        d.setText(f"Delete  «{self.task.get('title', '')}»?")
        d.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        d.setStyleSheet(f"QMessageBox{{background:{BG_MID};}} QLabel{{color:{TEXT1};}}")
        if d.exec() == QMessageBox.StandardButton.Yes:
            self.sig_delete.emit(self.task["id"])

# ── Column ────────────────────────────────────────────────────────────────────
class Column(QFrame):
    changed = pyqtSignal()
    HEADERS = {
        "planned":     ("PLANNED",         ACCENT, "Ready"),
        "in_progress": ("ACTIVE WORKFLOW",  AMBER,  "In Progress"),
        "completed":   ("COMPLETED",        GREEN,  "Crossed Out"),
    }

    def __init__(self, status, data, parent=None):
        super().__init__(parent)
        self.status = status
        self._data = data
        title, color, sub = self.HEADERS[status]
        self.setObjectName("col")
        self.setStyleSheet(f"""
            #col {{
                background:rgba(255,255,255,0.06);
                border:1px solid rgba(255,255,255,0.13);
                border-radius:18px;
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(10)

        hr = QHBoxLayout(); hr.setSpacing(8)
        dot = QLabel("●"); dot.setFont(sf(10))
        dot.setStyleSheet(f"color:{color}; background:transparent;")
        tl = QLabel(title); tl.setFont(sf(11, QFont.Weight.Bold))
        tl.setStyleSheet(f"color:{TEXT1}; background:transparent;")
        self._badge = QLabel("0")
        self._badge.setFont(sf(9, QFont.Weight.Bold))
        self._badge.setStyleSheet(f"color:{color}; background:{color}22; border:1px solid {color}44; border-radius:9px; padding:1px 9px;")
        sl = QLabel(sub); sl.setFont(sf(8, italic=True))
        sl.setStyleSheet(f"color:{TEXT3}; background:transparent;")
        hr.addWidget(dot); hr.addWidget(tl); hr.addWidget(self._badge)
        hr.addStretch(); hr.addWidget(sl)
        lay.addLayout(hr)
        lay.addWidget(divider())

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet("""
            QScrollArea { background:transparent; border:none; }
            QScrollBar:vertical { background:transparent; width:4px; }
            QScrollBar::handle:vertical { background:rgba(255,255,255,0.25); border-radius:2px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
        """)
        self._inner = QWidget()
        self._inner.setStyleSheet("background:transparent;")
        self._il = QVBoxLayout(self._inner)
        self._il.setContentsMargins(0, 0, 4, 0)
        self._il.setSpacing(8)
        self._il.addStretch()
        self._scroll.setWidget(self._inner)
        lay.addWidget(self._scroll, 1)

    def refresh(self):
        while self._il.count() > 1:
            it = self._il.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        tasks = sorted(
            [t for t in self._data["tasks"] if t["status"] == self.status],
            key=lambda t: (t.get("date", ""), t.get("time", ""))
        )
        for t in tasks:
            c = TaskCard(t)
            c.sig_delete.connect(self._del)
            c.sig_status.connect(self._chg)
            self._il.insertWidget(self._il.count() - 1, c)
        self._badge.setText(str(len(tasks)))

    def _del(self, tid):
        self._data["tasks"] = [t for t in self._data["tasks"] if t["id"] != tid]
        save_data(self._data)
        self.changed.emit()

    def _chg(self, tid, ns):
        for t in self._data["tasks"]:
            if t["id"] == tid:
                t["status"] = ns
                break
        save_data(self._data)
        self.changed.emit()

# ── New Plan Dialog ───────────────────────────────────────────────────────────
class NewPlanDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.task = task or {}
        self.setWindowTitle("New Plan")
        self.setFixedSize(500, 530)
        self.setStyleSheet(f"""
            QDialog {{ background:{BG_MID}; }}
            QLabel {{ color:{TEXT2}; background:transparent; }}
            QLineEdit, QTextEdit, QTimeEdit, QDateEdit, QComboBox {{
                background:rgba(255,255,255,0.09); color:{TEXT1};
                border:1px solid rgba(255,255,255,0.20);
                border-radius:9px; padding:7px 11px;
                font-family:'Segoe UI'; font-size:10pt;
            }}
            QLineEdit:focus, QTextEdit:focus {{ border-color:{ACCENT}; }}
            QComboBox::drop-down {{ border:none; width:22px; }}
            QComboBox QAbstractItemView {{
                background:{BG_MID}; color:{TEXT1};
                selection-background-color:{ACCENT}44;
                border:1px solid rgba(255,255,255,0.20);
            }}
            QScrollBar:vertical {{ background:transparent; width:0px; }}
        """)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(12)

        lay.addWidget(lbl("New Plan", 18, TEXT1, bold=True))

        lay.addWidget(lbl("Title", 9, TEXT2))
        self.e_title = QLineEdit(self.task.get("title", ""))
        self.e_title.setPlaceholderText("What do you need to do?")
        lay.addWidget(self.e_title)

        r1 = QHBoxLayout(); r1.setSpacing(12)

        def col(label_text, widget):
            c = QVBoxLayout(); c.setSpacing(4)
            c.addWidget(lbl(label_text, 9, TEXT2))
            c.addWidget(widget)
            return c

        self.e_date = QDateEdit()
        self.e_date.setCalendarPopup(True)
        # Minimum date = today (cannot pick past dates)
        self.e_date.setMinimumDate(QDate.currentDate())
        saved_date = QDate.fromString(self.task.get("date", date.today().isoformat()), "yyyy-MM-dd")
        # If editing an existing task with a past date, allow it; otherwise floor to today
        if saved_date < QDate.currentDate() and not self.task.get("id"):
            saved_date = QDate.currentDate()
        self.e_date.setDate(saved_date)
        self.e_date.setDisplayFormat("yyyy-MM-dd")
        # When date changes, update minimum time if today is selected
        self.e_date.dateChanged.connect(self._on_date_changed)
        r1.addLayout(col("Date", self.e_date))

        self.e_time = QTimeEdit()
        self.e_time.setDisplayFormat("HH:mm")
        if self.task.get("time"):
            self.e_time.setTime(QTime.fromString(self.task["time"], "HH:mm"))
        else:
            # Default to next round 5 minutes from now
            now_t = QTime.currentTime().addSecs(60)
            rounded = QTime(now_t.hour(), (now_t.minute() // 5 + 1) * 5 % 60)
            self.e_time.setTime(rounded)
        self._on_date_changed(self.e_date.date())  # apply minimum time immediately
        r1.addLayout(col("Time", self.e_time))

        self.e_dur = QLineEdit(str(self.task.get("duration", "")))
        self.e_dur.setPlaceholderText("mins")
        r1.addLayout(col("Duration", self.e_dur))
        lay.addLayout(r1)

        r2 = QHBoxLayout(); r2.setSpacing(12)

        self.e_pri = QComboBox()
        for p in ["LOW", "MEDIUM", "HIGH"]:
            self.e_pri.addItem(p)
        self.e_pri.setCurrentText(self.task.get("priority", "MEDIUM"))
        r2.addLayout(col("Priority", self.e_pri))

        self.e_rem = QComboBox()
        for o in ["None", "At time", "5 min before", "15 min before", "30 min before", "1 hr before", "1 day before"]:
            self.e_rem.addItem(o)
        self.e_rem.setCurrentText(self.task.get("reminder", "None"))
        r2.addLayout(col("Reminder", self.e_rem))

        self.e_status = QComboBox()
        for v, t in [("planned", "Planned"), ("in_progress", "In Progress"), ("completed", "Completed")]:
            self.e_status.addItem(t, v)
        cur = self.task.get("status", "planned")
        for i in range(self.e_status.count()):
            if self.e_status.itemData(i) == cur:
                self.e_status.setCurrentIndex(i)
                break
        r2.addLayout(col("Status", self.e_status))
        lay.addLayout(r2)

        lay.addWidget(lbl("Notes", 9, TEXT2))
        self.e_notes = QTextEdit(self.task.get("notes", ""))
        self.e_notes.setPlaceholderText("Details, context, overview…")
        self.e_notes.setFixedHeight(85)
        lay.addWidget(self.e_notes)

        lay.addStretch()

        br = QHBoxLayout(); br.setSpacing(12)
        cancel = glass_btn("Cancel", CORAL, h=38)
        cancel.clicked.connect(self.reject)
        save = glass_btn("Save Plan", ACCENT, filled=True, h=38)
        save.setFont(sf(11, QFont.Weight.DemiBold))
        save.clicked.connect(self._validate_and_save)
        br.addWidget(cancel)
        br.addStretch()
        br.addWidget(save)
        lay.addLayout(br)

    def _on_date_changed(self, qdate):
        """If today is selected, block times in the past."""
        if qdate == QDate.currentDate():
            now_time = QTime.currentTime()
            self.e_time.setMinimumTime(now_time)
            # If current selected time is now in the past, bump it forward
            if self.e_time.time() < now_time:
                rounded = now_time.addSecs(60)
                self.e_time.setTime(QTime(rounded.hour(), (rounded.minute() // 5 + 1) * 5 % 60))
        else:
            # Future date — any time is valid
            self.e_time.setMinimumTime(QTime(0, 0))

    def _validate_and_save(self):
        title = self.e_title.text().strip()
        if not title:
            msg = QMessageBox(self)
            msg.setWindowTitle("Missing Title")
            msg.setText("Please enter a task title.")
            msg.setStyleSheet(f"QMessageBox{{background:#16213e;}} QLabel{{color:#f5f5f7;}}")
            msg.exec()
            return

        # Check the chosen date+time is not in the past
        chosen_dt = datetime.strptime(
            f"{self.e_date.date().toString('yyyy-MM-dd')} {self.e_time.time().toString('HH:mm')}",
            "%Y-%m-%d %H:%M"
        )
        if chosen_dt < datetime.now() and not self.task.get("id"):
            msg = QMessageBox(self)
            msg.setWindowTitle("Past Time")
            msg.setText("You cannot schedule a task in the past.\nPlease choose a future date and time.")
            msg.setStyleSheet(f"QMessageBox{{background:#16213e;}} QLabel{{color:#f5f5f7;}}")
            msg.exec()
            return

        self.accept()

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
    STATUS_LABEL = {
        "planned":     "📋 Planned",
        "in_progress": "⚡ In Progress",
        "completed":   "✅ Completed",
    }

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data
        self.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(14)

        hcard = glass_card(14)
        hl = QVBoxLayout(hcard)
        hl.setContentsMargins(20, 18, 20, 18)
        hl.setSpacing(10)
        hl.addWidget(lbl("🔍  Search Tasks", 15, TEXT1, bold=True))
        hl.addWidget(lbl("Search by title, notes, date, or priority", 9, TEXT3, italic=True))

        bar = QHBoxLayout(); bar.setSpacing(10)
        self._inp = QLineEdit()
        self._inp.setFont(sf(11))
        self._inp.setPlaceholderText("Search anything…")
        self._inp.setFixedHeight(42)
        self._inp.setStyleSheet(f"""
            QLineEdit {{
                background:rgba(255,255,255,0.09); color:{TEXT1};
                border:1px solid rgba(255,255,255,0.20);
                border-radius:12px; padding:0 16px;
            }}
            QLineEdit:focus {{ border-color:{ACCENT}; background:rgba(10,132,255,0.10); }}
        """)
        self._inp.textChanged.connect(self._search)
        bar.addWidget(self._inp, 1)

        clr = glass_btn("✕", CORAL, h=42)
        clr.setFixedSize(42, 42)
        clr.clicked.connect(lambda: self._inp.clear())
        bar.addWidget(clr)
        hl.addLayout(bar)
        lay.addWidget(hcard)

        self._count_lbl = lbl("", 9, TEXT3, italic=True)
        lay.addWidget(self._count_lbl)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet("QScrollArea{background:transparent;border:none;} QScrollBar:vertical{background:transparent;width:4px;} QScrollBar::handle:vertical{background:rgba(255,255,255,0.25);border-radius:2px;} QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        self._inner = QWidget()
        self._inner.setStyleSheet("background:transparent;")
        self._il = QVBoxLayout(self._inner)
        self._il.setContentsMargins(0, 0, 4, 0)
        self._il.setSpacing(10)
        self._il.addStretch()
        self._scroll.setWidget(self._inner)
        lay.addWidget(self._scroll, 1)

    def _search(self, query):
        while self._il.count() > 1:
            it = self._il.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        q = query.strip().lower()
        if not q:
            self._count_lbl.setText("")
            return

        results = [t for t in self._data["tasks"]
                   if q in t.get("title", "").lower()
                   or q in t.get("notes", "").lower()
                   or q in t.get("date", "").lower()
                   or q in t.get("priority", "").lower()]

        self._count_lbl.setText(f"{len(results)} result{'s' if len(results) != 1 else ''} found")

        for t in results:
            sc = STATUS_COLORS.get(t["status"], ACCENT)
            row = glass_card(12, accent=sc)
            rl = QVBoxLayout(row)
            rl.setContentsMargins(15, 12, 15, 12)
            rl.setSpacing(5)

            top = QHBoxLayout()
            done = t["status"] == "completed"
            tl2 = QLabel(t.get("title", ""))
            tl2.setFont(sf(12, QFont.Weight.Bold))
            if done:
                tl2.setStyleSheet("color:rgba(245,245,247,0.28); text-decoration:line-through; background:transparent;")
            else:
                tl2.setStyleSheet(f"color:{TEXT1}; background:transparent;")
            top.addWidget(tl2)
            top.addStretch()
            sp = QLabel(self.STATUS_LABEL.get(t["status"], ""))
            sp.setFont(sf(8, QFont.Weight.Bold))
            sp.setStyleSheet(f"color:{sc}; background:{sc}22; border:1px solid {sc}44; border-radius:8px; padding:2px 9px;")
            top.addWidget(sp)
            rl.addLayout(top)

            meta = QHBoxLayout(); meta.setSpacing(14)
            if t.get("date"): meta.addWidget(lbl(f"📅 {t['date']}", 8, TEXT2))
            if t.get("time"): meta.addWidget(lbl(f"🕐 {t['time']}", 8, TEXT2))
            if t.get("priority"):
                pc, _ = PRIORITY_COLORS.get(t["priority"], PRIORITY_COLORS["MEDIUM"])
                meta.addWidget(lbl(t["priority"], 8, pc))
            meta.addStretch()
            rl.addLayout(meta)

            if t.get("notes"):
                rl.addWidget(lbl(t["notes"][:80] + ("…" if len(t["notes"]) > 80 else ""), 8, TEXT3, wrap=True))

            col_name = {"planned": "Planned", "in_progress": "Active Workflow", "completed": "Completed"}.get(t["status"], "")
            jb = glass_btn(f"→  Go to {col_name}", sc, h=28)
            jb.clicked.connect(lambda checked=False, s=t["status"]: self.jump_to.emit(s))
            rl.addWidget(jb, alignment=Qt.AlignmentFlag.AlignRight)
            self._il.insertWidget(self._il.count() - 1, row)

    def refresh(self):
        self._search(self._inp.text())

# ── Reflections Tab ───────────────────────────────────────────────────────────
class ReflectionsTab(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data
        self._today = date.today().isoformat()
        self.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(16)

        wcard = glass_card(18)
        wl = QVBoxLayout(wcard)
        wl.setContentsMargins(24, 20, 24, 20)
        wl.setSpacing(12)
        wl.addWidget(lbl("📓  Daily Reflection", 15, TEXT1, bold=True))
        wl.addWidget(lbl(date.today().strftime("%A, %d %B %Y"), 10, TEXT2))
        wl.addWidget(lbl("How did today go? Write your overview, wins, thoughts…", 9, TEXT3, italic=True))

        self.editor = QTextEdit()
        self.editor.setFont(sf(10))
        self.editor.setPlaceholderText("Start writing…")
        self.editor.setPlainText(self._data.get("daily_notes", {}).get(self._today, ""))
        self.editor.setMinimumHeight(150)
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                background:rgba(255,255,255,0.08); color:{TEXT1};
                border:1px solid rgba(255,255,255,0.16);
                border-radius:11px; padding:12px;
            }}
            QTextEdit:focus {{ border-color:{ACCENT}; }}
        """)
        wl.addWidget(self.editor)

        sb = glass_btn("Save Reflection", GREEN, filled=True, h=38)
        sb.setFont(sf(10, QFont.Weight.DemiBold))
        sb.clicked.connect(self._save)
        wl.addWidget(sb, alignment=Qt.AlignmentFlag.AlignRight)
        lay.addWidget(wcard)

        lay.addWidget(lbl("Previous Entries", 12, TEXT1, bold=True))

        self._ps = QScrollArea()
        self._ps.setWidgetResizable(True)
        self._ps.setFrameShape(QFrame.Shape.NoFrame)
        self._ps.setStyleSheet("QScrollArea{background:transparent;border:none;} QScrollBar:vertical{background:transparent;width:4px;} QScrollBar::handle:vertical{background:rgba(255,255,255,0.25);border-radius:2px;} QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        self._pi = QWidget()
        self._pi.setStyleSheet("background:transparent;")
        self._pl = QVBoxLayout(self._pi)
        self._pl.setContentsMargins(0, 0, 0, 0)
        self._pl.setSpacing(10)
        self._pl.addStretch()
        self._ps.setWidget(self._pi)
        lay.addWidget(self._ps, 1)
        self._load_past()

    def _save(self):
        self._data.setdefault("daily_notes", {})[self._today] = self.editor.toPlainText()
        save_data(self._data)
        self._load_past()

    def _load_past(self):
        while self._pl.count() > 1:
            it = self._pl.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for dk in sorted(self._data.get("daily_notes", {}).keys(), reverse=True):
            txt = self._data["daily_notes"][dk]
            if not txt.strip():
                continue
            c = glass_card(12)
            cl = QVBoxLayout(c)
            cl.setContentsMargins(18, 14, 18, 14)
            cl.setSpacing(5)
            top = QHBoxLayout()
            try:
                dfmt = datetime.strptime(dk, "%Y-%m-%d").strftime("%A, %d %b %Y")
            except:
                dfmt = dk
            top.addWidget(lbl(dfmt, 9, TEAL, bold=True))
            top.addStretch()
            db = glass_btn("🗑", CORAL, h=28)
            db.setFixedHeight(28)
            db.clicked.connect(lambda checked=False, key=dk: self._delete_entry(key))
            top.addWidget(db)
            cl.addLayout(top)
            tl2 = QLabel(txt[:200] + ("…" if len(txt) > 200 else ""))
            tl2.setFont(sf(9))
            tl2.setWordWrap(True)
            tl2.setStyleSheet(f"color:{TEXT2}; background:transparent;")
            cl.addWidget(tl2)
            self._pl.insertWidget(self._pl.count() - 1, c)

    def _delete_entry(self, key):
        d = QMessageBox(self)
        d.setWindowTitle("Delete Entry")
        d.setText(f"Delete reflection for  {key}?")
        d.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        d.setStyleSheet(f"QMessageBox{{background:{BG_MID};}} QLabel{{color:{TEXT1};}}")
        if d.exec() == QMessageBox.StandardButton.Yes:
            self._data["daily_notes"].pop(key, None)
            save_data(self._data)
            self._load_past()

# ── Boards Tab ────────────────────────────────────────────────────────────────
class BoardsTab(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data
        self.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(14)

        sr = QHBoxLayout(); sr.setSpacing(12)
        self._stat_nums = {}
        for t, c, k in [("Planned", ACCENT, "planned"), ("In Progress", AMBER, "in_progress"),
                         ("Completed", GREEN, "completed"), ("Total", PURPLE, "total")]:
            cf = glass_card(13)
            cf.setFixedHeight(60)
            cl = QVBoxLayout(cf)
            cl.setContentsMargins(12, 8, 12, 8)
            cl.setSpacing(1)
            n = QLabel("0")
            n.setFont(sf(20, QFont.Weight.Bold))
            n.setStyleSheet(f"color:{c}; background:transparent;")
            n.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l2 = QLabel(t)
            l2.setFont(sf(8))
            l2.setStyleSheet(f"color:{TEXT3}; background:transparent;")
            l2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(n); cl.addWidget(l2)
            sr.addWidget(cf, 1)
            self._stat_nums[k] = n
        lay.addLayout(sr)

        cols = QHBoxLayout(); cols.setSpacing(14)
        self._cp = Column("planned", data)
        self._cw = Column("in_progress", data)
        self._cd = Column("completed", data)
        for c in [self._cp, self._cw, self._cd]:
            c.changed.connect(self.refresh)
            cols.addWidget(c, 1)
        lay.addLayout(cols, 1)

    def refresh(self):
        self._cp.refresh(); self._cw.refresh(); self._cd.refresh()
        t = self._data["tasks"]
        self._stat_nums["planned"].setText(str(sum(1 for x in t if x["status"] == "planned")))
        self._stat_nums["in_progress"].setText(str(sum(1 for x in t if x["status"] == "in_progress")))
        self._stat_nums["completed"].setText(str(sum(1 for x in t if x["status"] == "completed")))
        self._stat_nums["total"].setText(str(len(t)))

# ── Reminder Checker ─────────────────────────────────────────────────────────
class ReminderChecker:
    """
    Checks every 1 second. Fires the instant remind_at is reached.
    Window of 2 seconds handles any single missed tick.
    Result: reminder fires within 1-2 seconds of the exact moment.
    """
    OFFSETS = {
        "At time":        0,
        "5 min before":   5,
        "15 min before":  15,
        "30 min before":  30,
        "1 hr before":    60,
        "1 day before":   1440,
    }

    def __init__(self, data, on_remind):
        self._data  = data
        self._cb    = on_remind
        self._fired = set()
        self._timer = QTimer()
        self._timer.setInterval(1000)    # every 1 second — precise
        self._timer.timeout.connect(self.check)
        self._timer.start()

    def check(self):
        now = datetime.now()
        for t in self._data.get("tasks", []):
            if t.get("status") == "completed":
                continue
            rem = t.get("reminder", "None")
            if rem == "None" or not t.get("date") or not t.get("time"):
                continue
            try:
                task_dt = datetime.strptime(
                    f"{t['date']} {t['time']}", "%Y-%m-%d %H:%M"
                )
            except Exception:
                continue
            remind_at = task_dt - timedelta(minutes=self.OFFSETS.get(rem, 0))
            diff_secs = (now - remind_at).total_seconds()
            fid = f"{t['id']}::{rem}"
            # Fire the moment diff_secs enters 0–2 range (i.e. right on time)
            if 0 <= diff_secs <= 2 and fid not in self._fired:
                self._fired.add(fid)
                if rem == "At time":
                    msg = f"It's time:  {t['title']}\nScheduled at {t['time']} on {t['date']}"
                else:
                    msg = f"{rem}:  {t['title']}\nScheduled at {t['time']} on {t['date']}"
                self._cb(t["title"], msg)

    def stop(self):
        self._timer.stop()

# ── Tab Button ────────────────────────────────────────────────────────────────
class TabBtn(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFont(sf(10, QFont.Weight.Medium))
        self.setFixedHeight(32)
        self.toggled.connect(lambda _: self._style())
        self._style()

    def _style(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background:rgba(255,255,255,0.18); color:{TEXT1};
                    border:1px solid rgba(255,255,255,0.28);
                    border-radius:10px; padding:0 18px; font-weight:600;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background:transparent; color:{TEXT2};
                    border:1px solid transparent;
                    border-radius:10px; padding:0 18px;
                }}
                QPushButton:hover {{ background:rgba(255,255,255,0.09); color:{TEXT1}; }}
            """)

# ── Main Window ───────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._data = load_data()
        self.setWindowTitle("OliSched")
        self.resize(1320, 880)
        self.setMinimumSize(980, 660)

        icon_path = resource_path("OliSchedIcon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._build()
        self._start_rem()
        self._boards.refresh()

    def _build(self):
        self._bg = GradientBG()
        self.setCentralWidget(self._bg)
        rl = QVBoxLayout(self._bg)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QFrame(); hdr.setObjectName("hdr"); hdr.setFixedHeight(68)
        hdr.setStyleSheet("#hdr { background:rgba(255,255,255,0.10); border-bottom:1px solid rgba(255,255,255,0.14); }")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(26, 0, 26, 0); hl.setSpacing(0)

        logo_box = QFrame(); logo_box.setObjectName("lb"); logo_box.setFixedSize(44, 44)
        logo_box.setStyleSheet(f"#lb {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {ACCENT},stop:1 {PURPLE}); border:none; border-radius:13px; }}")
        lbx = QHBoxLayout(logo_box); lbx.setContentsMargins(4, 4, 4, 4)

        icon_path = resource_path("OliSchedIcon.ico")
        li = QLabel()
        if os.path.exists(icon_path):
            px = QPixmap(icon_path).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            li.setPixmap(px)
        else:
            li.setText("◈"); li.setFont(sf(18, QFont.Weight.Bold))
        li.setStyleSheet("background:transparent;"); li.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbx.addWidget(li); hl.addWidget(logo_box); hl.addSpacing(14)

        nc = QVBoxLayout(); nc.setSpacing(1)
        nc.addWidget(lbl("OliSched", 17, TEXT1, bold=True))
        nc.addWidget(lbl("Personal Command Center", 8, TEXT3))
        hl.addLayout(nc); hl.addStretch()

        self._clock = QLabel()
        self._clock.setFont(sf(18, QFont.Weight.Bold))
        self._clock.setStyleSheet(f"color:{TEXT1}; background:transparent;")
        self._clock.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._date_lbl = QLabel()
        self._date_lbl.setFont(sf(8))
        self._date_lbl.setStyleSheet(f"color:{TEXT2}; background:transparent;")
        self._date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        cc = QVBoxLayout(); cc.setSpacing(1)
        cc.addWidget(self._clock); cc.addWidget(self._date_lbl)
        hl.addLayout(cc)
        self._tick()
        ct = QTimer(self); ct.timeout.connect(self._tick); ct.start(1000)
        rl.addWidget(hdr)

        # ── Tab bar ───────────────────────────────────────────────────────────
        tb = QFrame(); tb.setObjectName("tb"); tb.setFixedHeight(52)
        tb.setStyleSheet("#tb { background:rgba(255,255,255,0.06); border-bottom:1px solid rgba(255,255,255,0.11); }")
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(26, 0, 26, 0); tbl.setSpacing(6)

        self._tab_btns = []
        for txt, idx in [("📋  Schedule Boards", 0), ("🔍  Search", 1), ("📓  Reflections", 2)]:
            b = TabBtn(txt); b.setChecked(idx == 0)
            b.clicked.connect(lambda checked=False, i=idx: self._switch(i))
            self._tab_btns.append(b); tbl.addWidget(b)

        tbl.addStretch()
        tbl.addWidget(lbl("Active Day:", 9, TEXT3))
        day_lbl = QLabel(date.today().strftime("%d/%m/%Y"))
        day_lbl.setFont(sf(9, QFont.Weight.Bold))
        day_lbl.setStyleSheet(f"color:{TEXT1}; background:rgba(255,255,255,0.10); border:1px solid rgba(255,255,255,0.20); border-radius:8px; padding:4px 12px;")
        tbl.addWidget(day_lbl); tbl.addSpacing(14)

        np_btn = glass_btn("＋  New Plan", ACCENT, filled=True, h=36)
        np_btn.setFont(sf(10, QFont.Weight.DemiBold))
        np_btn.clicked.connect(self._on_new)
        tbl.addWidget(np_btn)
        rl.addWidget(tb)

        # ── Stack ─────────────────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:transparent;")

        def wrap(w, pad=(26, 14, 26, 0)):
            sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.Shape.NoFrame)
            sc.setStyleSheet("QScrollArea{background:transparent;border:none;} QScrollBar:vertical{background:transparent;width:5px;} QScrollBar::handle:vertical{background:rgba(255,255,255,0.25);border-radius:2px;} QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
            inner = QWidget(); inner.setStyleSheet("background:transparent;")
            il = QVBoxLayout(inner); il.setContentsMargins(*pad); il.setSpacing(0)
            il.addWidget(w, 1); inner.setMinimumHeight(1)
            sc.setWidget(inner); return sc

        self._boards  = BoardsTab(self._data)
        self._search  = SearchPanel(self._data)
        self._search.jump_to.connect(lambda s: self._switch(0))
        self._reflect = ReflectionsTab(self._data)

        self._stack.addWidget(wrap(self._boards))
        self._stack.addWidget(wrap(self._search))
        self._stack.addWidget(wrap(self._reflect))
        rl.addWidget(self._stack, 1)

        # ── Footer ────────────────────────────────────────────────────────────
        ft = QFrame(); ft.setObjectName("ft"); ft.setFixedHeight(28)
        ft.setStyleSheet("QFrame { background:rgba(255,255,255,0.05); border-top:1px solid rgba(255,255,255,0.10); }")
        fl = QHBoxLayout(ft); fl.setContentsMargins(26, 0, 26, 0)
        fl.addWidget(lbl("OliSched  ·  macOS Tahoe Style", 8, TEXT3))
        fl.addStretch()
        fl.addWidget(lbl("Offline  ·  Secure  ·  Local Storage", 8, TEXT3))
        rl.addWidget(ft)

    def _switch(self, idx):
        self._stack.setCurrentIndex(idx)
        for i, b in enumerate(self._tab_btns):
            b.setChecked(i == idx)

    def _on_new(self):
        dlg = NewPlanDialog(self)
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
        # Runs on main thread — no threading issues, always reliable
        self._checker = ReminderChecker(self._data, self._show_remind)

    def closeEvent(self, event):
        if hasattr(self, "_checker"):
            self._checker.stop()
        event.accept()

    def _show_remind(self, title, msg):
        m = QMessageBox(self)
        m.setWindowTitle("🔔  OliSched Reminder")
        m.setText(f"<b style='color:{GREEN}; font-size:14pt;'>{title}</b>")
        m.setInformativeText(msg)
        m.setStandardButtons(QMessageBox.StandardButton.Ok)
        m.setStyleSheet(f"""
            QMessageBox {{
                background:{BG_MID};
            }}
            QLabel {{
                color:{TEXT1}; font-size:10pt;
            }}
            QPushButton {{
                background:{ACCENT}; color:white;
                border:none; border-radius:8px;
                padding:7px 28px; font-weight:600;
            }}
            QPushButton:hover {{ background:{ACCENT}cc; }}
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
    p.setColor(QPalette.ColorRole.Window,          QColor(BG_TOP))
    p.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT1))
    p.setColor(QPalette.ColorRole.Base,            QColor(BG_MID))
    p.setColor(QPalette.ColorRole.Text,            QColor(TEXT1))
    p.setColor(QPalette.ColorRole.Button,          QColor(BG_MID))
    p.setColor(QPalette.ColorRole.ButtonText,      QColor(TEXT1))
    p.setColor(QPalette.ColorRole.Highlight,       QColor(ACCENT))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(p)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()