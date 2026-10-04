import { useCallback, useRef } from "react";
import Shepherd from "shepherd.js";
import type { Tour } from "shepherd.js";
import { markShepherdCompleted } from "../lib/shepherdStorage";

import "shepherd.js/dist/css/shepherd.css";

export type ShepherdTourControls = {
  openCitation: () => void;
  closeCitation: () => void;
  openActivity: () => void;
  scrollToTourTarget: (selector: string) => void;
};

type Options = {
  onFinish: () => void;
};

function waitForSelector(selector: string, timeoutMs = 4000): Promise<Element | null> {
  return new Promise((resolve) => {
    const existing = document.querySelector(selector);
    if (existing) {
      resolve(existing);
      return;
    }
    const deadline = Date.now() + timeoutMs;
    const tick = () => {
      const el = document.querySelector(selector);
      if (el) {
        resolve(el);
        return;
      }
      if (Date.now() >= deadline) {
        resolve(null);
        return;
      }
      window.requestAnimationFrame(tick);
    };
    tick();
  });
}

export function useShepherdTour({ onFinish }: Options) {
  const tourRef = useRef<Tour | null>(null);

  const cancelTour = useCallback(() => {
    tourRef.current?.cancel();
    tourRef.current = null;
  }, []);

  const startTour = useCallback(
    (controls: ShepherdTourControls) => {
      cancelTour();
      controls.closeCitation();
      controls.scrollToTourTarget("[data-tour='shepherd-upload']");

      const tour = new Shepherd.Tour({
        useModalOverlay: true,
        defaultStepOptions: {
          cancelIcon: { enabled: true },
          scrollTo: { behavior: "smooth", block: "center" },
          classes: "papyrus-shepherd-step",
          modalOverlayOpeningPadding: 8,
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

      const go = (selector: string, action: () => void) => {
        controls.scrollToTourTarget(selector);
        window.setTimeout(action, 350);
      };

      tour.addStep({
        id: "upload",
        title: "Upload your manuscript",
        text:
          "Start a live audit from a PDF, DOI, or URL. Bulk ZIP and sample PDF shortcuts live here too. Nothing is uploaded during this tour until you choose to.",
        attachTo: { element: "[data-tour='shepherd-upload']", on: "bottom" },
        beforeShowPromise: () =>
          waitForSelector("[data-tour='shepherd-upload']").then((el) => {
            controls.closeCitation();
            el?.scrollIntoView({ behavior: "smooth", block: "center" });
          }),
        buttons: [
          { text: "Skip tour", classes: "shepherd-button-secondary", action: tour.cancel },
          { text: "Next", action: tour.next },
        ],
      });

      tour.addStep({
        id: "serpapi-meter",
        title: "SerpApi credit ledger",
        text:
          "Live audits call Google Scholar through SerpApi (`google_scholar`, `google_scholar_cite`, `google_scholar_author`). This meter tracks monthly spend against your cap.",
        attachTo: { element: "[data-tour='shepherd-serpapi-meter']", on: "bottom" },
        beforeShowPromise: () =>
          waitForSelector("[data-tour='shepherd-serpapi-meter']").then((el) => {
            controls.closeCitation();
            el?.scrollIntoView({ behavior: "smooth", block: "center" });
          }),
        buttons: [
          { text: "Back", classes: "shepherd-button-secondary", action: tour.back },
          { text: "Next", action: tour.next },
        ],
      });

      tour.addStep({
        id: "audit",
        title: "Audit summary",
        text:
          "Coverage, risk, and pipeline version for the preloaded replay audit (real fixture data). After the tour, this panel stays so you can export reports or run your own uploads.",
        attachTo: { element: "[data-tour='shepherd-audit']", on: "bottom" },
        beforeShowPromise: () =>
          waitForSelector("[data-tour='shepherd-audit']").then((el) => {
            controls.closeCitation();
            el?.scrollIntoView({ behavior: "smooth", block: "center" });
          }),
        buttons: [
          { text: "Back", classes: "shepherd-button-secondary", action: tour.back },
          { text: "Next", action: tour.next },
        ],
      });

      tour.addStep({
        id: "heatmap",
        title: "Citation heatmap",
        text: "Each tile is a reference. Colors show tier and verdict. Next we open one citation to show SerpApi witness evidence.",
        attachTo: { element: "[data-tour='shepherd-heatmap']", on: "top" },
        beforeShowPromise: () =>
          waitForSelector("[data-tour='shepherd-heatmap']").then((el) => {
            controls.closeCitation();
            el?.scrollIntoView({ behavior: "smooth", block: "center" });
          }),
        buttons: [
          { text: "Back", classes: "shepherd-button-secondary", action: tour.back },
          {
            text: "Open citation",
            action: () => {
              controls.openCitation();
              go("[data-tour='shepherd-witness-block']", () => tour.next());
            },
          },
        ],
      });

      tour.addStep({
        id: "witness",
        title: "Witness matrix (incl. SerpApi Scholar)",
        text:
          "CrossRef, OpenAlex, and Semantic Scholar are independent indexes. SerpApi Scholar is an extra witness: a hit can corroborate a reference; silence is never treated as guilt.",
        attachTo: { element: "[data-tour='shepherd-witness-block']", on: "left" },
        beforeShowPromise: () =>
          waitForSelector("[data-tour='shepherd-witness-block']").then((el) => {
            controls.openCitation();
            el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }),
        buttons: [
          { text: "Back", classes: "shepherd-button-secondary", action: tour.back },
          { text: "Next", action: tour.next },
        ],
      });

      tour.addStep({
        id: "receipts",
        title: "SerpApi receipts",
        text:
          "Every Scholar call stores a receipt (`search_metadata.id`, engine, redacted params, credits). Download the evidence bundle ZIP to verify offline.",
        attachTo: { element: "[data-tour='shepherd-serpapi-receipts']", on: "top" },
        beforeShowPromise: () =>
          waitForSelector("[data-tour='shepherd-serpapi-receipts']").then((el) => {
            controls.openCitation();
            el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }),
        buttons: [
          { text: "Back", classes: "shepherd-button-secondary", action: tour.back },
          {
            text: "Next",
            action: () => {
              controls.closeCitation();
              go("[data-tour='shepherd-activity']", () => tour.next());
            },
          },
        ],
      });

      tour.addStep({
        id: "activity",
        title: "Live activity log",
        text: "Resolver steps stream here during a run. Replay mode replays recorded events with compressed timing.",
        attachTo: { element: "[data-tour='shepherd-activity']", on: "top" },
        beforeShowPromise: () =>
          waitForSelector("[data-tour='shepherd-activity']").then((el) => {
            controls.closeCitation();
            controls.openActivity();
            el?.scrollIntoView({ behavior: "smooth", block: "center" });
          }),
        buttons: [
          { text: "Back", classes: "shepherd-button-secondary", action: tour.back },
          {
            text: "Finish",
            action: () => {
              controls.closeCitation();
              tour.complete();
            },
          },
        ],
      });

      tourRef.current = tour;
      tour.start();
    },
    [cancelTour, onFinish],
  );

  return { startTour, cancelTour };
}
