'use client'
import { useState } from "react";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Spinner } from "./ui/spinner";


export function FetchVideo({ onVideoFetched }: { onVideoFetched: (data: any) => void }) {
    const [url, setUrl] = useState("");
    const [loading, setLoading] = useState(false);

    const handleFetch = async () => {
        setLoading(true);

        try {
            const response = await fetch("http://localhost:8000/videos/yt_video", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ url })
            });

            const data = await response.json();
            onVideoFetched(data.metadata);
        } catch(error) {
            console.log("FETCH VIDEO FAILED!");
            console.error(error);
        } finally {
            setLoading(false);
        }
    }

    const checkUrl = (url: string) => {
        const regex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$/;
        return regex.test(url);
    }

    const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        setUrl(e.target.value);
    }
    return (
        <div className="flex flex-row gap-2 p-2">
            <Input type="text" placeholder="http://youtube.com/watch?v=6dVI3gOEGXo" value={url} onChange={handleInput} />
                {loading ? (
                    <Button disabled>
                        <Spinner data-icon="inline-start" />
                        Fetch Video
                    </Button>
                ) : (
                    <Button disabled={!checkUrl(url)} onClick={handleFetch}>
                        Fetch Video
                    </Button>
                )}
        </div>
    )
}