'use client'
import { Button, Chip, Label, ListBox, ListBoxItemIndicator, Select } from "@heroui/react";
import { TranscriptField } from "./TranscriptField";
import { NAME_TO_NLLB_CODE, NLLB_CODE_TO_NAME, WHISPER_ISO_TO_NAME } from "@/lib/constants";
import { useState } from "react";

export interface Segments {
    id: number,
    start_time: number,
    end_time: number,
    text: string
}

interface Translated {
    message: string,
    tgt_lang: string,
    translated_segments: Segments[]    
}

export function TranslatedPane ({video_id, translated, onTranslatedFetched} : {video_id: string, translated: Translated, onTranslatedFetched: (data: any) => void}) {
    const [loading, setLoading] = useState<any>(null);
    const [language, setLanguage] = useState<any>(null);
    const [changes, setChanges] = useState<any>(null);


    const handleFetch = async() => {
        setLoading(true);

        // try {
        //     console.log("IMPLEMENT TTS QUICKLYYY NIGGAAA!");
        // } catch(error) {
        //     console.log("TRANSLATE FETCH ERROR");
        //     console.error(error);
        // } finally {
        //     setLoading(false);
        // }
    }
    // console.log("CHANGES: ", changes);

    return (
        <div className="w-auto lg:w-lg">
            <div className="flex flex-col md:flex-row gap-2 mx-4 mt-4">
                <h2 className="text-md">
                    Translated Transcript
                </h2>

                <div className="flex flex-row gap-2">
                    <Chip size="sm" color="accent" variant="secondary" className="rounded-3xl"> { NLLB_CODE_TO_NAME[translated?.tgt_lang] } </Chip>
                </div>
            </div>
            {
                translated?.translated_segments?.map((segment, index) => (
                    <TranscriptField
                        key={index}
                        segments={segment}
                        onValueChanged={(data) => setChanges(data)}
                    />
                ))
            }
        </div>
    )
}
