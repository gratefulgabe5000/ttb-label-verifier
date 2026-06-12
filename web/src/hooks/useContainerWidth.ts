import { useEffect, useState, type RefObject } from "react";

/** Tracks the rendered width of `ref`'s element, falling back to `fallback`
 * until the element is measurable (e.g. in jsdom, or before first paint). */
export function useContainerWidth(ref: RefObject<HTMLElement | null>, fallback: number): number {
  const [width, setWidth] = useState(fallback);

  useEffect(() => {
    function measure() {
      const measured = ref.current?.getBoundingClientRect().width;
      if (measured) setWidth(measured);
    }

    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [ref]);

  return width;
}
