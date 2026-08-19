# Carousel

```python
from ux_behavior import Component, MorphState, RefState, action

class HeroCarousel(Component):
    id = "hero.carousel"
    index = MorphState(0)
    slides = MorphState(("A", "B", "C"))  # or load from Host
    playing = RefState(False)            # silent; Host timer

    def render(self):
        slides = list(self.slides or ())
        n = len(slides) or 1
        i = int(self.index) % n
        body = slides[i] if slides else ""
        dots = "".join(
            f"<button data-i='{k}' class='{"on" if k == i else ""}'></button>"
            for k in range(n)
        )
        return f"""
        <div id="hero.carousel" data-index="{i}">
          <div class="slide">{body}</div>
          <button data-act="prev">Prev</button>
          <button data-act="next">Next</button>
          <div class="dots">{dots}</div>
        </div>"""

    def _len(self):
        return max(1, len(self.slides or ()))

    @action(caps=())
    def next(self):
        self.index = (int(self.index) + 1) % self._len()
        return None

    @action(caps=())
    def prev(self):
        self.index = (int(self.index) - 1) % self._len()
        return None

    @action(caps=())
    def go(self, i: int = 0):
        self.index = int(i) % self._len()
        return None

    @action(caps=())
    def play(self):
        self.playing = True
        return None

    @action(caps=())
    def pause(self):
        self.playing = False
        return None
```

**Autoplay:** Host `setInterval` → `hero.carousel.next` while you treat `playing` as advisory, or store `playing` as Morph if the play button must re-render.
