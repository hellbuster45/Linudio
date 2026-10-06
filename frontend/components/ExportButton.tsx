'use client'
import { buttonVariants, Dropdown } from "@heroui/react";
import { downloadTextFile, segmentsToSrt, segmentsToTxt, type ExportSegment } from "@/lib/utils";

export function ExportButton({
    segments,
    filenameBase,
}: {
    segments: ExportSegment[],
    filenameBase: string,
}) {
    const handleExport = (format: string) => {
        if (format === "srt") {
            downloadTextFile(`${filenameBase}.srt`, segmentsToSrt(segments));
        } else if (format === "txt") {
            downloadTextFile(`${filenameBase}.txt`, segmentsToTxt(segments));
        }
    };

    return (
        <Dropdown>
            <Dropdown.Trigger className={buttonVariants({ variant: "outline" })}>
                Download
            </Dropdown.Trigger>
            <Dropdown.Popover>
                <Dropdown.Menu onAction={(key) => handleExport(key as string)}>
                    <Dropdown.Item id="srt" textValue="Download as .srt">
                        Download as .srt
                    </Dropdown.Item>
                    <Dropdown.Item id="txt" textValue="Download as .txt">
                        Download as .txt
                    </Dropdown.Item>
                </Dropdown.Menu>
            </Dropdown.Popover>
        </Dropdown>
    );
}
