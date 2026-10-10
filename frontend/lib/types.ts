export interface Segment {
    id: number;
    start_time: number;
    end_time: number;
    text: string;
}

export interface VideoMetadata {
    video_id: string;
    title: string;
    thumbnail: string;
    duration: number;
    upload_date: string;
    resolution: string;
    fps: number;
}

export interface Transcript {
    src_lang: string;
    language_probability: number;
    segments: Segment[];
}

export interface Translated {
    status: string;
    tgt_lang: string;
    translated_segments: Segment[];
}

export interface PreflightCheck {
    name: string;
    ok: boolean;
    optional: boolean;
    hint: string;
}

export interface Preflight {
    ok: boolean;
    checks: PreflightCheck[];
}
