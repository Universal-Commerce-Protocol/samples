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
import type {Location} from '../types';

interface LocationCardProps {
  location: Location;
  onSelect?: (locationId: string) => void;
  isSelected?: boolean;
}

const LocationCard: React.FC<LocationCardProps> = ({
  location,
  onSelect,
  isSelected,
}) => {
  const formatAddress = (address?: Location['address']) => {
    if (!address) return null;
    const parts = [
      address.address_line_1,
      address.address_line_2,
      [address.locality, address.administrative_district_level_1, address.postal_code]
        .filter(Boolean)
        .join(', '),
    ].filter(Boolean);
    return parts.join('\n');
  };

  return (
    <div
      className={`bg-white rounded-lg shadow-md overflow-hidden w-72 flex-shrink-0 border-2 transition-colors ${
        isSelected ? 'border-blue-500' : 'border-transparent'
      }`}>
      <div className="p-4">
        <div className="flex justify-between items-start mb-2">
          <h3
            className="text-lg font-semibold text-gray-800 truncate flex-1"
            title={location.name}>
            {location.name}
          </h3>
        </div>
        {location.address && (
          <div className="flex items-start text-sm text-gray-600 mt-2">
            <svg
              className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            <span className="whitespace-pre-line">
              {formatAddress(location.address)}
            </span>
          </div>
        )}
        {location.timezone && (
          <div className="flex items-center text-sm text-gray-500 mt-2">
            <svg
              className="w-4 h-4 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>{location.timezone}</span>
          </div>
        )}
        {onSelect && (
          <button
            type="button"
            onClick={() => onSelect(location.id)}
            className={`block w-full text-center py-2 rounded-md mt-4 transition-colors ${
              isSelected
                ? 'bg-blue-600 text-white'
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}>
            {isSelected ? 'Selected' : 'Select Location'}
          </button>
        )}
      </div>
    </div>
  );
};

export default LocationCard;
