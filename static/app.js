/**
 * PM-AJAY AI Livelihood Guidance Assistant
 * Frontend Controller: Voice-First ASR/TTS, Facilitator Mode, IVR Simulator, Admin Dashboard
 */

// Application State
const state = {
  sessionId: null,
  entryMode: 'app', // 'app', 'call', 'facilitator'
  language: 'hi',
  isRecording: false,
  recognition: null,
  profileComplete: false,
  currentRecommendation: null,
  ivrActive: false,
  ivrDialed: '',
  ivrStep: 0
};

// Language Locales Map for Web Speech API
const LANG_LOCALES = {
  hi: 'hi-IN',
  mr: 'mr-IN',
  pa: 'pa-IN',
  ta: 'ta-IN',
  en: 'en-IN'
};

// Initial Greeting Prompts by Language
const INITIAL_PROMPTS = {
  hi: "नमस्ते! आप अपने बारे में बताएं — आपकी पढ़ाई कितनी हुई है, और आप किस तरह का काम सीखना या करना चाहते हैं?",
  mr: "नमस्कार! तुमच्याबद्दल सांगा — तुमचे शिक्षण किती झाले आहे आणि तुम्हाला कोणत्या प्रकारचे काम शिकायला आवडेल?",
  pa: "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਆਪਣੇ ਬਾਰੇ ਦੱਸੋ — ਤੁਹਾਡੀ ਪੜ੍ਹਾਈ ਕਿੰਨੀ ਹੈ ਅਤੇ ਤੁਸੀਂ ਕਿਸ ਤਰ੍ਹਾਂ ਦਾ ਕੰਮ ਸਿੱਖਣਾ ਚਾਹੁੰਦੇ ਹੋ?",
  ta: "வணக்கம்! உங்களைப் பற்றி கூறுங்கள் — உங்கள் கல்வித்தகுதி என்ன, என்ன வேலை செய்ய விரும்புகிறீர்கள்?",
  en: "Welcome! Please tell me about yourself — what is your education level, and what kind of work interests you?"
};

