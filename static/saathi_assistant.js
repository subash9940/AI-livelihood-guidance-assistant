/**
 * Nivara Saathi — Personal AI Livelihood Assistant (Phase 4)
 * Siri-like voice-first assistant accessible from every page via a floating button.
 * Features: Consented Onboarding Profile, View/Edit/Delete Data,
 * Daily Next Best Step, Deadline & Document Reminders, Goal Progress Tracker,
 * Suggested Schemes on Profile Changes, Big Wake-Style Mic & TTS.
 */

(function () {
  let isListening = false;
  let recognitionInstance = null;
  let saathiMemory = null;

  function getActiveUserId() {
    let uid = localStorage.getItem('nivara_user_id');
    if (!uid) {
      uid = 'user_' + Math.random().toString(36).substring(2, 9);
      localStorage.setItem('nivara_user_id', uid);
    }
    return uid;
  }

  function initSpeech() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return null;
    const rec = new SpeechRec();
    rec.continuous = false;
    rec.interimResults = true;
    return rec;
  }

  // -------------------------------------------------------------
  // Load or Refresh Saathi Proactive Data
  // -------------------------------------------------------------
  async function refreshSaathiData() {
    const uid = getActiveUserId();
    try {
      // 1. Fetch proactive bundle
      const proResp = await fetch(`/rag/saathi/proactive/${encodeURIComponent(uid)}?region=delhi`);
      const proData = await proResp.json();

      // 2. Fetch full memory bundle
      const memResp = await fetch(`/rag/memory/${encodeURIComponent(uid)}`);
      saathiMemory = await memResp.json();

      renderProactiveCards(proData);
      renderProfileForm(saathiMemory.profile, saathiMemory.active_goal);
      renderConsentStatus(saathiMemory.consent_given);
    } catch (err) {
      console.warn('Could not fetch Saathi proactive data:', err);
    }
  }

  function renderProactiveCards(data) {
    if (!data) return;

    // 1. Next Best Step Card
    const nextStepContainer = document.getElementById('saathiNextBestStepCard');
    if (nextStepContainer && data.next_best_step) {
      const step = data.next_best_step;
      nextStepContainer.innerHTML = `
        <div class="flex items-start gap-3">
          <div class="w-9 h-9 rounded-xl bg-saffron/15 text-saffron flex items-center justify-center flex-shrink-0 mt-0.5">
            <span class="material-symbols-outlined text-[20px]">flag</span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between gap-1">
              <span class="text-[10px] font-bold uppercase tracking-wider text-saffron">Daily Next Best Step</span>
              <span class="text-[10px] text-on-surface-variant font-medium">Step ${data.goal_progress?.current_step || 1} of 4</span>
            </div>
            <h4 class="font-bold text-xs text-on-surface mt-0.5">${escapeHtml(step.title)}</h4>
            <p class="text-[11px] text-on-surface-variant mt-1 leading-relaxed">${escapeHtml(step.description)}</p>
          </div>
        </div>
      `;
    }

    // 2. Goal Progress Tracker
    const goalTitleEl = document.getElementById('saathiGoalTitle');
    const goalPctEl = document.getElementById('saathiGoalPct');
    const goalBarEl = document.getElementById('saathiGoalBar');
    const goalStepDesc = document.getElementById('saathiGoalStepDesc');
    
    if (data.goal_progress) {
      const gp = data.goal_progress;
      if (goalTitleEl) goalTitleEl.textContent = gp.goal || "PM-AJAY NSQF Skill Certification";
      if (goalPctEl) goalPctEl.textContent = `${gp.percentage}% Complete`;
      if (goalBarEl) goalBarEl.style.width = `${gp.percentage}%`;
      if (goalStepDesc) goalStepDesc.textContent = `Current Stage: ${gp.current_step_title}`;
    }

    // 3. Reminders
    const remindersContainer = document.getElementById('saathiRemindersList');
    if (remindersContainer && data.reminders) {
      remindersContainer.innerHTML = data.reminders.map(rem => {
        const icon = rem.type === 'deadline' ? 'event_upcoming' : 'badge';
        const badgeColor = rem.type === 'deadline' ? 'text-amber bg-amber/10 border-amber/20' : 'text-secondary bg-secondary/10 border-secondary/20';
        return `
          <div class="bg-surface-container-low p-2.5 rounded-xl border border-border-subtle flex items-start gap-2.5">
            <div class="w-7 h-7 rounded-lg ${badgeColor} border flex items-center justify-center flex-shrink-0 mt-0.5">
              <span class="material-symbols-outlined text-[16px]">${icon}</span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between gap-1">
                <span class="font-bold text-[11px] text-on-surface truncate">${escapeHtml(rem.title)}</span>
                <span class="text-[10px] text-on-surface-variant flex-shrink-0 font-medium">${escapeHtml(rem.due_date)}</span>
              </div>
              <p class="text-[11px] text-on-surface-variant leading-relaxed mt-0.5">${escapeHtml(rem.detail)}</p>
            </div>
          </div>
        `;
      }).join('');
    }

    // 4. Suggested Schemes based on profile
    const suggestedContainer = document.getElementById('saathiSuggestedSchemesList');
    if (suggestedContainer && data.suggested_schemes) {
      suggestedContainer.innerHTML = data.suggested_schemes.map(sch => {
        const isEligible = sch.eligible;
        const badge = isEligible
          ? `<span class="bg-[#ecfdf5] text-[#065f46] text-[10px] font-bold px-2 py-0.5 rounded-full">Eligible (${sch.match_percentage}%)</span>`
          : `<span class="bg-surface-container-high text-on-surface-variant text-[10px] font-semibold px-2 py-0.5 rounded-full">${sch.match_percentage}% Match</span>`;
        return `
          <div class="bg-surface-container-low p-2.5 rounded-xl border border-border-subtle flex items-center justify-between gap-2">
            <div class="flex items-center gap-2 min-w-0">
              <span class="material-symbols-outlined text-secondary text-[18px]">verified</span>
              <div class="truncate">
                <h5 class="text-xs font-bold text-on-surface truncate">${escapeHtml(sch.scheme_name)}</h5>
                <span class="text-[10px] text-on-surface-variant">${sch.met_criteria.length} criteria satisfied</span>
              </div>
            </div>
            ${badge}
          </div>
        `;
      }).join('');
    }
  }

  function renderProfileForm(profile, activeGoal) {
    if (!profile) profile = {};
    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el && val !== undefined) el.value = val;
    };

    setVal('saathiName', profile.name || '');
    setVal('saathiAge', profile.age || '');
    setVal('saathiGender', profile.gender || 'male');
    setVal('saathiEducation', profile.education_level || profile.education || '10th Standard');
    setVal('saathiSkills', Array.isArray(profile.skills) ? profile.skills.join(', ') : (profile.skills || ''));
    setVal('saathiDistrict', profile.district || profile.location || 'South Delhi');
    setVal('saathiIncome', profile.income_bracket || 'Under ₹1.5 Lakh');
    setVal('saathiCategory', profile.category || 'SC');
    setVal('saathiGoal', activeGoal || profile.goals || 'Become a certified Solar PV Installer, NSQF 4');
  }

  function renderConsentStatus(consented) {
    const banner = document.getElementById('saathiConsentBanner');
    const badge = document.getElementById('saathiConsentBadge');
    if (consented) {
      if (banner) banner.classList.add('hidden');
      if (badge) {
        badge.innerHTML = `<span class="material-symbols-outlined text-[12px] text-[#10b981]">verified_user</span> Consented Profile`;
        badge.className = "text-[10px] font-bold text-[#065f46] bg-[#ecfdf5] px-2 py-0.5 rounded-full flex items-center gap-1 border border-[#a7f3d0]";
      }
    } else {
      if (banner) banner.classList.remove('hidden');
      if (badge) {
        badge.innerHTML = `<span class="material-symbols-outlined text-[12px] text-amber">privacy_tip</span> Consent Pending`;
        badge.className = "text-[10px] font-bold text-amber bg-amber/10 px-2 py-0.5 rounded-full flex items-center gap-1 border border-amber/20";
      }
    }
  }

  // -------------------------------------------------------------
  // Saathi Conversational Messaging
  // -------------------------------------------------------------
  function appendSaathiUserBubble(text) {
    const container = document.getElementById('saathiChatContainer');
    if (!container) return;
    const div = document.createElement('div');
    div.className = 'flex items-start justify-end gap-2 max-w-[85%] self-end';
    div.innerHTML = `
      <div class="bg-gradient-to-r from-secondary to-secondary-container text-on-secondary p-3 rounded-2xl rounded-tr-sm text-xs shadow-sm flex flex-col gap-1">
        <p class="leading-relaxed font-medium">${escapeHtml(text)}</p>
        <span class="text-[9px] text-on-secondary/70 self-end">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
      </div>
      <div class="w-6 h-6 rounded-full bg-secondary text-on-secondary flex items-center justify-center flex-shrink-0 text-[10px] font-bold">
        You
      </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  function appendSaathiTyping() {
    const container = document.getElementById('saathiChatContainer');
    if (!container) return null;
    const div = document.createElement('div');
    div.id = 'saathiTypingIndicator';
    div.className = 'flex items-start gap-2 max-w-[90%]';
    div.innerHTML = `
      <div class="w-7 h-7 rounded-full bg-gradient-to-tr from-saffron via-indigo to-emerald flex items-center justify-center flex-shrink-0 text-white text-[11px] font-bold shadow-sm animate-spin">
        ✦
      </div>
      <div class="bg-surface-container-lowest text-on-surface p-3 rounded-2xl rounded-tl-sm text-xs shadow-sm border border-border-subtle flex items-center gap-1.5 text-on-surface-variant">
        <span class="w-1.5 h-1.5 rounded-full bg-saffron animate-bounce"></span>
        <span class="w-1.5 h-1.5 rounded-full bg-indigo animate-bounce [animation-delay:0.2s]"></span>
        <span class="w-1.5 h-1.5 rounded-full bg-emerald animate-bounce [animation-delay:0.4s]"></span>
        <span class="text-[11px] ml-1">Nivara Saathi is thinking &amp; searching Delhi knowledge...</span>
      </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
  }

  function appendSaathiAssistantBubble(data) {
    const container = document.getElementById('saathiChatContainer');
    const typing = document.getElementById('saathiTypingIndicator');
    if (typing) typing.remove();
    if (!container) return;

    const answer = data.answer || "I could not retrieve an answer at this time.";
    const citations = data.citations || [];
    const div = document.createElement('div');
    div.className = 'flex items-start gap-2 max-w-[92%]';

    let citationsHtml = '';
    if (citations.length > 0) {
      citationsHtml = `<div class="flex flex-wrap items-center gap-1 pt-1 mt-1 border-t border-border-subtle/60">
        <span class="text-[10px] text-on-surface-variant font-bold">Official Sources:</span>`;
      citations.forEach(c => {
        citationsHtml += `
          <a href="${c.url}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-0.5 text-[10px] bg-surface-container text-secondary hover:underline px-2 py-0.5 rounded-full border border-border-subtle">
            <span>${escapeHtml(c.name.split('(')[0].trim())}</span>
            <span class="material-symbols-outlined text-[10px]">launch</span>
          </a>
        `;
      });
      citationsHtml += `</div>`;
    }

    const formattedAnswer = formatMarkdown(answer);
    const isAnswerVerified = citations.length > 0 && citations.every(c => c.verification_status === 'verified');
    const answerBadge = isAnswerVerified
      ? `<span class="inline-flex items-center gap-1 text-[10px] font-bold text-[#065f46] bg-[#ecfdf5] border border-[#a7f3d0] px-2 py-0.5 rounded">
           <span class="material-symbols-outlined text-[11px]">verified</span> Verified ${escapeHtml(citations[0].last_verified || '')}
         </span>`
      : `<span class="inline-flex items-center gap-1 text-[10px] font-semibold text-[#92400e] bg-[#fffbeb] border border-[#f59e0b]/50 px-2 py-0.5 rounded">
           <span class="material-symbols-outlined text-[11px] text-[#d97706]">warning</span> Sample data - verify on official site
         </span>`;

    div.innerHTML = `
      <div class="w-7 h-7 rounded-full bg-gradient-to-tr from-saffron via-indigo to-emerald flex items-center justify-center flex-shrink-0 text-white text-[11px] font-bold shadow-md">
        ✦
      </div>
      <div class="bg-surface-container-lowest text-on-surface p-3.5 rounded-2xl rounded-tl-sm text-xs shadow-sm border border-border-subtle flex flex-col gap-1.5 flex-1 min-w-0">
        <div class="leading-relaxed text-on-surface space-y-1">${formattedAnswer}</div>
        ${citationsHtml}
        <div class="flex items-center justify-between gap-2 pt-1 border-t border-border-subtle/50 text-[10px] flex-wrap">
          <div class="flex items-center gap-1.5 flex-wrap">
            ${answerBadge}
            ${citations.length > 0 ? `
              <a href="${citations[0].url}" target="_blank" rel="noopener noreferrer" class="text-secondary font-semibold hover:underline inline-flex items-center gap-0.5">
                <span>Official Link</span>
                <span class="material-symbols-outlined text-[10px]">open_in_new</span>
              </a>` : ''}
          </div>
          <button class="btn-saathi-listen text-secondary font-bold flex items-center gap-0.5 hover:underline">
            <span class="material-symbols-outlined text-[14px]">volume_up</span>
            <span>Listen / सुनें</span>
          </button>
        </div>
      </div>
    `;

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    const listenBtn = div.querySelector('.btn-saathi-listen');
    if (listenBtn) {
      listenBtn.addEventListener('click', () => {
        if (typeof speak === 'function') speak(answer);
      });
    }

    // Automatically speak the response if voice-first interaction was initiated
    if (isListening || document.getElementById('saathiVoiceVisualizer')?.classList.contains('active-speaking')) {
      if (typeof speak === 'function') speak(answer);
    }
  }

  async function submitSaathiQuery(text) {
    const clean = (text || '').trim();
    if (!clean) return;

    appendSaathiUserBubble(clean);
    appendSaathiTyping();

    const input = document.getElementById('saathiTextInput');
    if (input) input.value = '';

    const uid = getActiveUserId();
    const currentLang = window.state ? window.state.language : 'en';

    try {
      const resp = await fetch('/rag/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: clean,
          user_id: uid,
          language: currentLang,
          region: 'delhi'
        })
      });

      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      if (data.method) {
        const normEl = document.getElementById('telemetryNormMethod');
        if (normEl) normEl.textContent = data.method;
      }
      appendSaathiAssistantBubble(data);

      // Refresh proactive cards in case profile changed
      refreshSaathiData();
    } catch (e) {
      console.error('Error in Saathi query:', e);
      const typing = document.getElementById('saathiTypingIndicator');
      if (typing) typing.remove();
      appendSaathiAssistantBubble({
        answer: "I apologize, but I could not reach the Nivara knowledge pipeline. Please consult https://socialjustice.gov.in or call 1800-11-762529."
      });
    }
  }

  // -------------------------------------------------------------
  // Profile & Consent Management
  // -------------------------------------------------------------
  async function saveProfileAndConsent(isConsented = true) {
    const uid = getActiveUserId();
    const name = document.getElementById('saathiName')?.value?.trim() || 'Beneficiary';
    const age = parseInt(document.getElementById('saathiAge')?.value) || 22;
    const gender = document.getElementById('saathiGender')?.value || 'male';
    const education = document.getElementById('saathiEducation')?.value || '10th Standard';
    const skillsRaw = document.getElementById('saathiSkills')?.value || '';
    const skills = skillsRaw.split(',').map(s => s.trim()).filter(Boolean);
    const district = document.getElementById('saathiDistrict')?.value || 'South Delhi';
    const income = document.getElementById('saathiIncome')?.value || 'Under ₹1.5 Lakh';
    const category = document.getElementById('saathiCategory')?.value || 'SC';
    const goal = document.getElementById('saathiGoal')?.value?.trim() || 'Become a certified Solar PV Installer, NSQF 4';

    const profilePayload = {
      name, age, gender, education_level: education, education, skills,
      district, location: district, state: 'Delhi', income_bracket: income,
      annual_income: income.includes('1.5') ? 120000 : 200000,
      category, goals: goal, documents_held: ["Aadhaar Card", "Caste Certificate (SC)"]
    };

    try {
      // 1. Update memory profile
      await fetch(`/rag/memory/${encodeURIComponent(uid)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile: profilePayload,
          active_goal: goal
        })
      });

      // 2. Record consent
      await fetch(`/rag/memory/${encodeURIComponent(uid)}/consent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ consented: isConsented })
      });

      if (typeof showToast === 'function') {
        showToast('Your consented profile & goal have been securely saved!', 'verified');
      }

      // Close profile drawer / switch back to assistant view
      toggleProfileView(false);
      refreshSaathiData();
    } catch (e) {
      console.error('Error saving profile:', e);
    }
  }

  async function deleteUserData() {
    if (!confirm('Are you sure you want to permanently delete all your profile data, conversation history, and saved plans? (Right to be Forgotten)')) {
      return;
    }
    const uid = getActiveUserId();
    try {
      await fetch(`/rag/memory/${encodeURIComponent(uid)}`, {
        method: 'DELETE'
      });
      localStorage.removeItem('nivara_user_id');
      localStorage.removeItem('pathway_chat_html_' + uid);
      if (typeof showToast === 'function') {
        showToast('All your personal data has been completely erased.', 'delete_forever');
      }
      location.reload();
    } catch (e) {
      console.error('Error deleting data:', e);
    }
  }

  function toggleProfileView(showProfile) {
    const chatView = document.getElementById('saathiChatView');
    const profileView = document.getElementById('saathiProfileView');
    if (showProfile) {
      if (chatView) chatView.classList.add('hidden');
      if (profileView) profileView.classList.remove('hidden');
    } else {
      if (chatView) chatView.classList.remove('hidden');
      if (profileView) profileView.classList.add('hidden');
    }
  }

  function formatMarkdown(text) {
    if (!text) return '';
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^[•\-\*]\s+(.*)$/gm, '<li class="ml-3 list-disc">$1</li>')
      .replace(/(<li.*<\/li>)/g, '<ul class="my-1">$1</ul>')
      .replace(/\n\n/g, '<br/>');
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // -------------------------------------------------------------
  // Voice Input (Siri-like Wake Mic)
  // -------------------------------------------------------------
  function setupVoiceInteractions() {
    const bigMicBtn = document.getElementById('saathiBigMicBtn');
    const visualizer = document.getElementById('saathiVoiceVisualizer');
    const statusLabel = document.getElementById('saathiVoiceStatusText');

    if (!bigMicBtn) return;

    bigMicBtn.addEventListener('click', () => {
      if (!recognitionInstance) {
        recognitionInstance = initSpeech();
      }
      if (!recognitionInstance) {
        if (typeof showToast === 'function') {
          showToast('Speech recognition not supported in this browser. Please type.', 'mic_off');
        }
        return;
      }

      if (isListening) {
        recognitionInstance.stop();
        return;
      }

      const lang = (window.state && window.state.language === 'hi') ? 'hi-IN' : 'en-IN';
      recognitionInstance.lang = lang;

      recognitionInstance.onstart = () => {
        isListening = true;
        bigMicBtn.classList.add('scale-110', 'ring-8', 'ring-secondary/40', 'animate-pulse');
        if (visualizer) visualizer.classList.remove('hidden');
        if (statusLabel) statusLabel.textContent = "Listening to you... Speak in Hindi or English";
      };

      recognitionInstance.onresult = (evt) => {
        let transcript = '';
        for (let i = evt.resultIndex; i < evt.results.length; i++) {
          transcript += evt.results[i][0].transcript;
        }
        if (statusLabel) statusLabel.textContent = `"${transcript}"`;
      };

      recognitionInstance.onerror = (e) => {
        console.warn('Saathi speech error:', e.error);
        isListening = false;
        bigMicBtn.classList.remove('scale-110', 'ring-8', 'ring-secondary/40', 'animate-pulse');
        if (visualizer) visualizer.classList.add('hidden');
        if (statusLabel) statusLabel.textContent = "Tap the glowing mic to speak with Nivara Saathi";
      };

      recognitionInstance.onend = () => {
        isListening = false;
        bigMicBtn.classList.remove('scale-110', 'ring-8', 'ring-secondary/40', 'animate-pulse');
        if (visualizer) visualizer.classList.add('hidden');
        const text = statusLabel?.textContent?.replace(/^"|"$/g, '').trim();
        if (statusLabel) statusLabel.textContent = "Tap the glowing mic to speak with Nivara Saathi";
        if (text && text.length > 3 && !text.includes('Tap the glowing mic')) {
          submitSaathiQuery(text);
        }
      };

      try {
        recognitionInstance.start();
      } catch (err) {
        console.warn('Recognition start exception:', err);
      }
    });
  }

  // -------------------------------------------------------------
  // Public Initializer
  // -------------------------------------------------------------
  window.initSaathiAssistant = function () {
    const openBtn = document.getElementById('btnOpenSaathi');
    const modal = document.getElementById('saathiModal');
    const closeBtn = document.getElementById('btnCloseSaathi');
    const btnToggleProfile = document.getElementById('btnSaathiToggleProfile');
    const btnSaveConsent = document.getElementById('btnSaathiSaveConsent');
    const btnAcceptConsentBanner = document.getElementById('btnAcceptConsentBanner');
    const btnDeleteData = document.getElementById('btnSaathiDeleteData');
    const btnBackToChat = document.getElementById('btnSaathiBackToChat');
    const sendBtn = document.getElementById('btnSendSaathiText');
    const textInput = document.getElementById('saathiTextInput');

    if (openBtn && modal) {
      openBtn.addEventListener('click', () => {
        modal.classList.remove('hidden');
        refreshSaathiData();
      });
    }

    if (closeBtn && modal) {
      closeBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
        if (typeof stopSpeaking === 'function') stopSpeaking();
      });
    }

    if (btnToggleProfile) {
      btnToggleProfile.addEventListener('click', () => toggleProfileView(true));
    }

    if (btnBackToChat) {
      btnBackToChat.addEventListener('click', () => toggleProfileView(false));
    }

    if (btnSaveConsent) {
      btnSaveConsent.addEventListener('click', () => saveProfileAndConsent(true));
    }

    if (btnAcceptConsentBanner) {
      btnAcceptConsentBanner.addEventListener('click', () => saveProfileAndConsent(true));
    }

    if (btnDeleteData) {
      btnDeleteData.addEventListener('click', deleteUserData);
    }

    if (sendBtn && textInput) {
      sendBtn.addEventListener('click', () => submitSaathiQuery(textInput.value));
      textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          submitSaathiQuery(textInput.value);
        }
      });
    }

    setupVoiceInteractions();
    refreshSaathiData();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.initSaathiAssistant());
  } else {
    window.initSaathiAssistant();
  }
})();
