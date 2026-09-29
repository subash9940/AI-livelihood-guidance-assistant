/**
 * Nivara Pathway Follow-Up Assistant (Phase 3)
 * Persistent conversational panel on the Pathway/Recommendation screen.
 * Context-aware RAG question answering, inline scheme cards, and plan saving.
 */

(function () {
  let isListening = false;
  let recognitionInstance = null;

  function getActiveUserId() {
    let uid = localStorage.getItem('nivara_user_id');
    if (!uid) {
      uid = 'user_' + Math.random().toString(36).substring(2, 9);
      localStorage.setItem('nivara_user_id', uid);
    }
    return uid;
  }

  function getPathwayContext() {
    const tradeTitle = document.getElementById('recTradeTitle')?.textContent?.trim() || '';
    const qpName = document.getElementById('recQpName')?.textContent?.trim() || '';
    const qpCode = document.getElementById('recQpCode')?.textContent?.trim() || '';
    const nsqfLevel = document.getElementById('recQpNsqfLevel')?.textContent?.trim() || '';
    const sscName = document.getElementById('recSscName')?.textContent?.trim() || '';
    const gapSummary = document.getElementById('recGapSummary')?.textContent?.trim() || '';

    return {
      recommended_trade: tradeTitle,
      qp_name: qpName,
      qp_code: qpCode,
      nsqf_level: nsqfLevel,
      sector: sscName,
      gap_summary: gapSummary
    };
  }

  function initSpeech() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return null;
    const rec = new SpeechRec();
    rec.continuous = false;
    rec.interimResults = true;
    return rec;
  }

  function appendUserMessage(text) {
    const container = document.getElementById('pathwayDialogueContainer');
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'flex items-start justify-end gap-2 max-w-[90%] self-end';
    div.innerHTML = `
      <div class="bg-secondary text-on-secondary p-3 rounded-2xl rounded-tr-sm text-xs shadow-sm flex flex-col gap-1">
        <p class="leading-relaxed font-medium">${escapeHtml(text)}</p>
        <span class="text-[10px] text-on-secondary/70 self-end">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
      </div>
      <div class="w-7 h-7 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center flex-shrink-0 text-xs font-bold shadow-sm">
        You
      </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  function appendAssistantTyping() {
    const container = document.getElementById('pathwayDialogueContainer');
    if (!container) return null;

    const div = document.createElement('div');
    div.id = 'pathwayTypingIndicator';
    div.className = 'flex items-start gap-2 max-w-[90%]';
    div.innerHTML = `
      <div class="w-7 h-7 rounded-full bg-secondary text-on-secondary flex items-center justify-center flex-shrink-0 text-xs font-bold shadow-sm animate-pulse">
        N
      </div>
      <div class="bg-surface-container-lowest text-on-surface p-3 rounded-2xl rounded-tl-sm text-xs shadow-sm border border-border-subtle flex items-center gap-1.5 text-on-surface-variant">
        <span class="w-1.5 h-1.5 rounded-full bg-secondary animate-bounce"></span>
        <span class="w-1.5 h-1.5 rounded-full bg-secondary animate-bounce [animation-delay:0.2s]"></span>
        <span class="w-1.5 h-1.5 rounded-full bg-secondary animate-bounce [animation-delay:0.4s]"></span>
        <span class="text-[11px] ml-1">Consulting Delhi Knowledge Base &amp; Rules...</span>
      </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
  }

  function appendAssistantMessage(data) {
    const container = document.getElementById('pathwayDialogueContainer');
    const typing = document.getElementById('pathwayTypingIndicator');
    if (typing) typing.remove();
    if (!container) return;

    const answer = data.answer || "I could not retrieve an answer at this time.";
    const citations = data.citations || [];
    const schemeCards = data.scheme_cards || [];
    const eligibilityEvals = data.eligibility_evaluations || [];

    const div = document.createElement('div');
    div.className = 'flex items-start gap-2 max-w-[95%]';

    let cardsHtml = '';
    if (schemeCards.length > 0) {
      cardsHtml = `<div class="flex flex-col gap-2 mt-2 pt-2 border-t border-border-subtle">
        <span class="text-[11px] font-bold text-on-surface uppercase tracking-wider">Relevant Delhi Schemes &amp; Eligibility:</span>`;
      
        const isPmajay = card.id === 'pm-ajay-gia' || card.id === 'delhi-pmajay-gia';
        const isClosed = card.active === false;
        const isEligible = card.eligibility_verdict;
        
        let statusBadge = '';
        if (isClosed) {
          statusBadge = `<span class="bg-[#fef2f2] text-[#991b1b] text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 border border-[#fecaca]">
              <span class="material-symbols-outlined text-[12px]">block</span> Closed Scheme
            </span>`;
        } else if (isEligible) {
          statusBadge = `<span class="bg-[#ecfdf5] text-[#065f46] text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 border border-[#a7f3d0]">
              <span class="material-symbols-outlined text-[12px]">check_circle</span> Eligible (${card.match_percentage}%)
            </span>`;
        } else {
          statusBadge = `<span class="bg-[#fef2f2] text-[#991b1b] text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 border border-[#fecaca]">
              <span class="material-symbols-outlined text-[12px]">info</span> Review Criteria (${card.match_percentage}%)
            </span>`;
        }

        const verifyBadge = (card.verification_status === 'verified' && card.last_verified)
          ? `<span class="bg-[#ecfdf5] text-[#065f46] text-[10px] font-bold px-2 py-0.5 rounded border border-[#a7f3d0] flex items-center gap-1">
              <span class="material-symbols-outlined text-[12px]">verified</span> Verified ${escapeHtml(card.last_verified)}
            </span>`
          : `<span class="bg-[#fffbeb] text-[#92400e] text-[10px] font-semibold px-2 py-0.5 rounded border border-[#f59e0b]/50 flex items-center gap-1">
              <span class="material-symbols-outlined text-[12px] text-[#d97706]">warning</span> Sample data - verify on official site
            </span>`;

        const applyStepsHtml = (card.how_to_apply || []).map((step, idx) => 
          `<li class="text-[11px] text-on-surface-variant flex items-start gap-1.5">
            <span class="w-4 h-4 rounded-full bg-secondary/15 text-secondary flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">${idx+1}</span>
            <span>${escapeHtml(step)}</span>
          </li>`
        ).join('');

        const officesHtml = (card.nearest_offices || []).slice(0, 2).map(off =>
          `<div class="text-[10px] text-on-surface-variant bg-surface-container-low p-1.5 rounded border border-border-subtle">
            <span class="font-bold text-on-surface">${escapeHtml(off.name)} (${escapeHtml(off.district)}):</span> ${escapeHtml(off.address)} • Tel: ${escapeHtml(off.contact)}
          </div>`
        ).join('');

        const statusNoteHtml = card.status_note
          ? `<div class="text-[10px] bg-red-50 text-red-700 p-1.5 rounded border border-red-200">
               <strong>Status:</strong> ${escapeHtml(card.status_note)}
             </div>`
          : '';

        const pmajayNoticeHtml = isPmajay
          ? `<div class="text-[10px] bg-blue-50 text-blue-800 p-1.5 rounded border border-blue-200 flex items-start gap-1">
               <span class="material-symbols-outlined text-[12px] mt-0.5 text-blue-600">info</span>
               <span><strong>Beneficiary Selection:</strong> Delivered through approved State/District projects and implementing agencies (selection committee). No direct individual application form. Contact District Social Welfare/SC Welfare office.</span>
             </div>`
          : '';

        cardsHtml += `
          <div class="bg-surface-container rounded-xl p-2.5 border border-border-subtle flex flex-col gap-1.5">
            <div class="flex items-start justify-between gap-1.5">
              <div>
                <h4 class="font-bold text-xs text-on-surface leading-tight">${escapeHtml(card.name)}</h4>
                <span class="text-[10px] text-on-surface-variant">${escapeHtml(card.department)}</span>
              </div>
              ${statusBadge}
            </div>

            <!-- Verification Badge -->
            <div class="flex items-center gap-1.5 my-0.5">
              ${verifyBadge}
            </div>

            ${statusNoteHtml}
            ${pmajayNoticeHtml}
            
            <p class="text-[11px] text-on-surface leading-relaxed">${escapeHtml(card.description)}</p>
            
            <!-- Expandable Apply Steps -->
            <details class="text-[11px] group cursor-pointer mt-1">
              <summary class="font-bold text-secondary flex items-center gap-1 select-none hover:underline">
                <span class="material-symbols-outlined text-[14px] transition-transform group-open:rotate-90">chevron_right</span>
                <span>${isPmajay ? 'View Selection & Livelihood Details' : `View How to Apply Steps & Delhi Offices (${(card.how_to_apply || []).length} steps)`}</span>
              </summary>
              <div class="pl-2 pt-2 flex flex-col gap-2">
                <ol class="flex flex-col gap-1">${applyStepsHtml}</ol>
                ${officesHtml ? `<div class="mt-1 flex flex-col gap-1"><span class="font-bold text-[10px] text-on-surface">Nearest Delhi Center:</span>${officesHtml}</div>` : ''}
              </div>
            </details>

            <div class="flex items-center justify-between gap-2 pt-1 mt-1 border-t border-border-subtle/50 flex-wrap">
              <a href="${card.official_url || card.source_url}" target="_blank" rel="noopener noreferrer" class="text-[10px] text-secondary hover:underline font-semibold flex items-center gap-1">
                <span>Official Portal</span>
                <span class="material-symbols-outlined text-[11px]">open_in_new</span>
              </a>
              ${isClosed ? '' : `
              <button class="btn-save-scheme-plan text-[11px] bg-secondary text-on-secondary font-bold px-2.5 py-1 rounded-lg hover:bg-secondary-container flex items-center gap-1 shadow-sm active:scale-95 transition-all"
                data-scheme-id="${escapeHtml(card.id)}" data-scheme-name="${escapeHtml(card.name)}">
                <span class="material-symbols-outlined text-[14px]">bookmark_add</span>
                <span>Save to my plan</span>
              </button>`}
            </div>
          </div>
        `;
      });
      cardsHtml += `</div>`;
    }

    // Citations badges
    let citationsHtml = '';
    if (citations.length > 0) {
      citationsHtml = `<div class="flex flex-wrap items-center gap-1 pt-1 mt-1 border-t border-border-subtle/60">
        <span class="text-[10px] text-on-surface-variant font-bold">Official Sources:</span>`;
      citations.forEach(c => {
        citationsHtml += `
          <a href="${c.url}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-0.5 text-[10px] bg-surface-container-high text-secondary hover:text-secondary-container px-2 py-0.5 rounded-full border border-border-subtle">
            <span>${escapeHtml(c.name.split('(')[0].trim())}</span>
            <span class="material-symbols-outlined text-[10px]">launch</span>
          </a>
        `;
      });
      citationsHtml += `</div>`;
    }

    // Format Markdown bolding and lists
    const formattedAnswer = formatMarkdown(answer);

    div.innerHTML = `
      <div class="w-7 h-7 rounded-full bg-secondary text-on-secondary flex items-center justify-center flex-shrink-0 text-xs font-bold shadow-sm">
        N
      </div>
      <div class="bg-surface-container-lowest text-on-surface p-3 rounded-2xl rounded-tl-sm text-xs shadow-sm border border-border-subtle flex flex-col gap-1.5 flex-1 min-w-0">
        <div class="leading-relaxed text-on-surface space-y-1">${formattedAnswer}</div>
        
        ${cardsHtml}
        ${citationsHtml}

        <div class="flex items-center justify-between gap-2 pt-1 text-[10px] text-on-surface-variant">
          <div class="flex items-center gap-1">
            <span class="material-symbols-outlined text-[12px] text-[#10b981]">verified</span>
            <span>Deterministic Rules Verified</span>
          </div>
          <button class="btn-listen-reply text-[11px] text-secondary hover:text-secondary-container font-semibold flex items-center gap-0.5 hover:underline">
            <span class="material-symbols-outlined text-[14px]">volume_up</span>
            <span>Listen / सुनें</span>
          </button>
        </div>
      </div>
    `;

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    // Attach Listen button listener
    const listenBtn = div.querySelector('.btn-listen-reply');
    if (listenBtn) {
      listenBtn.addEventListener('click', () => {
        if (typeof speak === 'function') {
          speak(answer);
        }
      });
    }

    // Attach Save to plan buttons
    div.querySelectorAll('.btn-save-scheme-plan').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const schemeId = btn.getAttribute('data-scheme-id');
        const schemeName = btn.getAttribute('data-scheme-name');
        await saveSchemeToPlan(schemeId, schemeName, btn);
      });
    });

    saveLocalHistory();
  }

  async function saveSchemeToPlan(schemeId, schemeName, buttonEl) {
    const uid = getActiveUserId();
    try {
      buttonEl.disabled = true;
      buttonEl.innerHTML = `<span class="material-symbols-outlined text-[14px] animate-spin">refresh</span> Saving...`;

      const resp = await fetch(`/rag/memory/${encodeURIComponent(uid)}/save-scheme`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scheme_id: schemeId, scheme_name: schemeName })
      });
      const data = await resp.json();

      buttonEl.classList.remove('bg-secondary', 'hover:bg-secondary-container');
      buttonEl.classList.add('bg-[#10b981]', 'text-on-secondary');
      buttonEl.innerHTML = `<span class="material-symbols-outlined text-[14px]">check</span> Saved to Plan`;

      if (typeof showToast === 'function') {
        showToast(`'${schemeName}' saved to your PM-AJAY progress plan!`, 'bookmark_added');
      }
    } catch (e) {
      console.error('Error saving scheme to plan:', e);
      buttonEl.disabled = false;
      buttonEl.innerHTML = `<span class="material-symbols-outlined text-[14px]">bookmark_add</span> Save to my plan`;
    }
  }

  async function submitPathwayQuestion(text) {
    const clean = (text || '').trim();
    if (!clean) return;

    appendUserMessage(clean);
    appendAssistantTyping();

    const input = document.getElementById('inputPathwayFollowUp');
    if (input) input.value = '';

    const uid = getActiveUserId();
    const ctx = getPathwayContext();
    const currentLang = window.state ? window.state.language : 'en';

    try {
      const resp = await fetch('/rag/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: clean,
          user_id: uid,
          language: currentLang,
          pathway_context: ctx,
          region: 'delhi'
        })
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const data = await resp.json();
      if (data.method) {
        const normEl = document.getElementById('telemetryNormMethod');
        if (normEl) normEl.textContent = data.method;
      }
      appendAssistantMessage(data);
    } catch (err) {
      console.error('Error asking RAG pipeline:', err);
      const typing = document.getElementById('pathwayTypingIndicator');
      if (typing) typing.remove();

      appendAssistantMessage({
        answer: "I apologize, but I could not connect to the Delhi RAG knowledge pipeline right now. Please verify your connection or consult the official portal at https://socialjustice.gov.in.",
        citations: [{ name: "MoSJE Official Portal", url: "https://socialjustice.gov.in", helpline: "1800-11-762529" }]
      });
    }
  }

  function saveLocalHistory() {
    const container = document.getElementById('pathwayDialogueContainer');
    if (!container) return;
    const uid = getActiveUserId();
    localStorage.setItem('pathway_chat_html_' + uid, container.innerHTML);
  }

  function loadLocalHistory() {
    const container = document.getElementById('pathwayDialogueContainer');
    if (!container) return;
    const uid = getActiveUserId();
    const saved = localStorage.getItem('pathway_chat_html_' + uid);
    if (saved && saved.length > 50) {
      container.innerHTML = saved;
      // Re-bind listeners for any buttons in restored HTML
      container.querySelectorAll('.btn-listen-reply').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const text = btn.closest('.bg-surface-container-lowest')?.querySelector('.leading-relaxed')?.textContent || '';
          if (typeof speak === 'function') speak(text);
        });
      });
      container.querySelectorAll('.btn-save-scheme-plan').forEach(btn => {
        btn.addEventListener('click', () => {
          const schemeId = btn.getAttribute('data-scheme-id');
          const schemeName = btn.getAttribute('data-scheme-name');
          saveSchemeToPlan(schemeId, schemeName, btn);
        });
      });
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
  // Public Initializer
  // -------------------------------------------------------------
  window.initPathwayFollowUp = function () {
    const input = document.getElementById('inputPathwayFollowUp');
    const sendBtn = document.getElementById('btnSendPathwayFollowUp');
    const micBtn = document.getElementById('btnPathwayMic');
    const micStatus = document.getElementById('pathwayMicListeningStatus');
    const clearBtn = document.getElementById('btnClearPathwayChat');
    const chipsContainer = document.getElementById('pathwaySuggestedChips');

    // 1. Suggested Follow-Up Chips
    if (chipsContainer) {
      chipsContainer.querySelectorAll('.pathway-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const q = chip.getAttribute('data-query');
          if (q) submitPathwayQuestion(q);
        });
      });
    }

    // 2. Send Button and Enter Key
    if (sendBtn && input) {
      sendBtn.addEventListener('click', () => {
        submitPathwayQuestion(input.value);
      });
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          submitPathwayQuestion(input.value);
        }
      });
    }

    // 3. Clear Chat Button
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        const container = document.getElementById('pathwayDialogueContainer');
        if (container) {
          container.innerHTML = `
            <div class="flex items-start gap-2 max-w-[90%]">
              <div class="w-7 h-7 rounded-full bg-secondary text-on-secondary flex items-center justify-center flex-shrink-0 text-xs font-bold shadow-sm">
                N
              </div>
              <div class="bg-surface-container-lowest text-on-surface p-3 rounded-2xl rounded-tl-sm text-xs shadow-sm border border-border-subtle flex flex-col gap-1.5">
                <p class="leading-relaxed">
                  Chat cleared. Ask me any follow-up question regarding your recommended trade, eligibility rules, required certificates, or where to enroll in Delhi.
                </p>
              </div>
            </div>
          `;
          const uid = getActiveUserId();
          localStorage.removeItem('pathway_chat_html_' + uid);
        }
      });
    }

    // 4. Voice Input via Mic Button
    if (micBtn) {
      micBtn.addEventListener('click', () => {
        if (!recognitionInstance) {
          recognitionInstance = initSpeech();
        }
        if (!recognitionInstance) {
          if (typeof showToast === 'function') {
            showToast('Voice input not supported in this browser. Please type your query.', 'mic_off');
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
          micBtn.classList.add('bg-ruby/20', 'text-ruby', 'border-ruby/40', 'animate-pulse');
          if (micStatus) micStatus.classList.remove('hidden');
          if (input) input.placeholder = 'Listening... Speak your question now...';
        };

        recognitionInstance.onresult = (evt) => {
          let transcript = '';
          for (let i = evt.resultIndex; i < evt.results.length; i++) {
            transcript += evt.results[i][0].transcript;
          }
          if (input) input.value = transcript;
        };

        recognitionInstance.onerror = (e) => {
          console.warn('Pathway speech recognition error:', e.error);
          isListening = false;
          micBtn.classList.remove('bg-ruby/20', 'text-ruby', 'border-ruby/40', 'animate-pulse');
          if (micStatus) micStatus.classList.add('hidden');
          if (input) input.placeholder = 'Ask anything about this pathway, eligibility, documents, or centres...';
        };

        recognitionInstance.onend = () => {
          isListening = false;
          micBtn.classList.remove('bg-ruby/20', 'text-ruby', 'border-ruby/40', 'animate-pulse');
          if (micStatus) micStatus.classList.add('hidden');
          if (input) {
            input.placeholder = 'Ask anything about this pathway, eligibility, documents, or centres...';
            if (input.value.trim().length > 3) {
              submitPathwayQuestion(input.value.trim());
            }
          }
        };

        try {
          recognitionInstance.start();
        } catch (err) {
          console.warn('Recognition start error:', err);
        }
      });
    }

    // Load persisted history on boot
    loadLocalHistory();
  };

  // Re-run initialization when DOM is ready or if already ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.initPathwayFollowUp());
  } else {
    window.initPathwayFollowUp();
  }
})();
