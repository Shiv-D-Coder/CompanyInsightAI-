from gtts import gTTS

test = "गूगल के संस्थापक लैरी पेज और सर्गे ब्रिन हैं। उन्होंने ४ सितंबर १९९८ को गूगल की स्थापना की थी।"

speach = gTTS(text = test, lang = 'hi', slow = False)
speach.save('Adiou.mp3')