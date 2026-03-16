---
name: realtime-socket-react-query
description: Use when implementing real-time updates in a React app that uses React Query (TanStack Query) and WebSockets. Use when adding live data sync, push notifications of backend changes, or replacing polling with socket-driven cache invalidation.
context: fork
---

# Real-Time Updates with WebSockets + React Query

## Purpose

This skill guides implementing real-time frontend updates by combining WebSockets as an **event notifier** with React Query as the **data fetcher and cache manager**. Instead of pushing full data through sockets, the backend emits lightweight event signals, and the frontend invalidates the relevant React Query cache to refetch fresh data.

## When to Use This Skill

Use this skill when:
- Adding real-time updates to an app already using React Query / TanStack Query
- Replacing polling (`refetchInterval`) with socket-driven invalidation
- Building features like live dashboards, transaction feeds, or status trackers
- You need consistent cache state between REST API responses and real-time events

Do NOT use when:
- You need sub-50ms latency for every data update (push full data via socket instead)
- The app doesn't use React Query for data fetching
- You're building a chat/messaging system where socket IS the primary data transport

## Architecture Overview

```
User logs in --> Frontend opens socket connection
Backend event occurs (transaction, status change, etc.)
Backend emits lightweight event: { type: "balance_updated", userId: "123" }
Frontend receives event --> invalidates matching React Query cache
React Query refetches fresh data from REST API
UI updates automatically
```

**Key principle:** Sockets notify, React Query fetches. No dual state management.

## Quick Reference

| Concern | Handled By |
|---------|-----------|
| Data fetching & caching | React Query |
| Real-time event notification | WebSocket |
| Cache invalidation trigger | Socket event listener |
| Retry & error handling | React Query (built-in) |
| Reconnection | Socket client (built-in) |

## Implementation

### Phase 1: Socket Connection Manager

Create a singleton socket hook that connects on auth and disconnects on logout.

```typescript
// hooks/useSocketConnection.ts
import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { io, Socket } from 'socket.io-client';
import { useAuth } from './useAuth';

// Map of socket event names to the React Query keys they invalidate
const EVENT_QUERY_MAP: Record<string, string[]> = {
  transaction_happened: ['transactions', 'balance'],
  balance_updated: ['balance'],
  loan_status_changed: ['loans', 'loan-summary'],
  profile_updated: ['profile'],
};

export function useSocketConnection() {
  const queryClient = useQueryClient();
  const socketRef = useRef<Socket | null>(null);
  const { user, token } = useAuth();

  useEffect(() => {
    if (!user || !token) return;

    const socket = io(process.env.NEXT_PUBLIC_WS_URL!, {
      auth: { token },
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
    });

    // Register all event listeners from the map
    Object.entries(EVENT_QUERY_MAP).forEach(([event, queryKeys]) => {
      socket.on(event, () => {
        queryKeys.forEach((key) => {
          queryClient.invalidateQueries({ queryKey: [key] });
        });
      });
    });

    socket.on('connect_error', (err) => {
      console.error('Socket connection error:', err.message);
    });

    socketRef.current = socket;

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [user, token, queryClient]);

  return socketRef;
}
```

### Phase 2: Mount at App Root

```typescript
// app/providers.tsx (or layout wrapper)
function SocketProvider({ children }: { children: React.ReactNode }) {
  useSocketConnection(); // connects when authenticated
  return <>{children}</>;
}

// Wrap inside QueryClientProvider
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <SocketProvider>
          {children}
        </SocketProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
```

### Phase 3: Backend Event Emission (Django Example)

```python
# utils/realtime.py
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def emit_event(user_id: str, event_type: str, metadata: dict | None = None):
    """
    Emit a lightweight event through WebSocket.
    No full data payload - just the event signal.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "push.event",
            "event": event_type,
            "metadata": metadata or {},
        },
    )
```

```python
# Usage in views/signals/tasks
from utils.realtime import emit_event

def process_transaction(transaction):
    # ... business logic ...
    transaction.save()

    # Notify frontend - no data payload, just the signal
    emit_event(
        user_id=str(transaction.user_id),
        event_type="transaction_happened",
    )
```

### Phase 4: Node.js / Express Backend Alternative

```typescript
// For Socket.IO backends
io.to(`user_${userId}`).emit('transaction_happened', {
  // Minimal metadata only - no full data
  timestamp: Date.now(),
});
```

## Adding New Real-Time Events

To add a new real-time event:

1. **Backend:** Call `emit_event()` (or `io.emit()`) with the new event name
2. **Frontend:** Add the event name and its query keys to `EVENT_QUERY_MAP`

```typescript
// Just add one line:
const EVENT_QUERY_MAP: Record<string, string[]> = {
  // ... existing events ...
  notification_received: ['notifications', 'unread-count'],  // new
};
```

No new hooks, no new components, no new state management.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Sending full data objects through socket | Send only event name + minimal metadata. Let React Query fetch the data. |
| Creating separate state for socket data | Don't. React Query is the single source of truth. |
| Not handling socket reconnection | Use `reconnection: true` in socket config. React Query handles stale data on reconnect via `refetchOnReconnect`. |
| Invalidating too broadly | Be specific with query keys. `['transactions']` not `['data']`. |
| Missing cleanup on unmount | Always return cleanup function in useEffect to disconnect socket. |
| Connecting before auth is ready | Guard socket connection with auth check (`if (!user || !token) return`). |

## Scaling Considerations

- **Multiple tabs:** Each tab opens its own socket. Consider `BroadcastChannel` API to share one connection across tabs.
- **High-frequency events:** If backend emits events rapidly (e.g., stock tickers), debounce invalidation to avoid refetch storms:

```typescript
import { debounce } from 'lodash-es';

const debouncedInvalidate = debounce(
  (queryKey: string) => queryClient.invalidateQueries({ queryKey: [queryKey] }),
  300
);
```

- **Selective refetch:** For events with metadata, use `queryClient.invalidateQueries({ queryKey: ['transactions', { type: metadata.txType }] })` for granular invalidation.
