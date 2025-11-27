import * as amplitude from '@amplitude/analytics-browser'

// Initialize Amplitude
const AMPLITUDE_API_KEY = import.meta.env.VITE_AMPLITUDE_API_KEY || ''

if (AMPLITUDE_API_KEY) {
  amplitude.init(AMPLITUDE_API_KEY, {
    defaultTracking: {
      pageViews: true,
      sessions: true,
      formInteractions: true,
      fileDownloads: true,
    },
  })
}

// Analytics service
export const analytics = {
  // Track page views
  trackPageView: (pageName: string, properties?: Record<string, any>) => {
    if (AMPLITUDE_API_KEY) {
      amplitude.track('Page View', {
        page_name: pageName,
        ...properties,
      })
    }
  },

  // Track user login
  trackLogin: (userId: string, method: string = 'handle') => {
    if (AMPLITUDE_API_KEY) {
      amplitude.setUserId(userId)
      amplitude.track('User Logged In', {
        login_method: method,
      })
    }
  },

  // Track user logout
  trackLogout: () => {
    if (AMPLITUDE_API_KEY) {
      amplitude.track('User Logged Out')
      amplitude.setUserId(null)
    }
  },

  // Track chat creation
  trackChatCreated: (chatType: 'dm' | 'group', chatId: number) => {
    if (AMPLITUDE_API_KEY) {
      amplitude.track('Chat Created', {
        chat_type: chatType,
        chat_id: chatId,
      })
    }
  },

  // Track message sent
  trackMessageSent: (chatId: number, messageLength: number, hasReply: boolean = false) => {
    if (AMPLITUDE_API_KEY) {
      amplitude.track('Message Sent', {
        chat_id: chatId,
        message_length: messageLength,
        has_reply: hasReply,
      })
    }
  },

  // Track reaction added
  trackReactionAdded: (messageId: number, emoji: string) => {
    if (AMPLITUDE_API_KEY) {
      amplitude.track('Reaction Added', {
        message_id: messageId,
        emoji: emoji,
      })
    }
  },

  // Track booking created
  trackBookingCreated: (bookingId: number, bookingType: string) => {
    if (AMPLITUDE_API_KEY) {
      amplitude.track('Booking Created', {
        booking_id: bookingId,
        booking_type: bookingType,
      })
    }
  },

  // Track user search
  trackUserSearch: (query: string, resultsCount: number) => {
    if (AMPLITUDE_API_KEY) {
      amplitude.track('User Search', {
        query_length: query.length,
        results_count: resultsCount,
      })
    }
  },

  // Track WebSocket connection
  trackWebSocketConnected: (chatId: number) => {
    if (AMPLITUDE_API_KEY) {
      amplitude.track('WebSocket Connected', {
        chat_id: chatId,
      })
    }
  },

  // Track WebSocket disconnected
  trackWebSocketDisconnected: (chatId: number) => {
    if (AMPLITUDE_API_KEY) {
      amplitude.track('WebSocket Disconnected', {
        chat_id: chatId,
      })
    }
  },

  // Generic track event
  track: (eventName: string, properties?: Record<string, any>) => {
    if (AMPLITUDE_API_KEY) {
      amplitude.track(eventName, properties)
    }
  },

  // Set user properties
  setUserProperties: (properties: Record<string, any>) => {
    if (AMPLITUDE_API_KEY) {
      amplitude.identify(
        new amplitude.Identify().set(properties)
      )
    }
  },
}

