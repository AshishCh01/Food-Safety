import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  getUnreadNotificationCount,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from './notificationService';

afterEach(() => {
  vi.unstubAllGlobals();
});

function stubFetch(body = { items: [], total: 0 }) {
  const fetchMock = vi.fn(() =>
    Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(body),
    })
  );
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

describe('listNotifications', () => {
  it('builds a query string with only the provided filters', async () => {
    const fetchMock = stubFetch();

    await listNotifications('token123', { isRead: false, page: 2, pageSize: 10 });

    const calledUrl = fetchMock.mock.calls[0][0].toString();
    expect(calledUrl).toContain('/notifications?');
    expect(calledUrl).toContain('is_read=false');
    expect(calledUrl).toContain('page=2');
    expect(calledUrl).toContain('page_size=10');
  });

  it('omits is_read when not specified', async () => {
    const fetchMock = stubFetch();

    await listNotifications('token123', {});

    const calledUrl = fetchMock.mock.calls[0][0].toString();
    expect(calledUrl).not.toContain('is_read');
  });

  it('attaches the bearer token', async () => {
    const fetchMock = stubFetch();

    await listNotifications('token123', {});

    const options = fetchMock.mock.calls[0][1];
    expect(options.headers.Authorization).toBe('Bearer token123');
  });
});

describe('getUnreadNotificationCount', () => {
  it('requests the unread-count endpoint', async () => {
    const fetchMock = stubFetch({ unread_count: 3 });

    const result = await getUnreadNotificationCount('token123');

    expect(fetchMock.mock.calls[0][0].toString()).toContain('/notifications/unread-count');
    expect(result.unread_count).toBe(3);
  });
});

describe('markNotificationRead', () => {
  it('sends a PATCH to the notification read endpoint', async () => {
    const fetchMock = stubFetch({ id: 'abc', is_read: true });

    await markNotificationRead('abc', 'token123');

    const [url, options] = fetchMock.mock.calls[0];
    expect(url.toString()).toContain('/notifications/abc/read');
    expect(options.method).toBe('PATCH');
  });
});

describe('markAllNotificationsRead', () => {
  it('sends a POST to the read-all endpoint', async () => {
    const fetchMock = stubFetch({ marked_count: 2 });

    await markAllNotificationsRead('token123');

    const [url, options] = fetchMock.mock.calls[0];
    expect(url.toString()).toContain('/notifications/read-all');
    expect(options.method).toBe('POST');
  });
});
