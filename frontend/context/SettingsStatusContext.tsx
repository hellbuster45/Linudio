'use client'
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

type SettingsStage = "idle" | "loading" | "ready" | "error";

interface SettingsStatus {
    stage: SettingsStage;
    target: string | null;
    error: string | null;
}

interface SettingsStatusContextValue {
    isBusy: boolean;
    statusLabel: string | null;
    // Called right after a POST is fired, so the UI locks immediately
    // instead of waiting for the first poll tick to catch up.
    notifyStarted: () => void;
}

const SettingsStatusContext = createContext<SettingsStatusContextValue>({
    isBusy: false,
    statusLabel: null,
    notifyStarted: () => {},
});

export function useSettingsStatus() {
    return useContext(SettingsStatusContext);
}

export function SettingsStatusProvider({ children }: { children: React.ReactNode }) {
    const [isBusy, setIsBusy] = useState(false);
    const [statusLabel, setStatusLabel] = useState<string | null>(null);
    const pollRef = useRef<NodeJS.Timeout | null>(null);

    const poll = useCallback(async () => {
        try {
            const response = await fetch("http://localhost:8000/settings/status");
            const data: SettingsStatus = await response.json();

            if (data.stage === "loading") {
                setIsBusy(true);
                setStatusLabel(data.target ?? "Loading…");
            } else {
                setIsBusy(false);
                setStatusLabel(null);
                if (pollRef.current) {
                    clearInterval(pollRef.current);
                    pollRef.current = null;
                }
            }
        } catch (error) {
            console.error("SETTINGS STATUS POLL ERROR:", error);
        }
    }, []);

    const notifyStarted = useCallback(() => {
        setIsBusy(true);
        if (pollRef.current) return;
        poll();
        pollRef.current = setInterval(poll, 1000);
    }, [poll]);

    useEffect(() => {
        return () => {
            if (pollRef.current) clearInterval(pollRef.current);
        };
    }, []);

    return (
        <SettingsStatusContext.Provider value={{ isBusy, statusLabel, notifyStarted }}>
            {children}
        </SettingsStatusContext.Provider>
    );
}
