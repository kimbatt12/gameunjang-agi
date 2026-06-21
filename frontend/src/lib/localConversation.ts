import type {
  AssistantMessage,
  ConversationMessage,
  LocalConversation,
  UserMessage,
} from './types.js';
import { isChatResponse } from './chatResponseValidation.js';

export const LOCAL_CONVERSATION_KEY = 'gameunjang_agi_conversation';

export type LocalStorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;

export function createConversationId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }

  return `local-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function createEmptyConversation(now = new Date()): LocalConversation {
  const timestamp = now.toISOString();
  return {
    id: createConversationId(),
    messages: [],
    updatedAt: timestamp,
  };
}

export function loadConversation(storage: LocalStorageLike): LocalConversation {
  const rawValue = storage.getItem(LOCAL_CONVERSATION_KEY);
  if (!rawValue) {
    return createEmptyConversation();
  }

  try {
    const parsed: unknown = JSON.parse(rawValue);
    if (isLocalConversation(parsed)) {
      return parsed;
    }
  } catch {
    // Ignore invalid localStorage content and start a fresh local conversation.
  }

  return createEmptyConversation();
}

export function saveConversation(
  storage: LocalStorageLike,
  conversation: LocalConversation,
): void {
  storage.setItem(LOCAL_CONVERSATION_KEY, JSON.stringify(conversation));
}

export function appendMessages(
  conversation: LocalConversation,
  messages: ConversationMessage[],
  now = new Date(),
): LocalConversation {
  return {
    ...conversation,
    messages: [...conversation.messages, ...messages],
    updatedAt: now.toISOString(),
  };
}

export function clearConversation(storage: LocalStorageLike): LocalConversation {
  storage.removeItem(LOCAL_CONVERSATION_KEY);
  return createEmptyConversation();
}

function isLocalConversation(payload: unknown): payload is LocalConversation {
  if (!payload || typeof payload !== 'object') {
    return false;
  }

  const candidate = payload as Partial<LocalConversation>;
  return (
    typeof candidate.id === 'string' &&
    typeof candidate.updatedAt === 'string' &&
    Array.isArray(candidate.messages) &&
    candidate.messages.every(isConversationMessage)
  );
}

function isConversationMessage(payload: unknown): payload is ConversationMessage {
  if (!payload || typeof payload !== 'object') {
    return false;
  }

  const candidate = payload as Partial<ConversationMessage>;
  if (typeof candidate.id !== 'string' || typeof candidate.createdAt !== 'string') {
    return false;
  }

  if (candidate.role === 'user') {
    return isUserMessage(candidate);
  }

  if (candidate.role === 'assistant') {
    return isAssistantMessage(candidate);
  }

  return false;
}

function isUserMessage(candidate: Partial<UserMessage>): candidate is UserMessage {
  return candidate.role === 'user' && typeof candidate.content === 'string';
}

function isAssistantMessage(
  candidate: Partial<AssistantMessage>,
): candidate is AssistantMessage {
  return candidate.role === 'assistant' && isChatResponse(candidate.response);
}
