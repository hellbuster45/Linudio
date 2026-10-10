'use client'
import { Button, Input, Spinner, toast } from "@heroui/react";
import { useState } from "react";
import { apiErrorMessage, apiUrl } from "@/lib/api";
import type { VideoMetadata } from "@/lib/types";

export function FetchVideo({ onVideoFetched }: { onVideoFetched: (data: VideoMetadata) => void }) {
    const [url, setUrl] = useState("");
    const [loading, setLoading] = useState(false);

    const handleFetch = async () => {
        setLoading(true);

        try {
            const response = await fetch(apiUrl("/videos/yt_video"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });

            const data = await response.json();
            const message = apiErrorMessage(data);
            if (message || !data.metadata) {
                toast.danger(message ?? "Couldn't fetch that video");
                return;
            }

            onVideoFetched(data.metadata);
        } catch (error) {
            console.error("FETCH VIDEO FAILED:", error);
            toast.danger("Could not reach the Linudio backend. Is it running?");
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
