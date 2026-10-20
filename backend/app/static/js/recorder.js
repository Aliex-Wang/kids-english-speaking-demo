export class MicRecorder {
  constructor({maxSeconds, onComplete, onError}) {
    this.maxSeconds = maxSeconds;
    this.onComplete = onComplete;
    this.onError = onError;
    this.mediaRecorder = null;
    this.stream = null;
    this.chunks = [];
    this.timer = null;
    this.starting = false;
    this.stopRequested = false;
  }

  isRecording() {
    return this.mediaRecorder?.state === 'recording';
  }

  isStarting() {
    return this.starting;
  }

  async start() {
    if (this.starting || this.isRecording()) return false;
    this.starting = true;
    try {
      try {
        this.stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
      } catch (error) {
        this.stopRequested = false;
        this.onError(error);
        return false;
      }
      try {
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
          window.clearTimeout(this.timer);
          this.timer = null;
          const type = this.mediaRecorder.mimeType || 'audio/webm';
          const blob = new Blob(this.chunks, {type});
          this.stopTracks();
          this.onComplete(blob);
        };
        this.mediaRecorder.start();
        // Let a stop click queued during permission capture a brief answer.
        const duration = this.stopRequested ? 300 : this.maxSeconds * 1000;
        this.stopRequested = false;
        this.timer = window.setTimeout(
          () => this.stop(),
          duration,
        );
        return true;
      } catch (error) {
        window.clearTimeout(this.timer);
        this.timer = null;
        this.mediaRecorder = null;
        this.chunks = [];
        this.stopRequested = false;
        this.stopTracks();
        this.onError(error);
        return false;
      }
    } finally {
      this.starting = false;
    }
  }

  stop() {
    if (this.starting) {
      this.stopRequested = true;
      return;
    }
    if (this.isRecording()) {
      window.clearTimeout(this.timer);
      this.timer = null;
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
