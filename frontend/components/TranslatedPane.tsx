'use client'
import { Button, Chip, ScrollShadow, Spinner } from "@heroui/react";
import { TranscriptField } from "./TranscriptField";
import { NLLB_CODE_TO_NAME } from "@/lib/constants";
import { useState } from "react";

export interface Segments {
    id: number,
    start_time: number,
    end_time: number,
    text: string
}

interface Translated {
    status: string,
    tgt_lang: string,
    translated_segments: Segments[]    
}

export function TranslatedPane ({
    video_id,
    translated,
    onReset,
    onUpdate,
    onDubStarted
} : {
    video_id: string,
    translated: Translated,
    onReset: () => void,
    onUpdate: (index: number, newText: string) => void,
    onDubStarted: (data: any) => void
}) {
    const [loading, setLoading] = useState<any>(null);
    const [changes, setChanges] = useState<Set<number>>(new Set());

    const handleUpdate = (index: number, newText: string) => {
        onUpdate(index, newText);
        setChanges(prev => new Set(prev).add(index));
    }
    
    const handleReset = () => {
        onReset();
        setChanges(new Set());
    }
    const hasLocalChanges = changes.size > 0;


    const startDub = async() => {
        setLoading(true);
        const payload = {
            video_id: video_id,
            lang_code: translated?.tgt_lang,
            segments: translated?.translated_segments
        }

        try {
            const response = await fetch("http://localhost:8000/text_to_speech/dub", {
                method: "GET",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            onDubStarted(data);
        } catch(error) {
            console.log("TRANSLATE FETCH ERROR");
            console.error(error);
        } finally {
            setLoading(false);
        }
    }
    // console.log("CHANGES: ", changes);

    return (
        <div className="w-full">
            <div className="flex flex-col md:flex-row gap-2 mx-4">
                <h2 className="text-md">
                    Translated Transcript
                </h2>

                <div className="flex flex-row gap-2">
                    <Chip size="sm" color="accent" variant="secondary" className="rounded-3xl"> { NLLB_CODE_TO_NAME[translated?.tgt_lang] } </Chip>
                </div>
            </div>
            <ScrollShadow hideScrollBar className="max-h-120">
                {
                    translated?.translated_segments?.map((segment, index) => (
                        <TranscriptField
                            key={index}
                            segments={segment}
                            onValueChanged={(newText: string) => handleUpdate(index, newText)}
                        />
                    ))
                }
            </ScrollShadow>

            <div className=" w-full md:w-auto flex flex-col md:flex-row gap-2 mt-2">
                {
                    !loading ? (
                        <Button
                            onClick={startDub}
                        >
                            Start Dubbing
                        </Button>
                    ) : (
                        <Button>
                            <Spinner color="current" />
                            Processing..
                        </Button>
                    )
                }
                { hasLocalChanges && (
                    <Button
                        variant="outline"
                        onClick={handleReset}
                    >
                        Reset Changes
                    </Button>
                )}
            </div>
        </div>
    )
}
