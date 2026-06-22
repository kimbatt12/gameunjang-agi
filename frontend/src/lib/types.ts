export type ChatResponseType = 'answer' | 'rejection' | 'limit_exceeded';

export type ChatItem = {
  title: string;
  reason?: string;
  address?: string;
  openingHours?: string;
  price?: string;
  officialUrl?: string;
  mapUrl?: string;
};

export type ChatResponse = {
  type: ChatResponseType;
  isTourismRelated: boolean | null;
  answer: string;
  items?: ChatItem[];
  sourceDomains: string[];
  warnings: string[];
};

export type ChatApiRequest = {
  message: string;
  localConversationId: string;
  clientSessionQuestionCount: number;
  clientContext: {
    timezone: string;
  };
};

export type UserMessage = {
  id: string;
  role: 'user';
  content: string;
  createdAt: string;
};

export type AssistantMessage = {
  id: string;
  role: 'assistant';
  response: ChatResponse;
  createdAt: string;
};

export type ConversationMessage = UserMessage | AssistantMessage;

export type LocalConversation = {
  id: string;
  messages: ConversationMessage[];
  updatedAt: string;
};
