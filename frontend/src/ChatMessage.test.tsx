import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { renderToStaticMarkup } from 'react-dom/server';
import { ChatMessage } from './ChatMessage.js';
import type { ConversationMessage } from './lib/types.js';

describe('ChatMessage', () => {
  it('renders sourceDomains from assistant responses in a visible 출처 section', () => {
    const message: ConversationMessage = {
      id: 'assistant-1',
      role: 'assistant',
      createdAt: '2026-06-22T00:00:00.000Z',
      response: {
        type: 'answer',
        isTourismRelated: true,
        answer: '공식 데이터 기반 추천입니다.',
        sourceDomains: ['visitkorea.or.kr', 'mcst.go.kr'],
        warnings: [],
      },
    };

    const html = renderToStaticMarkup(<ChatMessage message={message} />);

    assert.match(html, /<section class="source-domains" aria-label="출처 도메인">/);
    assert.match(html, /출처: /);
    assert.match(html, /visitkorea\.or\.kr, mcst\.go\.kr/);
  });

  it('does not render a visible warnings or debug section', () => {
    const message: ConversationMessage = {
      id: 'assistant-1',
      role: 'assistant',
      createdAt: '2026-06-22T00:00:00.000Z',
      response: {
        type: 'answer',
        isTourismRelated: true,
        answer: '공식 데이터 기반 추천입니다.',
        sourceDomains: [],
        warnings: ['api_data_first_answer', 'llm_scope_recheck_accepted'],
      },
    };

    const html = renderToStaticMarkup(<ChatMessage message={message} />);

    assert.doesNotMatch(html, /aria-label="경고"/);
    assert.doesNotMatch(html, /안내/);
    assert.doesNotMatch(html, /api_data_first_answer/);
    assert.doesNotMatch(html, /llm_scope_recheck_accepted/);
  });
});
