import { useState } from "react";
import Image from "next/image";
import { Button, Card, CardFooter, CardHeader, CardTitle, Separator, Spinner, toast } from "@heroui/react";
import { apiErrorMessage, apiUrl } from "@/lib/api";
import type { Transcript, VideoMetadata } from "@/lib/types";

export function VideoCard({ metadata, onTranscriptFetched }: { metadata: VideoMetadata, onTranscriptFetched: (data: Transcript) => void }) {
    const [loading, setLoading] = useState(false);

    // Helper to format "20181025" -> "Oct 25, 2018"
    const formatUploadDate = (dateStr: string) => {
        if (!dateStr || dateStr.length !== 8) return dateStr;

        const year = parseInt(dateStr.substring(0, 4));
        const month = parseInt(dateStr.substring(4, 6)) - 1; // JS months are 0-indexed
        const day = parseInt(dateStr.substring(6, 8));

        const date = new Date(year, month, day);

        return new Intl.DateTimeFormat("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
        }).format(date);
    };

    const handleFetch = async () => {
        setLoading(true);
        const video_id = metadata.video_id;
        try {
            const response = await fetch(apiUrl("/synthesize/"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ video_id })
            });

            const data = await response.json();
            const message = apiErrorMessage(data);
            if (message || !data.segments) {
                toast.danger(message ?? "Transcription failed");
                return;
            }

            onTranscriptFetched(data);
        } catch (error) {
            console.error("TRANSCRIPTION FETCH ERROR:", error);
            toast.danger("Could not reach the Linudio backend. Is it running?");
        } finally {
            setLoading(false);
        }
    }

    return (
        <Card className="md:w-2xl lg:w-3xl">
            <CardHeader>
                <CardTitle className="flex flex-col gap-2">
                    <Image
                        src={metadata?.thumbnail}
                        className="rounded-xl w-full"
                        alt="thumbnail"
                        width={400} // Removed quotes, Next.js Image expects numbers
                        height={300}
                    />
                    <p className="md:text-xl font-semibold">
                        {metadata?.title}
                    </p>
                </CardTitle>
            </CardHeader>

            {/* Metadata bar with better alignment */}
            <div className="flex flex-row items-center gap-3 text-muted">
                <span>Upload Date: {formatUploadDate(metadata?.upload_date)}</span>
                <Separator orientation="vertical" className="h-4" />
                <span>Resolution: {metadata?.resolution}</span>
            </div>

            <CardFooter className="flex flex-row justify-center pb-6">
                {!loading ? (
                    <Button onClick={handleFetch}> Start Transcription </Button>
                ) : (
                    <Button isDisabled>
                        <Spinner color="current" size="sm" />
                        Processing..
                    </Button>
                )}
            </CardFooter>
        </Card>
    );
}