from yt_dlp import YoutubeDL


def yt_downloader(url: str):
    pass

def get_metadata(url: str):
    options = {
        "quiet": True,
        "js-runtime": {"node": {}}
    }
    
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url=url, download=False)
    
    print(info.keys())
    
    return {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "upload_date": info.get("upload_date"),
        "resolution": info.get("resolution"),
        "fps": info.get("fps")
    }