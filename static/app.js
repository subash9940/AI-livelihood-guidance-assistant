/**
 * Nivara — AI Livelihood Guidance Assistant
 * Frontend Controller: Voice-First ASR/TTS, Stitch AI Responsive Multi-Screen Layout,
 * Real-time Skill Gap Breakdown, Regional Schemes Directory, Feature Phone IVR Simulator, District Admin Dashboard.
 */

// Application State
const state = {
  sessionId: null,
  entryMode: 'app', // 'app', 'facilitator', 'call'
  language: 'en', // Default to English for intuitive demo testing & reliable browser speech
  isRecording: false,
  recognition: null,
  profileComplete: false,
  currentRecommendation: null,
  activeTab: 'viewVoiceApp',
  beneficiaryProfile: null,
  profile: null,
  selectedCapacityState: 'Delhi',
  ivrActive: true,
  ivrTimer: 42,
  ivrInterval: null,
  audioPlaying: false,
  audioInterval: null
};

// Regional Language Locales Map for Web Speech API
const LANG_LOCALES = {
  en: 'en-IN',
  hi: 'hi-IN',
  mr: 'mr-IN',
  pa: 'pa-IN',
  ta: 'ta-IN'
};

// -------------------------------------------------------------
// Voice Cache & User-Gesture Unlocking Subsystem
// -------------------------------------------------------------
let cachedVoices = [];
let isAudioUnlocked = false;

function refreshVoices() {
  if (!('speechSynthesis' in window)) return;
  const v = window.speechSynthesis.getVoices();
  if (v && v.length) cachedVoices = v;
}

if ('speechSynthesis' in window) {
  refreshVoices();
  window.speechSynthesis.onvoiceschanged = refreshVoices;
}

/**
 * Prime & unlock browser speech synthesis & HTML5 Audio synchronously
 * off an active user gesture (tap/click/touch) to bypass Chrome autoplay blocks.
 */
function unlockSpeechAndAudio() {
  if (isAudioUnlocked) return;
  isAudioUnlocked = true;

  if ('speechSynthesis' in window) {
    try {
      window.speechSynthesis.resume();
      // Synchronous silent primer utterance inside user gesture chain
      const primer = new SpeechSynthesisUtterance('');
      primer.volume = 0;
      primer.rate = 10;
      window.speechSynthesis.speak(primer);
    } catch (e) {
      console.warn('SpeechSynthesis unlock note:', e);
    }
  }

  try {
    const silentAudio = new Audio('data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQQAAAAAAP8A');
    silentAudio.volume = 0;
    silentAudio.play().then(() => silentAudio.pause()).catch(() => {});
  } catch (e) {}
}

// Global passive unlock on first user interaction
['click', 'touchstart', 'keydown'].forEach(evt => {
  document.addEventListener(evt, unlockSpeechAndAudio, { passive: true, once: true });
});

// Initial Greeting Prompts by Language
const INITIAL_PROMPTS = {
  hi: "नमस्ते! आप अपने बारे में बताएं — आपकी पढ़ाई कितनी हुई है, और आप किस तरह का काम सीखना या करना चाहते हैं?",
  mr: "नमस्कार! तुमच्याबद्दल सांगा — तुमचे शिक्षण किती झाले आहे आणि तुम्हाला कोणत्या प्रकारचे काम शिकायला आवडेल?",
  pa: "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਆਪਣੇ ਬਾਰੇ ਦੱਸੋ — ਤੁਹਾਡੀ ਪੜ੍ਹਾਈ ਕਿੰਨੀ ਹੈ ਅਤੇ ਤੁਸੀਂ ਕਿਸ ਤਰ੍ਹਾਂ ਦਾ ਕੰਮ ਸਿੱਖਣਾ ਚਾਹੁੰਦੇ ਹੋ?",
  ta: "வணக்கம்! உங்களைப் பற்றி கூறுங்கள் — உங்கள் கல்வித்தகுதி என்ன, என்ன வேலை செய்ய விரும்புகிறீர்கள்?",
  en: "Welcome! Please tell me about yourself — what is your education level, and what kind of work interests you?"
};

const INITIAL_PROMPTS_SUB = {
  hi: "Hello! Please share about yourself — your education, skills, and what kind of livelihood or trade you wish to pursue.",
  mr: "Hello! Share your education level and what vocational trade interests you.",
  pa: "Hello! Tell us about your education and vocational aspirations.",
  ta: "Hello! Share your education and career aspirations under PM-AJAY.",
  en: "Nivara Free Vocational Training & Direct Placement Linkage Assistant."
};

// Trade Sector Icon Mappings for Material Symbols
const TRADE_ICONS = {
  food_processing: 'agriculture',
  apparel_tailoring: 'checkroom',
  solar_technician: 'solar_power',
  automotive_ev: 'electric_car',
  healthcare_assistant: 'medical_services',
  digital_csc: 'devices'
};

const TRADE_ICONS_EMOJI = {
  food_processing: '🌾',
  apparel_tailoring: '🧵',
  solar_technician: '☀️',
  automotive_ev: '🛵',
  healthcare_assistant: '🏥',
  digital_csc: '💻'
};

// Interactive IVR Phone Keypad Voice Responses
const IVR_RESPONSES = {
  '1': {
    title: 'हिंदी चयनित',
    prompt: '"हिंदी चुनी गई। पीएम-अजय कौशल्य प्रशिक्षण के लिए 1, व्यवसाय अनुदान (₹50,000) के लिए 2, स्थिति के लिए 3 दबाएं।"'
  },
  '2': {
    title: 'मराठी निवडली',
    prompt: '"मराठी भाषा निवडली. स्वयंरोजगार अनुदानासाठी 1 दाबा, कौशल्य केंद्रासाठी 2 दाबा."'
  },
  '3': {
    title: 'ਪੰਜਾਬੀ ਚੁਣੀ',
    prompt: '"ਪੰਜਾਬੀ ਚੁਣੀ ਗਈ। ਨਵੇਂ ਰੋਜ਼ਗਾਰ ਅਤੇ ਸਰਕਾਰੀ ਸਬਸਿਡੀ ਜਾਣਕਾਰੀ ਲਈ 1 ਦਬਾਓ।"'
  },
  '4': {
    title: 'தமிழ் தெரிவு',
    prompt: '"தமிழ் தேர்ந்தெடுக்கப்பட்டது. தொழில் வழிகாட்டுதலுக்கு 1-ஐ அழுத்தவும்."'
  },
  '5': {
    title: 'Special Track',
    prompt: '"अनुसूचित जाति कौशल्य विकास: निःशुल्क प्रशिक्षण और छात्रवृत्ति हेतु 1 दबाएं।"'
  },
  '6': {
    title: 'Status Check',
    prompt: '"आवेदन स्थिति: आपका आधार लिंक्ड बैंक खाता मान्य है। स्वीकृति पत्र शीघ्र उपलब्ध होगा।"'
  },
  '7': {
    title: 'Mitra Help',
    prompt: '"ग्राम मित्र अनुरोध दर्ज किया गया। आपके पंचायत केंद्र से 24 घंटे में संपर्क किया जाएगा।"'
  },
  '8': {
    title: 'SMS Sent',
    prompt: '"एसएमएस भेजा गया! आपके फोन पर नजदीकी कौशल्य केंद्र का पता व हेल्पलाइन विवरण प्रेषित हुआ।"'
  },
  '9': {
    title: 'Loan Grant',
    prompt: '"पीएम-अजय आजीविका अनुदान: अनुसूचित जाति वर्ग के लिए ₹50,000 तक 100% सब्सिडी स्वीकृत।"'
  },
  '*': {
    title: 'Replay Menu',
    prompt: '"मुख्य मेनू: 1 हिंदी, 2 मराठी, 3 ਪੰਜਾਬੀ, 4 தமிழ். कृपया विकल्प चुनें।"'
  },
  '0': {
    title: 'Officer Help',
    prompt: '"कृपया प्रतीक्षा करें, आपकी कॉल जिला समन्वयक अधिकारी को स्थानांतरित की जा रही है..."'
  },
  '#': {
    title: 'Confirmed',
    prompt: '"धन्यवाद! आपकी प्रविष्टि सुरक्षित है। संदर्भ संख्या: AJAY-2024-9812 दर्ज हुई।"'
  }
};

// Hardcoded Realistic Demo Beneficiary Profiles (Section 1 Demo Feature)
const DEMO_PROFILES = {
  textiles_delhi: {
    id: 'textiles_delhi',
    name: 'Sunita Verma',
    education: '8th Standard',
    education_level: '8th Standard',
    location: 'Delhi',
    state: 'Delhi',
    interests: ['Tailoring & Garment Making'],
    skills: [
      'Basic Stitching & Fabric Cutting',
      'Commercial Pattern Drafting & Measuring',
      'Industrial Sewing Machine Operation'
    ],
    family_occupation: 'Tailoring / Weaving',
    employment_preference: 'self_employment',
    mobility: 'Cannot travel far (Restricted to village/cluster)',
    mobility_constraint: 'Cannot travel far (Restricted to village/cluster)',
    transcript: 'My name is Sunita Verma from Delhi. I am 8th pass and my family does tailoring. I know basic stitching, pattern cutting, and machine sewing. I want to start my own tailoring boutique and cannot travel far.'
  },
  agri_up: {
    id: 'agri_up',
    name: 'Ramkishan Yadav',
    education: '10th Standard',
    education_level: '10th Standard',
    location: 'Varanasi',
    state: 'Uttar Pradesh',
    interests: ['Food Processing & Preservation'],
    skills: [
      'Food Handling & Raw Ingredient Quality',
      'Preservation & Processing Techniques',
      'Packaging & Product Labeling',
      'Micro-Enterprise Costing & Market Linkage'
    ],
    family_occupation: 'Agriculture & Farming',
    employment_preference: 'self_employment',
    mobility: 'Cannot travel far (Restricted to village/cluster)',
    mobility_constraint: 'Cannot travel far (Restricted to village/cluster)',
    transcript: 'My name is Ramkishan Yadav from Varanasi, Uttar Pradesh. I passed 10th standard. My family works in agriculture. I have skills in crop quality, preservation, packaging, and want to establish a local food processing unit.'
  },
  auto_tn: {
    id: 'auto_tn',
    name: 'Karthik Raja',
    education: '12th Standard',
    education_level: '12th Standard',
    location: 'Madurai',
    state: 'Tamil Nadu',
    interests: ['Two-Wheeler & EV Maintenance'],
    skills: [
      'Hand Tools & Mechanical Maintenance'
    ],
    family_occupation: 'Daily Wage Labor',
    employment_preference: 'wage_employment',
    mobility: 'Willing to commute to District/Taluka center',
    mobility_constraint: 'Willing to commute to District/Taluka center',
    transcript: 'My name is Karthik Raja from Madurai, Tamil Nadu. I completed 12th standard. I have experience with basic mechanical hand tools and want a salaried technician job in two-wheeler and electric vehicle servicing.'
  },
  solar_maha: {
    id: 'solar_maha',
    name: 'Amit Shinde',
    education: '12th Standard',
    education_level: '12th Standard',
    location: 'Pune',
    state: 'Maharashtra',
    interests: ['Solar PV & Electrical Installations'],
    skills: [
      'Basic Electrical Wiring & Circuit Safety',
      'Photovoltaic Module Mounting & Alignment',
      'Electrical Safety & Earthing Protocols'
    ],
    family_occupation: 'Agriculture & Farming',
    employment_preference: 'wage_employment',
    mobility: 'Willing to commute to District/Taluka center',
    mobility_constraint: 'Willing to commute to District/Taluka center',
    transcript: 'My name is Amit Shinde from Pune, Maharashtra. I passed 12th standard. I know basic electrical wiring, PV mounting, and safety protocols. I want to become a certified Suryamitra technician.'
  }
};

