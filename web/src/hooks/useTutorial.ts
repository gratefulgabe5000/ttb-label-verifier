import { useContext, useEffect } from "react";
import { TutorialContext } from "@/contexts/tutorial-context";

export function useTutorial() {
  const context = useContext(TutorialContext);
  if (!context) {
    throw new Error("useTutorial must be used within a TutorialProvider");
  }
  return context;
}

/** Registers `document.getElementById("tutorial-{stepId}")` as the anchor for
 * a tutorial step while `enabled` is true, unregistering on cleanup.
 *
 * A MutationObserver keeps re-checking after the initial mount because the
 * anchor element (e.g. inside a Dialog's portal) may not exist in the DOM yet
 * at the moment this effect first runs -- without it, a step whose anchor
 * appears a tick late gets permanently auto-skipped by TutorialProvider
 * before its popup ever has a chance to show. */
export function useTutorialAnchor(stepId: string, enabled: boolean) {
  const { registerAnchor } = useTutorial();

  useEffect(() => {
    if (!enabled) {
      registerAnchor(stepId, null);
      return;
    }

    const sync = () => registerAnchor(stepId, document.getElementById(`tutorial-${stepId}`));
    sync();

    const observer = new MutationObserver(sync);
    observer.observe(document.body, { childList: true, subtree: true });

    return () => {
      observer.disconnect();
      registerAnchor(stepId, null);
    };
  }, [stepId, enabled, registerAnchor]);
}
