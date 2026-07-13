import clsx from 'clsx';
import { MessageSquare, Plus } from 'lucide-react';
import { Chat } from '@/types';
import Spinner from '@/components/common/Spinner';

interface ChatListProps {
  chats: Chat[] | undefined;
  activeChatId?: string;
  loading?: boolean;
  onSelect: (chat: Chat) => void;
  onNew: () => void;
  disabled?: boolean;
}

export default function ChatList({
  chats,
  activeChatId,
  loading,
  onSelect,
  onNew,
  disabled,
}: ChatListProps) {
  return (
    <div className="flex h-full flex-col">
      <div className="p-3">
        <button
          onClick={onNew}
          disabled={disabled}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Plus className="h-4 w-4" /> New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-3">
        {loading ? (
          <div className="py-6">
            <Spinner label="Loading chats..." />
          </div>
        ) : !chats || chats.length === 0 ? (
          <p className="px-3 py-6 text-center text-xs text-slate-400">
            No conversations yet.
          </p>
        ) : (
          <ul className="space-y-1">
            {chats.map((chat) => (
              <li key={chat.id}>
                <button
                  onClick={() => onSelect(chat)}
                  className={clsx(
                    'flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors',
                    chat.id === activeChatId
                      ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300'
                      : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
                  )}
                >
                  <MessageSquare className="h-4 w-4 shrink-0" />
                  <span className="truncate">{chat.title || 'Untitled'}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
