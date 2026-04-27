## http://127.0.0.1:8000/videos/yt_video

#### Request POST
```
{
    "url": "https://www.youtube.com/watch?v=v4t0E3S1N1k"
}
```

#### Response
```
{
    "message": "Download Started..",
    "metadata": {
        "video_id": "v4t0E3S1N1k",
        "title": "English in a Minute: Grow Like a Weed",
        "thumbnail": "https://i.ytimg.com/vi/v4t0E3S1N1k/maxresdefault.jpg",
        "duration": 60,
        "upload_date": "20230619",
        "resolution": "1920x1080",
        "fps": 30
    }
}
```

## http://127.0.0.1:8000/synthesize

#### Request POST
```
{
    "video_id": "v4t0E3S1N1k"
}
```

#### Response
```
{
    "src_lang": "eng_Latn",
    "language_probablity": 0.9998449087142944,
    "segments": [
        {
            "id": 1,
            "start_time": 0.0,
            "end_time": 6.0,
            "text": " Welcome to English in a Minute."
        }, ...
    ]
}
```

## http://127.0.0.1:8000/translate

#### Request POST
```
{
    "video_id": "v4t0E3S1N1k",
    "tgt_lang": "jpn_Jpan",
    "text": [
        {
            "id": 1,
            "start_time": 0.0,
            "end_time": 6.0,
            "text": " Welcome to English in a Minute."
        },
    ]
}
```

#### Response
```
{
    "message": "success",
    "translated_text": [
        {
            "id": 1,
            "start_time": 0.0,
            "end_time": 6.0,
            "text": "英語にようこそ!"
        }, ...
    ]
}
```