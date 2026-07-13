import { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import clsx from 'clsx';
import { Bot, User as UserIcon } from 'lucide-react';
import { Message } from '@/types';
import MessageArtifacts from './MessageArtifacts';

interface MessageBubbleProps {
  message: Pick<Message, 'role' | 'content' | 'artifacts' | 'id'>;
  streaming?: boolean;
}

function MessageBubble({ message, streaming }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={clsx(
        'flex w-full gap-3 py-4',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      <div
        className={clsx(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg',
          isUser
            ? 'bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-200'
            : 'bg-brand-600 text-white'
        )}
      >
        {isUser ? <UserIcon className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div
        className={clsx(
          'min-w-0 max-w-[85%] flex-1',
          isUser ? 'flex flex-col items-end' : ''
        )}
      >
        <div
          className={clsx(
            'rounded-2xl px-4 py-3',
            isUser
              ? 'bg-brand-600 text-white'
              : 'surface text-slate-800 dark:text-slate-100'
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {message.content}
            </p>
          ) : (
            <div className="prose-chat">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    const isBlock = Boolean(match) || String(children).includes('\n');
                    if (!isBlock) {
                      return (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    }
                    return (
                      <SyntaxHighlighter
                        style={oneDark}
                        language={match?.[1] ?? 'text'}
                        PreTag="div"
                        customStyle={{
                          borderRadius: 8,
                          fontSize: 12.5,
                          margin: '0.5rem 0',
                        }}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    );
                  },
                }}
              >
                {message.content || (streaming ? '' : '_No response._')}
              </ReactMarkdown>
              {streaming && (
                <span className="ml-0.5 inline-block h-4 w-2 animate-pulse bg-brand-500 align-middle" />
              )}
            </div>
          )}
        </div>

        {!isUser && message.artifacts && (
          <MessageArtifacts artifacts={message.artifacts} messageId={message.id} />
        )}
      </div>
    </div>
  );
}

export default memo(MessageBubble);
