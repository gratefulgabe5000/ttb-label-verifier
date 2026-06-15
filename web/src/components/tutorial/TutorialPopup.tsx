import { useEffect, useReducer, type CSSProperties } from "react";
import { X } from "lucide-react";
import { TUTORIAL_STEPS, type TutorialPlacement } from "@/lib/tutorial-steps";
import { useTutorial } from "@/hooks/useTutorial";

const POPUP_WIDTH = 280;
const GAP = 8;

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function getPopupStyle(rect: DOMRect, placement: TutorialPlacement): CSSProperties {
  // Clamp the anchor's edges to the viewport first, so a popup whose anchor is
  // scrolled off-screen (e.g. the Parameter Results card below the fold)
  // still renders at the nearest visible edge instead of off-screen itself.
  const anchorTop = clamp(rect.top, 0, window.innerHeight);
  const anchorBottom = clamp(rect.bottom, 0, window.innerHeight);
  const anchorLeft = clamp(rect.left, 0, window.innerWidth);
  const anchorRight = clamp(rect.right, 0, window.innerWidth);

  const left = clamp(anchorLeft, GAP, window.innerWidth - POPUP_WIDTH - GAP);
  const top = clamp(anchorTop, GAP, window.innerHeight - GAP);

  switch (placement) {
    case "top":
      return { left, bottom: clamp(window.innerHeight - anchorTop + GAP, GAP, window.innerHeight - GAP), width: POPUP_WIDTH };
    case "left":
      return { right: clamp(window.innerWidth - anchorLeft + GAP, GAP, window.innerWidth - POPUP_WIDTH - GAP), top, width: POPUP_WIDTH };
    case "right":
      return { left: clamp(anchorRight + GAP, GAP, window.innerWidth - POPUP_WIDTH - GAP), top, width: POPUP_WIDTH };
    case "bottom":
    default:
      return { left, top: clamp(anchorBottom + GAP, GAP, window.innerHeight - GAP), width: POPUP_WIDTH };
  }
}

export function TutorialPopup() {
  const { activeStepId, activeAnchorEl, dismiss } = useTutorial();
  const [, forceRecalculate] = useReducer((tick: number) => tick + 1, 0);

  // Reposition on resize/scroll -- these listeners only ever call
  // forceRecalculate() from their own callbacks, never synchronously in the
  // effect body, so the position (read fresh from the DOM below) stays current.
  useEffect(() => {
    if (!activeAnchorEl) return;
    window.addEventListener("resize", forceRecalculate);
    window.addEventListener("scroll", forceRecalculate, true);
    return () => {
      window.removeEventListener("resize", forceRecalculate);
      window.removeEventListener("scroll", forceRecalculate, true);
    };
  }, [activeAnchorEl]);

  if (!activeStepId || !activeAnchorEl) {
    return null;
  }

  const step = TUTORIAL_STEPS.find((candidate) => candidate.id === activeStepId);
  if (!step) {
    return null;
  }

  const rect = activeAnchorEl.getBoundingClientRect();

  return (
    <div
      role="dialog"
      style={{ position: "fixed", zIndex: 100, ...getPopupStyle(rect, step.placement) }}
      className="rounded-lg border border-yellow-300 bg-yellow-100 p-3 pr-8 text-sm text-yellow-950 shadow-lg"
    >
      <button
        type="button"
        aria-label="Dismiss"
        onClick={() => dismiss(step.id)}
        className="absolute right-2 top-2 text-yellow-700 hover:text-yellow-950"
      >
        <X className="size-4" />
      </button>
      <p className="whitespace-pre-line">{step.message}</p>
    </div>
  );
}
