/*
 * Course Allocator — document chat panel (no dependencies, works in any front-end).
 *
 *   RagChat.mount('#chat', {
 *     apiBase: '/rag',                                    // where the FastAPI router lives
 *     getHeaders: () => ({ Authorization: 'Bearer ' + token })   // optional
 *   });
 *
 * React:  useEffect(() => { const c = RagChat.mount(ref.current, opts); return () => c.destroy(); }, []);
 */
(function (global) {
  'use strict';

  var KIND = { course_outline: 'Course outline', faculty_feedback: 'Faculty feedback' };

  function h(tag, props) {
    var node = document.createElement(tag);
    props = props || {};
    Object.keys(props).forEach(function (k) {
      var v = props[k];
      if (v == null || v === false) return;
      if (k === 'class') node.className = v;
      else if (k === 'text') node.textContent = v;
      else if (k.slice(0, 2) === 'on') node.addEventListener(k.slice(2), v);
      else if (k === 'dataset') Object.keys(v).forEach(function (d) { node.dataset[d] = v[d]; });
      else node.setAttribute(k, v === true ? '' : v);
    });
    for (var i = 2; i < arguments.length; i++) {
      var c = arguments[i];
      if (c == null || c === false) continue;
      node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    }
    return node;
  }

  function Panel(target, opts) {
    this.opts = Object.assign({ apiBase: '/rag', getHeaders: function () { return {}; } }, opts || {});
    this.base = this.opts.apiBase.replace(/\/$/, '');
    this.root = typeof target === 'string' ? document.querySelector(target) : target;
    if (!this.root) throw new Error('RagChat.mount: target element not found');
    this.docs = [];
    this.meta = { instructors: [], courses: [] };
    this.history = [];
    this.scope = { doc_type: '', instructor_id: '', course_code: '' };
    this.busy = false;
    this.files = [];
    this.build();
    this.refresh();
  }

  /* ------------------------------------------------------------ API */
  Panel.prototype.api = function (path, o) {
    o = o || {};
    var headers = Object.assign({}, this.opts.getHeaders());
    var body;
    if (o.json) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(o.json); }
    if (o.form) body = o.form;
    return fetch(this.base + path, { method: o.method || 'GET', headers: headers, body: body }).then(function (res) {
      if (res.ok) return res.status === 204 ? null : res.json();
      return res.json().catch(function () { return {}; }).then(function (j) {
        var d = j.detail, msg;
        if (typeof d === 'string') msg = d;
        else if (Array.isArray(d)) msg = d.map(function (x) { return x.msg; }).join('; ');
        else msg = res.status === 401 || res.status === 403 ? 'You are not signed in or not allowed to do this.' : 'Request failed (' + res.status + ').';
        throw new Error(msg);
      });
    });
  };

  Panel.prototype.toast = function (text, isError) {
    var t = h('div', { class: 'rag-toast' + (isError ? ' is-error' : ''), role: 'status', text: text });
    this.root.appendChild(t);
    setTimeout(function () { t.remove(); }, isError ? 7000 : 3500);
  };

  Panel.prototype.refresh = function () {
    var self = this;
    return Promise.all([this.api('/documents'), this.api('/meta')]).then(function (r) {
      self.docs = r[0]; self.meta = r[1];
      self.renderDocs(); self.renderScope(); self.renderIntro();
    }).catch(function (e) { self.toast('Could not load documents: ' + e.message, true); });
  };

  /* ------------------------------------------------------------ layout */
  Panel.prototype.build = function () {
    var self = this;
    this.root.innerHTML = '';
    this.el = h('div', { class: 'rag-root', dataset: { view: 'chat' } });
    this.root.appendChild(this.el);

    var tabLib = h('button', { role: 'tab', 'aria-selected': 'false', text: 'Documents', onclick: function () { setView('library'); } });
    var tabChat = h('button', { role: 'tab', 'aria-selected': 'true', text: 'Chat', onclick: function () { setView('chat'); } });
    function setView(v) {
      self.el.dataset.view = v;
      tabLib.setAttribute('aria-selected', v === 'library');
      tabChat.setAttribute('aria-selected', v === 'chat');
    }
    this.setView = setView;
    this.el.appendChild(h('div', { class: 'rag-tabs', role: 'tablist' }, tabChat, tabLib));
    this.el.appendChild(this.buildLibrary());
    this.el.appendChild(this.buildChat());
  };

  /* ------------------------------------------------------------ library */
  Panel.prototype.buildLibrary = function () {
    var self = this;
    var lib = h('section', { class: 'rag-library', 'aria-label': 'Documents' });
    lib.appendChild(h('div', { class: 'rag-pane-head' },
      h('h2', { text: 'Documents' }),
      h('p', { text: 'Upload outlines and feedback, then ask questions about them.' })));

    // upload form
    var kindOutline = h('input', { type: 'radio', name: 'rag-kind', value: 'course_outline', checked: true });
    var kindFeedback = h('input', { type: 'radio', name: 'rag-kind', value: 'faculty_feedback' });
    var fileInput = h('input', { type: 'file', multiple: true, accept: '.pdf,.docx,.txt,.md' });
    var drop = h('label', { class: 'rag-drop' },
      h('strong', { text: 'Choose files or drop them here' }),
      h('small', { text: 'PDF, Word, or text' }), fileInput);
    var picked = h('ul', { class: 'rag-picked', 'aria-live': 'polite' });

    var title = h('input', { type: 'text', placeholder: 'Defaults to the file name' });
    var course = h('input', { type: 'text', placeholder: 'e.g. CS-301' });
    var facultyList = h('datalist', { id: 'rag-faculty-list' });
    var faculty = h('input', { type: 'text', list: 'rag-faculty-list', placeholder: 'Full name' });
    var semester = h('input', { type: 'text', placeholder: 'e.g. Fall 2025' });
    var facultyLabel = h('label', { text: 'Faculty member (required)' });
    var submit = h('button', { class: 'rag-btn', type: 'submit', text: 'Upload and index', disabled: true });

    function field(label, input, wide) {
      var lab = typeof label === 'string' ? h('label', { text: label }) : label;
      return h('div', { class: 'rag-field' + (wide ? ' rag-wide' : '') }, lab, input);
    }
    var fTitle = field('Title', title, true);
    var form = h('form', { class: 'rag-upload' },
      h('div', { class: 'rag-kind', role: 'radiogroup', 'aria-label': 'Document type' },
        h('label', null, kindOutline, h('span', { text: 'Course outline' })),
        h('label', null, kindFeedback, h('span', { text: 'Faculty feedback' }))),
      drop, picked,
      h('div', { class: 'rag-fields' }, fTitle, field('Course code', course), field('Semester', semester), field(facultyLabel, faculty, true)),
      facultyList, submit);
    lib.appendChild(form);

    function kind() { return kindFeedback.checked ? 'faculty_feedback' : 'course_outline'; }
    function sync() {
      var fb = kind() === 'faculty_feedback';
      facultyLabel.textContent = fb ? 'Faculty member (required)' : 'Faculty member (optional)';
      fTitle.style.display = self.files.length > 1 ? 'none' : '';
      submit.disabled = !self.files.length || self.uploading;
      picked.innerHTML = '';
      self.files.forEach(function (f) {
        f.li = h('li', null, h('span', { class: 'rag-fname', text: f.file.name }), h('span', { text: f.status || '' }));
        picked.appendChild(f.li);
      });
    }
    this.syncUpload = sync;
    kindOutline.addEventListener('change', sync);
    kindFeedback.addEventListener('change', sync);

    function setFiles(list) {
      self.files = Array.prototype.slice.call(list).map(function (file) { return { file: file }; });
      sync();
    }
    fileInput.addEventListener('change', function () { setFiles(fileInput.files); });
    ['dragenter', 'dragover'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add('is-over'); }); });
    ['dragleave', 'drop'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove('is-over'); }); });
    drop.addEventListener('drop', function (e) { setFiles(e.dataTransfer.files); });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (kind() === 'faculty_feedback' && !faculty.value.trim()) {
        self.toast('Enter the faculty member this feedback is about.', true);
        faculty.focus();
        return;
      }
      self.uploading = true; submit.disabled = true; submit.textContent = 'Reading and indexing…';
      var known = self.meta.instructors.filter(function (i) { return i.name.toLowerCase() === faculty.value.trim().toLowerCase(); })[0];
      var queue = self.files.slice(), ok = 0;

      (function next() {
        var item = queue.shift();
        if (!item) {
          self.uploading = false; submit.textContent = 'Upload and index';
          if (ok) {
            self.toast(ok + (ok === 1 ? ' document' : ' documents') + ' ready to chat with.');
            self.files = self.files.filter(function (f) { return f.status !== 'Done'; });
            if (!self.files.length) { fileInput.value = ''; title.value = ''; }
            self.refresh();
          }
          sync();
          return;
        }
        item.li.lastChild.textContent = 'Indexing…';
        var fd = new FormData();
        fd.append('file', item.file);
        fd.append('doc_type', kind());
        var multi = self.files.length > 1;
        [['title', multi ? '' : title.value], ['course_code', course.value], ['semester', semester.value],
         ['instructor_name', faculty.value], ['instructor_id', known && known.id != null ? String(known.id) : '']
        ].forEach(function (p) { if (p[1] && p[1].trim()) fd.append(p[0], p[1].trim()); });

        self.api('/documents', { method: 'POST', form: fd }).then(function () {
          ok++; item.status = 'Done'; item.li.lastChild.textContent = 'Done'; item.li.lastChild.className = 'is-ok';
        }).catch(function (err) {
          item.status = 'Failed'; item.li.lastChild.textContent = 'Failed'; item.li.lastChild.className = 'is-err';
          item.li.title = err.message;
          self.toast(item.file.name + ': ' + err.message, true);
        }).then(next);
      })();
    });

    this.facultyList = facultyList;
    this.docList = h('div', { class: 'rag-docs' });
    lib.appendChild(this.docList);
    return lib;
  };

  Panel.prototype.renderDocs = function () {
    var self = this;
    this.docList.innerHTML = '';
    this.facultyList.innerHTML = '';
    this.meta.instructors.forEach(function (i) { self.facultyList.appendChild(h('option', { value: i.name })); });

    if (!this.docs.length) {
      this.docList.appendChild(h('p', { class: 'rag-empty', text: 'No documents yet. Upload a course outline or a faculty feedback file to get started.' }));
      return;
    }
    this.docList.appendChild(h('h3', { text: this.docs.length + (this.docs.length === 1 ? ' document' : ' documents') }));
    this.docs.forEach(function (d) {
      var meta = [d.course_code, d.instructor_name, d.semester, d.num_pages ? d.num_pages + (d.num_pages === 1 ? ' page' : ' pages') : null, d.num_chunks + ' passages']
        .filter(Boolean).join(', ');
      var del = h('button', { class: 'rag-doc-del', type: 'button', text: 'Delete', 'aria-label': 'Delete ' + d.title });
      var armed = false, timer;
      del.addEventListener('click', function () {
        if (!armed) {
          armed = true; del.textContent = 'Confirm delete'; del.classList.add('is-confirm');
          timer = setTimeout(function () { armed = false; del.textContent = 'Delete'; del.classList.remove('is-confirm'); }, 3500);
          return;
        }
        clearTimeout(timer);
        self.api('/documents/' + d.id, { method: 'DELETE' }).then(function () {
          self.toast('Deleted “' + d.title + '”.'); self.refresh();
        }).catch(function (e) { self.toast(e.message, true); });
      });
      self.docList.appendChild(h('div', { class: 'rag-doc' },
        h('div', null,
          h('span', { class: 'rag-tag rag-tag--' + d.doc_type, text: KIND[d.doc_type] || d.doc_type }),
          h('button', { class: 'rag-doc-title', type: 'button', text: d.title, onclick: function () { self.openFile(d.id); } })),
        del,
        h('div', { class: 'rag-doc-meta', text: meta })));
    });
  };

  Panel.prototype.openFile = function (docId, page) {
    var self = this;
    var doc = this.docs.filter(function (d) { return d.id === docId; })[0];
    var name = doc ? doc.filename : 'document';
    var isPdf = /\.pdf$/i.test(name);
    var win = isPdf ? window.open('', '_blank') : null;   // opened synchronously so pop-up blockers allow it
    fetch(this.base + '/documents/' + docId + '/file', { headers: this.opts.getHeaders() }).then(function (res) {
      if (!res.ok) throw new Error(res.status === 410 ? 'The original file is no longer on the server.' : 'Could not open the file.');
      return res.blob();
    }).then(function (blob) {
      var url = URL.createObjectURL(blob);
      if (isPdf && win) { win.location = url + (page ? '#page=' + page : ''); }
      else { var a = h('a', { href: url, download: name }); document.body.appendChild(a); a.click(); a.remove(); }
      setTimeout(function () { URL.revokeObjectURL(url); }, 60000);
    }).catch(function (e) { if (win) win.close(); self.toast(e.message, true); });
  };

  /* ------------------------------------------------------------ chat */
  Panel.prototype.buildChat = function () {
    var self = this;
    var chat = h('section', { class: 'rag-chat', 'aria-label': 'Chat' });

    var segs = [['', 'All'], ['course_outline', 'Outlines'], ['faculty_feedback', 'Feedback']].map(function (s) {
      return h('button', { type: 'button', text: s[1], 'aria-pressed': s[0] === '' ? 'true' : 'false',
        onclick: function () { self.scope.doc_type = s[0]; segs.forEach(function (b, i) { b.setAttribute('aria-pressed', ['', 'course_outline', 'faculty_feedback'][i] === s[0]); }); } });
    });
    this.facultySel = h('select', { 'aria-label': 'Faculty member', onchange: function (e) { self.scope.instructor_id = e.target.value; } });
    this.courseSel = h('select', { 'aria-label': 'Course', onchange: function (e) { self.scope.course_code = e.target.value; } });
    var clear = h('button', { class: 'rag-link', type: 'button', text: 'New conversation', onclick: function () { self.history = []; self.renderIntro(); } });

    chat.appendChild(h('div', { class: 'rag-scope' },
      h('div', { class: 'rag-seg', role: 'group', 'aria-label': 'Document type' }, segs), this.facultySel, this.courseSel,
      h('span', { class: 'rag-spacer' }), clear));

    this.log = h('div', { class: 'rag-log', 'aria-live': 'polite' });
    chat.appendChild(this.log);

    this.input = h('textarea', { rows: '1', placeholder: 'Ask about a course outline or faculty feedback…', 'aria-label': 'Your question',
      onkeydown: function (e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); self.send(); } },
      oninput: function () { self.input.style.height = 'auto'; self.input.style.height = Math.min(self.input.scrollHeight, 140) + 'px'; } });
    this.sendBtn = h('button', { class: 'rag-btn', type: 'button', text: 'Send', onclick: function () { self.send(); } });
    chat.appendChild(h('div', { class: 'rag-composer' }, this.input, this.sendBtn));
    return chat;
  };

  Panel.prototype.renderScope = function () {
    var f = this.facultySel, c = this.courseSel;
    var fv = f.value, cv = c.value;
    f.innerHTML = ''; c.innerHTML = '';
    f.appendChild(h('option', { value: '', text: 'All faculty' }));
    this.meta.instructors.filter(function (i) { return i.id != null; })
      .forEach(function (i) { f.appendChild(h('option', { value: String(i.id), text: i.name })); });
    c.appendChild(h('option', { value: '', text: 'All courses' }));
    this.meta.courses.forEach(function (code) { c.appendChild(h('option', { value: code, text: code })); });
    f.value = fv; c.value = cv;
    // Faculty without an id can't be used as a dropdown filter; naming them in the question still works.
    f.style.display = f.options.length > 1 ? '' : 'none';
    c.style.display = c.options.length > 1 ? '' : 'none';
  };

  Panel.prototype.renderIntro = function () {
    if (this.history.length) return;
    var self = this;
    this.log.innerHTML = '';
    var inst = this.meta.instructors[0], course = this.meta.courses[0];
    var examples = [];
    if (course) examples.push('What topics and grading components does ' + course + ' cover?');
    if (inst) examples.push('Summarize the student feedback about ' + inst.name + '.');
    if (course && inst) examples.push('Is ' + inst.name + ' a good fit to teach ' + course + '?');
    var intro = h('div', { class: 'rag-intro' },
      h('h2', { text: 'Ask your documents' }),
      h('p', { text: this.docs.length
        ? 'Answers come only from the files you uploaded, with a numbered reference for each claim.'
        : 'Upload a course outline or faculty feedback file on the left, then ask a question here.' }));
    examples.forEach(function (q) {
      intro.appendChild(h('button', { class: 'rag-ex', type: 'button', text: q, onclick: function () { self.input.value = q; self.send(); } }));
    });
    this.log.appendChild(intro);
  };

  Panel.prototype.send = function () {
    var self = this, text = this.input.value.trim();
    if (!text || this.busy) return;
    if (!this.history.length) this.log.innerHTML = '';
    this.input.value = ''; this.input.style.height = 'auto';
    this.busy = true; this.sendBtn.disabled = true;

    this.log.appendChild(h('div', { class: 'rag-msg rag-msg--user' }, h('div', { class: 'rag-bubble', text: text })));
    var typing = h('div', { class: 'rag-msg rag-msg--bot' },
      h('div', { class: 'rag-bubble' }, h('span', { class: 'rag-typing', role: 'status', 'aria-label': 'Searching the documents' }, h('i'), h('i'), h('i'))));
    this.log.appendChild(typing);
    this.scrollDown();

    var s = this.scope;
    var payload = { message: text, history: this.history.slice(-8) };
    if (s.doc_type) payload.doc_type = s.doc_type;
    if (s.instructor_id) payload.instructor_id = Number(s.instructor_id);
    if (s.course_code) payload.course_code = s.course_code;

    this.api('/chat', { method: 'POST', json: payload }).then(function (r) {
      typing.remove();
      self.history.push({ role: 'user', content: text }, { role: 'assistant', content: r.answer });
      self.log.appendChild(self.renderAnswer(r));
    }).catch(function (e) {
      typing.remove();
      self.history.push({ role: 'user', content: text });
      self.log.appendChild(h('div', { class: 'rag-msg rag-msg--bot' },
        h('div', { class: 'rag-note', role: 'alert', text: 'Could not get an answer: ' + e.message })));
    }).then(function () {
      self.busy = false; self.sendBtn.disabled = false; self.scrollDown(); self.input.focus();
    });
  };

  Panel.prototype.scrollDown = function () { this.log.scrollTop = this.log.scrollHeight; };

  /* ------------------------------------------------------------ answer rendering */
  // Safe mini-markdown: paragraphs, bullet/numbered lists, **bold**, and [n] citation chips. Built with DOM nodes, never innerHTML.
  Panel.prototype.renderAnswer = function (r) {
    var self = this;
    var byN = {};
    r.sources.forEach(function (s) { byN[s.n] = s; });
    var msg = h('div', { class: 'rag-msg rag-msg--bot' });
    var bubble = h('div', { class: 'rag-bubble' });
    msg.appendChild(bubble);

    function inline(parent, text) {
      text.split(/(\*\*[^*]+\*\*|\[\d+\])/g).forEach(function (part) {
        if (!part) return;
        var cite = /^\[(\d+)\]$/.exec(part), bold = /^\*\*([^*]+)\*\*$/.exec(part);
        if (cite && byN[+cite[1]]) {
          var n = +cite[1];
          parent.appendChild(h('button', { type: 'button', class: 'rag-chip rag-chip--' + byN[n].doc_type, text: String(n),
            title: byN[n].title + (byN[n].page ? ', page ' + byN[n].page : ''), 'aria-label': 'Source ' + n + ': ' + byN[n].title,
            onclick: function () { self.focusSource(msg, n); } }));
        } else if (bold) parent.appendChild(h('strong', { text: bold[1] }));
        else parent.appendChild(document.createTextNode(part));
      });
    }

    var list = null;
    r.answer.split('\n').forEach(function (raw) {
      var line = raw.trim();
      if (!line) { list = null; return; }
      var li = /^([-*•]|\d+[.)])\s+(.*)$/.exec(line);
      if (li) {
        var ordered = /\d/.test(li[1]);
        if (!list || list.ordered !== ordered) {
          list = { ordered: ordered, node: h(ordered ? 'ol' : 'ul') };
          bubble.appendChild(list.node);
        }
        var item = h('li'); inline(item, li[2]); list.node.appendChild(item);
      } else {
        list = null;
        var p = h('p'); inline(p, line.replace(/^#+\s*/, '')); bubble.appendChild(p);
      }
    });

    var sc = r.scope && r.scope.auto_detected;
    if (sc) {
      var names = (sc.instructors || []).concat(sc.courses || []);
      msg.appendChild(h('div', { class: 'rag-scopenote', text: 'Searched only documents for ' + names.join(', ') + ', based on your question.' }));
    }
    if (r.warning) msg.appendChild(h('div', { class: 'rag-note', role: 'alert', text: r.warning }));

    if (r.sources.length) {
      var cited = r.sources.filter(function (s) { return s.cited; });
      var rest = r.sources.filter(function (s) { return !s.cited; });
      if (cited.length) msg.appendChild(h('div', { class: 'rag-sources', 'aria-label': 'Sources cited' }, cited.map(function (s) { return self.sourceCard(s); })));
      if (rest.length) {
        var det = h('details', { class: 'rag-more' },
          h('summary', { text: cited.length ? rest.length + ' more ' + (rest.length === 1 ? 'passage' : 'passages') + ' considered' : 'Passages found (' + rest.length + ')' }),
          h('div', { class: 'rag-sources' }, rest.map(function (s) { return self.sourceCard(s); })));
        if (!cited.length) det.open = true;
        msg.appendChild(det);
      }
    }
    return msg;
  };

  Panel.prototype.sourceCard = function (s) {
    var self = this;
    var meta = [KIND[s.doc_type], s.instructor_name, s.course_code, s.semester, s.page ? 'page ' + s.page : null, 'match ' + Math.round(s.score * 100) + '%']
      .filter(Boolean).join(', ');
    var text = h('p', { class: 'rag-src-text', text: s.snippet });
    var more = h('button', { class: 'rag-src-more', type: 'button', text: 'Show more', onclick: function () {
      var open = text.classList.toggle('is-open'); more.textContent = open ? 'Show less' : 'Show more'; } });
    return h('div', { class: 'rag-src rag-src--' + s.doc_type, dataset: { n: String(s.n) } },
      h('span', { class: 'rag-chip rag-chip--' + s.doc_type + ' rag-src-n', text: String(s.n) }),
      h('div', { class: 'rag-src-head' },
        h('button', { class: 'rag-src-title', type: 'button', text: s.title, onclick: function () { self.openFile(s.document_id, s.page); } }),
        h('span', { class: 'rag-src-meta', text: meta })),
      text, more);
  };

  Panel.prototype.focusSource = function (msg, n) {
    var card = msg.querySelector('.rag-src[data-n="' + n + '"]');
    if (!card) return;
    var det = card.closest('details'); if (det) det.open = true;
    card.scrollIntoView({ block: 'nearest', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    card.classList.add('rag-flash');
    setTimeout(function () { card.classList.remove('rag-flash'); }, 1400);
  };

  Panel.prototype.destroy = function () { this.root.innerHTML = ''; };

  global.RagChat = { mount: function (target, opts) { return new Panel(target, opts); } };
})(window);
