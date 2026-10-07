'use client'
import { Label, ListBox, ListBoxItemIndicator, Select, Spinner, toast } from "@heroui/react";
import { useEffect, useRef, useState } from "react";
import { useSettingsStatus } from "@/context/SettingsStatusContext";

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

export function ModelSettings() {
    const [whisperModel, setWhisperModel] = useState<string | null>(null);
    const [nllbModel, setNllbModel] = useState<string | null>(null);
    const [loadingWhisper, setLoadingWhisper] = useState(false);
    const [loadingNllb, setLoadingNllb] = useState(false);
    const [initializing, setInitializing] = useState(true);
    const { isBusy, statusLabel, notifyStarted } = useSettingsStatus();

    const fetchModelInfo = async () => {
        try {
            const response = await fetch("http://localhost:8000/settings/device");
            const data = await response.json();
            setWhisperModel(data.whisper_model);
            setNllbModel(data.nllb_model);
        } catch (error) {
            console.error("MODEL SETTINGS FETCH ERROR:", error);
        } finally {
            setInitializing(false);
        }
    };

    useEffect(() => {
        fetchModelInfo();
    }, []);

    // Once a global settings change finishes, refresh our own view of the models.
    // Only react to the busy -> idle transition (not every render where isBusy
    // happens to be false), since our own setLoading*(true) and the context's
    // setIsBusy(true) land in separate commits and would otherwise race.
    const wasBusyRef = useRef(false);
    useEffect(() => {
        if (isBusy) wasBusyRef.current = true;

        if (!isBusy && wasBusyRef.current && (loadingWhisper || loadingNllb)) {
            wasBusyRef.current = false;
            setLoadingWhisper(false);
            setLoadingNllb(false);
            fetchModelInfo();
        }
    }, [isBusy, loadingWhisper, loadingNllb]);

    const handleWhisperChange = async (value: string) => {
        if (value === whisperModel) return;

        setLoadingWhisper(true);
        try {
            const response = await fetch("http://localhost:8000/settings/whisper_model", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ model_size: value }),
            });

            const data = await response.json();

            if (data.error) {
                toast.danger(data.error);
                setLoadingWhisper(false);
                return;
            }

            notifyStarted();
            toast.success(`Switching transcription model to ${value}…`);
        } catch (error) {
            console.error("WHISPER MODEL UPDATE ERROR:", error);
            toast.danger("Failed to update Whisper model");
            setLoadingWhisper(false);
        }
    };

    const handleNllbChange = async (value: string) => {
        if (value === nllbModel) return;

        setLoadingNllb(true);
        try {
            const response = await fetch("http://localhost:8000/settings/nllb_model", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ model_name: value }),
            });

            const data = await response.json();

            if (data.error) {
                toast.danger(data.error);
                setLoadingNllb(false);
                return;
            }

            notifyStarted();
            toast.success(`Switching translation model to ${NLLB_LABELS[value] ?? value}…`);
        } catch (error) {
            console.error("NLLB MODEL UPDATE ERROR:", error);
            toast.danger("Failed to update translation model");
            setLoadingNllb(false);
        }
    };

    if (initializing) return null;

    return (
        <div className="flex flex-col md:flex-row items-center gap-3">
            <Select
                placeholder="Whisper Model"
                variant="secondary"
                selectedKey={whisperModel}
                onChange={(value) => handleWhisperChange(value as string)}
                isDisabled={isBusy}
            >
                <Label>Transcription Model</Label>
                <Select.Trigger className="px-8 rounded-full font-bold">
                    {loadingWhisper ? (
                        <span className="flex items-center gap-2">
                            <Spinner color="current" size="sm" />
                            {statusLabel ?? "Reloading…"}
                        </span>
                    ) : (
                        <Select.Value />
                    )}
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
                selectedKey={nllbModel}
                onChange={(value) => handleNllbChange(value as string)}
                isDisabled={isBusy}
            >
                <Label>Translation Model</Label>
                <Select.Trigger className="px-8 rounded-full font-bold">
                    {loadingNllb ? (
                        <span className="flex items-center gap-2">
                            <Spinner color="current" size="sm" />
                            {statusLabel ?? "Reloading…"}
                        </span>
                    ) : (
                        <Select.Value />
                    )}
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
        </div>
    );
}
