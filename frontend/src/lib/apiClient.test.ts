import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { ChatApiError, sendChatMessage } from './apiClient.js';
import type { ChatApiRequest, ChatResponse } from './types.js';

const request: ChatApiRequest = {
  message: '부산 실내 관광지 추천해줘',
  localConversationId: 'conversation-1',
  clientSessionQuestionCount: 1,
  clientContext: {
    timezone: 'Asia/Seoul',
  },
};

const validResponse: ChatResponse = {
  type: 'answer',
  isTourismRelated: true,
  answer: '추천합니다.',
  items: [
    {
      title: '부산시립미술관',
      reason: '비 오는 날에도 관람할 수 있습니다.',
      address: '부산 해운대구 APEC로 58',
      openingHours: '10:00-18:00',
      price: '무료',
      officialUrl: 'https://example.com',
      mapUrl: 'https://maps.example.com',
    },
  ],
  sourceDomains: ['example.com'],
  warnings: [],
};

describe('sendChatMessage', () => {
  it('returns deeply validated API chat responses', async () => {
    const response = await sendChatMessage(request, createJsonFetcher(validResponse));

    assert.deepEqual(response, validResponse);
  });

  it('posts /api/chat happy path requests with the expected JSON contract', async () => {
    const calls: Array<{ input: string | URL | Request; init?: RequestInit }> = [];
    const fetcher: typeof fetch = async (input, init) => {
      calls.push({ input, init });
      return jsonResponse(validResponse, 200);
    };

    const response = await sendChatMessage(request, fetcher);

    assert.deepEqual(response, validResponse);
    assert.equal(calls.length, 1);
    assert.equal(calls[0].input, '/api/chat');
    assert.equal(calls[0].init?.method, 'POST');
    assert.deepEqual(calls[0].init?.headers, { 'Content-Type': 'application/json' });
    assert.deepEqual(JSON.parse(String(calls[0].init?.body)), request);
  });

  it('raises a typed error for /api/chat error responses', async () => {
    const fetcher: typeof fetch = async () => jsonResponse({ detail: 'backend failed' }, 503);

    await assert.rejects(
      sendChatMessage(request, fetcher),
      (error: unknown) =>
        error instanceof ChatApiError &&
        error.status === 503 &&
        error.message === '답변을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요. (503)',
    );
  });

  it('rejects malformed nested API item payloads', async () => {
    const malformedResponse = {
      ...validResponse,
      items: [{ title: '부산시립미술관', reason: null }],
    };

    await assert.rejects(
      sendChatMessage(request, createJsonFetcher(malformedResponse)),
      (error: unknown) =>
        error instanceof ChatApiError && error.message === '서버 응답 형식이 올바르지 않습니다.',
    );
  });

  it('rejects API responses with invalid tourism relation flags', async () => {
    const malformedResponse = {
      ...validResponse,
      isTourismRelated: 'yes',
    };

    await assert.rejects(
      sendChatMessage(request, createJsonFetcher(malformedResponse)),
      (error: unknown) =>
        error instanceof ChatApiError && error.message === '서버 응답 형식이 올바르지 않습니다.',
    );
  });
});

function createJsonFetcher(payload: unknown): typeof fetch {
  return async () => jsonResponse(payload, 200);
}

function jsonResponse(payload: unknown, status: number): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      'Content-Type': 'application/json',
    },
  });
}
