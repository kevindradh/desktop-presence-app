"""Play registration prompts using the system's Indonesian voice when available."""
from PyQt6.QtCore import QLocale, QObject, QUrl
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtWidgets import QApplication

try:
    from PyQt6.QtTextToSpeech import QTextToSpeech
except ImportError:
    QTextToSpeech = None


class EnrollmentAudio(QObject):
    def __init__(self, resource_root, parent=None):
        super().__init__(parent)
        self.prompt = None
        self.tone = QSoundEffect(self)
        source = resource_root / 'resources/sounds/success.wav'
        if source.is_file():
            self.tone.setSource(QUrl.fromLocalFile(str(source)))
        self.tone.setVolume(.35)
        self.speech = self._indonesian_voice()
        if self.speech is not None:
            self.speech.errorOccurred.connect(self._speech_failed)

    def _indonesian_voice(self):
        if QTextToSpeech is None:
            return None
        for engine in QTextToSpeech.availableEngines():
            if engine == 'mock':
                continue
            speech = QTextToSpeech(engine, self)
            locale = next((locale for locale in speech.availableLocales()
                           if locale.language() == QLocale.Language.Indonesian), None)
            if locale is not None:
                speech.setLocale(locale)
                if (speech.state() != QTextToSpeech.State.Error
                        and speech.locale().language() == QLocale.Language.Indonesian
                        and speech.availableVoices()):
                    speech.setVolume(.65)
                    return speech
            speech.deleteLater()
        return None

    def announce(self, text):
        if text == self.prompt:
            return
        self.stop()
        self.prompt = text
        if self.speech is None:
            self._beep()
        else:
            self.speech.say(text)

    def stop(self):
        self.prompt = None
        self.tone.stop()
        if self.speech is not None:
            self.speech.stop(QTextToSpeech.BoundaryHint.Immediate)

    def _speech_failed(self, *_):
        speech, self.speech = self.speech, None
        if speech is not None:
            speech.deleteLater()
            if self.prompt is not None:
                self._beep()

    def _beep(self):
        if self.tone.status() == QSoundEffect.Status.Ready:
            self.tone.play()
        else:
            QApplication.beep()
