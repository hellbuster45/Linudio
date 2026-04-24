'use client'
import { FetchVideo } from "@/components/FetchVideo";
import { TranscriptPane } from "@/components/TranscriptPane";
import { VideoCard } from "@/components/VideoCard";
import { useState } from "react";

export default function Home() {
  const [metadata, setMetadata] = useState<any>(null);


  return (
    <main className="max-w-[95%] mx-auto w-full flex flex-1 flex-col p-4 border-black border items-center">
      <div className="">
        <h3>Linudio</h3>
        <p>Translator</p>
      </div>
      <FetchVideo onVideoFetched={(data) => setMetadata(data)} />

      <TranscriptPane />

      {metadata && (
        <VideoCard
          metadata={metadata}
          onStartSTT={() => { }}
        />
      )}
    </main>
  );
}
