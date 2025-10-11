import os
from typing import List, Optional

DEFAULT_IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff'}


def list_image_files(
    dir_path: str,
    exts: Optional[List[str]] = None,
    recursive: bool = False,
    limit: Optional[int] = None,
) -> List[str]:
    """Return a list of image file paths found in `dir_path`.

    - exts: optional list of extensions to include (case-insensitive, e.g. ['.png']).
    - recursive: whether to walk subdirectories.
    - limit: maximum number of results to return (None for no limit).

    This function does not depend on any GUI toolkit; it only returns file paths
    so the caller (usually the GUI) can load and render thumbnails as desired.
    """
    if not dir_path:
        return []

    if exts is None:
        exts_set = DEFAULT_IMAGE_EXTS
    else:
        exts_set = {e.lower() if e.startswith('.') else f'.{e.lower()}' for e in exts}

    results: List[str] = []
    try:
        if recursive:
            for root, _dirs, files in os.walk(dir_path):
                for name in sorted(files):
                    _, ext = os.path.splitext(name)
                    if ext.lower() in exts_set:
                        results.append(os.path.join(root, name))
                        if limit and len(results) >= limit:
                            return results
        else:
            for name in sorted(os.listdir(dir_path)):
                full = os.path.join(dir_path, name)
                if not os.path.isfile(full):
                    continue
                _, ext = os.path.splitext(name)
                if ext.lower() in exts_set:
                    results.append(full)
                    if limit and len(results) >= limit:
                        break
    except Exception:
        # On any filesystem error, return what we have so caller can handle empty list gracefully
        return results

    return results


def load_thumbnails(
    dir_path: str,
    size: tuple = (128, 128),
    exts: Optional[List[str]] = None,
    recursive: bool = False,
    limit: Optional[int] = 12,
) -> List[tuple]:
    """Return a list of (file_path, QPixmap) tuples for images in `dir_path`.

    - size: (width, height) target thumbnail size.
    - limit: maximum number of thumbnails to return.

    This function imports PyQt5 locally so callers that don't have PyQt
    won't fail at import time (it will return an empty list instead).
    """
    files = list_image_files(dir_path, exts=exts, recursive=recursive, limit=limit)
    thumbnails: List[tuple] = []
    if not files:
        return thumbnails

    try:
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtCore import Qt
    except Exception:
        # PyQt not available; caller should handle empty result
        return thumbnails

    w, h = size
    for path in files:
        try:
            pix = QPixmap(path)
            if pix.isNull():
                continue
            thumb = pix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            thumbnails.append((path, thumb))
        except Exception:
            # skip files that can't be loaded as images
            continue

    return thumbnails


def clear_layout(layout) -> None:
    """Remove and delete all widgets from a QLayout."""
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            # schedule for deletion
            w.setParent(None)
            try:
                w.deleteLater()
            except Exception:
                pass


def populate_thumbnails(layout, dir_path: str, thumb_size=(96, 96), limit=24) -> int:
    """Populate a QLayout with thumbnail QLabel widgets for images in dir_path.

    Returns the number of thumbnails added.
    """
    try:
        from PyQt5.QtWidgets import QLabel
    except Exception:
        return 0

    clear_layout(layout)
    thumbs = load_thumbnails(dir_path, size=thumb_size, limit=limit)
    added = 0
    for path, pixmap in thumbs:
        try:
            lbl = QLabel()
            lbl.setPixmap(pixmap)
            lbl.setFixedSize(pixmap.width(), pixmap.height())
            lbl.setToolTip(path)
            layout.addWidget(lbl)
            added += 1
        except Exception:
            continue

    # Keep a stretch at the end so items align left
    try:
        from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
        layout.addStretch()
    except Exception:
        pass

    return added


def start_qtimer(interval_ms: int, callback, single_shot: bool = False, parent=None):
    """Start a non-blocking QTimer that calls `callback` on the main (GUI) thread.

    Returns the QTimer instance so the caller can keep a reference and stop it later.

    - interval_ms: milliseconds between callbacks
    - callback: callable with no arguments (or use functools.partial)
    - single_shot: if True, the timer will fire once
    - parent: optional QObject parent for the timer

    Notes:
    - This uses PyQt5.QtCore.QTimer under the hood and will raise RuntimeError if PyQt5
      isn't available in the environment.
    - The callback runs on the Qt event loop (main thread), so it won't block the UI
      unless the callback itself is long-running. For long tasks, use a worker thread
      or offload work to concurrent.futures.
    """
    try:
        from PyQt5.QtCore import QTimer
    except Exception as e:
        raise RuntimeError('PyQt5 is required for start_qtimer') from e

    timer = QTimer(parent)
    timer.setInterval(int(interval_ms))
    timer.setSingleShot(bool(single_shot))
    timer.timeout.connect(callback)
    timer.start()
    print("DEBUG: Started!")
    return timer


def stop_qtimer(timer):
    """Stop and delete a QTimer started with start_qtimer.

    Safe to call with None or non-QTimer values (it will no-op).
    """
    if timer is None:
        return
    try:
        timer.stop()
        print("DEBUG: Stopped!")
        try:
            timer.deleteLater()
        except Exception:
            pass
    except Exception:
        # ignore any errors
        pass


# --- FlowLayout implementation (wraps items into rows) -----------------
try:
    from PyQt5.QtCore import QPoint, QRect, QSize
    from PyQt5.QtWidgets import QLayout, QWidgetItem


    class FlowLayout(QLayout):
        """A flow layout that arranges child widgets left-to-right and wraps rows.

        Adapted for PyQt from the Qt example.
        """

        def __init__(self, parent=None, margin=0, spacing=-1):
            super().__init__(parent)
            if parent is not None:
                self.setContentsMargins(margin, margin, margin, margin)
            self._item_list = []
            self.setSpacing(spacing if spacing >= 0 else 6)

        def addItem(self, item):
            self._item_list.append(item)

        def count(self):
            return len(self._item_list)

        def itemAt(self, index):
            if 0 <= index < len(self._item_list):
                return self._item_list[index]
            return None

        def takeAt(self, index):
            if 0 <= index < len(self._item_list):
                return self._item_list.pop(index)
            return None

        def expandingDirections(self):
            return 0

        def hasHeightForWidth(self):
            return True

        def heightForWidth(self, width):
            return self.doLayout(QRect(0, 0, width, 0), True)

        def setGeometry(self, rect):
            super().setGeometry(rect)
            self.doLayout(rect, False)

        def sizeHint(self):
            return self.minimumSize()

        def minimumSize(self):
            size = QSize()
            for item in self._item_list:
                size = size.expandedTo(item.minimumSize())
            margins = self.contentsMargins()
            size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
            return size

        def doLayout(self, rect: QRect, testOnly: bool):
            x = rect.x()
            y = rect.y()
            lineHeight = 0

            for item in self._item_list:
                widget = item.widget()
                spaceX = self.spacing()
                spaceY = self.spacing()
                nextX = x + item.sizeHint().width() + spaceX
                if nextX - spaceX > rect.right() and lineHeight > 0:
                    x = rect.x()
                    y = y + lineHeight + spaceY
                    nextX = x + item.sizeHint().width() + spaceX
                    lineHeight = 0

                if not testOnly:
                    item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

                x = nextX
                lineHeight = max(lineHeight, item.sizeHint().height())

            return y + lineHeight - rect.y()

except Exception:
    # If PyQt isn't available at import time, skip FlowLayout definition.
    FlowLayout = None

