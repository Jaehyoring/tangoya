// kuromoji-worker.js — Web Worker: kuromoji 초기화 및 토크나이즈 처리
// 메인 스레드와 postMessage로 통신

importScripts('kuromoji.js');

let tokenizer = null;

// 초기화
kuromoji.builder({ dicPath: 'dict' }).build((err, _tokenizer) => {
  if (err) {
    postMessage({ type: 'error', message: err.message || String(err) });
    return;
  }
  tokenizer = _tokenizer;
  postMessage({ type: 'ready' });
});

// 메인 스레드로부터 토크나이즈 요청 수신
self.onmessage = function(e) {
  if (e.data.type === 'tokenize') {
    if (!tokenizer) {
      postMessage({ type: 'tokenize_error', id: e.data.id, message: '초기화 미완료' });
      return;
    }
    try {
      const tokens = tokenizer.tokenize(e.data.text);
      postMessage({ type: 'tokenize_result', id: e.data.id, tokens });
    } catch(err) {
      postMessage({ type: 'tokenize_error', id: e.data.id, message: err.message });
    }
  }
};