// Localized Demo Utterance Scenarios (Does NOT change active language)
const DEMO_SCENARIOS = [
  {
    icon: '🌾',
    id: 'food_processing',
    labels: {
      en: '10th Pass + Farming Family + Food Processing + Low Mobility (Demo Script)',
      hi: '10वीं पास + किसान परिवार + खाद्य प्रसंस्करण + सीमित गतिशीलता',
      mr: '१०वी पास + शेतकरी कुटुंब + अन्न प्रक्रिया + गावातच काम',
      pa: '10ਵੀਂ ਪਾਸ + ਕਿਸਾਨ ਪਰਿਵਾਰ + ਫੂਡ ਪ੍ਰੋਸੈਸਿੰਗ + ਪਿੰਡ ਵਿੱਚ ਕੰਮ',
      ta: '10வது தேர்ச்சி + விவசாய குடும்பம் + உணவு பதப்படுத்துதல்'
    },
    texts: {
      en: "I finished 10th, my family does farming, I want something food-related, I can't travel far",
      hi: "मैंने 10वीं पास की है, मेरा परिवार खेती करता है, मुझे खाने से जुड़ा काम सीखना है और मैं गाँव से दूर नहीं जा सकता",
      mr: "मी १०वी पास आहे, माझे कुटुंब शेती करते, मला अन्न प्रक्रियेशी संबंधित काम शिकायचे आहे आणि मी जास्त लांब जाऊ शकत नाही",
      pa: "ਮੈਂ ਦਸਵੀਂ ਪਾਸ ਹਾਂ, ਮੇਰਾ ਪਰਿਵਾਰ ਖੇਤੀ ਕਰਦਾ ਹੈ, ਮੈਨੂੰ ਫੂਡ ਪ੍ਰੋਸੈਸਿੰਗ ਦਾ ਕੰਮ ਸਿੱਖਣਾ ਹੈ ਅਤੇ ਮੈਂ ਦੂਰ ਨਹੀਂ ਜਾ ਸਕਦਾ",
      ta: "நான் 10வது முடித்துள்ளேன், எங்கள் குடும்பம் விவசாயம் செய்கிறது, உணவு சார்ந்த தொழில் செய்ய விரும்புகிறேன், தூரம் செல்ல முடியாது"
    }
  },
  {
    icon: '🧵',
    id: 'tailoring',
    labels: {
      en: '8th Pass + Tailoring & Garments + Self-Employment',
      hi: '8वीं पास + सिलाई व परिधान + खुद की दुकान',
      mr: '८वी पास + शिलाई काम + स्वतःचे दुकान',
      pa: '8ਵੀਂ ਪਾਸ + ਸਿਲਾਈ ਅਤੇ ਆਪਣੀ ਦੁਕਾਨ',
      ta: '8வது தேர்ச்சி + தையல் தொழில் + சொந்த தொழில்'
    },
    texts: {
      en: "I passed 8th, I want to learn tailoring and open my own shop in my village",
      hi: "मुझे सिलाई का काम सीखना है, खुद की दुकान खोलनी है, 8वीं पास हूँ",
      mr: "मला शिलाई काम शिकायचे आहे, स्वतःचे दुकान सुरू करायचे आहे, ८वी पास आहे",
      pa: "ਮੈਂ ਅੱਠਵੀਂ ਪਾਸ ਹਾਂ, ਮੈਨੂੰ ਸਿਲਾਈ ਦਾ ਕੰਮ ਸਿੱਖਣਾ ਹੈ ਅਤੇ ਪਿੰਡ ਵਿੱਚ ਆਪਣੀ ਦੁਕਾਨ ਖੋਲ੍ਹਣੀ ਹੈ",
      ta: "நான் 8வது படித்துள்ளேன், தையல் தொழில் கற்றுக்கொண்டு சொந்த கடை வைக்க விரும்புகிறேன்"
    }
  },
  {
    icon: '☀️',
    id: 'solar',
    labels: {
      en: '12th Pass + Solar PV Suryamitra + Commute OK',
      hi: '12वीं पास + सोलर सूर्यमित्र + शहर जा सकते हैं',
      mr: '१२वी पास + सोलर सूर्यमित्र + तालुक्यात जाऊ शकतो',
      pa: '12ਵੀਂ ਪਾਸ + ਸੋਲਰ ਪੈਨਲ ਸਿਖਲਾਈ',
      ta: '12வது தேர்ச்சி + சோலார் தொழில்நுட்பம்'
    },
    texts: {
      en: "I passed 12th, want to learn solar panel installation and electrical work, can commute to district",
      hi: "मैंने 12वीं पास की है, मुझे सोलर पैनल और बिजली वायरिंग का काम सीखना है, शहर जा सकता हूँ",
      mr: "मी १२वी पास आहे, मला सोलर पॅनेल आणि वायरिंगचे काम शिकायचे आहे, तालुक्यात जाऊ शकतो",
      pa: "ਮੈਂ ਬਾਰ੍ਹਵੀਂ ਪਾਸ ਹਾਂ, ਮੈਨੂੰ ਸੋਲਰ ਪੈਨਲ ਅਤੇ ਵਾਇਰਿੰਗ ਦਾ ਕੰਮ ਸਿੱਖਣਾ ਹੈ",
      ta: "நான் 12வது முடித்துள்ளேன், சோலਾਰ பேனல் பொருத்தும் வேலை கற்க விரும்புகிறேன்"
    }
  },
  {
    icon: '💻',
    id: 'digital_csc',
    labels: {
      en: '10th Pass + Digital Services / CSC Operator',
      hi: '10वीं पास + डिजिटल सेवा ऑपरेटर / सीएससी केंद्र',
      mr: '१०वी पास + डिजिटल सेवा ऑपरेटर / सीएससी केंद्र',
      pa: '10ਵੀਂ ਪਾਸ + ਡਿਜੀਟਲ ਸੇਵਾਵਾਂ / ਸੀਐਸਸੀ',
      ta: '10வது தேர்ச்சி + டிஜிட்டல் சேவை மையம்'
    },
    texts: {
      en: "I passed 10th, want to learn digital services and computer applications for citizen schemes",
      hi: "मैंने 10वीं पास की है, मुझे कंप्यूटर और डिजिटल सरकारी योजनाओं (सीएससी) का काम सीखना है",
      mr: "मी १०वी पास आहे, मला संगणक आणि डिजिटल शासकीय योजनांचे (सीएससी) काम शिकायचे आहे",
      pa: "ਮੈਂ ਦਸਵੀਂ ਪਾਸ ਹਾਂ, ਮੈਨੂੰ ਕੰਪਿਊਟਰ ਅਤੇ ਸਰਕਾਰੀ ਸਕੀਮਾਂ ਦਾ ਕੰਮ ਸਿੱਖਣਾ ਹੈ",
      ta: "நான் 10வது முடித்துள்ளேன், கணினி மற்றும் அரசு டிஜிட்டல் திட்ட பணிகளை கற்க விரும்புகிறேன்"
    }
  }
];

