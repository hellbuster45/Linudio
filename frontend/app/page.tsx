'use client'
import { SettingsDrawer } from "@/components/SettingsDrawer";
import { useSettingsStatus } from "@/context/SettingsStatusContext";
import { FetchVideo } from "@/components/FetchVideo";
import { TranscriptPane } from "@/components/TranscriptPane";
import { TranslatedPane } from "@/components/TranslatedPane";
import { VideoCard } from "@/components/VideoCard";
import { Button, Card, Separator, Spinner, toast, Toast, useOverlayState } from "@heroui/react";
import { Settings } from "lucide-react";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { apiUrl } from "@/lib/api";
import { downloadFromUrl } from "@/lib/utils";
import type { Transcript, Translated, VideoMetadata } from "@/lib/types";

const DUB_STATUS_LABELS: Record<string, string> = {
  pending: "Queued",
  seperation: "Separating vocals",
  tts_generation: "Generating speech",
  complete: "Finishing up",
};

function SettingsTrigger({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      aria-label="Open settings"
      className="fixed top-6 right-6 z-40 flex items-center justify-center w-11 h-11 rounded-full border border-white/10 bg-white/5 backdrop-blur-md hover:bg-white/10 transition-colors cursor-pointer"
    >
      <Settings className="w-5 h-5" />
    </button>
  );
}

function PreflightNotice() {
  const { preflight } = useSettingsStatus();
  const missing = preflight?.checks.filter((check) => !check.ok) ?? [];

  if (missing.length === 0) return null;

  return (
    <div className="mt-6 mx-auto max-w-md rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 text-left text-sm">
      <p className="font-semibold">Some tools weren&apos;t found on this machine:</p>
      <ul className="mt-2 list-disc pl-5 space-y-1 text-muted-foreground">
        {missing.map((check) => (
          <li key={check.name}>
            <span className="font-medium text-foreground">
              {check.name}
              {check.optional ? " (optional)" : ""}
            </span>
            : {check.hint}
          </li>
        ))}
      </ul>
    </div>
  );
}

function GetStartedSection({ onClick }: { onClick: () => void }) {
  const { isBusy, isReady, initializing } = useSettingsStatus();

  if (initializing) return null;

  if (!isReady) {
    return (
      <>
        <div className="mt-6 flex flex-col items-center gap-2 text-center">
          <p className="text-muted-foreground max-w-md">
            Models haven&apos;t been set up yet. Open{" "}
            <span className="font-semibold text-foreground">Settings</span> (top-right) to
            choose your device and model sizes, then load them up before getting started.
          </p>
        </div>
        <PreflightNotice />
      </>
    );
  }

  return (
    <>
      <motion.div
        className="mt-6"
        initial={{ scale: 0.9 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: isBusy ? 1 : 1.05 }}
      >
        <Button
          size="lg"
          variant="primary"
          className="font-bold px-12 rounded-full"
          onClick={onClick}
          isDisabled={isBusy}
        >
          Get Started
        </Button>
      </motion.div>
      <PreflightNotice />
    </>
  );
}

