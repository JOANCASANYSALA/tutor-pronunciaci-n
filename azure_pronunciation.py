import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv

# Carga las variables del .env
#parte 1
load_dotenv()
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")

#parte 2
def evaluar_pronunciacion(audio_path: str, texto_referencia: str):#El audio y la frase
    """Evalúa la pronunciación de un archivo de audio con Azure Speech."""
    #parte 
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)#pase de entrada
    audio_input = speechsdk.audio.AudioConfig(filename=audio_path)#prepara el archivo audio para azure


    #parte 3
    pronunciation_config = speechsdk.PronunciationAssessmentConfig(
        reference_text=texto_referencia, #esto es como decirle a azure que la persona deberia de haber dicho este texto
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,#puntua sobre cien
        granularity=speechsdk.PronunciationAssessmentGranularity.Word,#evalua por separado
        enable_miscue=True#detecta la equivocación
    )

    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    #recognizer es como el profesor 
    pronunciation_config.apply_to(recognizer)
    #y apply recognize es darle instruciones

    result = recognizer.recognize_once_async().get()
    #esto es deci que lo escuche y que lo evalue


    #organizar datos
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        pron_result = speechsdk.PronunciationAssessmentResult(result)
        datos = {
            "PronunciationScore": pron_result.pronunciation_score,
            "AccuracyScore": pron_result.accuracy_score,
            "FluencyScore": pron_result.fluency_score,
            "CompletenessScore": pron_result.completeness_score,
            "Words": [
                {"Word": w.word, "Score": w.accuracy_score} for w in pron_result.words
            ]
        }
        return datos
    else:
        raise Exception(f"Error: {result.reason}")
