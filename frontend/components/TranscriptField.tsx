import { Card, Chip, TextArea } from "@heroui/react";
import { Segments } from "./TranscriptPane";
import { formatWhisperTimestamp } from "@/lib/utils";

export function TranscriptField ({ segments, onValueChanged }: { segments: Segments, onValueChanged: (newText: string) => void }) {
    return (
        <Card className="w-auto">
            <Card.Header>
                <Card.Description className="flex flex-row gap-2">
                    <Chip className="text-muted">{ formatWhisperTimestamp(segments?.start_time) }</Chip>
                    -
                    <Chip className="text-muted">{ formatWhisperTimestamp(segments?.end_time) }</Chip>
                </Card.Description>
            </Card.Header>
            <Card.Content>
                <TextArea
                    value={ segments?.text }
                    className={"border border-border/50 w-full"}
                    variant="secondary"
                    onChange={(event) => onValueChanged(event.target.value)}
                />
            </Card.Content>
        </Card>
    )
}