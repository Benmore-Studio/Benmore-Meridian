# AI Chatbot Skill - Enterprise Website Assistant

A production-ready AI chatbot skill for creating sophisticated conversational interfaces on business websites. Built with assistant-ui React components, featuring dynamic context-aware responses, professional UI, and easy customization for any industry.

## When to Use This Skill

Use this skill when:
- Building AI chatbots for business websites (B2B or B2C)
- Creating customer support or sales assistance chatbots
- Implementing assistant-ui based chat widgets with OpenAI/Anthropic
- Need dynamic, context-aware follow-up questions
- Building professional chat interfaces with markdown support
- Want a floating chat widget that doesn't interfere with page content

## Quick Start

```bash
# Install required packages
npm install @assistant-ui/react @assistant-ui/react-ai-sdk @assistant-ui/react-markdown ai @ai-sdk/openai lucide-react remark-gfm

# Set up environment variables
echo "OPENAI_API_KEY=your_openai_api_key" >> .env.local
```

## Complete Implementation Guide

### 1. API Route (`app/api/chat/route.ts`)

```typescript
import { openai } from '@ai-sdk/openai';
import { streamText, convertToModelMessages } from 'ai';
import { SYSTEM_PROMPT } from '@/lib/chat/system-prompt';

export const maxDuration = 30;

export async function POST(req: Request) {
  try {
    // Check if API key is configured
    if (!process.env.OPENAI_API_KEY) {
      return new Response(
        JSON.stringify({
          error: 'OpenAI API key not configured. Please add OPENAI_API_KEY to your environment variables.',
        }),
        {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const { messages } = await req.json();

    if (!messages || !Array.isArray(messages)) {
      return new Response(
        JSON.stringify({ error: 'Invalid messages format' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const result = streamText({
      model: openai('gpt-4o-mini'), // Customize model as needed
      system: SYSTEM_PROMPT,
      messages: convertToModelMessages(messages),
      temperature: 0.7,
    });

    return result.toUIMessageStreamResponse();
  } catch (error) {
    console.error('Chat API error:', error);
    return new Response(
      JSON.stringify({
        error: 'An error occurred while processing your message. Please try again.',
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}
```

### 2. System Prompt Template (`lib/chat/system-prompt.ts`)

```typescript
/**
 * CUSTOMIZATION REQUIRED: Replace all placeholders with your company information
 *
 * Placeholders to replace:
 * - [COMPANY_NAME] - Your company name
 * - [COMPANY_TYPE] - Type of business (e.g., "technology company", "law firm", "healthcare provider")
 * - [TONE_STYLE] - Communication style (e.g., "professional", "friendly", "technical")
 * - [PHONE] - Contact phone number
 * - [EMAIL] - Contact email address
 * - [WEBSITE] - Main website URL
 *
 * Add your specific sections for:
 * - Products/Services
 * - Team members
 * - FAQs
 * - Pricing information
 * - Company policies
 */

export const SYSTEM_PROMPT = `You are the AI assistant for [COMPANY_NAME], a [COMPANY_TYPE].
Provide helpful, accurate, and [TONE_STYLE] responses based on the information below.

## Your Role
- Answer questions about our products, services, and company
- Provide helpful information to visitors
- Direct complex inquiries to our human team: [PHONE] or [EMAIL]
- Maintain a [TONE_STYLE] tone in all interactions

## Contact Information
- Phone: [PHONE]
- Email: [EMAIL]
- Website: [WEBSITE]
- Business Hours: [HOURS]
- Location: [ADDRESS]

---

## COMPANY INFORMATION

### About Us
[Add your company description, mission, and values]

### Products/Services
[List and describe your main offerings]

### Team
[Add key team members if relevant]

### Frequently Asked Questions
[Include common Q&As]

### Policies
[Add relevant policies, terms, or important information]

---

## Response Guidelines
- Be concise and helpful
- If unsure, direct to human support
- Don't make up information
- Stay within the provided knowledge base

For detailed assistance, contact us at [PHONE] or [EMAIL].`;
```

