import requests

# Send the POST request
response = requests.post(url="http://localhost:8000/tts", data={
    "text": "In the heart of an ancient forest, where the trees whispered secrets of the past, there lived a peculiar rabbit named Luna. Unlike any other rabbit, Luna was born with wings, a rare gift that she had yet to understand the purpose of. Each night, under the glow of the moon, she would gaze up at the stars, wondering if there was more to her existence. One evening, as the forest bathed in silvery moonlight, Luna discovered a clearing she had never seen before. In the center stood a crystal-clear pond that mirrored the night sky. Drawn to its beauty, Luna approached the pond and, for the first time, unfolded her wings. As she touched the water's surface with her paw, the pond rippled, and the reflection of the stars began to swirl.",
    "speaker_id": 335
})

with open("myfile.wav", mode="bw") as f:
    f.write(response.content)
