export class MicRecorder {
  constructor({maxSeconds, onComplete, onError}) {
    this.maxSeconds = maxSeconds;
    this.onComplete = onComplete;
    this.onError = onError;
    this.mediaRecorder = null;
    this.stream = null;
    this.chunks = [];
    this.timer = null;
  }

  isRecording() {
    return this.mediaRecorder?.state === 'recording';
  }

  async start() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
    } catch (error) {
      this.onError(error);
      return false;
    }
    const mimeType = this.pickMimeType();
    const options = mimeType ? {mimeType} : undefined;
    this.mediaRecorder = new MediaRecorder(this.stream, options);
    this.chunks = [];
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        this.chunks.push(event.data);
      }
    };
    this.mediaRecorder.onstop = () => {
      const type = this.mediaRecorder.mimeType || 'audio/webm';
      const blob = new Blob(this.chunks, {type});
      this.stopTracks();
      this.onComplete(blob);
    };
    this.mediaRecorder.start();
    this.timer = window.setTimeout(
      () => this.stop(),
      this.maxSeconds * 1000,
    );
    return true;
  }

  stop() {
    if (this.isRecording()) {
      window.clearTimeout(this.timer);
      this.mediaRecorder.stop();
    }
  }

  stopTracks() {
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
  }

  pickMimeType() {
    const options = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/ogg;codecs=opus',
    ];
    return options.find(
      (type) => MediaRecorder.isTypeSupported(type),
    ) || '';
  }
}