import whisper
model = whisper.load_model('base', device='cpu')
print('Model loaded successfully')