// DOM Elements
const elements = {
  // Tabs & Views
  tabApp: document.getElementById('tabApp'),
  tabIvr: document.getElementById('tabIvr'),
  tabAdmin: document.getElementById('tabAdmin'),
  viewVoiceApp: document.getElementById('viewVoiceApp'),
  viewIvr: document.getElementById('viewIvr'),
  viewAdmin: document.getElementById('viewAdmin'),

  // Language & Mode
  langSelect: document.getElementById('langSelect'),
  facilitatorBanner: document.getElementById('facilitatorBanner'),
  btnStartFacilitator: document.getElementById('btnStartFacilitator'),
  btnExitFacilitator: document.getElementById('btnExitFacilitator'),
  btnResetSession: document.getElementById('btnResetSession'),

  // Mic & Speech UI
  dominantMicBtn: document.getElementById('dominantMicBtn'),
  micStage: document.querySelector('.mic-stage'),
  micLabel: document.getElementById('micLabel'),
  micIcon: document.getElementById('micIcon'),
  waveformVisualizer: document.getElementById('waveformVisualizer'),
  liveTranscriptText: document.getElementById('liveTranscriptText'),
  assistantSpeechText: document.getElementById('assistantSpeechText'),
  btnReplayAudio: document.getElementById('btnReplayAudio'),
  audioStatusPill: document.getElementById('audioStatusPill'),
  statusText: document.getElementById('statusText'),

  // Signals
  sigEducation: document.getElementById('sigEducation'),
  sigFamilyOcc: document.getElementById('sigFamilyOcc'),
  sigSkills: document.getElementById('sigSkills'),
  sigMobility: document.getElementById('sigMobility'),
  sigPref: document.getElementById('sigPref'),
  sigEntryMode: document.getElementById('sigEntryMode'),
  signalsBadge: document.getElementById('signalsBadge'),

  // Roadmap
  roadmapContainer: document.getElementById('roadmapContainer'),
  recNsqfBadge: document.getElementById('recNsqfBadge'),
  recTradeTitle: document.getElementById('recTradeTitle'),
  recGapSummary: document.getElementById('recGapSummary'),
  recSpokenSummaryText: document.getElementById('recSpokenSummaryText'),
  btnPlayRoadmapAudio: document.getElementById('btnPlayRoadmapAudio'),
  step1Title: document.getElementById('step1Title'),
  step1Desc: document.getElementById('step1Desc'),
  step2Title: document.getElementById('step2Title'),
  step2Desc: document.getElementById('step2Desc'),
  step3Title: document.getElementById('step3Title'),
  step3Desc: document.getElementById('step3Desc'),
  step4Title: document.getElementById('step4Title'),
  step4Desc: document.getElementById('step4Desc'),
  btnPrintRoadmap: document.getElementById('btnPrintRoadmap'),
  btnSmsRoadmap: document.getElementById('btnSmsRoadmap'),
  btnNewRoadmapAssessment: document.getElementById('btnNewRoadmapAssessment'),

  // IVR Simulator
  lcdPrompt: document.getElementById('lcdPrompt'),
  lcdDialed: document.getElementById('lcdDialed'),
  lcdAudioStatus: document.getElementById('lcdAudioStatus'),
  lcdTime: document.getElementById('lcdTime'),
  keyCall: document.getElementById('keyCall'),
  keyEnd: document.getElementById('keyEnd'),

  // Admin Dashboard
  districtSelect: document.getElementById('districtSelect'),
  btnRefreshDashboard: document.getElementById('btnRefreshDashboard'),
  valEnrolments: document.getElementById('valEnrolments'),
  valPlacements: document.getElementById('valPlacements'),
  valDropouts: document.getElementById('valDropouts'),
  valTotalBeneficiaries: document.getElementById('valTotalBeneficiaries'),
  demandBarsContainer: document.getElementById('demandBarsContainer'),
  beneficiaryTableBody: document.getElementById('beneficiaryTableBody'),
  beneficiaryCountTag: document.getElementById('beneficiaryCountTag'),

  // Toast
  toast: document.getElementById('toastNotification'),
  toastMessage: document.getElementById('toastMessage')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initSpeechRecognition();
  bindEvents();
  startNewSession();
  updateClock();
  setInterval(updateClock, 1000);
});