### 3. Chat Widget Component (`app/components/ChatWidget.tsx`)

```typescript
'use client';

import { AssistantRuntimeProvider } from '@assistant-ui/react';
import { useChatRuntime } from '@assistant-ui/react-ai-sdk';
import { MessageCircle } from 'lucide-react';
import { useState } from 'react';
import { ChatThread } from './ChatThread';

interface ChatWidgetProps {
  // CUSTOMIZATION: Add any props your implementation needs
  onPageChange?: (page: string) => void;
  primaryColor?: string;
  secondaryColor?: string;
}

export function ChatWidget({
  onPageChange,
  primaryColor = '#008B8B',  // CUSTOMIZE: Your primary brand color
  secondaryColor = '#2A4A3F'  // CUSTOMIZE: Your secondary brand color
}: ChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);

  // useChatRuntime uses /api/chat by default
  const runtime = useChatRuntime();

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {/* Floating Button - CUSTOMIZE: Position, size, colors */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 p-4 rounded-full shadow-2xl hover:shadow-3xl hover:scale-110 transition-all duration-300"
          style={{
            background: `linear-gradient(to right, ${primaryColor}, ${secondaryColor})`
          }}
          aria-label="Open Chat Assistant"
        >
          <MessageCircle className="w-6 h-6 text-white" />
        </button>
      )}

      {/* Chat Modal */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          />

          {/* CUSTOMIZE: Modal size and positioning */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="w-full max-w-4xl h-[90vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden">
              <ChatThread
                onClose={() => setIsOpen(false)}
                onPageChange={onPageChange}
                primaryColor={primaryColor}
                secondaryColor={secondaryColor}
              />
            </div>
          </div>
        </>
      )}
    </AssistantRuntimeProvider>
  );
}
```

### 4. Thread Component with Dynamic Follow-ups (`app/components/ChatThread.tsx`)

