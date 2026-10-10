'use client'
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { apiUrl } from "@/lib/api";
import type { Preflight } from "@/lib/types";

type SettingsStage = "idle" | "loading" | "ready" | "error";

interface SettingsStatus {
    stage: SettingsStage;
    target: string | null;
    bytes_downloaded: number | null;
    bytes_total: number | null;
    error: string | null;
}

interface DeviceInfo {
    device: string;
    active_stt_device: string | null;
    active_translation_device: string | null;
    cuda_available: boolean;
    whisper_model: string | null;
    nllb_model: string | null;
    default_whisper_model: string;
    default_nllb_model: string;
    is_ready: boolean;
}

interface SettingsStatusContextValue {
    isBusy: boolean;
    statusLabel: string | null;
    bytesDownloaded: number | null;
    bytesTotal: number | null;
    isReady: boolean;
    initializing: boolean;
    device: DeviceInfo | null;
    preflight: Preflight | null;
    // Called right after a POST is fired, so the UI locks immediately
    // instead of waiting for the first poll tick to catch up.
    notifyStarted: () => void;
    refreshDevice: () => Promise<void>;
}

const SettingsStatusContext = createContext<SettingsStatusContextValue>({
    isBusy: false,
    statusLabel: null,
    bytesDownloaded: null,
    bytesTotal: null,
    isReady: false,
    initializing: true,
    device: null,
    preflight: null,
    notifyStarted: () => {},
    refreshDevice: async () => {},
});

export function useSettingsStatus() {
    return useContext(SettingsStatusContext);
}

export function SettingsStatusProvider({ children }: { children: React.ReactNode }) {
    const [isBusy, setIsBusy] = useState(false);
    const [statusLabel, setStatusLabel] = useState<string | null>(null);
    const [bytesDownloaded, setBytesDownloaded] = useState<number | null>(null);
    const [bytesTotal, setBytesTotal] = useState<number | null>(null);
    const [device, setDevice] = useState<DeviceInfo | null>(null);
    const [preflight, setPreflight] = useState<Preflight | null>(null);
    const [initializing, setInitializing] = useState(true);
    const pollRef = useRef<NodeJS.Timeout | null>(null);

    const refreshDevice = useCallback(async () => {
        try {
            const response = await fetch(apiUrl("/settings/device"));
            const data: DeviceInfo = await response.json();
            setDevice(data);
        } catch (error) {
            console.error("DEVICE FETCH ERROR:", error);
        } finally {
            setInitializing(false);
        }
    }, []);

    /* eslint-disable react-hooks/set-state-in-effect --
       Fetch-on-mount via stable, externally-reusable callbacks (refreshDevice is also
       called from poll() and exposed through context). Not a cascading setState loop,
       just the initial load of remote data. */
    useEffect(() => {
        refreshDevice();

        fetch(apiUrl("/settings/preflight"))
            .then((response) => response.json())
            .then((data: Preflight) => setPreflight(data))
            .catch((error) => console.error("PREFLIGHT FETCH ERROR:", error));
    }, [refreshDevice]);
    /* eslint-enable react-hooks/set-state-in-effect */

    const poll = useCallback(async () => {
        try {
            const response = await fetch(apiUrl("/settings/status"));
            const data: SettingsStatus = await response.json();

            if (data.stage === "loading") {
                setIsBusy(true);
                setStatusLabel(data.target ?? "Loading…");
                setBytesDownloaded(data.bytes_downloaded);
                setBytesTotal(data.bytes_total);
            } else {
                setIsBusy(false);
                setStatusLabel(null);
                setBytesDownloaded(null);
                setBytesTotal(null);
                if (pollRef.current) {
                    clearInterval(pollRef.current);
                    pollRef.current = null;
                }
                // Settings change (or initial setup) just finished — refresh
                // our view of the device/models so is_ready etc. stay current.
                refreshDevice();
            }
        } catch (error) {
            console.error("SETTINGS STATUS POLL ERROR:", error);
        }
    }, [refreshDevice]);

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
        <SettingsStatusContext.Provider
            value={{
                isBusy,
                statusLabel,
                bytesDownloaded,
                bytesTotal,
                isReady: device?.is_ready ?? false,
                initializing,
                device,
                preflight,
                notifyStarted,
                refreshDevice,
            }}
        >
            {children}
        </SettingsStatusContext.Provider>
    );
}