// DOM Elements Cache
let el = {};

function initElements() {
  el = {
    // Navigation & Views
    navTabs: document.querySelectorAll('.nav-tab'),
    views: document.querySelectorAll('.view-panel'),
    headerTitle: document.getElementById('headerActiveViewTitle'),
    langSelect: document.getElementById('langSelect'),
    langPills: document.querySelectorAll('.lang-pill'),

    // Voice AI Intake Elements
    facilitatorBanner: document.getElementById('facilitatorBanner'),
    btnExitFacilitator: document.getElementById('btnExitFacilitator'),
    btnStartFacilitator: document.getElementById('btnStartFacilitator'),
    btnResetSession: document.getElementById('btnResetSession'),
    statusText: document.getElementById('statusText'),
    assistantSpeechText: document.getElementById('assistantSpeechText'),
    assistantSpeechSub: document.getElementById('assistantSpeechSub'),
    btnReplayAudio: document.getElementById('btnReplayAudio'),
    ttsIcon: document.getElementById('ttsIcon'),
    dominantMicBtn: document.getElementById('dominantMicBtn'),
    micRipple1: document.getElementById('micRipple1'),
    micRipple2: document.getElementById('micRipple2'),
    micIcon: document.getElementById('micIcon'),
    micLabel: document.getElementById('micLabel'),
    waveformVisualizer: document.getElementById('waveformVisualizer'),
    liveTranscriptText: document.getElementById('liveTranscriptText'),
    btnManualSubmitUtterance: document.getElementById('btnManualSubmitUtterance'),
    confidenceTag: document.getElementById('confidenceTag'),
    scenarioChips: document.querySelectorAll('.scenario-chip'),
    demoBeneficiaryBtns: document.querySelectorAll('.demo-beneficiary-btn'),

    // Conversation Feed & Story Summary Elements
    liveStorySummaryText: document.getElementById('liveStorySummaryText'),
    turnCounterBadge: document.getElementById('turnCounterBadge'),
    conversationThread: document.getElementById('conversationThread'),
    chatGreetingText: document.getElementById('chatGreetingText'),
    initialBubbleListenBtn: document.getElementById('initialBubbleListenBtn'),
    chatTypingIndicator: document.getElementById('chatTypingIndicator'),
    chatTextForm: document.getElementById('chatTextForm'),
    chatTextInput: document.getElementById('chatTextInput'),
    btnClearConversation: document.getElementById('btnClearConversation'),

    // Signals
    sigEducation: document.getElementById('sigEducation'),
    sigFamilyOcc: document.getElementById('sigFamilyOcc'),
    sigSkills: document.getElementById('sigSkills'),
    sigMobility: document.getElementById('sigMobility'),
    sigPref: document.getElementById('sigPref'),
    sigEntryMode: document.getElementById('sigEntryMode'),
    signalsBadge: document.getElementById('signalsBadge'),
    matchConfidenceBadge: document.getElementById('matchConfidenceBadge'),

    // Pathways / Roadmap Elements
    recNsqfBadge: document.getElementById('recNsqfBadge'),
    recTradeTitle: document.getElementById('recTradeTitle'),
    recTradeSubTitle: document.getElementById('recTradeSubTitle'),
    recQpName: document.getElementById('recQpName'),
    recQpNsqfLevel: document.getElementById('recQpNsqfLevel'),
    recQpCode: document.getElementById('recQpCode'),
    recSscName: document.getElementById('recSscName'),
    recTradeIcon: document.getElementById('recTradeIcon'),
    recGapSummary: document.getElementById('recGapSummary'),
    readinessScoreContainer: document.getElementById('readinessScoreContainer'),
    readinessScoreBadge: document.getElementById('readinessScoreBadge'),
    readinessIcon: document.getElementById('readinessIcon'),
    audioPlayerContainer: document.getElementById('audioPlayerContainer'),
    btnPlayRoadmapAudio: document.getElementById('btnPlayRoadmapAudio'),
    playPauseIcon: document.getElementById('playPauseIcon'),
    scrubberTrack: document.getElementById('scrubberTrack'),
    audioProgressBar: document.getElementById('audioProgressBar'),
    currentTimeLabel: document.getElementById('currentTimeLabel'),
    recSpokenSummaryText: document.getElementById('recSpokenSummaryText'),
    skillGapsContainer: document.getElementById('skillGapsContainer'),
    gapModulesCount: document.getElementById('gapModulesCount'),
    regionalSchemesContainer: document.getElementById('regionalSchemesContainer'),
    regionalSchemesBadge: document.getElementById('regionalSchemesBadge'),
    nearbyOpportunitiesContainer: document.getElementById('nearbyOpportunitiesContainer'),
    nearbyOpportunitiesBadge: document.getElementById('nearbyOpportunitiesBadge'),
    step1Title: document.getElementById('step1Title'),
    step1Desc: document.getElementById('step1Desc'),
    step2Title: document.getElementById('step2Title'),
    step2Desc: document.getElementById('step2Desc'),
    step2Location: document.getElementById('step2Location'),
    step3Title: document.getElementById('step3Title'),
    step3Desc: document.getElementById('step3Desc'),
    step4Title: document.getElementById('step4Title'),
    step4Desc: document.getElementById('step4Desc'),
    districtContactLine: document.getElementById('districtContactLine'),
    btnPrintRoadmap: document.getElementById('btnPrintRoadmap'),
    btnSmsRoadmap: document.getElementById('btnSmsRoadmap'),
    btnNewRoadmapAssessment: document.getElementById('btnNewRoadmapAssessment'),

    // IVR Elements
    retroScreen: document.getElementById('retroScreen'),
    callStatusBadge: document.getElementById('callStatusBadge'),
    timerBadge: document.getElementById('timerBadge'),
    ivrPromptBox: document.getElementById('lcdPrompt'),
    lcdDialed: document.getElementById('lcdDialed'),
    lcdAudioStatus: document.getElementById('lcdAudioStatus'),
    lcdTime: document.getElementById('lcdTime'),
    keyCall: document.getElementById('keyCall'),
    keyEnd: document.getElementById('keyEnd'),
    keyNav: document.getElementById('keyNav'),
    keypadBtns: document.querySelectorAll('.keypad-btn'),

    // District Admin Elements
    districtSelect: document.getElementById('districtSelect'),
    btnRefreshDashboard: document.getElementById('btnRefreshDashboard'),
    syncIcon: document.getElementById('syncIcon'),
    syncTime: document.getElementById('syncTime'),
    valEnrolments: document.getElementById('valEnrolments'),
    valPlacements: document.getElementById('valPlacements'),
    valDropouts: document.getElementById('valDropouts'),
    valTotalBeneficiaries: document.getElementById('valTotalBeneficiaries'),
    beneficiaryCountTag: document.getElementById('beneficiaryCountTag'),
    demandBarsContainer: document.getElementById('demandBarsContainer'),
    beneficiaryTableBody: document.getElementById('beneficiaryTableBody'),
    btnExportReport: document.getElementById('btnExportReport'),
    btnBulkSms: document.getElementById('btnBulkSms'),

    // Regional Capacity Gap Elements
    capacityGapSection: document.getElementById('capacityGapSection'),
    capacityActiveStateLabel: document.getElementById('capacityActiveStateLabel'),
    capacityStateTabs: document.querySelectorAll('.capacity-state-btn'),
    capacityTotalDemand: document.getElementById('capacityTotalDemand'),
    capacityTotalEst: document.getElementById('capacityTotalEst'),
    capacityOverallBadge: document.getElementById('capacityOverallBadge'),
    capacityTableContainer: document.getElementById('capacityTableContainer'),

    // Toast
    toast: document.getElementById('toastNotification'),
    toastIcon: document.getElementById('toastIcon'),
    toastMessage: document.getElementById('toastMessage')
  };
}

// -------------------------------------------------------------
// App Initialization
// -------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  initElements();
  bindNavigation();
  initSpeechRecognition();
  bindVoiceEvents();
  bindRoadmapEvents();
  bindIvrEvents();
  bindAdminEvents();
  startNewSession();
  startIvrTimer();
  updateClock();
  setInterval(updateClock, 1000);

  // Pre-fetch browser speech synthesis voices so audio is instantly ready
  if ('speechSynthesis' in window) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => {
      window.speechSynthesis.getVoices();
    };
  }
});

// -------------------------------------------------------------
// Navigation & Tab Switching
// -------------------------------------------------------------
function bindNavigation() {
  el.navTabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      const targetView = tab.getAttribute('data-view');
      const title = tab.getAttribute('data-title') || 'PM-AJAY';
      switchTab(targetView, title);
    });
  });

  // Language Dropdown & Interactive Pills
  if (el.langSelect) {
    el.langSelect.addEventListener('change', (e) => {
      setAppLanguage(e.target.value);
    });
  }

  if (el.langPills) {
    el.langPills.forEach(pill => {
      pill.addEventListener('click', () => {
        const lang = pill.getAttribute('data-lang');
        if (lang) setAppLanguage(lang);
      });
    });
  }
}

function setAppLanguage(lang) {
  unlockSpeechAndAudio();
  state.language = lang;

  if (el.langSelect) {
    el.langSelect.value = lang;
  }

  if (el.langPills) {
    el.langPills.forEach(p => {
      if (p.getAttribute('data-lang') === lang) {
        p.className = 'lang-pill active text-xs font-bold px-3 py-1 rounded-full bg-secondary text-on-secondary shadow-sm transition-all cursor-pointer';
      } else {
        p.className = 'lang-pill text-xs font-semibold px-3 py-1 rounded-full bg-surface-container text-on-surface hover:bg-surface-container-high transition-all cursor-pointer';
      }
    });
  }

  if (state.recognition) {
    state.recognition.lang = LANG_LOCALES[lang] || 'en-IN';
  }

  const langNames = { en: 'English', hi: 'हिन्दी', mr: 'मराठी', pa: 'ਪੰਜਾਬੀ', ta: 'தமிழ்' };
  showToast(`Language set to ${langNames[lang] || lang}`, 'translate');
  startNewSession(state.entryMode, state.language);
}

