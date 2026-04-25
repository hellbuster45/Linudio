'use client'
import { FetchVideo } from "@/components/FetchVideo";
import { TranscriptPane } from "@/components/TranscriptPane";
import { VideoCard } from "@/components/VideoCard";
import { useState } from "react";

export default function Home() {
  const [video_id, setVideoID] = useState<any>(null);
  const [metadata, setMetadata] = useState<any>(null);
  const [transcript, setTranscript] = useState<any>(null);

  const handleData = (data: any) => {
    setMetadata(data);
    setVideoID(data.video_id);
  }

  return (
    <main className="max-w-[95%] mx-auto w-full flex flex-1 flex-col p-4 border-black border items-center">
      <div className="">
        <h3>Linudio</h3>
        <p>Translator</p>
      </div>
      <FetchVideo onVideoFetched={(data) => handleData(data)} />

      <TranscriptPane />

      {metadata && (
        <VideoCard
          metadata={metadata}
          onTranscriptFetched={(data) => setTranscript(data)}
        />
      )}
    </main>
  );
}
