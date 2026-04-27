'use client'
import { Button, Input, Label, Spinner } from "@heroui/react";
import { useState } from "react";


export function FetchVideo({ onVideoFetched }: { onVideoFetched: (data: any) => void }) {
    const [url, setUrl] = useState("");
    const [loading, setLoading] = useState(false);

    const handleFetch = async () => {
        setLoading(true);

        try {
            const response = await fetch("http://localhost:8000/videos/yt_video", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });

            const data = await response.json();
            onVideoFetched(data.metadata);
        } catch (error) {
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
        <div className="md:w-2xl lg:w-3xl p-4 flex flex-row gap-2 justify-between items-center">
            <Input
                type="text"
                name="yt_url"
                placeholder="Enter a valid Youtube URL!"
                value={url}
                onChange={handleInput}
                className={'w-full md:py-4 md:px-6'}
                variant="primary"
            />

            {
                loading ? (
                    <Button
                        isDisabled
                        className={'md:p-6'}
                    >
                        <Spinner color="current" />
                        Fetch Video
                    </Button>
                ) : (
                    <Button
                        isDisabled={!checkUrl(url)}
                        onClick={handleFetch}
                        className={'md:p-6'}
                    >
                        Fetch Video
                    </Button>
                )
            }
        </div>
    )
}
