import { useState } from "react";
import Image from "next/image";
import { Button, Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle, Spinner } from "@heroui/react";

export function VideoCard({ metadata, onStartSTT }: { metadata: any, onStartSTT: () => void }) {
    const [loading, setLoading] = useState(false);

    return (
        <Card className="border-2 border-black">
            <CardHeader>
                <CardTitle>
                    Fetched Video Successfully !
                </CardTitle>
                <CardDescription>Desc</CardDescription>
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
                        <Button onClick={() => setLoading(true)}> Start Transcription </Button>
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