function switchTab(viewId, title) {
  state.activeTab = viewId;

  // Toggle active class on views
  el.views.forEach(v => {
    if (v.id === viewId) {
      v.classList.add('active');
    } else {
      v.classList.remove('active');
    }
  });

  // Toggle active styling on nav buttons
  el.navTabs.forEach(tab => {
    if (tab.getAttribute('data-view') === viewId) {
      tab.classList.add('active', 'text-secondary', 'font-semibold', 'bg-surface-container-low', 'rounded-xl');
      tab.classList.remove('text-on-surface-variant');
    } else {
      tab.classList.remove('active', 'text-secondary', 'font-semibold', 'bg-surface-container-low', 'rounded-xl');
      tab.classList.add('text-on-surface-variant');
    }
  });

  if (el.headerTitle) {
    el.headerTitle.textContent = title;
  }

  // Auto-refresh admin dashboard when switching to it
  if (viewId === 'viewAdmin') {
    loadAdminDashboard();
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// -------------------------------------------------------------
// Session Management: POST /session/start
// -------------------------------------------------------------
async function startNewSession(entryMode = null, language = null) {
  if (entryMode) state.entryMode = entryMode;
  if (language) state.language = language;

  if (el.langSelect) el.langSelect.value = state.language;
  if (el.sigEntryMode) {
    el.sigEntryMode.textContent =
      state.entryMode === 'facilitator' ? 'Facilitator Assisted' :
      state.entryMode === 'call' ? 'IVR Button Phone' : 'PM-AJAY Direct Mobile';
  }

  if (el.facilitatorBanner) {
    if (state.entryMode === 'facilitator') {
      el.facilitatorBanner.classList.remove('hidden');
    } else {
      el.facilitatorBanner.classList.add('hidden');
    }
  }

  state.dialogueTurn = 0;
  if (el.turnCounterBadge) {
    el.turnCounterBadge.textContent = 'Story in Progress';
    el.turnCounterBadge.className = 'text-[11px] font-bold px-2 py-0.5 rounded-full bg-secondary/10 text-secondary border border-secondary/20';
  }
  if (el.liveStorySummaryText) {
    el.liveStorySummaryText.textContent = "Listening to beneficiary's background and vocational story... Tap the microphone above to speak about your schooling, family work, or interests.";
  }
  if (el.conversationThread) {
    el.conversationThread.innerHTML = '';
  }

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
    addChatBubble(prompt, 'assistant');
  } catch (err) {
    console.warn('Session start fallback:', err);
    state.sessionId = 'local-' + Date.now();
    const prompt = INITIAL_PROMPTS[state.language] || INITIAL_PROMPTS.en;
    setAssistantSpeech(prompt);
    addChatBubble(prompt, 'assistant');
  }
}

function resetSignalDisplay() {
  if (el.sigEducation) el.sigEducation.textContent = '—';
  if (el.sigFamilyOcc) el.sigFamilyOcc.textContent = '—';
  if (el.sigSkills) el.sigSkills.textContent = '—';
  if (el.sigMobility) el.sigMobility.textContent = '—';
  if (el.sigPref) el.sigPref.textContent = '—';
  if (el.signalsBadge) {
    el.signalsBadge.textContent = 'Intake In Progress';
    el.signalsBadge.className = 'text-xs bg-surface-container px-2 py-0.5 rounded-full text-on-surface-variant font-semibold';
  }
  if (el.liveTranscriptText) {
    el.liveTranscriptText.textContent = 'Press the mic button and speak freely in your language...';
  }
  if (el.btnManualSubmitUtterance) {
    el.btnManualSubmitUtterance.classList.add('hidden');
  }
}

function setAssistantSpeech(text, autoSpeak = false, audioBase64 = null) {
  if (el.assistantSpeechText) el.assistantSpeechText.textContent = `"${text}"`;
  if (el.assistantSpeechSub) el.assistantSpeechSub.textContent = INITIAL_PROMPTS_SUB[state.language] || INITIAL_PROMPTS_SUB.en;
  if (el.chatGreetingText) el.chatGreetingText.textContent = text;

  if (autoSpeak) {
    speak(text, audioBase64);
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function addChatBubble(text, role = 'user', audioBase64 = null) {
  if (!el.conversationThread || !text) return;

  const isUser = role === 'user';
  const bubbleDiv = document.createElement('div');
  bubbleDiv.className = isUser
    ? 'flex items-start gap-2 max-w-[88%] self-end user-bubble transition-all'
    : 'flex items-start gap-2.5 max-w-[88%] self-start assistant-bubble transition-all';

  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (isUser) {
    bubbleDiv.innerHTML = `
      <div class="bg-primary text-on-primary rounded-2xl rounded-tr-sm p-3 text-xs leading-relaxed shadow-sm">
        <p class="font-medium text-white">${escapeHtml(text)}</p>
        <span class="text-[10px] text-white/70 block text-right mt-1">${timeStr}</span>
      </div>
      <div class="w-7 h-7 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center flex-shrink-0 text-xs shadow-sm">
        <span class="material-symbols-outlined text-[16px]">person</span>
      </div>
    `;
  } else {
    const bubbleId = 'tts-btn-' + Math.random().toString(36).substring(2, 9);
    bubbleDiv.innerHTML = `
      <div class="w-7 h-7 rounded-full bg-secondary text-on-secondary flex items-center justify-center flex-shrink-0 text-xs shadow-sm">
        <span class="material-symbols-outlined text-[16px]">smart_toy</span>
      </div>
      <div class="bg-surface-container-low rounded-2xl rounded-tl-sm p-3 text-xs text-on-surface leading-relaxed shadow-sm space-y-1">
        <div class="flex items-center justify-between gap-2">
          <span class="font-semibold text-secondary">Nivara Assistant</span>
          <span class="text-[10px] text-on-surface-variant">${timeStr}</span>
        </div>
        <p class="font-medium">${escapeHtml(text)}</p>
        <button id="${bubbleId}" class="chat-bubble-tts text-[11px] text-secondary font-bold inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-secondary/10 hover:bg-secondary/20 transition-all cursor-pointer mt-1">
          <span class="material-symbols-outlined text-[15px]">volume_up</span>
          <span>Listen / सुनें</span>
        </button>
      </div>
    `;

    setTimeout(() => {
      const btn = document.getElementById(bubbleId);
      if (btn) {
        btn.addEventListener('click', () => {
          unlockSpeechAndAudio();
          speak(text, audioBase64);
        });
      }
    }, 50);
  }

  el.conversationThread.appendChild(bubbleDiv);
  el.conversationThread.scrollTop = el.conversationThread.scrollHeight;
}

// -------------------------------------------------------------
// Continuous Voice Recognition Engine (Web Speech API)
// -------------------------------------------------------------
let accumulatedTranscript = '';
let interimTranscript = '';
let silenceDebounceTimer = null;

function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.info('Speech Recognition not supported natively in this browser; fallback chips enabled.');
    return;
  }

  state.recognition = new SpeechRecognition();
  // Enable continuous recognition so speaking multiple sentences does NOT cut off automatically!
  state.recognition.continuous = true;
  state.recognition.interimResults = true;

  state.recognition.onstart = () => {
    state.isRecording = true;
    accumulatedTranscript = '';
    interimTranscript = '';
    if (el.micRipple1) el.micRipple1.classList.remove('hidden');
    if (el.micRipple2) el.micRipple2.classList.remove('hidden');
    if (el.micLabel) el.micLabel.textContent = 'Listening... (Tap when done)';
    if (el.statusText) el.statusText.textContent = 'LISTENING • SPEAK FREELY • TAP MIC OR PAUSE TO SUBMIT';
    if (el.micIcon) el.micIcon.textContent = 'graphic_eq';
    if (el.btnManualSubmitUtterance) el.btnManualSubmitUtterance.classList.add('hidden');
  };

  state.recognition.onresult = (event) => {
    interimTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      const piece = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        accumulatedTranscript += piece + ' ';
      } else {
        interimTranscript += piece;
      }
    }

    const currentSpoken = (accumulatedTranscript + ' ' + interimTranscript).trim();
    if (el.liveTranscriptText) el.liveTranscriptText.textContent = `"${currentSpoken}"`;
    if (el.btnManualSubmitUtterance && currentSpoken.length > 0) {
      el.btnManualSubmitUtterance.classList.remove('hidden');
    }

    // Reset silence timer on every spoken syllable
    clearTimeout(silenceDebounceTimer);
    if (currentSpoken.length > 8) {
      // 3.8s natural silence window: gives beneficiary ample time to breathe and continue speaking
      silenceDebounceTimer = setTimeout(() => {
        if (state.isRecording && currentSpoken.length > 8) {
          stopRecordingAndSubmit();
        }
      }, 3800);
    }
  };

  state.recognition.onerror = (event) => {
    console.warn('Speech recognition warning:', event.error);
    if (event.error !== 'no-speech') {
      stopRecording();
    }
  };

  state.recognition.onend = () => {
    if (state.isRecording) {
      const finalSpoken = (accumulatedTranscript + ' ' + interimTranscript).trim();
      if (finalSpoken.length > 5) {
        stopRecordingAndSubmit();
      } else {
        stopRecording();
      }
    }
  };
}

function stopRecordingAndSubmit() {
  clearTimeout(silenceDebounceTimer);
  const textToSubmit = (accumulatedTranscript + ' ' + interimTranscript).trim();
  stopRecording();
  if (textToSubmit.length > 0) {
    handleUserVoiceUtterance(textToSubmit);
    accumulatedTranscript = '';
    interimTranscript = '';
  }
}

function toggleRecording() {
  unlockSpeechAndAudio();

  if (!state.recognition) {
    showToast('Simulating mic input: 10th Pass + Farming');
    handleUserVoiceUtterance("I finished 10th, my family does farming, I want something food-related, I can't travel far");
    return;
  }

  if (state.isRecording) {
    // User tapped mic button to finish speaking
    stopRecordingAndSubmit();
  } else {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    state.recognition.lang = LANG_LOCALES[state.language] || 'en-IN';
    try {
      state.recognition.start();
    } catch (e) {
      state.recognition.stop();
      setTimeout(() => {
        try { state.recognition.start(); } catch (err) {}
      }, 150);
    }
  }
}

function stopRecording() {
  state.isRecording = false;
  clearTimeout(silenceDebounceTimer);
  if (el.micRipple1) el.micRipple1.classList.add('hidden');
  if (el.micRipple2) el.micRipple2.classList.add('hidden');
  if (el.micLabel) el.micLabel.textContent = 'Tap & Speak / बोलिए';
  if (el.statusText) el.statusText.textContent = 'VOICE READY • TAP TO SPEAK';
  if (el.micIcon) el.micIcon.textContent = 'mic';
}

