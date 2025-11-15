/**
 * Sound Notification Service
 * Plays audio notifications for trading signals and system events
 */

class SoundService {
  constructor() {
    this.audioContext = null;
    this.enabled = true;
    this.volume = 0.5;

    // Initialize Audio Context on first user interaction
    this.initAudioContext();
  }

  initAudioContext() {
    if (!this.audioContext) {
      try {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      } catch (error) {
        console.warn('Web Audio API not supported:', error);
      }
    }
  }

  /**
   * Play a simple beep tone
   * @param {number} frequency - Frequency in Hz
   * @param {number} duration - Duration in milliseconds
   * @param {string} type - Oscillator type (sine, square, sawtooth, triangle)
   */
  playTone(frequency, duration, type = 'sine') {
    if (!this.enabled || !this.audioContext) return;

    try {
      // Resume audio context if suspended (required by browser autoplay policies)
      if (this.audioContext.state === 'suspended') {
        this.audioContext.resume();
      }

      const oscillator = this.audioContext.createOscillator();
      const gainNode = this.audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(this.audioContext.destination);

      oscillator.frequency.value = frequency;
      oscillator.type = type;

      // Envelope for smoother sound
      const now = this.audioContext.currentTime;
      gainNode.gain.setValueAtTime(0, now);
      gainNode.gain.linearRampToValueAtTime(this.volume, now + 0.01);
      gainNode.gain.exponentialRampToValueAtTime(0.01, now + duration / 1000);

      oscillator.start(now);
      oscillator.stop(now + duration / 1000);
    } catch (error) {
      console.error('Error playing tone:', error);
    }
  }

  /**
   * Play a chord (multiple tones simultaneously)
   * @param {number[]} frequencies - Array of frequencies in Hz
   * @param {number} duration - Duration in milliseconds
   */
  playChord(frequencies, duration) {
    frequencies.forEach(freq => {
      this.playTone(freq, duration, 'sine');
    });
  }

  /**
   * Strong Buy Signal - Ascending major chord
   */
  playStrongBuySignal() {
    // C Major chord ascending
    this.playChord([523.25, 659.25, 783.99], 300);
    setTimeout(() => {
      this.playTone(1046.50, 400, 'sine'); // High C
    }, 150);
  }

  /**
   * Buy Signal - Pleasant two-tone
   */
  playBuySignal() {
    this.playTone(659.25, 200, 'sine'); // E
    setTimeout(() => {
      this.playTone(783.99, 200, 'sine'); // G
    }, 150);
  }

  /**
   * Sell Signal - Descending tones
   */
  playSellSignal() {
    this.playTone(783.99, 200, 'sine'); // G
    setTimeout(() => {
      this.playTone(659.25, 200, 'sine'); // E
    }, 150);
  }

  /**
   * Strong Sell Signal - Descending minor chord
   */
  playStrongSellSignal() {
    // C Minor chord descending
    this.playTone(1046.50, 200, 'sine'); // High C
    setTimeout(() => {
      this.playChord([523.25, 622.25, 783.99], 300);
    }, 150);
  }

  /**
   * Neutral Signal - Single neutral tone
   */
  playNeutralSignal() {
    this.playTone(523.25, 150, 'sine'); // Middle C
  }

  /**
   * Trade Executed - Success sound
   */
  playTradeExecuted() {
    this.playTone(880.00, 100, 'sine'); // A
    setTimeout(() => {
      this.playTone(1046.50, 100, 'sine'); // C
    }, 80);
    setTimeout(() => {
      this.playTone(1318.51, 150, 'sine'); // E
    }, 160);
  }

  /**
   * Trade Failed - Error sound
   */
  playTradeFailed() {
    this.playTone(200, 400, 'square'); // Low dissonant tone
  }

  /**
   * Alert Notification - Attention sound
   */
  playAlert() {
    this.playTone(880.00, 150, 'square');
    setTimeout(() => {
      this.playTone(880.00, 150, 'square');
    }, 200);
  }

  /**
   * Price Target Hit - Achievement sound
   */
  playPriceTargetHit() {
    const frequencies = [523.25, 659.25, 783.99, 1046.50];
    frequencies.forEach((freq, index) => {
      setTimeout(() => {
        this.playTone(freq, 120, 'sine');
      }, index * 80);
    });
  }

  /**
   * Stop Loss Triggered - Warning sound
   */
  playStopLoss() {
    this.playTone(300, 200, 'square');
    setTimeout(() => {
      this.playTone(250, 200, 'square');
    }, 150);
    setTimeout(() => {
      this.playTone(200, 300, 'square');
    }, 300);
  }

  /**
   * New Analysis Available - Soft notification
   */
  playNewAnalysis() {
    this.playTone(800, 100, 'sine');
    setTimeout(() => {
      this.playTone(900, 100, 'sine');
    }, 100);
  }

  /**
   * Market Data Update - Subtle tick
   */
  playDataUpdate() {
    this.playTone(1200, 30, 'sine');
  }

  /**
   * Connection Established - Success tone
   */
  playConnected() {
    this.playTone(600, 100, 'sine');
    setTimeout(() => {
      this.playTone(800, 150, 'sine');
    }, 100);
  }

  /**
   * Connection Lost - Warning tone
   */
  playDisconnected() {
    this.playTone(400, 200, 'square');
    setTimeout(() => {
      this.playTone(300, 300, 'square');
    }, 200);
  }

  /**
   * Backtest Complete - Completion chime
   */
  playBacktestComplete() {
    const notes = [523.25, 659.25, 783.99, 1046.50, 1318.51];
    notes.forEach((freq, index) => {
      setTimeout(() => {
        this.playTone(freq, 150, 'sine');
      }, index * 100);
    });
  }

  /**
   * Play notification based on signal type
   * @param {string} signalType - Type of signal (STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL)
   */
  playSignalNotification(signalType) {
    switch (signalType) {
      case 'STRONG_BUY':
        this.playStrongBuySignal();
        break;
      case 'BUY':
        this.playBuySignal();
        break;
      case 'NEUTRAL':
        this.playNeutralSignal();
        break;
      case 'SELL':
        this.playSellSignal();
        break;
      case 'STRONG_SELL':
        this.playStrongSellSignal();
        break;
      default:
        this.playTone(440, 150, 'sine'); // Default A note
    }
  }

  /**
   * Enable sound notifications
   */
  enable() {
    this.enabled = true;
    this.initAudioContext();
  }

  /**
   * Disable sound notifications
   */
  disable() {
    this.enabled = false;
  }

  /**
   * Toggle sound notifications
   */
  toggle() {
    this.enabled = !this.enabled;
    if (this.enabled) {
      this.initAudioContext();
    }
    return this.enabled;
  }

  /**
   * Set volume (0.0 to 1.0)
   * @param {number} volume - Volume level
   */
  setVolume(volume) {
    this.volume = Math.max(0, Math.min(1, volume));
  }

  /**
   * Get current volume
   * @returns {number} Current volume level
   */
  getVolume() {
    return this.volume;
  }

  /**
   * Check if sound is enabled
   * @returns {boolean} Whether sound is enabled
   */
  isEnabled() {
    return this.enabled;
  }
}

// Create and export singleton instance
const soundService = new SoundService();

export default soundService;
