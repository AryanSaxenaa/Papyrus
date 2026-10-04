import { useCallback, useRef } from "react";
import Shepherd from "shepherd.js";
import type { Tour } from "shepherd.js";
import { markShepherdCompleted } from "../lib/shepherdStorage";

import "shepherd.js/dist/css/shepherd.css";

type Options = {
  onFinish: () => void;
};

export function useShepherdTour({ onFinish }: Options) {
  const tourRef = useRef<Tour | null>(null);

  const cancelTour = useCallback(() => {
    tourRef.current?.cancel();
    tourRef.current = null;
  }, []);

  const startTour = useCallback(
    (openCitationDrawer: () => void) => {
      cancelTour();

      const tour = new Shepherd.Tour({
        useModalOverlay: true,
        defaultStepOptions: {
          cancelIcon: { enabled: true },
          scrollTo: { behavior: "smooth", block: "center" },
          classes: "papyrus-shepherd-step",
        },
      });

      tour.on("complete", () => {
        markShepherdCompleted();
        tourRef.current = null;
        onFinish();
      });
      tour.on("cancel", () => {
        tourRef.current = null;
        onFinish();
      });

      tour.addStep({
        id: "welcome",
        title: "Guided tour",
        text: "This audit was loaded from a real recorded run (fixtures + SerpApi receipts). When you exit, the same results stay on screen so you can explore live.",
        attachTo: { element: "[data-testid='current-audit-card']", on: "bottom" },
        buttons: [
          { text: "Skip", classes: "shepherd-button-secondary", action: tour.cancel },
          { text: "Next", action: tour.next },
        ],
      });

      tour.addStep({
        id: "heatmap",
        title: "Citation heatmap",
        text: "Each tile is a reference. Color encodes integrity tier and verdict — click one to open the evidence drawer.",
        attachTo: { element: "[data-testid='citation-heatmap-section']", on: "top" },
        buttons: [
          { text: "Back", classes: "shepherd-button-secondary", action: tour.back },
          {
            text: "Open citation",
            action: () => {
              openCitationDrawer();
              void tour.next();
            },
          },
        ],
      });

      tour.addStep({
        id: "witness",
        title: "Witness matrix",
        text: "CrossRef, OpenAlex, Semantic Scholar, and SerpApi Scholar each corroborate (or stay silent). Silence is not guilt.",
        attachTo: { element: "[data-testid='witness-matrix']", on: "left" },
        buttons: [
          { text: "Back", classes: "shepherd-button-secondary", action: tour.back },
          { text: "Next", action: tour.next },
        ],
      });

      tour.addStep({
        id: "upload",
        title: "Your own manuscripts",
        text: "When you're ready, upload a PDF, DOI, or URL here for a live audit. Public demo may ask for an access code.",
        attachTo: { element: "[data-testid='app-upload-card']", on: "right" },
        buttons: [
          { text: "Back", classes: "shepherd-button-secondary", action: tour.back },
          { text: "Finish", action: tour.complete },
        ],
      });

      tourRef.current = tour;
      tour.start();
    },
    [cancelTour, onFinish],
  );

  return { startTour, cancelTour };
}
