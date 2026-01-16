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
import React, {useState} from 'react';

import {Checkout} from '../types';

interface CheckoutProps {
  checkout: Checkout;
  onCheckout?: () => void;
  onCompletePayment?: (checkout: Checkout) => void;
}

const CheckoutComponent: React.FC<CheckoutProps> = ({
  checkout,
  onCheckout,
  onCompletePayment,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const itemsToShow = isExpanded
    ? checkout.line_items
    : checkout.line_items.slice(0, 5);

  const formatCurrency = (amount: number, currency: string) => {
    const currencySymbol = currency === 'EUR' ? '€' : '$';
    return `${currencySymbol}${(amount / 100).toFixed(2)}`;
  };

  const getTotal = (type: string) => {
    return checkout.totals.find((t) => t.type === type);
  };

  const getItemTotal = (lineItem: any) => {
    return lineItem.totals.find((t) => t.type === 'total');
  };

  const grandTotal = getTotal('total');

  return (
    <div className="flex w-full my-2 justify-start">
      <div className="max-w-md bg-white rounded-lg shadow-lg p-4 border border-gray-200">
        <h3 className="text-md font-bold text-gray-800 border-b pb-2 mb-3 flex items-center">
          <svg
            role="img"
            aria-label="Checkout"
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6 mr-2"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}>
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
          {checkout.status === 'completed'
            ? 'Order Confirmed'
            : 'Checkout Summary'}
        </h3>
        {checkout.order?.id && (
          <p className="border-b pt-3 pb-3 text-sm space-y-2">
            Order ID: {checkout.order.id}
          </p>
        )}
        <div className="pt-3 space-y-3">
          {itemsToShow.map((lineItem: any) => (
            <div key={lineItem.id} className="flex items-center text-sm">
              <img
                src={lineItem.item.image_url}
                alt={lineItem.item.id}
                className="w-16 h-16 object-cover rounded-md mr-4"
              />
              <div className="flex-grow">
                <p className="font-semibold text-gray-700">
                  {lineItem.item.title}
                </p>
                <p className="text-gray-500">Qty: {lineItem.quantity}</p>
              </div>
              <p className="text-gray-800 font-medium pl-2">
                {formatCurrency(
                  getItemTotal(lineItem).amount,
                  checkout.currency,
                )}
              </p>
            </div>
          ))}
        </div>
        {checkout.line_items.length > 5 && (
          <div className="mt-3">
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-sm text-blue-600 hover:underline w-full text-center">
              {isExpanded
                ? 'Show less'
                : `Show ${checkout.line_items.length - 5} more items`}
            </button>
          </div>
        )}
        <div className="border-t mt-4 pt-3 text-sm space-y-2">
          {checkout.totals
            .filter((t) => t.type !== 'total' && t.amount > 0)
            .map((total) => (
              <div
                key={total.type}
                className="flex justify-between items-center">
                <span className="text-gray-600">{total.display_text}</span>
                <span className="text-gray-800 font-medium">
                  {formatCurrency(total.amount, checkout.currency)}
                </span>
              </div>
            ))}
        </div>
        {grandTotal && (
          <div className="border-t mt-4 pt-3">
            <div className="flex justify-between items-center font-bold text-md">
              <span>{grandTotal.display_text}</span>
              <span>
                {formatCurrency(grandTotal.amount, checkout.currency)}
              </span>
            </div>
          </div>
        )}
        <p className="text-xs text-gray-400 mt-3 text-center">
          Checkout ID: {checkout.id}
        </p>
        {checkout.status !== 'completed' && (
          <div className="border-t mt-4 pt-4 flex justify-around items-center">
            {checkout.continue_url && (
              <a
                href={checkout.continue_url}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded text-sm">
                Go to Checkout
              </a>
            )}
            {onCheckout && (
              <button
                type="button"
                onClick={onCheckout}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded text-sm">
                Start Payment
              </button>
            )}
            {onCompletePayment && (
              <button
                type="button"
                onClick={() => onCompletePayment && onCompletePayment(checkout)}
                className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded text-sm">
                Complete Payment
              </button>
            )}
          </div>
        )}
        {checkout.order?.permalink_url && (
          <a
            href={checkout.order.permalink_url}
            className="block mt-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded text-center">
            View Order
          </a>
        )}
      </div>
    </div>
  );
};

export default CheckoutComponent;
