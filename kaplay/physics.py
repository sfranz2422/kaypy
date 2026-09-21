"""Gravity/integration and AABB collision — resolution and event firing.

Physical pushback only happens between two objects that BOTH have
body(): a wall (isStatic=True) or a heavy box (mass=n) blocks you, but
a coin or an enemy with only area() is a pass-through trigger, exactly
as Lesson 3 sets it up. Collision *events* (onCollide/onCollideUpdate/
onCollideEnd) fire for any two objects that both carry area(), whether
or not either has a body.
"""
class PhysicsSystem:
    # A body is never allowed to travel more than this many pixels in one
    # collision step; anything faster gets split into substeps (up to
    # MAX_SUBSTEPS of them). Without this, a fast fall can clear a whole
    # tile between one frame and the next and land underneath the floor
    # having never overlapped it — and no amount of cleverness in
    # _resolve can catch a collision that never happened. Frame times
    # aren't ours to control (a browser tab that just lost focus, a slow
    # machine, a breakpoint), so the fix has to be in how far one step is
    # allowed to move things, not in hoping every frame is 16ms.
    MAX_STEP_PX = 16.0
    MAX_SUBSTEPS = 4

    def __init__(self):
        self.gravity = 0.0

    def substeps_for(self, objs, dt):
        """How many substeps this frame needs to keep every body's
        movement under MAX_STEP_PX."""
        worst = 0.0
        for obj in objs:
            if not (obj.has("body") and obj.has("pos")):
                continue
            body = obj.comp("body")
            if body.isStatic:
                continue
            vx = abs(body.vel.x)
            vy = abs(body.vel.y) + abs(self.gravity) * dt
            worst = max(worst, max(vx, vy) * dt)
        if worst <= self.MAX_STEP_PX:
            return 1
        return min(self.MAX_SUBSTEPS, int(worst // self.MAX_STEP_PX) + 1)

    def step(self, objs, dt):
        for obj in objs:
            if not (obj.has("body") and obj.has("pos")):
                continue
            body = obj.comp("body")
            body._pending_grounded = False
            # Remember where this body was before it moved. _resolve reads
            # it to work out which way the two came together — see
            # _entry_axis_is_vertical.
            body._prev_rect = obj.comp("area").get_rect() if obj.has("area") else None
            if body.isStatic:
                continue
            if self.gravity:
                body.vel.y += self.gravity * dt
            pos = obj.comp("pos")
            pos.pos = pos.pos + body.vel * dt


class CollisionSystem:
    def __init__(self):
        self._touching = {}  # obj id -> set of other obj ids currently overlapping

    def step(self, objs):
        area_objs = [o for o in objs if o.has("area") and o.exists()]
        n = len(area_objs)
        rects = {o._id: o.comp("area").get_rect() for o in area_objs}
        seen_pairs = set()

        for i in range(n):
            a = area_objs[i]
            ra = rects[a._id]
            a_touch = self._touching.setdefault(a._id, set())
            for j in range(i + 1, n):
                b = area_objs[j]
                rb = rects[b._id]
                b_touch = self._touching.setdefault(b._id, set())
                seen_pairs.add((a._id, b._id))

                if ra.colliderect(rb):
                    is_new = b._id not in a_touch
                    if is_new:
                        # The object-free onCollide(tagA, tagB, fn). Here
                        # rather than on the objects, because neither object
                        # in a bullets-and-enemies pair exists when the
                        # handler is written.
                        from .engine import _engine
                        if _engine is not None:
                            _engine.events.fire_tag_collision(a, b)
                    for t in b.tags:
                        a._fire("collide" if is_new else "collideUpdate", t, b)
                    for t in a.tags:
                        b._fire("collide" if is_new else "collideUpdate", t, a)
                    a_touch.add(b._id)
                    b_touch.add(a._id)

                    if a.has("body") and b.has("body"):
                        self._resolve(a, b, ra, rb)
                        # rects moved; refresh cached copies for later pairs
                        rects[a._id] = a.comp("area").get_rect()
                        rects[b._id] = b.comp("area").get_rect()
                        ra = rects[a._id]
                else:
                    if b._id in a_touch:
                        for t in b.tags:
                            a._fire("collideEnd", t, b)
                        for t in a.tags:
                            b._fire("collideEnd", t, a)
                        a_touch.discard(b._id)
                        b_touch.discard(a._id)

        # drop bookkeeping for destroyed objects
        live_ids = {o._id for o in area_objs}
        for oid in list(self._touching):
            if oid not in live_ids:
                del self._touching[oid]

        for obj in objs:
            if obj.has("body"):
                b = obj.comp("body")
                b._apply_grounded(b._pending_grounded)

    @staticmethod
    def _entry_axis_is_vertical(body_a, body_b, overlap_x, overlap_y) -> bool:
        """Which axis did these two actually come together on?

        "Push out along whichever axis overlaps least" is the usual
        shortcut, and it is wrong in exactly the case a platformer hits
        constantly: a floor built out of separate tiles. Land on the seam
        between two of them and the player overlaps each tile by only
        half its width, while a single fast frame can bury it deeper than
        that vertically. Both tiles then push sideways — in opposite
        directions, so they cancel — and nobody pushes up, so the player
        sinks through a floor that is plainly there. (Found exactly this
        way: in the browser, where frames are less even than they are
        natively, the bean fell through the level's floor while the same
        code at a steady 60fps on the desktop never penetrated deeply
        enough to trip it.)

        Where the two were BEFORE this step settles it without guessing:
        if they already lined up horizontally and have only now started
        overlapping vertically, this is a landing (or a head bump), no
        matter how deep it got in one frame. Only when the previous
        positions say nothing useful — a spawn, a teleport, two objects
        that were already inside each other — does it fall back to the
        smallest-overlap guess.
        """
        pa = getattr(body_a, "_prev_rect", None)
        pb = getattr(body_b, "_prev_rect", None)
        if pa is not None and pb is not None:
            was_x = pa.right > pb.left and pa.left < pb.right
            was_y = pa.bottom > pb.top and pa.top < pb.bottom
            if was_x and not was_y:
                return True
            if was_y and not was_x:
                return False
        return overlap_y <= overlap_x

    def _resolve(self, a, b, ra, rb):
        body_a, body_b = a.comp("body"), b.comp("body")
        if body_a.isStatic and body_b.isStatic:
            return

        overlap_x = min(ra.right, rb.right) - max(ra.left, rb.left)
        overlap_y = min(ra.bottom, rb.bottom) - max(ra.top, rb.top)
        if overlap_x <= 0 or overlap_y <= 0:
            return

        # Which one is on top / on the left has to be read off the two
        # boxes, NOT off their pos(): pos() means different things to
        # different objects. A plain tile's pos is its top-left corner,
        # but anchor("bot") — what a platformer character usually wants,
        # so it can be placed by its feet — makes pos the BOTTOM edge. A
        # bean standing on a tile then has the larger pos.y of the two,
        # and comparing those two numbers concludes the tile is above the
        # bean and pushes the bean DOWN, deeper in, every frame, until it
        # is through the floor and falling forever. The rects come from
        # geometry.get_world_rect(), which has already folded the anchor
        # in, so they are directly comparable.
        a_is_left = ra.centerx < rb.centerx
        a_is_above = ra.centery < rb.centery

        if body_a.isStatic:
            share_a, share_b = 0.0, 1.0
        elif body_b.isStatic:
            share_a, share_b = 1.0, 0.0
        else:
            total = body_a.mass + body_b.mass
            share_a = body_b.mass / total
            share_b = body_a.mass / total

        if not self._entry_axis_is_vertical(body_a, body_b, overlap_x, overlap_y):
            depth = overlap_x
            dx_a = -depth * share_a if a_is_left else depth * share_a
            dx_b = depth * share_b if a_is_left else -depth * share_b
            if a.has("pos"):
                a.comp("pos").pos.x += dx_a
            if b.has("pos"):
                b.comp("pos").pos.x += dx_b
        else:
            depth = overlap_y
            dy_a = -depth * share_a if a_is_above else depth * share_a
            dy_b = depth * share_b if a_is_above else -depth * share_b
            if a.has("pos"):
                a.comp("pos").pos.y += dy_a
            if b.has("pos"):
                b.comp("pos").pos.y += dy_b
            top, bot = (a, b) if a_is_above else (b, a)
            top_body, bot_body = top.comp("body"), bot.comp("body")
            if not top_body.isStatic:
                if top_body.vel.y > 0:
                    top_body.vel.y = 0
                top_body._pending_grounded = True
            if not bot_body.isStatic and bot_body.vel.y < 0:
                bot_body.vel.y = 0
