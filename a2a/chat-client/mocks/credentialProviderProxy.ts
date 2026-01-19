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
import type {PaymentInstrument, PaymentMethod} from '../types';

/**
 * A mock CredentialProvider to simulate calls to a remote service for credentials.
 * In a real application, this would make a network request to a provider's service.
 */
export class CredentialProviderProxy {
  handler_id = 'example_payment_provider';
  handler_name = 'example.payment.provider';

  _getMockPaymentMethods(): {payment_method_aliases: PaymentMethod[]} {
    return {
      'payment_method_aliases': [
        {
          'id': 'instr_1',
          'type': 'card',
          'brand': 'amex',
          'last_digits': '1111',
          'expiry_month': 12,
          'expiry_year': 2026,
        },
        {
          'id': 'instr_2',
          'type': 'card',
          'brand': 'visa',
          'last_digits': '8888',
          'expiry_month': 12,
          'expiry_year': 2026,
        },
        {
          'id': 'instr_3',
          'type': 'card',
          'brand': 'mastercard',
          'last_digits': '5555',
          'expiry_month': 12,
          'expiry_year': 2026,
        },
      ],
    };
  }
  /**
   * Simulates fetching supported payment methods based on the cart mandate.
   * @param config The payment handler config defined by the merchant.
   * @returns A promise that resolves to a mock payment methods response.
   */  
  async getSupportedPaymentMethods(
    user_email: string,
    // biome-ignore lint/suspicious/noExplicitAny: no specific type for config
    config: any,
  ): Promise<{payment_method_aliases: PaymentMethod[]}> {
    console.log(
      `CredentialProviderProxy: Simulating fetch for ${user_email} supported payment methods with config:`,
      config,
    );
    // Simulate network latency
    await new Promise((resolve) => setTimeout(resolve, 500));
    return this._getMockPaymentMethods();
  }

  /**
   * Simulates fetching a payment token for a selected payment method.
   * @param user_email The user's email.
   * @param payment_method_id The selected payment method alias.
   * @returns A promise that resolves to a mock payment token response.
   */
  async getPaymentToken(
    user_email: string,
    payment_method_id: string,
  ): Promise<PaymentInstrument | undefined> {
    console.log(
      `CredentialProviderProxy: Simulating fetch for payment token for user ${user_email} and method ${payment_method_id}`,
    );
    // Simulate network latency
    await new Promise((resolve) => setTimeout(resolve, 500));
    const randomId = crypto.randomUUID();
    const payment_method =
      this._getMockPaymentMethods().payment_method_aliases.find(
        (method) => method.id === payment_method_id,
      );

    if (!payment_method) {
      return undefined;
    }

    return {
      ...payment_method,
      handler_id: this.handler_id,
      handler_name: this.handler_name,
      credential: {
        type: 'token',
        token: `mock_token_${randomId}`
      },
    };
  }
}
