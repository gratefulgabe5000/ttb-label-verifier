import { createContext } from "react";

export interface TutorialContextValue {
  activeStepId: string | null;
  activeAnchorEl: HTMLElement | null;
  registerAnchor: (stepId: string, el: HTMLElement | null) => void;
  dismiss: (stepId: string) => void;
  reset: () => void;
}

export const TutorialContext = createContext<TutorialContextValue | undefined>(undefined);
