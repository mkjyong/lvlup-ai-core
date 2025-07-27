import React from 'react';
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

const ChatBubble: React.FC<Props> = ({ message }) => (
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
      {message.structured ? (
        <CoachStructuredView data={message.structured} game={message.game} />
      ) : (
        message.text && <p className="mb-1 whitespace-pre-wrap">{message.text}</p>
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

export default ChatBubble; 