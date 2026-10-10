import { Card, Chip, TextArea } from "@heroui/react";
import type { Segment } from "@/lib/types";
import { formatWhisperTimestamp } from "@/lib/utils";
import { JSX, memo, useCallback, useRef } from "react";

export const TranscriptField = memo(function TranscriptField({ segments, onValueChanged }: { segments: Segment, onValueChanged: (newText: string) => void }): JSX.Element {
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    const handleChange = useCallback((newText: string) => {
        // Clear previous timer
        if (timerRef.current) {
            clearTimeout(timerRef.current);
        }

        // Set new timer to update parent after of no typing
        timerRef.current = setTimeout(() => {
            onValueChanged(newText);
        }, 2);
    }, [onValueChanged]);

    return (
        <Card className="w-full">
            <Card.Header>
                <Card.Description className="flex flex-row gap-2">
                    <Chip className="text-muted">{formatWhisperTimestamp(segments?.start_time)}</Chip>
                    -
                    <Chip className="text-muted">{formatWhisperTimestamp(segments?.end_time)}</Chip>
                </Card.Description>
            </Card.Header>
            <Card.Content>
                <TextArea
                    value={segments?.text}
                    className={"border border-border/50 w-full"}
                    variant="secondary"
                    onChange={(event) => handleChange(event.target.value)}
                />
            </Card.Content>
        </Card>
    )
}, (prevProps, nextProps) => {
    return prevProps.segments.text === nextProps.segments.text &&
        prevProps.segments.id === nextProps.segments.id;
});