// Clock for IVR LCD
function updateClock() {
  if (elements.lcdTime) {
    const now = new Date();
    elements.lcdTime.textContent = now.toTimeString().substring(0, 5);
  }
}

// -------------------------------------------------------------
// Session Management
// -------------------------------------------------------------
async function startNewSession(entryMode = null, language = null) {
  if (entryMode) state.entryMode = entryMode;
  if (language) state.language = language;

  elements.langSelect.value = state.language;
  elements.sigEntryMode.textContent = 
    state.entryMode === 'facilitator' ? 'Facilitator Assisted (Doorstep)' :
    state.entryMode === 'call' ? 'Button Phone (IVR Line)' : 'Smartphone (App Direct)';

  if (state.entryMode === 'facilitator') {
    elements.facilitatorBanner.classList.remove('hidden');
  } else {
    elements.facilitatorBanner.classList.add('hidden');
  }

  // Hide roadmap on reset
  elements.roadmapContainer.classList.add('hidden');
  state.profileComplete = false;
  state.currentRecommendation = null;
  resetSignalDisplay();
  renderDemoChips();

  try {
    const res = await fetch('/session/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        entry_mode: state.entryMode,
        language: state.language
      })
    });
    const data = await res.json();
    state.sessionId = data.session_id;

    const prompt = data.initial_prompt || INITIAL_PROMPTS[state.language] || INITIAL_PROMPTS.en;
    setAssistantSpeech(prompt);
  } catch (err) {
    console.error('Session start error:', err);
    state.sessionId = 'local-' + Date.now();
    setAssistantSpeech(INITIAL_PROMPTS[state.language] || INITIAL_PROMPTS.en);
  }
}

function resetSignalDisplay() {
  elements.sigEducation.textContent = '—';
  elements.sigFamilyOcc.textContent = '—';
  elements.sigSkills.textContent = '—';
  elements.sigMobility.textContent = '—';
  elements.sigPref.textContent = '—';
  elements.signalsBadge.textContent = 'Intake In Progress';
  elements.signalsBadge.classList.remove('complete');
  elements.liveTranscriptText.textContent = 'Press the mic button or choose a sample prompt below to start...';
}

function renderDemoChips() {
  const container = document.querySelector('.chips-list');
  if (!container) return;
  const lang = state.language || 'hi';
  container.innerHTML = '';

  DEMO_SCENARIOS.forEach(scenario => {
    const btn = document.createElement('button');
    btn.className = 'demo-chip';
    const label = scenario.labels[lang] || scenario.labels.en;
    const textToSend = scenario.texts[lang] || scenario.texts.en;
    btn.innerHTML = `${scenario.icon} ${label}`;
    btn.setAttribute('data-text', textToSend);
    btn.setAttribute('title', textToSend);
    btn.addEventListener('click', () => {
      // Intentionally preserves state.language and elements.langSelect without toggling!
      handleUserVoiceUtterance(textToSend);
    });
    container.appendChild(btn);
  });
}

function setAssistantSpeech(text, autoPlay = true) {
  elements.assistantSpeechText.textContent = `"${text}"`;
  if (autoPlay) {
    speakText(text, state.language);
  }
}

