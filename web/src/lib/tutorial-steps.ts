export type TutorialPlacement = "top" | "bottom" | "left" | "right";

export interface TutorialStep {
  id: string;
  message: string;
  placement: TutorialPlacement;
}

// Canonical order: TutorialProvider shows the first step in this array that
// is both not-yet-completed and has a registered anchor on the page.
export const TUTORIAL_STEPS: TutorialStep[] = [
  { id: "login", message: "Login using\nUsername: agent1\nPassword: password123", placement: "bottom" },
  { id: "api-key", message: "Enter your Anthropic API Key", placement: "bottom" },
  { id: "new-upload", message: "Click 'New Upload'!", placement: "bottom" },
  {
    id: "upload-form",
    message: "Add an Application Form PDF and matching Label images, then Upload.",
    placement: "right",
  },
  {
    id: "open-application",
    message: "Click on the application in this list to see Details.",
    placement: "bottom",
  },
  {
    id: "process",
    message: "Click 'Process' to assess the application using AI Vision.",
    placement: "bottom",
  },
  {
    id: "review-parameters",
    message: "Review parameters at the bottom of the page, if desired.",
    placement: "top",
  },
  {
    id: "review-recommendation",
    message: "Review the AI's recommendation, and either Override or Finalize!",
    placement: "bottom",
  },
  {
    id: "process-selected",
    message: "Check multiple applications, and click 'Process Selected', if desired!",
    placement: "right",
  },
];

export const TUTORIAL_STORAGE_KEY = "ttb-lvs-tutorial-completed-steps";