function bindVoiceEvents() {
  // Mic Button
  if (el.dominantMicBtn) {
    el.dominantMicBtn.addEventListener('click', toggleRecording);
  }

  // Manual Send Button next to live transcript
  if (el.btnManualSubmitUtterance) {
    el.btnManualSubmitUtterance.addEventListener('click', () => {
      unlockSpeechAndAudio();
      stopRecordingAndSubmit();
    });
  }

  // Text Input Form for typing stories
  if (el.chatTextForm) {
    el.chatTextForm.addEventListener('submit', (e) => {
      e.preventDefault();
      unlockSpeechAndAudio();
      const val = el.chatTextInput ? el.chatTextInput.value.trim() : '';
      if (val) {
        el.chatTextInput.value = '';
        handleUserVoiceUtterance(val);
      }
    });
  }

  // Clear Conversation Button
  if (el.btnClearConversation) {
    el.btnClearConversation.addEventListener('click', () => {
      startNewSession(state.entryMode, state.language);
      showToast('Conversation reset. Ready for new voice intake.', 'restart_alt');
    });
  }

  // TTS Replay Button
  if (el.btnReplayAudio) {
    el.btnReplayAudio.addEventListener('click', () => {
      unlockSpeechAndAudio();
      const prompt = el.assistantSpeechText ? el.assistantSpeechText.textContent.replace(/^"+|"+$/g, '') : '';
      if (el.ttsIcon) el.ttsIcon.textContent = 'graphic_eq';
      speak(prompt, null, () => {
        if (el.ttsIcon) el.ttsIcon.textContent = 'volume_up';
      });
    });
  }

  // Initial Opening Chat Bubble Listen Button
  if (el.initialBubbleListenBtn) {
    el.initialBubbleListenBtn.addEventListener('click', () => {
      unlockSpeechAndAudio();
      const text = el.chatGreetingText ? el.chatGreetingText.textContent.trim() : '';
      if (text) {
        speak(text);
      }
    });
  }

  // Scenario Chips
  el.scenarioChips.forEach(chip => {
    chip.addEventListener('click', () => {
      unlockSpeechAndAudio();
      const text = chip.getAttribute('data-text');
      if (text) {
        chip.classList.add('bg-surface-container-high');
        setTimeout(() => chip.classList.remove('bg-surface-container-high'), 300);
        handleUserVoiceUtterance(text);
      }
    });
  });

  // Facilitator Mode Buttons
  if (el.btnStartFacilitator) {
    el.btnStartFacilitator.addEventListener('click', () => {
      startNewSession('facilitator', state.language);
      showToast('Facilitator Mode enabled: Doorstep intake active', 'handshake');
    });
  }

  if (el.btnExitFacilitator) {
    el.btnExitFacilitator.addEventListener('click', () => {
      startNewSession('app', state.language);
      showToast('Switched to Self-Service Beneficiary Mode');
    });
  }

  if (el.btnResetSession) {
    el.btnResetSession.addEventListener('click', () => {
      startNewSession(state.entryMode, state.language);
      showToast('Session reset. Ready for new voice intake.', 'restart_alt');
    });
  }

  // Demo Beneficiary Selector Buttons (1-Click Pipeline Simulation)
  if (el.demoBeneficiaryBtns) {
    el.demoBeneficiaryBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const demoId = btn.getAttribute('data-demo-id');
        if (demoId) triggerDemoBeneficiary(demoId);
      });
    });
  }
}

// -------------------------------------------------------------
// Demo Beneficiary Pipeline Trigger (Exact same API path)
// -------------------------------------------------------------
async function triggerDemoBeneficiary(demoId) {
  const profile = DEMO_PROFILES[demoId];
  if (!profile) return;

  // 1. Visual feedback on clicked button
  const btn = document.querySelector(`[data-demo-id="${demoId}"]`);
  if (btn) {
    btn.classList.add('ring-2', 'ring-secondary', 'bg-surface-container');
    setTimeout(() => btn.classList.remove('ring-2', 'ring-secondary', 'bg-surface-container'), 500);
  }

  showToast(`Loading Beneficiary: ${profile.name} (${profile.state})`, 'account_circle');

  // 2. Populate form/signals & UI state with profile
  state.profile = { ...profile };
  state.beneficiaryProfile = { ...profile };
  updateSignalsView(profile);
  if (el.liveTranscriptText) {
    el.liveTranscriptText.textContent = `"${profile.transcript}"`;
  }
  if (el.statusText) {
    el.statusText.textContent = `BENEFICIARY SELECTED: ${profile.name.toUpperCase()} • RUNNING PIPELINE...`;
  }

  // 3. Immediately trigger existing recommendation flow using exact same API path
  try {
    const startRes = await fetch('/session/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        entry_mode: state.entryMode || 'app',
        language: state.language || 'en'
      })
    });
    const startData = await startRes.json();
    state.sessionId = startData.session_id;

    const voiceRes = await fetch(`/session/${state.sessionId}/voice-input`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transcript: profile.transcript,
        profile_data: profile,
        language: state.language || 'en'
      })
    });
    const voiceData = await voiceRes.json();

    if (voiceData.profile_complete) {
      state.profileComplete = true;
      if (el.signalsBadge) {
        el.signalsBadge.textContent = '✅ Profile Complete';
        el.signalsBadge.className = 'text-xs bg-[#ecfdf5] text-[#065f46] px-2.5 py-0.5 rounded-full font-bold shadow-sm';
      }
      if (voiceData.extracted_fields) {
        updateSignalsView(voiceData.extracted_fields);
      }

      await loadRoadmapRecommendation();
      switchTab('viewRoadmap', 'Roadmap & Skills');
      showToast(`Roadmap generated for ${profile.name}!`, 'verified');
    }
  } catch (err) {
    console.error('Error running demo beneficiary pipeline:', err);
    showToast('Demo pipeline error. Please try again.');
  }
}

// -------------------------------------------------------------
// Voice Input Pipeline: POST /session/{id}/voice-input
// -------------------------------------------------------------
async function handleUserVoiceUtterance(utteranceText) {
  if (!utteranceText || !utteranceText.trim()) return;

  // 1. Add User Bubble to Conversation Thread
  addChatBubble(utteranceText, 'user');

  state.dialogueTurn = (state.dialogueTurn || 0) + 1;
  if (el.turnCounterBadge) {
    el.turnCounterBadge.textContent = `Dialogue Turn ${state.dialogueTurn}`;
  }

  if (el.liveTranscriptText) el.liveTranscriptText.textContent = `"${utteranceText}"`;
  if (el.statusText) el.statusText.textContent = 'ANALYZING STORY WITH LLM & EXTRACTING SIGNALS...';
  if (el.chatTypingIndicator) el.chatTypingIndicator.classList.remove('hidden');

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
    if (el.chatTypingIndicator) el.chatTypingIndicator.classList.add('hidden');

    // 2. Add Assistant Response Bubble to Conversation Thread
    addChatBubble(data.next_prompt, 'assistant', data.reply_audio_base64);

    // 3. Update Story Summary
    if (data.story_summary && el.liveStorySummaryText) {
      el.liveStorySummaryText.textContent = data.story_summary;
    }

    // 4. Update Signals Display
    updateSignalsView(data.extracted_fields);

    // 5. Play Next Prompt with audio
    setAssistantSpeech(data.next_prompt, true, data.reply_audio_base64);

    // 6. If Complete, fetch Recommendation and transition to Pathways Tab
    if (data.profile_complete) {
      state.profileComplete = true;
      if (el.signalsBadge) {
        el.signalsBadge.textContent = '✅ Profile Complete';
        el.signalsBadge.className = 'text-xs bg-[#ecfdf5] text-[#065f46] px-2.5 py-0.5 rounded-full font-bold shadow-sm';
      }
      if (el.turnCounterBadge) {
        el.turnCounterBadge.textContent = '✅ Profile Ready';
        el.turnCounterBadge.className = 'text-[11px] font-bold px-2 py-0.5 rounded-full bg-[#ecfdf5] text-[#065f46] border border-[#a7f3d0]';
      }
      showToast('Profile Complete! Generating NSQF Livelihood Pathway...', 'verified');

      setTimeout(async () => {
        await loadRoadmapRecommendation();
        switchTab('viewRoadmap', 'Roadmap & Skills');
      }, 1600);
    }

  } catch (err) {
    if (el.chatTypingIndicator) el.chatTypingIndicator.classList.add('hidden');
    console.error('Error submitting voice input:', err);
    showToast('Voice processing note: Please try speaking again.');
  }
}

function updateSignalsView(fields = {}) {
  const edu = fields.education_level || fields.education;
  if (edu && el.sigEducation) el.sigEducation.textContent = edu;

  if (fields.family_occupation && el.sigFamilyOcc) el.sigFamilyOcc.textContent = fields.family_occupation;

  if (el.sigSkills) {
    if (fields.skills && fields.skills.length > 0) {
      el.sigSkills.textContent = Array.isArray(fields.skills) ? fields.skills.join(', ') : fields.skills;
    } else if (fields.interests && fields.interests.length > 0) {
      el.sigSkills.textContent = Array.isArray(fields.interests) ? fields.interests.join(', ') : fields.interests;
    }
  }

  const mob = fields.mobility_constraint || fields.mobility;
  if (mob && el.sigMobility) el.sigMobility.textContent = mob;

  if (fields.employment_preference && el.sigPref) {
    el.sigPref.textContent = fields.employment_preference === 'self_employment' ? 'Self-Employment' : 'Wage / Salaried';
  }
}

// -------------------------------------------------------------
// Recommendation Pipeline: GET /session/{id}/recommendation
// -------------------------------------------------------------
async function loadRoadmapRecommendation() {
  try {
    const res = await fetch(`/session/${state.sessionId}/recommendation`);
    if (!res.ok) {
      showToast('Please continue the voice intake before viewing recommendations.');
      return;
    }
    const data = await res.json();
    state.currentRecommendation = data;
    renderRoadmap(data);
  } catch (err) {
    console.error('Error fetching recommendation:', err);
  }
}

function updateReadinessBadge(score, tier) {
  const container = el.readinessScoreContainer || document.getElementById('readinessScoreContainer');
  const badge = el.readinessScoreBadge || document.getElementById('readinessScoreBadge');
  const icon = el.readinessIcon || document.getElementById('readinessIcon');
  if (!badge) return;

  const validScore = (typeof score === 'number' && !isNaN(score)) ? Math.round(score) : 0;
  
  let tierLabel = tier;
  if (!tierLabel) {
    if (validScore >= 70) {
      tierLabel = 'Direct Pathway Ready';
    } else if (validScore >= 40) {
      tierLabel = 'Skill Bridge Track';
    } else {
      tierLabel = 'Exploratory Track — Review Options';
    }
  }

  badge.textContent = `Readiness: ${validScore}/100 — ${tierLabel}`;

  if (!container) return;

  // Transparent ratio badge styling: red under 40, yellow 40-69, green 70+
  if (validScore < 40) {
    container.className = 'flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold shadow-sm border transition-colors bg-[#fee2e2] text-[#991b1b] border-[#fecaca]';
    if (icon) icon.textContent = 'warning';
  } else if (validScore < 70) {
    container.className = 'flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold shadow-sm border transition-colors bg-[#fef3c7] text-[#92400e] border-[#fde68a]';
    if (icon) icon.textContent = 'speed';
  } else {
    container.className = 'flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold shadow-sm border transition-colors bg-[#d1fae5] text-[#065f46] border-[#a7f3d0]';
    if (icon) icon.textContent = 'verified';
  }
}

