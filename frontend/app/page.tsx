'use client'
import { FetchVideo } from "@/components/FetchVideo";
import { TranscriptPane } from "@/components/TranscriptPane";
import { TranslatedPane } from "@/components/TranslatedPane";
import { VideoCard } from "@/components/VideoCard";
import { Button, Separator } from "@heroui/react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function Home() {
  const [started, setStarted] = useState(false);
  const [video_id, setVideoID] = useState<string | null>(null);

  const [metadata, setMetadata] = useState<any>(null);

  const [transcript, setTranscript] = useState<any>(null);
  const [originalTranscript, setOriginalTranscript] = useState<any>(null);

  const [translated, setTranslated] = useState<any>(null);
  const [originalTranslated, setOriginalTranslated] = useState<any>(null);

  const handleData = (data: any) => {
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

  return (
    <main className="min-h-screen bg-background font-sans selection:bg-accent/30">
      <div className="max-w-[95%] mx-auto px-4 py-12 flex flex-col items-center gap-12 border border-white">

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
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              whileHover={{ scale: 1.05 }}
            >
              <Button
                size="lg"
                variant="primary"
                className="mt-6 font-bold px-12 rounded-full"
                onClick={() => setStarted(true)}
              >
                Get Started
              </Button>
            </motion.div>
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
                  onTranslatedFetched={(data) => setTranslated(data)}
                  onReset={resetTranslated}
                  onUpdate={(idx, text) => updatedSegment('translated', idx, text)}
                />
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}