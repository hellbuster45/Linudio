'use client'
import {
    Button,
    Drawer,
    Label,
    ListBox,
    ListBoxItemIndicator,
    ProgressBar,
    Select,
    toast,
    useOverlayState,
} from "@heroui/react";
import { useEffect, useState } from "react";
import { useSettingsStatus } from "@/context/SettingsStatusContext";

type OverlayState = ReturnType<typeof useOverlayState>;

const DEVICE_LABELS: Record<string, string> = {
    cpu: "CPU",
    cuda: "GPU (CUDA)",
    auto: "Auto",
};

const WHISPER_MODELS = ["tiny", "small", "medium", "large-v3", "large-v3-turbo"];
const NLLB_MODELS = [
    "facebook/nllb-200-distilled-600M",
    "facebook/nllb-200-distilled-1.3B",
    "facebook/nllb-200-3.3B",
];
const NLLB_LABELS: Record<string, string> = {
    "facebook/nllb-200-distilled-600M": "NLLB 600M (fastest)",
    "facebook/nllb-200-distilled-1.3B": "NLLB 1.3B (balanced)",
    "facebook/nllb-200-3.3B": "NLLB 3.3B (best quality)",
};

function formatBytes(bytes: number | null): string {
    if (bytes === null) return "";
    const mb = bytes / (1024 * 1024);
    if (mb < 1024) return `${mb.toFixed(0)} MB`;
    return `${(mb / 1024).toFixed(2)} GB`;
}