function renderRoadmap(rec) {
  if (rec.needs_more_info) {
    if (el.recTradeTitle) el.recTradeTitle.textContent = 'I need more information to recommend confidently';
    if (el.recNsqfBadge) el.recNsqfBadge.textContent = `Clarification: ${rec.missing_piece || 'Information'}`;
    if (el.recQpName) el.recQpName.textContent = 'Additional Information Required';
    if (el.recQpNsqfLevel) el.recQpNsqfLevel.textContent = 'Gated Evaluation';
    if (el.recQpCode) el.recQpCode.textContent = `Missing Piece: ${rec.missing_piece || 'Details'}`;
    if (el.recSscName) el.recSscName.textContent = 'PM-AJAY Guidance';

    const missingLabelMap = {
      'region': 'Location / State Not Recognized',
      'skill': 'Trade Skill Category Not Matched',
      'clarity of intent': 'Multiple Trade Paths Tied'
    };
    const friendlyMissing = missingLabelMap[rec.missing_piece] || rec.missing_piece || 'Information';

    if (el.recGapSummary) {
      el.recGapSummary.innerHTML = `
        <div class="p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-amber-950 font-medium text-xs flex flex-col gap-2">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-amber-700 text-lg">help</span>
            <span class="font-bold text-sm text-amber-900">I need more information to recommend confidently</span>
          </div>
          <div class="text-amber-800">${rec.detail || rec.gap_summary || 'Please provide more details.'}</div>
          <div class="flex items-center gap-2 mt-1">
            <span class="text-[11px] text-amber-700 font-semibold">Missing Piece:</span>
            <span class="px-2 py-0.5 rounded-full bg-amber-200/80 text-amber-900 text-[11px] font-bold uppercase tracking-wider">${rec.missing_piece} (${friendlyMissing})</span>
          </div>
        </div>
      `;
    }
    if (el.recSpokenSummaryText) {
      el.recSpokenSummaryText.textContent = `"${rec.clarifying_question || rec.spoken_summary}"`;
    }
    updateReadinessBadge(0, 'Exploratory Track — Review Options');
    renderSkillGaps([]);
    renderRegionalSchemes(rec.regional_schemes || []);
    return;
  }

  // Title & Badges
  if (el.recTradeTitle) el.recTradeTitle.textContent = rec.recommended_trade;
  const nsqfLvl = rec.nsqf_level || rec.nsqf_alignment || 'NSQF Level 4';
  if (el.recNsqfBadge) el.recNsqfBadge.textContent = `${nsqfLvl} Certified`;

  // Real NSQF Qualification Pack Details
  if (el.recQpName) el.recQpName.textContent = rec.qp_name || rec.recommended_trade;
  if (el.recQpNsqfLevel) el.recQpNsqfLevel.textContent = nsqfLvl;
  if (el.recQpCode) el.recQpCode.textContent = rec.qp_code ? `QP Code: ${rec.qp_code}` : 'NSQF Aligned';
  if (el.recSscName) el.recSscName.textContent = rec.ssc_name || rec.sector || 'Sector Skill Council';

  if (el.recGapSummary) {
    el.recGapSummary.innerHTML = `<span class="font-semibold text-secondary">AI Diagnostic Summary:</span> ${rec.gap_summary}`;
  }
  if (el.recSpokenSummaryText) el.recSpokenSummaryText.textContent = `"${rec.spoken_summary}"`;

  // Dynamic Sector Icon
  const tradeKey = rec.trade_key || 'food_processing';
  if (el.recTradeIcon) {
    el.recTradeIcon.textContent = TRADE_ICONS[tradeKey] || 'psychology';
  }

  // Update Numeric Skill Readiness Score Badge & Qualitative Tier (Feature 2)
  updateReadinessBadge(rec.readiness_score, rec.readiness_tier);

  // 1. Render Structured Skill Gap Breakdown (Task 3 Feature)
  renderSkillGaps(rec.skill_gap_breakdown || []);

  // 2. Render Regional Schemes in Beneficiary State (Nivara Regional Schemes)
  renderRegionalSchemes(rec.regional_schemes || []);

  // 3. Render Nearby Employment & Enterprise Opportunities (Local Opportunities)
  renderNearbyOpportunities(rec.nearby_opportunities || []);

  // 4. Render 4-Stage Pathway Timeline
  const steps = rec.roadmap_steps || [];
  if (steps[0] && el.step1Title) {
    el.step1Title.textContent = steps[0].split('(')[0] || 'Enroll in PM-AJAY Free Skill Training';
    if (el.step1Desc) el.step1Desc.textContent = steps[0];
  }
  if (steps[1] && el.step2Title) {
    el.step2Title.textContent = steps[1].split('with')[0] || 'Practical Lab Training';
    if (el.step2Desc) el.step2Desc.textContent = steps[1];
    if (el.step2Location) el.step2Location.textContent = rec.training_centre || 'District ITI / PMKK Center';
  }
  if (steps[2] && el.step3Title) {
    el.step3Title.textContent = `${rec.nsqf_alignment} National Certification`;
    if (el.step3Desc) el.step3Desc.textContent = steps[2];
  }
  if (steps[3] && el.step4Title) {
    el.step4Title.textContent = 'Enterprise Launch / Placement Linkage';
    if (el.step4Desc) el.step4Desc.textContent = rec.local_opportunity || steps[3];
  }

  // Contact line
  if (el.districtContactLine) {
    el.districtContactLine.textContent = `${rec.training_centre || 'District Center'} • Toll-Free: 1800-11-7625`;
  }
}

function renderSkillGaps(gaps = []) {
  if (!el.skillGapsContainer) return;
  el.skillGapsContainer.innerHTML = '';

  if (!gaps || gaps.length === 0) {
    // Fallback realistic gaps if empty
    gaps = [
      { skill: "Certified Quality & Hygiene Standards", where: "Jan Shikshan Sansthan (JSS) District Lab" },
      { skill: "Modern Equipment & Machine Operation", where: "PMKK Center Hands-on Workshop" },
      { skill: "Micro-Enterprise Costing & Mudra Loan Filing", where: "RSETI Rural Entrepreneurship Center" }
    ];
  }

  if (el.gapModulesCount) {
    el.gapModulesCount.textContent = `${gaps.length} Targeted Modules`;
  }

  const borderColors = ['#f59e0b', '#0051d5', '#10b981', '#7c839b'];
  const icons = ['sanitizer', 'inventory_2', 'account_balance', 'electric_meter'];

  gaps.forEach((g, idx) => {
    const borderColor = borderColors[idx % borderColors.length];
    const icon = icons[idx % icons.length];
    const card = document.createElement('div');
    card.className = 'bg-surface-container-lowest rounded-xl p-space-md shadow-sm relative overflow-hidden flex flex-col gap-space-xs';
    card.innerHTML = `
      <div class="absolute left-0 top-0 bottom-0 w-1.5" style="background-color: ${borderColor}"></div>
      <div class="flex items-start justify-between gap-space-xs">
        <div class="flex flex-col">
          <div class="flex items-center gap-2">
            <span class="text-[11px] uppercase tracking-wide font-bold" style="color: ${borderColor}">Skill Gap ${idx + 1}</span>
            <span class="text-[11px] text-on-surface-variant">• Targeted Competency</span>
          </div>
          <h3 class="font-display font-semibold text-sm text-on-surface mt-0.5">${g.skill}</h3>
        </div>
        <span class="material-symbols-outlined text-on-surface-variant text-[20px]">${icon}</span>
      </div>
      <div class="bg-surface-container-low rounded-lg p-space-sm flex items-center justify-between gap-space-xs mt-1">
        <div class="flex items-center gap-2 min-w-0">
          <span class="material-symbols-outlined text-secondary text-[18px] flex-shrink-0">domain</span>
          <div class="flex flex-col min-w-0">
            <span class="text-[10px] text-on-surface-variant">Recommended Learning Source</span>
            <span class="text-xs text-on-surface font-semibold truncate">${g.where}</span>
          </div>
        </div>
        <span class="text-[10px] bg-secondary/10 text-secondary font-bold px-2 py-1 rounded-full flex-shrink-0">Free PM-AJAY</span>
      </div>
    `;
    el.skillGapsContainer.appendChild(card);
  });
}

function renderRegionalSchemes(schemes = []) {
  if (!el.regionalSchemesContainer) return;
  el.regionalSchemesContainer.innerHTML = '';

  if (el.regionalSchemesBadge) {
    el.regionalSchemesBadge.textContent = schemes && schemes.length > 0
      ? `${schemes.length} Schemes Available`
      : 'No State Schemes';
  }

  if (!schemes || schemes.length === 0) {
    const emptyCard = document.createElement('div');
    emptyCard.className = 'bg-surface-container-lowest rounded-xl p-space-md shadow-sm relative overflow-hidden flex flex-col items-center justify-center py-6 text-center border border-dashed border-secondary/20';
    emptyCard.innerHTML = `
      <span class="material-symbols-outlined text-on-surface-variant text-[28px] mb-1">travel_explore</span>
      <p class="text-xs font-semibold text-on-surface">No regional schemes matched for your state</p>
      <p class="text-[11px] text-on-surface-variant mt-0.5">Reference state schemes are available for Delhi, Maharashtra, Tamil Nadu, Karnataka, and Uttar Pradesh.</p>
    `;
    el.regionalSchemesContainer.appendChild(emptyCard);
    return;
  }

  const borderColors = ['#0051d5', '#10b981', '#f59e0b', '#7c839b'];
  const icons = ['verified', 'assured_workload', 'payments', 'work'];

  schemes.forEach((s, idx) => {
    const borderColor = borderColors[idx % borderColors.length];
    const icon = icons[idx % icons.length];
    const card = document.createElement('div');
    card.className = 'bg-surface-container-lowest rounded-xl p-space-md shadow-sm relative overflow-hidden flex flex-col gap-space-xs';
    card.innerHTML = `
      <div class="absolute left-0 top-0 bottom-0 w-1.5" style="background-color: ${borderColor}"></div>
      <div class="flex items-start justify-between gap-space-xs">
        <div class="flex flex-col flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-[11px] uppercase tracking-wide font-bold" style="color: ${borderColor}">${s.provider || 'State Department'}</span>
            <span class="text-[11px] text-on-surface-variant">• Regional Opportunity</span>
          </div>
          <h3 class="font-display font-semibold text-sm text-on-surface mt-0.5">${s.name}</h3>
        </div>
        <span class="material-symbols-outlined text-on-surface-variant text-[20px] flex-shrink-0">${icon}</span>
      </div>

      <!-- Data Provenance & Verification Badge -->
      <div class="flex flex-wrap items-center gap-2 my-1">
        <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#fffbeb] text-[#92400e] border border-[#f59e0b]/50 shadow-xs" title="${s.source_note || 'Compiled from official state corporation portals, manually verified as of 2026-09-27'}">
          <span class="material-symbols-outlined text-[14px] text-[#d97706]">verified_user</span>
          Community-compiled — verify with local office
        </span>
        <span class="inline-flex items-center gap-1 text-[11px] text-on-surface-variant font-medium">
          <span class="material-symbols-outlined text-[13px] text-on-surface-variant/70">calendar_today</span>
          Checked: ${s.last_checked || '2026-09-27'}
        </span>
      </div>
      
      <div class="flex flex-col gap-1 mt-1">
        <div class="text-xs text-on-surface leading-relaxed">
          <span class="font-bold text-secondary">Benefit:</span> ${s.benefit}
        </div>
        ${s.eligibility ? `
        <div class="text-[11px] text-on-surface-variant leading-normal">
          <span class="font-semibold text-on-surface">Eligibility:</span> ${s.eligibility}
        </div>` : ''}
      </div>

      <div class="bg-surface-container-low rounded-lg p-space-sm flex items-center justify-between gap-space-xs mt-1">
        <div class="flex items-center gap-2 min-w-0">
          <span class="material-symbols-outlined text-secondary text-[18px] flex-shrink-0">apartment</span>
          <div class="flex flex-col min-w-0">
            <span class="text-[10px] text-on-surface-variant font-medium">How to Apply</span>
            <span class="text-xs text-on-surface font-semibold truncate">${s.how_to_apply}</span>
          </div>
        </div>
        <span class="text-[10px] bg-secondary/10 text-secondary font-bold px-2 py-1 rounded-full flex-shrink-0">Official Office / Portal</span>
      </div>
    `;
    el.regionalSchemesContainer.appendChild(card);
  });
}

