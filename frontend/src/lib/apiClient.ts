import type { ChatApiRequest, ChatResponse } from './types.js';
import { isChatResponse } from './chatResponseValidation.js';

export class ChatApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = 'ChatApiError';
  }
}

export async function sendChatMessage(
  request: ChatApiRequest,
  fetcher: typeof fetch = fetch,
): Promise<ChatResponse> {
  const response = await fetcher('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new ChatApiError(
      `답변을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요. (${response.status})`,
      response.status,
    );
  }

  const payload: unknown = await response.json();
  if (!isChatResponse(payload)) {
    throw new ChatApiError('서버 응답 형식이 올바르지 않습니다.');
  }

  return payload;
}
