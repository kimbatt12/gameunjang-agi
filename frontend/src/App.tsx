import { FormEvent, useEffect, useRef, useState } from 'react';
import './App.css';
import { ChatMessage } from './ChatMessage.js';
import { sendChatMessage } from './lib/apiClient.js';
import {
  appendMessages,
  clearConversation,
  loadConversation,
  saveConversation,
} from './lib/localConversation.js';
import {
  LIMIT_REACHED_MESSAGE,
  MAX_SESSION_QUESTIONS,
  canAskQuestion,
  getQuestionCount,
  incrementQuestionCount,
} from './lib/sessionLimit.js';
import type { ChatResponse, ConversationMessage } from './lib/types.js';

const REQUEST_ERROR_RESPONSE: ChatResponse = {
  type: 'answer',
  isTourismRelated: null,
  answer: '답변을 가져오지 못했습니다. 네트워크 상태를 확인한 뒤 다시 시도해 주세요.',
  sourceDomains: [],
  warnings: ['api_request_failed'],
};

function createMessageId(prefix: string): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return `${prefix}-${crypto.randomUUID()}`;
  }

  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function App() {
  const [conversation, setConversation] = useState(() =>
    loadConversation(window.localStorage),
  );
  const [inputValue, setInputValue] = useState('');
  const [questionCount, setQuestionCount] = useState(() =>
    getQuestionCount(window.sessionStorage),
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const messageListRef = useRef<HTMLDivElement | null>(null);
  const conversationRevisionRef = useRef(0);

  const remainingQuestions = Math.max(MAX_SESSION_QUESTIONS - questionCount, 0);
  const isLimitReached = remainingQuestions === 0;

  useEffect(() => {
    saveConversation(window.localStorage, conversation);
  }, [conversation]);

  useEffect(() => {
    messageListRef.current?.scrollTo({
      top: messageListRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [conversation.messages.length, isSubmitting]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedMessage = inputValue.trim();

    if (!trimmedMessage || isSubmitting) {
      return;
    }

    if (!canAskQuestion(window.sessionStorage)) {
      setErrorMessage(LIMIT_REACHED_MESSAGE);
      return;
    }

    setErrorMessage(null);
    const now = new Date().toISOString();
    const userMessage: ConversationMessage = {
      id: createMessageId('user'),
      role: 'user',
      content: trimmedMessage,
      createdAt: now,
    };
    const nextCount = incrementQuestionCount(window.sessionStorage);
    setQuestionCount(nextCount);
    setConversation((current) => appendMessages(current, [userMessage]));
    setInputValue('');
    setIsSubmitting(true);
    const requestConversationRevision = conversationRevisionRef.current;

    try {
      const response = await sendChatMessage({
        message: trimmedMessage,
        localConversationId: conversation.id,
        clientSessionQuestionCount: nextCount,
        clientContext: {
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        },
      });
      const assistantMessage: ConversationMessage = {
        id: createMessageId('assistant'),
        role: 'assistant',
        response,
        createdAt: new Date().toISOString(),
      };
      if (requestConversationRevision !== conversationRevisionRef.current) {
        return;
      }
      setConversation((current) => appendMessages(current, [assistantMessage]));
    } catch (error) {
      if (requestConversationRevision !== conversationRevisionRef.current) {
        return;
      }
      const message = error instanceof Error ? error.message : REQUEST_ERROR_RESPONSE.answer;
      setErrorMessage(message);
      setConversation((current) =>
        appendMessages(current, [
          {
            id: createMessageId('assistant'),
            role: 'assistant',
            response: {
              ...REQUEST_ERROR_RESPONSE,
              answer: message,
            },
            createdAt: new Date().toISOString(),
          },
        ]),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleClearConversation() {
    conversationRevisionRef.current += 1;
    setConversation(clearConversation(window.localStorage));
    setErrorMessage(null);
  }

  return (
    <main className="app-shell">
      <section className="chat-panel" aria-labelledby="app-title">
        <header className="chat-header">
          <div>
            <p className="eyebrow">Gameunjang-agi</p>
            <h1 id="app-title">국내 관광 챗봇</h1>
            <p>
              관광지, 숙소, 맛집, 축제, 일정 질문을 공식·공공 데이터 기반으로
              물어보세요.
            </p>
          </div>
          <button
            className="ghost-button"
            type="button"
            onClick={handleClearConversation}
            disabled={isSubmitting}
          >
            대화 초기화
          </button>
        </header>

        <div className="session-notice" role={isLimitReached ? 'alert' : 'status'}>
          <strong>{MAX_SESSION_QUESTIONS}회 중 {questionCount}회 사용</strong>
          <span>
            {isLimitReached
              ? LIMIT_REACHED_MESSAGE
              : `이번 브라우저 세션에서 ${remainingQuestions}회 더 질문할 수 있습니다.`}
          </span>
        </div>

        <div className="message-list" ref={messageListRef} aria-live="polite">
          {conversation.messages.length === 0 ? <EmptyState /> : null}
          {conversation.messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {isSubmitting ? (
            <article className="message message-assistant loading-message">
              답변을 준비하고 있습니다…
            </article>
          ) : null}
        </div>

        {errorMessage ? (
          <div className="error-banner" role="alert">
            {errorMessage}
          </div>
        ) : null}

        <form className="chat-form" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="chat-input">
            국내 관광 질문 입력
          </label>
          <textarea
            id="chat-input"
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            placeholder="예: 이번 주말 아이랑 부산에서 갈 만한 실내 관광지 추천해줘"
            rows={3}
            disabled={isSubmitting || isLimitReached}
          />
          <button type="submit" disabled={isSubmitting || isLimitReached || !inputValue.trim()}>
            질문하기
          </button>
        </form>
      </section>
    </main>
  );
}

function EmptyState() {
  return (
    <article className="empty-state">
      <h2>무엇을 도와드릴까요?</h2>
      <p>“강릉 2박 3일 코스”, “서울 이번 달 축제”, “제주 비 오는 날 갈 곳”처럼 질문해 보세요.</p>
    </article>
  );
}