// -------------------------------------------------------------
// Speech Synthesis (TTS) & ASR (Speech Recognition)
// -------------------------------------------------------------
function speakText(text, lang = 'en') {
  if (!('speechSynthesis' in window)) return;

  // Stop any ongoing speech
  window.speechSynthesis.cancel();

  const cleanText = text.replace(/[#*]/g, '');
  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.lang = LANG_LOCALES[lang] || 'en-IN';
  utterance.rate = 0.95; // Slightly slower for low literacy clarity
  utterance.pitch = 1.0;

  elements.waveformVisualizer.classList.add('active');
  elements.statusText.textContent = 'Speaking...';

  utterance.onend = () => {
    elements.waveformVisualizer.classList.remove('active');
    elements.statusText.textContent = 'Voice Ready • Tap to Speak';
  };

  utterance.onerror = () => {
    elements.waveformVisualizer.classList.remove('active');
    elements.statusText.textContent = 'Voice Ready • Tap to Speak';
  };

  window.speechSynthesis.speak(utterance);
}

function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn('Web Speech API not supported in this browser; fallback chips enabled.');
    return;
  }

  state.recognition = new SpeechRecognition();
  state.recognition.continuous = false;
  state.recognition.interimResults = true;

  state.recognition.onstart = () => {
    state.isRecording = true;
    elements.micStage.classList.add('recording');
    elements.waveformVisualizer.classList.add('active');
    elements.micLabel.textContent = 'Listening...';
    elements.statusText.textContent = 'Listening to Beneficiary...';
  };

  state.recognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      transcript += event.results[i][0].transcript;
    }
    elements.liveTranscriptText.textContent = transcript;
    if (event.results[0].isFinal) {
      handleUserVoiceUtterance(transcript);
    }
  };

  state.recognition.onerror = (event) => {
    console.warn('Speech recognition error:', event.error);
    stopRecording();
    showToast('Microphone note: ' + event.error);
  };

  state.recognition.onend = () => {
    stopRecording();
  };
}

function toggleRecording() {
  if (!state.recognition) {
    // If browser doesn't have microphone permission or speech api, simulate realistic prompt
    showToast('Simulating voice input for demo environment');
    handleUserVoiceUtterance("I finished 10th, my family does farming, I want something food-related, I can't travel far");
    return;
  }

  if (state.isRecording) {
    state.recognition.stop();
  } else {
    // Stop any speech playing first
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    
    state.recognition.lang = LANG_LOCALES[state.language] || 'en-IN';
    try {
      state.recognition.start();
    } catch (e) {
      console.warn('Start recognition error:', e);
      state.recognition.stop();
    }
  }
}

function stopRecording() {
  state.isRecording = false;
  elements.micStage.classList.remove('recording');
  elements.waveformVisualizer.classList.remove('active');
  elements.micLabel.textContent = 'Tap & Speak';
  elements.statusText.textContent = 'Voice Ready • Tap to Speak';
}

// -------------------------------------------------------------
// Voice Input API Pipeline: POST /session/{id}/voice-input
// -------------------------------------------------------------
async function handleUserVoiceUtterance(utteranceText) {
  if (!utteranceText || !utteranceText.trim()) return;

  elements.liveTranscriptText.textContent = utteranceText;
  elements.statusText.textContent = 'Analyzing Voice Signals...';

  try {
    const res = await fetch(`/session/${state.sessionId}/voice-input`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transcript: utteranceText,
        language: state.language
      })
    });

    const data = await res.json();
    
    // Update Extracted Signals in Real-Time
    updateSignalsView(data.extracted_fields);

    // Speak Assistant Next Prompt
    setAssistantSpeech(data.next_prompt, true);

    // If profile is complete, fetch and display Livelihood Roadmap!
    if (data.profile_complete) {
      state.profileComplete = true;
      elements.signalsBadge.textContent = '✅ Profile Complete';
      elements.signalsBadge.classList.add('complete');
      setTimeout(() => {
        loadRoadmapRecommendation();
      }, 1200);
    }

  } catch (err) {
    console.error('Error submitting voice input:', err);
    showToast('Failed to process voice input');
  }
}

