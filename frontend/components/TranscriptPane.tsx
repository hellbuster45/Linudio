'use client'
import { Button, Chip, Label, ListBox, ListBoxItemIndicator, ScrollShadow, Select, Spinner } from "@heroui/react";
import { TranscriptField } from "./TranscriptField";
import { ExportButton } from "./ExportButton";
import { NLLB_CODE_TO_NAME } from "@/lib/constants";
import { useState } from "react";

export interface Segments {
    id: number,
    start_time: number,
    end_time: number,
    text: string
}

interface Transcript {
    src_lang: string,
    language_probability: number,
    segments: Segments[]    
}

export function TranscriptPane ({
    video_id,
    transcript,
    onReset,
    onUpdate,
    onTranslatedFetched
} : {
    video_id: string,
    transcript: Transcript,
    onReset: () => void,
    onUpdate: (index: number, newText: string) => void,
    onTranslatedFetched: (data: any) => void
}) {
    const [loading, setLoading] = useState<any>(null);
    const [language, setLanguage] = useState<any>(null);
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


    const rawAccuracy = transcript?.language_probability || 0;
    const formattedAccuracy = (rawAccuracy * 100).toFixed(1);

    const handleFetch = async() => {
        setLoading(true);

        try {
            const payload = {
                video_id: video_id,
                tgt_lang: language,
                segments: transcript?.segments
            };

            console.log("PAYLOAD: ", payload);

            const response = await fetch("http://localhost:8000/translate", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify( payload )
            });

            const data = await response.json();
            console.log("TRANSLATED FETCHED", data);
            onTranslatedFetched(data);
        } catch(error) {
            console.log("TRANSLATE FETCH ERROR");
            console.error(error);
        } finally {
            setLoading(false);
        }
    }

    // console.log(changes)
    return (
        <div className="w-full">
            <div className="flex flex-col md:flex-row gap-2 mx-4 mb-4 justify-between">
                <h2 className="text-md">
                    Original Transcript
                </h2>

                <div className="flex flex-row gap-2">
                    <Chip size="sm" color="accent" variant="secondary" className="rounded-3xl"> { NLLB_CODE_TO_NAME[transcript?.src_lang] } </Chip>
                    <Chip size="sm" color="accent" variant="secondary" className="rounded-3xl">Accuracy: { formattedAccuracy }% </Chip>
                </div>
            </div>
            <ScrollShadow hideScrollBar className="max-h-120">
                <div className="flex flex-col gap-4 mb-4">
                    {
                        transcript?.segments?.map((segment, index) => (
                            <TranscriptField
                                key={index}
                                segments={segment}
                                onValueChanged={(newText: string) => handleUpdate(index, newText)}
                            />
                        ))
                    }
                </div>
            </ScrollShadow>
            <div>
                <Select placeholder="Select One" onChange={(value) => setLanguage(value)}>
                    <Label>Choose Target Language: </Label>
                    <Select.Trigger>
                        <Select.Value />
                        <Select.Indicator />
                    </Select.Trigger>
                    <Select.Popover>
                        <ListBox>
                            {
                                Object.entries(NLLB_CODE_TO_NAME).map(([code, name]) => (
                                    <ListBox.Item key={ code } id={ code } textValue={ name }>
                                        { name }
                                        <ListBoxItemIndicator />
                                    </ListBox.Item>
                                ))
                            }
                        </ListBox>
                    </Select.Popover>
                </Select>
                
                <div className=" w-full md:w-auto flex flex-col md:flex-row gap-2 mt-2">
                    { language ? (
                        !loading ? (
                            <Button onClick={() => handleFetch()}> Start Translation </Button>
                        ) : (
                            <Button isDisabled>
                                <Spinner color="current" />
                                Processing..
                            </Button>
                        )
                    ) : (
                        <Button isDisabled>Start Translation</Button>
                    )}
                    
                    { hasLocalChanges && (
                        <Button
                            variant="outline"
                            onClick={handleReset}
                        >
                            Reset Changes
                        </Button>
                    )}

                    { transcript?.segments && (
                        <ExportButton
                            segments={transcript.segments}
                            filenameBase={`${video_id}_transcript`}
                        />
                    )}
                </div>
            </div>
        </div>
    )
}
