import { Chip } from "@heroui/react";
import { TranscriptField } from "./TranscriptField";

export function TranscriptPane () {
    return (
        <div>
            <div className="flex flex-col md:flex-row gap-2 mx-4 mt-4">
                <h2 className="text-md">
                    Original Transcript
                </h2>

                <div className="flex flex-row gap-2">
                    <Chip size="sm" color="accent" variant="secondary" className="rounded-3xl">English</Chip>
                    <Chip size="sm" color="accent" variant="secondary" className="rounded-3xl">Accuracy: 99%</Chip>
                </div>
            </div>
            <TranscriptField />
        </div>
    )
}