```typescript
'use client';

import {
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useMessage,
} from '@assistant-ui/react';
import { Send, Sparkles, X } from 'lucide-react';
import type { FC } from 'react';
import { MarkdownText } from './markdown-text';

interface ChatThreadProps {
  onClose: () => void;
  onPageChange?: (page: string) => void;
  primaryColor?: string;
  secondaryColor?: string;
}

export const ChatThread: FC<ChatThreadProps> = ({
  onClose,
  onPageChange,
  primaryColor = '#008B8B',
  secondaryColor = '#2A4A3F'
}) => {
  return (
    <ThreadPrimitive.Root className="flex h-full flex-col">
      {/* Header - CUSTOMIZE: Company name, tagline, colors */}
      <div
        className="flex items-center justify-between p-6 text-white"
        style={{
          background: `linear-gradient(to right, ${primaryColor}, ${secondaryColor})`
        }}
      >
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-white/20 rounded-full">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-semibold text-xl">[COMPANY_NAME] Assistant</h3>
            <p className="text-sm text-white/90">[YOUR_TAGLINE]</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-white/20 rounded-full transition-colors"
          aria-label="Close chat"
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      {/* Messages */}
      <ThreadPrimitive.Viewport className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50">
        <ThreadPrimitive.Empty>
          <WelcomeMessage primaryColor={primaryColor} />
        </ThreadPrimitive.Empty>

        <ThreadPrimitive.Messages
          components={{
            UserMessage: () => <UserMessage primaryColor={primaryColor} secondaryColor={secondaryColor} />,
            AssistantMessage: () => <AssistantMessage onPageChange={onPageChange} primaryColor={primaryColor} />,
          }}
        />
      </ThreadPrimitive.Viewport>

      {/* Input */}
      <div className="p-6 border-t border-gray-200 bg-white">
        <Composer primaryColor={primaryColor} secondaryColor={secondaryColor} />
      </div>

      {/* Footer - CUSTOMIZE: Contact email */}
      <div className="px-6 py-3 text-center text-sm text-gray-500 bg-gray-50 border-t border-gray-200">
        Powered by AI •{' '}
        <a
          href="mailto:[EMAIL]"
          className="hover:underline font-medium"
          style={{ color: primaryColor }}
        >
          Contact us
        </a>
      </div>
    </ThreadPrimitive.Root>
  );
};

// CUSTOMIZE: Welcome message and initial suggestions
const WelcomeMessage: FC<{primaryColor: string}> = ({ primaryColor }) => {
  return (
    <div className="flex flex-col items-center justify-center text-center py-12">
      <div
        className="p-4 rounded-full mb-6"
        style={{
          background: `linear-gradient(to bottom right, ${primaryColor}20, ${primaryColor}10)`
        }}
      >
        <Sparkles className="w-16 h-16" style={{ color: primaryColor }} />
      </div>
      <h4 className="text-2xl font-bold text-gray-900 mb-3">
        Welcome to [COMPANY_NAME]
      </h4>
      <p className="text-base text-gray-600 mb-8 max-w-xl leading-relaxed">
        [WELCOME_MESSAGE - Describe what your assistant can help with]
      </p>
      <div className="flex flex-wrap gap-3 justify-center max-w-2xl">
        {/* CUSTOMIZE: Add your own welcome suggestions */}
        <ThreadPrimitive.Suggestion
          prompt="[SUGGESTION_1_PROMPT]"
          autoSend
          asChild
        >
          <button
            className="px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-all shadow-sm hover:shadow"
            style={{
              borderColor: primaryColor + '50',
              '&:hover': { borderColor: primaryColor, color: primaryColor }
            }}
          >
            [SUGGESTION_1_LABEL]
          </button>
        </ThreadPrimitive.Suggestion>
        {/* Add more suggestions as needed */}
      </div>
    </div>
  );
};

const UserMessage: FC<{primaryColor: string, secondaryColor: string}> = ({ primaryColor, secondaryColor }) => {
  return (
    <MessagePrimitive.Root className="flex justify-end">
      <div
        className="max-w-[75%] rounded-2xl rounded-tr-sm px-5 py-3 text-white shadow-md text-base leading-relaxed whitespace-pre-wrap"
        style={{
          background: `linear-gradient(to right, ${primaryColor}, ${secondaryColor})`
        }}
      >
        <MessagePrimitive.Parts />
      </div>
    </MessagePrimitive.Root>
  );
};

const AssistantMessage: FC<{onPageChange?: (page: string) => void, primaryColor: string}> = ({ onPageChange, primaryColor }) => {
  const message = useMessage();

  // CUSTOMIZE: Add your own context analysis and follow-up logic
  const getMessageContent = (): string => {
    try {
      const content = message.content;
      if (Array.isArray(content)) {
        return content
          .filter(part => part.type === 'text')
          .map(part => 'text' in part ? part.text : '')
          .join(' ')
          .toLowerCase();
      }
      return String(content).toLowerCase();
    } catch {
      return '';
    }
  };

  const messageContent = getMessageContent();

  // CUSTOMIZE: Define your own contextual follow-ups based on your business
  const getContextualFollowUps = () => {
    // Example for e-commerce
    if (messageContent.includes('product') || messageContent.includes('buy')) {
      return [
        { prompt: "Show me product categories", label: "Categories", action: null },
        { prompt: "What are today's deals?", label: "Deals", action: null },
        { prompt: "Help with shipping", label: "Shipping", action: null },
        { prompt: "Return policy", label: "Returns", action: null },
        { prompt: "Contact support", label: "Contact", action: 'contact' },
      ];
    }

    // Example for services
    if (messageContent.includes('service') || messageContent.includes('help')) {
      return [
        { prompt: "What services do you offer?", label: "Services", action: null },
        { prompt: "How much does it cost?", label: "Pricing", action: null },
        { prompt: "Schedule a consultation", label: "Schedule", action: 'contact' },
        { prompt: "See case studies", label: "Case Studies", action: null },
        { prompt: "Contact us", label: "Contact", action: 'contact' },
      ];
    }

    // Default follow-ups
    return [
      { prompt: "Tell me more about your company", label: "About Us", action: null },
      { prompt: "What can you help me with?", label: "Services", action: null },
      { prompt: "Show me your products", label: "Products", action: null },
      { prompt: "Contact support", label: "Contact", action: 'contact' },
    ];
  };

  const followUps = getContextualFollowUps();

  const handleFollowUpClick = (followUp: { action: string | null; prompt: string }) => {
    if (followUp.action && onPageChange) {
      onClose?.();
      onPageChange(followUp.action);
    }
  };

  return (
    <MessagePrimitive.Root className="flex flex-col items-start space-y-3">
      <div className="max-w-[85%] rounded-2xl rounded-tl-sm px-6 py-4 bg-white border border-gray-200 shadow-md">
        <MessagePrimitive.Parts
          components={{
            Text: MarkdownText,
          }}
        />
      </div>

      {/* Dynamic Follow-up Questions */}
      <MessagePrimitive.If lastOrHover>
        <div className="flex flex-wrap gap-2 pl-2">
          {followUps.map((followUp, index) => (
            followUp.action ? (
              <button
                key={index}
                onClick={() => handleFollowUpClick(followUp)}
                className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-full hover:bg-gray-50 transition-all"
                style={{
                  '&:hover': { borderColor: primaryColor, color: primaryColor }
                }}
              >
                {followUp.label}
              </button>
            ) : (
              <ThreadPrimitive.Suggestion
                key={index}
                prompt={followUp.prompt}
                autoSend
                asChild
              >
                <button
                  className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-full hover:bg-gray-50 transition-all"
                  style={{
                    '&:hover': { borderColor: primaryColor, color: primaryColor }
                  }}
                >
                  {followUp.label}
                </button>
              </ThreadPrimitive.Suggestion>
            )
          ))}
        </div>
      </MessagePrimitive.If>
    </MessagePrimitive.Root>
  );
};

const Composer: FC<{primaryColor: string, secondaryColor: string}> = ({ primaryColor, secondaryColor }) => {
  return (
    <ComposerPrimitive.Root className="flex items-end gap-3 bg-gray-100 rounded-xl p-3">
      <ComposerPrimitive.Input
        className="flex-1 bg-transparent resize-none outline-none text-base placeholder:text-gray-500 max-h-32 py-2 px-3"
        placeholder="Ask me anything about [COMPANY_NAME]..."
        rows={1}
      />
      <ThreadPrimitive.If running={false}>
        <ComposerPrimitive.Send asChild>
          <button
            className="p-3 text-white rounded-lg hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg"
            style={{
              background: `linear-gradient(to right, ${primaryColor}, ${secondaryColor})`
            }}
            aria-label="Send message"
          >
            <Send className="w-5 h-5" />
          </button>
        </ComposerPrimitive.Send>
      </ThreadPrimitive.If>
      <ThreadPrimitive.If running>
        <ComposerPrimitive.Cancel asChild>
          <button
            className="p-3 bg-gray-400 text-white rounded-lg hover:opacity-90 transition-all shadow-md"
            aria-label="Cancel"
          >
            <div className="w-5 h-5 bg-white/80 rounded-sm" />
          </button>
        </ComposerPrimitive.Cancel>
      </ThreadPrimitive.If>
    </ComposerPrimitive.Root>
  );
};
```

