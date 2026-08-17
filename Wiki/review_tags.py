"""섹션 검토 태그를 찍고 세어 본다.

    python Wiki/review_tags.py          → 태그 없는 h2/h3에 「사람이 문장 검토 필요함」를 찍는다
    python Wiki/review_tags.py --check  → 아무것도 안 고치고 현황만 센다
    python Wiki/review_tags.py --reset <문서>
                                        → 그 문서의 t-ok을 전부 t-review로 되돌린다

축이 둘이다. 헷갈리지 말 것 —
  .status  기획이 정해졌는가        확정 / 미정 / 해당 없음   (문서를 쓰는 사람이 붙인다)
  .tag     사람이 읽고 승인했는가   사람이 문장 검토 필요함 / 사람이 문장 검토함

**t-ok으로 바꾸는 것은 사용자만 한다.** 클로드가 스스로 달지 않는다.
클로드가 어떤 섹션의 문단을 새로 쓰거나 고쳤으면 그 섹션은 다시 t-review여야 한다 —
고친 문서에 --reset을 걸고 사용자가 다시 읽는 것이 정상 경로다.

검토 축으로 세는 것은 t-review와 t-ok **둘뿐이다.** t-now / t-next / t-later / t-block은
진행 상태를 알리는 자유 문구 배지라서 검토와 무관하다 — 그것만 달린 제목도 태그 없는 것으로 보고
t-review를 찍는다. (2026-08-18까지는 `class="tag t-`만 보고 넘겨서 그런 제목이 영구히 빠졌다.)

DevLog/와 Archive/는 제외한다. 일지는 「그때 무엇을 했는가」의 기록이고 아카이브는 폐기된 것이라,
둘 다 지금 와서 승인할 대상이 아니다. index.html도 문서가 아니라 목록이라 뺀다.
(그런 폴더가 없는 위키에서는 그냥 걸리지 않고 지나간다.)

이 스크립트는 세 저장소의 위키가 같은 것을 쓴다 — `Carrot/Wiki/`와 `CarrotProject/Wiki/`의
사본은 동일해야 한다. 규약은 `Carrot/CLAUDE.md`의 「위키 규약 — 세 저장소 공통」.
"""
import io
import os
import posixpath
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = ("DevLog", "Archive")
SKIP_FILES = ("index.html",)

# 글자는 wiki.css의 :empty::after가 넣는다 — class가 곧 문구라 둘이 어긋날 일이 없다
REVIEW = '<span class="tag t-review"></span>'
OK = '<span class="tag t-ok"></span>'

HEADING = re.compile(r"<(h2|h3)([^>]*)>(.*?)</\1>", re.S)
FILLED = re.compile(r'(<span class="tag (?:t-review|t-ok)">)[^<]*(</span>)')
# 검토 축은 이 둘뿐이다 — t-now 같은 진행 배지는 「태그가 있다」로 세지 않는다
TAGGED = re.compile(r'class="tag (?:t-review|t-ok)"')


def targets():
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if f.endswith(".html") and f not in SKIP_FILES:
                yield posixpath.relpath(
                    os.path.join(root, f).replace("\\", "/"), ROOT.replace("\\", "/")
                )


def stamp(text):
    """태그가 없는 h2/h3에만 t-review를 더한다. 이미 있는 것은 손대지 않는다(멱등)."""
    added = [0]

    def sub(m):
        tag, attrs, inner = m.groups()
        if TAGGED.search(inner):
            return m.group(0)
        added[0] += 1
        return "<%s%s>%s %s</%s>" % (tag, attrs, inner.rstrip(), REVIEW, tag)

    return HEADING.sub(sub, text), added[0]


def count(text):
    return text.count('class="tag t-review"'), text.count('class="tag t-ok"')


def main():
    args = sys.argv[1:]
    check = "--check" in args
    reset = args[args.index("--reset") + 1] if "--reset" in args else None

    total_r = total_o = total_add = 0
    for rel in targets():
        path = os.path.join(ROOT, rel)
        s = io.open(path, encoding="utf-8").read()
        out, added = (s, 0) if check else stamp(FILLED.sub(r"\1\2", s))

        if reset and posixpath.normpath(rel) == posixpath.normpath(reset):
            out = out.replace(OK, REVIEW)

        if out != s:
            io.open(path, "w", encoding="utf-8", newline="\n").write(out)

        r, o = count(out)
        total_r += r
        total_o += o
        total_add += added
        flag = "  +%d" % added if added else ""
        print("%-52s 검토 필요 %2d · 검토함 %2d%s" % (rel, r, o, flag))

    print("-" * 78)
    done = total_o / (total_r + total_o) * 100 if (total_r + total_o) else 0
    print("합계  검토 필요 %d · 검토함 %d  (%.0f%% 승인)%s"
          % (total_r, total_o, done, "  새로 찍은 태그 %d" % total_add if total_add else ""))


if __name__ == "__main__":
    main()
