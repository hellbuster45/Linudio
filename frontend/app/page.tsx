// 'use client'
// import { FetchVideo } from "@/components/FetchVideo";
// import { TranscriptPane } from "@/components/TranscriptPane";
// import { TranslatedPane } from "@/components/TranslatedPane";
// import { VideoCard } from "@/components/VideoCard";
// import { Separator } from "@heroui/react";
// import { useState } from "react";

// export default function Home() {
//   const [video_id, setVideoID] = useState<any>(null);
//   const [metadata, setMetadata] = useState<any>(null);
//   const [transcript, setTranscript] = useState<any>(null);
//   const [translated, setTranslated] = useState<any>(null);

//   const handleData = (data: any) => {
//     setMetadata(data);
//     setVideoID(data.video_id);
//   }

//   return (
//     <main className="max-w-[95%] mx-auto w-full flex flex-1 flex-col p-4 gap-4 border-white border items-center">
//       <div className="text-center">
//         <h3>Linudio</h3>
//         <p>Multi-Agent Youtube Video Translation and Dubbing Simplified!</p>
//       </div>

//       <FetchVideo onVideoFetched={(data) => handleData(data)} />

//       {/* <TranscriptPane
//         video_id={video_id}
//         transcript={transcript}
//         onTranslatedFetched={(data) => setTranslated(data)}
//       /> */}

//       {metadata && (
//         <VideoCard
//           metadata={metadata}
//           onTranscriptFetched={(data) => setTranscript(data)}
//         />
//       )}


//       <div className="flex flex-row ">
//         {
//           transcript && (
//             <TranscriptPane
//               video_id={video_id}
//               transcript={transcript}
//               onTranslatedFetched={(data) => setTranslated(data)}
//             />
//           )
//         }
        
//         {
//           translated && (
//             <>
//               <Separator orientation="vertical"/>
//               <TranslatedPane
//                 video_id={video_id}
//                 translated={translated}
//                 onTranslatedFetched={(data) => setTranslated(data)}
//               />
//             </>
//           )
//         }
//       </div>
//     </main>
//   );
// }

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
  const [translated, setTranslated] = useState<any>(null);

  const handleData = (data: any) => {
    setMetadata(data);
    setVideoID(data.video_id);
  };

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
                onTranscriptFetched={(data) => setTranscript(data)}
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
                    onTranslatedFetched={(data) => setTranslated(data)}
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
                  onTranslatedFetched={(data) => setTranslated(data)}
                />
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}