'use client'
import { ListBox, ListBoxItemIndicator, Select, Spinner, toast } from "@heroui/react";
import { useEffect, useRef, useState } from "react";
import { useSettingsStatus } from "@/context/SettingsStatusContext";

const DEVICE_LABELS: Record<string, string> = {
    cpu: "CPU",
    cuda: "GPU (CUDA)",
    auto: "Auto",
};

export function DeviceSelector() {
    const [device, setDevice] = useState<string | null>(null);
    const [cudaAvailable, setCudaAvailable] = useState(false);
    const [loading, setLoading] = useState(false);
    const [initializing, setInitializing] = useState(true);
    const { isBusy, statusLabel, notifyStarted } = useSettingsStatus();

    const fetchDeviceInfo = async () => {
        try {
            const response = await fetch("http://localhost:8000/settings/device");
            const data = await response.json();
            setDevice(data.device);
            setCudaAvailable(data.cuda_available);
        } catch (error) {
            console.error("DEVICE FETCH ERROR:", error);
        } finally {
            setInitializing(false);
        }
    };

    useEffect(() => {
        fetchDeviceInfo();
    }, []);

    // Once a global settings change finishes, refresh our own view of the device.
    // Only react to the busy -> idle transition (not every render where isBusy
    // happens to be false), since our own setLoading(true) and the context's
    // setIsBusy(true) land in separate commits and would otherwise race.
    const wasBusyRef = useRef(false);
    useEffect(() => {
        if (isBusy) wasBusyRef.current = true;

        if (!isBusy && wasBusyRef.current && loading) {
            wasBusyRef.current = false;
            setLoading(false);
            fetchDeviceInfo();
        }
    }, [isBusy, loading]);

    const handleChange = async (value: string) => {
        if (value === device) return;

        setLoading(true);
        try {
            const response = await fetch("http://localhost:8000/settings/device", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ device: value }),
            });

            const data = await response.json();

            if (data.error) {
                toast.danger(data.error);
                setLoading(false);
                return;
            }

            notifyStarted();
            toast.success(`Switching to ${DEVICE_LABELS[value] ?? value}…`);
        } catch (error) {
            console.error("DEVICE UPDATE ERROR:", error);
            toast.danger("Failed to update device");
            setLoading(false);
        }
    };

    if (initializing) return null;

    return (
        <Select
            placeholder="Choose Device Mode"
            variant="secondary"
            selectedKey={device}
            onChange={(value) => handleChange(value as string)}
            isDisabled={isBusy}
        >
            <Select.Trigger className="px-12 rounded-full font-bold">
                {loading ? (
                    <span className="flex items-center gap-2">
                        <Spinner color="current" size="sm" />
                        {statusLabel ?? "Reloading models…"}
                    </span>
                ) : (
                    <Select.Value />
                )}
                <Select.Indicator />
            </Select.Trigger>
            <Select.Popover>
                <ListBox>
                    <ListBox.Item id="cpu" textValue="CPU">
                        CPU
                        <ListBoxItemIndicator />
                    </ListBox.Item>
                    <ListBox.Item id="cuda" textValue="GPU (CUDA)" isDisabled={!cudaAvailable}>
                        GPU (CUDA){!cudaAvailable && " — unavailable"}
                        <ListBoxItemIndicator />
                    </ListBox.Item>
                    <ListBox.Item id="auto" textValue="Auto">
                        Auto
                        <ListBoxItemIndicator />
                    </ListBox.Item>
                </ListBox>
            </Select.Popover>
        </Select>
    );
}
