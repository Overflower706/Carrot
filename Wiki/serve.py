"""Wiki 문서 로컬 서버. 편집 기능(wiki-edit.js)의 저장을 받기 위해 PUT만 얹었다.

    python Wiki/serve.py     →  http://127.0.0.1:8765/index.html

file://로 열면 편집 버튼이 아예 뜨지 않는다 — 브라우저가 파일에 쓸 방법이 없기 때문.
"""
import http.server
import os
import socketserver

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8765


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_PUT(self):
        path = self.translate_path(self.path)  # cwd 밖으로 못 나감(상위 경로 정규화됨)
        if not path.lower().endswith(".html") or not os.path.isfile(path):
            self.send_error(403, "only existing .html")
            return
        data = self.rfile.read(int(self.headers["Content-Length"]))
        with open(path, "wb") as f:
            f.write(data)
        self.send_response(204)
        self.end_headers()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    os.chdir(ROOT)
    print(f"http://127.0.0.1:{PORT}/index.html  (Ctrl+C 종료)")
    # allow_reuse_address는 일부러 끈다 — Windows에선 이미 쓰는 포트를 뺏어버려서
    # 서버가 두 번 뜬 걸 모른 채로 굴러가게 된다. 그냥 "포트 사용 중"으로 죽는 게 낫다.
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.serve_forever()
