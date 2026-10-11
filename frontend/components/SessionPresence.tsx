'use client'
import { useEffect } from "react";
import { API_BASE_URL, apiUrl } from "@/lib/api";

// When Linudio is started with Linudio.bat, the backend wants to know when the last browser tab
// is closed so it can stop the servers. Holding a WebSocket open is how it knows: the browser
// closes it when the tab goes away. A normal backend reports exit_on_close: false and this does nothing.
export function SessionPresence() {
    useEffect(() => {
        let socket: WebSocket | null = null;
        let retry: ReturnType<typeof setTimeout> | undefined;
        let stopped = false;

        const connect = () => {
            socket = new WebSocket(`${API_BASE_URL.replace(/^http/, "ws")}/session/ws`);
            // Reconnect after a drop (e.g. the backend restarted) until the page is unmounted.
            socket.onclose = () => {
                if (!stopped) retry = setTimeout(connect, 2000);
            };
        };

        fetch(apiUrl("/session"))
            .then((response) => response.json())
            .then((data: { exit_on_close?: boolean }) => {
                if (data.exit_on_close && !stopped) connect();
            })
            .catch(() => {});

        return () => {
            stopped = true;
            clearTimeout(retry);
            socket?.close();
        };
    }, []);

    return null;
}