## Customization Checklist

### Essential Customizations (Required)
- [ ] Replace all `[PLACEHOLDER]` values in system prompt
- [ ] Update company name and branding throughout components
- [ ] Set your brand colors (primaryColor, secondaryColor)
- [ ] Configure welcome message and initial suggestions
- [ ] Add your contact information (email, phone)
- [ ] Customize follow-up question logic for your business

### Visual Customizations (Recommended)
- [ ] Adjust chat widget position (bottom-6 right-6)
- [ ] Modify modal size (max-w-4xl h-[90vh])
- [ ] Update button styles and hover effects
- [ ] Customize font sizes and spacing
- [ ] Add your company logo/icon

### Content Customizations
- [ ] Write comprehensive system prompt with your data
- [ ] Create context-specific follow-up questions
- [ ] Add relevant welcome suggestions
- [ ] Include FAQs in system prompt
- [ ] Add product/service information

### Advanced Customizations (Optional)
- [ ] Add authentication wrapper
- [ ] Implement custom actions (booking, ordering, etc.)
- [ ] Add analytics tracking
- [ ] Create custom markdown components
- [ ] Add file upload capabilities
- [ ] Implement conversation history

## Industry-Specific Templates

### E-commerce
```typescript
// Follow-up questions for products
if (messageContent.includes('product')) {
  return [
    { prompt: "Browse by category", label: "Categories" },
    { prompt: "Current promotions", label: "Deals" },
    { prompt: "Track my order", label: "Track Order" },
    { prompt: "Return policy", label: "Returns" },
  ];
}
```

