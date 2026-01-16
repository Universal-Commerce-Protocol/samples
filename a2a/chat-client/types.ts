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
export enum Sender {
  USER = 'user',
  MODEL = 'model',
}

export interface Product {
  productID: string;
  name: string;
  image: string[];
  brand: {name: string};
  offers: {
    price: string;
    priceCurrency: string;
    availability: string;
  };
  url: string;
  description: string;
  size: {
    name: string;
  };
}

export interface Credential {
  type: string;
  token: string;
}

export interface PaymentMethod {
  id: string;
  type: string;
  brand: string;
  last_digits: string;
  expiry_month: number;
  expiry_year: number;
}

export interface PaymentInstrument extends PaymentMethod {
  handler_id: string;
  handler_name: string;
  credential: Credential;
}

export interface ChatMessage {
  id: string;
  sender: Sender;
  text: string;
  products?: Product[];
  isLoading?: boolean;
  paymentMethods?: PaymentMethod[];
  isUserAction?: boolean;
  checkout?: Checkout;
  paymentInstrument?: PaymentInstrument;
}

// Type guard to check for a valid text response
export const isTextResult = (data: any): boolean => {
  try {
    return (
      data.result.status.message.parts[0].kind === 'text' &&
      typeof data.result.status.message.parts[0].text === 'string'
    );
  } catch (e) {
    return false;
  }
};

export interface CheckoutTotal {
  type: string;
  display_text: string;
  amount: number;
}

export interface CheckoutItem {
  id: string;
  item: {
    id: string;
    quantity: number;
    unit_cost: number;
  };
  total: number;
}

export interface Checkout {
  id: string;
  line_items: CheckoutItem[];
  currency: string;
  continue_url?: string | null;
  status: string;
  totals: CheckoutTotal[];
  order_id?: string;
  order_permalink_url?: string;
  payment?: any;
}