function renderNearbyOpportunities(opps = []) {
  if (!el.nearbyOpportunitiesContainer) return;
  el.nearbyOpportunitiesContainer.innerHTML = '';

  if (el.nearbyOpportunitiesBadge) {
    el.nearbyOpportunitiesBadge.textContent = opps && opps.length > 0
      ? `${opps.length} Local Openings`
      : 'No Openings Found';
  }

  if (!opps || opps.length === 0) {
    const emptyCard = document.createElement('div');
    emptyCard.className = 'bg-surface-container-lowest rounded-xl p-space-md shadow-sm relative overflow-hidden flex flex-col items-center justify-center py-6 text-center border border-dashed border-secondary/20';
    emptyCard.innerHTML = `
      <span class="material-symbols-outlined text-on-surface-variant text-[28px] mb-1">domain_disabled</span>
      <p class="text-xs font-semibold text-on-surface">No local opportunities indexed for this sector</p>
      <p class="text-[11px] text-on-surface-variant mt-0.5">District employment exchange data is being synchronized.</p>
    `;
    el.nearbyOpportunitiesContainer.appendChild(emptyCard);
    return;
  }

  const borderColors = ['#10b981', '#0051d5', '#f59e0b', '#7c839b'];
  const icons = ['storefront', 'precision_manufacturing', 'work_outline', 'handshake'];

  opps.forEach((o, idx) => {
    const borderColor = borderColors[idx % borderColors.length];
    const icon = icons[idx % icons.length];
    const card = document.createElement('div');
    card.className = 'bg-surface-container-lowest rounded-xl p-space-md shadow-sm relative overflow-hidden flex flex-col gap-space-xs';
    card.innerHTML = `
      <div class="absolute left-0 top-0 bottom-0 w-1.5" style="background-color: ${borderColor}"></div>
      <div class="flex items-start justify-between gap-space-xs">
        <div class="flex flex-col flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-[11px] uppercase tracking-wide font-bold" style="color: ${borderColor}">${o.employer_type || 'Local Enterprise'}</span>
            <span class="text-[11px] text-on-surface-variant">• ${o.distance || 'Local Cluster'}</span>
          </div>
          <h3 class="font-display font-semibold text-sm text-on-surface mt-0.5">${o.title}</h3>
        </div>
        <span class="material-symbols-outlined text-on-surface-variant text-[20px] flex-shrink-0">${icon}</span>
      </div>

      <!-- Provenance badge -->
      <div class="flex flex-wrap items-center gap-2 my-1">
        <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#eff6ff] text-[#1d4ed8] border border-[#93c5fd]/50 shadow-xs" title="Synthetic/illustrative local data pending direct integration with National Career Service (NCS) and UDYAM registries">
          <span class="material-symbols-outlined text-[14px] text-[#2563eb]">info</span>
          Estimated local cluster — pending NCS live registry
        </span>
        ${o.wage_range ? `
        <span class="inline-flex items-center gap-1 text-[11px] text-[#065f46] bg-[#ecfdf5] px-2 py-0.5 rounded-full font-bold">
          <span class="material-symbols-outlined text-[13px]">payments</span>
          ${o.wage_range}
        </span>` : ''}
      </div>

      <div class="bg-surface-container-low rounded-lg p-space-sm flex items-center justify-between gap-space-xs mt-1">
        <div class="flex items-center gap-2 min-w-0">
          <span class="material-symbols-outlined text-secondary text-[18px] flex-shrink-0">near_me</span>
          <div class="flex flex-col min-w-0">
            <span class="text-[10px] text-on-surface-variant font-medium">Linkage Channel</span>
            <span class="text-xs text-on-surface font-semibold truncate">District Employment Office / PMKK Placement Cell</span>
          </div>
        </div>
        <span class="text-[10px] bg-secondary/10 text-secondary font-bold px-2 py-1 rounded-full flex-shrink-0">Direct Linkage</span>
      </div>
    `;
    el.nearbyOpportunitiesContainer.appendChild(card);
  });
}

function bindRoadmapEvents() {
  // Audio Player Scrubber and Toggle
  if (el.btnPlayRoadmapAudio) {
    el.btnPlayRoadmapAudio.addEventListener('click', toggleRoadmapAudio);
  }

  if (el.scrubberTrack) {
    el.scrubberTrack.addEventListener('click', (e) => {
      const rect = el.scrubberTrack.getBoundingClientRect();
      const pct = Math.max(0, Math.min(100, Math.round(((e.clientX - rect.left) / rect.width) * 100)));
      if (el.audioProgressBar) el.audioProgressBar.style.width = pct + '%';
    });
  }

  // Print Summary
  if (el.btnPrintRoadmap) {
    el.btnPrintRoadmap.addEventListener('click', () => {
      window.print();
    });
  }

  // Send SMS
  if (el.btnSmsRoadmap) {
    el.btnSmsRoadmap.addEventListener('click', () => {
      showToast('Roadmap slip dispatched to beneficiary phone via SMS & WhatsApp.', 'send');
    });
  }

  // Start Next Assessment
  if (el.btnNewRoadmapAssessment) {
    el.btnNewRoadmapAssessment.addEventListener('click', () => {
      startNewSession('app', state.language);
      switchTab('viewVoiceApp', 'Voice Assistant');
      showToast('Starting new beneficiary assessment session...', 'add');
    });
  }
}

function toggleRoadmapAudio() {
  state.audioPlaying = !state.audioPlaying;

  if (state.audioPlaying) {
    if (el.playPauseIcon) el.playPauseIcon.textContent = 'pause';
    let progress = 10;
    if (el.audioProgressBar) el.audioProgressBar.style.width = progress + '%';

    if (state.currentRecommendation && state.currentRecommendation.spoken_summary) {
      speakText(state.currentRecommendation.spoken_summary, state.language, () => {
        state.audioPlaying = false;
        if (el.playPauseIcon) el.playPauseIcon.textContent = 'play_arrow';
        clearInterval(state.audioInterval);
      });
    }

    state.audioInterval = setInterval(() => {
      if (progress >= 100) {
        progress = 0;
        state.audioPlaying = false;
        if (el.playPauseIcon) el.playPauseIcon.textContent = 'play_arrow';
        clearInterval(state.audioInterval);
      } else {
        progress += 4;
      }
      if (el.audioProgressBar) el.audioProgressBar.style.width = progress + '%';
      const sec = Math.floor((progress / 100) * 60);
      if (el.currentTimeLabel) el.currentTimeLabel.textContent = `0:${sec < 10 ? '0' : ''}${sec}`;
    }, 500);

  } else {
    if (el.playPauseIcon) el.playPauseIcon.textContent = 'play_arrow';
    clearInterval(state.audioInterval);
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  }
}

// -------------------------------------------------------------
// Interactive Feature Phone IVR Simulator
// -------------------------------------------------------------
function startIvrTimer() {
  if (state.ivrInterval) clearInterval(state.ivrInterval);
  state.ivrInterval = setInterval(() => {
    if (state.ivrActive) {
      state.ivrTimer++;
      const mins = String(Math.floor(state.ivrTimer / 60)).padStart(2, '0');
      const secs = String(state.ivrTimer % 60).padStart(2, '0');
      if (el.timerBadge) el.timerBadge.textContent = `${mins}:${secs}`;
    }
  }, 1000);
}

function bindIvrEvents() {
  // Keypad keys
  el.keypadBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.getAttribute('data-key');
      handleIvrKeyPress(key);
    });
  });

  // Call Button
  if (el.keyCall) {
    el.keyCall.addEventListener('click', () => {
      state.ivrActive = true;
      state.ivrTimer = 0;
      if (el.callStatusBadge) {
        el.callStatusBadge.textContent = '● CALL CONNECTED';
        el.callStatusBadge.className = 'font-bold text-[11px] tracking-wide text-[#09140a]';
      }
      if (el.ivrPromptBox) {
        el.ivrPromptBox.textContent = '"प्रेस 1 हिंदी के लिए, 2 मराठीसाठी, 3 ਪੰਜਾਬੀ ਲਈ... ऋण व कौशल्य मार्गदर्शन के लिए 9 दबाएं"';
      }
      if (el.lcdAudioStatus) el.lcdAudioStatus.textContent = 'CALL CONNECTED';
      speakText("Welcome to PM-AJAY Toll-Free IVR Helpline. Press 1 for Hindi, 2 for Marathi, 3 for Punjabi.", 'en');
    });
  }

  // End Call Button
  if (el.keyEnd) {
    el.keyEnd.addEventListener('click', () => {
      state.ivrActive = false;
      if (el.callStatusBadge) {
        el.callStatusBadge.textContent = '○ CALL ENDED';
        el.callStatusBadge.className = 'font-bold text-[11px] tracking-wide text-[#7f1d1d]';
      }
      if (el.ivrPromptBox) {
        el.ivrPromptBox.textContent = '"कॉल समाप्त हुई (Call Ended). Toll-Free 1800-11-7625 पर कभी भी पुनः संपर्क करें।"';
      }
      if (el.lcdAudioStatus) el.lcdAudioStatus.textContent = 'DISCONNECTED';
      if (el.timerBadge) el.timerBadge.textContent = '--:--';
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    });
  }

  // D-Pad / Nav Button
  if (el.keyNav) {
    el.keyNav.addEventListener('click', () => {
      showToast('Speakerphone toggled on AJAY-PHONE.');
    });
  }
}

