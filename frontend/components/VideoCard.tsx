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
        <Card className="md:w-2xl lg:3xl">
            <CardHeader>
                <CardTitle className="flex flex-col gap-2">
                    <Image
                        src={ metadata?.thumbnail }
                        className="rounded-xl w-full"
                        alt="thumbnail"
                        width={"400"}
                        height={"300"}
                    />
                    <p className="md:text-xl">
                        { metadata?.title }
                    </p>
                </CardTitle>
                <CardDescription className="flex flex-row gap-2">
                    { metadata?.resolution }
                    <Separator orientation="vertical"/>
                    { metadata?.upload_date }
                </CardDescription>
            </CardHeader>
            <CardFooter className="flex flex-row justify-center">
                {
                    !loading ? (
                        <Button onClick={() => handleFetch()}> Start Transcription </Button>
                    ) : (
                        <Button isDisabled>
                            <Spinner color="current" />
                            Processing..
                        </Button>
                    )
                }
            </CardFooter>
        </Card>
    )
}