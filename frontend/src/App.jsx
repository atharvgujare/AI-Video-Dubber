import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Play,
  Volume2,
  Globe,
  Sliders,
  CheckCircle,
  AlertTriangle,
  Download,
  RefreshCw,
  UploadCloud,
  Video,
  Layers,
  FileText,
  Music,
  Check,
  Headphones,
  Save,
  Clock,
  ChevronDown,
  ChevronUp,
  Smartphone,
  QrCode,
  Trash2,
  Copy,
  X,
  Shield,
  Palette,
  User,
  LogOut,
  Plus,
  Clipboard,
  Share2,
  Scissors,
  Mic,
  Music2,
  FileAudio
} from 'lucide-react';

const API_BASE = '';

const THEMES = [
  { id: 'cyber-dark', name: 'Cyber Dark', icon: '🌌' },
  { id: 'midnight-blue', name: 'Midnight Navy', icon: '🌊' },
  { id: 'sunset', name: 'Sunset Studio', icon: '🌅' },
  { id: 'clean-light', name: 'Clean Light', icon: '☀️' },
];

function WaveformStudio({ segments = [], currentTime = 0, duration = 30, onSeek }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement?.clientWidth || 700;
    const height = canvas.height = 90;

    ctx.clearRect(0, 0, width, height);

    const dur = Math.max(1, duration || (segments.length > 0 ? segments[segments.length - 1].end : 30));

    // Dark timeline background
    ctx.fillStyle = 'rgba(8, 10, 15, 0.85)';
    ctx.fillRect(0, 0, width, height);

    // Time markers (grid lines)
    const step = dur > 120 ? 30 : dur > 60 ? 15 : 5;
    ctx.fillStyle = 'rgba(255, 255, 255, 0.12)';
    ctx.font = '10px sans-serif';
    for (let t = 0; t <= dur; t += step) {
      const x = (t / dur) * width;
      ctx.fillRect(x, 0, 1, height);
      ctx.fillText(`${t}s`, x + 3, 14);
    }

    // Simulated amplitude bars with speech segment highlight
    const barWidth = 3;
    const barGap = 2;
    const totalBars = Math.floor(width / (barWidth + barGap));

    for (let b = 0; b < totalBars; b++) {
      const x = b * (barWidth + barGap);
      const barTime = (b / totalBars) * dur;

      const activeSeg = segments.find(s => barTime >= s.start && barTime <= s.end);

      let amp = 0.2;
      if (activeSeg) {
        const segDuration = Math.max(0.1, activeSeg.end - activeSeg.start);
        const relTime = (barTime - activeSeg.start) / segDuration;
        amp = 0.4 + 0.5 * Math.abs(Math.sin(relTime * Math.PI * 4 + b * 0.7));
      } else {
        amp = 0.08 + 0.05 * Math.sin(b * 0.3);
      }

      const barHeight = Math.max(4, amp * (height - 30));
      const y = (height - barHeight) / 2;

      if (activeSeg) {
        const isSpeaker1 = (activeSeg.speaker_id === 1) || (activeSeg.speaker === 'Speaker 1') || !activeSeg.speaker_id;
        ctx.fillStyle = isSpeaker1 ? '#06b6d4' : '#a855f7';
      } else {
        ctx.fillStyle = 'rgba(148, 163, 184, 0.25)';
      }

      if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, 2);
        ctx.fill();
      } else {
        ctx.fillRect(x, y, barWidth, barHeight);
      }
    }

    // Red playback needle
    const playheadX = Math.min(width, Math.max(0, (currentTime / dur) * width));
    ctx.fillStyle = '#f43f5e';
    ctx.fillRect(playheadX - 1, 0, 2, height);

    // Needle top handle
    ctx.beginPath();
    ctx.arc(playheadX, 6, 5, 0, Math.PI * 2);
    ctx.fillStyle = '#f43f5e';
    ctx.fill();
  }, [segments, currentTime, duration]);

  const handleCanvasClick = (e) => {
    const canvas = canvasRef.current;
    if (!canvas || !onSeek) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const dur = Math.max(1, duration || (segments.length > 0 ? segments[segments.length - 1].end : 30));
    const newTime = (clickX / rect.width) * dur;
    onSeek(Math.max(0, Math.min(dur, newTime)));
  };

  return (
    <div className="waveform-container">
      <div className="waveform-header">
        <span className="waveform-title">
          <Volume2 size={15} color="var(--accent-cyan)" /> Interactive Audio Waveform Timeline
        </span>
        <div className="waveform-legend">
          <span className="legend-item"><span className="legend-dot" style={{ background: '#06b6d4' }}></span> Speaker 1</span>
          <span className="legend-item"><span className="legend-dot" style={{ background: '#a855f7' }}></span> Speaker 2</span>
          <span className="legend-item"><span className="legend-dot" style={{ background: 'rgba(148, 163, 184, 0.3)' }}></span> Music/Ambience</span>
        </div>
      </div>
      <canvas
        ref={canvasRef}
        className="waveform-canvas"
        onClick={handleCanvasClick}
        title="Click anywhere to jump playback time"
      />
      <div className="waveform-hint">
        💡 Click anywhere on the waveform to seek video playback. Colored bars indicate dialogue segments and speaker turns.
      </div>
    </div>
  );
}

const SIMPLE_STEPS = [
  { id: 'ingestion', label: '1. Video Source' },
  { id: 'transcription', label: '2. Listen & Transcribe' },
  { id: 'translation', label: '3. Translate Words' },
  { id: 'speech_synthesis', label: '4. Generate Voice' },
  { id: 'mastering', label: '5. Balance Audio' },
  { id: 'muxing', label: '6. Finish Video' },
];

const SOURCE_LANGUAGES = [
  { code: 'auto', label: '🌐 Auto-Detect Language' },
  { code: 'en', label: '🇺🇸 English' },
  { code: 'hi', label: '🇮🇳 Hindi' },
  { code: 'es', label: '🇪🇸 Spanish' },
  { code: 'fr', label: '🇫🇷 French' },
  { code: 'de', label: '🇩🇪 German' },
  { code: 'ja', label: '🇯🇵 Japanese' },
  { code: 'zh', label: '🇨🇳 Chinese' },
  { code: 'ar', label: '🇸🇦 Arabic' },
  { code: 'ru', label: '🇷🇺 Russian' },
  { code: 'pt', label: '🇵🇹 Portuguese' },
  { code: 'ko', label: '🇰🇷 Korean' },
  { code: 'it', label: '🇮🇹 Italian' },
];

