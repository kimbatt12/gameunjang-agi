import { getSafeHttpUrl } from './lib/safeUrl.js';
import type { ChatItem, ConversationMessage } from './lib/types.js';

export function ChatMessage({ message }: { message: ConversationMessage }) {
  if (message.role === 'user') {
    return <article className="message message-user">{message.content}</article>;
  }

  return (
    <article className="message message-assistant">
      <p className="answer-text">{message.response.answer}</p>
      {message.response.items?.length ? <ItemList items={message.response.items} /> : null}
      {message.response.warnings.length ? (
        <section className="response-section" aria-label="경고">
          <h3>안내</h3>
          <ul>
            {message.response.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </section>
      ) : null}
      {message.response.sourceDomains.length ? (
        <section className="source-domains" aria-label="출처 도메인">
          출처: {message.response.sourceDomains.join(', ')}
        </section>
      ) : null}
    </article>
  );
}

function ItemList({ items }: { items: ChatItem[] }) {
  return (
    <section className="response-section" aria-label="추천 항목">
      <h3>추천 항목</h3>
      <ul className="item-list">
        {items.map((item) => (
          <li key={`${item.title}-${item.address ?? ''}`} className="item-card">
            <strong>{item.title}</strong>
            {item.reason ? <p>{item.reason}</p> : null}
            <dl>
              {item.address ? <Detail label="주소" value={item.address} /> : null}
              {item.openingHours ? <Detail label="운영시간" value={item.openingHours} /> : null}
              {item.price ? <Detail label="비용" value={item.price} /> : null}
            </dl>
            <div className="item-links">
              <SafeItemLink href={item.officialUrl} label="공식 링크" />
              <SafeItemLink href={item.mapUrl} label="지도 링크" />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

function SafeItemLink({ href, label }: { href: string | null | undefined; label: string }) {
  const safeHref = getSafeHttpUrl(href);
  return safeHref ? <a href={safeHref}>{label}</a> : null;
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  );
}
