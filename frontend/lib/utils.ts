import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export interface ExportSegment {
  id: number
  start_time: number
  end_time: number
  text: string
}

/** Formats seconds as SRT's required HH:MM:SS,mmm timestamp. */
const formatSrtTimestamp = (seconds: number): string => {
  // Work in whole milliseconds so rounding can never produce a ",1000" overflow.
  const totalMs = Math.round(seconds * 1000)
  const hrs = Math.floor(totalMs / 3_600_000)
  const mins = Math.floor((totalMs % 3_600_000) / 60_000)
  const secs = Math.floor((totalMs % 60_000) / 1000)
  const ms = totalMs % 1000

  return `${hrs.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")},${ms.toString().padStart(3, "0")}`
}

export const segmentsToSrt = (segments: ExportSegment[]): string => {
  return segments
    .map((segment, index) => {
      const start = formatSrtTimestamp(segment.start_time)
      const end = formatSrtTimestamp(segment.end_time)
      return `${index + 1}\n${start} --> ${end}\n${segment.text.trim()}\n`
    })
    .join("\n")
}

export const segmentsToTxt = (segments: ExportSegment[]): string => {
  return segments.map((segment) => segment.text.trim()).join("\n")
}

/** Triggers a browser download of the given text content as a file. */
export const downloadTextFile = (filename: string, content: string) => {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" })
  const url = URL.createObjectURL(blob)

  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}

/** Downloads a file from a URL via a blob, so the browser saves it instead of navigating
 *  (the `download` attribute is ignored for cross-origin URLs such as the API server). */
export const downloadFromUrl = async (url: string, filename: string) => {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Download failed (${response.status})`)

  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)

  const link = document.createElement("a")
  link.href = objectUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(objectUrl)
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