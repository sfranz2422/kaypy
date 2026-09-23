"""The panel, as real HTML over the canvas.

Only imported in a browser — panel.py picks between this and its own pygame
drawing by looking at sys.platform. On a desktop this module is never loaded
at all, so `import js` at the top would be a crash there; it is imported
inside the class for that reason.

WHY BOTHER, WHEN THE PYGAME ONE ALREADY WORKS

Because everything a browser gives a panel for free is exactly what a panel
needs and a canvas cannot do:

    text you can select, and a screen reader can read
    a real <a>, which middle-clicks and opens in a new tab
    a real <input>, with the phone keyboard, autocorrect off, and paste
    text that reflows and stays sharp when the page is zoomed

Drawn on a canvas, every one of those is gone. For a message in a game that
would be a fair trade; for a question a student has to answer, and a link a
visitor is meant to follow, it is not.

WHERE IT ATTACHES

Over the canvas, positioned with fixed coordinates taken from the canvas's
own bounding box, and appended to <body> rather than next to the canvas.

That is deliberate. kaypy runs in three different pages — its own export,
PyIDE, and the site's playground — and they agree on exactly one thing: a
<canvas id="canvas">, because SDL insists on that id. They do not agree on
what is around it, and PyIDE *replaces* the canvas element on every run. An
overlay parented to the canvas, or to whatever happens to contain it, would
be at the mercy of all that. A fixed box on <body>, measured from the canvas
each time it is shown, is not.
"""
from __future__ import annotations

CSS = """
.kaypy-panel-veil {
  position: fixed; z-index: 2147483000;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0, 0, 0, .55);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
.kaypy-panel {
  background: #fafafc; color: #141821;
  border-radius: 12px; padding: 20px 22px;
  width: min(70%, 520px); max-height: 80%; overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, .45);
}
.kaypy-panel p { margin: 0 0 14px; white-space: pre-wrap; }
.kaypy-panel button.kaypy-choice {
  display: block; width: 100%; text-align: left;
  font: inherit; margin: 0 0 8px; padding: 9px 12px;
  border: 2px solid #c8ced6; border-radius: 7px;
  background: #f0f2f6; color: inherit; cursor: pointer;
}
.kaypy-panel button.kaypy-choice:hover,
.kaypy-panel button.kaypy-choice:focus-visible {
  border-color: #50963c; background: #e1eedd; outline: none;
}
.kaypy-panel input.kaypy-text {
  width: 100%; font: inherit; padding: 9px 12px; margin-bottom: 10px;
  border: 2px solid #7890aa; border-radius: 7px; background: #fff; color: inherit;
}
.kaypy-panel .kaypy-go {
  font: inherit; font-weight: 600; padding: 9px 18px;
  border: 0; border-radius: 7px; cursor: pointer;
  background: #50963c; color: #fff;
}
.kaypy-panel a { color: #2b5fc8; }
.kaypy-panel .kaypy-hint { margin: 12px 0 0; font-size: 13px; color: #6b7280; }
"""


