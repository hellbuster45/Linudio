import { useState } from "react";
import Image from "next/image";
import { Button, Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle, Separator, Spinner } from "@heroui/react";

export function VideoCard({ metadata, onTranscriptFetched }: { metadata: any, onTranscriptFetched: (data: any) => void }) {
    const [loading, setLoading] = useState(false);

    const handleFetch = async () => {
        setLoading(true);
        const video_id = metadata.video_id;
        try {
            const response = await fetch("http://localhost:8000/synthesize/", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ video_id })
            });

            const data = await response.json();
            onTranscriptFetched(data);
        } catch(error) {
            console.log("TRANSCRIPTION FETCH ERROR");
            console.error(error);
        } finally {
            setLoading(false);
        }
    }

    return (
        <Card className="border-2 border-black">
            <CardHeader>
                <CardTitle>
                    { metadata?.title }
                </CardTitle>
                <CardDescription className="flex flex-row gap-2">
                    { metadata?.upload_date }
                    <Separator orientation="vertical"/>
                    { metadata?.resolution }
                </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-row gap-2">
                <div className="flex-1/3">
                    <Image
                        src={ metadata?.thumbnail }
                        className="rounded-lg"
                        alt="thumbnail"
                        width={"400"}
                        height={"300"}/>
                </div>
                <div className="border-black border flex-2/3">
                    <h3>metadata</h3>
                    <p>Resolution: 1920 * 1080</p>
                </div>
            </CardContent>
            <CardFooter>
                {
                    !loading ? (
                        <Button onClick={() => handleFetch()}> Start Transcription </Button>
                    ) : (
                        <Button isDisabled>
                            <Spinner data-icon="inline-start" />
                            Processing..
                        </Button>
                    )
                }
            </CardFooter>
        </Card>
    )
}