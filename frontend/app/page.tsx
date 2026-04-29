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
    console.log("SAVED FOR SOME FUCKING REASON");

    // create a new reference in memory, without it,
    // both trans and og_trans point to same reference,
    // and updating one will affect the other too, defeating the whole purpose
    setOriginalTranscript(JSON.parse(JSON.stringify(data)));
    
    setTranscript(data);
  }

  const saveTranslated = (data: any) => {
    console.log("SAVED FOR SOME FUCKING REASON: TRANSLATED");
    setOriginalTranslated(JSON.parse(JSON.stringify(data)));
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
    if (transcript && type === "original") {
      const updated = {...transcript};
      console.log("SEGMENTS: ", updated)
      updated.segments[index].text = newText;
      setTranscript(updated);

      console.log("TRANSCRIPT:----------------------------", transcript);
      console.log("ORIGINAL TRANSCRIPT:-------------------", originalTranscript);
    } else {
      if (translated) {
        const updated = {...translated};
        updated.translated_segments[index].text = newText;
        setTranslated(updated);
      }
    }
  }

  return (
    <main className="min-h-screen bg-background font-sans selection:bg-accent/30">
      <div className="max-w-7xl mx-auto px-4 py-12 flex flex-col items-center gap-12">

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
              className="w-full max-w-2xl"
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

          <div className="flex flex-row justify-center gap-0 overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md">
            <AnimatePresence mode="wait">
              {transcript && (
                <motion.div
                  initial={{ opacity: 0, x: -50 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="p-6"
                >
                  <TranscriptPane
                    video_id={video_id!}
                    transcript={transcript}
                    hasChanges={JSON.stringify(transcript) !== JSON.stringify(originalTranscript)}
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
                className="p-6 border-l border-white/10 relative"
              >
                <div className="absolute inset-y-0 left-[0.5px] hidden lg:block">
                  <Separator orientation="vertical" />
                </div>
                <TranslatedPane
                  video_id={video_id!}
                  translated={translated}
                  hasChanges={JSON.stringify(translated) !== JSON.stringify(originalTranslated)}
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