class DomView:
    """A panel built out of real elements."""

    def __init__(self, panel):
        import js                                              # noqa: PLC0415

        self.js = js
        self.panel = panel
        self.veil = None
        self._build()

    # ---- building --------------------------------------------------------

    def _build(self):
        js = self.js
        doc = js.document
        p = self.panel

        self._install_css()

        veil = doc.createElement("div")
        veil.className = "kaypy-panel-veil"
        self._place(veil)

        box = doc.createElement("div")
        box.className = "kaypy-panel"
        box.setAttribute("role", "dialog")
        box.setAttribute("aria-modal", "true")
        # A <div> cannot take focus without this, so focus() below would do
        # nothing, the event target would stay <body>, and the number-key
        # shortcut would quietly stop working.
        box.setAttribute("tabindex", "-1")

        para = doc.createElement("p")
        # textContent, never innerHTML. The text comes from a game, and a
        # game's text comes from wherever the person who wrote it got it.
        # Nothing in a panel is worth an injection bug.
        para.textContent = p.text
        box.appendChild(para)

        if p.choices:
            for i, choice in enumerate(p.choices):
                b = doc.createElement("button")
                b.className = "kaypy-choice"
                b.type = "button"
                b.textContent = "%d.  %s" % (i + 1, choice)
                b.addEventListener("click", _handler(
                    lambda _e, i=i: self._answered(i, p.choices[i])))
                box.appendChild(b)
        else:
            field = doc.createElement("input")
            field.className = "kaypy-text"
            field.type = "text"
            field.placeholder = p.placeholder or ""
            field.setAttribute("autocomplete", "off")
            field.setAttribute("autocapitalize", "off")
            box.appendChild(field)
            self.field = field

            go = doc.createElement("button")
            go.className = "kaypy-go"
            go.type = "button"
            go.textContent = p.button or "OK"
            go.addEventListener("click", _handler(
                lambda _e: self._answered(None, self.field.value)))
            box.appendChild(go)

        if p.link:
            label, url = p.link
            wrap = doc.createElement("p")
            a = doc.createElement("a")
            a.textContent = label
            a.href = url
            # A link out of a game goes to a new tab. Replacing the page
            # would take the game with it, and the player's progress.
            a.target = "_blank"
            a.rel = "noopener noreferrer"
            wrap.appendChild(a)
            box.appendChild(wrap)

        hint = doc.createElement("p")
        hint.className = "kaypy-hint"
        hint.textContent = ("Click an answer, or press its number."
                            if p.choices else
                            "Type your answer, then press Enter.")
        box.appendChild(hint)

        veil.appendChild(box)
        doc.body.appendChild(veil)
        self.veil = veil

        # The canvas has the keyboard while a game is running, so without
        # this the first thing typed goes to the game, not the panel.
        try:
            (self.field if not p.choices else box).focus()
        except Exception:                                      # noqa: BLE001
            pass

        self._on_resize = _handler(lambda _e: self._place(self.veil))
        js.window.addEventListener("resize", self._on_resize)
        js.window.addEventListener("scroll", self._on_resize)

        # Keys, intercepted at the window, in the CAPTURE phase.
        #
        # This is the whole reason typing into the box works at all. SDL, in
        # a browser, puts its own key listeners on `document` and calls
        # preventDefault() on them, so that arrow keys and space drive the
        # game instead of scrolling the page. It never takes them off. A
        # cancelled keydown still *fires* — which is why clicking a choice or
        # pressing "2" worked — but the browser's default action for it does
        # not happen, and typing a character into an <input> IS that default
        # action. So the box stayed empty while everything else worked.
        #
        # Capture runs outermost-first: window, then document. Listening here
        # gets the event before SDL does, and stopPropagation() means SDL's
        # document listener never runs and never cancels anything. The
        # default action then happens normally and the character appears.
        #
        # Note it does NOT call preventDefault() itself — that would be the
        # same bug with a different author.
        self._on_key = _handler(self._key_capture)
        for kind in ("keydown", "keyup", "keypress"):
            js.window.addEventListener(kind, self._on_key, True)

    def _install_css(self):
        doc = self.js.document
        if doc.getElementById("kaypy-panel-css"):
            return
        style = doc.createElement("style")
        style.id = "kaypy-panel-css"
        style.textContent = CSS
        doc.head.appendChild(style)

    def _place(self, veil):
        """Sit exactly over the canvas, wherever it currently is."""
        canvas = self.js.document.getElementById("canvas")
        if canvas is None:
            # No canvas to cover: fill the window rather than vanish.
            veil.style.inset = "0"
            return
        r = canvas.getBoundingClientRect()
        veil.style.left = "%fpx" % r.left
        veil.style.top = "%fpx" % r.top
        veil.style.width = "%fpx" % r.width
        veil.style.height = "%fpx" % r.height

    # ---- input -----------------------------------------------------------

    def _key_capture(self, event):
        """Every key, before SDL can cancel it.

        Only keys aimed at the panel are taken. A key pressed with the game
        focused is left alone: the game is paused and its handlers are not
        running anyway, and swallowing those would break a page that has
        anything else on it — PyIDE has an editor two inches away.
        """
        if self.veil is None:
            return

        target = getattr(event, "target", None)
        try:
            inside = bool(self.veil.contains(target))
        except Exception:                                      # noqa: BLE001
            inside = False

        # The canvas and <body> count too. A panel is modal, and the player
        # may well have clicked the game before the question appeared — SDL
        # keeps the canvas focused — so keys arriving from there belong to
        # the panel. What is deliberately NOT taken is a key aimed at some
        # other field on the page: PyIDE has a code editor two inches away,
        # and swallowing its keystrokes would be far worse than this bug.
        elsewhere = False
        try:
            name = (getattr(target, "tagName", "") or "").upper()
            elsewhere = name in ("BODY", "CANVAS", "HTML", "")
        except Exception:                                      # noqa: BLE001
            elsewhere = False

        if not (inside or elsewhere):
            return

        # SDL must not see this one.
        event.stopPropagation()

        if getattr(event, "type", "") != "keydown":
            return

        p = self.panel
        key = getattr(event, "key", "")
        if p.choices:
            if len(key) == 1 and key.isdigit():
                i = int(key) - 1
                if 0 <= i < len(p.choices):
                    self._answered(i, p.choices[i])
        elif key == "Enter":
            self._answered(None, self.field.value)

    def _answered(self, index, text):
        self.panel.finish(index, text)

    # ---- taking it away --------------------------------------------------

    def destroy(self):
        js = self.js
        try:
            js.window.removeEventListener("resize", self._on_resize)
            js.window.removeEventListener("scroll", self._on_resize)
            for kind in ("keydown", "keyup", "keypress"):
                js.window.removeEventListener(kind, self._on_key, True)
        except Exception:                                      # noqa: BLE001
            pass
        if self.veil is not None:
            try:
                self.veil.remove()
            except Exception:                                  # noqa: BLE001
                pass
            self.veil = None
        # Whatever had the keyboard before, the canvas should have it again,
        # or the game is running and not listening.
        try:
            canvas = js.document.getElementById("canvas")
            if canvas is not None:
                canvas.focus()
        except Exception:                                      # noqa: BLE001
            pass

    def handle(self, events):
        """Nothing to do: the browser delivers the input to the elements.

        This exists so panel.handle_events() can say "the panel took it"
        without caring which view it has — which is what stops the pygame
        events reaching the game behind a DOM panel.
        """
        return


def _handler(fn):
    """A Python function a browser can call.

    create_proxy, where Pyodide offers it: a bare Python callable handed to
    addEventListener is garbage-collected while the browser still holds a
    reference to it, and the listener then fails on a later click rather
    than at the point of the mistake.
    """
    try:
        from pyodide.ffi import create_proxy                    # noqa: PLC0415
        return create_proxy(fn)
    except Exception:                                           # noqa: BLE001
        return fn
