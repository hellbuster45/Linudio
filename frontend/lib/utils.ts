import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Converts seconds into a formatted string (HH:MM:SS or MM:SS)
 * @param seconds - The total seconds from Whisper metadata
 * @param showHours - Force hours to show even if they are 0
 */
export const formatWhisperTimestamp = (seconds: number, showHours: boolean = false): string => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    const mmss = `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;

    if (hrs > 0 || showHours) {
        return `${hrs.toString().padStart(2, "0")}:${mmss}`;
    }

    return mmss;
};