function handleIvrKeyPress(key) {
  if (!state.ivrActive && el.keyCall) {
    el.keyCall.click();
  }

  const res = IVR_RESPONSES[key];
  if (res) {
    if (el.lcdAudioStatus) el.lcdAudioStatus.textContent = `KEY [${key}] ${res.title}`;
    if (el.ivrPromptBox) el.ivrPromptBox.textContent = res.prompt;
    if (el.lcdDialed) el.lcdDialed.textContent = `DIALED: ${key}`;

    // Speak prompt
    speakText(res.prompt.replace(/"/g, ''), state.language);

    if (navigator.vibrate) {
      navigator.vibrate(30);
    }
  }
}

// -------------------------------------------------------------
// District Officer Admin Dashboard: GET /dashboard/summary
// -------------------------------------------------------------
async function loadAdminDashboard() {
  const district = el.districtSelect ? el.districtSelect.value : 'all';
  
  if (el.syncIcon) el.syncIcon.classList.add('animate-spin');

  try {
    const res = await fetch(`/dashboard/summary?district=${encodeURIComponent(district)}`);
    const data = await res.json();

    // 1. Stat Metric Values
    if (el.valEnrolments) el.valEnrolments.textContent = data.enrolments ?? 5;
    if (el.valPlacements) el.valPlacements.textContent = data.placements ?? 3;
    if (el.valDropouts) el.valDropouts.textContent = data.dropouts ?? 1;
    if (el.valTotalBeneficiaries) el.valTotalBeneficiaries.textContent = data.total_beneficiaries ?? 10;
    if (el.beneficiaryCountTag) el.beneficiaryCountTag.textContent = `${data.total_beneficiaries ?? 10} Records`;

    // 2. Trade Demand Trends
    renderDemandBars(data.skill_demand_by_trade || []);

    // 3. Regional Capacity vs Demand Analysis
    loadCapacityGap(state.selectedCapacityState || 'Delhi');

    // 4. Beneficiary Queue Cards
    renderBeneficiaryCards(data.beneficiaries || []);

    // Sync timestamp
    if (el.syncTime) {
      const now = new Date();
      el.syncTime.textContent = `Updated: ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }

  } catch (err) {
    console.error('Error fetching admin metrics:', err);
  } finally {
    if (el.syncIcon) {
      setTimeout(() => el.syncIcon.classList.remove('animate-spin'), 600);
    }
  }
}

async function loadCapacityGap(stateName = 'Delhi') {
  try {
    const res = await fetch(`/dashboard/capacity-gap?state=${encodeURIComponent(stateName)}`);
    if (!res.ok) return;
    const data = await res.json();
    renderCapacityGap(data);
  } catch (err) {
    console.error('Error loading capacity gap data:', err);
  }
}

function renderCapacityGap(report) {
  if (!report) return;

  if (el.capacityActiveStateLabel) {
    el.capacityActiveStateLabel.textContent = report.state === 'all' ? 'All Regions (Consolidated)' : report.state;
  }
  if (el.capacityTotalDemand) {
    el.capacityTotalDemand.textContent = report.total_demand || 0;
  }
  if (el.capacityTotalEst) {
    el.capacityTotalEst.textContent = report.total_estimated_capacity || 0;
  }
  if (el.capacityOverallBadge && report.overall_gap) {
    el.capacityOverallBadge.textContent = report.overall_gap.short_label;
    el.capacityOverallBadge.className = `inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${report.overall_gap.badge_class}`;
  }

  if (!el.capacityTableContainer) return;
  el.capacityTableContainer.innerHTML = '';

  const trades = report.trades || [];
  if (!trades.length) {
    el.capacityTableContainer.innerHTML = '<p class="text-xs text-on-surface-variant p-3 text-center">No capacity benchmarking data for this state.</p>';
    return;
  }

  trades.forEach(t => {
    const card = document.createElement('div');
    card.className = 'bg-surface-container-low/50 hover:bg-surface-container-low border border-secondary/15 rounded-xl p-space-sm flex flex-col gap-1.5 transition-all';

    const demandPct = t.estimated_capacity > 0
      ? Math.min(Math.round((t.demand / t.estimated_capacity) * 100), 100)
      : (t.demand > 0 ? 100 : 0);

    card.innerHTML = `
      <div class="flex items-start justify-between gap-space-xs">
        <div class="flex items-center gap-2 min-w-0">
          <span class="text-xl flex-shrink-0">${TRADE_ICONS_EMOJI[t.trade_key] || '💼'}</span>
          <div class="min-w-0">
            <h4 class="font-display font-bold text-xs text-on-surface truncate">${t.trade_name}</h4>
            <p class="text-[10px] text-on-surface-variant truncate">${t.qp_name || ''} • <span class="font-semibold text-secondary">${t.qp_code || ''}</span> (${t.nsqf_level || 'NSQF L4'})</p>
          </div>
        </div>
        <div class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${t.gap_badge_class} flex-shrink-0">
          <span class="material-symbols-outlined text-[13px]">${t.gap_icon}</span>
          <span>${t.gap_label}</span>
        </div>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 gap-2 bg-surface-container-lowest p-2 rounded-lg text-xs mt-0.5">
        <div class="flex flex-col">
          <span class="text-[10px] text-secondary font-bold flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-secondary"></span> Live Demand
          </span>
          <span class="font-bold text-sm text-on-surface mt-0.5">${t.demand} <span class="text-[10px] font-normal text-on-surface-variant">applicants</span></span>
        </div>
        <div class="flex flex-col">
          <span class="text-[10px] text-amber-700 font-bold flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span> Est. Capacity*
          </span>
          <span class="font-bold text-sm text-on-surface mt-0.5">${t.estimated_capacity} <span class="text-[10px] font-normal text-on-surface-variant">seats (illustrative)</span></span>
        </div>
        <div class="flex flex-col col-span-2 sm:col-span-1">
          <span class="text-[10px] text-on-surface-variant font-medium">Demand vs Capacity Balance</span>
          <span class="font-bold text-xs text-on-surface mt-0.5">${Math.round(t.ratio * 100)}% (${t.difference > 0 ? '+' + t.difference + ' deficit' : t.difference + ' seats'})</span>
        </div>
      </div>

      <!-- Capacity Visual Comparison Bar -->
      <div class="w-full mt-0.5">
        <div class="flex justify-between text-[10px] text-on-surface-variant mb-0.5 font-medium">
          <span>Demand Utilization</span>
          <span>${t.demand} / ${t.estimated_capacity} seats</span>
        </div>
        <div class="w-full bg-surface-container-high h-2 rounded-full overflow-hidden flex">
          <div class="${t.gap_status === 'demand_exceeding' ? 'bg-[#ef4444]' : t.gap_status === 'roughly_matched' ? 'bg-[#3b82f6]' : 'bg-[#10b981]'} h-full rounded-full transition-all duration-700" style="width: ${demandPct}%"></div>
        </div>
      </div>
    `;

    el.capacityTableContainer.appendChild(card);
  });
}

function renderDemandBars(trades = []) {
  if (!el.demandBarsContainer) return;
  el.demandBarsContainer.innerHTML = '';

  if (!trades.length) {
    el.demandBarsContainer.innerHTML = '<p class="text-xs text-on-surface-variant">No trade demands registered yet.</p>';
    return;
  }

  const total = trades.reduce((acc, t) => acc + t.count, 0) || 1;
  const barColors = ['bg-secondary', 'bg-secondary-container', 'bg-primary-container', 'bg-tertiary-fixed-dim'];

  trades.forEach((t, i) => {
    const pct = Math.round((t.count / total) * 100);
    const colorClass = barColors[i % barColors.length];
    const row = document.createElement('div');
    row.className = 'flex flex-col gap-1';
    row.innerHTML = `
      <div class="flex justify-between items-center text-xs">
        <span class="text-on-surface font-semibold flex items-center gap-1.5">
          <span class="material-symbols-outlined text-[15px] text-secondary">${TRADE_ICONS[t.trade_key] || 'work'}</span>
          ${t.trade}
        </span>
        <span class="text-secondary font-bold">${pct}% (${t.count})</span>
      </div>
      <div class="w-full bg-surface-container-low h-2 rounded-full overflow-hidden flex">
        <div class="${colorClass} h-full rounded-full transition-all duration-700" style="width: ${pct}%"></div>
      </div>
    `;
    el.demandBarsContainer.appendChild(row);
  });
}

function renderBeneficiaryCards(list = []) {
  if (!el.beneficiaryTableBody) return;
  el.beneficiaryTableBody.innerHTML = '';

  if (!list.length) {
    el.beneficiaryTableBody.innerHTML = '<p class="text-xs text-on-surface-variant p-4 text-center">No beneficiaries found for this district filter.</p>';
    return;
  }

  list.forEach(b => {
    const card = document.createElement('div');
    card.className = 'bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col gap-space-sm relative overflow-hidden transition-all';
    
    // Status Badge colors
    const isEnrolled = b.status === 'enrolled';
    const isPlaced = b.status === 'placed';
    const isDropped = b.status === 'dropped';
    const statusBg = isPlaced ? 'bg-surface-variant text-secondary' :
                     isEnrolled ? 'bg-[#ecfdf5] text-[#065f46]' :
                     isDropped ? 'bg-error-container text-error' : 'bg-amber-50 text-[#b87500]';

    const initials = b.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'AJ';

    card.innerHTML = `
      <div class="flex items-start justify-between">
        <div class="flex items-center gap-space-sm min-w-0">
          <div class="w-9 h-9 rounded-full bg-surface-container flex items-center justify-center font-display font-bold text-xs text-on-surface flex-shrink-0">
            ${initials}
          </div>
          <div class="flex flex-col min-w-0">
            <div class="flex items-center gap-1.5">
              <span class="text-xs font-bold text-on-surface truncate">${b.name}</span>
              <span class="text-[10px] bg-surface-container-low text-on-surface-variant px-1.5 py-0.2 rounded font-medium">${b.education || '10th Pass'}</span>
            </div>
            <span class="text-[10px] text-on-surface-variant">${b.location} • ID: ${b.id.substring(0, 8)}</span>
          </div>
        </div>
        <div class="flex items-center gap-1 ${statusBg} px-2 py-0.5 rounded-full text-[10px] font-bold flex-shrink-0">
          <span class="w-1.5 h-1.5 rounded-full ${isPlaced ? 'bg-secondary' : isEnrolled ? 'bg-[#10b981]' : 'bg-amber-500'}"></span>
          <span class="capitalize">${b.status}</span>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-space-xs bg-surface-container-low/50 p-space-xs rounded-lg text-xs">
        <div class="flex flex-col">
          <span class="text-on-surface-variant text-[10px]">Applied Trade</span>
          <span class="text-on-surface font-semibold truncate">${b.trade}</span>
        </div>
        <div class="flex flex-col">
          <span class="text-on-surface-variant text-[10px]">Intake Mode</span>
          <span class="text-on-surface font-semibold flex items-center gap-1 capitalize">
            <span class="material-symbols-outlined text-[13px] text-secondary">devices</span>
            ${b.entry_mode}
          </span>
        </div>
      </div>

      <div class="flex items-center justify-between pt-1">
        <select class="status-dropdown text-[11px] bg-surface-container-low border border-secondary/15 rounded-md px-2 py-1 font-semibold text-on-surface cursor-pointer" data-id="${b.id}">
          <option value="enrolled" ${b.status === 'enrolled' ? 'selected' : ''}>Status: Enrolled</option>
          <option value="placed" ${b.status === 'placed' ? 'selected' : ''}>Status: Placed</option>
          <option value="dropped" ${b.status === 'dropped' ? 'selected' : ''}>Status: Dropped</option>
          <option value="no_contact" ${b.status === 'no_contact' ? 'selected' : ''}>Status: Pending</option>
        </select>
        <button class="btn-view-beneficiary bg-secondary-fixed text-on-secondary-fixed hover:bg-secondary hover:text-on-secondary px-2.5 py-1 rounded-lg text-[11px] font-bold flex items-center gap-1 transition-colors" data-name="${b.name}">
          <span class="material-symbols-outlined text-[14px]">visibility</span>
          <span>View File</span>
        </button>
      </div>
    `;
    el.beneficiaryTableBody.appendChild(card);
  });

  // Attach status change events
  document.querySelectorAll('.status-dropdown').forEach(sel => {
    sel.addEventListener('change', async (e) => {
      const bId = e.target.getAttribute('data-id');
      const newStatus = e.target.value;
      try {
        const res = await fetch(`/followup/${bId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
          showToast(`Beneficiary status updated to ${newStatus}`, 'check_circle');
          loadAdminDashboard();
        }
      } catch (err) {
        showToast('Failed to update status');
      }
    });
  });

  // Attach View File click events
  document.querySelectorAll('.btn-view-beneficiary').forEach(btn => {
    btn.addEventListener('click', () => {
      const name = btn.getAttribute('data-name');
      showToast(`Loading PM-AJAY beneficiary dossier for ${name}...`, 'folder_open');
    });
  });
}

