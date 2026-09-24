# kaypy — known bugs, waiting for a day to fix them

Three bugs found while building quiz games in September 2026. None of them
raise anything useful; all three were found by a person being confused rather
than by a test. Each one is small on its own, and together they are the
difference between "the panel API works" and "a fourteen-year-old can debug
their own quiz".

Fixing any of these means re-vendoring afterwards:

    cd ~/pyide       && python3 tools/vendor_kaypy.py --from ~/kaypy
    cd ~/kaypy-site  && python3 vendor.py --from ~/pyide && python3 build.py

---

## 1. ~~`say()` draws a text box that does nothing~~ — FIXED in 0.13.7

A `Panel` now carries `asks`, set true by `ask()` and false by `say()`. Both
renderers read it instead of guessing from `choices`, and `finish()` reads it
instead of inferring from three negatives. See `tests/test_say_panel.py`,
which also gives the browser renderer its first tests, via a small fake DOM.

## 2. `_call()` guesses a handler's arity by catching TypeError

**Where** `kaypy/panel.py`, `_call()`.

```python
try:
    return fn(value)
except TypeError:
    return fn()
```

The intent is "a handler that ignores the answer is fine". The effect is that
a `TypeError` raised *inside* the handler is misread as "this handler takes no
arguments", and the handler is then called a second time, wrongly, and fails
for a completely different reason. What the person sees:

```python
@ask("What is your name?")
def name_check(reply):
    print("Hello, " + reply)
    flash("Hello, " + reply)        # flash() takes two arguments
```

```
Hello, Steve
TypeError: name_check() missing 1 required positional argument: 'reply'
```

The message names the handler's signature, which is fine, and says nothing
about `flash`, which is not. The handler also ran half way, so its `print` had
already happened.

**The fix** Read the signature with `inspect.signature` and call it with the
right number of arguments, so a `TypeError` from the body is left alone to
propagate as itself.

---

## 3. An error inside a panel callback disappears

**Where** `kaypy/panel.py` (`Panel.finish`), and PyIDE's
`static/runtime.js`.

PyIDE catches errors in two places: `_pyide_run()` for console programs, and
`_pyide_run_game()` around `await engine.run_async()` — which is why an error
inside an `onUpdate` callback does reach the output pane.

A panel handler is in neither. It is fired by a DOM click listener, so it runs
outside `run_async()` entirely; the exception unwinds into the browser's event
dispatch and Pyodide logs it to the devtools console. There is no
`window.onerror` in `app.js` or `runtime.js` to catch it.

So a student who typos inside an `@ask` handler gets a panel that closes and a
game that sits there. No traceback, no message, nothing in the pane they have
been taught to read. Found the hard way:

```python
@ask(q[1])
def short_answer(reply):
    flash(reply, GREEN)     # flash was not defined in that file
    advance()               # never runs
```

Symptom: answer the question, and nothing happens. Ever.

**The fix** Wrap the callback in `finish()` so anything it raises goes through
`_write_traceback` into the output pane, the same as a frame-loop error. Worth
checking whether that belongs in kaypy, in PyIDE's bootstrap, or both — kaypy
should not know about PyIDE, so probably a hook kaypy calls and PyIDE fills in.

---

## Tests to write with the fixes

`tests/test_panel_queue.py` already covers ordering and the queue. It does not
cover any of the above, because all three are about what happens when
something goes *wrong*:

- a `say()` panel has no input field, and an `ask()` without choices does
- a handler whose body raises `TypeError` reports that `TypeError`, not an
  arity error, and is not called twice
- a handler that raises anything at all has it reported somewhere a student
  will see it

Falsify each against a deliberately broken copy, in both directions.
