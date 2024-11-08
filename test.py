import requests

text = """The average distance between the Earth and Jupiter varies as both planets follow elliptical orbits around the Sun. The closest point, known as perihelion, occurs when the two planets are about 465 million miles (746 million kilometers) apart, while the farthest point, aphelion, is around 928 million miles (1.5 billion kilometers) away."""
compress = True

response = requests.post(url="http://localhost:8000/tts", data={
    "text": text,
    "speaker_id": 335,
    "compress": compress
})

with open("myfile.{}".format("flac" if compress else "wav"), mode="bw") as f:
    f.write(response.content)