### Healthcare
```typescript
// Follow-up questions for healthcare
if (messageContent.includes('appointment')) {
  return [
    { prompt: "Book appointment", label: "Book Now" },
    { prompt: "View available times", label: "Availability" },
    { prompt: "Insurance coverage", label: "Insurance" },
    { prompt: "Find a doctor", label: "Doctors" },
  ];
}
```

### Financial Services
```typescript
// Follow-up questions for finance
if (messageContent.includes('investment')) {
  return [
    { prompt: "Investment options", label: "Options" },
    { prompt: "Schedule consultation", label: "Consult" },
    { prompt: "View performance", label: "Performance" },
    { prompt: "Risk assessment", label: "Risk" },
  ];
}
```

### SaaS/Technology
```typescript
// Follow-up questions for SaaS
if (messageContent.includes('feature')) {
  return [
    { prompt: "See pricing plans", label: "Pricing" },
    { prompt: "Start free trial", label: "Free Trial" },
    { prompt: "View documentation", label: "Docs" },
    { prompt: "Technical support", label: "Support" },
  ];
}
```

## Deployment Steps

### 1. Environment Variables
```bash
# Production (Vercel, Netlify, etc.)
OPENAI_API_KEY=sk-...
NEXT_PUBLIC_SITE_URL=https://yoursite.com
```

### 2. Testing Checklist
- [ ] Test on mobile devices (iOS/Android)
- [ ] Verify keyboard accessibility
- [ ] Check loading states
- [ ] Test error handling
- [ ] Verify markdown rendering
- [ ] Test follow-up buttons
- [ ] Check modal open/close
- [ ] Test with slow connections

### 3. Performance Optimization
```typescript
// Lazy load the widget
import dynamic from 'next/dynamic';

const ChatWidget = dynamic(
  () => import('./components/ChatWidget'),
  {
    ssr: false,
    loading: () => null
  }
);
```

### 4. Security Configuration
- Set up rate limiting on API route
- Add CORS headers if needed
- Implement content filtering
- Use environment variables for sensitive data
- Add request validation

## AI Model Selection Guide

### GPT-4o-mini (Recommended for most)
- Cost-effective
- Fast responses
- Good for general customer support

### GPT-4o
- Best quality responses
- Higher cost
- Use for complex domains

### GPT-3.5-turbo
- Fastest responses
- Lowest cost
- Good for simple Q&A

## Common Issues & Solutions

### Chat not responding
- Check OPENAI_API_KEY in environment variables
- Verify API route is accessible
- Check browser console for errors

### Styling issues
- Ensure Tailwind CSS is configured
- Check for CSS conflicts
- Verify z-index values

### Follow-ups not showing
- Update to MessagePrimitive.If lastOrHover
- Check message content parsing
- Verify ThreadPrimitive imports

## Support & Resources

- [assistant-ui Documentation](https://www.assistant-ui.com/docs)
- [Vercel AI SDK](https://sdk.vercel.ai/docs)
- [OpenAI API](https://platform.openai.com/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)

## License

This skill template is free to use and modify for your projects.