import { AspectRatio } from "./ui/aspect-ratio";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardFooter, CardTitle } from "./ui/card";
import { useState } from "react";
import { Spinner } from "./ui/spinner";
import Image from "next/image";

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
                    <AspectRatio ratio={16 / 9} className="rounded-2xl">
                        <Image src={ metadata?.thumbnail } alt="thumbnail" />
                    </AspectRatio>
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
                        <Button disabled>
                            <Spinner data-icon="inline-start" />
                            Processing..
                        </Button>
                    )
                }
            </CardFooter>
        </Card>
    )
}