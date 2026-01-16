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
import {PaymentInstrument} from '../types';

interface PaymentConfirmationProps {
  paymentInstrument: PaymentInstrument;
  onConfirm: () => void;
}

const PaymentConfirmationComponent: React.FC<PaymentConfirmationProps> = ({
  paymentInstrument,
  onConfirm,
}) => {
  const [isConfirming, setIsConfirming] = useState(false);

  const handleConfirmClick = () => {
    if (isConfirming) return;
    setIsConfirming(true);
    onConfirm();
  };

  return (
    <div className="max-w-md bg-white rounded-lg shadow-lg p-4 border border-gray-200">
      <h3 className="text-lg font-bold text-gray-800 mb-3">
        Confirm Your Purchase
      </h3>
      <div className="flex justify-between items-center text-md mb-4">
        <span>Selected Payment Method</span>
        <span>
          {paymentInstrument.brand.toUpperCase()} ending in{' '}
          {paymentInstrument.last_digits}
        </span>
      </div>
      <p className="text-gray-600 mb-4">
        Please confirm to complete your purchase.
      </p>
      <button
        type="button"
        onClick={handleConfirmClick}
        disabled={isConfirming}
        className="flex justify-center items-center w-full text-center bg-green-500 text-white py-2 rounded-md hover:bg-green-600 transition-colors disabled:bg-green-400 disabled:cursor-wait">
        {isConfirming ? (
          <>
            <svg
              title="Processing"
              aria-label="Processing"
              role="img"
              className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Processing...
          </>
        ) : (
          'Confirm Purchase'
        )}
      </button>
    </div>
  );
};

export default PaymentConfirmationComponent;
