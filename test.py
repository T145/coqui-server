import requests


text = """Hey there Andy! 🌎

The average distance between the Earth and Jupiter varies as both planets follow elliptical orbits around the Sun. The closest point, known as perihelion, occurs when the two planets are about 465 million miles (746 million kilometers) apart, while the farthest point, aphelion, is around 928 million miles (1.5 billion kilometers) away.

On average, though, the Earth is roughly 483.8 million miles (780.3 million kilometers) from Jupiter at its closest and about 483.9 million miles (782.4 million kilometers) away at its farthest.

One more thing to note is that this distance is an estimate since both planets have complex orbital patterns, but 483.8-483.9 million miles seems a pretty reliable average range 👍"""

response = requests.post(url="http://localhost:8000/tts", data={
    "text": text,
    "speaker_id": 335
})

with open("myfile.wav", mode="bw") as f:
    f.write(response.content)
