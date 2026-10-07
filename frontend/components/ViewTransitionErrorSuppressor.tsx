'use client'
import { useEffect } from "react";

// HeroUI's toast queue (and Next.js route transitions) call
// document.startViewTransition() without attaching a .catch() to the
// returned transition's promises. If the tab is hidden right as a
// transition starts, the browser rejects with InvalidStateError, and
// since nothing ever handles it, it surfaces as an unhandled rejection —
// which Next's dev overlay reports unconditionally, ignoring
// event.preventDefault(). So listening for the rejection after the fact
// is too late; we patch startViewTransition itself so the rejection is
// handled at the source and never becomes "unhandled" in the first place.
function isHiddenDocumentAbort(reason: unknown) {
    return (
        reason instanceof DOMException &&
        reason.name === "InvalidStateError" &&
        reason.message.includes("Document hidden")
    );
}

export function ViewTransitionErrorSuppressor() {
    useEffect(() => {
        if (!("startViewTransition" in document)) return;

        const original = document.startViewTransition.bind(document);
        document.startViewTransition = ((callback?: () => void | Promise<void>) => {
            const transition = original(callback);
            transition.ready.catch((reason) => {
                if (!isHiddenDocumentAbort(reason)) throw reason;
            });
            transition.finished.catch((reason) => {
                if (!isHiddenDocumentAbort(reason)) throw reason;
            });
            return transition;
        }) as typeof document.startViewTransition;

        return () => {
            document.startViewTransition = original;
        };
    }, []);

    return null;
}
