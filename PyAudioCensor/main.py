import wave
import json
from vosk import Model, KaldiRecognizer, SetLogLevel

class Word:


    def __init__(self, dict):


        self.conf = dict["conf"]
        self.end = dict["end"]
        self.start = dict["start"]
        self.word = dict["word"]

    def to_string(self):

        return "{:20} from {:.2f} sec to {:.2f} sec, confidence is {:.2f}%".format(
            self.word, self.start, self.end, self.conf*100)
    

    # def start_pointt(self):

    #     return "{:20},{:.2f}".format(
    #         self.word, self.start)
    
    def start_point(self):

        return [self.word, self.start]
    


def timestamp_list (base_audio_path,model_path):

    audio_filename = base_audio_path

    model = Model("PyAudioCensor\model")
    wf = wave.open(audio_filename, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)

    # get the list of JSON dictionaries
    results = []
    # recognize speech using vosk model
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            part_result = json.loads(rec.Result())
            results.append(part_result)
    part_result = json.loads(rec.FinalResult())
    results.append(part_result)

    # convert list of JSON dictionaries to list of 'Word' objects
    list_of_Words = []
    for sentence in results:
        if len(sentence) == 1:
            # sometimes there are bugs in recognition 
            # and it returns an empty dictionary
            # {'text': ''}
            continue
        for obj in sentence['result']:
            w = Word(obj)  # create custom Word object
            list_of_Words.append(w)  # and add it to list

    wf.close()  # close audiofile

    final=[]

    # output to the screen
    for word in list_of_Words:
        print(word.to_string())

    
    print("Now taking only the word and its starting time of occurence")
    
    for word in list_of_Words:
        time = word.start_point()
        final.append(time)
    
    for value in final:
        print(value)

    return final



def censor_audio(base_audio_path, censor_audio_path, output_audio_path, model_path, to_censor, gain_of_censor=0, gain_of_base=-40,  silent=1):
    
    time_list=timestamp_list(base_audio_path,model_path)

    def find_time_occurrences(to_censor):
        result = []
        for word in to_censor:
            for item in time_list:
                if item[0] == word:
                    result.append(item[1]*1000)
        return result

    censor_time=find_time_occurrences(to_censor)

    positions=censor_time

    for value in censor_time:
       print(value)

    # Open the base audio file
    base_audio_file = wave.open(base_audio_path, "rb")
    base_audio_params = base_audio_file.getparams()
    base_audio_frames = base_audio_file.readframes(base_audio_params.nframes)

    # Open the censor audio file
    censor_audio_file = wave.open(censor_audio_path, "rb")
    censor_audio_params = censor_audio_file.getparams()
    censor_audio_frames = censor_audio_file.readframes(censor_audio_params.nframes)

    # Define a function to convert dB to float
    def db_to_float(db):
        return 10 ** (db / 10)

    # Convert the audio frames to integers
    base_samples = list(base_audio_frames)
    censor_samples = list(censor_audio_frames)

    # Define the gain during censor
    base_gain = db_to_float(gain_of_base)

    # Apply gain to the censor audio if necessary
    if gain_of_censor is not None:
        # Convert gain from dB to float
        censor_gain = db_to_float(gain_of_censor)
        # Apply gain to the censor samples
        censor_samples = [int(sample * censor_gain) for sample in censor_samples]

    # Iterate over each position in the positions list
    for position in positions:
        # Calculate the position in samples
        position_samples = int(position / 500.0 * base_audio_params.framerate)

        # Insert the censor audio at the desired position
        for i in range(len(censor_samples)):
            if silent == 1:  # Check if silent mode is enabled
                base_samples[position_samples + i] = censor_samples[i]
            else:
                base_samples[position_samples + i] = int(base_samples[position_samples + i] * base_gain) + censor_samples[i]
            # Clip the values to the valid range of 0 to 255
            base_samples[position_samples + i] = max(0, min(base_samples[position_samples + i], 255))

    # Save the mixed audio as a new file
    with wave.open(output_audio_path, "wb") as mixed_file:
        mixed_file.setparams(base_audio_params)
        mixed_file.writeframes(bytearray(base_samples))
    return(output_audio_path)