export default function App() {
  // Theme state
  const [currentTheme, setCurrentTheme] = useState(() => {
    return localStorage.getItem('ai_dubber_theme') || 'cyber-dark';
  });

  // User auth state
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('ai_dubber_user') || 'null');
    } catch {
      return null;
    }
  });

  // Languages & server status
  const [languages, setLanguages] = useState({});
  const [serverHealth, setServerHealth] = useState(null);
  const [networkInfo, setNetworkInfo] = useState({ local_ip: '127.0.0.1', port: 8000, url: 'http://localhost:8000' });

  // Form states
  const [inputTab, setInputTab] = useState('youtube'); // 'youtube' | 'upload'
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [sourceLang, setSourceLang] = useState('auto');
  const [targetLang, setTargetLang] = useState('hi');
  const [voiceGender, setVoiceGender] = useState('female');
  const [whisperModel, setWhisperModel] = useState('base');
  const [enableDucking, setEnableDucking] = useState(true);
  const [duckingVolume, setDuckingVolume] = useState(0.15);
  const [keepOriginal, setKeepOriginal] = useState(true);
  const [burnSubtitles, setBurnSubtitles] = useState(false);
  const [protectedTerms, setProtectedTerms] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Multi-Speaker Voice Assignment states
  const [enableMultiSpeaker, setEnableMultiSpeaker] = useState(false);
  const [speaker1Gender, setSpeaker1Gender] = useState('female');
  const [speaker2Gender, setSpeaker2Gender] = useState('male');

  // AI Vocal Stripping & Music Isolation state
  const [isolateVocals, setIsolateVocals] = useState(false);

  // Waveform Studio Timeline & Video sync states
  const mainVideoRef = useRef(null);
  const [videoCurrentTime, setVideoCurrentTime] = useState(0);
  const [videoPlayerDuration, setVideoPlayerDuration] = useState(0);

  // Viral Shorts & Reels Auto-Clipper states
  const [showShortsModal, setShowShortsModal] = useState(false);
  const [shortsStartTime, setShortsStartTime] = useState(0);
  const [shortsDuration, setShortsDuration] = useState(30);
  const [isGeneratingShort, setIsGeneratingShort] = useState(false);
  const [shortGeneratedUrl, setShortGeneratedUrl] = useState(null);
  const [shortError, setShortError] = useState(null);

  // Native Mobile Web Share feedback
  const [shareCopied, setShareCopied] = useState(false);

  // Active Projects Queue & Selected Project
  const [activeJobId, setActiveJobId] = useState(null);
  const [jobData, setJobData] = useState(null);
  const [recentJobs, setRecentJobs] = useState([]);
  const [activeQueueJobs, setActiveQueueJobs] = useState([]);

  // Submission & feedback
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [justSubmitted, setJustSubmitted] = useState(false);

  // Audio preview audition state
  const [isPlayingTestVoice, setIsPlayingTestVoice] = useState(false);
  const testAudioRef = useRef(null);

  // Video playback
  const [activeVideoTrack, setActiveVideoTrack] = useState('dubbed'); // 'dubbed' | 'source'

  // Editable segments
  const [editableSegments, setEditableSegments] = useState([]);
  const [isSavingSegments, setIsSavingSegments] = useState(false);
  const [segmentSaveSuccess, setSegmentSaveSuccess] = useState(false);

  // Modals & Drawers
  const [showPhoneModal, setShowPhoneModal] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showThemeModal, setShowThemeModal] = useState(false);
  const [showInstallModal, setShowInstallModal] = useState(false);
  const [copiedLanUrl, setCopiedLanUrl] = useState(false);

  // Auth form states
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'register'
  const [authName, setAuthName] = useState('');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  // PWA install prompt handler
  const [deferredInstallPrompt, setDeferredInstallPrompt] = useState(null);
  const [isInstalledPWA, setIsInstalledPWA] = useState(false);

  // In-App PWA Auto-Update state
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [waitingWorker, setWaitingWorker] = useState(null);
  const [groqApiKey, setGroqApiKey] = useState(() => localStorage.getItem('groq_api_key') || '');

  // Apply Theme on change
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('ai_dubber_theme', currentTheme);
  }, [currentTheme]);

  // Catch PWA beforeinstallprompt
  useEffect(() => {
    const handleBeforeInstall = (e) => {
      e.preventDefault();
      setDeferredInstallPrompt(e);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);

    if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
      setIsInstalledPWA(true);
    }

    return () => window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
  }, []);

  // Listen for PWA service worker background updates
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistration().then((reg) => {
        if (!reg) return;
        if (reg.waiting) {
          setUpdateAvailable(true);
          setWaitingWorker(reg.waiting);
        }
        reg.addEventListener('updatefound', () => {
          const newWorker = reg.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                setUpdateAvailable(true);
                setWaitingWorker(newWorker);
              }
            });
          }
        });
      });

      let refreshing = false;
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!refreshing) {
          refreshing = true;
          window.location.reload();
        }
      });
    }
  }, []);

  const handleApplyUpdate = () => {
    if (waitingWorker) {
      waitingWorker.postMessage({ type: 'SKIP_WAITING' });
    } else {
      window.location.reload();
    }
  };

  // Fetch initial data
  const fetchRecentJobs = () => {
    fetch(`${API_BASE}/api/jobs`)
      .then(res => res.json())
      .then(data => {
        if (data.jobs) setRecentJobs(data.jobs);
      })
      .catch(err => console.warn('Failed to load past jobs', err));

    fetch(`${API_BASE}/api/jobs/active`)
      .then(res => res.json())
      .then(data => {
        if (data.active_jobs) setActiveQueueJobs(data.active_jobs);
      })
      .catch(err => console.warn('Failed to load active queue', err));
  };

  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then(res => res.json())
      .then(data => setServerHealth(data))
      .catch(() => setServerHealth({ status: 'offline' }));

    fetch(`${API_BASE}/api/languages`)
      .then(res => res.json())
      .then(data => {
        if (data.languages) setLanguages(data.languages);
      })
      .catch(err => console.error('Failed to load languages', err));

    fetch(`${API_BASE}/api/network-info`)
      .then(res => res.json())
      .then(data => setNetworkInfo(data))
      .catch(err => console.warn('Failed to load network info', err));

    fetchRecentJobs();
    const interval = setInterval(fetchRecentJobs, 4000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket live updates for currently viewed active job
  useEffect(() => {
    if (!activeJobId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/ws/${activeJobId}`;
    let ws;

    try {
      ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        if (payload.type === 'state' && payload.job) {
          setJobData(prev => ({ ...prev, ...payload.job }));
          if (payload.job.segments && payload.job.segments.length > 0) {
            setEditableSegments(payload.job.segments);
          }
        } else if (payload.type === 'progress') {
          setJobData(prev => ({
            ...prev,
            stage: payload.stage,
            progress: payload.progress,
            logs: payload.logs || prev?.logs || []
          }));
          if (payload.data?.segments) {
            setEditableSegments(payload.data.segments);
          }
        } else if (payload.type === 'completed') {
          fetch(`${API_BASE}/api/jobs/${activeJobId}`)
            .then(res => res.json())
            .then(data => {
              setJobData(data);
              setEditableSegments(data.segments || []);
              fetchRecentJobs();
            });
        } else if (payload.type === 'error') {
          setErrorMessage(payload.error || payload.message);
          fetchRecentJobs();
        }
      };

      ws.onerror = (err) => console.warn('WebSocket notification', err);
    } catch (e) {
      console.warn('WS Init fallback to polling', e);
    }

    const interval = setInterval(() => {
      fetch(`${API_BASE}/api/jobs/${activeJobId}`)
        .then(res => res.json())
        .then(data => {
          setJobData(data);
          if (data.status === 'failed') {
            setErrorMessage(data.error || 'Dubbing pipeline failed.');
          }
          if (data.segments && data.segments.length > 0) {
            setEditableSegments(prev => (prev.length === 0 ? data.segments : prev));
          }
        })
        .catch(() => {});
    }, 2000);

    return () => {
      if (ws) ws.close();
      clearInterval(interval);
    };
  }, [activeJobId]);

  // Handle Form Submission (Allows concurrent queuing without locking the UI)
  const handleStartDubbing = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (inputTab === 'youtube' && !youtubeUrl.trim()) {
      setErrorMessage('Please enter or paste a valid YouTube video link.');
      return;
    }
    if (inputTab === 'upload' && !uploadedFile) {
      setErrorMessage('Please select or drop a video file.');
      return;
    }

    setIsSubmitting(true);

    try {
      const formData = new FormData();
      if (inputTab === 'youtube') {
        formData.append('source_url', youtubeUrl.trim());
      } else {
        formData.append('file', uploadedFile);
      }
      formData.append('target_lang', targetLang);
      formData.append('voice_gender', voiceGender);
      formData.append('whisper_model', whisperModel);
      formData.append('source_lang', sourceLang);
      formData.append('protected_terms', protectedTerms);
      formData.append('burn_subtitles', burnSubtitles);
      formData.append('enable_ducking', enableDucking);
      formData.append('ducking_volume', duckingVolume);
      formData.append('keep_original', keepOriginal);
      formData.append('isolate_vocals', isolateVocals);
      if (enableMultiSpeaker) {
        const currentLang = languages[targetLang];
        const s1Voice = currentLang?.voices?.[speaker1Gender]?.id || currentLang?.default_voice;
        const s2Voice = currentLang?.voices?.[speaker2Gender]?.id || currentLang?.default_voice;
        formData.append('voice_map', JSON.stringify({
          'Speaker 1': s1Voice,
          'Speaker 2': s2Voice,
        }));
      }
      if (currentUser?.id) {
        formData.append('user_id', currentUser.id);
      }
      if (groqApiKey && groqApiKey.trim()) {
        formData.append('groq_api_key', groqApiKey.trim());
      }

      const res = await fetch(`${API_BASE}/api/dub`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Could not start video dubbing.');
      }

      const data = await res.json();
      setActiveJobId(data.job_id);
      setJobData({
        id: data.job_id,
        status: 'queued',
        stage: 'ingestion',
        progress: 2.0,
        logs: [{ time: new Date().toLocaleTimeString(), message: 'Project added to dubbing queue.' }],
        segments: [],
      });

      setJustSubmitted(true);
      setTimeout(() => setJustSubmitted(false), 3000);
      fetchRecentJobs();
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Generate 9:16 Vertical Short with kinetic burned-in subtitles
  const handleGenerateShort = async () => {
    if (!activeJobId) return;
    setIsGeneratingShort(true);
    setShortError(null);
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${activeJobId}/generate-short`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_time: Number(shortsStartTime),
          duration: Number(shortsDuration),
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to generate vertical short.');
      }
      const data = await res.json();
      setShortGeneratedUrl(`${API_BASE}${data.short_url}?t=${Date.now()}`);
    } catch (err) {
      setShortError(err.message);
    } finally {
      setIsGeneratingShort(false);
    }
  };

  // Native Mobile Web Share API
  const handleShareMobile = async () => {
    if (!activeJobId) return;
    const shareUrl = `${window.location.origin}/api/media/${activeJobId}/dubbed_video`;
    if (navigator.share) {
      try {
        await navigator.share({
          title: jobData?.title || 'Dubbed Video',
          text: `Watch this video dubbed with AI Dubber Studio!`,
          url: shareUrl,
        });
      } catch (err) {
        if (err.name !== 'AbortError') console.warn('Share error', err);
      }
    } else {
      await navigator.clipboard.writeText(shareUrl);
      setShareCopied(true);
      setTimeout(() => setShareCopied(false), 2500);
    }
  };

  // URL input helper: Clear link
  const handleClearUrl = () => {
    setYoutubeUrl('');
  };

  // URL input helper: Paste from clipboard
  const handlePasteUrl = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) setYoutubeUrl(text.trim());
    } catch (err) {
      console.warn('Clipboard read error', err);
    }
  };

  // Audition voice sample
  const handleAuditionVoice = async () => {
    if (isPlayingTestVoice) {
      if (testAudioRef.current) testAudioRef.current.pause();
      setIsPlayingTestVoice(false);
      return;
    }

    const currentLang = languages[targetLang];
    const voiceId = currentLang?.voices?.[voiceGender]?.id || currentLang?.default_voice;

    try {
      setIsPlayingTestVoice(true);
      const res = await fetch(`${API_BASE}/api/test-voice`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          voice_id: voiceId,
          text: `नमस्ते! This is a voice sample in ${currentLang?.name || 'this language'}.`,
        }),
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);

      if (testAudioRef.current) {
        testAudioRef.current.src = url;
        testAudioRef.current.play();
        testAudioRef.current.onended = () => setIsPlayingTestVoice(false);
      }
    } catch (err) {
      console.error('Audition failed', err);
      setIsPlayingTestVoice(false);
    }
  };

  // Re-render edited segments
  const handleSaveAndReRender = async () => {
    if (!activeJobId) return;
    setIsSavingSegments(true);
    setSegmentSaveSuccess(false);

    try {
      const res = await fetch(`${API_BASE}/api/jobs/${activeJobId}/update-segments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ segments: editableSegments }),
      });

      if (!res.ok) throw new Error('Failed to update speech.');
      setSegmentSaveSuccess(true);
      setTimeout(() => setSegmentSaveSuccess(false), 3000);
      fetchRecentJobs();
    } catch (err) {
      alert('Error updating speech: ' + err.message);
    } finally {
      setIsSavingSegments(false);
    }
  };

  // Load project from history
  const handleLoadJob = async (jobId) => {
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
      if (res.ok) {
        const data = await res.json();
        setActiveJobId(jobId);
        setJobData(data);
        if (data.segments && data.segments.length > 0) {
          setEditableSegments(data.segments);
        }
        setShowHistory(false);
      }
    } catch (err) {
      console.error('Failed to load project', err);
    }
  };

  // Delete project
  const handleDeleteJob = async (jobId, e) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this project?')) return;
    try {
      await fetch(`${API_BASE}/api/jobs/${jobId}`, { method: 'DELETE' });
      if (activeJobId === jobId) {
        setActiveJobId(null);
        setJobData(null);
        setEditableSegments([]);
      }
      fetchRecentJobs();
    } catch (err) {
      console.error('Failed to delete project', err);
    }
  };

  // Auth Handler
  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthLoading(true);

    const endpoint = authMode === 'register' ? '/api/auth/register' : '/api/auth/login';
    const payload = authMode === 'register'
      ? { name: authName, email: authEmail, password: authPassword }
      : { email: authEmail, password: authPassword };

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Authentication failed.');
      }

      const data = await res.json();
      setCurrentUser(data.user);
      localStorage.setItem('ai_dubber_user', JSON.stringify(data.user));
      setShowProfileModal(false);
      setAuthPassword('');
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('ai_dubber_user');
    setShowProfileModal(false);
  };

  // PWA Install Trigger
  const handleInstallClick = async () => {
    if (deferredInstallPrompt) {
      deferredInstallPrompt.prompt();
      const choice = await deferredInstallPrompt.userChoice;
      if (choice.outcome === 'accepted') {
        setIsInstalledPWA(true);
      }
      setDeferredInstallPrompt(null);
    } else {
      setShowInstallModal(true);
    }
  };

  // Copy LAN link
  const handleCopyLink = () => {
    if (networkInfo?.url) {
      navigator.clipboard.writeText(networkInfo.url);
      setCopiedLanUrl(true);
      setTimeout(() => setCopiedLanUrl(false), 2500);
    }
  };

  const selectedLangInfo = languages[targetLang] || { name: 'Hindi', native: 'हिन्दी' };

  return (
    <div className="app-layout">
      {/* Hidden audio element for voice auditioning */}
      <audio ref={testAudioRef} />

      {/* Top Mobile-First Clean Header */}
      <header className="app-header">
        <div className="brand-badge" onClick={() => setActiveJobId(null)} style={{ cursor: 'pointer' }}>
          <div className="brand-logo-icon">
            <Sparkles size={20} />
          </div>
          <div>
            <h1 className="brand-title">AI Dubber</h1>
            <span className="brand-subtitle">Smart Studio</span>
          </div>
        </div>

        {/* Compact Action Icon Buttons (Clean on all devices) */}
        <div className="header-actions">
          {/* Theme Selector */}
          <button
            type="button"
            className="icon-btn"
            title="Change Theme"
            onClick={() => setShowThemeModal(true)}
          >
            <Palette size={18} />
          </button>

          {/* Recent Projects Drawer Button */}
          <button
            type="button"
            className="icon-btn"
            title="Saved Projects"
            onClick={() => setShowHistory(!showHistory)}
          >
            <Clock size={18} />
            {recentJobs.length > 0 && (
              <span className="badge-counter">{recentJobs.length}</span>
            )}
          </button>

          {/* Connect Phone / Install PWA */}
          <button
            type="button"
            className="icon-btn"
            title="Install App / Connect Phone"
            onClick={() => setShowPhoneModal(true)}
          >
            <Smartphone size={18} color="var(--accent-cyan)" />
          </button>

          {/* User Profile / Auth Button */}
          <button
            type="button"
            className="icon-btn"
            title={currentUser ? currentUser.name : 'Sign In / Account'}
            onClick={() => setShowProfileModal(true)}
            style={{
              background: currentUser ? 'var(--primary-glow)' : 'var(--bg-secondary)',
              borderColor: currentUser ? 'var(--primary)' : 'var(--border-subtle)',
            }}
          >
            {currentUser ? (
              <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'white' }}>
                {currentUser.name.charAt(0).toUpperCase()}
              </span>
            ) : (
              <User size={18} />
            )}
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="main-container">
        {/* In-App PWA Update Notification Banner */}
        {updateAvailable && (
          <div className="update-banner">
            <div className="update-content">
              <span className="update-icon">✨</span>
              <span><strong>New Studio Update Available!</strong> Tap to reload and use the latest features.</span>
            </div>
            <button type="button" className="update-btn" onClick={handleApplyUpdate}>Update Now</button>
          </div>
        )}

        {errorMessage && (
          <div className="glass-card" style={{ borderColor: 'var(--accent-rose)', background: 'rgba(244, 63, 94, 0.1)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--accent-rose)' }}>
              <AlertTriangle size={20} />
              <span style={{ fontWeight: 600 }}>{errorMessage}</span>
            </div>
          </div>
        )}

        {/* Multi-Project Active Queue Bar */}
        {(activeQueueJobs.length > 0 || activeJobId) && (
          <div className="queue-bar">
            {activeQueueJobs.map((qj) => {
              const isSelected = activeJobId === qj.id;
              const isDone = qj.status === 'completed';
              return (
                <div
                  key={qj.id}
                  className={`queue-chip ${isSelected ? 'active' : ''} ${!isDone ? 'processing' : ''}`}
                  onClick={() => handleLoadJob(qj.id)}
                >
                  <div
                    className="pulse-dot"
                    style={{
                      background: isDone ? 'var(--accent-emerald)' : 'var(--accent-cyan)',
                      boxShadow: isDone ? '0 0 10px var(--accent-emerald)' : '0 0 10px var(--accent-cyan)',
                    }}
                  />
                  <span className="queue-chip-title">{qj.title}</span>
                  <span style={{ opacity: 0.8, fontSize: '0.75rem' }}>
                    {isDone ? 'Ready' : `${Math.round(qj.progress)}%`}
                  </span>
                </div>
              );
            })}

            <button
              type="button"
              className="queue-chip"
              style={{ background: 'rgba(255, 255, 255, 0.05)', color: 'var(--accent-cyan)' }}
              onClick={() => {
                setActiveJobId(null);
                setJobData(null);
                setEditableSegments([]);
              }}
            >
              <Plus size={14} /> New Video
            </button>
          </div>
        )}

        {/* Recent Projects Drawer */}
        {showHistory && (
          <div className="glass-card" style={{ border: '1px solid var(--border-focus)' }}>
            <div className="section-header" style={{ marginBottom: '14px' }}>
              <h2 className="section-title">
                <Clock size={19} color="var(--accent-cyan)" />
                Recent Projects
              </h2>
              <button
                type="button"
                className="status-pill"
                style={{ cursor: 'pointer' }}
                onClick={() => setShowHistory(false)}
              >
                <X size={14} /> Close
              </button>
            </div>

            {recentJobs.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                No saved projects yet. Paste a link below to dub your first video!
              </p>
            ) : (
              <div className="history-list">
                {recentJobs.map((j) => (
                  <div
                    key={j.id}
                    className="history-item"
                    onClick={() => handleLoadJob(j.id)}
                    style={{
                      cursor: 'pointer',
                      borderColor: activeJobId === j.id ? 'var(--primary)' : 'var(--border-subtle)',
                    }}
                  >
                    <div className="history-info">
                      <span className="history-title">{j.title || 'Video Project'}</span>
                      <div className="history-meta">
                        <span>Language: <strong>{languages[j.target_lang]?.name || j.target_lang}</strong></span>
                        <span>•</span>
                        <span>{new Date(j.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        {j.burn_subtitles && (
                          <>
                            <span>•</span>
                            <span style={{ color: 'var(--accent-purple)', fontWeight: 600 }}>Subtitles Added</span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="history-actions">
                      <span
                        className="status-pill"
                        style={{
                          fontSize: '0.72rem',
                          background: j.status === 'completed' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                          color: j.status === 'completed' ? 'var(--accent-emerald)' : 'var(--text-muted)',
                        }}
                      >
                        {j.status.toUpperCase()}
                      </span>
                      <button
                        type="button"
                        className="status-pill"
                        style={{ cursor: 'pointer', background: 'transparent' }}
                        title="Delete project"
                        onClick={(e) => handleDeleteJob(j.id, e)}
                      >
                        <Trash2 size={13} color="var(--accent-rose)" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="studio-grid">
          {/* Left Column: Media Selection & Dubbing Language */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="glass-card">
              <div className="section-header">
                <h2 className="section-title">
                  <Video size={19} color="var(--primary)" />
                  1. Choose Video
                </h2>
              </div>

              {/* Tabs */}
              <div className="tab-row">
                <button
                  type="button"
                  className={`tab-btn ${inputTab === 'youtube' ? 'active' : ''}`}
                  onClick={() => setInputTab('youtube')}
                >
                  <Video size={15} /> YouTube Link
                </button>
                <button
                  type="button"
                  className={`tab-btn ${inputTab === 'upload' ? 'active' : ''}`}
                  onClick={() => setInputTab('upload')}
                >
                  <UploadCloud size={15} /> Upload File
                </button>
              </div>

              {inputTab === 'youtube' ? (
                <div className="input-group">
                  <label className="input-label" htmlFor="youtube-input">
                    <span>Paste YouTube URL</span>
                    <span style={{ color: 'var(--accent-cyan)' }}>Auto-Downloaded</span>
                  </label>
                  <div className="input-with-actions">
                    <input
                      id="youtube-input"
                      type="url"
                      className="text-input"
                      placeholder="https://www.youtube.com/watch?v=..."
                      value={youtubeUrl}
                      onChange={(e) => setYoutubeUrl(e.target.value)}
                    />
                    <div className="input-actions-group">
                      {youtubeUrl ? (
                        <button
                          type="button"
                          className="input-action-btn clear-btn"
                          title="Clear link"
                          onClick={handleClearUrl}
                        >
                          <X size={16} />
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="input-action-btn paste-btn"
                          title="Paste from clipboard"
                          onClick={handlePasteUrl}
                        >
                          <Clipboard size={14} /> Paste
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div
                  className="drop-zone"
                  onClick={() => document.getElementById('file-input').click()}
                >
                  <UploadCloud size={34} color="var(--primary)" />
                  <p style={{ fontWeight: 600 }}>
                    {uploadedFile ? uploadedFile.name : 'Tap to select or drop video'}
                  </p>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Supports MP4, MOV, MKV (up to 2GB)
                  </span>
                  <input
                    id="file-input"
                    type="file"
                    accept="video/*"
                    style={{ display: 'none' }}
                    onChange={(e) => {
                      if (e.target.files?.[0]) setUploadedFile(e.target.files[0]);
                    }}
                  />
                </div>
              )}

              {/* Source Language */}
              <div className="input-group" style={{ marginTop: '14px', marginBottom: 0 }}>
                <label className="input-label">
                  <span>Spoken Language in Video</span>
                  <span style={{ color: 'var(--accent-cyan)' }}>Auto-Detects 99+ Languages</span>
                </label>
                <select
                  className="text-input"
                  value={sourceLang}
                  onChange={(e) => setSourceLang(e.target.value)}
                >
                  {SOURCE_LANGUAGES.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Language & Voice Selector */}
            <div className="glass-card">
              <div className="section-header">
                <h2 className="section-title">
                  <Globe size={19} color="var(--accent-purple)" />
                  2. Choose Dubbing Language
                </h2>
                <span className="status-pill" style={{ color: 'var(--accent-purple)' }}>
                  {selectedLangInfo.name} ({selectedLangInfo.native})
                </span>
              </div>

              {/* Languages Grid */}
              <div className="lang-grid">
                {Object.entries(languages).map(([code, item]) => (
                  <div
                    key={code}
                    className={`lang-card ${targetLang === code ? 'selected' : ''}`}
                    onClick={() => setTargetLang(code)}
                  >
                    <span className="lang-flag">{item.flag || '🌐'}</span>
                    <span className="lang-name">{item.name}</span>
                    <span className="lang-native">{item.native}</span>
                  </div>
                ))}
              </div>

              {/* Voice Style (Single vs Multi-Speaker) */}
              <div className="input-label" style={{ marginBottom: '8px' }}>
                <span>Voice Style & Speakers</span>
                <button
                  type="button"
                  className="status-pill"
                  style={{ cursor: 'pointer', background: 'var(--primary-glow)', color: 'white' }}
                  onClick={handleAuditionVoice}
                >
                  <Headphones size={13} />
                  {isPlayingTestVoice ? 'Playing...' : 'Listen Sample'}
                </button>
              </div>

              {/* Multi-Speaker Dialogue Mode Switch */}
              <div style={{
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '10px 14px',
                marginBottom: '12px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Mic size={16} color="var(--accent-cyan)" />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      Multi-Speaker Dialogue Mode
                    </div>
                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                      Assign distinct voices for two or more speakers in conversations
                    </div>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={enableMultiSpeaker}
                  onChange={(e) => setEnableMultiSpeaker(e.target.checked)}
                  style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }}
                />
              </div>

              {enableMultiSpeaker ? (
                <div className="speaker-matrix-grid">
                  <div className="speaker-card">
                    <div className="speaker-card-header">
                      <span style={{ color: 'var(--accent-cyan)' }}>🎙️ Speaker 1 (Lead)</span>
                    </div>
                    <div className="voice-selector" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }}>
                      <button
                        type="button"
                        className={`voice-btn ${speaker1Gender === 'female' ? 'selected' : ''}`}
                        onClick={() => setSpeaker1Gender('female')}
                        style={{ padding: '6px' }}
                      >
                        <span style={{ fontSize: '0.82rem' }}>Female</span>
                      </button>
                      <button
                        type="button"
                        className={`voice-btn ${speaker1Gender === 'male' ? 'selected' : ''}`}
                        onClick={() => setSpeaker1Gender('male')}
                        style={{ padding: '6px' }}
                      >
                        <span style={{ fontSize: '0.82rem' }}>Male</span>
                      </button>
                    </div>
                  </div>

                  <div className="speaker-card">
                    <div className="speaker-card-header">
                      <span style={{ color: 'var(--accent-purple)' }}>🎙️ Speaker 2 (Co-Host)</span>
                    </div>
                    <div className="voice-selector" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }}>
                      <button
                        type="button"
                        className={`voice-btn ${speaker2Gender === 'female' ? 'selected' : ''}`}
                        onClick={() => setSpeaker2Gender('female')}
                        style={{ padding: '6px' }}
                      >
                        <span style={{ fontSize: '0.82rem' }}>Female</span>
                      </button>
                      <button
                        type="button"
                        className={`voice-btn ${speaker2Gender === 'male' ? 'selected' : ''}`}
                        onClick={() => setSpeaker2Gender('male')}
                        style={{ padding: '6px' }}
                      >
                        <span style={{ fontSize: '0.82rem' }}>Male</span>
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="voice-selector">
                  <button
                    type="button"
                    className={`voice-btn ${voiceGender === 'female' ? 'selected' : ''}`}
                    onClick={() => setVoiceGender('female')}
                  >
                    <span>Female Voice</span>
                    <span style={{ fontSize: '0.8rem', opacity: 0.8 }}>Natural</span>
                  </button>
                  <button
                    type="button"
                    className={`voice-btn ${voiceGender === 'male' ? 'selected' : ''}`}
                    onClick={() => setVoiceGender('male')}
                  >
                    <span>Male Voice</span>
                    <span style={{ fontSize: '0.8rem', opacity: 0.8 }}>Deep</span>
                  </button>
                </div>
              )}

              {/* More Settings Drawer */}
              <div style={{ marginTop: '16px' }}>
                <button
                  type="button"
                  className="btn-secondary"
                  style={{ width: '100%', justifyContent: 'space-between' }}
                  onClick={() => setShowAdvanced(!showAdvanced)}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sliders size={16} /> More Settings (Optional)
                  </span>
                  {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>

                {showAdvanced && (
                  <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {/* Vocal Stripping & Background Music Isolation */}
                    <div style={{
                      background: 'rgba(6, 182, 212, 0.08)',
                      border: '1px solid rgba(6, 182, 212, 0.25)',
                      borderRadius: 'var(--radius-md)',
                      padding: '12px 14px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>
                          <Music2 size={16} /> AI Vocal Stripping & Background Music Isolation
                        </div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                          Cancels original speech to isolate background music and sound effects cleanly.
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        checked={isolateVocals}
                        onChange={(e) => setIsolateVocals(e.target.checked)}
                        style={{ width: '18px', height: '18px', accentColor: 'var(--accent-cyan)' }}
                      />
                    </div>

                    {/* Burn Subtitles Toggle */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <label className="input-label" style={{ marginBottom: 0 }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <FileText size={15} color="var(--accent-purple)" />
                          Add subtitles directly on video (for Shorts & Reels)
                        </span>
                      </label>
                      <input
                        type="checkbox"
                        checked={burnSubtitles}
                        onChange={(e) => setBurnSubtitles(e.target.checked)}
                        style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }}
                      />
                    </div>

                    {/* Words to keep unchanged */}
                    <div className="input-group" style={{ marginBottom: 0 }}>
                      <label className="input-label">
                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Shield size={15} color="var(--accent-emerald)" />
                          Words to keep unchanged (Brand names, products)
                        </span>
                      </label>
                      <input
                        type="text"
                        className="text-input"
                        placeholder="e.g. iPhone, OpenAI, Python (comma-separated)"
                        value={protectedTerms}
                        onChange={(e) => setProtectedTerms(e.target.value)}
                      />
                    </div>

                    {/* Auto-lower background music */}
                    {!isolateVocals && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <label className="input-label" style={{ marginBottom: 0 }}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <Music size={15} color="var(--accent-cyan)" /> Auto-soften background music while speaking
                            </span>
                          </label>
                          <input
                            type="checkbox"
                            checked={enableDucking}
                            onChange={(e) => setEnableDucking(e.target.checked)}
                            style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }}
                          />
                        </div>
                        {enableDucking && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <input
                              type="range"
                              min="0.05"
                              max="0.4"
                              step="0.05"
                              value={duckingVolume}
                              onChange={(e) => setDuckingVolume(parseFloat(e.target.value))}
                              style={{ flex: 1, accentColor: 'var(--accent-cyan)' }}
                            />
                            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', minWidth: '45px' }}>
                              {Math.round(duckingVolume * 100)}%
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Multi-audio track */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <label className="input-label" style={{ marginBottom: 0 }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Layers size={15} /> Keep original speech as secondary audio track
                        </span>
                      </label>
                      <input
                        type="checkbox"
                        checked={keepOriginal}
                        onChange={(e) => setKeepOriginal(e.target.checked)}
                        style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Start Button */}
              <div style={{ marginTop: '22px' }}>
                <button
                  type="button"
                  className="btn-primary"
                  onClick={handleStartDubbing}
                  disabled={isSubmitting}
                  style={{
                    background: justSubmitted
                      ? 'var(--accent-emerald)'
                      : 'linear-gradient(135deg, var(--primary), var(--accent-purple))'
                  }}
                >
                  {isSubmitting ? (
                    <>
                      <RefreshCw size={18} className="spin" /> Queuing Video...
                    </>
                  ) : justSubmitted ? (
                    <>
                      <Check size={18} /> Dubbing Started! (See Status)
                    </>
                  ) : (
                    <>
                      <Sparkles size={18} /> Generate {selectedLangInfo.name} Dubbed Video
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Live Progress & Media Player */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Live Progress Card */}
            <div className="glass-card" style={{
              borderColor: jobData?.status === 'processing' ? 'var(--primary)' : 'var(--border-subtle)',
              boxShadow: jobData?.status === 'processing' ? '0 0 30px var(--primary-glow)' : '0 8px 32px 0 rgba(0, 0, 0, 0.36)'
            }}>
              <div className="section-header">
                <h2 className="section-title">
                  <Play size={19} color="var(--accent-cyan)" />
                  Dubbing Status
                </h2>
                <span
                  className="status-pill"
                  style={{
                    background: jobData?.status === 'processing' ? 'rgba(99, 102, 241, 0.2)' : jobData?.status === 'completed' ? 'rgba(16, 185, 129, 0.2)' : jobData?.status === 'failed' ? 'rgba(244, 63, 94, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                    color: jobData?.status === 'processing' ? 'var(--accent-cyan)' : jobData?.status === 'completed' ? 'var(--accent-emerald)' : jobData?.status === 'failed' ? 'var(--accent-rose)' : 'var(--text-muted)',
                    borderColor: jobData?.status === 'processing' ? 'var(--primary)' : jobData?.status === 'completed' ? 'var(--accent-emerald)' : jobData?.status === 'failed' ? 'var(--accent-rose)' : 'var(--border-subtle)',
                  }}
                >
                  {jobData?.status === 'processing' ? (
                    <>
                      <RefreshCw size={12} className="spin" /> IN PROGRESS
                    </>
                  ) : jobData?.status ? (
                    jobData.status.toUpperCase()
                  ) : (
                    'READY'
                  )}
                </span>
              </div>

              {/* Plain-English Status Banner */}
              {jobData?.status === 'processing' && (
                <div style={{
                  background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(6, 182, 212, 0.15))',
                  border: '1px solid var(--border-focus)',
                  borderRadius: 'var(--radius-md)',
                  padding: '14px 16px',
                  marginBottom: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px'
                }}>
                  <RefreshCw size={22} className="spin" color="var(--accent-cyan)" />
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--text-primary)' }}>
                      {jobData?.stage === 'ingestion'
                        ? '1/6: Downloading video file...'
                        : jobData?.stage === 'transcription'
                        ? '2/6: Listening to spoken words...'
                        : jobData?.stage === 'translation'
                        ? `3/6: Translating sentences into ${selectedLangInfo.name}...`
                        : jobData?.stage === 'speech_synthesis'
                        ? '4/6: Generating natural AI voice...'
                        : jobData?.stage === 'mastering'
                        ? '5/6: Balancing speech volume and music...'
                        : jobData?.stage === 'muxing'
                        ? '6/6: Creating your final dubbed video...'
                        : 'Dubbing your video in background...'}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {jobData?.logs?.[jobData.logs.length - 1]?.message || 'Working on video tasks...'}
                    </div>
                  </div>
                </div>
              )}

              {/* Failure Banner */}
              {jobData?.status === 'failed' && (
                <div style={{
                  background: 'rgba(244, 63, 94, 0.15)',
                  border: '1px solid var(--accent-rose)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px',
                  marginBottom: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-rose)', fontWeight: 700 }}>
                    <AlertTriangle size={18} /> Processing Notice
                  </div>
                  <p style={{ fontSize: '0.85rem', color: '#fecdd3' }}>
                    {jobData?.error || 'Could not complete video processing.'}
                  </p>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    💡 Tip: If YouTube restricted this video, you can download it and use the <strong>Upload File</strong> tab to drop it directly.
                  </div>
                </div>
              )}

              {/* 6-Step Visual Stepper */}
              <div className="pipeline-stepper">
                {SIMPLE_STEPS.map((step, idx) => {
                  const currentIdx = SIMPLE_STEPS.findIndex(s => s.id === jobData?.stage);
                  const isCompleted = jobData?.status === 'completed' || (currentIdx > idx);
                  const isActive = jobData?.status === 'processing' && jobData?.stage === step.id;
                  const isFailed = jobData?.status === 'failed' && jobData?.stage === step.id;

                  return (
                    <div
                      key={step.id}
                      className={`step-node ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''} ${isFailed ? 'failed' : ''}`}
                    >
                      {isCompleted ? (
                        <CheckCircle size={15} color="var(--accent-emerald)" />
                      ) : isFailed ? (
                        <AlertTriangle size={15} color="var(--accent-rose)" />
                      ) : isActive ? (
                        <RefreshCw size={15} className="spin" color="var(--accent-cyan)" />
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>0{idx + 1}</span>
                      )}
                      <span className="step-title">{step.label}</span>
                    </div>
                  );
                })}
              </div>

              {/* Progress Bar */}
              <div className="progress-container">
                <div
                  className="progress-fill"
                  style={{ width: `${jobData ? jobData.progress || 0 : 0}%` }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                <span>{jobData?.logs?.[jobData.logs.length - 1]?.message || 'Ready for next video'}</span>
                <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                  {Math.round(jobData?.progress || 0)}%
                </span>
              </div>
            </div>

            {/* Video Player & Downloads */}
            {jobData?.status === 'completed' && (
              <div className="glass-card">
                <div className="section-header">
                  <h2 className="section-title">
                    <Play size={19} color="var(--accent-emerald)" />
                    Watch Dubbed Video
                  </h2>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      className={`status-pill ${activeVideoTrack === 'dubbed' ? 'active' : ''}`}
                      style={{ cursor: 'pointer', background: activeVideoTrack === 'dubbed' ? 'var(--primary)' : 'transparent' }}
                      onClick={() => setActiveVideoTrack('dubbed')}
                    >
                      Dubbed Video
                    </button>
                    <button
                      className={`status-pill ${activeVideoTrack === 'source' ? 'active' : ''}`}
                      style={{ cursor: 'pointer', background: activeVideoTrack === 'source' ? 'var(--primary)' : 'transparent' }}
                      onClick={() => setActiveVideoTrack('source')}
                    >
                      Original Video
                    </button>
                  </div>
                </div>

                <div className="player-container">
                  <video
                    ref={mainVideoRef}
                    className="video-frame"
                    controls
                    src={`${API_BASE}/api/media/${jobData.id}/${activeVideoTrack === 'dubbed' ? 'dubbed_video' : 'source_video'}`}
                    key={activeVideoTrack}
                    onTimeUpdate={(e) => setVideoCurrentTime(e.target.currentTime)}
                    onLoadedMetadata={(e) => setVideoPlayerDuration(e.target.duration)}
                  />

                  {/* Interactive Visual Waveform Timeline Studio */}
                  <WaveformStudio
                    segments={editableSegments && editableSegments.length > 0 ? editableSegments : (jobData.segments || [])}
                    currentTime={videoCurrentTime}
                    duration={videoPlayerDuration || jobData.result?.duration || jobData.result?.video_duration || 30}
                    onSeek={(time) => {
                      if (mainVideoRef.current) {
                        mainVideoRef.current.currentTime = time;
                        mainVideoRef.current.play().catch(() => {});
                      }
                    }}
                  />

                  {/* Quick Action Bar: Shorts & Mobile Share */}
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      className="btn-primary"
                      style={{
                        flex: 1,
                        background: 'linear-gradient(135deg, var(--accent-rose), var(--accent-purple))',
                        boxShadow: '0 4px 15px rgba(244, 63, 94, 0.3)',
                        gap: '8px'
                      }}
                      onClick={() => setShowShortsModal(true)}
                    >
                      <Scissors size={18} /> ✨ Create 9:16 Short / Reel
                    </button>

                    <button
                      type="button"
                      className="btn-secondary"
                      style={{
                        background: shareCopied ? 'var(--accent-emerald)' : 'var(--bg-tertiary)',
                        color: shareCopied ? 'white' : 'var(--text-primary)',
                        borderColor: shareCopied ? 'var(--accent-emerald)' : 'var(--border-subtle)',
                        gap: '8px'
                      }}
                      onClick={handleShareMobile}
                    >
                      {shareCopied ? <Check size={16} /> : <Share2 size={16} color="var(--accent-cyan)" />}
                      {shareCopied ? 'Link Copied!' : 'Share on Mobile'}
                    </button>
                  </div>

                  {/* Multi-Format Studio Exports Deck */}
                  <div className="exports-deck">
                    <div className="exports-deck-title">
                      <Download size={16} color="var(--accent-emerald)" /> Studio Exports & Downloads
                    </div>
                    <div className="exports-grid">
                      <a
                        href={`${API_BASE}/api/media/${jobData.id}/dubbed_video`}
                        download
                        className="export-tile"
                      >
                        <div className="export-tile-icon" style={{ color: 'var(--accent-emerald)' }}>
                          <Video size={16} /> Dubbed MP4
                        </div>
                        <div className="export-tile-sub">Full 1080p Video</div>
                      </a>

                      <a
                        href={`${API_BASE}/api/media/${jobData.id}/mp3`}
                        download
                        className="export-tile"
                      >
                        <div className="export-tile-icon" style={{ color: 'var(--accent-cyan)' }}>
                          <Volume2 size={16} /> Voice MP3
                        </div>
                        <div className="export-tile-sub">192k Audio Track</div>
                      </a>

                      <a
                        href={`${API_BASE}/api/media/${jobData.id}/music`}
                        download
                        className="export-tile"
                      >
                        <div className="export-tile-icon" style={{ color: 'var(--accent-purple)' }}>
                          <Music2 size={16} /> Music / SFX
                        </div>
                        <div className="export-tile-sub">Isolated Ambience</div>
                      </a>

                      <a
                        href={`${API_BASE}/api/media/${jobData.id}/subtitles`}
                        download
                        className="export-tile"
                      >
                        <div className="export-tile-icon" style={{ color: 'var(--accent-amber)' }}>
                          <FileText size={16} /> Subtitles (.SRT)
                        </div>
                        <div className="export-tile-sub">Standard timed SRT</div>
                      </a>

                      <a
                        href={`${API_BASE}/api/media/${jobData.id}/vtt`}
                        download
                        className="export-tile"
                      >
                        <div className="export-tile-icon" style={{ color: '#38bdf8' }}>
                          <FileText size={16} /> WebVTT (.VTT)
                        </div>
                        <div className="export-tile-sub">HTML5 Video Subtitles</div>
                      </a>

                      <a
                        href={`${API_BASE}/api/media/${jobData.id}/transcript_txt`}
                        download
                        className="export-tile"
                      >
                        <div className="export-tile-icon" style={{ color: 'var(--text-secondary)' }}>
                          <FileAudio size={16} /> Transcript (.TXT)
                        </div>
                        <div className="export-tile-sub">Plain Text Script</div>
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Interactive Segment Editor */}
        {editableSegments && editableSegments.length > 0 && (
          <div className="glass-card">
            <div className="section-header">
              <div>
                <h2 className="section-title">
                  <FileText size={19} color="var(--primary)" />
                  Edit Words & Subtitles
                </h2>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Want to change any translation? Edit the text below and tap "Save & Re-dub" to re-generate updated voice clips.
                </p>
              </div>

              <button
                type="button"
                className="btn-secondary"
                onClick={handleSaveAndReRender}
                disabled={isSavingSegments}
                style={{ background: segmentSaveSuccess ? 'var(--accent-emerald)' : 'var(--bg-secondary)' }}
              >
                {isSavingSegments ? (
                  <>
                    <RefreshCw size={15} className="spin" /> Updating...
                  </>
                ) : segmentSaveSuccess ? (
                  <>
                    <Check size={15} /> Saved & Updated!
                  </>
                ) : (
                  <>
                    <Save size={15} /> Save & Re-dub
                  </>
                )}
              </button>
            </div>

            <div className="segment-table-wrapper">
              <table className="segment-table">
                <thead>
                  <tr>
                    <th style={{ width: '45px' }}>#</th>
                    <th style={{ width: '120px' }}>Speaker</th>
                    <th style={{ width: '130px' }}>Time</th>
                    <th>Original Spoken Speech</th>
                    <th>Translated Speech ({selectedLangInfo.name})</th>
                  </tr>
                </thead>
                <tbody>
                  {editableSegments.map((seg, idx) => (
                    <tr key={seg.id || idx}>
                      <td style={{ color: 'var(--text-muted)', fontWeight: 600 }}>{idx + 1}</td>
                      <td>
                        <button
                          type="button"
                          className="speaker-badge"
                          style={{
                            background: (seg.speaker_id === 2 || seg.speaker === 'Speaker 2') ? 'rgba(168, 85, 247, 0.2)' : 'rgba(6, 182, 212, 0.2)',
                            color: (seg.speaker_id === 2 || seg.speaker === 'Speaker 2') ? 'var(--accent-purple)' : 'var(--accent-cyan)',
                            borderColor: (seg.speaker_id === 2 || seg.speaker === 'Speaker 2') ? 'var(--accent-purple)' : 'var(--accent-cyan)',
                            cursor: 'pointer'
                          }}
                          onClick={() => {
                            const nextId = (seg.speaker_id === 2 || seg.speaker === 'Speaker 2') ? 1 : 2;
                            setEditableSegments(prev =>
                              prev.map((s, i) => (i === idx ? { ...s, speaker_id: nextId, speaker: `Speaker ${nextId}` } : s))
                            );
                          }}
                          title="Click to toggle speaker turn between Speaker 1 and Speaker 2"
                        >
                          <Mic size={11} /> {seg.speaker || `Speaker ${seg.speaker_id || 1}`}
                        </button>
                      </td>
                      <td>
                        <span className="status-pill" style={{ padding: '2px 8px', fontSize: '0.75rem' }}>
                          <Clock size={11} /> {seg.start.toFixed(1)}s - {seg.end.toFixed(1)}s
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        {seg.text}
                      </td>
                      <td>
                        <textarea
                          className="editable-textarea"
                          rows={2}
                          value={seg.translated || ''}
                          onChange={(e) => {
                            const val = e.target.value;
                            setEditableSegments(prev =>
                              prev.map((s, i) => (i === idx ? { ...s, translated: val } : s))
                            );
                          }}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Theme Selection Modal */}
      {showThemeModal && (
        <div className="modal-backdrop" onClick={() => setShowThemeModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Palette size={22} color="var(--primary)" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Choose Studio Theme</h3>
              </div>
              <button
                type="button"
                className="status-pill"
                style={{ cursor: 'pointer', background: 'transparent' }}
                onClick={() => setShowThemeModal(false)}
              >
                <X size={16} />
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
              {THEMES.map((th) => (
                <div
                  key={th.id}
                  onClick={() => {
                    setCurrentTheme(th.id);
                    setShowThemeModal(false);
                  }}
                  style={{
                    padding: '16px',
                    borderRadius: 'var(--radius-md)',
                    background: currentTheme === th.id ? 'var(--primary-glow)' : 'var(--bg-tertiary)',
                    border: `1px solid ${currentTheme === th.id ? 'var(--primary)' : 'var(--border-subtle)'}`,
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                    transition: 'all 200ms ease',
                  }}
                >
                  <span style={{ fontSize: '1.6rem' }}>{th.icon}</span>
                  <span style={{ fontWeight: 700, fontSize: '0.92rem' }}>{th.name}</span>
                  {currentTheme === th.id && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--accent-emerald)', fontWeight: 600 }}>
                      ✓ Active Theme
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* User Profile & Auth Modal */}
      {showProfileModal && (
        <div className="modal-backdrop" onClick={() => setShowProfileModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <User size={22} color="var(--primary)" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>
                  {currentUser ? 'Creator Profile' : 'Sign In / Register'}
                </h3>
              </div>
              <button
                type="button"
                className="status-pill"
                style={{ cursor: 'pointer', background: 'transparent' }}
                onClick={() => setShowProfileModal(false)}
              >
                <X size={16} />
              </button>
            </div>

            {currentUser ? (
              <div>
                <div className="profile-card-header">
                  <div className="profile-avatar-circle">
                    {currentUser.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h4 style={{ fontSize: '1.1rem', fontWeight: 700 }}>{currentUser.name}</h4>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{currentUser.email}</span>
                    <div style={{ marginTop: '4px' }}>
                      <span className="status-pill" style={{ fontSize: '0.72rem', color: 'var(--accent-cyan)' }}>
                        ★ Pro Studio Creator
                      </span>
                    </div>
                  </div>
                </div>

                <div className="profile-stats-grid">
                  <div className="stat-box">
                    <span className="stat-num">{currentUser.videos_dubbed || 0}</span>
                    <span className="stat-label">Videos Dubbed</span>
                  </div>
                  <div className="stat-box">
                    <span className="stat-num">{recentJobs.length}</span>
                    <span className="stat-label">Saved Projects</span>
                  </div>
                </div>

                {/* Cloud & Performance Settings */}
                <div style={{ marginTop: '20px', padding: '14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '8px', color: 'var(--accent-cyan)' }}>
                    ⚡ Cloud & Speed Settings
                  </div>
                  <label className="input-label" style={{ fontSize: '0.8rem' }}>
                    Groq Free Cloud Whisper API Key (Optional)
                  </label>
                  <input
                    type="password"
                    className="text-input"
                    placeholder="gsk_..."
                    value={groqApiKey}
                    onChange={(e) => {
                      setGroqApiKey(e.target.value);
                      localStorage.setItem('groq_api_key', e.target.value);
                    }}
                    style={{ fontSize: '0.82rem', padding: '6px 10px' }}
                  />
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginTop: '4px' }}>
                    Enables ~2-second cloud transcription on Render. Free at <a href="https://console.groq.com/keys" target="_blank" rel="noreferrer" style={{ color: 'var(--accent-cyan)' }}>console.groq.com</a>.
                  </span>
                  <div style={{ marginTop: '10px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    App Version: <strong style={{ color: 'var(--text-primary)' }}>v2.2.0 (Cloud Edition)</strong>
                  </div>
                </div>

                <div style={{ marginTop: '16px' }}>
                  <button
                    type="button"
                    className="btn-secondary"
                    style={{ width: '100%', color: 'var(--accent-rose)', borderColor: 'rgba(244, 63, 94, 0.3)' }}
                    onClick={handleLogout}
                  >
                    <LogOut size={16} /> Sign Out
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <div className="auth-tabs">
                  <button
                    type="button"
                    className={`auth-tab ${authMode === 'login' ? 'active' : ''}`}
                    onClick={() => { setAuthMode('login'); setAuthError(''); }}
                  >
                    Sign In
                  </button>
                  <button
                    type="button"
                    className={`auth-tab ${authMode === 'register' ? 'active' : ''}`}
                    onClick={() => { setAuthMode('register'); setAuthError(''); }}
                  >
                    Create Account
                  </button>
                </div>

                {authError && (
                  <div style={{ color: 'var(--accent-rose)', fontSize: '0.85rem', marginBottom: '12px' }}>
                    {authError}
                  </div>
                )}

                <form onSubmit={handleAuthSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {authMode === 'register' && (
                    <div className="input-group" style={{ marginBottom: 0 }}>
                      <label className="input-label">Your Name</label>
                      <input
                        type="text"
                        className="text-input"
                        placeholder="e.g. Alex"
                        value={authName}
                        onChange={(e) => setAuthName(e.target.value)}
                        required
                      />
                    </div>
                  )}

                  <div className="input-group" style={{ marginBottom: 0 }}>
                    <label className="input-label">Email Address</label>
                    <input
                      type="email"
                      className="text-input"
                      placeholder="name@example.com"
                      value={authEmail}
                      onChange={(e) => setAuthEmail(e.target.value)}
                      required
                    />
                  </div>

                  <div className="input-group" style={{ marginBottom: 0 }}>
                    <label className="input-label">Password</label>
                    <input
                      type="password"
                      className="text-input"
                      placeholder="••••••••"
                      value={authPassword}
                      onChange={(e) => setAuthPassword(e.target.value)}
                      required
                    />
                  </div>

                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={authLoading}
                    style={{ marginTop: '8px' }}
                  >
                    {authLoading ? 'Signing in...' : authMode === 'register' ? 'Create Account' : 'Sign In'}
                  </button>

                  <div style={{ textAlign: 'center', marginTop: '4px' }}>
                    <button
                      type="button"
                      style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '0.82rem', cursor: 'pointer' }}
                      onClick={() => setShowProfileModal(false)}
                    >
                      Continue as Guest (No login required)
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Connect Phone & Mobile Install Modal */}
      {showPhoneModal && (
        <div className="modal-backdrop" onClick={() => setShowPhoneModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Smartphone size={22} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Mobile Access & Install</h3>
              </div>
              <button
                type="button"
                className="status-pill"
                style={{ cursor: 'pointer', background: 'transparent' }}
                onClick={() => setShowPhoneModal(false)}
              >
                <X size={16} />
              </button>
            </div>

            <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Scan this QR code with your iPhone or Android camera to open AI Dubber Studio on your phone!
            </p>

            <div className="qr-box">
              <img
                src={`${API_BASE}/api/qr-code`}
                alt="Studio QR Code"
                width="200"
                height="200"
              />
            </div>

            <div className="lan-link-box">
              <span className="lan-link-text">{networkInfo?.url || 'http://localhost:8000'}</span>
              <button
                type="button"
                className="status-pill"
                style={{
                  cursor: 'pointer',
                  background: copiedLanUrl ? 'var(--accent-emerald)' : 'var(--primary)',
                  color: 'white',
                  flexShrink: 0
                }}
                onClick={handleCopyLink}
              >
                {copiedLanUrl ? <Check size={14} /> : <Copy size={14} />}
                <span>{copiedLanUrl ? 'Copied!' : 'Copy'}</span>
              </button>
            </div>

            {/* Direct PWA Install Button */}
            <div>
              <button
                type="button"
                className="btn-primary"
                style={{ width: '100%', gap: '8px' }}
                onClick={handleInstallClick}
              >
                <Smartphone size={17} /> Install App Directly on Phone
              </button>
            </div>

            <div className="ios-instructions">
              <strong>📲 How to install as a Home Screen App:</strong>
              <ol>
                <li><strong>iPhone (Safari):</strong> Tap the <strong>Share</strong> button (box with arrow) at the bottom, then choose <strong>"Add to Home Screen"</strong>.</li>
                <li><strong>Android (Chrome):</strong> Tap the <strong>three dots menu</strong> [⋮], then select <strong>"Install App"</strong> or <strong>"Add to Home Screen"</strong>.</li>
              </ol>
            </div>
          </div>
        </div>
      )}

      {/* iOS / Browser Install Instructions Modal */}
      {showInstallModal && (
        <div className="modal-backdrop" onClick={() => setShowInstallModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Smartphone size={22} color="var(--primary)" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Install AI Dubber App</h3>
              </div>
              <button
                type="button"
                className="status-pill"
                style={{ cursor: 'pointer', background: 'transparent' }}
                onClick={() => setShowInstallModal(false)}
              >
                <X size={16} />
              </button>
            </div>

            <div className="ios-instructions" style={{ fontSize: '0.9rem' }}>
              <p>You can add AI Dubber directly to your home screen or desktop for a full-screen, native app experience:</p>
              <ol style={{ marginTop: '12px' }}>
                <li><strong>iPhone / iPad (Safari):</strong> Tap the <strong>Share</strong> icon (square with arrow up), scroll down and tap <strong>"Add to Home Screen"</strong>.</li>
                <li><strong>Android (Chrome):</strong> Tap the <strong>three dots</strong> in top right and choose <strong>"Install app"</strong>.</li>
                <li><strong>PC / Mac (Chrome/Edge):</strong> Look for the <strong>Install icon</strong> ⊕ in the browser address bar.</li>
              </ol>
            </div>

            <button
              type="button"
              className="btn-primary"
              onClick={() => setShowInstallModal(false)}
            >
              Got it!
            </button>
          </div>
        </div>
      )}

      {/* Viral Shorts & Reels Auto-Clipper Modal */}
      {showShortsModal && (
        <div className="modal-backdrop" onClick={() => setShowShortsModal(false)}>
          <div className="modal-card" style={{ maxWidth: '480px' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Scissors size={22} color="var(--accent-rose)" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>9:16 Shorts & Reels Clipper</h3>
              </div>
              <button
                type="button"
                className="status-pill"
                style={{ cursor: 'pointer', background: 'transparent' }}
                onClick={() => setShowShortsModal(false)}
              >
                <X size={16} />
              </button>
            </div>

            {shortGeneratedUrl ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', alignItems: 'center' }}>
                <div style={{ fontSize: '0.88rem', color: 'var(--accent-emerald)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CheckCircle size={18} /> Vertical Short Ready!
                </div>

                <video
                  src={shortGeneratedUrl}
                  controls
                  autoPlay
                  className="shorts-video-preview"
                />

                <div style={{ display: 'flex', gap: '10px', width: '100%' }}>
                  <a
                    href={shortGeneratedUrl}
                    download="dubbed_short_9x16.mp4"
                    className="btn-primary"
                    style={{
                      flex: 1,
                      background: 'linear-gradient(135deg, var(--accent-rose), var(--accent-purple))',
                      textDecoration: 'none',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px'
                    }}
                  >
                    <Download size={18} /> Download Short (.MP4)
                  </a>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => setShortGeneratedUrl(null)}
                  >
                    Trim Again
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Automatically re-crop your video into a 9:16 vertical layout (1080x1920) with cinematic blurred padding and burned-in kinetic captions for YouTube Shorts, Instagram Reels, and TikTok.
                </p>

                {/* Start Time Controller */}
                <div className="input-group" style={{ marginBottom: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <label className="input-label" style={{ marginBottom: 0 }}>
                      <Clock size={14} color="var(--accent-cyan)" /> Clip Start Time
                    </label>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                      {Math.floor(shortsStartTime / 60)}:{(shortsStartTime % 60).toFixed(0).padStart(2, '0')} ({shortsStartTime}s)
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max={Math.max(1, Math.floor((videoPlayerDuration || jobData?.result?.video_duration || 60) - shortsDuration))}
                    step="1"
                    value={shortsStartTime}
                    onChange={(e) => setShortsStartTime(Number(e.target.value))}
                    style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
                  />
                </div>

                {/* Duration Presets */}
                <div>
                  <label className="input-label" style={{ marginBottom: '6px' }}>
                    Target Short Duration
                  </label>
                  <div className="shorts-preset-pills">
                    {[
                      { sec: 15, label: '15s (Stories)' },
                      { sec: 30, label: '30s (Reels)' },
                      { sec: 60, label: '60s (Shorts)' },
                    ].map((p) => (
                      <button
                        key={p.sec}
                        type="button"
                        className={`shorts-preset-pill ${shortsDuration === p.sec ? 'active' : ''}`}
                        onClick={() => setShortsDuration(p.sec)}
                      >
                        {p.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Window Preview Banner */}
                <div style={{
                  background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px',
                  fontSize: '0.82rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span style={{ color: 'var(--text-muted)' }}>Trim Window:</span>
                  <strong style={{ color: 'var(--text-primary)' }}>
                    {shortsStartTime}s → {shortsStartTime + shortsDuration}s ({shortsDuration}s Total)
                  </strong>
                </div>

                {shortError && (
                  <div style={{ color: 'var(--accent-rose)', fontSize: '0.82rem', background: 'rgba(244, 63, 94, 0.15)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
                    {shortError}
                  </div>
                )}

                <button
                  type="button"
                  className="btn-primary"
                  onClick={handleGenerateShort}
                  disabled={isGeneratingShort}
                  style={{
                    background: 'linear-gradient(135deg, var(--accent-rose), var(--accent-purple))',
                    boxShadow: '0 4px 15px rgba(244, 63, 94, 0.3)',
                    gap: '8px'
                  }}
                >
                  {isGeneratingShort ? (
                    <>
                      <RefreshCw size={17} className="spin" /> Rendering 9:16 Short & Captions...
                    </>
                  ) : (
                    <>
                      <Scissors size={17} /> Render 9:16 Vertical Short
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
