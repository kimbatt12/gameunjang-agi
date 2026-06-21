export const SESSION_LIMIT_KEY = 'gameunjang_agi_question_count';
export const MAX_SESSION_QUESTIONS = 10;
export const LIMIT_REACHED_MESSAGE =
  '이번 브라우저 세션의 질문 한도 10회에 도달했습니다. 새 브라우저 세션을 시작한 뒤 다시 이용해 주세요.';

export type SessionStorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;

export function getQuestionCount(storage: SessionStorageLike): number {
  const rawCount = storage.getItem(SESSION_LIMIT_KEY);
  const parsed = Number.parseInt(rawCount ?? '0', 10);
  return Number.isFinite(parsed) && parsed > 0
    ? Math.min(parsed, MAX_SESSION_QUESTIONS)
    : 0;
}

export function canAskQuestion(storage: SessionStorageLike): boolean {
  return getQuestionCount(storage) < MAX_SESSION_QUESTIONS;
}

export function incrementQuestionCount(storage: SessionStorageLike): number {
  const nextCount = Math.min(getQuestionCount(storage) + 1, MAX_SESSION_QUESTIONS);
  storage.setItem(SESSION_LIMIT_KEY, String(nextCount));
  return nextCount;
}

export function resetQuestionCount(storage: SessionStorageLike): void {
  storage.removeItem(SESSION_LIMIT_KEY);
}

export function getRemainingQuestions(storage: SessionStorageLike): number {
  return Math.max(MAX_SESSION_QUESTIONS - getQuestionCount(storage), 0);
}