function bindAdminEvents() {
  if (el.districtSelect) {
    el.districtSelect.addEventListener('change', () => {
      showToast(`Loading metrics for ${el.districtSelect.value}...`);
      loadAdminDashboard();
    });
  }

  if (el.btnRefreshDashboard) {
    el.btnRefreshDashboard.addEventListener('click', () => {
      showToast('Live synchronization with State NIC server initiated...', 'sync');
      loadAdminDashboard();
    });
  }

  if (el.btnExportReport) {
    el.btnExportReport.addEventListener('click', () => {
      showToast('Generating official PM-AJAY Excel report for district...', 'file_download');
    });
  }

  if (el.btnBulkSms) {
    el.btnBulkSms.addEventListener('click', () => {
      showToast('SMS Gateway: Dispatched stipend reminders to all registered numbers.', 'cell_tower');
    });
  }

  // Regional Capacity State Filter Tabs
  if (el.capacityStateTabs) {
    el.capacityStateTabs.forEach(btn => {
      btn.addEventListener('click', () => {
        const stateKey = btn.getAttribute('data-state');
        if (!stateKey) return;
        state.selectedCapacityState = stateKey;

        // Visual toggle on buttons
        el.capacityStateTabs.forEach(b => {
          b.className = 'capacity-state-btn text-xs font-semibold px-3 py-1.5 rounded-lg border transition-all active:scale-95 bg-surface-container-low text-on-surface-variant border-secondary/15 hover:bg-surface-container';
        });
        btn.className = 'capacity-state-btn text-xs font-bold px-3 py-1.5 rounded-lg border transition-all active:scale-95 bg-secondary text-on-secondary border-secondary shadow-sm';

        loadCapacityGap(stateKey);
      });
    });
  }
}

// -------------------------------------------------------------
// Speech Synthesis (TTS) & Audio Player Helper
// -------------------------------------------------------------
let activeAudioElement = null;
let activeUtterance = null;

function speak(text, audioBase64 = null, onEnd = null) {
  if (!text && !audioBase64) {
    if (onEnd) onEnd();
    return;
  }

  unlockSpeechAndAudio();

  // 1. If base64 audio is provided from backend (Bhashini WAV), play it directly
  if (audioBase64) {
    try {
      if (activeAudioElement) {
        activeAudioElement.pause();
        activeAudioElement = null;
      }
      activeAudioElement = new Audio('data:audio/wav;base64,' + audioBase64);
      activeAudioElement.volume = 1.0;
      activeAudioElement.onended = () => {
        activeAudioElement = null;
        if (el.ttsIcon) el.ttsIcon.textContent = 'volume_up';
        if (onEnd) onEnd();
      };
      activeAudioElement.onerror = (e) => {
        console.warn('Audio playback error, falling back to browser speechSynthesis:', e);
        activeAudioElement = null;
        speakViaBrowserTTS(text, onEnd);
      };
      if (el.ttsIcon) el.ttsIcon.textContent = 'graphic_eq';
      const playPromise = activeAudioElement.play();
      if (playPromise !== undefined) {
        playPromise.catch(err => {
          console.warn('Audio play() blocked by autoplay policy, falling back to speechSynthesis:', err);
          speakViaBrowserTTS(text, onEnd);
        });
      }
      return;
    } catch (err) {
      console.warn('Audio instantiation failed, using speechSynthesis:', err);
    }
  }

  // 2. Fallback to browser's native SpeechSynthesis (Free, runs offline without API keys!)
  speakViaBrowserTTS(text, onEnd);
}

// Backward-compatible alias for speakText
function speakText(text, lang = null, audioBase64 = null, onEnd = null) {
  speak(text, audioBase64, onEnd);
}

function speakViaBrowserTTS(text, onEnd = null) {
  if (!('speechSynthesis' in window)) {
    console.warn('SpeechSynthesis is not supported in this browser.');
    if (onEnd) onEnd();
    return;
  }

  try {
    window.speechSynthesis.cancel();
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
  } catch (e) {}

  const cleanText = (text || '')
    .replace(/[*_#`~]/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/^"+|"+$/g, '')
    .trim();

  if (!cleanText) {
    if (onEnd) onEnd();
    return;
  }

  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.volume = 1.0;
  utterance.rate = 1.0;
  utterance.pitch = 1.0;

  if (!cachedVoices.length) {
    refreshVoices();
  }

  const currentLang = state.language || 'en';
  const targetLocale = LANG_LOCALES[currentLang] || 'en-IN';

  let voice = null;
  if (cachedVoices.length) {
    if (currentLang === 'hi') {
      voice = cachedVoices.find(v => v.lang.toLowerCase().startsWith('hi') || v.name.toLowerCase().includes('hindi')) ||
              cachedVoices.find(v => v.lang.includes('IN') || v.name.includes('India'));
    } else if (currentLang === 'mr') {
      voice = cachedVoices.find(v => v.lang.toLowerCase().startsWith('mr') || v.name.toLowerCase().includes('marathi')) ||
              cachedVoices.find(v => v.lang.toLowerCase().startsWith('hi'));
    } else if (currentLang === 'pa') {
      voice = cachedVoices.find(v => v.lang.toLowerCase().startsWith('pa') || v.name.toLowerCase().includes('punjabi'));
    } else if (currentLang === 'ta') {
      voice = cachedVoices.find(v => v.lang.toLowerCase().startsWith('ta') || v.name.toLowerCase().includes('tamil'));
    } else {
      // English default
      voice = cachedVoices.find(v => v.lang === 'en-IN' || v.lang.replace('_', '-').toLowerCase() === 'en-in') ||
              cachedVoices.find(v => v.lang.startsWith('en') && (v.name.includes('India') || v.name.includes('Heera') || v.name.includes('Ravi'))) ||
              cachedVoices.find(v => v.lang.startsWith('en')) ||
              cachedVoices[0];
    }
  }

  // Windows SAPI5 safeguard: if non-Latin text is to be read but ONLY English voice exists
  const hasIndicScript = /[\u0900-\u097F\u0A00-\u0A7F\u0B80-\u0BFF]/.test(cleanText);
  if (hasIndicScript && voice && !voice.lang.includes('hi') && !voice.lang.includes('IN') && !voice.name.toLowerCase().includes('hindi')) {
    const fallbackEnglish = INITIAL_PROMPTS_SUB[currentLang] || "Your voice information has been captured by Nivara AI.";
    utterance.text = fallbackEnglish;
    utterance.lang = 'en-US';
  } else if (voice) {
    utterance.voice = voice;
    utterance.lang = voice.lang;
  } else {
    utterance.lang = targetLocale;
  }

  utterance.onstart = () => {
    if (el.ttsIcon) el.ttsIcon.textContent = 'graphic_eq';
  };

  utterance.onend = () => {
    activeUtterance = null;
    if (el.ttsIcon) el.ttsIcon.textContent = 'volume_up';
    if (onEnd) onEnd();
  };

  utterance.onerror = (e) => {
    console.warn('SpeechSynthesis playback note:', e);
    activeUtterance = null;
    if (el.ttsIcon) el.ttsIcon.textContent = 'volume_up';
    if (onEnd) onEnd();
  };

  activeUtterance = utterance;

  try {
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
    window.speechSynthesis.speak(utterance);
  } catch (err) {
    console.warn('speechSynthesis.speak execution error:', err);
  }

  // Periodic resume guard against Chrome 15-second background speech pause bug
  const keepAliveTimer = setInterval(() => {
    if (!window.speechSynthesis.speaking) {
      clearInterval(keepAliveTimer);
    } else if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
  }, 3000);
}

// -------------------------------------------------------------
// Toast Notification Utility
// -------------------------------------------------------------
let toastTimer = null;
function showToast(message, icon = 'info') {
  if (!el.toast) return;
  if (el.toastMessage) el.toastMessage.textContent = message;
  if (el.toastIcon) el.toastIcon.textContent = icon;

  el.toast.classList.remove('opacity-0', 'pointer-events-none');
  el.toast.classList.add('opacity-100');

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.toast.classList.remove('opacity-100');
    el.toast.classList.add('opacity-0', 'pointer-events-none');
  }, 3200);
}

// Clock Utility for LCD Screen
function updateClock() {
  if (el.lcdTime) {
    const now = new Date();
    el.lcdTime.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
}
