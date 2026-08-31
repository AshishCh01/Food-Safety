import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { listNotifications, markAllNotificationsRead, markNotificationRead } from '../../services/notificationService';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Checkbox from '../../components/ui/Checkbox';
import EmptyState from '../../components/ui/EmptyState';
import ErrorState from '../../components/ui/ErrorState';
import Pagination from '../../components/ui/Pagination';
import Skeleton from '../../components/ui/Skeleton';
import { formatDateTime } from '../../utils/formatters';
import { configFor, NOTIFICATION_TYPES } from '../../utils/statusConfig';

const PAGE_SIZE = 20;

function Notifications() {
  const { getAccessToken } = useAuth();
  const [result, setResult] = useState(null);
  const [page, setPage] = useState(1);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    const token = getAccessToken();
    listNotifications(token, { isRead: unreadOnly ? false : undefined, page, pageSize: PAGE_SIZE })
      .then(setResult)
      .catch((err) => setError(err.message));
  }, [getAccessToken, page, unreadOnly]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleMarkRead(notificationId) {
    try {
      await markNotificationRead(notificationId, getAccessToken());
      window.dispatchEvent(new CustomEvent('notifications_updated'));
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleMarkAllRead() {
    try {
      await markAllNotificationsRead(getAccessToken());
      window.dispatchEvent(new CustomEvent('notifications_updated'));
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <ContentContainer>
      <PageHeader
        title="Notifications"
        actions={
          <Button variant="secondary" size="sm" onClick={handleMarkAllRead}>
            Mark all as read
          </Button>
        }
      />

      {error && <ErrorState message={error} />}

      <Checkbox
        id="unread-only-filter"
        label="Unread only"
        checked={unreadOnly}
        onChange={(event) => {
          setPage(1);
          setUnreadOnly(event.target.checked);
        }}
      />

      {!result && !error && <Skeleton.List rows={4} />}
      {result && result.items.length === 0 && <EmptyState title="No notifications yet." />}

      <ul className="flex flex-col gap-2">
        {result?.items.map((item) => (
          <NotificationItem key={item.id} item={item} onMarkRead={() => handleMarkRead(item.id)} />
        ))}
      </ul>

      {result && result.total > PAGE_SIZE && (
        <Pagination page={page} pageSize={PAGE_SIZE} total={result.total} onPageChange={setPage} />
      )}
    </ContentContainer>
  );
}

function NotificationItem({ item, onMarkRead }) {
  const type = configFor(NOTIFICATION_TYPES, item.type);
  return (
    <li
      className={`rounded-lg border p-4 ${item.is_read ? 'border-slate-200 bg-white' : 'border-brand-200 bg-brand-50/40'}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <p className="font-medium text-slate-900">{item.title}</p>
        {!item.is_read && <Badge tone="info">Unread</Badge>}
      </div>
      <p className="mt-0.5 text-xs text-slate-500">
        {type.label} &middot; {formatDateTime(item.created_at)}
      </p>
      <p className="mt-1.5 text-sm text-slate-600">{item.message}</p>
      {!item.is_read && (
        <Button variant="ghost" size="sm" className="mt-2 px-0" onClick={onMarkRead}>
          Mark as read
        </Button>
      )}
    </li>
  );
}

export default Notifications;