function updateSignalsView(fields = {}) {
  if (fields.education_level) elements.sigEducation.textContent = fields.education_level;
  if (fields.family_occupation) elements.sigFamilyOcc.textContent = fields.family_occupation;
  if (fields.skills && fields.skills.length > 0) {
    elements.sigSkills.textContent = fields.skills.join(', ');
  } else if (fields.interests && fields.interests.length > 0) {
    elements.sigSkills.textContent = fields.interests.join(', ');
  }
  if (fields.mobility_constraint) elements.sigMobility.textContent = fields.mobility_constraint;
  if (fields.employment_preference) {
    elements.sigPref.textContent = fields.employment_preference === 'self_employment' ? 'Self-Employment / Own Shop' : 'Wage / Salaried Job';
  }
}

// -------------------------------------------------------------
// Recommendation Engine: GET /session/{id}/recommendation
// -------------------------------------------------------------
async function loadRoadmapRecommendation() {
  try {
    const res = await fetch(`/session/${state.sessionId}/recommendation`);
    if (!res.ok) {
      showToast("Please finish answering first");
      return;
    }
    const data = await res.json();
    state.currentRecommendation = data;

    renderRoadmap(data);
  } catch (err) {
    console.error('Error fetching recommendation:', err);
  }
}

function renderRoadmap(rec) {
  elements.recTradeTitle.textContent = rec.recommended_trade;
  elements.recNsqfBadge.textContent = rec.nsqf_alignment;
  elements.recGapSummary.textContent = rec.gap_summary;
  elements.recSpokenSummaryText.textContent = `"${rec.spoken_summary}"`;

  // Render 4-step sequence
  const steps = rec.roadmap_steps || [];
  if (steps[0]) {
    elements.step1Title.textContent = steps[0].split('(')[0];
    elements.step1Desc.textContent = steps[0];
  }
  if (steps[1]) {
    elements.step2Title.textContent = rec.training_centre || steps[1].split('with')[0];
    elements.step2Desc.textContent = steps[1];
  }
  if (steps[2]) {
    elements.step3Title.textContent = rec.nsqf_alignment + ' Certification';
    elements.step3Desc.textContent = steps[2];
  }
  if (steps[3]) {
    elements.step4Title.textContent = 'Local Livelihood Linkage';
    elements.step4Desc.textContent = rec.local_opportunity || steps[3];
  }

  elements.roadmapContainer.classList.remove('hidden');
  elements.roadmapContainer.scrollIntoView({ behavior: 'smooth' });

  // Play Spoken Summary Audio
  setTimeout(() => {
    speakText(rec.spoken_summary, state.language);
  }, 600);
}

// -------------------------------------------------------------
// Interactive Feature Phone IVR Simulator
// -------------------------------------------------------------
function handleKeypadPress(digit) {
  if (!state.ivrActive) {
    state.ivrDialed += digit;
    elements.lcdDialed.textContent = state.ivrDialed;
    return;
  }

  // Active Call Menu Logic
  if (digit === '1') {
    elements.lcdPrompt.textContent = "भाषा: हिंदी। अपनी शिक्षा और रुचि बताएं...";
    speakText("नमस्ते। आप कौन सा काम सीखना चाहते हैं? खेती, सिलाई, सोलर या अन्य?", 'hi');
  } else if (digit === '2') {
    elements.lcdPrompt.textContent = "भाषा: मराठी. तुमचे शिक्षण व कामाची आवड सांगा...";
    speakText("नमस्कार. तुम्हाला कोणते काम शिकायचे आहे? शेती प्रक्रिया, टेलरिंग, की सोलर?", 'mr');
  } else if (digit === '3') {
    elements.lcdPrompt.textContent = "ਭਾਸ਼ਾ: ਪੰਜਾਬੀ। ਆਪਣੀ ਪੜ੍ਹਾਈ ਅਤੇ ਰੁਚੀ ਦੱਸੋ...";
    speakText("ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ। ਤੁਸੀਂ ਕਿਹੜਾ ਕੰਮ ਸਿੱਖਣਾ ਚਾਹੁੰਦੇ ਹੋ?", 'pa');
  } else if (digit === '4') {
    elements.lcdPrompt.textContent = "Trade Selected: Food Processing. Center: Pune JSS Hub.";
    speakText("आपका नामांकन पीएम-अजय फूड प्रोसेसिंग में दर्ज किया गया है। नजदीकी केंद्र जन शिक्षण संस्थान है।", 'hi');
  }
}

