import { useEffect, useRef, useState } from "react";

const MIN_ZOOM = 0.5;
const MAX_ZOOM = 3;

/** Lets the user zoom an element in/out with the mousewheel. Attaches a
 * non-passive wheel listener so the page doesn't scroll while zooming. */
export function useWheelZoom(initialZoom = 1) {
  const [zoom, setZoom] = useState(initialZoom);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    function handleWheel(event: WheelEvent) {
      event.preventDefault();
      setZoom((current) => {
        const next = current * (1 - event.deltaY * 0.001);
        return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, next));
      });
    }

    el.addEventListener("wheel", handleWheel, { passive: false });
    return () => el.removeEventListener("wheel", handleWheel);
  }, []);

  return { zoom, containerRef };
}
