import type { ChatResponse } from '../../lib/types.js';

export const backendChatResponseWithNullOptionalItemFields = {
  type: 'answer',
  isTourismRelated: true,
  answer: '비 오는 날에도 방문하기 좋은 부산 실내 관광지를 추천합니다.',
  items: [
    {
      title: '부산시립미술관',
      reason: '실내 전시를 관람할 수 있습니다.',
      address: null,
      openingHours: null,
      price: null,
      officialUrl: null,
      mapUrl: null,
    },
  ],
  sourceDomains: ['visitbusan.net'],
  warnings: [],
} satisfies ChatResponse;
