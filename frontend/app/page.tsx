'use client'
import { DeviceSelector } from "@/components/DeviceSelector";
import { ModelSettings } from "@/components/ModelSettings";
import { SettingsStatusProvider, useSettingsStatus } from "@/context/SettingsStatusContext";
import { FetchVideo } from "@/components/FetchVideo";
import { TranscriptPane } from "@/components/TranscriptPane";
import { TranslatedPane } from "@/components/TranslatedPane";
import { VideoCard } from "@/components/VideoCard";
import { Button, Card, Separator, Spinner, toast, Toast } from "@heroui/react";
import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

function GetStartedButton({ onClick }: { onClick: () => void }) {
  const { isBusy } = useSettingsStatus();

  return (
    <motion.div
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
  );
}

export default function Home() {
  const [started, setStarted] = useState(false);
  const [video_id, setVideoID] = useState<string | null>(null);

  const [metadata, setMetadata] = useState<any>(null);

  const [transcript, setTranscript] = useState<any>(null);
  const [originalTranscript, setOriginalTranscript] = useState<any>(null);

  const [translated, setTranslated] = useState<any>(null);
  const [originalTranslated, setOriginalTranslated] = useState<any>(null);

  const [dubStarted, setDubStarted] = useState<any>(false);
  const [dubStatus, setDubStatus] = useState<string | null>(null);
  const [finalVideoUrl, setFinalVideoUrl] = useState<string | null>(null);

  const dubStatusRef = useRef<string | null>(null);
  const setDubStatusRef = (s: string | null) => {
    dubStatusRef.current = s;
    setDubStatus(s);
  };

  const handleData = (data: any) => {
    toast.success("Video Fetched !");
    setMetadata(data);
    setVideoID(data.video_id);
  };

  const saveTranscript = (data: any) => {
    // create a new reference in memory, without it,
    // both trans and og_trans point to same reference,
    // and updating one will affect the other too, defeating the whole purpose
    setOriginalTranscript(JSON.parse(JSON.stringify(data)));

    setTranscript(data);
  }

  const saveTranslated = (data: any) => {
    setOriginalTranslated(JSON.parse(JSON.stringify(data)));
    setTranslated(data);
  }

  const resetTranscript = () => {
    if (originalTranscript) {
      setTranscript(originalTranscript);
      console.log(transcript);
    }
  }

  const resetTranslated = () => {
    if (originalTranslated) {
      setTranslated(originalTranslated);
    }
  }

  const updatedSegment = (type: "original" | "translated", index: number, newText: string) => {
    if (type === "original" && transcript) {
      setTranscript((prev: any) => {
        if (prev.segments[index].text === newText) return prev;
        // 1. Create a new array reference for segments
        const newSegments = [...prev.segments];

        // 2. Create a new object reference for the specific segment being edited
        newSegments[index] = { ...newSegments[index], text: newText };

        // 3. Return a brand new object for the transcript
        return { ...prev, segments: newSegments };
      });
    } else if (type === "translated" && translated) {
      setTranslated((prev: any) => {
        if (prev.translated_segments[index].text === newText) return prev;

        const newSegments = [...prev.translated_segments];
        newSegments[index] = { ...newSegments[index], text: newText };
        return { ...prev, translated_segments: newSegments };
      });
    }
  }

  const pollDubStatus = async (v_id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/text_to_speech/dub_status?video_id=${v_id}`);
      const data = await response.json();

      setDubStatusRef(data.status);
      console.log("DUB RESPONSE: ", data);
      console.log("CURRENT DUB STATUS", data.status);
      console.log("STATUS IN WEBSITE (ref): ", dubStatusRef.current);

      if(dubStatusRef.current === "success") {
        setFinalVideoUrl(data.video_path);
      }
    } catch (err) {
      console.error("Polling error", err);
      return true; // Stop on error
    }
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (dubStarted && dubStatusRef.current !== "success") {
      setDubStatusRef("Initializing...");
      
      interval = setInterval(async () => {
        const isDone = await pollDubStatus(video_id!);
        if (isDone) clearInterval(interval);
      }, 10000);
    }

    return () => clearInterval(interval);
  }, [dubStarted]);

  return (
    <main className="min-h-screen bg-background font-sans selection:bg-accent/30">
      <Toast.Provider placement="top" />
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

          {!started && (
            <SettingsStatusProvider>
              <div className="mt-6 flex flex-col items-center justify-center gap-3">
                <DeviceSelector />
                <ModelSettings />
                <GetStartedButton onClick={() => setStarted(true)} />
              </div>
            </SettingsStatusProvider>
          )}
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
                <p className="font-bold capitalize">{dubStatus.replace('_', ' ')}</p>
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
                  onDubStarted={(data) => setDubStarted(data)}
                  onReset={resetTranslated}
                  onUpdate={(idx, text) => updatedSegment('translated', idx, text)}
                />
              </motion.div>
            )}
          </div>
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
              <video controls className="w-full rounded-xl">
                <source src={finalVideoUrl} type="video/mp4" />
              </video>
              <Card.Footer>
                <Button>
                  Download Button
                </Button>
              </Card.Footer>
            </Card>
          </motion.div>
        )}
      </div>
    </main>
  );
}