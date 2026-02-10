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
import type React from 'react';
import type {ServiceVariation} from '../types';

interface ServiceCardProps {
  service: ServiceVariation;
  onAddToCheckout?: (service: ServiceVariation) => void;
}

const ServiceCard: React.FC<ServiceCardProps> = ({service, onAddToCheckout}) => {
  const isAvailable = service.available_for_booking !== false;
  const handleBookClick = () => onAddToCheckout?.(service);

  const formatDuration = () => {
    // Use duration_seconds if available (new backend format)
    if (service.duration_seconds) {
      const minutes = Math.floor(service.duration_seconds / 60);
      if (minutes >= 60) {
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
      }
      return `${minutes} min`;
    }
    // Fallback to service_duration (legacy format, already in minutes)
    if (service.service_duration) {
      const minutes = service.service_duration;
      if (minutes >= 60) {
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
      }
      return `${minutes} min`;
    }
    return null;
  };

  const formatPrice = () => {
    // Use display_price if available (new backend format)
    if (service.display_price) return service.display_price;
    // Fallback to price_money (legacy format)
    if (service.price_money) {
      const currencySymbol = service.price_money.currency === 'EUR' ? '€' : '$';
      return `${currencySymbol}${(service.price_money.amount / 100).toFixed(2)}`;
    }
    return 'Price varies';
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden w-64 flex-shrink-0">
      {service.image_url ? (
        <img
          src={service.image_url}
          alt={service.name}
          className="w-full h-48 object-cover"
        />
      ) : (
        <div className="w-full h-48 bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center">
          <svg
            className="w-16 h-16 text-blue-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
      )}
      <div className="p-4">
        <h3
          className="text-lg font-semibold text-gray-800 truncate"
          title={service.name}>
          {service.name}
        </h3>
        {service.description && (
          <p className="text-sm text-gray-600 mt-1 line-clamp-2">
            {service.description}
          </p>
        )}
        <div className="flex justify-between items-center mt-3">
          <p className="text-lg font-bold text-gray-900">
            {formatPrice()}
          </p>
          {(service.duration_seconds || service.service_duration) && (
            <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
              {formatDuration()}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={handleBookClick}
          disabled={!isAvailable || !onAddToCheckout}
          className="block w-full text-center bg-blue-500 text-white py-2 rounded-md mt-4 hover:bg-blue-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed">
          Book Service
        </button>
      </div>
    </div>
  );
};

export default ServiceCard;
