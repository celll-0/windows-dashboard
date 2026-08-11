"""Keeps the frameless window pinned to the bottom of the Z-order on Windows.

``Qt.WindowStaysOnBottomHint`` covers the common case, but some shells restack
windows on focus changes. Re-issuing ``SetWindowPos(HWND_BOTTOM, …)`` on a short
timer keeps the widget sitting on the desktop beneath everything else.
"""
from __future__ import annotations
import sys

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtGui import QWindow

_HWND_BOTTOM = 1
# SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
_SWP_FLAGS = 0x0001 | 0x0002 | 0x0010
_REPIN_INTERVAL_MS = 500


class WidgetBehaviour(QObject):
    def __init__(self, window: QWindow, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._window = window

        if sys.platform == "win32":
            self._pin = self._pin_win
        elif sys.platform == "darwin":
            # Get NSWindow from Qt window ID
            import objc

            ns_view = objc.objc_object(c_void_p=int(self._window.winId()))
            self._pin = self._pin_mac
            self._ns_window = ns_view.window()
            self._configure_mac_window_behavior()

        self._timer = QTimer(self)
        self._timer.setInterval(_REPIN_INTERVAL_MS)
        self._timer.timeout.connect(self._pin)
        self._timer.start()
        self._pin()

    def _pin_win(self) -> None:
        """Pin the window to the bottom of the Z-order on Windows."""
        import ctypes

        hwnd = int(self._window.winId())
        ctypes.windll.user32.SetWindowPos(
            hwnd, _HWND_BOTTOM, 0, 0, 0, 0, _SWP_FLAGS
        )

    def _pin_mac(self):
        # Set window level to just above desktop (effectively always behind)
        from Quartz import CGWindowLevelForKey, kCGNormalWindowLevelKey

        norm_window_level = CGWindowLevelForKey(
            kCGNormalWindowLevelKey
        )
        self._ns_window.setLevel_(norm_window_level - 1)

    def _configure_mac_window_behavior(self):
        # Set window behavior to stay on desktop and not hide on app deactivation
        from AppKit import NSApp
        from AppKit import (
            NSWindowCollectionBehaviorCanJoinAllSpaces,
            NSWindowCollectionBehaviorStationary,
            NSWindowCollectionBehaviorIgnoresCycle
        )
        NSApp().setActivationPolicy_(1)

        self._ns_window.setHidesOnDeactivate_(False)
        self._ns_window.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorIgnoresCycle
        )
