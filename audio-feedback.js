// Audio Feedback System - Adds click sounds and audio feedback
// This creates a smooth, professional user experience

class AudioFeedback {
    constructor() {
        this.enabled = localStorage.getItem('audioEnabled') !== 'false';
        this.volume = parseFloat(localStorage.getItem('audioVolume') || '0.3');
        this.sounds = {};
        this.initializeSounds();
        this.attachEventListeners();
    }

    // Initialize sound effects using Web Audio API
    initializeSounds() {
        // Create audio context
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Define sound frequencies and durations
        this.soundConfigs = {
            click: { frequency: 800, duration: 0.05, type: 'sine' },
            hover: { frequency: 600, duration: 0.03, type: 'sine' },
            success: { frequency: 1000, duration: 0.15, type: 'sine' },
            error: { frequency: 400, duration: 0.2, type: 'square' },
            submit: { frequency: 900, duration: 0.1, type: 'triangle' },
            open: { frequency: 700, duration: 0.08, type: 'sine' },
            close: { frequency: 500, duration: 0.08, type: 'sine' },
            notify: { frequency: 850, duration: 0.12, type: 'sine' }
        };
    }

    // Play a sound effect
    playSound(soundName) {
        if (!this.enabled || !this.soundConfigs[soundName]) return;

        const config = this.soundConfigs[soundName];
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();

        oscillator.type = config.type;
        oscillator.frequency.setValueAtTime(config.frequency, this.audioContext.currentTime);
        
        // Create smooth envelope
        gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(this.volume, this.audioContext.currentTime + 0.01);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + config.duration);

        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);

        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + config.duration);
    }

    // Attach event listeners to interactive elements
    attachEventListeners() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupListeners());
        } else {
            this.setupListeners();
        }
    }

    setupListeners() {
        // Click sounds for buttons
        document.addEventListener('click', (e) => {
            const target = e.target.closest('button, .activity-card, .application-row, .stat-card, a, .theme-btn, input[type="radio"], input[type="checkbox"]');
            if (target) {
                this.playSound('click');
                this.addRippleEffect(e, target);
            }
        });

        // Hover sounds for interactive elements
        const interactiveElements = 'button, .activity-card, .application-row, .stat-card, a:not(.switch-form a), .theme-btn';
        document.addEventListener('mouseover', (e) => {
            if (e.target.matches(interactiveElements)) {
                this.playSound('hover');
            }
        }, true);

        // Form submission sounds
        document.addEventListener('submit', () => {
            this.playSound('submit');
        });

        // Input focus sounds
        document.addEventListener('focus', (e) => {
            if (e.target.matches('input, textarea, select')) {
                this.playSound('open');
            }
        }, true);
    }

    // Add ripple effect on click
    addRippleEffect(event, element) {
        const ripple = document.createElement('span');
        ripple.classList.add('ripple-effect');
        
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        
        element.style.position = element.style.position || 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    }

    // Toggle audio on/off
    toggle() {
        this.enabled = !this.enabled;
        localStorage.setItem('audioEnabled', this.enabled);
        this.playSound(this.enabled ? 'success' : 'close');
        return this.enabled;
    }

    // Set volume
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        localStorage.setItem('audioVolume', this.volume);
    }
}

// Create global audio feedback instance
const audioFeedback = new AudioFeedback();

// Add enhanced notification system with sound
const originalShowNotification = window.showNotification;
if (typeof originalShowNotification === 'function') {
    window.showNotification = function(message, type = 'success') {
        // Play appropriate sound
        if (type === 'success') {
            audioFeedback.playSound('success');
        } else if (type === 'error') {
            audioFeedback.playSound('error');
        } else {
            audioFeedback.playSound('notify');
        }
        
        // Call original notification
        originalShowNotification(message, type);
    };
}

// Add audio toggle button (can be added to settings)
function createAudioToggle() {
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'audio-toggle-btn';
    toggleBtn.innerHTML = `<i class="fas fa-volume-${audioFeedback.enabled ? 'up' : 'mute'}"></i>`;
    toggleBtn.title = audioFeedback.enabled ? 'إيقاف الأصوات' : 'تشغيل الأصوات';
    toggleBtn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: var(--primary-color, #3b82f6);
        color: white;
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 999;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    `;
    
    toggleBtn.addEventListener('click', () => {
        const enabled = audioFeedback.toggle();
        toggleBtn.innerHTML = `<i class="fas fa-volume-${enabled ? 'up' : 'mute'}"></i>`;
        toggleBtn.title = enabled ? 'إيقاف الأصوات' : 'تشغيل الأصوات';
    });
    
    toggleBtn.addEventListener('mouseenter', () => {
        toggleBtn.style.transform = 'scale(1.1)';
    });
    
    toggleBtn.addEventListener('mouseleave', () => {
        toggleBtn.style.transform = 'scale(1)';
    });
    
    document.body.appendChild(toggleBtn);
}

// Add audio toggle on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createAudioToggle);
} else {
    createAudioToggle();
}

// Add ripple effect CSS
const rippleStyle = document.createElement('style');
rippleStyle.textContent = `
    .ripple-effect {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }
    
    .audio-toggle-btn:hover {
        box-shadow: 0 6px 20px rgba(0,0,0,0.25);
    }
    
    .audio-toggle-btn:active {
        transform: scale(0.95) !important;
    }
`;
document.head.appendChild(rippleStyle);

console.log('🔊 Audio Feedback System initialized');
