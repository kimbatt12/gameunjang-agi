import type { ChatItem, ChatResponse, ChatResponseType } from './types.js';

export function isChatResponse(payload: unknown): payload is ChatResponse {
  if (!payload || typeof payload !== 'object') {
    return false;
  }

  const candidate = payload as Partial<ChatResponse>;
  return (
    isChatResponseType(candidate.type) &&
    (typeof candidate.isTourismRelated === 'boolean' || candidate.isTourismRelated === null) &&
    typeof candidate.answer === 'string' &&
    (candidate.items === undefined ||
      (Array.isArray(candidate.items) && candidate.items.every(isChatItem))) &&
    Array.isArray(candidate.sourceDomains) &&
    candidate.sourceDomains.every(isString) &&
    Array.isArray(candidate.warnings) &&
    candidate.warnings.every(isString)
  );
}

function isChatResponseType(value: unknown): value is ChatResponseType {
  return value === 'answer' || value === 'rejection' || value === 'limit_exceeded';
}

function isChatItem(payload: unknown): payload is ChatItem {
  if (!payload || typeof payload !== 'object') {
    return false;
  }

  const candidate = payload as Partial<ChatItem>;
  return (
    typeof candidate.title === 'string' &&
    isOptionalNullableString(candidate.reason) &&
    isOptionalNullableString(candidate.address) &&
    isOptionalNullableString(candidate.openingHours) &&
    isOptionalNullableString(candidate.price) &&
    isOptionalNullableString(candidate.officialUrl) &&
    isOptionalNullableString(candidate.mapUrl)
  );
}

function isOptionalNullableString(value: unknown): value is string | null | undefined {
  return value === undefined || value === null || typeof value === 'string';
}

function isString(value: unknown): value is string {
  return typeof value === 'string';
}
