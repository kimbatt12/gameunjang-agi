import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { backendChatResponseWithNullOptionalItemFields } from '../test/fixtures/backendChatResponse.js';
import { isChatResponse } from './chatResponseValidation.js';

describe('isChatResponse', () => {
  it('accepts backend-shaped chat responses with null optional item fields', () => {
    assert.equal(isChatResponse(backendChatResponseWithNullOptionalItemFields), true);
  });

  it('accepts public chat responses with an empty warnings list', () => {
    assert.equal(
      isChatResponse({
        type: 'answer',
        isTourismRelated: true,
        answer: '공식 데이터 기반 추천입니다.',
        items: [],
        sourceDomains: ['visitkorea.or.kr'],
        warnings: [],
      }),
      true,
    );
  });

  it('rejects optional item fields with non-string non-null values', () => {
    const malformedResponse = {
      ...backendChatResponseWithNullOptionalItemFields,
      items: [
        {
          ...backendChatResponseWithNullOptionalItemFields.items[0],
          officialUrl: 123,
        },
      ],
    };

    assert.equal(isChatResponse(malformedResponse), false);
  });
});