export function SettingsDrawer({ state }: { state: OverlayState }) {
    const { isBusy, statusLabel, bytesDownloaded, bytesTotal, isReady, device, notifyStarted, refreshDevice } =
        useSettingsStatus();

    // Local selections: pre-filled from the backend once loaded (or sane
    // defaults pre-setup), editable regardless of isReady so the user can
    // pick their initial setup options before anything is loaded.
    const [selectedDevice, setSelectedDevice] = useState<string>("cpu");
    const [selectedWhisper, setSelectedWhisper] = useState<string>("large-v3-turbo");
    const [selectedNllb, setSelectedNllb] = useState<string>("facebook/nllb-200-distilled-600M");

    /* eslint-disable react-hooks/set-state-in-effect --
       Mirrors the backend's device/model state (arrives async via polling)
       into local editable selection state. Intentional derived-state sync,
       not a cascading setState loop. */
    useEffect(() => {
        if (!device) return;
        setSelectedDevice(device.device);
        if (device.whisper_model) setSelectedWhisper(device.whisper_model);
        if (device.nllb_model) setSelectedNllb(device.nllb_model);
    }, [device]);
    /* eslint-enable react-hooks/set-state-in-effect */

    const handleSetup = async () => {
        try {
            const response = await fetch("http://localhost:8000/settings/setup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    device: selectedDevice,
                    whisper_model: selectedWhisper,
                    nllb_model: selectedNllb,
                }),
            });
            const data = await response.json();

            if (data.error) {
                toast.danger(data.error);
                return;
            }

            notifyStarted();
            toast.success("Setting up models…");
        } catch (error) {
            console.error("SETUP ERROR:", error);
            toast.danger("Failed to start setup");
        }
    };

    const handleDeviceChange = async (value: string) => {
        setSelectedDevice(value);
        if (!isReady) return; // part of the pending setup payload, not applied yet

        try {
            const response = await fetch("http://localhost:8000/settings/device", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ device: value }),
            });
            const data = await response.json();

            if (data.error) {
                toast.danger(data.error);
                refreshDevice();
                return;
            }

            notifyStarted();
            toast.success(`Switching to ${DEVICE_LABELS[value] ?? value}…`);
        } catch (error) {
            console.error("DEVICE UPDATE ERROR:", error);
            toast.danger("Failed to update device");
        }
    };

    const handleWhisperChange = async (value: string) => {
        setSelectedWhisper(value);
        if (!isReady) return;

        try {
            const response = await fetch("http://localhost:8000/settings/whisper_model", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ model_size: value }),
            });
            const data = await response.json();

            if (data.error) {
                toast.danger(data.error);
                refreshDevice();
                return;
            }

            notifyStarted();
            toast.success(`Switching transcription model to ${value}…`);
        } catch (error) {
            console.error("WHISPER MODEL UPDATE ERROR:", error);
            toast.danger("Failed to update Whisper model");
        }
    };

    const handleNllbChange = async (value: string) => {
        setSelectedNllb(value);
        if (!isReady) return;

        try {
            const response = await fetch("http://localhost:8000/settings/nllb_model", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ model_name: value }),
            });
            const data = await response.json();

            if (data.error) {
                toast.danger(data.error);
                refreshDevice();
                return;
            }

            notifyStarted();
            toast.success(`Switching translation model to ${NLLB_LABELS[value] ?? value}…`);
        } catch (error) {
            console.error("NLLB MODEL UPDATE ERROR:", error);
            toast.danger("Failed to update translation model");
        }
    };

    const progressPercent =
        bytesDownloaded !== null && bytesTotal !== null && bytesTotal > 0
            ? Math.min(100, Math.round((bytesDownloaded / bytesTotal) * 100))
            : null;

    return (
        <Drawer state={state}>
            <Drawer.Backdrop>
                <Drawer.Content placement="right">
                    <Drawer.Dialog>
                        <Drawer.Header>
                            <Drawer.Heading>Settings</Drawer.Heading>
                            <Drawer.CloseTrigger />
                        </Drawer.Header>
                        <Drawer.Body className="flex flex-col gap-6">
                            {!isReady && !isBusy && (
                                <p className="text-sm text-muted-foreground">
                                    Pick your device and model sizes below, then click{" "}
                                    <span className="font-semibold">Set Up</span> to download and load
                                    them. This only needs to be done once — switching settings later
                                    just reloads the one you changed.
                                </p>
                            )}

                            <Select
                                placeholder="Choose Device Mode"
                                variant="secondary"
                                selectedKey={selectedDevice}
                                onChange={(value) => handleDeviceChange(value as string)}
                                isDisabled={isBusy}
                            >
                                <Label>Device</Label>
                                <Select.Trigger className="rounded-full font-bold">
                                    <Select.Value />
                                    <Select.Indicator />
                                </Select.Trigger>
                                <Select.Popover>
                                    <ListBox>
                                        <ListBox.Item id="cpu" textValue="CPU">
                                            CPU
                                            <ListBoxItemIndicator />
                                        </ListBox.Item>
                                        <ListBox.Item
                                            id="cuda"
                                            textValue="GPU (CUDA)"
                                            isDisabled={!device?.cuda_available}
                                        >
                                            GPU (CUDA){!device?.cuda_available && " — unavailable"}
                                            <ListBoxItemIndicator />
                                        </ListBox.Item>
                                        <ListBox.Item id="auto" textValue="Auto">
                                            Auto
                                            <ListBoxItemIndicator />
                                        </ListBox.Item>
                                    </ListBox>
                                </Select.Popover>
                            </Select>

                            <Select
                                placeholder="Whisper Model"
                                variant="secondary"
                                selectedKey={selectedWhisper}
                                onChange={(value) => handleWhisperChange(value as string)}
                                isDisabled={isBusy}
                            >
                                <Label>Transcription Model</Label>
                                <Select.Trigger className="rounded-full font-bold">
                                    <Select.Value />
                                    <Select.Indicator />
                                </Select.Trigger>
                                <Select.Popover>
                                    <ListBox>
                                        {WHISPER_MODELS.map((m) => (
                                            <ListBox.Item key={m} id={m} textValue={m}>
                                                {m}
                                                <ListBoxItemIndicator />
                                            </ListBox.Item>
                                        ))}
                                    </ListBox>
                                </Select.Popover>
                            </Select>

                            <Select
                                placeholder="Translation Model"
                                variant="secondary"
                                selectedKey={selectedNllb}
                                onChange={(value) => handleNllbChange(value as string)}
                                isDisabled={isBusy}
                            >
                                <Label>Translation Model</Label>
                                <Select.Trigger className="rounded-full font-bold">
                                    <Select.Value />
                                    <Select.Indicator />
                                </Select.Trigger>
                                <Select.Popover>
                                    <ListBox>
                                        {NLLB_MODELS.map((m) => (
                                            <ListBox.Item key={m} id={m} textValue={NLLB_LABELS[m]}>
                                                {NLLB_LABELS[m]}
                                                <ListBoxItemIndicator />
                                            </ListBox.Item>
                                        ))}
                                    </ListBox>
                                </Select.Popover>
                            </Select>

                            {isBusy && (
                                <div className="flex flex-col gap-2 rounded-xl border border-white/10 bg-white/5 p-4">
                                    <p className="text-sm font-semibold">{statusLabel ?? "Working…"}</p>
                                    {progressPercent !== null ? (
                                        <ProgressBar value={progressPercent} minValue={0} maxValue={100}>
                                            <div className="flex justify-between text-xs text-muted-foreground">
                                                <ProgressBar.Output />
                                                <span>
                                                    {formatBytes(bytesDownloaded)} / {formatBytes(bytesTotal)}
                                                </span>
                                            </div>
                                            <ProgressBar.Track>
                                                <ProgressBar.Fill />
                                            </ProgressBar.Track>
                                        </ProgressBar>
                                    ) : (
                                        <p className="text-xs text-muted-foreground">
                                            Preparing… this can take a while on first run.
                                        </p>
                                    )}
                                </div>
                            )}
                        </Drawer.Body>
                        {!isReady && (
                            <Drawer.Footer>
                                <Button
                                    size="lg"
                                    variant="primary"
                                    className="w-full font-bold rounded-full"
                                    onClick={handleSetup}
                                    isDisabled={isBusy}
                                >
                                    Set Up
                                </Button>
                            </Drawer.Footer>
                        )}
                    </Drawer.Dialog>
                </Drawer.Content>
            </Drawer.Backdrop>
        </Drawer>
    );
}
