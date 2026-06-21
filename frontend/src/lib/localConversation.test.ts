import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  LOCAL_CONVERSATION_KEY,
  appendMessages,
  clearConversation,
  loadConversation,
  saveConversation,
} from './localConversation.js';
import { MemoryStorage } from './testStorage.js';

describe('localConversation', () => {
  it('persists and reloads local conversation history', () => {
    const storage = new MemoryStorage();
    const conversation = loadConversation(storage);
    const updated = appendMessages(
      conversation,
      [
        {
          id: 'user-1',
          role: 'user',
          content: '부산 실내 관광지 추천해줘',
          createdAt: '2026-06-21T00:00:00.000Z',
        },
      ],
      new Date('2026-06-21T00:00:00.000Z'),
    );

    saveConversation(storage, updated);

    assert.deepEqual(loadConversation(storage), updated);
  });

  it('clears invalid or user-deleted conversation history', () => {
    const storage = new MemoryStorage();
    storage.setItem(LOCAL_CONVERSATION_KEY, '{invalid-json');

    const recovered = loadConversation(storage);
    assert.equal(recovered.messages.length, 0);

    saveConversation(storage, recovered);
    const cleared = clearConversation(storage);

    assert.equal(storage.getItem(LOCAL_CONVERSATION_KEY), null);
    assert.equal(cleared.messages.length, 0);
  });

  it('starts fresh when persisted user messages are malformed', () => {
    const storage = new MemoryStorage();
    storage.setItem(
      LOCAL_CONVERSATION_KEY,
      JSON.stringify({
        id: 'conversation-1',
        updatedAt: '2026-06-21T00:00:00.000Z',
        messages: [
          {
            id: 'user-1',
            role: 'user',
            createdAt: '2026-06-21T00:00:00.000Z',
          },
        ],
      }),
    );

    assert.equal(loadConversation(storage).messages.length, 0);
  });

  it('starts fresh when persisted assistant messages are malformed', () => {
    const storage = new MemoryStorage();
    storage.setItem(
      LOCAL_CONVERSATION_KEY,
      JSON.stringify({
        id: 'conversation-1',
        updatedAt: '2026-06-21T00:00:00.000Z',
        messages: [
          {
            id: 'assistant-1',
            role: 'assistant',
            createdAt: '2026-06-21T00:00:00.000Z',
            response: {
              type: 'answer',
              isTourismRelated: true,
              answer: '추천합니다.',
              sourceDomains: ['example.com'],
              warnings: [null],
            },
          },
        ],
      }),
    );

    assert.equal(loadConversation(storage).messages.length, 0);
  });

  it('starts fresh when persisted assistant item payloads are malformed', () => {
    const storage = new MemoryStorage();
    storage.setItem(
      LOCAL_CONVERSATION_KEY,
      JSON.stringify({
        id: 'conversation-1',
        updatedAt: '2026-06-21T00:00:00.000Z',
        messages: [
          {
            id: 'assistant-1',
            role: 'assistant',
            createdAt: '2026-06-21T00:00:00.000Z',
            response: {
              type: 'answer',
              isTourismRelated: true,
              answer: '추천합니다.',
              items: [{ reason: 'title missing' }],
              sourceDomains: [],
              warnings: [],
            },
          },
        ],
      }),
    );

    assert.equal(loadConversation(storage).messages.length, 0);
  });
});
