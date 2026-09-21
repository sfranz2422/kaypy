"""Kaplay callbacks can ignore arguments they don't want: onKeyDown hands
the key that was pressed, but `lambda: ...` takes nothing and works
anyway, exactly as `() => ...` does in JavaScript. If you *do* want the
argument, `lambda key: ...` gets it."""
import inspect

_sig_cache = {}


def register_or_decorate(fn, register):
    """Let one event function serve as both a callback and a decorator.

        onKeyPress("space", jump)     # hand it a function
        @onKeyPress("space")          # or put it above one
        def jump(): ...

    Kaplay's own form is the first one, and it stays the form every
    Kaplay example and doc page translates into directly. The second
    exists because a lambda can only hold one expression, and working
    around that teaches bad habits: `lambda: p.jump() if p.isGrounded()
    else None` has an `else None` that does nothing and exists purely to
    satisfy a conditional expression, and `lambda: setattr(p, "pos", v)`
    reaches for setattr only because a lambda can't assign. With a
    decorator, both are just ordinary indented code — and the handler
    gets a name, so it shows up in tracebacks as `jump` rather than
    `<lambda>`.

    `register` does the actual work and returns the function; this only
    decides whether to call it now or hand back something that will.
    """
    if fn is not None:
        return register(fn)

    def decorator(f):
        register(f)
        return f          # leave the name bound to the function itself

    return decorator


def call_flexible(fn, *args):
    n = _sig_cache.get(fn)
    if n is None:
        try:
            params = inspect.signature(fn).parameters.values()
            has_varargs = any(p.kind == p.VAR_POSITIONAL for p in params)
            n = len(args) if has_varargs else sum(
                1 for p in params
                if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
            )
        except (TypeError, ValueError):
            n = len(args)
        _sig_cache[fn] = n
    return fn(*args[:n])
