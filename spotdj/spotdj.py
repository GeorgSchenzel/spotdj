from spotdl import Spotdl

spotdl = Spotdl(client_id="5f573c9620494bae87890c0f08a60293", client_secret="212476d9b0f3472eaa762d90b19b0ba8")

songs = spotdl.search(['Hot Mess - Dom Dolla Remix'])
print(songs)

#results = spotdl.download_songs(songs)
#song, path = spotd.download(songs[0])