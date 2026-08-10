// 위키식 인라인 편집기. 전체 문서 편집 / 섹션 편집 두 가지.
// 편집 대상은 렌더된 DOM이 아니라 파일의 원본 HTML 소스다 — 들여쓰기와 주석이 그대로 보존된다.
// 저장은 serve.py의 PUT으로 파일에 직접 쓴다. file://로 열면 저장할 방법이 없으므로 편집 UI를 띄우지 않는다.
(function () {
  if (location.protocol === 'file:') return;

  var url = location.pathname;
  var src = '', bodyStart = 0, bodyEnd = 0;

  function bodySrc() { return src.slice(bodyStart, bodyEnd); }

  // 소스에서 h2/h3 위치를 찾아 [시작, 끝) 구간으로 자른다.
  // 한 섹션은 자기 제목부터 "같거나 더 높은 레벨의 다음 제목" 직전까지.
  function sections() {
    var body = bodySrc(), re = /<h([23])\b[^>]*>/gi, out = [], m;
    while ((m = re.exec(body))) out.push({ level: +m[1], start: m.index });
    out.forEach(function (s, i) {
      var next = out.slice(i + 1).find(function (t) { return t.level <= s.level; });
      s.end = next ? next.start : body.length;
    });
    return out;
  }

  var dlg = document.createElement('dialog');
  dlg.className = 'wiki-editor';
  dlg.innerHTML =
    '<form method="dialog">' +
    '<h3></h3><textarea spellcheck="false"></textarea>' +
    '<menu><button value="cancel">취소</button>' +
    '<button value="save" class="primary">저장</button></menu></form>';
  var dlgTitle = dlg.querySelector('h3'), dlgText = dlg.querySelector('textarea');

  // apply(편집된 텍스트) → 새 body 소스 전체
  function edit(label, text, apply) {
    dlgTitle.textContent = label;
    dlgText.value = text;
    dlg.returnValue = '';
    dlg.showModal();
    dlgText.focus();
    dlg.addEventListener('close', function once() {
      dlg.removeEventListener('close', once);
      if (dlg.returnValue === 'save') save(apply(dlgText.value));
    });
  }

  function editLink(text, onclick) {
    var btn = document.createElement('button');
    btn.className = 'wiki-editsec';
    btn.textContent = text;
    btn.onclick = onclick;
    return btn;
  }

  function save(newBody) {
    fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
      body: src.slice(0, bodyStart) + newBody + src.slice(bodyEnd)
    }).then(function (res) {
      if (res.ok) location.reload();
      else alert('저장 실패 (' + res.status + ')');
    }, function (e) { alert('저장 실패 — serve.py가 떠 있는지 확인. ' + e); });
  }

  fetch(url, { cache: 'no-store' }).then(function (r) { return r.text(); }).then(function (text) {
    src = text;
    bodyStart = src.indexOf('>', src.indexOf('<body')) + 1;
    bodyEnd = src.lastIndexOf('</body>');
    if (bodyStart <= 0 || bodyEnd < bodyStart) return;

    document.body.appendChild(dlg);

    // 전체 편집은 h1 옆에 — 섹션 편집과 같은 모양으로 둔다(문서 제목의 [편집] = 문서 전체).
    var h1 = document.querySelector('h1');
    if (h1) h1.appendChild(editLink('[전체 편집]', function () {
      edit('전체 문서 편집 — ' + url.split('/').pop(), bodySrc(), function (v) { return v; });
    }));

    var secs = sections();
    var heads = [].filter.call(document.querySelectorAll('h2, h3'), function (h) {
      return !h.closest('dialog');
    });
    // 소스의 제목과 DOM의 제목은 1:1이어야 인덱스로 짝지을 수 있다.
    // (예: <pre> 안에 이스케이프 안 된 <h2>가 들어가면 어긋난다 — 그럴 땐 전체 편집만 남긴다.)
    if (secs.length !== heads.length) {
      console.warn('[wiki-edit] 제목 수 불일치(소스 ' + secs.length + ' / DOM ' + heads.length + ') — 섹션 편집 비활성');
      return;
    }

    heads.forEach(function (h, i) {
      var label = h.textContent;
      h.appendChild(editLink('[편집]', function () {
        var s = secs[i], body = bodySrc();
        edit('섹션 편집 — ' + label, body.slice(s.start, s.end), function (v) {
          return body.slice(0, s.start) + v + body.slice(s.end);
        });
      }));
    });
  });
})();
