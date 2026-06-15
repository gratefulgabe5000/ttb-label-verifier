import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { TUTORIAL_STEPS, TUTORIAL_STORAGE_KEY } from "@/lib/tutorial-steps";
import { TutorialContext, type TutorialContextValue } from "./tutorial-context";

function loadCompletedSteps(): Set<string> {
  try {
    const raw = localStorage.getItem(TUTORIAL_STORAGE_KEY);
    return raw ? new Set(JSON.parse(raw) as string[]) : new Set();
  } catch {
    return new Set();
  }
}

function saveCompletedSteps(steps: Set<string>) {
  localStorage.setItem(TUTORIAL_STORAGE_KEY, JSON.stringify(Array.from(steps)));
}

export function TutorialProvider({ children }: { children: ReactNode }) {
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(loadCompletedSteps);
  const [anchors, setAnchors] = useState<Record<string, HTMLElement | null>>({});

  const registerAnchor = useCallback((stepId: string, el: HTMLElement | null) => {
    setAnchors((prev) => (prev[stepId] === el ? prev : { ...prev, [stepId]: el }));
  }, []);

  const dismiss = useCallback((stepId: string) => {
    setCompletedSteps((prev) => {
      if (prev.has(stepId)) return prev;
      const next = new Set(prev);
      next.add(stepId);
      saveCompletedSteps(next);
      return next;
    });
  }, []);

  const reset = useCallback(() => {
    setCompletedSteps(new Set());
    localStorage.removeItem(TUTORIAL_STORAGE_KEY);
  }, []);

  // The active step is the first not-yet-completed step (in canonical order)
  // whose anchor is currently registered. If an earlier step's anchor has
  // disappeared while a later step's anchor is ready, the user moved past it
  // without dismissing it -- fold it into `effectiveCompleted` (persisted
  // below) so it doesn't reappear later.
  const { activeStepId, effectiveCompleted } = useMemo(() => {
    const completed = new Set(completedSteps);
    let active: string | null = null;

    for (let i = 0; i < TUTORIAL_STEPS.length; i++) {
      const step = TUTORIAL_STEPS[i];
      if (completed.has(step.id)) continue;
      if (anchors[step.id]) {
        active = step.id;
        break;
      }
      const laterAvailable = TUTORIAL_STEPS.slice(i + 1).some(
        (later) => !completed.has(later.id) && anchors[later.id]
      );
      if (laterAvailable) {
        completed.add(step.id);
      } else {
        break;
      }
    }

    return { activeStepId: active, effectiveCompleted: completed };
  }, [anchors, completedSteps]);

  useEffect(() => {
    if (effectiveCompleted.size > completedSteps.size) {
      saveCompletedSteps(effectiveCompleted);
    }
  }, [effectiveCompleted, completedSteps]);

  const activeAnchorEl = activeStepId ? anchors[activeStepId] ?? null : null;

  const value = useMemo<TutorialContextValue>(
    () => ({ activeStepId, activeAnchorEl, registerAnchor, dismiss, reset }),
    [activeStepId, activeAnchorEl, registerAnchor, dismiss, reset]
  );

  return <TutorialContext.Provider value={value}>{children}</TutorialContext.Provider>;
}