function startIvrCall() {
  state.ivrActive = true;
  elements.lcdAudioStatus.textContent = "CALL CONNECTED • 00:01";
  elements.lcdPrompt.textContent = "Welcome to PM-AJAY IVR Helpline.\nPress 1 for Hindi, 2 for Marathi, 3 for Punjabi.";
  speakText("Welcome to PM-AJAY Toll Free Voice Helpline. For Hindi press 1. Marathi sathi 2 daba. Punjabi lai 3 dabao.", 'en');
}

function endIvrCall() {
  state.ivrActive = false;
  state.ivrDialed = '';
  elements.lcdDialed.textContent = '';
  elements.lcdAudioStatus.textContent = "CALL ENDED";
  elements.lcdPrompt.textContent = "Call disconnected. Dial 1800-11-7625 or tap Call.";
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
}

// -------------------------------------------------------------
// Admin Dashboard: GET /dashboard/summary?district=
// -------------------------------------------------------------
async function loadAdminDashboard() {
  const district = elements.districtSelect.value;
  try {
    const res = await fetch(`/dashboard/summary?district=${encodeURIComponent(district)}`);
    const data = await res.json();

    // Stats
    elements.valEnrolments.textContent = data.enrolments;
    elements.valPlacements.textContent = data.placements;
    elements.valDropouts.textContent = data.dropouts;
    elements.valTotalBeneficiaries.textContent = data.total_beneficiaries;
    elements.beneficiaryCountTag.textContent = `${data.total_beneficiaries} Records`;

    // Demand Breakdown Bars
    renderDemandBars(data.skill_demand_by_trade);

    // Beneficiary Table
    renderBeneficiaryTable(data.beneficiaries);

  } catch (err) {
    console.error('Error fetching admin dashboard:', err);
  }
}

function renderDemandBars(trades = []) {
  elements.demandBarsContainer.innerHTML = '';
  if (!trades.length) {
    elements.demandBarsContainer.innerHTML = '<p class="text-muted">No trade demands registered yet.</p>';
    return;
  }

  const maxVal = Math.max(...trades.map(t => t.count), 1);

  trades.forEach(t => {
    const percentage = Math.round((t.count / maxVal) * 100);
    const item = document.createElement('div');
    item.className = 'demand-bar-item';
    item.innerHTML = `
      <div class="bar-meta">
        <span>${t.trade}</span>
        <span>${t.count} Beneficiaries (${percentage}%)</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width: ${percentage}%"></div>
      </div>
    `;
    elements.demandBarsContainer.appendChild(item);
  });
}

function renderBeneficiaryTable(list = []) {
  elements.beneficiaryTableBody.innerHTML = '';
  if (!list.length) {
    elements.beneficiaryTableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:1.5rem;">No beneficiaries found for this filter.</td></tr>';
    return;
  }

  list.forEach(b => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${b.name}</strong><br><small style="color:var(--text-dim);">${b.education}</small></td>
      <td>${b.location}</td>
      <td><span style="color:var(--saffron-light); font-weight:600;">${b.trade}</span></td>
      <td><span class="signals-badge">${b.entry_mode.toUpperCase()}</span></td>
      <td><span class="status-badge status-${b.status}">${b.status}</span></td>
      <td>
        <select class="status-select-inline" data-id="${b.id}">
          <option value="enrolled" ${b.status === 'enrolled' ? 'selected' : ''}>Enrolled</option>
          <option value="placed" ${b.status === 'placed' ? 'selected' : ''}>Placed</option>
          <option value="dropped" ${b.status === 'dropped' ? 'selected' : ''}>Dropped</option>
          <option value="no_contact" ${b.status === 'no_contact' ? 'selected' : ''}>No Contact</option>
        </select>
      </td>
    `;
    elements.beneficiaryTableBody.appendChild(tr);
  });

  // Attach status change events: POST /followup/{beneficiary_id}
  document.querySelectorAll('.status-select-inline').forEach(select => {
    select.addEventListener('change', async (e) => {
      const bId = e.target.getAttribute('data-id');
      const newStatus = e.target.value;
      try {
        const res = await fetch(`/followup/${bId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
          showToast(`Beneficiary status updated to ${newStatus}`);
          loadAdminDashboard();
        }
      } catch (err) {
        showToast('Failed to update status');
      }
    });
  });
}

