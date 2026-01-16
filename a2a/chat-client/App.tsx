/*
 * Copyright 2026 UCP Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
import React, {useEffect, useRef, useState} from 'react';
import ChatInput from './components/ChatInput';
import ChatMessageComponent from './components/ChatMessage';
import Header from './components/Header';
import {appConfig} from './config';
import {CredentialProviderProxy} from './mocks/credentialProviderProxy';

import {ChatMessage, PaymentInstrument, Product, Sender} from './types';

function createChatMessage(
  sender: Sender,
  text: string,
  props: Partial<ChatMessage> = {},
): ChatMessage {
  return {
    id: crypto.randomUUID(),
    sender,
    text,
    ...props,
  };
}

const initialMessage: ChatMessage = createChatMessage(
  Sender.MODEL,
  appConfig.defaultMessage,
  {id: 'initial'},
);

/**
 * An example A2A chat client that demonstrates consuming a business's A2A Agent with UCP Extension.
 * Only for demo purposes, not intended for production use.
 */
function App() {
  const [user_email, setUserEmail] = useState<string | null>('foo@example.com');
  const [messages, setMessages] = useState<ChatMessage[]>([initialMessage]);
  const [isLoading, setIsLoading] = useState(false);
  const [contextId, setContextId] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const credentialProvider = useRef(new CredentialProviderProxy());
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Scroll to the bottom when new messages are added
  // biome-ignore lint/correctness/useExhaustiveDependencies: Scroll when messages change
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleAddToCheckout = (productToAdd: Product) => {
    const actionPayload = JSON.stringify({
      action: 'add_to_checkout',
      product_id: productToAdd.productID,
      quantity: 1,
    });
    handleSendMessage(actionPayload, {isUserAction: true});
  };

  const handleStartPayment = () => {
    const actionPayload = JSON.stringify({action: 'start_payment'});
    handleSendMessage(actionPayload, {
      isUserAction: true,
    });
  };

  const handlePaymentMethodSelection = async (checkout: any) => {
    if (!checkout || !checkout.payment || !checkout.payment.handlers) {
      const errorMessage = createChatMessage(
        Sender.MODEL,
        "Sorry, I couldn't retrieve payment methods.",
      );
      setMessages((prev) => [...prev, errorMessage]);
      return;
    }

    //find the handler with id "example_payment_provider"
    const handler = checkout.payment.handlers.find(
      (handler: any) => handler.id === 'example_payment_provider',
    );
    if (!handler) {
      const errorMessage = createChatMessage(
        Sender.MODEL,
        "Sorry, I couldn't find the supported payment handler.",
      );
      setMessages((prev) => [...prev, errorMessage]);
      return;
    }

    try {
      const paymentResponse =
        await credentialProvider.current.getSupportedPaymentMethods(
          user_email,
          handler.config,
        );
      const paymentMethods = paymentResponse.payment_method_aliases;

      const paymentSelectorMessage = createChatMessage(Sender.MODEL, '', {
        paymentMethods,
      });
      setMessages((prev) => [...prev, paymentSelectorMessage]);
    } catch (error) {
      console.error('Failed to resolve mandate:', error);
      const errorMessage = createChatMessage(
        Sender.MODEL,
        "Sorry, I couldn't retrieve payment methods.",
      );
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handlePaymentMethodSelected = async (selectedMethod: string) => {
    // Hide the payment selector by removing it from the messages
    setMessages((prev) => prev.filter((msg) => !msg.paymentMethods));

    // Add a temporary user message
    const userActionMessage = createChatMessage(
      Sender.USER,
      `User selected payment method: ${selectedMethod}`,
      {isUserAction: true},
    );
    setMessages((prev) => [...prev, userActionMessage]);

    try {
      if (!user_email) {
        throw new Error('User email is not set.');
      }

      const paymentInstrument =
        await credentialProvider.current.getPaymentToken(
          user_email,
          selectedMethod,
        );

      if (!paymentInstrument || !paymentInstrument.credential) {
        throw new Error('Failed to retrieve payment credential');
      }

      const paymentInstrumentMessage = createChatMessage(Sender.MODEL, '', {
        paymentInstrument,
      });
      setMessages((prev) => [...prev, paymentInstrumentMessage]);
    } catch (error) {
      console.error('Failed to process payment mandate:', error);
      const errorMessage = createChatMessage(
        Sender.MODEL,
        "Sorry, I couldn't process the payment. Please try again.",
      );
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handleConfirmPayment = async (paymentInstrument: PaymentInstrument) => {
    // Hide the payment confirmation component
    const userActionMessage = createChatMessage(
      Sender.USER,
      `User confirmed payment.`,
      {isUserAction: true},
    );
    // Let handleSendMessage manage the loading indicator
    setMessages((prev) => [
      ...prev.filter((msg) => !msg.paymentInstrument),
      userActionMessage,
    ]);

    try {
      const parts = [
        {type: 'data', data: {'action': 'complete_checkout'}},
        {
          type: 'data',
          data: {
            'a2a.ucp.checkout.payment_data': paymentInstrument,
            'a2a.ucp.checkout.risk_signals': {'data': 'some risk data'},
          },
        },
      ];

      await handleSendMessage(parts, {
        isUserAction: true,
      });
    } catch (error) {
      console.error('Error confirming payment:', error);
      const errorMessage = createChatMessage(
        Sender.MODEL,
        'Sorry, there was an issue confirming your payment.',
      );
      // If handleSendMessage wasn't called, we might need to manually update state
      // In this case, we remove the loading indicator that handleSendMessage would have added
      setMessages((prev) => [...prev.slice(0, -1), errorMessage]); // This assumes handleSendMessage added a loader
      setIsLoading(false); // Ensure loading is stopped on authorization error
    }
  };

  const handleSendMessage = async (
    messageContent: string | any[],
    options?: {isUserAction?: boolean; headers?: Record<string, string>},
  ) => {
    if (isLoading) return;

    const userMessage = createChatMessage(
      Sender.USER,
      options?.isUserAction
        ? '<User Action>'
        : typeof messageContent === 'string'
          ? messageContent
          : 'Sent complex data',
    );
    if (userMessage.text) {
      // Only add if there's text
      setMessages((prev) => [...prev, userMessage]);
    }
    setMessages((prev) => [
      ...prev,
      createChatMessage(Sender.MODEL, '', {isLoading: true}),
    ]);
    setIsLoading(true);

    try {
      const requestParts =
        typeof messageContent === 'string'
          ? [{type: 'text', text: messageContent}]
          : messageContent;

      const requestParams: any = {
        message: {
          role: 'user',
          parts: requestParts,
          messageId: crypto.randomUUID(),
          kind: 'message',
        },
        configuration: {
          historyLength: 0,
        },
      };

      if (contextId) {
        requestParams.message.contextId = contextId;
      }
      if (taskId) {
        requestParams.message.taskId = taskId;
      }

      const defaultHeaders = {
        'Content-Type': 'application/json',
        'X-A2A-Extensions':
          'https://ucp.dev/specification/reference?v=2026-01-11',
        'UCP-Agent':
          'profile="http://localhost:3000/profile/agent_profile.json"',
      };

      const response = await fetch('/api', {
        method: 'POST',
        headers: {...defaultHeaders, ...options?.headers},
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: crypto.randomUUID(),
          method: 'message/send',
          params: requestParams,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data = await response.json();

      // Update context and task IDs from the response for subsequent requests
      if (data.result?.contextId) {
        setContextId(data.result.contextId);
      }
      //if there is a task and it's in one of the active states
      if (
        data.result?.id &&
        data.result?.status?.state in ['working', 'submitted', 'input-required']
      ) {
        setTaskId(data.result.id);
      } else {
        //if not reset taskId
        setTaskId(undefined);
      }

      const combinedBotMessage = createChatMessage(Sender.MODEL, '');

      const responseParts =
        data.result?.parts || data.result?.status?.message?.parts || [];

      for (const part of responseParts) {
        if (part.text) {
          // Simple text
          combinedBotMessage.text +=
            (combinedBotMessage.text ? '\n' : '') + part.text;
        } else if (part.data?.['a2a.product_results']) {
          // Product results
          combinedBotMessage.text +=
            (combinedBotMessage.text ? '\n' : '') +
            (part.data['a2a.product_results'].content || '');
          combinedBotMessage.products =
            part.data['a2a.product_results'].results;
        } else if (part.data?.['a2a.ucp.checkout']) {
          // Checkout
          combinedBotMessage.checkout = part.data['a2a.ucp.checkout'];
        }
      }

      const newMessages: ChatMessage[] = [];
      const hasContent =
        combinedBotMessage.text ||
        combinedBotMessage.products ||
        combinedBotMessage.checkout;
      if (hasContent) {
        newMessages.push(combinedBotMessage);
      }

      if (newMessages.length > 0) {
        setMessages((prev) => [...prev.slice(0, -1), ...newMessages]);
      } else {
        const fallbackResponse =
          "Sorry, I received a response I couldn't understand.";
        setMessages((prev) => [
          ...prev.slice(0, -1),
          createChatMessage(Sender.MODEL, fallbackResponse),
        ]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = createChatMessage(
        Sender.MODEL,
        'Sorry, something went wrong. Please try again.',
      );
      // Replace the placeholder with the error message
      setMessages((prev) => [...prev.slice(0, -1), errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const lastCheckoutIndex = messages.map((m) => !!m.checkout).lastIndexOf(true);

  return (
    <div className="flex flex-col h-screen max-h-screen bg-white font-sans">
      <Header logoUrl={appConfig.logoUrl} title={appConfig.name} />
      <main
        ref={chatContainerRef}
        className="flex-grow overflow-y-auto p-4 md:p-6 space-y-2">
        {messages.map((msg, index) => (
          <ChatMessageComponent
            key={msg.id}
            message={msg}
            onAddToCart={handleAddToCheckout}
            onCheckout={
              msg.checkout?.status !== 'ready_for_complete'
                ? handleStartPayment
                : undefined
            }
            onSelectPaymentMethod={handlePaymentMethodSelected}
            onConfirmPayment={handleConfirmPayment}
            onCompletePayment={
              msg.checkout?.status === 'ready_for_complete'
                ? handlePaymentMethodSelection
                : undefined
            }
            isLastCheckout={index === lastCheckoutIndex}></ChatMessageComponent>
        ))}
      </main>
      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
}

export default App;
