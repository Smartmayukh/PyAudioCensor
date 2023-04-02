from PyAudioCensor import main

main.censor_audio("base_audio.wav","overlay_audio.wav","censored.wav",model_path="PyCensorAudio\model",to_censor=["happier","morning","story","mind"],silent=1)