// -------------------------------------------------------------
// Event Bindings
// -------------------------------------------------------------
function bindEvents() {
  // Navigation Tabs
  elements.tabApp.addEventListener('click', () => switchTab('voice-app'));
  elements.tabIvr.addEventListener('click', () => switchTab('ivr-view'));
  elements.tabAdmin.addEventListener('click', () => {
    switchTab('admin-view');
    loadAdminDashboard();
  });

  // Mic Button
  elements.dominantMicBtn.addEventListener('click', toggleRecording);

  // Audio Replay Button
  elements.btnReplayAudio.addEventListener('click', () => {
    const text = elements.assistantSpeechText.textContent.replace(/"/g, '');
    speakText(text, state.language);
  });

  // Language Dropdown
  elements.langSelect.addEventListener('change', (e) => {
    startNewSession(state.entryMode, e.target.value);
  });

  // Demo chips are rendered dynamically without altering active language
  renderDemoChips();

  // Facilitator Handoff Button (Section 6, Screen 4)
  elements.btnStartFacilitator.addEventListener('click', () => {
    startNewSession('facilitator', state.language);
    showToast('Switched to Facilitator Mode: Zero-friction intake for rural citizen');
  });

  elements.btnExitFacilitator.addEventListener('click', () => {
    startNewSession('app', state.language);
    showToast('Switched back to Smartphone Self-Mode');
  });

  elements.btnResetSession.addEventListener('click', () => {
    startNewSession(state.entryMode, state.language);
    showToast('Conversation reset');
  });

  // Roadmap Actions
  elements.btnPlayRoadmapAudio.addEventListener('click', () => {
    if (state.currentRecommendation && state.currentRecommendation.spoken_summary) {
      speakText(state.currentRecommendation.spoken_summary, state.language);
    }
  });

  elements.btnPrintRoadmap.addEventListener('click', () => {
    window.print();
  });

  elements.btnSmsRoadmap.addEventListener('click', () => {
    showToast('📲 SMS Roadmap & JSS Training Hub details dispatched to beneficiary mobile!');
  });

  elements.btnNewRoadmapAssessment.addEventListener('click', () => {
    startNewSession(state.entryMode, state.language);
    elements.viewVoiceApp.scrollIntoView({ behavior: 'smooth' });
  });

  // IVR Simulator Keypad
  document.querySelectorAll('.keypad-btn[data-key]').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.getAttribute('data-key');
      handleKeypadPress(key);
    });
  });

  elements.keyCall.addEventListener('click', startIvrCall);
  elements.keyEnd.addEventListener('click', endIvrCall);

  // Admin Dashboard Controls
  elements.districtSelect.addEventListener('change', loadAdminDashboard);
  elements.btnRefreshDashboard.addEventListener('click', loadAdminDashboard);
}

function switchTab(viewId) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));

  if (viewId === 'voice-app') {
    elements.tabApp.classList.add('active');
    elements.viewVoiceApp.classList.add('active');
  } else if (viewId === 'ivr-view') {
    elements.tabIvr.classList.add('active');
    elements.viewIvr.classList.add('active');
  } else if (viewId === 'admin-view') {
    elements.tabAdmin.classList.add('active');
    elements.viewAdmin.classList.add('active');
  }
}

function showToast(msg) {
  elements.toastMessage.textContent = msg;
  elements.toast.classList.remove('hidden');
  setTimeout(() => {
    elements.toast.classList.add('hidden');
  }, 3500);
}
