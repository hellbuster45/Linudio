'use client'
import { Button, Chip, Label, ListBox, ListBoxItemIndicator, Select, Spinner } from "@heroui/react";
import { TranscriptField } from "./TranscriptField";
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

export function TranscriptPane ({video_id, transcript, onTranslatedFetched} : {video_id: string, transcript: Transcript, onTranslatedFetched: (data: any) => void}) {
    const [loading, setLoading] = useState<any>(null);
    const [language, setLanguage] = useState<any>(null);
    const [changes, setChanges] = useState<any>(null);

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

    return (
        <div className="w-auto lg:w-lg">
            <div className="flex flex-col md:flex-row gap-2 mx-4 mt-4">
                <h2 className="text-md">
                    Original Transcript
                </h2>

                <div className="flex flex-row gap-2">
                    <Chip size="sm" color="accent" variant="secondary" className="rounded-3xl"> { NLLB_CODE_TO_NAME[transcript?.src_lang] } </Chip>
                    <Chip size="sm" color="accent" variant="secondary" className="rounded-3xl">Accuracy: { formattedAccuracy }% </Chip>
                </div>
            </div>
            {
                transcript?.segments?.map((segment, index) => (
                    <TranscriptField
                        key={index}
                        segments={segment}
                        onValueChanged={(data) => setChanges(data)}
                    />
                ))
            }
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
                
                { language ? (
                    !loading ? (
                        <Button onClick={() => handleFetch()}> Start Trranslation </Button>
                    ) : (
                        <Button isDisabled>
                            <Spinner color="current" />
                            Processing..
                        </Button>
                    )
                ) : (
                    <Button isDisabled>Start Translation</Button>
                )}
            </div>
        </div>
    )
}
