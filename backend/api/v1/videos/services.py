from yt_dlp import YoutubeDL


def yt_downloader():
    pass

def get_metadata(url: str):
    options = {"quiet": True, "no-warnings": True}
    
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(download=False)