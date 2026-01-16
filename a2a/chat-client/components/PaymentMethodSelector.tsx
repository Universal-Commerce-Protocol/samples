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
import {PaymentMethod} from '../types';

interface PaymentMethodSelectorProps {
  paymentMethods: PaymentMethod[];
  onSelect: (selectedMethod: string) => void;
}

const PaymentMethodSelector: React.FC<PaymentMethodSelectorProps> = ({
  paymentMethods,
  onSelect,
}) => {
  const [selectedMethod, setSelectedMethod] = useState<string | null>(null);

  const handleContinue = () => {
    if (selectedMethod) {
      onSelect(selectedMethod);
    }
  };

  return (
    <div className="max-w-md bg-white rounded-lg shadow-lg p-4 border border-gray-200">
      <h3 className="text-lg font-bold text-gray-800 mb-3">
        Select a Payment Method
      </h3>
      <div className="space-y-2 mb-4">
        {paymentMethods.map((method, index) => (
          <label
            key={method.id}
            className="flex items-center p-2 rounded-md hover:bg-gray-100 cursor-pointer">
            <input
              type="radio"
              name="paymentMethod"
              value={method.id}
              checked={selectedMethod === method.id}
              onChange={() => setSelectedMethod(method.id)}
              className="form-radio h-4 w-4 text-blue-600"
            />
            <span className="ml-3 text-gray-700">
              {method.brand.toUpperCase()} ending in {method.last_digits}
            </span>
          </label>
        ))}
      </div>
      <button
        type="button"
        onClick={handleContinue}
        disabled={!selectedMethod}
        className="block w-full text-center bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed">
        Continue
      </button>
    </div>
  );
};

export default PaymentMethodSelector;
