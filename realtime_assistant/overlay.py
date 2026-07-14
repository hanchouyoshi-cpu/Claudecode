"""常時最前面のカンペ表示ウィンドウ (tkinter)。"""
import queue
import tkinter as tk
from tkinter import scrolledtext


class Overlay:
    """他スレッドからは post_* メソッドで更新を依頼する(tkinter はメインスレッド専用)。"""

    def __init__(self, title: str = "回答アシスタント"):
        self._events: "queue.Queue[tuple[str, str]]" = queue.Queue()

        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("420x560+40+40")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)

        tk.Label(self.root, text="会話ログ", anchor="w").pack(fill="x", padx=8)
        self.transcript = scrolledtext.ScrolledText(
            self.root, height=10, wrap="word", state="disabled")
        self.transcript.pack(fill="both", expand=False, padx=8, pady=(0, 8))

        tk.Label(self.root, text="回答候補", anchor="w").pack(fill="x", padx=8)
        self.suggestion = scrolledtext.ScrolledText(
            self.root, height=14, wrap="word", state="disabled",
            font=("Yu Gothic UI", 12))
        self.suggestion.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.root.after(50, self._drain)

    # ---- 他スレッドから呼べるAPI ----
    def post_transcript(self, speaker: str, text: str) -> None:
        label = "相手" if speaker == "other" else "自分"
        self._events.put(("transcript", f"{label}: {text}\n"))

    def post_suggestion_reset(self) -> None:
        self._events.put(("reset", ""))

    def post_suggestion_delta(self, text: str) -> None:
        self._events.put(("delta", text))

    # ---- メインスレッド側 ----
    def _drain(self) -> None:
        try:
            while True:
                kind, text = self._events.get_nowait()
                if kind == "transcript":
                    self._append(self.transcript, text)
                elif kind == "reset":
                    self._clear(self.suggestion)
                elif kind == "delta":
                    self._append(self.suggestion, text)
        except queue.Empty:
            pass
        self.root.after(50, self._drain)

    @staticmethod
    def _append(widget: scrolledtext.ScrolledText, text: str) -> None:
        widget.configure(state="normal")
        widget.insert("end", text)
        widget.see("end")
        widget.configure(state="disabled")

    @staticmethod
    def _clear(widget: scrolledtext.ScrolledText) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.configure(state="disabled")

    def run(self) -> None:
        self.root.mainloop()
