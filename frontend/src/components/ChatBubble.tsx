import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import clsx from 'classnames';
import CoachStructuredView from './coach/CoachStructuredView';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text?: string;
  imageUrls?: string[];
  structured?: any;
  game?: 'general' | 'lol' | 'pubg';
}

interface Props {
  message: ChatMessage;
}

const ChatBubble: React.FC<Props> = ({ message }) => {
  let structuredData: any = null;
  if (message.structured) {
    structuredData = message.structured;
  } else if (message.role === 'assistant' && message.text?.trim().startsWith('{')) {
    try {
      const parsed = JSON.parse(message.text);
      // 최소 필드 존재 여부 확인 – overview 또는 recommendations 등
      if (
        parsed && typeof parsed === 'object' &&
        ('overview' in parsed || 'recommendations' in parsed || 'strengths' in parsed)
      ) {
        structuredData = parsed;
      }
    } catch {
      /* ignore */
    }
  }

  // Hide empty assistant placeholder (render ThinkingBubble externally)
  if (
    message.role === 'assistant' &&
    (!message.text || message.text.trim().length === 0) &&
    !structuredData &&
    (!message.imageUrls || message.imageUrls.length === 0)
  ) {
    return null;
  }

  return (
    <div
      className={clsx('my-2 flex', {
        'justify-end': message.role === 'user',
        'justify-start': message.role === 'assistant',
      })}
    >
      <div
        className={clsx(
          'max-w-[75%] rounded-lg p-3 text-sm',
          message.role === 'user'
            ? 'bg-primary text-bg rounded-br-none'
            : 'bg-surface text-text border border-border rounded-bl-none',
        )}
      >
        {structuredData ? (
          <CoachStructuredView data={structuredData} game={message.game} />
        ) : (
          message.text && (
            message.role === 'assistant' ? (
              <ReactMarkdown remarkPlugins={[remarkGfm]} className="whitespace-pre-wrap">
                {message.text}
              </ReactMarkdown>
            ) : (
              <p className="mb-1 whitespace-pre-wrap">{message.text}</p>
            )
          )
        )}

        {message.imageUrls && message.imageUrls.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.imageUrls.map((u) => (
              <img key={u} src={u} alt="uploaded" className="max-w-[150px] rounded" />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatBubble; 