export default function Home() {
  const [started, setStarted] = useState(false);
  const [video_id, setVideoID] = useState<string | null>(null);
  const settingsDrawerState = useOverlayState();

  const [metadata, setMetadata] = useState<VideoMetadata | null>(null);

  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [originalTranscript, setOriginalTranscript] = useState<Transcript | null>(null);

  const [translated, setTranslated] = useState<Translated | null>(null);
  const [originalTranslated, setOriginalTranslated] = useState<Translated | null>(null);

  const [dubStarted, setDubStarted] = useState(false);
  const [dubStatus, setDubStatus] = useState<string | null>(null);
  const [finalVideoUrl, setFinalVideoUrl] = useState<string | null>(null);

  const handleData = (data: VideoMetadata) => {
    toast.success("Video Fetched !");
    // A new video invalidates everything derived from the previous one.
    setTranscript(null);
    setOriginalTranscript(null);
    setTranslated(null);
    setOriginalTranslated(null);
    setDubStatus(null);
    setFinalVideoUrl(null);

    setMetadata(data);
    setVideoID(data.video_id);
  };

  const saveTranscript = (data: Transcript) => {
    // Keep an independent deep copy: without it, transcript and originalTranscript
    // would point to the same object, and editing one would change the other,
    // defeating the "Reset Changes" button.
    setOriginalTranscript(structuredClone(data));

    setTranscript(data);
  }

  const saveTranslated = (data: Translated) => {
    setOriginalTranslated(structuredClone(data));
    setTranslated(data);
  }

  const resetTranscript = () => {
    if (originalTranscript) {
      setTranscript(originalTranscript);
    }
  }

  const resetTranslated = () => {
    if (originalTranslated) {
      setTranslated(originalTranslated);
    }
  }

  const updatedSegment = (type: "original" | "translated", index: number, newText: string) => {
    if (type === "original" && transcript) {
      setTranscript((prev) => {
        if (!prev || prev.segments[index].text === newText) return prev;
        // 1. Create a new array reference for segments
        const newSegments = [...prev.segments];

        // 2. Create a new object reference for the specific segment being edited
        newSegments[index] = { ...newSegments[index], text: newText };

        // 3. Return a brand new object for the transcript
        return { ...prev, segments: newSegments };
      });
    } else if (type === "translated" && translated) {
      setTranslated((prev) => {
        if (!prev || prev.translated_segments[index].text === newText) return prev;

        const newSegments = [...prev.translated_segments];
        newSegments[index] = { ...newSegments[index], text: newText };
        return { ...prev, translated_segments: newSegments };
      });
    }
  }

  // Poll the backend while a dub is running, and stop on every way it can end.
  useEffect(() => {
    if (!dubStarted || !video_id) return;

    let consecutiveFailures = 0;

    const interval = setInterval(async () => {
      try {
        const response = await fetch(apiUrl(`/text_to_speech/dub_status?video_id=${video_id}`));
        const data = await response.json();
        consecutiveFailures = 0;

        if (data.status === "success") {
          setFinalVideoUrl(apiUrl(data.video_path));
          setDubStatus(null);
          setDubStarted(false);
        } else if (data.status === "failed" || data.status === "not_found") {
          toast.danger(
            data.status === "failed"
              ? "Dubbing failed. Check the backend logs for details."
              : "The dubbing job could not be found."
          );
          setDubStatus(null);
          setDubStarted(false);
        } else {
          setDubStatus(data.status);
        }
      } catch (err) {
        console.error("Polling error", err);
        consecutiveFailures += 1;
        if (consecutiveFailures >= 5) {
          toast.danger("Lost connection to the backend while dubbing.");
          setDubStatus(null);
          setDubStarted(false);
        }
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [dubStarted, video_id]);

  const handleDownload = () => {
    if (!finalVideoUrl || !video_id) return;
    downloadFromUrl(finalVideoUrl, `${video_id}_dubbed.mp4`).catch(() => toast.danger("Download failed"));
  };

  return (
    <main className="min-h-screen bg-background font-sans selection:bg-accent/30">
      <Toast.Provider placement="top" />
      <SettingsTrigger onClick={settingsDrawerState.open} />
      <SettingsDrawer state={settingsDrawerState} />
      <div className="max-w-[95%] mx-auto px-4 py-12 flex flex-col items-center gap-12">

        {/* --- Header Section --- */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-4"
        >
          <h1 className="text-5xl font-bold tracking-tight bg-linear-to-r from-primary to-accent bg-clip-text text-transparent">
            Linudio
          </h1>
          <p className="text-muted-foreground text-xl max-w-2xl">
            Multi-Agent Youtube Video Translation and Dubbing Simplified!
          </p>

          {!started && <GetStartedSection onClick={() => setStarted(true)} />}
        </motion.div>

        {/* --- Input Section --- */}
        <AnimatePresence>
          {started && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="w-full flex justify-center"
            >
              <FetchVideo onVideoFetched={handleData} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* --- Polling Status Overlay --- */}
        {!finalVideoUrl && dubStatus && (
          <div className="fixed bottom-10 right-10 z-50">
            <div className="bg-zinc-900 border border-white/10 p-6 rounded-2xl shadow-2xl flex flex-col items-center gap-4">
              <Spinner color="current" />
              <div className="text-center">
                <p className="font-bold">{DUB_STATUS_LABELS[dubStatus] ?? dubStatus}</p>
                <p className="text-xs text-muted-foreground">Please keep this tab open</p>
              </div>
            </div>
          </div>
        )}

        {/* --- Result Grid --- */}
        <div className="w-full space-y-8 flex flex-col items-center">
          {metadata && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
            >
              <VideoCard
                metadata={metadata}
                onTranscriptFetched={(data) => saveTranscript(data)}
              />
            </motion.div>
          )}

          {(transcript || translated) && (
            <div className="w-auto md:w-[50%] lg:w-[75%] flex flex-row justify-center gap-0 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md">
              <AnimatePresence mode="wait">
                {transcript && (
                  <motion.div
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="p-6 w-full"
                  >
                    <TranscriptPane
                      video_id={video_id!}
                      transcript={transcript}
                      onTranslatedFetched={(data) => saveTranslated(data)}
                      onReset={resetTranscript}
                      onUpdate={(idx, text) => updatedSegment('original', idx, text)}
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              {translated && (
                <motion.div
                  initial={{ opacity: 0, x: 50 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="p-6 border-l border-white/10 relative w-full"
                >
                  <div className="absolute inset-y-0 left-[0.5px] hidden lg:block">
                    <Separator orientation="vertical" />
                  </div>
                  <TranslatedPane
                    video_id={video_id!}
                    translated={translated}
                    onDubStarted={() => {
                      setFinalVideoUrl(null);
                      setDubStatus("pending");
                      setDubStarted(true);
                    }}
                    onReset={resetTranslated}
                    onUpdate={(idx, text) => updatedSegment('translated', idx, text)}
                  />
                </motion.div>
              )}
            </div>
          )}
        </div>

        {/* --- Final Video Display --- */}
        {finalVideoUrl && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-4xl rounded-xl overflow-hidden shadow-2xl"
          >
            <Card>
              <Card.Header>
                <Card.Title className="text-2xl text-accent">Dubbing Complete !</Card.Title>
              </Card.Header>
              <video key={finalVideoUrl} controls className="w-full rounded-xl">
                <source src={finalVideoUrl} type="video/mp4" />
              </video>
              <Card.Footer>
                <Button onClick={handleDownload}>
                  Download Video
                </Button>
              </Card.Footer>
            </Card>
          </motion.div>
        )}
      </div>
    </main>
  );
}
